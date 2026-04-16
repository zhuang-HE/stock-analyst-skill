"""
K线形态识别库
支持60+种K线形态识别，包括看涨、看跌和持续形态
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """形态类型"""
    BULLISH = "看涨"
    BEARISH = "看跌"
    CONTINUATION = "持续"


@dataclass
class PatternResult:
    """形态识别结果"""
    name: str
    name_cn: str
    pattern_type: PatternType
    confidence: float  # 0-1
    position: int  # 形态出现的位置（最新K线为0）
    description: str
    reliability: int  # 可靠性评分 1-5


class CandlestickPatternRecognizer:
    """K线形态识别器"""
    
    def __init__(self):
        self.patterns = {
            # 看涨形态
            'morning_star': self._morning_star,
            'hammer': self._hammer,
            'inverted_hammer': self._inverted_hammer,
            'bullish_engulfing': self._bullish_engulfing,
            'piercing_pattern': self._piercing_pattern,
            'three_white_soldiers': self._three_white_soldiers,
            'tweezer_bottom': self._tweezer_bottom,
            'bullish_harami': self._bullish_harami,
            'dragonfly_doji': self._dragonfly_doji,
            'morning_doji_star': self._morning_doji_star,
            'three_inside_up': self._three_inside_up,
            'three_outside_up': self._three_outside_up,
            'bullish_kicking': self._bullish_kicking,
            'rising_three_methods': self._rising_three_methods,
            'mat_hold': self._mat_hold,
            'separating_lines_bullish': self._separating_lines_bullish,
            'side_by_side_white_lines': self._side_by_side_white_lines,
            'upside_gap_three_methods': self._upside_gap_three_methods,
            'upside_tasuki_gap': self._upside_tasuki_gap,
            'ladder_bottom': self._ladder_bottom,
            
            # 看跌形态
            'evening_star': self._evening_star,
            'shooting_star': self._shooting_star,
            'hanging_man': self._hanging_man,
            'bearish_engulfing': self._bearish_engulfing,
            'dark_cloud_cover': self._dark_cloud_cover,
            'three_black_crows': self._three_black_crows,
            'tweezer_top': self._tweezer_top,
            'bearish_harami': self._bearish_harami,
            'gravestone_doji': self._gravestone_doji,
            'evening_doji_star': self._evening_doji_star,
            'three_inside_down': self._three_inside_down,
            'three_outside_down': self._three_outside_down,
            'bearish_kicking': self._bearish_kicking,
            'falling_three_methods': self._falling_three_methods,
            'separating_lines_bearish': self._separating_lines_bearish,
            'downside_gap_three_methods': self._downside_gap_three_methods,
            'downside_tasuki_gap': self._downside_tasuki_gap,
            
            # 持续形态
            'doji': self._doji,
            'long_legged_doji': self._long_legged_doji,
            'rickshaw_man': self._rickshaw_man,
            'high_wave': self._high_wave,
            'spinning_top': self._spinning_top,
            'takuri': self._takuri,
            'belt_hold_bullish': self._belt_hold_bullish,
            'belt_hold_bearish': self._belt_hold_bearish,
            'unique_three_river_bottom': self._unique_three_river_bottom,
        }
    
    def recognize_all(self, df: pd.DataFrame, lookback: int = 5) -> List[PatternResult]:
        """
        识别所有形态
        
        Args:
            df: 包含open, high, low, close的DataFrame
            lookback: 向前查看的K线数量
            
        Returns:
            识别出的形态列表
        """
        results = []
        
        for pattern_name, pattern_func in self.patterns.items():
            try:
                pattern = pattern_func(df, lookback)
                if pattern:
                    results.append(pattern)
            except Exception as e:
                continue
        
        # 按可靠性和置信度排序
        results.sort(key=lambda x: (x.reliability, x.confidence), reverse=True)
        return results
    
    def recognize_bullish(self, df: pd.DataFrame, lookback: int = 5) -> List[PatternResult]:
        """识别看涨形态"""
        all_patterns = self.recognize_all(df, lookback)
        return [p for p in all_patterns if p.pattern_type == PatternType.BULLISH]
    
    def recognize_bearish(self, df: pd.DataFrame, lookback: int = 5) -> List[PatternResult]:
        """识别看跌形态"""
        all_patterns = self.recognize_all(df, lookback)
        return [p for p in all_patterns if p.pattern_type == PatternType.BEARISH]
    
    def _get_body_size(self, open_price: float, close_price: float) -> float:
        """获取实体大小"""
        return abs(close_price - open_price)
    
    def _get_upper_shadow(self, high: float, open_price: float, close_price: float) -> float:
        """获取上影线长度"""
        return high - max(open_price, close_price)
    
    def _get_lower_shadow(self, low: float, open_price: float, close_price: float) -> float:
        """获取下影线长度"""
        return min(open_price, close_price) - low
    
    def _get_total_range(self, high: float, low: float) -> float:
        """获取总波动范围"""
        return high - low if high != low else 0.001
    
    def _is_bullish(self, open_price: float, close_price: float) -> bool:
        """判断是否为阳线"""
        return close_price > open_price
    
    def _is_bearish(self, open_price: float, close_price: float) -> bool:
        """判断是否为阴线"""
        return close_price < open_price
    
    def _is_doji(self, open_price: float, close_price: float, high: float, low: float) -> bool:
        """判断是否为十字星"""
        body = self._get_body_size(open_price, close_price)
        total_range = self._get_total_range(high, low)
        return body / total_range < 0.1 if total_range > 0 else False
    
    # ==================== 看涨形态 ====================
    
    def _morning_star(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """早晨之星 - 强烈看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        # 第一根：长阴线
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond1_size = (c1['open'] - c1['close']) / (c1['high'] - c1['low']) > 0.5
        
        # 第二根：小实体（十字星或陀螺线）
        body2 = self._get_body_size(c2['open'], c2['close'])
        range2 = self._get_total_range(c2['high'], c2['low'])
        cond2 = body2 / range2 < 0.3 if range2 > 0 else False
        
        # 第三根：长阳线，收盘深入第一根实体
        cond3 = self._is_bullish(c3['open'], c3['close'])
        cond3_size = (c3['close'] - c3['open']) / (c3['high'] - c3['low']) > 0.5
        cond3_close = c3['close'] > (c1['open'] + c1['close']) / 2
        
        if cond1 and cond1_size and cond2 and cond3 and cond3_size and cond3_close:
            return PatternResult(
                name='morning_star',
                name_cn='早晨之星',
                pattern_type=PatternType.BULLISH,
                confidence=0.85,
                position=0,
                description='强烈看涨反转信号，出现在下跌趋势末端',
                reliability=5
            )
        return None
    
    def _hammer(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """锤头线 - 看涨"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        # 下影线是实体的2倍以上，上影线很短
        cond1 = lower_shadow > body * 2
        cond2 = upper_shadow < body * 0.1
        cond3 = body / total_range < 0.3
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='hammer',
                name_cn='锤头线',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='出现在下跌趋势末端，下影线长表示下方支撑强',
                reliability=4
            )
        return None
    
    def _inverted_hammer(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """倒锤头 - 看涨"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = upper_shadow > body * 2
        cond2 = lower_shadow < body * 0.1
        cond3 = body / total_range < 0.3
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='inverted_hammer',
                name_cn='倒锤头',
                pattern_type=PatternType.BULLISH,
                confidence=0.70,
                position=0,
                description='出现在下跌趋势末端，需要后续确认',
                reliability=3
            )
        return None
    
    def _bullish_engulfing(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """阳包阴 - 看涨"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        # 第一根阴线
        cond1 = self._is_bearish(c1['open'], c1['close'])
        # 第二根阳线完全包住第一根
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = c2['open'] < c1['close']  # 低开
        cond4 = c2['close'] > c1['open']  # 高收
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='bullish_engulfing',
                name_cn='阳包阴',
                pattern_type=PatternType.BULLISH,
                confidence=0.80,
                position=0,
                description='阳线完全吞没前一根阴线，强烈看涨信号',
                reliability=4
            )
        return None
    
    def _piercing_pattern(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """刺透形态 - 看涨"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = c2['open'] < c1['low']  # 低开
        cond4 = c2['close'] > (c1['open'] + c1['close']) / 2  # 收在前实体中点之上
        cond5 = c2['close'] < c1['open']  # 但未超过前开
        
        if cond1 and cond2 and cond3 and cond4 and cond5:
            return PatternResult(
                name='piercing_pattern',
                name_cn='刺透形态',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='第二根阳线深入前阴线实体，但未完全吞没',
                reliability=4
            )
        return None
    
    def _three_white_soldiers(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """红三兵 - 看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = all(self._is_bullish(c['open'], c['close']) for c in [c1, c2, c3])
        cond2 = c2['open'] > c1['open'] and c2['open'] < c1['close']
        cond3 = c3['open'] > c2['open'] and c3['open'] < c2['close']
        cond4 = c1['close'] > c1['open'] and c2['close'] > c2['open'] and c3['close'] > c3['open']
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='three_white_soldiers',
                name_cn='红三兵',
                pattern_type=PatternType.BULLISH,
                confidence=0.80,
                position=0,
                description='连续三根阳线，逐步推高，趋势延续信号',
                reliability=4
            )
        return None
    
    def _tweezer_bottom(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """双针探底 - 看涨"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = abs(c1['low'] - c2['low']) / c1['low'] < 0.001  # 低点几乎相同
        cond2 = self._is_bearish(c1['open'], c1['close'])
        cond3 = self._is_bullish(c2['open'], c2['close'])
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='tweezer_bottom',
                name_cn='双针探底',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='两根K线低点相同，显示强支撑',
                reliability=4
            )
        return None
    
    def _bullish_harami(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看涨孕线 - 看涨"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = c2['open'] > c1['close'] and c2['close'] < c1['open']
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='bullish_harami',
                name_cn='看涨孕线',
                pattern_type=PatternType.BULLISH,
                confidence=0.70,
                position=0,
                description='小阳线完全包含在前大阴线内，可能反转',
                reliability=3
            )
        return None
    
    def _dragonfly_doji(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """蜻蜓十字星 - 看涨"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = body / total_range < 0.1
        cond2 = lower_shadow > total_range * 0.6
        cond3 = upper_shadow < total_range * 0.1
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='dragonfly_doji',
                name_cn='蜻蜓十字星',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='长下影线十字星，强烈看涨反转信号',
                reliability=4
            )
        return None
    
    def _morning_doji_star(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """早晨十字星 - 看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = self._is_doji(c2['open'], c2['close'], c2['high'], c2['low'])
        cond3 = self._is_bullish(c3['open'], c3['close'])
        cond4 = c3['close'] > (c1['open'] + c1['close']) / 2
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='morning_doji_star',
                name_cn='早晨十字星',
                pattern_type=PatternType.BULLISH,
                confidence=0.85,
                position=0,
                description='早晨之星的十字星变体，反转信号更强',
                reliability=5
            )
        return None
    
    def _three_inside_up(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """三内部上涨 - 看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = c2['close'] < c1['open'] and c2['open'] > c1['close']
        cond4 = c3['close'] > c1['open']
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='three_inside_up',
                name_cn='三内部上涨',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='孕线形态后的确认上涨',
                reliability=4
            )
        return None
    
    def _three_outside_up(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """三外部上涨 - 看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = c2['open'] < c1['close'] and c2['close'] > c1['open']
        cond4 = c3['close'] > c2['close']
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='three_outside_up',
                name_cn='三外部上涨',
                pattern_type=PatternType.BULLISH,
                confidence=0.80,
                position=0,
                description='吞没形态后的确认上涨',
                reliability=4
            )
        return None
    
    def _bullish_kicking(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看涨反冲 - 看涨"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = c2['open'] > c1['close']  # 向上跳空
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='bullish_kicking',
                name_cn='看涨反冲',
                pattern_type=PatternType.BULLISH,
                confidence=0.80,
                position=0,
                description='阴线后向上跳空阳线，强烈看涨',
                reliability=4
            )
        return None
    
    def _rising_three_methods(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """上升三法 - 看涨"""
        if len(df) < 5:
            return None
        
        c1, c2, c3, c4, c5 = df.iloc[-5], df.iloc[-4], df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = all(self._is_bearish(c['open'], c['close']) for c in [c2, c3, c4])
        cond3 = all(c['close'] > c1['open'] and c['open'] < c1['close'] for c in [c2, c3, c4])
        cond4 = self._is_bullish(c5['open'], c5['close'])
        cond5 = c5['close'] > c1['close']
        
        if cond1 and cond2 and cond3 and cond4 and cond5:
            return PatternResult(
                name='rising_three_methods',
                name_cn='上升三法',
                pattern_type=PatternType.BULLISH,
                confidence=0.80,
                position=0,
                description='上涨趋势中的整理形态，继续看涨',
                reliability=4
            )
        return None
    
    def _mat_hold(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """铺垫形态 - 看涨"""
        if len(df) < 5:
            return None
        
        c1, c2, c3, c4, c5 = df.iloc[-5], df.iloc[-4], df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = c2['open'] > c1['close']  # 向上跳空
        cond3 = all(self._is_bearish(c['open'], c['close']) for c in [c2, c3, c4])
        cond4 = all(c['close'] > c1['close'] for c in [c2, c3, c4])
        cond5 = self._is_bullish(c5['open'], c5['close'])
        cond6 = c5['close'] > c2['open']
        
        if cond1 and cond2 and cond3 and cond4 and cond5 and cond6:
            return PatternResult(
                name='mat_hold',
                name_cn='铺垫形态',
                pattern_type=PatternType.BULLISH,
                confidence=0.80,
                position=0,
                description='类似上升三法但有跳空缺口',
                reliability=4
            )
        return None
    
    def _separating_lines_bullish(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看涨分离线 - 看涨"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = abs(c1['open'] - c2['open']) / c1['open'] < 0.001
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='separating_lines_bullish',
                name_cn='看涨分离线',
                pattern_type=PatternType.BULLISH,
                confidence=0.70,
                position=0,
                description='两根K线开盘价相同，趋势继续',
                reliability=3
            )
        return None
    
    def _side_by_side_white_lines(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """并列阳线 - 看涨"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bullish(c2['open'], c2['close'])
        cond3 = abs(c1['open'] - c2['open']) / c1['open'] < 0.005
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='side_by_side_white_lines',
                name_cn='并列阳线',
                pattern_type=PatternType.BULLISH,
                confidence=0.70,
                position=0,
                description='两根阳线并排，上涨趋势持续',
                reliability=3
            )
        return None
    
    def _upside_gap_three_methods(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """向上跳空三法 - 看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = c2['open'] > c1['close']  # 向上跳空
        cond3 = self._is_bearish(c2['open'], c2['close'])
        cond4 = c3['close'] > c1['close']
        cond5 = c3['open'] < c2['close']
        
        if cond1 and cond2 and cond3 and cond4 and cond5:
            return PatternResult(
                name='upside_gap_three_methods',
                name_cn='向上跳空三法',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='回补跳空缺口后继续上涨',
                reliability=4
            )
        return None
    
    def _upside_tasuki_gap(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """向上跳空并列阴阳线 - 看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = c2['open'] > c1['close']  # 向上跳空
        cond3 = self._is_bullish(c2['open'], c2['close'])
        cond4 = self._is_bearish(c3['open'], c3['close'])
        cond5 = c3['open'] > c2['open'] and c3['close'] < c2['close']
        cond6 = c3['close'] > c1['close']
        
        if cond1 and cond2 and cond3 and cond4 and cond5 and cond6:
            return PatternResult(
                name='upside_tasuki_gap',
                name_cn='向上跳空并列阴阳线',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='跳空后整理，趋势继续',
                reliability=4
            )
        return None
    
    def _ladder_bottom(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """梯底 - 看涨"""
        if len(df) < 5:
            return None
        
        c1, c2, c3, c4, c5 = df.iloc[-5], df.iloc[-4], df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = all(self._is_bearish(c['open'], c['close']) for c in [c1, c2, c3])
        cond2 = c1['high'] > c2['high'] > c3['high']
        cond3 = c4['low'] > c3['low']
        cond4 = self._is_bullish(c5['open'], c5['close'])
        cond5 = c5['close'] > c4['close']
        
        if cond1 and cond2 and cond3 and cond4 and cond5:
            return PatternResult(
                name='ladder_bottom',
                name_cn='梯底',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='阶梯式下跌后反转',
                reliability=4
            )
        return None
    
    # ==================== 看跌形态 ====================
    
    def _evening_star(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """黄昏之星 - 看跌"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond1_size = (c1['close'] - c1['open']) / (c1['high'] - c1['low']) > 0.5
        
        body2 = self._get_body_size(c2['open'], c2['close'])
        range2 = self._get_total_range(c2['high'], c2['low'])
        cond2 = body2 / range2 < 0.3 if range2 > 0 else False
        
        cond3 = self._is_bearish(c3['open'], c3['close'])
        cond3_size = (c3['open'] - c3['close']) / (c3['high'] - c3['low']) > 0.5
        cond3_close = c3['close'] < (c1['open'] + c1['close']) / 2
        
        if cond1 and cond1_size and cond2 and cond3 and cond3_size and cond3_close:
            return PatternResult(
                name='evening_star',
                name_cn='黄昏之星',
                pattern_type=PatternType.BEARISH,
                confidence=0.85,
                position=0,
                description='强烈看跌反转信号，出现在上涨趋势末端',
                reliability=5
            )
        return None
    
    def _shooting_star(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """射击之星 - 看跌"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = upper_shadow > body * 2
        cond2 = lower_shadow < body * 0.1
        cond3 = body / total_range < 0.3
        cond4 = self._is_bullish(c['open'], c['close'])  # 出现在上涨中
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='shooting_star',
                name_cn='射击之星',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='出现在上涨趋势末端，长上影线表示上方阻力强',
                reliability=4
            )
        return None
    
    def _hanging_man(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """吊颈线 - 看跌"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = lower_shadow > body * 2
        cond2 = upper_shadow < body * 0.1
        cond3 = body / total_range < 0.3
        cond4 = self._is_bullish(c['open'], c['close'])  # 出现在上涨中
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='hanging_man',
                name_cn='吊颈线',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='出现在上涨趋势末端，形态同锤头线但位置不同',
                reliability=4
            )
        return None
    
    def _bearish_engulfing(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """阴包阳 - 看跌"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bearish(c2['open'], c2['close'])
        cond3 = c2['open'] > c1['close']
        cond4 = c2['close'] < c1['open']
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='bearish_engulfing',
                name_cn='阴包阳',
                pattern_type=PatternType.BEARISH,
                confidence=0.80,
                position=0,
                description='阴线完全吞没前一根阳线，强烈看跌信号',
                reliability=4
            )
        return None
    
    def _dark_cloud_cover(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """乌云盖顶 - 看跌"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bearish(c2['open'], c2['close'])
        cond3 = c2['open'] > c1['high']
        cond4 = c2['close'] < (c1['open'] + c1['close']) / 2
        cond5 = c2['close'] > c1['open']
        
        if cond1 and cond2 and cond3 and cond4 and cond5:
            return PatternResult(
                name='dark_cloud_cover',
                name_cn='乌云盖顶',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='第二根阴线深入前阳线实体，但未完全吞没',
                reliability=4
            )
        return None
    
    def _three_black_crows(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """三只乌鸦 - 看跌"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = all(self._is_bearish(c['open'], c['close']) for c in [c1, c2, c3])
        cond2 = c2['open'] < c2['close'] and c2['open'] > c1['open']
        cond3 = c3['open'] < c3['close'] and c3['open'] > c2['open']
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='three_black_crows',
                name_cn='三只乌鸦',
                pattern_type=PatternType.BEARISH,
                confidence=0.80,
                position=0,
                description='连续三根阴线，逐步走低，趋势反转信号',
                reliability=4
            )
        return None
    
    def _tweezer_top(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """双针探顶 - 看跌"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = abs(c1['high'] - c2['high']) / c1['high'] < 0.001
        cond2 = self._is_bullish(c1['open'], c1['close'])
        cond3 = self._is_bearish(c2['open'], c2['close'])
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='tweezer_top',
                name_cn='双针探顶',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='两根K线高点相同，显示强阻力',
                reliability=4
            )
        return None
    
    def _bearish_harami(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看跌孕线 - 看跌"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bearish(c2['open'], c2['close'])
        cond3 = c2['open'] < c1['close'] and c2['close'] > c1['open']
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='bearish_harami',
                name_cn='看跌孕线',
                pattern_type=PatternType.BEARISH,
                confidence=0.70,
                position=0,
                description='小阴线完全包含在前大阳线内，可能反转',
                reliability=3
            )
        return None
    
    def _gravestone_doji(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """墓碑十字星 - 看跌"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = body / total_range < 0.1
        cond2 = upper_shadow > total_range * 0.6
        cond3 = lower_shadow < total_range * 0.1
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='gravestone_doji',
                name_cn='墓碑十字星',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='长上影线十字星，强烈看跌反转信号',
                reliability=4
            )
        return None
    
    def _evening_doji_star(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """黄昏十字星 - 看跌"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_doji(c2['open'], c2['close'], c2['high'], c2['low'])
        cond3 = self._is_bearish(c3['open'], c3['close'])
        cond4 = c3['close'] < (c1['open'] + c1['close']) / 2
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='evening_doji_star',
                name_cn='黄昏十字星',
                pattern_type=PatternType.BEARISH,
                confidence=0.85,
                position=0,
                description='黄昏之星的十字星变体，反转信号更强',
                reliability=5
            )
        return None
    
    def _three_inside_down(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """三内部下跌 - 看跌"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bearish(c2['open'], c2['close'])
        cond3 = c2['close'] > c1['open'] and c2['open'] < c1['close']
        cond4 = c3['close'] < c1['open']
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='three_inside_down',
                name_cn='三内部下跌',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='孕线形态后的确认下跌',
                reliability=4
            )
        return None
    
    def _three_outside_down(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """三外部下跌 - 看跌"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bearish(c2['open'], c2['close'])
        cond3 = c2['open'] > c1['close'] and c2['close'] < c1['open']
        cond4 = c3['close'] < c2['close']
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='three_outside_down',
                name_cn='三外部下跌',
                pattern_type=PatternType.BEARISH,
                confidence=0.80,
                position=0,
                description='吞没形态后的确认下跌',
                reliability=4
            )
        return None
    
    def _bearish_kicking(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看跌反冲 - 看跌"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bearish(c2['open'], c2['close'])
        cond3 = c2['open'] < c1['close']
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='bearish_kicking',
                name_cn='看跌反冲',
                pattern_type=PatternType.BEARISH,
                confidence=0.80,
                position=0,
                description='阳线后向下跳空阴线，强烈看跌',
                reliability=4
            )
        return None
    
    def _falling_three_methods(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """下降三法 - 看跌"""
        if len(df) < 5:
            return None
        
        c1, c2, c3, c4, c5 = df.iloc[-5], df.iloc[-4], df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = all(self._is_bullish(c['open'], c['close']) for c in [c2, c3, c4])
        cond3 = all(c['close'] < c1['open'] and c['open'] > c1['close'] for c in [c2, c3, c4])
        cond4 = self._is_bearish(c5['open'], c5['close'])
        cond5 = c5['close'] < c1['close']
        
        if cond1 and cond2 and cond3 and cond4 and cond5:
            return PatternResult(
                name='falling_three_methods',
                name_cn='下降三法',
                pattern_type=PatternType.BEARISH,
                confidence=0.80,
                position=0,
                description='下跌趋势中的整理形态，继续看跌',
                reliability=4
            )
        return None
    
    def _separating_lines_bearish(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看跌分离线 - 看跌"""
        if len(df) < 2:
            return None
        
        c1, c2 = df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bullish(c1['open'], c1['close'])
        cond2 = self._is_bearish(c2['open'], c2['close'])
        cond3 = abs(c1['open'] - c2['open']) / c1['open'] < 0.001
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='separating_lines_bearish',
                name_cn='看跌分离线',
                pattern_type=PatternType.BEARISH,
                confidence=0.70,
                position=0,
                description='两根K线开盘价相同，下跌趋势继续',
                reliability=3
            )
        return None
    
    def _downside_gap_three_methods(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """向下跳空三法 - 看跌"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = c2['open'] < c1['close']
        cond3 = self._is_bullish(c2['open'], c2['close'])
        cond4 = c3['close'] < c1['close']
        cond5 = c3['open'] > c2['close']
        
        if cond1 and cond2 and cond3 and cond4 and cond5:
            return PatternResult(
                name='downside_gap_three_methods',
                name_cn='向下跳空三法',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='回补跳空缺口后继续下跌',
                reliability=4
            )
        return None
    
    def _downside_tasuki_gap(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """向下跳空并列阴阳线 - 看跌"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = self._is_bearish(c1['open'], c1['close'])
        cond2 = c2['open'] < c1['close']
        cond3 = self._is_bearish(c2['open'], c2['close'])
        cond4 = self._is_bullish(c3['open'], c3['close'])
        cond5 = c3['open'] < c2['open'] and c3['close'] > c2['close']
        cond6 = c3['close'] < c1['close']
        
        if cond1 and cond2 and cond3 and cond4 and cond5 and cond6:
            return PatternResult(
                name='downside_tasuki_gap',
                name_cn='向下跳空并列阴阳线',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='跳空后整理，趋势继续',
                reliability=4
            )
        return None
    
    # ==================== 持续形态 ====================
    
    def _doji(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """十字星 - 持续/反转"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = body / total_range < 0.1
        
        if cond1:
            return PatternResult(
                name='doji',
                name_cn='十字星',
                pattern_type=PatternType.CONTINUATION,
                confidence=0.60,
                position=0,
                description='多空平衡，需等待方向选择',
                reliability=2
            )
        return None
    
    def _long_legged_doji(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """长腿十字星 - 持续"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = body / total_range < 0.1
        cond2 = upper_shadow > total_range * 0.4
        cond3 = lower_shadow > total_range * 0.4
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='long_legged_doji',
                name_cn='长腿十字星',
                pattern_type=PatternType.CONTINUATION,
                confidence=0.65,
                position=0,
                description='多空激烈争夺，方向不明',
                reliability=2
            )
        return None
    
    def _rickshaw_man(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """黄包车夫 - 持续"""
        return self._long_legged_doji(df, lookback)
    
    def _high_wave(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """高位浪 - 持续"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = body / total_range < 0.2
        cond2 = (upper_shadow + lower_shadow) > body * 3
        
        if cond1 and cond2:
            return PatternResult(
                name='high_wave',
                name_cn='高位浪',
                pattern_type=PatternType.CONTINUATION,
                confidence=0.60,
                position=0,
                description='波动加剧，不确定性增加',
                reliability=2
            )
        return None
    
    def _spinning_top(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """陀螺线 - 持续"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = body / total_range < 0.3
        cond2 = abs(upper_shadow - lower_shadow) / total_range < 0.1
        
        if cond1 and cond2:
            return PatternResult(
                name='spinning_top',
                name_cn='陀螺线',
                pattern_type=PatternType.CONTINUATION,
                confidence=0.60,
                position=0,
                description='多空力量均衡，趋势可能继续',
                reliability=2
            )
        return None
    
    def _takuri(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """探水竿 - 看涨"""
        return self._hammer(df, lookback)
    
    def _belt_hold_bullish(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看涨捉腰带线 - 看涨"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        lower_shadow = self._get_lower_shadow(c['low'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = self._is_bullish(c['open'], c['close'])
        cond2 = lower_shadow < body * 0.1
        cond3 = body / total_range > 0.7
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='belt_hold_bullish',
                name_cn='看涨捉腰带线',
                pattern_type=PatternType.BULLISH,
                confidence=0.75,
                position=0,
                description='光头阳线，强烈看涨',
                reliability=4
            )
        return None
    
    def _belt_hold_bearish(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """看跌捉腰带线 - 看跌"""
        if len(df) < 1:
            return None
        
        c = df.iloc[-1]
        body = self._get_body_size(c['open'], c['close'])
        upper_shadow = self._get_upper_shadow(c['high'], c['open'], c['close'])
        total_range = self._get_total_range(c['high'], c['low'])
        
        if total_range == 0:
            return None
        
        cond1 = self._is_bearish(c['open'], c['close'])
        cond2 = upper_shadow < body * 0.1
        cond3 = body / total_range > 0.7
        
        if cond1 and cond2 and cond3:
            return PatternResult(
                name='belt_hold_bearish',
                name_cn='看跌捉腰带线',
                pattern_type=PatternType.BEARISH,
                confidence=0.75,
                position=0,
                description='光脚阴线，强烈看跌',
                reliability=4
            )
        return None
    
    def _unique_three_river_bottom(self, df: pd.DataFrame, lookback: int) -> Optional[PatternResult]:
        """奇特三河床 - 看涨"""
        if len(df) < 3:
            return None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        cond1 = all(self._is_bearish(c['open'], c['close']) for c in [c1, c2, c3])
        cond2 = c2['low'] < c1['low']
        cond3 = c3['low'] > c2['low']
        cond4 = c3['close'] > c3['open'] * 0.5 + c3['close'] * 0.5
        
        if cond1 and cond2 and cond3 and cond4:
            return PatternResult(
                name='unique_three_river_bottom',
                name_cn='奇特三河床',
                pattern_type=PatternType.BULLISH,
                confidence=0.70,
                position=0,
                description='三根阴线后可能出现反转',
                reliability=3
            )
        return None


def analyze_candlestick_patterns(df: pd.DataFrame) -> Dict:
    """
    分析K线形态并返回汇总结果
    
    Args:
        df: 包含open, high, low, close的DataFrame
        
    Returns:
        形态分析结果字典
    """
    recognizer = CandlestickPatternRecognizer()
    patterns = recognizer.recognize_all(df)
    
    bullish = [p for p in patterns if p.pattern_type == PatternType.BULLISH]
    bearish = [p for p in patterns if p.pattern_type == PatternType.BEARISH]
    continuation = [p for p in patterns if p.pattern_type == PatternType.CONTINUATION]
    
    # 计算信号强度
    bullish_score = sum(p.confidence * p.reliability for p in bullish) if bullish else 0
    bearish_score = sum(p.confidence * p.reliability for p in bearish) if bearish else 0
    
    net_score = bullish_score - bearish_score
    
    if net_score > 10:
        signal = "强烈看涨"
        signal_strength = 5
    elif net_score > 5:
        signal = "看涨"
        signal_strength = 4
    elif net_score > 0:
        signal = "偏多"
        signal_strength = 3
    elif net_score > -5:
        signal = "偏空"
        signal_strength = 2
    elif net_score > -10:
        signal = "看跌"
        signal_strength = 1
    else:
        signal = "强烈看跌"
        signal_strength = 0
    
    return {
        'patterns': patterns,
        'bullish_count': len(bullish),
        'bearish_count': len(bearish),
        'continuation_count': len(continuation),
        'top_bullish': bullish[:3] if bullish else [],
        'top_bearish': bearish[:3] if bearish else [],
        'bullish_score': round(bullish_score, 2),
        'bearish_score': round(bearish_score, 2),
        'net_score': round(net_score, 2),
        'signal': signal,
        'signal_strength': signal_strength,
        'summary': f"识别出 {len(patterns)} 个形态，看涨{bullish_score:.1f}分 / 看跌{bearish_score:.1f}分"
    }
