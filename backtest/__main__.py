# -*- coding: utf-8 -*-
"""
回测框架命令行入口

用法：
    python -m backtest --code 600519.SH --strategy ma
    python -m backtest --code 600519.SH --strategy macd --start 20240101
    python -m backtest --codes 600519.SH,000001.SZ --strategy rsi
    python -m backtest --code 600519.SH --compare
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="A股回测框架")
    parser.add_argument("--code", default=None, help="股票代码（如 600519.SH）")
    parser.add_argument("--codes", default=None, help="多只股票（逗号分隔）")
    parser.add_argument("--strategy", default="ma",
                        choices=["ma", "macd", "rsi"],
                        help="策略选择（默认ma）")
    parser.add_argument("--start", default=None, help="起始日期 YYYYMMDD")
    parser.add_argument("--end", default=None, help="结束日期 YYYYMMDD")
    parser.add_argument("--cash", type=float, default=1000000.0, help="初始资金（默认100万）")
    parser.add_argument("--compare", action="store_true", help="比较所有内置策略")
    args = parser.parse_args()

    # 延迟导入
    from backtest.engine import BacktestEngine
    from backtest.strategy import MAStrategy, MACDStrategy, RSIStrategy

    engine = BacktestEngine(
        start_date=args.start,
        end_date=args.end,
        initial_cash=args.cash,
    )

    # 选择策略
    strategy_map = {
        "ma": MAStrategy(),
        "macd": MACDStrategy(),
        "rsi": RSIStrategy(),
    }

    if args.compare:
        # 比较所有策略
        if not args.code:
            print("请指定 --code")
            sys.exit(1)
        engine.ts_code = args.code
        results = engine.compare_strategies(list(strategy_map.values()), ts_code=args.code)

    elif args.codes:
        # 批量回测
        codes = [c.strip() for c in args.codes.split(",")]
        strategy = strategy_map[args.strategy]
        results = engine.run_batch(codes, strategy)

    elif args.code:
        # 单只股票回测
        strategy = strategy_map[args.strategy]
        result = engine.run(strategy, ts_code=args.code)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
