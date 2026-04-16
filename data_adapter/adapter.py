# -*- coding: utf-8 -*-
"""
数据适配器核心模块

将各种数据源的原始数据转换为 stock-analyst 需要的标准格式
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAdapter:
    """
    数据适配器
    
    职责：
    1. 接收各种数据源的原始数据
    2. 转换为 stock-analyst 需要的标准格式
    3. 数据校验和补全
    4. 多源数据融合（主源失败时使用备用源）
    """
    
    def __init__(self, primary_source='akshare', fallback_sources=None):
        """
        初始化适配器
        
        Args:
            primary_source: 主数据源名称
            fallback_sources: 备用数据源列表
        """
        self.primary_source = primary_source
        self.fallback_sources = fallback_sources or []
        self.cache = {}  # 简单内存缓存
        
    def get_complete_data(self, code: str, stock_name: str = '') -> Tuple[Dict, Optional[Dict]]:
        """
        获取完整的分析数据（一站式接口）
        
        Args:
            code: 股票代码
            stock_name: 股票名称（可选）
            
        Returns:
            (data, pattern_data): 基础数据和形态面数据
        """
        logger.info(f"开始获取 {code} 的完整数据...")
        
        try:
            # 1. 获取行情数据
            quote = self._get_quote_data(code)
            
            # 2. 获取K线数据（用于技术指标和形态面）
            klines = self._get_kline_data(code)
            
            # 3. 计算技术指标
            technical = self._calculate_technical_indicators(klines) if klines else {}
            
            # 4. 获取财务数据
            fundamental = self._get_fundamental_data(code)
            
            # 5. 获取资金流向
            money_flow = self._get_money_flow_data(code)
            
            # 6. 获取新闻数据
            news = self._get_news_data(code)
            
            # 7. 生成综合建议
            suggestion = self._generate_suggestion(
                quote, technical, fundamental, money_flow
            )
            
            # 组装基础数据
            data = {
                'code': code,
                'stock_name': stock_name or quote.get('stock_name', ''),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'quote': quote,
                'technical': technical,
                'fundamental': fundamental,
                'news': news,
                'money_flow': money_flow,
                'suggestion': suggestion
            }
            
            # 8. 形态面分析（需要K线数据）
            pattern_data = None
            if klines:
                pattern_data = self._analyze_patterns(klines, technical)
            
            logger.info(f"{code} 数据获取完成")
            return data, pattern_data
            
        except Exception as e:
            logger.error(f"获取 {code} 数据失败: {e}")
            # 返回最小化数据
            return self._get_minimal_data(code, stock_name), None
    
    def _get_quote_data(self, code: str) -> Dict:
        """获取行情数据"""
        # 这里调用 finance-data-retrieval 的接口
        # 返回模拟数据（实际使用时应替换为真实数据）
        return {
            'price': 31.91,
            'pct_change': 1.88,
            'volume': 2690000,
            'amount': 8.58,
            'turnover': 3.31,
            'open': 31.35,
            'high': 32.15,
            'low': 31.20,
            'prev_close': 31.32,
            'pe': 80.99,
            'pb': 5.62,
            'market_cap': 295.0
        }
    
    def _get_kline_data(self, code: str) -> Optional[List[Dict]]:
        """
        获取K线数据
        
        返回: [{date, open, high, low, close, volume}, ...]
        """
        try:
            # 调用 finance-data-retrieval 获取日线数据
            # 需要最近60-120天的数据用于形态识别
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            # 这里应该调用实际的接口
            # klines = finance_data_retrieval.get_daily_data(
            #     code, 
            #     start_date=start_date.strftime('%Y%m%d'),
            #     end_date=end_date.strftime('%Y%m%d')
            # )
            
            # 示例：返回模拟数据
            klines = self._generate_sample_klines()
            return klines
            
        except Exception as e:
            logger.warning(f"获取K线数据失败: {e}")
            return None
    
    def _calculate_technical_indicators(self, klines: List[Dict]) -> Dict:
        """
        基于K线计算技术指标
        
        Args:
            klines: K线数据列表
            
        Returns:
            技术指标字典
        """
        df = pd.DataFrame(klines)
        
        # 确保数据足够
        if len(df) < 60:
            logger.warning(f"K线数据不足: {len(df)} < 60")
            return {}
        
        # KDJ计算
        n = 9
        low_list = df['low'].rolling(window=n, min_periods=n).min()
        high_list = df['high'].rolling(window=n, min_periods=n).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d
        
        # MACD计算
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        # RSI计算
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 布林带
        ma20 = df['close'].rolling(20).mean()
        std20 = df['close'].rolling(20).std()
        bb_upper = ma20 + 2 * std20
        bb_lower = ma20 - 2 * std20
        
        # 均线
        ma5 = df['close'].rolling(5).mean()
        ma10 = df['close'].rolling(10).mean()
        ma60 = df['close'].rolling(60).mean()
        
        latest = -1
        prev = -2
        
        # 判断信号
        kdj_signal = '金叉' if k.iloc[latest] > d.iloc[latest] and k.iloc[prev] <= d.iloc[prev] else \
                     '死叉' if k.iloc[latest] < d.iloc[latest] and k.iloc[prev] >= d.iloc[prev] else '正常'
        
        macd_signal = '多头' if macd_line.iloc[latest] > 0 else '空头'
        rsi_signal = '超买' if rsi.iloc[latest] > 70 else '超卖' if rsi.iloc[latest] < 30 else '正常'
        
        close_price = df['close'].iloc[latest]
        trend = '上升趋势' if close_price > ma20.iloc[latest] > ma60.iloc[latest] else \
                '下降趋势' if close_price < ma20.iloc[latest] < ma60.iloc[latest] else '震荡'
        
        ma_alignment = '多头排列' if ma5.iloc[latest] > ma10.iloc[latest] > ma20.iloc[latest] else \
                       '空头排列' if ma5.iloc[latest] < ma10.iloc[latest] < ma20.iloc[latest] else '纠缠'
        
        return {
            'k': round(k.iloc[latest], 2),
            'd': round(d.iloc[latest], 2),
            'j': round(j.iloc[latest], 2),
            'kdj_signal': kdj_signal,
            'macd': round(macd_line.iloc[latest], 4),
            'dea': round(signal_line.iloc[latest], 4),
            'histogram': round(histogram.iloc[latest], 4),
            'macd_signal': macd_signal,
            'rsi': round(rsi.iloc[latest], 2),
            'rsi_signal': rsi_signal,
            'ma5': round(ma5.iloc[latest], 2),
            'ma10': round(ma10.iloc[latest], 2),
            'ma20': round(ma20.iloc[latest], 2),
            'ma60': round(ma60.iloc[latest], 2),
            'price_above_ma5': close_price > ma5.iloc[latest],
            'price_above_ma20': close_price > ma20.iloc[latest],
            'price_above_ma60': close_price > ma60.iloc[latest],
            'bb_upper': round(bb_upper.iloc[latest], 2),
            'bb_middle': round(ma20.iloc[latest], 2),
            'bb_lower': round(bb_lower.iloc[latest], 2),
            'trend': trend,
            'ma_alignment': ma_alignment
        }
    
    def _get_fundamental_data(self, code: str) -> Dict:
        """获取财务数据"""
        try:
            # 调用 finance-data-retrieval 获取财务数据
            # income = finance_data_retrieval.get_income(code)
            # balance = finance_data_retrieval.get_balance_sheet(code)
            
            # 示例：返回模拟数据
            return {
                'financial': {
                    'latest': {
                        'report_date': '2025-12-31',
                        'revenue': '50.5亿',
                        'revenue_yoy': '+15.2%',
                        'net_profit': '3.2亿',
                        'net_profit_yoy': '+8.5%',
                        'roe': '8.5%',
                        'gross_margin': '22%',
                        'net_margin': '6.3%',
                        'debt_ratio': '45%',
                        'eps': '0.35',
                        'ocf_ps': '0.42',
                        'pe': '80.99',
                        'pb': '5.62',
                        'pe_percentile': '75%',
                        'pb_percentile': '60%'
                    },
                    'history': [
                        {'report_date': '2025-09-30', 'revenue': '35.2亿', 'net_profit': '2.1亿'},
                        {'report_date': '2025-06-30', 'revenue': '22.8亿', 'net_profit': '1.3亿'},
                        {'report_date': '2025-03-31', 'revenue': '10.5亿', 'net_profit': '0.6亿'},
                    ]
                },
                'performance_trend': {
                    'overall_trend': '稳健增长',
                    'revenue_trend': '持续增长',
                    'profit_trend': '增速放缓'
                },
                'industry': '电子元器件',
                'business_segments': [
                    {'name': '智能控制器', 'revenue_pct': 75, 'growth': '+18%', 'margin': '20%'},
                    {'name': '射频芯片', 'revenue_pct': 20, 'growth': '+25%', 'margin': '35%'},
                    {'name': '其他', 'revenue_pct': 5, 'growth': '-5%', 'margin': '10%'}
                ]
            }
        except Exception as e:
            logger.warning(f"获取财务数据失败: {e}")
            return {}
    
    def _get_money_flow_data(self, code: str) -> Dict:
        """获取资金流向数据"""
        try:
            # 调用 finance-data-retrieval 获取资金流向
            # 需要最近20个交易日的数据
            
            return {
                'data_date': '最近20个交易日',
                'data_range': '20日',
                'main_flow': {
                    'main_net': 5.2,
                    'main_in': 12.5,
                    'main_out': 7.3,
                    'trend': '持续流入'
                },
                'retail_flow': {
                    'retail_net': -2.1
                },
                'north_flow': {
                    'north_net': 3.8,
                    'trend': '流入加速'
                },
                'flow_20d': [
                    {'date': '04-16', 'main_net': 0.8, 'retail_net': -0.3},
                    {'date': '04-15', 'main_net': 0.5, 'retail_net': -0.2},
                    {'date': '04-14', 'main_net': 0.6, 'retail_net': -0.1},
                ]
            }
        except Exception as e:
            logger.warning(f"获取资金流向失败: {e}")
            return {}
    
    def _get_news_data(self, code: str) -> Dict:
        """获取新闻数据"""
        try:
            # 调用 finance-data-retrieval 或外部API获取新闻
            
            return {
                'sentiment': '中性偏正面',
                'sentiment_score': 65,
                'fundamental_impact': '中性',
                'items': [
                    {
                        'title': '和而泰发布一季度业绩预告',
                        'date': '2026-04-10',
                        'source': '证券时报',
                        'sentiment': '正面'
                    },
                    {
                        'title': '电子元器件行业景气度回升',
                        'date': '2026-04-08',
                        'source': '上海证券报',
                        'sentiment': '正面'
                    }
                ],
                'key_events': [
                    '4月10日发布一季度业绩预告',
                    '智能控制器业务订单饱满'
                ]
            }
        except Exception as e:
            logger.warning(f"获取新闻数据失败: {e}")
            return {}
    
    def _analyze_patterns(self, klines: List[Dict], technical: Dict) -> Dict:
        """
        形态面分析
        
        调用 patterns 模块进行分析
        """
        try:
            from patterns.candlestick import analyze_candlestick_patterns
            from patterns.chanlun import ChanlunAnalyzer
            from signals.scoring import SignalResonanceScorer
            from ai_models.sentiment_index import SentimentIndexCalculator
            import pandas as pd
            
            if not klines or len(klines) < 20:
                logger.warning(f"K线数据不足，无法进行形态分析 (当前{len(klines)}根)")
                return None
            
            # 将K线数据转换为DataFrame
            df = pd.DataFrame(klines)
            
            # 确保必要的列存在
            required_cols = ['open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"K线数据缺少必要列: {df.columns.tolist()}")
                return None
            
            # K线形态识别
            candlestick = analyze_candlestick_patterns(df)
            
            # 缠论分析 (传入DataFrame而不是列表)
            chanlun = ChanlunAnalyzer().analyze(df)
            
            # 信号共振评分 - 构建信号列表
            signals = []
            
            # 从K线形态提取信号
            if candlestick and 'patterns' in candlestick:
                for pattern in candlestick['patterns']:
                    from signals.scoring import Signal, SignalType, SignalDirection
                    from patterns.candlestick import PatternType
                    direction = SignalDirection.BULLISH if pattern.pattern_type == PatternType.BULLISH else SignalDirection.BEARISH
                    signals.append(Signal(
                        signal_type=SignalType.CANDLESTICK,
                        direction=direction,
                        strength=pattern.reliability / 5.0,
                        description=pattern.name_cn,
                        weight=1.0
                    ))
            
            # 从缠论提取信号
            if chanlun and 'signals' in chanlun:
                for signal in chanlun['signals']:
                    from signals.scoring import Signal, SignalType, SignalDirection
                    direction = SignalDirection.BULLISH if '买' in signal.get('type', '') else SignalDirection.BEARISH
                    signals.append(Signal(
                        signal_type=SignalType.CHANLUN,
                        direction=direction,
                        strength=0.8,
                        description=signal.get('type', ''),
                        weight=1.0
                    ))
            
            # 从技术指标提取信号
            if technical:
                from signals.scoring import Signal, SignalType, SignalDirection
                # KDJ信号
                if technical.get('j', 50) > 80:
                    signals.append(Signal(SignalType.TECHNICAL, SignalDirection.BEARISH, 0.7, 'KDJ超买', 1.0))
                elif technical.get('j', 50) < 20:
                    signals.append(Signal(SignalType.TECHNICAL, SignalDirection.BULLISH, 0.7, 'KDJ超卖', 1.0))
                
                # MACD信号
                if technical.get('macd', 0) > 0:
                    signals.append(Signal(SignalType.TECHNICAL, SignalDirection.BULLISH, 0.6, 'MACD多头', 1.0))
                else:
                    signals.append(Signal(SignalType.TECHNICAL, SignalDirection.BEARISH, 0.6, 'MACD空头', 1.0))
            
            resonance = SignalResonanceScorer().calculate_resonance(signals)
            
            # 情绪指数 (传入DataFrame)
            sentiment = SentimentIndexCalculator().calculate(df)
            
            return {
                'data_date': datetime.now().strftime('%Y-%m-%d'),
                'data_source': '日线数据',
                'kline_count': len(klines),
                'validation': {
                    'kline_data': True,
                    'pattern_recognition': True,
                    'chanlun_analysis': True
                },
                'candlestick': candlestick,
                'chanlun': chanlun,
                'resonance': resonance,
                'sentiment': sentiment
            }
            
        except Exception as e:
            logger.error(f"形态面分析失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_suggestion(self, quote: Dict, technical: Dict, 
                            fundamental: Dict, money_flow: Dict) -> Dict:
        """生成综合建议"""
        # 简化的评分逻辑
        score = 50  # 基准分
        
        # 技术面评分
        if technical.get('trend') == '上升趋势':
            score += 10
        if '金叉' in technical.get('kdj_signal', ''):
            score += 5
        if technical.get('rsi', 50) < 70:
            score += 5
            
        # 资金面评分
        main_net = money_flow.get('main_flow', {}).get('main_net', 0)
        if main_net > 0:
            score += 10
        elif main_net < 0:
            score -= 10
            
        # 基本面评分（简化）
        pe = quote.get('pe', 0)
        if pe > 0 and pe < 30:
            score += 10
        elif pe > 80:
            score -= 10
        
        # 确定评级
        if score >= 80:
            rating, action = '强烈买入', '强烈买入'
        elif score >= 65:
            rating, action = '买入', '买入'
        elif score >= 50:
            rating, action = '中性', '观望'
        elif score >= 35:
            rating, action = '谨慎', '减仓'
        else:
            rating, action = '卖出', '卖出'
        
        price = quote.get('price', 0)
        
        return {
            'total_score': score,
            'action': action,
            'target_price': round(price * 1.1, 2) if price > 0 else 0,
            'stop_loss': round(price * 0.92, 2) if price > 0 else 0,
            'position': '50%' if score >= 65 else '30%' if score >= 50 else '10%',
            'level': '中等' if 40 <= score <= 70 else '高' if score > 70 else '低'
        }
    
    def _get_minimal_data(self, code: str, stock_name: str) -> Dict:
        """获取最小化数据（当主流程失败时）"""
        return {
            'code': code,
            'stock_name': stock_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'quote': {},
            'technical': {},
            'fundamental': {},
            'news': {},
            'money_flow': {},
            'suggestion': {
                'total_score': 0,
                'action': '数据获取失败',
                'target_price': 0,
                'stop_loss': 0,
                'position': '0%',
                'level': '未知'
            }
        }
    
    def _generate_sample_klines(self) -> List[Dict]:
        """生成示例K线数据（用于测试）"""
        # 这里应该返回真实的K线数据
        # 实际使用时删除此方法
        import random
        
        klines = []
        base_price = 30.0
        
        for i in range(100):
            change = random.uniform(-0.03, 0.03)
            close = base_price * (1 + change)
            high = close * (1 + random.uniform(0, 0.02))
            low = close * (1 - random.uniform(0, 0.02))
            open_price = base_price * (1 + random.uniform(-0.01, 0.01))
            volume = random.randint(1000000, 5000000)
            
            date = (datetime.now() - timedelta(days=100-i)).strftime('%Y-%m-%d')
            
            klines.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
            
            base_price = close
        
        return klines


# 便捷函数
def get_stock_analysis_data(code: str, stock_name: str = '') -> Tuple[Dict, Optional[Dict]]:
    """
    一键获取股票分析数据的便捷函数
    
    Args:
        code: 股票代码
        stock_name: 股票名称
        
    Returns:
        (data, pattern_data): 可直接传入报告模板的数据
    """
    adapter = DataAdapter()
    return adapter.get_complete_data(code, stock_name)
