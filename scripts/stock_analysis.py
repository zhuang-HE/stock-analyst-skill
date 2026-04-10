# -*- coding: utf-8 -*-
"""
完整的股票分析报告生成 - 修复版
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class StockAnalyzer:
    """股票分析器"""

    STOCK_NAMES = {
        '000001': '平安银行',
        '600519': '贵州茅台',
        '600036': '招商银行',
        '000002': '万科A',
        '000858': '五粮液',
        '600887': '伊利股份',
        '000333': '美的集团',
        '002475': '立讯精密',
        '601318': '中国平安',
        '601166': '兴业银行',
        '600276': '恒瑞医药',
        '300750': '宁德时代',
    }

    def __init__(self):
        self.data = {}

    def normalize_code(self, code: str) -> tuple:
        code = code.strip().upper()
        if code.endswith('.SH') or code.startswith('6'):
            return 'sh', code.replace('.SH', '')
        elif code.endswith('.SZ') or code.startswith(('0', '3')):
            return 'sz', code.replace('.SZ', '')
        else:
            if code.startswith('6'):
                return 'sh', code
            return 'sz', code

    def get_stock_name(self, code: str) -> str:
        return self.STOCK_NAMES.get(code, code)

    def _safe_get_column(self, df: pd.DataFrame, *names) -> str:
        """安全获取列名"""
        for name in names:
            if name in df.columns:
                return name
        return df.columns[0] if len(df.columns) > 0 else None

    def get_full_analysis(self, code: str) -> dict:
        """获取完整分析报告"""
        result = {
            'success': False,
            'code': code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            market, symbol = self.normalize_code(code)

            # 1. 获取历史K线
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')

            try:
                hist = ak.stock_zh_a_hist(symbol=symbol, period='daily',
                                         start_date=start_date, end_date=end_date)
            except:
                hist = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')

            if hist is not None and len(hist) > 0:
                # 统一列名
                close_col = self._safe_get_column(hist, '收盘', 'close', 'Close')
                open_col = self._safe_get_column(hist, '开盘', 'open', 'Open')
                high_col = self._safe_get_column(hist, '最高', 'high', 'High')
                low_col = self._safe_get_column(hist, '最低', 'low', 'Low')
                vol_col = self._safe_get_column(hist, '成交量', 'volume', 'Volume')
                amount_col = self._safe_get_column(hist, '成交额', 'amount', 'Amount')
                turnover_col = self._safe_get_column(hist, '换手率', 'turnover', 'Turnover')

                hist = hist.rename(columns={
                    close_col: 'close', open_col: 'open',
                    high_col: 'high', low_col: 'low',
                    vol_col: 'volume', amount_col: 'amount',
                    turnover_col: 'turnover'
                })

                # 最新数据
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest

                # 行情数据
                result['quote'] = {
                    'name': self.get_stock_name(symbol),
                    'price': float(latest['close']),
                    'change': float(latest['close'] - prev['close']),
                    'pct_change': float((latest['close'] - prev['close']) / prev['close'] * 100),
                    'open': float(latest['open']),
                    'high': float(latest['high']),
                    'low': float(latest['low']),
                    'volume': int(latest['volume']),
                    'amount': float(latest['amount'] / 100000000),
                    'turnover': float(latest.get('turnover', 0) * 100),
                    'date': str(latest.get('date', latest.name))[:10]
                }

                # 计算技术指标
                result['technical'] = self._calculate_indicators(hist)

                # 计算评分和建议
                result['suggestion'] = self._calculate_suggestion(result)

            # 2. 获取基本信息
            try:
                info_df = ak.stock_individual_info_em(symbol=symbol)
                if info_df is not None:
                    result['basic_info'] = {}
                    for _, row in info_df.iterrows():
                        result['basic_info'][row['item']] = row['value']
            except:
                pass

            # 3. 获取新闻
            try:
                news_df = ak.stock_news_em(symbol=symbol)
                if news_df is not None and len(news_df) > 0:
                    result['news'] = []
                    for _, row in news_df.head(3).iterrows():
                        result['news'].append({
                            'title': row.get('新闻标题', ''),
                            'content': str(row.get('新闻内容', ''))[:200],
                            'date': str(row.get('发布日期', ''))
                        })
            except:
                pass

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)
            import traceback
            result['trace'] = traceback.format_exc()

        return result

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """计算技术指标"""
        if df.empty or len(df) < 20:
            return {}

        data = df.copy()

        # 均线
        data['MA5'] = data['close'].rolling(window=5).mean()
        data['MA10'] = data['close'].rolling(window=10).mean()
        data['MA20'] = data['close'].rolling(window=20).mean()
        data['MA60'] = data['close'].rolling(window=60).mean()

        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # KDJ
        low14 = data['low'].rolling(window=9).min()
        high14 = data['high'].rolling(window=9).max()
        rsv = (data['close'] - low14) / (high14 - low14) * 100
        data['K'] = rsv.ewm(com=2).mean()
        data['D'] = data['K'].ewm(com=2).mean()
        data['J'] = 3 * data['K'] - 2 * data['D']

        latest = data.iloc[-1]

        # 趋势判断
        ma5 = latest['MA5'] if pd.notna(latest['MA5']) else 0
        ma20 = latest['MA20'] if pd.notna(latest['MA20']) else 0
        price = latest['close']

        if ma5 > ma20:
            trend = '上升趋势' if ma5 > ma20 * 1.02 else '震荡偏强'
        else:
            trend = '下降趋势' if ma5 < ma20 * 0.98 else '震荡偏弱'

        # KDJ信号
        k = latest['K'] if pd.notna(latest['K']) else 50
        d = latest['D'] if pd.notna(latest['D']) else 50
        j = latest['J'] if pd.notna(latest['J']) else 50

        if k > 80:
            kdj_signal = '超买区'
        elif k < 20:
            kdj_signal = '超卖区'
        elif k > d:
            kdj_signal = '金叉'
        else:
            kdj_signal = '死叉'

        # RSI信号
        rsi = latest['RSI'] if pd.notna(latest['RSI']) else 50
        if rsi > 70:
            rsi_signal = '超买'
        elif rsi < 30:
            rsi_signal = '超卖'
        else:
            rsi_signal = '正常'

        return {
            'ma5': round(float(ma5), 2),
            'ma10': round(float(latest['MA10']), 2) if pd.notna(latest['MA10']) else None,
            'ma20': round(float(ma20), 2),
            'ma60': round(float(latest['MA60']), 2) if pd.notna(latest['MA60']) else None,
            'rsi': round(float(rsi), 2),
            'rsi_signal': rsi_signal,
            'k': round(float(k), 2),
            'd': round(float(d), 2),
            'j': round(float(j), 2),
            'kdj_signal': kdj_signal,
            'trend': trend,
            'price_above_ma20': bool(price > ma20),
            'price_above_ma5': bool(price > ma5)
        }

    def _calculate_suggestion(self, result: dict) -> dict:
        """计算投资建议"""
        score = 50

        quote = result.get('quote', {})
        tech = result.get('technical', {})

        # 涨跌幅评分
        pct = quote.get('pct_change', 0)
        if pct > 5:
            score -= 15
        elif pct > 2:
            score -= 5
        elif pct < -3:
            score += 15
        elif pct < -1:
            score += 5

        # 趋势评分
        trend = tech.get('trend', '')
        if '上升' in trend:
            score += 15
        elif '下降' in trend:
            score -= 15
        elif '震荡偏强' in trend:
            score += 5
        elif '震荡偏弱' in trend:
            score -= 5

        # RSI评分
        rsi = tech.get('rsi', 50)
        if rsi < 30:
            score += 10
        elif rsi > 70:
            score -= 10
        elif 40 <= rsi <= 60:
            score += 5

        # KDJ评分
        kdj = tech.get('kdj_signal', '')
        if '超卖' in kdj:
            score += 10
        elif '超买' in kdj:
            score -= 10
        elif '金叉' in kdj:
            score += 5
        elif '死叉' in kdj:
            score -= 5

        score = max(0, min(100, score))

        # 生成建议
        if score >= 70:
            action, level = '积极买入', '积极'
        elif score >= 55:
            action, level = '适量买入', '谨慎乐观'
        elif score >= 45:
            action, level = '观望', '谨慎'
        elif score >= 30:
            action, level = '谨慎卖出', '风险'
        else:
            action, level = '建议卖出', '高风险'

        price = quote.get('price', 0)
        return {
            'score': score,
            'action': action,
            'level': level,
            'target_price': round(price * 1.08, 2) if price > 0 else 0,
            'stop_loss': round(price * 0.95, 2) if price > 0 else 0,
            'position': f'{min(30, max(5, score // 3))}%'
        }


def main():
    import json

    if len(sys.argv) < 2:
        print(json.dumps({'error': '请提供股票代码'}, ensure_ascii=False, indent=2))
        return

    code = sys.argv[1]
    analyzer = StockAnalyzer()
    result = analyzer.get_full_analysis(code)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
