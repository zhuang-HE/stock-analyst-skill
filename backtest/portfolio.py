# -*- coding: utf-8 -*-
"""
持仓管理模块

管理回测中的资金、仓位、交易记录。
支持：
- 初始资金设定
- 买入/卖出操作（含手续费计算）
- 持仓成本追踪
- 交易记录完整保存
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Trade:
    """单笔交易记录"""
    trade_date: str           # 交易日期
    action: str               # buy / sell
    price: float              # 成交价格
    shares: int               # 成交股数
    amount: float             # 成交金额
    commission: float         # 手续费
    stamp_tax: float          # 印花税（卖出时收取）
    net_amount: float         # 净金额（含手续费）
    reason: str = ""          # 交易理由
    profit: Optional[float] = None  # 卖出时的盈亏


class Portfolio:
    """
    持仓管理器

    追踪：
    - 可用资金
    - 持仓数量与成本
    - 交易历史
    - 净值曲线

    手续费规则（A股）：
    - 佣金：万2.5（最低5元）
    - 印花税：卖出千1
    - 过户费：万0.1（忽略不计）
    """

    # 手续费参数
    COMMISSION_RATE = 0.00025   # 佣金费率
    COMMISSION_MIN = 5.0        # 最低佣金
    STAMP_TAX_RATE = 0.001      # 印花税率（仅卖出）
    SLIPPAGE_RATE = 0.001       # 滑点（默认千1）

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.00025,
        stamp_tax_rate: float = 0.001,
        slippage_rate: float = 0.001,
    ):
        """
        Args:
            initial_cash: 初始资金（默认10万）
            commission_rate: 佣金费率
            stamp_tax_rate: 印花税率
            slippage_rate: 滑点率
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission_rate = commission_rate
        self.stamp_tax_rate = stamp_tax_rate
        self.slippage_rate = slippage_rate

        # 持仓
        self.position = 0           # 持仓股数
        self.avg_cost = 0.0         # 平均持仓成本
        self.holding_value = 0.0    # 持仓市值

        # 交易记录
        self.trades: List[Trade] = []

        # 净值曲线：[(date, equity), ...]
        self.equity_curve: List[tuple] = []

        # 统计
        self._total_buy_amount = 0.0
        self._total_sell_amount = 0.0
        self._win_count = 0
        self._loss_count = 0

        # 买入失败日志（用于调试）
        self._buy_fail_log: List[str] = []

    @property
    def equity(self) -> float:
        """当前总权益 = 现金 + 持仓市值"""
        return self.cash + self.holding_value

    @property
    def return_pct(self) -> float:
        """总收益率"""
        if self.initial_cash <= 0:
            return 0.0
        return round((self.equity - self.initial_cash) / self.initial_cash * 100, 2)

    def _calc_commission(self, amount: float) -> float:
        """计算佣金"""
        commission = amount * self.commission_rate
        return max(commission, self.COMMISSION_MIN)

    def _calc_stamp_tax(self, amount: float) -> float:
        """计算印花税（仅卖出）"""
        return amount * self.stamp_tax_rate

    def buy(
        self,
        price: float,
        ratio: float = 1.0,
        shares: Optional[int] = None,
        reason: str = "",
        trade_date: str = "",
    ) -> Optional[Trade]:
        """
        买入操作。

        Args:
            price: 目标价格（会加上滑点）
            ratio: 买入仓位比例（0~1），使用可用资金的多少
            shares: 指定买入股数（优先于 ratio）
            reason: 交易理由
            trade_date: 交易日期

        Returns:
            Trade 对象，如果资金不足则返回 None
        """
        # 加上滑点
        actual_price = price * (1 + self.slippage_rate)

        # 计算买入股数
        if shares is not None:
            buy_shares = shares
        else:
            buy_amount = self.cash * ratio
            buy_shares = int(buy_amount / (actual_price * 100)) * 100  # A股必须100的整数倍

        if buy_shares <= 0:
            self._buy_fail_log.append(
                f"{trade_date}: 资金不足, price={actual_price:.2f}, "
                f"cash={self.cash:.2f}, 需≥{actual_price * 100:.2f}"
            )
            return None

        amount = buy_shares * actual_price
        commission = self._calc_commission(amount)
        net_amount = amount + commission

        if net_amount > self.cash:
            # 资金不足，减少股数
            buy_shares = int((self.cash - commission) / (actual_price * 100)) * 100
            if buy_shares <= 0:
                return None
            amount = buy_shares * actual_price
            commission = self._calc_commission(amount)
            net_amount = amount + commission

        # 更新持仓
        old_total = self.position * self.avg_cost
        new_total = old_total + amount
        self.position += buy_shares
        self.avg_cost = new_total / self.position if self.position > 0 else 0.0
        self.holding_value = self.position * actual_price

        # 扣减资金
        self.cash -= net_amount
        self._total_buy_amount += amount

        trade = Trade(
            trade_date=trade_date,
            action="buy",
            price=round(actual_price, 2),
            shares=buy_shares,
            amount=round(amount, 2),
            commission=round(commission, 2),
            stamp_tax=0.0,
            net_amount=round(net_amount, 2),
            reason=reason,
        )
        self.trades.append(trade)
        return trade

    def sell(
        self,
        price: float,
        ratio: float = 1.0,
        shares: Optional[int] = None,
        reason: str = "",
        trade_date: str = "",
    ) -> Optional[Trade]:
        """
        卖出操作。

        Args:
            price: 目标价格（会减去滑点）
            ratio: 卖出仓位比例（0~1）
            shares: 指定卖出股数
            reason: 交易理由
            trade_date: 交易日期
        """
        if self.position <= 0:
            return None

        # 减去滑点
        actual_price = price * (1 - self.slippage_rate)

        # 计算卖出股数
        if shares is not None:
            sell_shares = min(shares, self.position)
        else:
            sell_shares = int(self.position * ratio / 100) * 100
            if sell_shares <= 0 and self.position > 0:
                # 不足100股时按100股卖出（A股最小单位）
                sell_shares = min(100, self.position)
            sell_shares = min(sell_shares, self.position)

        if sell_shares <= 0:
            return None

        amount = sell_shares * actual_price
        commission = self._calc_commission(amount)
        stamp_tax = self._calc_stamp_tax(amount)
        net_amount = amount - commission - stamp_tax

        # 计算盈亏
        profit = (actual_price - self.avg_cost) * sell_shares - commission - stamp_tax

        # 更新持仓
        self.position -= sell_shares
        if self.position <= 0:
            self.position = 0
            self.avg_cost = 0.0
            self.holding_value = 0.0
        else:
            self.holding_value = self.position * actual_price

        # 增加资金
        self.cash += net_amount
        self._total_sell_amount += amount

        # 盈亏统计
        if profit > 0:
            self._win_count += 1
        elif profit < 0:
            self._loss_count += 1

        trade = Trade(
            trade_date=trade_date,
            action="sell",
            price=round(actual_price, 2),
            shares=sell_shares,
            amount=round(amount, 2),
            commission=round(commission, 2),
            stamp_tax=round(stamp_tax, 2),
            net_amount=round(net_amount, 2),
            reason=reason,
            profit=round(profit, 2),
        )
        self.trades.append(trade)
        return trade

    def update_market_value(self, price: float, trade_date: str = ""):
        """更新持仓市值（每日收盘后调用）"""
        self.holding_value = self.position * price
        self.equity_curve.append((trade_date, round(self.equity, 2)))

    @property
    def win_rate(self) -> float:
        """胜率"""
        total = self._win_count + self._loss_count
        if total == 0:
            return 0.0
        return round(self._win_count / total * 100, 2)

    def summary(self) -> dict:
        """持仓与交易摘要"""
        return {
            "initial_cash": self.initial_cash,
            "current_equity": round(self.equity, 2),
            "cash": round(self.cash, 2),
            "position": self.position,
            "avg_cost": round(self.avg_cost, 2),
            "holding_value": round(self.holding_value, 2),
            "return_pct": self.return_pct,
            "total_trades": len(self.trades),
            "buy_count": sum(1 for t in self.trades if t.action == "buy"),
            "sell_count": sum(1 for t in self.trades if t.action == "sell"),
            "win_rate": self.win_rate,
        }
