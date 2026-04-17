"""
多视角投资分析模块 (multi_perspective)

借鉴 ai-hedge-fund 的多 Agent 投票机制，采用「本地量化为主、LLM 为辅」策略，
为股票分析报告增加多视角综合评估能力。

包含 5 个投资视角：
  - 💼 价值派 (ValuePerspective): PE/PB/ROE/股息率
  - 🚀 成长派 (GrowthPerspective): 营收/利润增速
  - 📈 技术派 (TechPerspective): 均线/MACD/RSI（复用信号体系）
  - 🔄 逆向派 (ContrarianPerspective): 情绪指数/资金面
  - 🛡️ 风控派 (RiskPerspective): 回撤/波动率/仓位约束

使用方式:
    from multi_perspective import MultiPerspectiveAnalyzer

    analyzer = MultiPerspectiveAnalyzer()
    result = analyzer.analyze(
        stock_code="600519",
        stock_name="贵州茅台",
        quote=quote_data,            # 行情数据 dict
        kline_df=kline_dataframe,    # K线数据 DataFrame
        fundamental=fund_data,       # 基本面数据 dict
        money_flow=flow_data,        # 资金流向 dict
        signal_resonance=resonance,  # 信号共振结果 dict
        sentiment_index=si_data,     # 情绪指数 dict
        technical_indicators=ti_data,# 技术指标 dict
    )

    # 获取完整报告（Markdown）
    report = analyzer.format_report(result)

    # 获取精简摘要（一行）
    brief = analyzer.format_brief(result)

    # 获取结构化数据
    data = result.to_dict()
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from .aggregator import AggregatedResult, ViewAggregator
from .perspectives import (
    ContrarianPerspective,
    GrowthPerspective,
    PerspectiveResult,
    RiskAssessment,
    RiskPerspective,
    TechPerspective,
    ValuePerspective,
)
from .report_formatter import format_multi_perspective_brief, format_multi_perspective_report


class MultiPerspectiveAnalyzer:
    """
    多视角投资分析器 — 顶层入口

    将 5 个视角的分析结果聚合，输出综合评估。
    所有计算在本地完成，零 Token 成本。
    """

    def __init__(self):
        self._value = ValuePerspective()
        self._growth = GrowthPerspective()
        self._tech = TechPerspective()
        self._contrarian = ContrarianPerspective()
        self._risk = RiskPerspective()
        self._aggregator = ViewAggregator()

    def analyze(
        self,
        *,
        stock_code: str = "",
        stock_name: str = "",
        quote: Optional[Dict[str, Any]] = None,
        kline_df: Optional[pd.DataFrame] = None,
        fundamental: Optional[Dict[str, Any]] = None,
        money_flow: Optional[Dict[str, Any]] = None,
        signal_resonance: Optional[Dict[str, Any]] = None,
        sentiment_index: Optional[Dict[str, Any]] = None,
        technical_indicators: Optional[Dict[str, Any]] = None,
    ) -> AggregatedResult:
        """
        执行多视角分析。

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            quote: 行情快照数据（pe, pb, dividend_yield, current 等）
            kline_df: K线 DataFrame（需含 close, high, low, vol/pct_chg 列）
            fundamental: 基本面数据（roe, revenue_growth, net_profit_growth 等）
            money_flow: 资金流向数据（north_flow, margin_balance_change 等）
            signal_resonance: 信号共振结果（来自 SignalResonanceScorer）
            sentiment_index: 情绪指数数据（来自 SentimentIndexCalculator）
            technical_indicators: 技术指标数据（rsi, macd, ma5/10/20/60 等）

        Returns:
            AggregatedResult 包含综合判断、各视角结果和风控约束
        """
        # 通用参数
        common = {
            "quote": quote or {},
            "kline_df": kline_df,
            "fundamental": fundamental or {},
            "money_flow": money_flow or {},
            "signal_resonance": signal_resonance or {},
            "sentiment_index": sentiment_index or {},
            "technical_indicators": technical_indicators or {},
        }

        # 各视角独立分析
        value_result = self._value.analyze(**common)
        growth_result = self._growth.analyze(**common)
        tech_result = self._tech.analyze(**common)
        contrarian_result = self._contrarian.analyze(**common)
        risk_result, risk_assessment = self._risk.analyze(**common)

        # 收集所有视角结果
        all_results = [
            value_result,
            growth_result,
            tech_result,
            contrarian_result,
            risk_result,
        ]

        # 聚合
        aggregated = self._aggregator.aggregate(all_results, risk_assessment)

        return aggregated

    def format_report(
        self,
        result: AggregatedResult,
        stock_name: str = "",
        stock_code: str = "",
    ) -> str:
        """
        生成完整的 Markdown 综合评估报告。

        此报告设计为追加在现有分析报告的最后，
        供阅读报告的人参考不同投资视角的分析意见。
        """
        return format_multi_perspective_report(result, stock_name, stock_code)

    def format_brief(
        self,
        result: AggregatedResult,
        stock_name: str = "",
        stock_code: str = "",
    ) -> str:
        """生成精简的一行摘要，适合插入报告概览区域。"""
        return format_multi_perspective_brief(result, stock_name, stock_code)


__all__ = [
    "MultiPerspectiveAnalyzer",
    "ViewAggregator",
    "AggregatedResult",
    "PerspectiveResult",
    "RiskAssessment",
    "ValuePerspective",
    "GrowthPerspective",
    "TechPerspective",
    "ContrarianPerspective",
    "RiskPerspective",
    "Opinion",
    "format_multi_perspective_report",
    "format_multi_perspective_brief",
]
