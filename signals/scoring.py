"""
信号共振评分系统
整合多维度信号，计算综合评分
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """信号类型"""
    CANDLESTICK = "K线形态"
    TECHNICAL = "技术指标"
    TREND = "趋势信号"
    VOLUME = "成交量"
    FUNDAMENTAL = "基本面"
    SENTIMENT = "情绪面"
    CHANLUN = "缠论"


class SignalDirection(Enum):
    """信号方向"""
    BULLISH = "看涨"
    BEARISH = "看跌"
    NEUTRAL = "中性"


@dataclass
class Signal:
    """单个信号"""
    signal_type: SignalType
    direction: SignalDirection
    strength: float  # 0-1
    description: str
    weight: float = 1.0  # 权重


@dataclass
class ResonanceResult:
    """共振结果"""
    total_score: float  # -100 到 100
    bullish_score: float
    bearish_score: float
    signal_count: int
    bullish_signals: List[Signal]
    bearish_signals: List[Signal]
    neutral_signals: List[Signal]
    resonance_level: str  # 强共振/中等共振/弱共振/无共振
    confidence: float
    summary: str


class SignalResonanceScorer:
    """信号共振评分器"""
    
    def __init__(self):
        # 各维度权重配置
        self.weights = {
            SignalType.CANDLESTICK: 0.20,
            SignalType.TECHNICAL: 0.20,
            SignalType.TREND: 0.15,
            SignalType.VOLUME: 0.10,
            SignalType.FUNDAMENTAL: 0.15,
            SignalType.SENTIMENT: 0.10,
            SignalType.CHANLUN: 0.10
        }
        
        # 共振阈值
        self.resonance_thresholds = {
            'strong': 70,
            'medium': 40,
            'weak': 20
        }
    
    def calculate_resonance(self, signals: List[Signal]) -> ResonanceResult:
        """
        计算信号共振
        
        Args:
            signals: 信号列表
            
        Returns:
            共振结果
        """
        if not signals:
            return ResonanceResult(
                total_score=0,
                bullish_score=0,
                bearish_score=0,
                signal_count=0,
                bullish_signals=[],
                bearish_signals=[],
                neutral_signals=[],
                resonance_level="无信号",
                confidence=0,
                summary="未检测到任何信号"
            )
        
        # 分类信号
        bullish_signals = [s for s in signals if s.direction == SignalDirection.BULLISH]
        bearish_signals = [s for s in signals if s.direction == SignalDirection.BEARISH]
        neutral_signals = [s for s in signals if s.direction == SignalDirection.NEUTRAL]
        
        # 计算加权得分
        bullish_score = sum(
            s.strength * self.weights.get(s.signal_type, 0.1) * s.weight
            for s in bullish_signals
        ) * 100
        
        bearish_score = sum(
            s.strength * self.weights.get(s.signal_type, 0.1) * s.weight
            for s in bearish_signals
        ) * 100
        
        # 计算净得分
        total_score = bullish_score - bearish_score
        
        # 确定共振级别
        abs_score = abs(total_score)
        if abs_score >= self.resonance_thresholds['strong']:
            resonance_level = "强共振"
        elif abs_score >= self.resonance_thresholds['medium']:
            resonance_level = "中等共振"
        elif abs_score >= self.resonance_thresholds['weak']:
            resonance_level = "弱共振"
        else:
            resonance_level = "无共振"
        
        # 计算置信度
        signal_diversity = len(set(s.signal_type for s in signals))
        confidence = min(0.95, 0.5 + signal_diversity * 0.1 + len(signals) * 0.02)
        
        # 生成摘要
        summary = self._generate_summary(
            total_score, bullish_score, bearish_score,
            len(bullish_signals), len(bearish_signals), resonance_level
        )
        
        return ResonanceResult(
            total_score=round(total_score, 2),
            bullish_score=round(bullish_score, 2),
            bearish_score=round(bearish_score, 2),
            signal_count=len(signals),
            bullish_signals=bullish_signals,
            bearish_signals=bearish_signals,
            neutral_signals=neutral_signals,
            resonance_level=resonance_level,
            confidence=round(confidence, 2),
            summary=summary
        )
    
    def _generate_summary(self, total_score: float, bullish_score: float,
                         bearish_score: float, bullish_count: int,
                         bearish_count: int, resonance_level: str) -> str:
        """生成摘要"""
        if total_score > 50:
            direction = "强烈看涨"
        elif total_score > 20:
            direction = "看涨"
        elif total_score > 0:
            direction = "偏多"
        elif total_score > -20:
            direction = "偏空"
        elif total_score > -50:
            direction = "看跌"
        else:
            direction = "强烈看跌"
        
        return (f"{direction}（{resonance_level}）："
                f"看涨{bullish_count}个信号{bullish_score:.1f}分 vs "
                f"看跌{bearish_count}个信号{bearish_score:.1f}分")
    
    def add_signal(self, signal_type: SignalType, direction: SignalDirection,
                   strength: float, description: str, weight: float = 1.0) -> Signal:
        """便捷方法：创建信号"""
        return Signal(
            signal_type=signal_type,
            direction=direction,
            strength=strength,
            description=description,
            weight=weight
        )
    
    def analyze_technical_signals(self, df: pd.DataFrame) -> List[Signal]:
        """分析技术信号"""
        signals = []
        
        if len(df) < 20:
            return signals
        
        # 计算技术指标
        close = df['close'].values
        
        # 1. MACD信号
        ema12 = pd.Series(close).ewm(span=12).mean()
        ema26 = pd.Series(close).ewm(span=26).mean()
        macd = ema12 - ema26
        signal_line = macd.ewm(span=9).mean()
        
        if len(macd) >= 2:
            if macd.iloc[-2] < signal_line.iloc[-2] and macd.iloc[-1] > signal_line.iloc[-1]:
                signals.append(self.add_signal(
                    SignalType.TECHNICAL, SignalDirection.BULLISH, 0.8,
                    "MACD金叉"
                ))
            elif macd.iloc[-2] > signal_line.iloc[-2] and macd.iloc[-1] < signal_line.iloc[-1]:
                signals.append(self.add_signal(
                    SignalType.TECHNICAL, SignalDirection.BEARISH, 0.8,
                    "MACD死叉"
                ))
        
        # 2. RSI信号
        delta = pd.Series(close).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        if len(rsi) > 0:
            current_rsi = rsi.iloc[-1]
            if current_rsi < 30:
                signals.append(self.add_signal(
                    SignalType.TECHNICAL, SignalDirection.BULLISH, 0.7,
                    f"RSI超卖({current_rsi:.1f})"
                ))
            elif current_rsi > 70:
                signals.append(self.add_signal(
                    SignalType.TECHNICAL, SignalDirection.BEARISH, 0.7,
                    f"RSI超买({current_rsi:.1f})"
                ))
        
        # 3. 均线排列
        ma5 = pd.Series(close).rolling(window=5).mean()
        ma10 = pd.Series(close).rolling(window=10).mean()
        ma20 = pd.Series(close).rolling(window=20).mean()
        
        if len(ma5) > 0 and len(ma10) > 0 and len(ma20) > 0:
            if ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1]:
                signals.append(self.add_signal(
                    SignalType.TREND, SignalDirection.BULLISH, 0.75,
                    "均线多头排列(MA5>MA10>MA20)"
                ))
            elif ma5.iloc[-1] < ma10.iloc[-1] < ma20.iloc[-1]:
                signals.append(self.add_signal(
                    SignalType.TREND, SignalDirection.BEARISH, 0.75,
                    "均线空头排列(MA5<MA10<MA20)"
                ))
        
        # 4. 布林带
        ma20 = pd.Series(close).rolling(window=20).mean()
        std20 = pd.Series(close).rolling(window=20).std()
        upper_band = ma20 + 2 * std20
        lower_band = ma20 - 2 * std20
        
        if len(upper_band) > 0:
            current_price = close[-1]
            if current_price > upper_band.iloc[-1]:
                signals.append(self.add_signal(
                    SignalType.TECHNICAL, SignalDirection.BEARISH, 0.6,
                    "价格突破布林带上轨"
                ))
            elif current_price < lower_band.iloc[-1]:
                signals.append(self.add_signal(
                    SignalType.TECHNICAL, SignalDirection.BULLISH, 0.6,
                    "价格跌破布林带下轨"
                ))
        
        return signals
    
    def analyze_volume_signals(self, df: pd.DataFrame) -> List[Signal]:
        """分析成交量信号"""
        signals = []
        
        if 'volume' not in df.columns or len(df) < 5:
            return signals
        
        volume = df['volume'].values
        close = df['close'].values
        
        # 成交量均值
        vol_ma5 = pd.Series(volume).rolling(window=5).mean()
        vol_ma20 = pd.Series(volume).rolling(window=20).mean()
        
        if len(vol_ma5) > 0 and len(vol_ma20) > 0:
            current_vol = volume[-1]
            current_price_change = (close[-1] - close[-2]) / close[-2] if len(close) > 1 else 0
            
            # 放量上涨
            if current_vol > vol_ma5.iloc[-1] * 1.5 and current_price_change > 0:
                signals.append(self.add_signal(
                    SignalType.VOLUME, SignalDirection.BULLISH, 0.75,
                    "放量上涨"
                ))
            # 放量下跌
            elif current_vol > vol_ma5.iloc[-1] * 1.5 and current_price_change < 0:
                signals.append(self.add_signal(
                    SignalType.VOLUME, SignalDirection.BEARISH, 0.75,
                    "放量下跌"
                ))
            # 缩量上涨
            elif current_vol < vol_ma5.iloc[-1] * 0.7 and current_price_change > 0:
                signals.append(self.add_signal(
                    SignalType.VOLUME, SignalDirection.NEUTRAL, 0.5,
                    "缩量上涨，需警惕"
                ))
        
        return signals
    
    def analyze_candlestick_signals(self, pattern_result: Dict) -> List[Signal]:
        """分析K线形态信号"""
        signals = []
        
        if not pattern_result:
            return signals
        
        # 看涨形态
        for pattern in pattern_result.get('top_bullish', []):
            signals.append(self.add_signal(
                SignalType.CANDLESTICK,
                SignalDirection.BULLISH,
                pattern.confidence * (pattern.reliability / 5),
                f"{pattern.name_cn}({pattern.description})"
            ))
        
        # 看跌形态
        for pattern in pattern_result.get('top_bearish', []):
            signals.append(self.add_signal(
                SignalType.CANDLESTICK,
                SignalDirection.BEARISH,
                pattern.confidence * (pattern.reliability / 5),
                f"{pattern.name_cn}({pattern.description})"
            ))
        
        return signals
    
    def analyze_chanlun_signals(self, chanlun_result: Dict) -> List[Signal]:
        """分析缠论信号"""
        signals = []
        
        if not chanlun_result:
            return signals
        
        buy_points = chanlun_result.get('buy_points', [])
        
        for bp in buy_points:
            if '买' in bp.bp_type.value:
                signals.append(self.add_signal(
                    SignalType.CHANLUN,
                    SignalDirection.BULLISH,
                    bp.confidence,
                    f"缠论{bp.bp_type.value}：{bp.description}"
                ))
            else:
                signals.append(self.add_signal(
                    SignalType.CHANLUN,
                    SignalDirection.BEARISH,
                    bp.confidence,
                    f"缠论{bp.bp_type.value}：{bp.description}"
                ))
        
        return signals
    
    def analyze_fundamental_signals(self, fundamental_data: Dict) -> List[Signal]:
        """分析基本面信号"""
        signals = []
        
        if not fundamental_data:
            return signals
        
        # 估值分析
        pe = fundamental_data.get('pe')
        pb = fundamental_data.get('pb')
        
        if pe and pe > 0:
            if pe < 15:
                signals.append(self.add_signal(
                    SignalType.FUNDAMENTAL, SignalDirection.BULLISH, 0.6,
                    f"PE估值偏低({pe:.1f})"
                ))
            elif pe > 50:
                signals.append(self.add_signal(
                    SignalType.FUNDAMENTAL, SignalDirection.BEARISH, 0.5,
                    f"PE估值偏高({pe:.1f})"
                ))
        
        if pb and pb > 0:
            if pb < 1.5:
                signals.append(self.add_signal(
                    SignalType.FUNDAMENTAL, SignalDirection.BULLISH, 0.5,
                    f"PB估值偏低({pb:.1f})"
                ))
            elif pb > 5:
                signals.append(self.add_signal(
                    SignalType.FUNDAMENTAL, SignalDirection.BEARISH, 0.5,
                    f"PB估值偏高({pb:.1f})"
                ))
        
        # 成长性
        revenue_growth = fundamental_data.get('revenue_growth')
        if revenue_growth and revenue_growth > 20:
            signals.append(self.add_signal(
                SignalType.FUNDAMENTAL, SignalDirection.BULLISH, 0.6,
                f"营收高增长({revenue_growth:.1f}%)"
            ))
        
        return signals


def analyze_signal_resonance(
    df: pd.DataFrame,
    pattern_result: Optional[Dict] = None,
    chanlun_result: Optional[Dict] = None,
    fundamental_data: Optional[Dict] = None
) -> ResonanceResult:
    """
    综合分析信号共振
    
    Args:
        df: 价格数据
        pattern_result: K线形态分析结果
        chanlun_result: 缠论分析结果
        fundamental_data: 基本面数据
        
    Returns:
        共振分析结果
    """
    scorer = SignalResonanceScorer()
    all_signals = []
    
    # 1. 技术信号
    all_signals.extend(scorer.analyze_technical_signals(df))
    
    # 2. 成交量信号
    all_signals.extend(scorer.analyze_volume_signals(df))
    
    # 3. K线形态信号
    if pattern_result:
        all_signals.extend(scorer.analyze_candlestick_signals(pattern_result))
    
    # 4. 缠论信号
    if chanlun_result:
        all_signals.extend(scorer.analyze_chanlun_signals(chanlun_result))
    
    # 5. 基本面信号
    if fundamental_data:
        all_signals.extend(scorer.analyze_fundamental_signals(fundamental_data))
    
    # 计算共振
    return scorer.calculate_resonance(all_signals)
