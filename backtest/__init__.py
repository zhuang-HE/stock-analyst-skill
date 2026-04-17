# -*- coding: utf-8 -*-
"""
回测框架 (backtest)

基于事件驱动的轻量回测引擎，支持：
- 多策略并行回测
- 持仓管理与资金追踪
- 绩效评估（收益率、夏普、最大回撤、胜率等）
- 结果可视化

用法：
    from backtest import BacktestEngine, Strategy, Portfolio

    # 定义策略
    class MyStrategy(Strategy):
        def on_bar(self, bar, portfolio, indicators):
            if indicators['rsi_14'] < 30 and portfolio.position == 0:
                portfolio.buy(bar['close'], reason='RSI超卖')
            elif indicators['rsi_14'] > 70 and portfolio.position > 0:
                portfolio.sell(bar['close'], reason='RSI超买')

    # 运行回测
    engine = BacktestEngine(ts_code='600519.SH')
    result = engine.run(MyStrategy())
    print(result['metrics'])
"""

from .engine import BacktestEngine
from .strategy import Strategy, MACDStrategy, MAStrategy, RSIStrategy
from .portfolio import Portfolio, Trade
from .metrics import calc_metrics

__all__ = [
    "BacktestEngine",
    "Strategy",
    "MACDStrategy",
    "MAStrategy",
    "RSIStrategy",
    "Portfolio",
    "Trade",
    "calc_metrics",
]

__version__ = "1.0.0"
