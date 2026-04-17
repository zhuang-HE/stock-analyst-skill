# -*- coding: utf-8 -*-
"""
绩效评估模块

计算回测的各种绩效指标：
- 累计收益率
- 年化收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比
- 交易统计
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


def calc_metrics(
    equity_curve: List[tuple],
    trades: list,
    initial_cash: float = 100000.0,
    risk_free_rate: float = 0.03,
    trading_days: int = 242,
) -> Dict:
    """
    计算回测绩效指标。

    Args:
        equity_curve: [(date, equity), ...] 净值曲线
        trades: 交易记录列表
        initial_cash: 初始资金
        risk_free_rate: 无风险利率（年化，默认3%）
        trading_days: 一年交易日数（默认242）

    Returns:
        绩效指标字典
    """
    if not equity_curve or len(equity_curve) < 2:
        return _empty_metrics()

    # 提取净值序列
    dates = [e[0] for e in equity_curve]
    equities = np.array([e[1] for e in equity_curve])

    # ─── 收益率 ───
    total_return = (equities[-1] - initial_cash) / initial_cash
    total_return_pct = round(total_return * 100, 2)

    # 回测天数
    total_days = len(equities)
    total_years = total_days / trading_days if trading_days > 0 else 0

    # 年化收益率
    if total_years > 0 and equities[-1] > 0:
        annualized_return = (equities[-1] / initial_cash) ** (1 / total_years) - 1
    else:
        annualized_return = 0.0
    annualized_return_pct = round(annualized_return * 100, 2)

    # ─── 日收益率序列 ───
    daily_returns = np.diff(equities) / equities[:-1]
    daily_returns = daily_returns[~np.isnan(daily_returns)]

    # ─── 夏普比率 ───
    if len(daily_returns) > 0 and np.std(daily_returns) > 0:
        daily_rf = risk_free_rate / trading_days
        sharpe = (np.mean(daily_returns) - daily_rf) / np.std(daily_returns) * np.sqrt(trading_days)
    else:
        sharpe = 0.0
    sharpe = round(float(sharpe), 2)

    # ─── 最大回撤 ───
    peak = equities[0]
    max_drawdown = 0.0
    max_drawdown_start = ""
    max_drawdown_end = ""

    for i, eq in enumerate(equities):
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        if dd > max_drawdown:
            max_drawdown = dd
            max_drawdown_end = dates[i]

    # 找到回撤起点
    if max_drawdown > 0:
        for i, eq in enumerate(equities):
            if eq == peak:
                max_drawdown_start = dates[i] if i < len(dates) else ""

    max_drawdown_pct = round(max_drawdown * 100, 2)

    # ─── 交易统计 ───
    buy_trades = [t for t in trades if t.action == "buy"]
    sell_trades = [t for t in trades if t.action == "sell"]

    # 盈亏统计
    profits = [t.profit for t in sell_trades if t.profit is not None]
    win_trades = [p for p in profits if p > 0]
    loss_trades = [p for p in profits if p < 0]

    win_rate = round(len(win_trades) / len(profits) * 100, 2) if profits else 0.0
    avg_profit = round(float(np.mean(win_trades)), 2) if win_trades else 0.0
    avg_loss = round(float(np.mean(loss_trades)), 2) if loss_trades else 0.0
    profit_loss_ratio = round(abs(avg_profit / avg_loss), 2) if avg_loss != 0 else float('inf')

    total_commission = round(sum(t.commission + t.stamp_tax for t in trades), 2)

    # ─── 波动率 ───
    if len(daily_returns) > 0:
        annual_volatility = round(float(np.std(daily_returns) * np.sqrt(trading_days) * 100), 2)
    else:
        annual_volatility = 0.0

    # ─── Calmar 比率 ───
    calmar = round(annualized_return / max_drawdown, 2) if max_drawdown > 0 else float('inf')

    return {
        # 收益
        "total_return_pct": total_return_pct,
        "annualized_return_pct": annualized_return_pct,
        "initial_cash": initial_cash,
        "final_equity": round(float(equities[-1]), 2),
        "profit": round(float(equities[-1] - initial_cash), 2),

        # 风险
        "max_drawdown_pct": max_drawdown_pct,
        "max_drawdown_start": max_drawdown_start,
        "max_drawdown_end": max_drawdown_end,
        "annual_volatility_pct": annual_volatility,

        # 风险调整收益
        "sharpe_ratio": sharpe,
        "calmar_ratio": calmar,

        # 交易
        "total_trades": len(trades),
        "buy_count": len(buy_trades),
        "sell_count": len(sell_trades),
        "win_rate": win_rate,
        "avg_profit": avg_profit,
        "avg_loss": avg_loss,
        "profit_loss_ratio": profit_loss_ratio,
        "total_commission": total_commission,

        # 回测信息
        "backtest_days": total_days,
        "backtest_years": round(total_years, 2),
        "start_date": dates[0] if dates else "",
        "end_date": dates[-1] if dates else "",
    }


def _empty_metrics() -> Dict:
    """空绩效指标"""
    return {
        "total_return_pct": 0.0,
        "annualized_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "sharpe_ratio": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
    }


def format_metrics(metrics: Dict) -> str:
    """格式化绩效指标为可读文本"""
    lines = [
        "╔══════════════════════════════════════╗",
        "║   回测绩效报告                       ║",
        "╚══════════════════════════════════════╝",
        "",
        f"  回测区间: {metrics.get('start_date', '')} ~ {metrics.get('end_date', '')}",
        f"  回测天数: {metrics.get('backtest_days', 0)} 天 ({metrics.get('backtest_years', 0)} 年)",
        "",
        "── 收益 ──────────────────────────────",
        f"  初始资金: ¥{metrics.get('initial_cash', 0):,.0f}",
        f"  最终权益: ¥{metrics.get('final_equity', 0):,.2f}",
        f"  总收益:   ¥{metrics.get('profit', 0):,.2f}",
        f"  累计收益率: {metrics.get('total_return_pct', 0):+.2f}%",
        f"  年化收益率: {metrics.get('annualized_return_pct', 0):+.2f}%",
        "",
        "── 风险 ──────────────────────────────",
        f"  最大回撤: {metrics.get('max_drawdown_pct', 0):.2f}%",
        f"  年化波动率: {metrics.get('annual_volatility_pct', 0):.2f}%",
        "",
        "── 风险调整收益 ──────────────────────",
        f"  夏普比率: {metrics.get('sharpe_ratio', 0):.2f}",
        f"  Calmar比率: {metrics.get('calmar_ratio', 0):.2f}",
        "",
        "── 交易统计 ──────────────────────────",
        f"  总交易: {metrics.get('total_trades', 0)} 笔",
        f"  买入: {metrics.get('buy_count', 0)} / 卖出: {metrics.get('sell_count', 0)}",
        f"  胜率: {metrics.get('win_rate', 0):.1f}%",
        f"  平均盈利: ¥{metrics.get('avg_profit', 0):,.2f}",
        f"  平均亏损: ¥{metrics.get('avg_loss', 0):,.2f}",
        f"  盈亏比: {metrics.get('profit_loss_ratio', 0):.2f}",
        f"  总手续费: ¥{metrics.get('total_commission', 0):,.2f}",
        "",
    ]
    return "\n".join(lines)
