# -*- coding: utf-8 -*-
"""
策略基类与内置策略

内置策略：
- MAStrategy: 均线交叉策略（MA5 上穿 MA20 买入，下穿卖出）
- MACDStrategy: MACD 金叉/死叉策略
- RSIStrategy: RSI 超买超卖策略

增强策略（含风控）：
- MAWithStopStrategy: MA均线 + ATR止损 + 仓位管理
- MACDWithADXStrategy: MACD + ADX趋势过滤，减少震荡市假信号
- BuyAndHoldStrategy: 买入持有基准策略（开仓后不动）

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
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

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


# ═══════════════════════════════════════════════════════════════
#  增强策略（含风控）
# ═══════════════════════════════════════════════════════════════


class MAWithStopStrategy(Strategy):
    """
    均线交叉策略 + ATR止损 + 固定比例仓位

    买入条件：MA5 上穿 MA20
    卖出条件：MA5 下穿 MA20 OR 浮亏超过 stop_loss_pct OR 价格低于 ATR止损线
    仓位管理：每次使用固定比例资金（默认90%）

    参数：
        fast_period: 快线周期（默认5）
        slow_period: 慢线周期（默认20）
        stop_loss_pct: 最大亏损比例（默认8%）
        atr_mult: ATR 止损倍数（默认2.0x），以买入均价为参考
        buy_ratio: 买入资金比例（默认0.9）
    """

    name = "MA均线+ATR止损"
    description = "MA均线交叉买卖 + ATR止损 + 固定比例仓位"

    def __init__(
        self,
        fast_period: int = 5,
        slow_period: int = 20,
        stop_loss_pct: float = 0.08,
        atr_mult: float = 2.0,
        buy_ratio: float = 0.9,
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.stop_loss_pct = stop_loss_pct
        self.atr_mult = atr_mult
        self.buy_ratio = buy_ratio

        self._prev_fast: Optional[float] = None
        self._prev_slow: Optional[float] = None
        self._stop_price: Optional[float] = None  # 止损价格

    def on_start(self, portfolio: Portfolio):
        self._prev_fast = None
        self._prev_slow = None
        self._stop_price = None

    def on_bar(self, bar: dict, portfolio: Portfolio, indicators: dict):
        fast_key = f"ma{self.fast_period}"
        slow_key = f"ma{self.slow_period}"
        fast = indicators.get(fast_key)
        slow = indicators.get(slow_key)
        atr = indicators.get("atr_14")
        close = bar["close"]
        trade_date = bar.get("trade_date", "")

        # ── 止损检查（持仓时每日检查）──
        if portfolio.position > 0:
            # ATR动态止损
            if atr and self._stop_price is not None:
                # 每日更新止损价（只上移，不下移 — 追踪止损）
                trailing_stop = close - self.atr_mult * atr
                if trailing_stop > self._stop_price:
                    self._stop_price = trailing_stop

            # 触发止损
            if self._stop_price is not None and close <= self._stop_price:
                portfolio.sell(
                    close,
                    reason=f"ATR止损触发(止损价={self._stop_price:.2f})",
                    trade_date=trade_date,
                )
                self._stop_price = None
                self._prev_fast = fast
                self._prev_slow = slow
                return

            # 固定比例止损（兜底）
            if portfolio.avg_cost > 0:
                loss_pct = (close - portfolio.avg_cost) / portfolio.avg_cost
                if loss_pct <= -self.stop_loss_pct:
                    portfolio.sell(
                        close,
                        reason=f"固定止损({loss_pct*100:.1f}%)",
                        trade_date=trade_date,
                    )
                    self._stop_price = None
                    self._prev_fast = fast
                    self._prev_slow = slow
                    return

        # ── 均线信号 ──
        if fast is None or slow is None:
            self._prev_fast = fast
            self._prev_slow = slow
            return

        if self._prev_fast is not None and self._prev_slow is not None:
            # 金叉：快线上穿慢线
            if self._prev_fast <= self._prev_slow and fast > slow:
                if portfolio.position == 0:
                    trade = portfolio.buy(
                        close,
                        ratio=self.buy_ratio,
                        reason=f"MA{self.fast_period}上穿MA{self.slow_period}",
                        trade_date=trade_date,
                    )
                    if trade and atr:
                        # 买入时设置初始止损价
                        self._stop_price = close - self.atr_mult * atr

            # 死叉：快线下穿慢线
            elif self._prev_fast >= self._prev_slow and fast < slow:
                if portfolio.position > 0:
                    portfolio.sell(
                        close,
                        reason=f"MA{self.fast_period}下穿MA{self.slow_period}",
                        trade_date=trade_date,
                    )
                    self._stop_price = None

        self._prev_fast = fast
        self._prev_slow = slow


class MACDWithADXStrategy(Strategy):
    """
    MACD 金叉/死叉 + ADX 趋势过滤

    只有当 ADX > adx_threshold 时（确认趋势存在）才接受 MACD 信号，
    从而过滤掉震荡市的频繁假信号。

    买入条件：MACD金叉 AND ADX > adx_threshold
    卖出条件：MACD死叉 OR ADX < adx_exit（趋势消失止盈）

    ADX 在线计算（14日，不依赖数据库字段）：
        ADX = EMA of DX，DX = |+DI - -DI| / (+DI + -DI) * 100

    参数：
        adx_period: ADX 计算周期（默认14）
        adx_threshold: 趋势过滤阈值（默认25，>25代表有趋势）
        adx_exit: 趋势消失退出阈值（默认20）
        stop_loss_pct: 固定比例止损（默认8%）
        buy_ratio: 买入资金比例（默认0.9）
    """

    name = "MACD+ADX趋势过滤"
    description = "MACD金叉死叉 + ADX趋势过滤，减少震荡市假信号"

    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        adx_exit: float = 20.0,
        stop_loss_pct: float = 0.08,
        buy_ratio: float = 0.9,
    ):
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.adx_exit = adx_exit
        self.stop_loss_pct = stop_loss_pct
        self.buy_ratio = buy_ratio

        # MACD 状态
        self._prev_dif: Optional[float] = None
        self._prev_dea: Optional[float] = None

        # ADX 在线计算所需状态
        self._prev_high: Optional[float] = None
        self._prev_low: Optional[float] = None
        self._prev_close: Optional[float] = None

        # 平滑均值（Wilder平滑）
        self._smooth_plus_dm: Optional[float] = None
        self._smooth_minus_dm: Optional[float] = None
        self._smooth_tr: Optional[float] = None
        self._adx_smooth: Optional[float] = None  # ADX的Wilder平滑
        self._adx: float = 0.0
        self._bar_count: int = 0

        # 暖机期数据（用于第一次计算）
        self._warmup_plus_dm: List[float] = []
        self._warmup_minus_dm: List[float] = []
        self._warmup_tr: List[float] = []

    def on_start(self, portfolio: Portfolio):
        # 重置所有状态
        self._prev_dif = None
        self._prev_dea = None
        self._prev_high = None
        self._prev_low = None
        self._prev_close = None
        self._smooth_plus_dm = None
        self._smooth_minus_dm = None
        self._smooth_tr = None
        self._adx_smooth = None
        self._adx = 0.0
        self._bar_count = 0
        self._warmup_plus_dm = []
        self._warmup_minus_dm = []
        self._warmup_tr = []

    def _update_adx(self, high: float, low: float, close: float) -> float:
        """Wilder法在线计算ADX，返回当前ADX值"""
        n = self.adx_period

        if self._prev_high is None:
            self._prev_high = high
            self._prev_low = low
            self._prev_close = close
            return 0.0

        # True Range
        tr = max(
            high - low,
            abs(high - self._prev_close),
            abs(low - self._prev_close),
        )

        # Directional Movement
        plus_dm = max(high - self._prev_high, 0) if (high - self._prev_high) > (self._prev_low - low) else 0.0
        minus_dm = max(self._prev_low - low, 0) if (self._prev_low - low) > (high - self._prev_high) else 0.0

        self._bar_count += 1

        if self._bar_count <= n:
            # 暖机期：积累数据
            self._warmup_plus_dm.append(plus_dm)
            self._warmup_minus_dm.append(minus_dm)
            self._warmup_tr.append(tr)

            if self._bar_count == n:
                # 第一个平滑值 = 简单求和
                self._smooth_plus_dm = sum(self._warmup_plus_dm)
                self._smooth_minus_dm = sum(self._warmup_minus_dm)
                self._smooth_tr = sum(self._warmup_tr)
        else:
            # Wilder平滑：S_new = S_old - S_old/n + new_val
            self._smooth_plus_dm = self._smooth_plus_dm - self._smooth_plus_dm / n + plus_dm
            self._smooth_minus_dm = self._smooth_minus_dm - self._smooth_minus_dm / n + minus_dm
            self._smooth_tr = self._smooth_tr - self._smooth_tr / n + tr

        # 更新历史
        self._prev_high = high
        self._prev_low = low
        self._prev_close = close

        if self._smooth_tr is None or self._smooth_tr == 0:
            return self._adx

        # DI计算
        plus_di = 100 * self._smooth_plus_dm / self._smooth_tr
        minus_di = 100 * self._smooth_minus_dm / self._smooth_tr
        di_sum = plus_di + minus_di

        if di_sum == 0:
            dx = 0.0
        else:
            dx = 100 * abs(plus_di - minus_di) / di_sum

        # ADX = Wilder平滑的DX
        if self._adx_smooth is None:
            self._adx_smooth = dx
        else:
            self._adx_smooth = (self._adx_smooth * (n - 1) + dx) / n

        self._adx = self._adx_smooth
        return self._adx

    def on_bar(self, bar: dict, portfolio: Portfolio, indicators: dict):
        dif = indicators.get("macd_dif")
        dea = indicators.get("macd_dea")
        close = bar["close"]
        high = bar["high"]
        low = bar["low"]
        trade_date = bar.get("trade_date", "")

        # 更新ADX
        adx = self._update_adx(high, low, close)

        # ── 止损检查 ──
        if portfolio.position > 0 and portfolio.avg_cost > 0:
            loss_pct = (close - portfolio.avg_cost) / portfolio.avg_cost
            if loss_pct <= -self.stop_loss_pct:
                portfolio.sell(
                    close,
                    reason=f"固定止损({loss_pct*100:.1f}%)",
                    trade_date=trade_date,
                )
                self._prev_dif = dif
                self._prev_dea = dea
                return

            # ADX趋势消失止盈（持仓时ADX跌破exit阈值）
            if adx > 0 and adx < self.adx_exit and portfolio.position > 0:
                portfolio.sell(
                    close,
                    reason=f"ADX趋势消失({adx:.1f}<{self.adx_exit})",
                    trade_date=trade_date,
                )
                self._prev_dif = dif
                self._prev_dea = dea
                return

        # ── MACD信号 ──
        if dif is None or dea is None:
            self._prev_dif = dif
            self._prev_dea = dea
            return

        if self._prev_dif is not None and self._prev_dea is not None:
            # 金叉 + ADX趋势确认
            if self._prev_dif <= self._prev_dea and dif > dea:
                if portfolio.position == 0 and adx >= self.adx_threshold:
                    portfolio.buy(
                        close,
                        ratio=self.buy_ratio,
                        reason=f"MACD金叉(ADX={adx:.1f})",
                        trade_date=trade_date,
                    )
                elif portfolio.position == 0 and adx < self.adx_threshold:
                    # 信号被ADX过滤
                    pass

            # 死叉卖出（无需ADX确认）
            elif self._prev_dif >= self._prev_dea and dif < dea:
                if portfolio.position > 0:
                    portfolio.sell(
                        close,
                        reason=f"MACD死叉(ADX={adx:.1f})",
                        trade_date=trade_date,
                    )

        self._prev_dif = dif
        self._prev_dea = dea


class BuyAndHoldStrategy(Strategy):
    """
    买入持有基准策略

    第一根K线买入，最后一根K线卖出，中间不操作。
    用于与主动策略比较，衡量策略是否创造了真实 alpha。

    参数：
        buy_ratio: 买入资金比例（默认0.9）
    """

    name = "买入持有"
    description = "第一根K线买入，持有到期末卖出，用作基准对比"

    def __init__(self, buy_ratio: float = 0.9):
        self.buy_ratio = buy_ratio
        self._bought = False

    def on_start(self, portfolio: Portfolio):
        self._bought = False

    def on_bar(self, bar: dict, portfolio: Portfolio, indicators: dict):
        if not self._bought and portfolio.position == 0:
            portfolio.buy(
                bar["close"],
                ratio=self.buy_ratio,
                reason="买入持有基准",
                trade_date=bar.get("trade_date", ""),
            )
            self._bought = True

    def on_end(self, portfolio: Portfolio):
        # 持仓没平，由引擎在最后一日按收盘价强平（通过equity_curve已记录）
        # 不需要额外操作，净值曲线已反映持仓市值
        pass
