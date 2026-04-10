# -*- coding: utf-8 -*-
"""
Stock Analyst - 股票分析核心模块
基于AkShare真实数据进行分析
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

    # A股股票名称映射表
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
        '688981': '中芯国际',
    }

    def __init__(self):
        self.data = {}

    def normalize_code(self, code: str) -> tuple:
        """标准化股票代码"""
        code = code.strip().upper()

        # 判断市场
        if code.endswith('.SH') or code.startswith('6'):
            market = 'sh'
            symbol = code.replace('.SH', '')
        elif code.endswith('.SZ') or code.startswith(('0', '3')):
            market = 'sz'
            symbol = code.replace('.SZ', '')
        elif code.endswith('.HK') or code.startswith('0'):
            if len(code) <= 5:
                market = 'hk'
                symbol = code.replace('.HK', '').zfill(5)
            else:
                market = 'hk'
                symbol = code.replace('.HK', '')
        elif code.endswith('.US') or code.isalpha():
            market = 'us'
            symbol = code.replace('.US', '')
        else:
            # 默认A股
            if code.startswith('6'):
                market = 'sh'
                symbol = code
            else:
                market = 'sz'
                symbol = code

        return market, symbol

    def get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        return self.STOCK_NAMES.get(code, code)

    def get_realtime_quote(self, code: str) -> dict:
        """获取实时行情"""
        try:
            market, symbol = self.normalize_code(code)

            # 尝试获取实时数据
            if market in ['sh', 'sz']:
                # A股实时数据
                df = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
                if df is not None and len(df) > 0:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest

                    # 计算涨跌幅
                    price_change = latest['close'] - prev['close']
                    pct_change = (price_change / prev['close']) * 100 if prev['close'] > 0 else 0

                    return {
                        'code': code,
                        'name': self.get_stock_name(symbol),
                        'market': 'A股',
                        'price': round(latest['close'], 2),
                        'change': round(price_change, 2),
                        'pct_change': round(pct_change, 2),
                        'open': round(latest['open'], 2),
                        'high': round(latest['high'], 2),
                        'low': round(latest['low'], 2),
                        'volume': int(latest['volume']),
                        'amount': round(latest['amount'] / 100000000, 2),  # 亿元
                        'turnover': round(latest['turnover'] * 100, 2),  # %
                        'date': str(latest.name)[:10],
                        'success': True
                    }
            elif market == 'hk':
                # 港股数据
                return {'success': False, 'message': '港股接口暂时不可用'}
            elif market == 'us':
                # 美股数据
                return {'success': False, 'message': '美股接口暂时不可用'}

        except Exception as e:
            return {'success': False, 'message': f'获取失败: {str(e)}'}

        return {'success': False, 'message': '未找到数据'}

    def get_basic_info(self, code: str) -> dict:
        """获取股票基本信息"""
        try:
            market, symbol = self.normalize_code(code)

            if market in ['sh', 'sz']:
                df = ak.stock_individual_info_em(symbol=symbol)
                if df is not None:
                    info = {}
                    for _, row in df.iterrows():
                        info[row['item']] = row['value']
                    return {
                        'success': True,
                        'data': info,
                        'name': info.get('股票简称', symbol)
                    }
        except Exception as e:
            return {'success': False, 'message': str(e)}

        return {'success': False, 'message': '获取基本信息失败'}

    def get_historical_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """获取历史数据"""
        try:
            market, symbol = self.normalize_code(code)

            if market in ['sh', 'sz']:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')

                df = ak.stock_zh_a_hist(symbol=symbol, period='daily',
                                       start_date=start_date, end_date=end_date)
                if df is not None and len(df) > 0:
                    return df

        except Exception:
            pass

        return pd.DataFrame()

    def calculate_technical_indicators(self, df: pd.DataFrame) -> dict:
        """计算技术指标"""
        if df.empty or len(df) < 20:
            return {}

        try:
            # 复制数据
            data = df.copy()

            # 计算均线
            data['MA5'] = data['收盘'].rolling(window=5).mean()
            data['MA10'] = data['收盘'].rolling(window=10).mean()
            data['MA20'] = data['收盘'].rolling(window=20).mean()
            data['MA60'] = data['收盘'].rolling(window=60).mean()

            # 计算RSI
            delta = data['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))

            # 计算KDJ
            low14 = data['最低'].rolling(window=14).min()
            high14 = data['最高'].rolling(window=14).max()
            rsv = (data['收盘'] - low14) / (high14 - low14) * 100
            data['K'] = rsv.ewm(com=2).mean()
            data['D'] = data['K'].ewm(com=2).mean()
            data['J'] = 3 * data['K'] - 2 * data['D']

            # 最新值
            latest = data.iloc[-1]

            return {
                'ma5': round(latest['MA5'], 2) if pd.notna(latest['MA5']) else None,
                'ma10': round(latest['MA10'], 2) if pd.notna(latest['MA10']) else None,
                'ma20': round(latest['MA20'], 2) if pd.notna(latest['MA20']) else None,
                'ma60': round(latest['MA60'], 2) if pd.notna(latest['MA60']) else None,
                'rsi': round(latest['RSI'], 2) if pd.notna(latest['RSI']) else None,
                'k': round(latest['K'], 2) if pd.notna(latest['K']) else None,
                'd': round(latest['D'], 2) if pd.notna(latest['D']) else None,
                'j': round(latest['J'], 2) if pd.notna(latest['J']) else None,
                'trend': self._get_trend(data),
                'signal': self._get_signal(data)
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_trend(self, data: pd.DataFrame) -> str:
        """判断趋势"""
        if len(data) < 20:
            return '数据不足'

        ma5 = data['MA5'].iloc[-1]
        ma20 = data['MA20'].iloc[-1]
        ma60 = data['MA60'].iloc[-1] if pd.notna(data['MA60'].iloc[-1]) else ma20

        if pd.notna(ma5) and pd.notna(ma20):
            if ma5 > ma20 > ma60:
                return '上升趋势'
            elif ma5 < ma20 < ma60:
                return '下降趋势'
            else:
                return '震荡整理'

        return '趋势不明'

    def _get_signal(self, data: pd.DataFrame) -> str:
        """判断信号"""
        if len(data) < 20:
            return '观望'

        latest = data.iloc[-1]

        # RSI判断
        rsi = latest['RSI'] if pd.notna(latest['RSI']) else 50

        # KDJ判断
        k = latest['K'] if pd.notna(latest['K']) else 50
        d = latest['D'] if pd.notna(latest['D']) else 50

        # 综合判断
        if rsi < 30 and k < 30:
            return '超卖，可能反弹'
        elif rsi > 70 and k > 70:
            return '超买，注意风险'
        elif k > d and k < 70:
            return '金叉，看涨'
        elif k < d and k > 30:
            return '死叉，看跌'
        else:
            return '中性观望'

    def get_news(self, code: str, limit: int = 5) -> list:
        """获取相关新闻"""
        try:
            _, symbol = self.normalize_code(code)
            if symbol.isdigit() and len(symbol) == 6:
                df = ak.stock_news_em(symbol=symbol)
                if df is not None and len(df) > 0:
                    return df.head(limit)[['关键证券', '新闻标题', '新闻内容', '发布日期']].to_dict('records')
        except Exception:
            pass

        return []

    def analyze(self, code: str) -> dict:
        """综合分析"""
        result = {
            'success': False,
            'code': code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 获取实时行情
        quote = self.get_realtime_quote(code)
        if quote.get('success'):
            result.update(quote)

        # 获取基本信息
        basic = self.get_basic_info(code)
        if basic.get('success'):
            result['basic_info'] = basic.get('data', {})

        # 获取历史数据和技术指标
        hist = self.get_historical_data(code, days=60)
        if not hist.empty:
            result['historical'] = {
                'count': len(hist),
                'latest_date': str(hist.index[-1])[:10] if hasattr(hist.index[-1], 'year') else str(hist.iloc[-1]['日期'])[:10]
            }
            result['technical'] = self.calculate_technical_indicators(hist)

        # 获取新闻
        news = self.get_news(code)
        if news:
            result['news'] = news[:3]

        # 生成投资建议
        if result.get('success'):
            result['suggestion'] = self._generate_suggestion(result)

        result['success'] = True
        return result

    def _generate_suggestion(self, data: dict) -> dict:
        """生成投资建议"""
        score = 50  # 基础分

        # 根据涨跌幅调整
        pct = data.get('pct_change', 0)
        if pct > 3:
            score -= 15  # 涨幅过大减分
        elif pct < -3:
            score += 10  # 跌幅过大可能反弹

        # 根据技术指标调整
        tech = data.get('technical', {})
        trend = tech.get('trend', '')
        signal = tech.get('signal', '')

        if '上升' in trend:
            score += 15
        elif '下降' in trend:
            score -= 15

        if '看涨' in signal:
            score += 10
        elif '看跌' in signal:
            score -= 10

        # RSI调整
        rsi = tech.get('rsi', 50)
        if rsi < 30:
            score += 10  # 超卖
        elif rsi > 70:
            score -= 10  # 超买

        # 确保分数在0-100之间
        score = max(0, min(100, score))

        # 生成建议
        if score >= 70:
            action = '买入'
            level = '积极'
        elif score >= 50:
            action = '观望'
            level = '谨慎'
        else:
            action = '卖出'
            level = '风险'

        # 计算目标价和止损价
        price = data.get('price', 0)
        if price > 0:
            target = round(price * 1.1, 2)  # 10%上涨目标
            stop = round(price * 0.95, 2)   # 5%止损
        else:
            target = stop = 0

        return {
            'score': score,
            'action': action,
            'level': level,
            'target_price': target,
            'stop_loss': stop,
            'position': f'{min(20, max(5, score // 5))}%'
        }


def main():
    """主函数"""
    import json

    if len(sys.argv) < 2:
        print(json.dumps({'error': '请提供股票代码'}, ensure_ascii=False))
        return

    code = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else 'analyze'

    analyzer = StockAnalyzer()

    if action == 'quote':
        result = analyzer.get_realtime_quote(code)
    elif action == 'basic':
        result = analyzer.get_basic_info(code)
    elif action == 'news':
        result = {'success': True, 'news': analyzer.get_news(code)}
    else:
        result = analyzer.analyze(code)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
