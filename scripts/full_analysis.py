# -*- coding: utf-8 -*-
"""
完整的股票分析报告生成 - 增强版
包含：行情、技术面、基本面、消息面、资金面
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

class StockFullAnalyzer:
    """股票全面分析器"""

    # A股股票名称映射表
    STOCK_NAMES = {
        '000001': '平安银行', '600519': '贵州茅台', '600036': '招商银行',
        '000002': '万科A', '000858': '五粮液', '600887': '伊利股份',
        '000333': '美的集团', '002475': '立讯精密', '601318': '中国平安',
        '601166': '兴业银行', '600276': '恒瑞医药', '300750': '宁德时代',
        '002149': '西部材料', '600309': '万华化学', '600585': '海螺水泥',
        '002415': '海康威视', '000568': '泸州老窖', '000661': '长春高新',
        '600900': '长江电力', '601012': '隆基绿能', '002594': '比亚迪',
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
            result['stock_name'] = self.get_stock_name(symbol)

            # ========== 1. 行情数据 ==========
            result['quote'] = self._get_quote(market, symbol)

            # ========== 2. 技术分析 ==========
            result['technical'] = self._get_technical_analysis(market, symbol)

            # ========== 3. 基本面分析 ==========
            result['fundamental'] = self._get_fundamental_analysis(symbol)

            # ========== 4. 消息面分析 ==========
            result['news'] = self._get_news_analysis(symbol)

            # ========== 5. 资金面分析 ==========
            result['money_flow'] = self._get_money_flow(symbol)

            # ========== 6. 综合建议 ==========
            result['suggestion'] = self._generate_suggestion(result)

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)
            import traceback
            result['trace'] = str(traceback.format_exc())[:500]

        return result

    def _get_quote(self, market: str, symbol: str) -> dict:
        """获取行情数据"""
        try:
            hist = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
            if hist is not None and len(hist) > 0:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest
                
                close_col = self._safe_get_column(hist, 'close', '收盘')
                open_col = self._safe_get_column(hist, 'open', '开盘')
                high_col = self._safe_get_column(hist, 'high', '最高')
                low_col = self._safe_get_column(hist, 'low', '最低')
                vol_col = self._safe_get_column(hist, 'volume', '成交量')
                amount_col = self._safe_get_column(hist, 'amount', '成交额')
                turnover_col = self._safe_get_column(hist, 'turnover', '换手率')

                price = float(latest[close_col])
                prev_price = float(prev[close_col])
                
                return {
                    'price': price,
                    'change': round(price - prev_price, 2),
                    'pct_change': round((price - prev_price) / prev_price * 100, 2),
                    'open': float(latest[open_col]),
                    'high': float(latest[high_col]),
                    'low': float(latest[low_col]),
                    'volume': int(latest[vol_col]),
                    'amount': round(float(latest[amount_col]) / 100000000, 2),
                    'turnover': round(float(latest.get(turnover_col, 0)) * 100, 2),
                    'date': str(latest.name)[:10] if hasattr(latest.name, 'year') else 'N/A'
                }
        except Exception as e:
            return {'error': str(e)}
        return {'error': '无法获取行情数据'}

    def _get_technical_analysis(self, market: str, symbol: str) -> dict:
        """获取技术分析"""
        try:
            hist = ak.stock_zh_a_daily(symbol=f'{market}{symbol}', adjust='qfq')
            if hist is None or len(hist) < 30:
                return {'error': '数据不足'}

            # 统一列名
            hist = hist.rename(columns={
                self._safe_get_column(hist, 'close', '收盘'): 'close',
                self._safe_get_column(hist, 'open', '开盘'): 'open',
                self._safe_get_column(hist, 'high', '最高'): 'high',
                self._safe_get_column(hist, 'low', '最低'): 'low',
                self._safe_get_column(hist, 'volume', '成交量'): 'volume',
            })

            # 计算均线
            for period in [5, 10, 20, 60]:
                hist[f'ma{period}'] = hist['close'].rolling(window=period).mean()

            # RSI
            delta = hist['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist['rsi'] = 100 - (100 / (1 + rs))

            # KDJ
            low9 = hist['low'].rolling(window=9).min()
            high9 = hist['high'].rolling(window=9).max()
            rsv = (hist['close'] - low9) / (high9 - low9) * 100
            hist['k'] = rsv.ewm(com=2).mean()
            hist['d'] = hist['k'].ewm(com=2).mean()
            hist['j'] = 3 * hist['k'] - 2 * hist['d']

            # MACD
            exp12 = hist['close'].ewm(span=12, adjust=False).mean()
            exp26 = hist['close'].ewm(span=26, adjust=False).mean()
            hist['macd'] = exp12 - exp26
            hist['signal'] = hist['macd'].ewm(span=9, adjust=False).mean()
            hist['histogram'] = hist['macd'] - hist['signal']

            latest = hist.iloc[-1]

            # 趋势判断
            ma5 = latest['ma5']
            ma20 = latest['ma20']
            ma60 = latest['ma60'] if pd.notna(latest.get('ma60')) else ma20
            price = latest['close']

            if ma5 > ma20 > ma60:
                trend = '上升趋势'
                trend_score = 20
            elif ma5 < ma20 < ma60:
                trend = '下降趋势'
                trend_score = -20
            elif ma5 > ma20:
                trend = '震荡偏强'
                trend_score = 10
            else:
                trend = '震荡偏弱'
                trend_score = -10

            # KDJ信号
            k = latest['k']
            d = latest['d']
            if k > 80:
                kdj_signal = '超买区'
                kdj_score = -15
            elif k < 20:
                kdj_signal = '超卖区'
                kdj_score = 15
            elif k > d:
                kdj_signal = '金叉'
                kdj_score = 5
            else:
                kdj_signal = '死叉'
                kdj_score = -5

            # RSI信号
            rsi = latest['rsi']
            if rsi > 70:
                rsi_signal = '超买'
                rsi_score = -10
            elif rsi < 30:
                rsi_signal = '超卖'
                rsi_score = 10
            else:
                rsi_signal = '正常'
                rsi_score = 0

            # MACD信号
            macd = latest['macd']
            signal = latest['signal']
            if macd > signal and macd > 0:
                macd_signal = '多头'
                macd_score = 10
            elif macd < signal and macd < 0:
                macd_signal = '空头'
                macd_score = -10
            else:
                macd_signal = '盘整'
                macd_score = 0

            return {
                'ma5': round(float(ma5), 2),
                'ma10': round(float(latest['ma10']), 2),
                'ma20': round(float(ma20), 2),
                'ma60': round(float(ma60), 2) if pd.notna(latest.get('ma60')) else None,
                'price_above_ma5': bool(price > ma5),
                'price_above_ma20': bool(price > ma20),
                'price_above_ma60': bool(price > ma60),
                'rsi': round(float(rsi), 2),
                'rsi_signal': rsi_signal,
                'k': round(float(k), 2),
                'd': round(float(d), 2),
                'j': round(float(latest['j']), 2),
                'kdj_signal': kdj_signal,
                'macd': round(float(macd), 2),
                'macd_signal': macd_signal,
                'histogram': round(float(latest['histogram']), 2),
                'trend': trend,
                'scores': {
                    'trend': trend_score,
                    'kdj': kdj_score,
                    'rsi': rsi_score,
                    'macd': macd_score
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_fundamental_analysis(self, symbol: str) -> dict:
        """获取基本面分析"""
        fundamental = {}

        # 1. 基本信息
        try:
            info_df = ak.stock_individual_info_em(symbol=symbol)
            if info_df is not None and len(info_df) > 0:
                fundamental['info'] = {}
                for _, row in info_df.iterrows():
                    item = str(row['item'])
                    value = str(row['value'])
                    fundamental['info'][item] = value
        except Exception as e:
            fundamental['info_error'] = str(e)

        # 2. 财务指标
        try:
            finance_df = ak.stock_financial_analysis_indicator(symbol=symbol, start_date='20250101')
            if finance_df is not None and len(finance_df) > 0:
                latest = finance_df.iloc[-1]
                fundamental['financial'] = {
                    '净资产收益率ROE': round(float(latest.get('净资产收益率(%)', 0)), 2),
                    '销售毛利率': round(float(latest.get('销售毛利率(%)', 0)), 2),
                    '销售净利率': round(float(latest.get('销售净利率(%)', 0)), 2),
                    '资产负债率': round(float(latest.get('资产负债率(%)', 0)), 2),
                    '存货周转率': round(float(latest.get('存货周转率(次)', 0)), 2),
                }
        except Exception as e:
            fundamental['financial_error'] = str(e)

        # 3. 估值分析
        try:
            hist = ak.stock_zh_a_daily(symbol=f'sz{symbol}' if not symbol.startswith('6') else f'sh{symbol}', adjust='qfq')
            if hist is not None and len(hist) >= 250:
                # 计算近一年涨跌幅
                year_start = hist.iloc[-250]['close']
                year_end = hist.iloc[-1]['close']
                ytd_return = round((year_end - year_start) / year_start * 100, 2)
                
                # 计算波动率
                returns = hist['close'].pct_change().dropna()
                volatility = round(float(returns.std() * np.sqrt(250) * 100), 2)
                
                fundamental['valuation'] = {
                    '近一年涨跌幅': ytd_return,
                    '年化波动率': volatility,
                    '近一年最高': round(float(hist['close'].max()), 2),
                    '近一年最低': round(float(hist['close'].min()), 2),
                }
        except Exception as e:
            fundamental['valuation_error'] = str(e)

        # 综合基本面评分
        fund_score = 50
        fund_reasons = []

        if 'financial' in fundamental:
            fin = fundamental['financial']
            roe = fin.get('净资产收益率ROE', 0)
            if roe > 15:
                fund_score += 15
                fund_reasons.append(f'ROE较高({roe}%)')
            elif roe > 10:
                fund_score += 5
                fund_reasons.append(f'ROE良好({roe}%)')
            elif roe < 5:
                fund_score -= 10
                fund_reasons.append(f'ROE偏低({roe}%)')

        fundamental['score'] = max(0, min(100, fund_score))
        fundamental['reasons'] = fund_reasons

        return fundamental

    def _get_news_analysis(self, symbol: str) -> dict:
        """获取消息面分析"""
        news_data = {'items': [], 'summary': ''}

        try:
            news_df = ak.stock_news_em(symbol=symbol)
            if news_df is not None and len(news_df) > 0:
                for idx, row in news_df.head(10).iterrows():
                    title = str(row.get('新闻标题', ''))
                    content = str(row.get('新闻内容', ''))[:300]
                    news_data['items'].append({
                        'title': title,
                        'content': content,
                        'date': str(row.get('发布日期', ''))
                    })
        except Exception as e:
            news_data['error'] = str(e)

        # 情感分析（简单关键词匹配）
        sentiment_score = 0
        positive_keywords = ['增长', '盈利', '突破', '创新', '扩张', '合作', '增持', '买入', '看好', '上调', '超预期']
        negative_keywords = ['下跌', '亏损', '风险', '减持', '卖出', '下调', '不及预期', '警告', '调查', '诉讼']

        all_text = ' '.join([n.get('title', '') + ' ' + n.get('content', '') for n in news_data['items']])
        
        for kw in positive_keywords:
            sentiment_score += all_text.count(kw) * 2
        for kw in negative_keywords:
            sentiment_score -= all_text.count(kw) * 2

        news_data['sentiment'] = '偏多' if sentiment_score > 5 else ('偏空' if sentiment_score < -5 else '中性')
        news_data['sentiment_score'] = sentiment_score

        return news_data

    def _get_money_flow(self, symbol: str) -> dict:
        """获取资金流向"""
        money_flow = {}

        try:
            # 主力资金流向
            df = ak.stock_individual_fund_flow(stock=symbol, market='sh' if symbol.startswith('6') else 'sz')
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                money_flow['main_flow'] = {
                    'date': str(latest.get('日期', ''))[:10],
                    'main_net': float(latest.get('主力净流入', 0)) / 100000000,
                    'main_pct': float(latest.get('主力净流入占比(%)', 0)),
                    'retail_net': float(latest.get('散户净流入', 0)) / 100000000,
                }
        except Exception as e:
            money_flow['flow_error'] = str(e)

        # 简单评分
        flow_score = 0
        if 'main_flow' in money_flow:
            net_flow = money_flow['main_flow'].get('main_net', 0)
            if net_flow > 0:
                flow_score += 10
            else:
                flow_score -= 10

        money_flow['score'] = max(0, min(100, 50 + flow_score))

        return money_flow

    def _generate_suggestion(self, result: dict) -> dict:
        """生成综合投资建议"""
        # 计算总分
        total_score = 50  # 基础分

        # 技术面评分
        tech = result.get('technical', {})
        if 'scores' in tech:
            scores = tech['scores']
            total_score += scores.get('trend', 0)
            total_score += scores.get('kdj', 0)
            total_score += scores.get('rsi', 0)
            total_score += scores.get('macd', 0)

        # 基本面评分
        fund = result.get('fundamental', {})
        if 'score' in fund:
            total_score += (fund['score'] - 50) * 0.5  # 权重0.5

        # 资金面评分
        money = result.get('money_flow', {})
        if 'score' in money:
            total_score += (money['score'] - 50) * 0.3  # 权重0.3

        # 消息面评分
        news = result.get('news', {})
        sentiment = news.get('sentiment', '中性')
        if sentiment == '偏多':
            total_score += 5
        elif sentiment == '偏空':
            total_score -= 5

        total_score = max(0, min(100, round(total_score)))

        # 生成建议
        if total_score >= 70:
            action, level = '积极买入', '积极'
        elif total_score >= 55:
            action, level = '适量买入', '谨慎乐观'
        elif total_score >= 45:
            action, level = '观望', '谨慎'
        elif total_score >= 30:
            action, level = '谨慎卖出', '风险'
        else:
            action, level = '建议卖出', '高风险'

        price = result.get('quote', {}).get('price', 0)
        return {
            'total_score': total_score,
            'action': action,
            'level': level,
            'target_price': round(price * 1.10, 2) if price > 0 else 0,
            'stop_loss': round(price * 0.95, 2) if price > 0 else 0,
            'position': f'{min(30, max(5, total_score // 3))}%',
            'tech_weight': 0.5,
            'fund_weight': 0.3,
            'money_weight': 0.2
        }


def main():
    import json

    if len(sys.argv) < 2:
        print(json.dumps({'error': '请提供股票代码'}, ensure_ascii=False, indent=2))
        return

    code = sys.argv[1]
    analyzer = StockFullAnalyzer()
    result = analyzer.get_full_analysis(code)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
