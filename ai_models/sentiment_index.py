"""
情绪指数计算模块
基于成交量、波动率、涨跌幅等指标计算市场情绪
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class SentimentLevel(Enum):
    """情绪等级"""
    EXTREME_FEAR = "极度恐慌"
    FEAR = "恐慌"
    NEUTRAL = "中性"
    GREED = "贪婪"
    EXTREME_GREED = "极度贪婪"


@dataclass
class SentimentResult:
    """情绪分析结果"""
    index_value: float  # 0-100
    level: SentimentLevel
    description: str
    components: Dict[str, float]
    trend: str  # 上升/下降/平稳
    signal: str  # 买入/卖出/观望


class SentimentIndexCalculator:
    """情绪指数计算器"""
    
    def __init__(self):
        # 情绪等级阈值
        self.level_thresholds = {
            SentimentLevel.EXTREME_FEAR: (0, 20),
            SentimentLevel.FEAR: (20, 40),
            SentimentLevel.NEUTRAL: (40, 60),
            SentimentLevel.GREED: (60, 80),
            SentimentLevel.EXTREME_GREED: (80, 100)
        }
    
    def calculate(self, df: pd.DataFrame, market_data: Dict = None) -> SentimentResult:
        """
        计算情绪指数
        
        Args:
            df: 包含open, high, low, close, volume的DataFrame
            market_data: 市场数据（如换手率、融资余额等）
            
        Returns:
            情绪分析结果
        """
        components = {}
        
        # 1. 价格波动情绪 (0-25分)
        components['price_volatility'] = self._calc_price_sentiment(df)
        
        # 2. 成交量情绪 (0-25分)
        components['volume_sentiment'] = self._calc_volume_sentiment(df)
        
        # 3. 涨跌情绪 (0-25分)
        components['momentum_sentiment'] = self._calc_momentum_sentiment(df)
        
        # 4. 技术情绪 (0-25分)
        components['technical_sentiment'] = self._calc_technical_sentiment(df)
        
        # 计算综合指数
        index_value = sum(components.values())
        index_value = max(0, min(100, index_value))  # 限制在0-100
        
        # 确定情绪等级
        level = self._get_sentiment_level(index_value)
        
        # 判断趋势
        trend = self._get_sentiment_trend(df)
        
        # 生成交易信号
        signal = self._generate_signal(index_value, trend)
        
        # 生成描述
        description = self._generate_description(index_value, level, components)
        
        return SentimentResult(
            index_value=round(index_value, 2),
            level=level,
            description=description,
            components={k: round(v, 2) for k, v in components.items()},
            trend=trend,
            signal=signal
        )
    
    def _calc_price_sentiment(self, df: pd.DataFrame) -> float:
        """计算价格波动情绪 (0-25分)"""
        if len(df) < 20:
            return 50
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # 计算ATR（平均真实波幅）
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr = pd.Series(tr).rolling(window=14).mean().iloc[-1] if len(tr) >= 14 else np.mean(tr)
        
        # 计算当前价格相对位置
        price_range = high[-20:].max() - low[-20:].min()
        if price_range == 0:
            return 50
        
        current_position = (close[-1] - low[-20:].min()) / price_range
        
        # 波动率越大，情绪越极端
        volatility_score = min(25, atr / close[-1] * 100 * 10)
        
        # 价格在高位 = 贪婪，低位 = 恐慌
        position_score = current_position * 25
        
        # 综合：高位高波动 = 极度贪婪，低位高波动 = 极度恐慌
        if current_position > 0.7:
            return 50 + volatility_score * 0.5 + position_score * 0.5
        elif current_position < 0.3:
            return 50 - volatility_score * 0.5 - (25 - position_score) * 0.5
        else:
            return 50 + (position_score - 12.5)
    
    def _calc_volume_sentiment(self, df: pd.DataFrame) -> float:
        """计算成交量情绪 (0-25分)"""
        if 'volume' not in df.columns or len(df) < 20:
            return 50
        
        volume = df['volume'].values
        close = df['close'].values
        
        # 成交量均值
        vol_ma20 = pd.Series(volume).rolling(window=20).mean().iloc[-1]
        current_vol = volume[-1]
        
        # 价格变化
        price_change = (close[-1] - close[-2]) / close[-2] if len(close) > 1 else 0
        
        # 放量上涨 = 贪婪，放量下跌 = 恐慌
        volume_ratio = current_vol / vol_ma20 if vol_ma20 > 0 else 1
        
        if price_change > 0:
            # 上涨时，放量增加贪婪
            return 50 + min(25, (volume_ratio - 1) * 20 + price_change * 100)
        else:
            # 下跌时，放量增加恐慌
            return 50 - min(25, (volume_ratio - 1) * 20 - price_change * 100)
    
    def _calc_momentum_sentiment(self, df: pd.DataFrame) -> float:
        """计算涨跌情绪 (0-25分)"""
        if len(df) < 10:
            return 50
        
        close = df['close'].values
        
        # 计算多周期涨跌幅
        returns = []
        for period in [1, 3, 5, 10]:
            if len(close) > period:
                ret = (close[-1] - close[-period-1]) / close[-period-1] * 100
                returns.append(ret)
        
        if not returns:
            return 50
        
        # 加权平均（近期权重更高）
        weights = [0.4, 0.3, 0.2, 0.1]
        avg_return = sum(r * w for r, w in zip(returns, weights[:len(returns)]))
        
        # 转换为情绪分数
        # 大涨 = 贪婪(高分)，大跌 = 恐慌(低分)
        sentiment = 50 + avg_return * 2
        return max(0, min(25, sentiment * 0.5))
    
    def _calc_technical_sentiment(self, df: pd.DataFrame) -> float:
        """计算技术情绪 (0-25分)"""
        if len(df) < 20:
            return 50
        
        close = df['close'].values
        
        # RSI
        delta = pd.Series(close).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        # 将RSI转换为情绪分数
        # RSI > 70 = 超买(贪婪)，RSI < 30 = 超卖(恐慌)
        if current_rsi > 70:
            return 50 + (current_rsi - 70) * 0.8
        elif current_rsi < 30:
            return 50 - (30 - current_rsi) * 0.8
        else:
            return 50 + (current_rsi - 50) * 0.3
    
    def _get_sentiment_level(self, index_value: float) -> SentimentLevel:
        """获取情绪等级"""
        for level, (low, high) in self.level_thresholds.items():
            if low <= index_value < high:
                return level
        return SentimentLevel.EXTREME_GREED if index_value >= 100 else SentimentLevel.EXTREME_FEAR
    
    def _get_sentiment_trend(self, df: pd.DataFrame) -> str:
        """获取情绪趋势"""
        if len(df) < 10:
            return "平稳"
        
        close = df['close'].values
        
        # 计算短期和中期趋势
        short_ma = pd.Series(close).rolling(window=5).mean().iloc[-1]
        medium_ma = pd.Series(close).rolling(window=10).mean().iloc[-1]
        
        if pd.isna(short_ma) or pd.isna(medium_ma):
            return "平稳"
        
        if short_ma > medium_ma * 1.02:
            return "上升"
        elif short_ma < medium_ma * 0.98:
            return "下降"
        else:
            return "平稳"
    
    def _generate_signal(self, index_value: float, trend: str) -> str:
        """生成交易信号"""
        if index_value <= 20:
            return "强烈买入"
        elif index_value <= 35:
            return "买入"
        elif index_value >= 80:
            return "强烈卖出"
        elif index_value >= 65:
            return "卖出"
        else:
            if trend == "上升":
                return "持有"
            elif trend == "下降":
                return "减仓"
            else:
                return "观望"
    
    def _generate_description(self, index_value: float, level: SentimentLevel, components: Dict) -> str:
        """生成描述"""
        descriptions = {
            SentimentLevel.EXTREME_FEAR: "市场处于极度恐慌状态，可能是买入机会",
            SentimentLevel.FEAR: "市场情绪偏恐慌，谨慎观望",
            SentimentLevel.NEUTRAL: "市场情绪中性，等待方向选择",
            SentimentLevel.GREED: "市场情绪偏贪婪，注意风险",
            SentimentLevel.EXTREME_GREED: "市场处于极度贪婪状态，可能是卖出时机"
        }
        
        base_desc = descriptions.get(level, "")
        
        # 找出主导因素
        max_component = max(components.items(), key=lambda x: abs(x[1] - 50))
        factor_desc = f"主要受{max_component[0]}影响"
        
        return f"{base_desc}。{factor_desc}。"


def calculate_sentiment_index(df: pd.DataFrame, market_data: Dict = None) -> SentimentResult:
    """
    计算情绪指数的便捷函数
    
    Args:
        df: 价格数据
        market_data: 市场数据
        
    Returns:
        情绪分析结果
    """
    calculator = SentimentIndexCalculator()
    return calculator.calculate(df, market_data)


class MarketSentimentMonitor:
    """市场情绪监控器"""
    
    def __init__(self):
        self.calculator = SentimentIndexCalculator()
        self.history = []
    
    def update(self, df: pd.DataFrame, market_data: Dict = None) -> SentimentResult:
        """更新情绪指数"""
        result = self.calculator.calculate(df, market_data)
        self.history.append({
            'timestamp': pd.Timestamp.now(),
            'index': result.index_value,
            'level': result.level
        })
        
        # 保留最近100条记录
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        return result
    
    def get_extreme_points(self) -> Dict:
        """获取极端情绪点"""
        if not self.history:
            return {}
        
        fear_points = [h for h in self.history if h['index'] < 25]
        greed_points = [h for h in self.history if h['index'] > 75]
        
        return {
            'fear_count': len(fear_points),
            'greed_count': len(greed_points),
            'last_fear': fear_points[-1] if fear_points else None,
            'last_greed': greed_points[-1] if greed_points else None
        }
    
    def get_sentiment_cycle(self) -> str:
        """获取情绪周期位置"""
        if len(self.history) < 20:
            return "数据不足"
        
        recent = self.history[-20:]
        avg_index = sum(h['index'] for h in recent) / len(recent)
        
        if avg_index < 30:
            return "恐慌期"
        elif avg_index < 45:
            return "恢复期"
        elif avg_index < 60:
            return "平衡期"
        elif avg_index < 75:
            return "乐观期"
        else:
            return "狂热期"
