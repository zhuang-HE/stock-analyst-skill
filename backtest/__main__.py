# -*- coding: utf-8 -*-
"""
回测框架命令行入口

用法：
    python -m backtest --code 600519.SH --strategy ma
    python -m backtest --code 600519.SH --strategy macd --start 20240101
    python -m backtest --codes 600519.SH,000001.SZ --strategy rsi
    python -m backtest --code 600519.SH --compare
    python -m backtest --code 600519.SH --strategy ma-stop   # MA+ATR止损
    python -m backtest --code 600519.SH --strategy macd-adx  # MACD+ADX过滤
    python -m backtest --code 600519.SH --benchmark          # 与买入持有对比
    python -m backtest --codes 600519.SH,000858.SZ --benchmark  # 批量+基准对比
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="A股回测框架")
    parser.add_argument("--code", default=None, help="股票代码（如 600519.SH）")
    parser.add_argument("--codes", default=None, help="多只股票（逗号分隔）")
    parser.add_argument("--strategy", default="ma",
                        choices=["ma", "macd", "rsi", "ma-stop", "macd-adx"],
                        help="策略选择（默认ma）")
    parser.add_argument("--start", default=None, help="起始日期 YYYYMMDD")
    parser.add_argument("--end", default=None, help="结束日期 YYYYMMDD")
    parser.add_argument("--cash", type=float, default=1000000.0, help="初始资金（默认100万）")
    parser.add_argument("--compare", action="store_true", help="比较所有内置策略")
    parser.add_argument("--benchmark", action="store_true",
                        help="与买入持有基准对比（输出alpha分析）")
    args = parser.parse_args()

    # 延迟导入
    from backtest.engine import BacktestEngine
    from backtest.strategy import (
        MAStrategy, MACDStrategy, RSIStrategy,
        MAWithStopStrategy, MACDWithADXStrategy, BuyAndHoldStrategy,
    )

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
        "ma-stop": MAWithStopStrategy(),
        "macd-adx": MACDWithADXStrategy(),
    }

    if args.compare:
        # 比较所有策略
        if not args.code:
            print("请指定 --code")
            sys.exit(1)
        all_strategies = [
            MAStrategy(),
            MACDStrategy(),
            RSIStrategy(),
            MAWithStopStrategy(),
            MACDWithADXStrategy(),
            BuyAndHoldStrategy(),
        ]
        engine.ts_code = args.code
        results = engine.compare_strategies(all_strategies, ts_code=args.code)

    elif args.codes:
        # 批量回测
        codes = [c.strip() for c in args.codes.split(",")]
        strategy = strategy_map[args.strategy]

        if args.benchmark:
            # 批量回测 + 买入持有基准对比
            _run_batch_with_benchmark(engine, codes, strategy)
        else:
            results = engine.run_batch(codes, strategy)

    elif args.code:
        # 单只股票回测
        strategy = strategy_map[args.strategy]

        if args.benchmark:
            # 与买入持有基准对比
            _run_with_benchmark(engine, args.code, strategy)
        else:
            result = engine.run(strategy, ts_code=args.code)

    else:
        parser.print_help()
        sys.exit(1)


def _run_with_benchmark(engine, ts_code: str, strategy):
    """单只股票：策略 vs 买入持有基准对比"""
    from backtest.strategy import BuyAndHoldStrategy

    print(f"\n{'='*60}")
    print(f"  Alpha 分析: {ts_code} | 策略: {strategy.name}")
    print(f"{'='*60}")

    # 跑策略
    result = engine.run(strategy, ts_code=ts_code, verbose=True)
    # 跑基准
    benchmark = BuyAndHoldStrategy()
    benchmark_result = engine.run(benchmark, ts_code=ts_code, verbose=True)

    if "error" in result or "error" in benchmark_result:
        print("  ⚠ 数据加载失败")
        return

    m = result["metrics"]
    bm = benchmark_result["metrics"]

    print(f"\n{'='*60}")
    print(f"  {'指标':<20} {'策略':>12} {'买入持有':>12} {'Alpha':>10}")
    print(f"  {'-'*56}")

    metrics_to_compare = [
        ("总收益%", "total_return_pct", "{:+.2f}%"),
        ("年化收益%", "annualized_return_pct", "{:+.2f}%"),
        ("夏普比率", "sharpe_ratio", "{:.3f}"),
        ("最大回撤%", "max_drawdown_pct", "{:.2f}%"),
        ("胜率%", "win_rate", "{:.1f}%"),
        ("交易次数", "trade_count", "{:.0f}"),
        ("Calmar比率", "calmar_ratio", "{:.3f}"),
    ]

    for label, key, fmt in metrics_to_compare:
        strat_val = m.get(key, 0)
        bm_val = bm.get(key, 0)
        if key in ("max_drawdown_pct",):
            alpha = bm_val - strat_val  # 回撤越小越好
        elif key in ("trade_count",):
            alpha = None
        else:
            alpha = strat_val - bm_val

        strat_str = fmt.format(strat_val)
        bm_str = fmt.format(bm_val)
        alpha_str = f"{alpha:+.2f}" if alpha is not None else "N/A"
        print(f"  {label:<20} {strat_str:>12} {bm_str:>12} {alpha_str:>10}")

    # 综合评价
    ret_alpha = m.get("total_return_pct", 0) - bm.get("total_return_pct", 0)
    dd_alpha = bm.get("max_drawdown_pct", 0) - m.get("max_drawdown_pct", 0)
    print(f"\n  {'结论'}")
    if ret_alpha > 0 and dd_alpha > 0:
        print(f"  ✅ 策略优于基准：超额收益 {ret_alpha:+.2f}%，同时回撤减少 {dd_alpha:.2f}%")
    elif ret_alpha > 0 and dd_alpha <= 0:
        print(f"  ⚠ 策略收益更高(+{ret_alpha:.2f}%)但回撤也更大({-dd_alpha:.2f}%)")
    elif ret_alpha <= 0 and dd_alpha > 0:
        print(f"  ⚠ 策略回撤更小({dd_alpha:.2f}%)但收益低于基准({ret_alpha:.2f}%)")
    else:
        print(f"  ❌ 策略不如买入持有：收益 {ret_alpha:.2f}%，回撤差 {-dd_alpha:.2f}%")


def _run_batch_with_benchmark(engine, codes: list, strategy):
    """批量：策略 vs 买入持有基准对比"""
    from backtest.strategy import BuyAndHoldStrategy

    print(f"\n{'='*70}")
    print(f"  批量 Alpha 分析 | 策略: {strategy.name}")
    print(f"{'='*70}")
    print(f"  {'代码':<12} {'策略收益%':>10} {'基准收益%':>10} {'超额Alpha%':>11} "
          f"{'策略回撤%':>10} {'基准回撤%':>10} {'回撤改善%':>10}")
    print(f"  {'-'*75}")

    for code in codes:
        result = engine.run(strategy, ts_code=code, verbose=False)
        benchmark_result = engine.run(BuyAndHoldStrategy(), ts_code=code, verbose=False)

        if "error" in result or "error" in benchmark_result:
            print(f"  {code:<12} 数据加载失败")
            continue

        m = result["metrics"]
        bm = benchmark_result["metrics"]

        ret_alpha = m.get("total_return_pct", 0) - bm.get("total_return_pct", 0)
        dd_improve = bm.get("max_drawdown_pct", 0) - m.get("max_drawdown_pct", 0)

        marker = "✅" if ret_alpha > 0 else "❌"
        print(f"  {code:<12} "
              f"{m['total_return_pct']:>+9.2f}% "
              f"{bm['total_return_pct']:>+9.2f}% "
              f"{ret_alpha:>+10.2f}% "
              f"{m['max_drawdown_pct']:>9.2f}% "
              f"{bm['max_drawdown_pct']:>9.2f}% "
              f"{dd_improve:>+9.2f}%  {marker}")

    print(f"  {'='*75}")


if __name__ == "__main__":
    main()

