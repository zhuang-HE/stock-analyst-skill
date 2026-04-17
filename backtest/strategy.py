# -*- coding: utf-8 -*-
"""
策略基类与内置策略

内置策略：
- MAStrategy: 均线交叉策略（MA5 上穿 MA20 买入，下穿卖出）
- MACDStrategy: MACD 金叉/死叉策略
- RSIStrategy: RSI 超买超卖策略

自定义策略示例：
    class MyStrategy(Strategy):
        name = "我的策略"

        def on_bar(self, bar, portfolio, indicators):
            if portfolio.position == 0 and indicators['rsi_14'] < 30:
                portfolio.buy(bar['close'], reason='RSI超卖买入')
            elif portfolio.position > 0 and indicators['rsi_14'] > 70:
                portfolio.sell(bar['close'], reason='RSI超买卖出')
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from .portfolio import Portfolio


class Strategy(ABC):
    """
    策略基类。

    子类必须实现 on_bar 方法。
    可选实现 on_start / on_end 进行初始化/收尾。
    """

    name: str = "BaseStrategy"
    description: str = ""

    def on_start(self, portfolio: Portfolio):
        """回测开始前的初始化（可选覆盖）"""
        pass

    @abstractmethod
    def on_bar(self, bar: dict, portfolio: Portfolio, indicators: dict):
        """
        每根K线触发的交易逻辑。

        Args:
            bar: 当日K线数据 {trade_date, open, high, low, close, vol, ...}
            portfolio: 持仓管理器
            indicators: 当日技术指标 {ma5, ma20, rsi_14, macd_dif, ...}
        """
        pass

    def on_end(self, portfolio: Portfolio):
        """回测结束后的收尾（可选覆盖）"""
        pass


# ═══════════════════════════════════════════════════════════════
#  内置策略
# ═══════════════════════════════════════════════════════════════


class MAStrategy(Strategy):
    """
    均线交叉策略

    买入：MA5 上穿 MA20
    卖出：MA5 下穿 MA20

    参数：
        fast_period: 快线周期（默认5）
        slow_period: 慢线周期（默认20）
        buy_ratio: 买入资金比例（默认0.9）
    """

    name = "均线交叉策略"
    description = "MA5/MA20 金叉买入，死叉卖出"

    def __init__(
        self,
        fast_period: int = 5,
        slow_period: int = 20,
        buy_ratio: float = 0.9,
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.buy_ratio = buy_ratio
        self._prev_fast: Optional[float] = None
        self._prev_slow: Optional[float] = None

    def on_bar(self, bar: dict, portfolio: Portfolio, indicators: dict):
        fast_key = f"ma{self.fast_period}"
        slow_key = f"ma{self.slow_period}"

        fast = indicators.get(fast_key)
        slow = indicators.get(slow_key)

        if fast is None or slow is None:
            return

        if self._prev_fast is not None and self._prev_slow is not None:
            # 金叉：快线上穿慢线
            if self._prev_fast <= self._prev_slow and fast > slow:
                if portfolio.position == 0:
                    portfolio.buy(
                        bar["close"],
                        ratio=self.buy_ratio,
                        reason=f"MA{self.fast_period}上穿MA{self.slow_period}",
                        trade_date=bar.get("trade_date", ""),
                    )
            # 死叉：快线下穿慢线
            elif self._prev_fast >= self._prev_slow and fast < slow:
                if portfolio.position > 0:
                    portfolio.sell(
                        bar["close"],
                        reason=f"MA{self.fast_period}下穿MA{self.slow_period}",
                        trade_date=bar.get("trade_date", ""),
                    )

        self._prev_fast = fast
        self._prev_slow = slow


class MACDStrategy(Strategy):
    """
    MACD 金叉/死叉策略

    买入：DIF 上穿 DEA（金叉）
    卖出：DIF 下穿 DEA（死叉）

    参数：
        buy_on_zero_cross: 是否在 DIF 上穿零轴时也买入（默认False）
    """

    name = "MACD金叉死叉策略"
    description = "MACD金叉买入，死叉卖出"

    def __init__(self, buy_on_zero_cross: bool = False):
        self.buy_on_zero_cross = buy_on_zero_cross
        self._prev_dif: Optional[float] = None
        self._prev_dea: Optional[float] = None

    def on_bar(self, bar: dict, portfolio: Portfolio, indicators: dict):
        dif = indicators.get("macd_dif")
        dea = indicators.get("macd_dea")

        if dif is None or dea is None:
            return

        if self._prev_dif is not None and self._prev_dea is not None:
            # 金叉：DIF 上穿 DEA
            if self._prev_dif <= self._prev_dea and dif > dea:
                if portfolio.position == 0:
                    portfolio.buy(
                        bar["close"],
                        reason="MACD金叉",
                        trade_date=bar.get("trade_date", ""),
                    )

            # 死叉：DIF 下穿 DEA
            elif self._prev_dif >= self._prev_dea and dif < dea:
                if portfolio.position > 0:
                    portfolio.sell(
                        bar["close"],
                        reason="MACD死叉",
                        trade_date=bar.get("trade_date", ""),
                    )

            # DIF 上穿零轴
            if self.buy_on_zero_cross and self._prev_dif <= 0 and dif > 0:
                if portfolio.position == 0:
                    portfolio.buy(
                        bar["close"],
                        reason="DIF上穿零轴",
                        trade_date=bar.get("trade_date", ""),
                    )

        self._prev_dif = dif
        self._prev_dea = dea


class RSIStrategy(Strategy):
    """
    RSI 超买超卖策略

    买入：RSI14 低于 oversold（默认30）
    卖出：RSI14 高于 overbought（默认70）

    参数：
        period: RSI周期（默认14）
        oversold: 超卖阈值（默认30）
        overbought: 超买阈值（默认70）
    """

    name = "RSI超买超卖策略"
    description = "RSI超卖买入，超买卖出"

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70,
    ):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def on_bar(self, bar: dict, portfolio: Portfolio, indicators: dict):
        rsi_key = f"rsi_{self.period}"
        rsi = indicators.get(rsi_key)

        if rsi is None:
            return

        # 超卖买入
        if rsi < self.oversold and portfolio.position == 0:
            portfolio.buy(
                bar["close"],
                reason=f"RSI{self.period}超卖({rsi:.1f})",
                trade_date=bar.get("trade_date", ""),
            )
        # 超买卖出
        elif rsi > self.overbought and portfolio.position > 0:
            portfolio.sell(
                bar["close"],
                reason=f"RSI{self.period}超买({rsi:.1f})",
                trade_date=bar.get("trade_date", ""),
            )
