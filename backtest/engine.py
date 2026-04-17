# -*- coding: utf-8 -*-
"""
回测引擎

核心职责：
1. 从 data_store 加载历史K线 + 技术指标
2. 逐日遍历，调用策略的 on_bar
3. 收集交易记录与净值曲线
4. 计算绩效指标

用法：
    from backtest import BacktestEngine, MAStrategy

    engine = BacktestEngine(ts_code='600519.SH', start_date='20250101')
    result = engine.run(MAStrategy())
    print(result['metrics'])

    # 比较多只股票
    results = engine.run_batch(['600519.SH', '000001.SZ'], MACDStrategy())
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

try:
    from .portfolio import Portfolio
    from .strategy import Strategy
    from .metrics import calc_metrics, format_metrics
except ImportError:
    from portfolio import Portfolio
    from strategy import Strategy
    from metrics import calc_metrics, format_metrics


class BacktestEngine:
    """
    回测引擎

    支持单股回测与批量回测，数据来自本地 data_store。
    """

    def __init__(
        self,
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_cash: float = 1000000.0,
        data_dir: Optional[str] = None,
    ):
        """
        Args:
            ts_code: 股票代码（如 600519.SH），run() 时也可传入
            start_date: 回测起始日期 YYYYMMDD
            end_date: 回测结束日期 YYYYMMDD
            initial_cash: 初始资金
            data_dir: 数据目录
        """
        self.ts_code = ts_code
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.data_dir = data_dir

    def _load_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        """
        从 data_store 加载K线和技术指标数据，合并为一个 DataFrame。

        Returns:
            合并后的 DataFrame（K线 + 技术指标），无数据返回 None
        """
        try:
            from data_store.queries import StockQueries
        except ImportError:
            print("  ⚠ 无法导入 data_store，请确保在项目根目录运行")
            return None

        q = StockQueries(data_dir=self.data_dir)
        try:
            # 加载日K线
            daily_df = q.get_daily(
                ts_code,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            if daily_df is None or daily_df.empty:
                print(f"  ⚠ {ts_code} 无日K线数据")
                return None

            # 加载技术指标
            tech_df = q.get_tech_indicators(
                ts_code,
                start_date=self.start_date,
            )
            if tech_df is not None and not tech_df.empty:
                # 合并K线和技术指标
                daily_df["trade_date"] = daily_df["trade_date"].astype(str)
                tech_df["trade_date"] = tech_df["trade_date"].astype(str)

                merged = daily_df.merge(
                    tech_df,
                    on=["ts_code", "trade_date"],
                    how="left",
                    suffixes=("", "_tech"),
                )
                return merged
            else:
                print(f"  ⚠ {ts_code} 无技术指标数据，请先运行 python -m data_store tech-calc --codes {ts_code}")
                return daily_df

        finally:
            q.close()

    def run(
        self,
        strategy: Strategy,
        ts_code: Optional[str] = None,
        verbose: bool = True,
    ) -> Dict:
        """
        运行单只股票的回测。

        Args:
            strategy: 策略实例
            ts_code: 股票代码（覆盖实例属性）
            verbose: 是否打印进度

        Returns:
            {
                "strategy": str,
                "ts_code": str,
                "metrics": dict,
                "portfolio": Portfolio,
                "report": str,  # 格式化绩效报告
            }
        """
        code = ts_code or self.ts_code
        if not code:
            raise ValueError("请指定 ts_code")

        if verbose:
            print(f"\n{'='*50}")
            print(f"  回测: {code} | 策略: {strategy.name}")
            print(f"{'='*50}")

        # 加载数据（已合并K线 + 技术指标）
        merged_df = self._load_data(code)
        if merged_df is None:
            return {"error": f"无数据: {code}"}

        # 初始化
        portfolio = Portfolio(initial_cash=self.initial_cash)
        if verbose and self.initial_cash < 500000:
            print(f"  ⚠ 初始资金 {self.initial_cash:,.0f} 较低，高价股可能买不起（如茅台一手约15万）")
        strategy.on_start(portfolio)

        # 按日期遍历
        start_time = time.time()
        trade_count = 0

        indicator_keys = [
            "ma5", "ma10", "ma20", "ma60", "ma120", "ma250",
            "macd_dif", "macd_dea", "macd_hist",
            "rsi_6", "rsi_14", "rsi_24",
            "kdj_k", "kdj_d", "kdj_j",
            "boll_upper", "boll_mid", "boll_lower",
            "atr_14", "obv",
        ]

        for _, row in merged_df.iterrows():
            trade_date = str(row.get("trade_date", ""))

            # 构建K线数据
            bar = {
                "trade_date": trade_date,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "vol": float(row.get("vol", 0)),
                "amount": float(row.get("amount", 0)),
                "pct_chg": float(row.get("pct_chg", 0)),
            }

            # 从合并后的 DataFrame 直接提取技术指标
            indicators = {}
            for key in indicator_keys:
                val = row.get(key)
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    try:
                        indicators[key] = float(val)
                    except (ValueError, TypeError):
                        pass

            # 调用策略
            prev_trades = len(portfolio.trades)
            strategy.on_bar(bar, portfolio, indicators)

            # 更新市值
            portfolio.update_market_value(bar["close"], trade_date)

            # 统计交易
            if len(portfolio.trades) > prev_trades:
                trade_count += 1

        strategy.on_end(portfolio)
        elapsed = time.time() - start_time

        # 计算绩效
        metrics = calc_metrics(
            portfolio.equity_curve,
            portfolio.trades,
            initial_cash=self.initial_cash,
        )

        report = format_metrics(metrics)

        if verbose:
            print(report)
            print(f"  回测耗时: {elapsed:.2f}s, 触发交易 {trade_count} 次")

        return {
            "strategy": strategy.name,
            "ts_code": code,
            "metrics": metrics,
            "portfolio": portfolio,
            "report": report,
        }

    def run_batch(
        self,
        ts_codes: List[str],
        strategy: Strategy,
        verbose: bool = True,
    ) -> List[Dict]:
        """
        批量回测多只股票。

        Returns:
            结果列表
        """
        results = []
        for i, code in enumerate(ts_codes):
            if verbose:
                print(f"\n[{i+1}/{len(ts_codes)}] ", end="")

            result = self.run(strategy, ts_code=code, verbose=verbose)
            results.append(result)

        # 汇总
        if verbose:
            print(f"\n{'='*60}")
            print(f"  批量回测汇总 ({len(ts_codes)} 只股票)")
            print(f"{'='*60}")
            for r in results:
                if "error" in r:
                    print(f"  {r.get('ts_code', '?')}: {r['error']}")
                else:
                    m = r["metrics"]
                    print(f"  {r['ts_code']}: 收益 {m['total_return_pct']:+.2f}% / "
                          f"夏普 {m['sharpe_ratio']:.2f} / "
                          f"回撤 {m['max_drawdown_pct']:.2f}% / "
                          f"胜率 {m['win_rate']:.1f}%")

        return results

    def compare_strategies(
        self,
        strategies: List[Strategy],
        ts_code: Optional[str] = None,
        verbose: bool = True,
    ) -> List[Dict]:
        """
        对同一只股票比较多个策略。

        Returns:
            各策略回测结果列表
        """
        code = ts_code or self.ts_code
        if not code:
            raise ValueError("请指定 ts_code")

        results = []
        for strategy in strategies:
            result = self.run(strategy, ts_code=code, verbose=verbose)
            results.append(result)

        if verbose:
            print(f"\n{'='*60}")
            print(f"  策略比较: {code}")
            print(f"{'='*60}")
            print(f"  {'策略':<20} {'收益%':>8} {'年化%':>8} {'夏普':>6} {'回撤%':>8} {'胜率%':>6}")
            print(f"  {'-'*60}")
            for r in results:
                if "error" in r:
                    continue
                m = r["metrics"]
                print(f"  {r['strategy']:<20} {m['total_return_pct']:>+8.2f} "
                      f"{m['annualized_return_pct']:>+8.2f} "
                      f"{m['sharpe_ratio']:>6.2f} "
                      f"{m['max_drawdown_pct']:>8.2f} "
                      f"{m['win_rate']:>6.1f}")

        return results
