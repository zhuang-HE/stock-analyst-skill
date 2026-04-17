"""
多视角报告格式化模块

将 AggregatedResult 格式化为 Markdown 报告的「综合评估」章节，
追加在现有报告内容之后，供阅读报告的人参考。

输出格式：纯 Markdown，可直接拼接到 unified_report_template 的报告末尾。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .aggregator import AggregatedResult

from .perspectives import OPINION_LABELS, Opinion


# ═══════════════════════════════════════════════════════════════
#  方向 → 图标/颜色映射
# ═══════════════════════════════════════════════════════════════

_OPINION_ICON = {
    Opinion.BULLISH: "🟢",
    Opinion.BEARISH: "🔴",
    Opinion.NEUTRAL: "⚪",
}

_RISK_LEVEL_ICON = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
}

_DIVERGENCE_ICON = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
}


def format_multi_perspective_report(
    result: "AggregatedResult",
    stock_name: str = "",
    stock_code: str = "",
) -> str:
    """
    将聚合结果格式化为 Markdown 格式的综合评估报告。

    Args:
        result: ViewAggregator 的聚合结果
        stock_name: 股票名称
        stock_code: 股票代码

    Returns:
        Markdown 格式的报告字符串，可直接追加到报告末尾
    """
    title = f"{stock_name} ({stock_code})" if stock_name else stock_code
    lines: list[str] = []

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## 🎯 多视角综合评估 — {title}")
    lines.append("")
    lines.append("> 以下分析由 5 个独立投资视角（价值派、成长派、技术派、逆向派、风控派）")
    lines.append("> 分别评估后投票汇总而成，供参考。各视角基于量化指标独立计算，非主观判断。")
    lines.append("")

    # ── 视角投票明细表 ──
    lines.append("### 📊 各视角投票结果")
    lines.append("")
    lines.append("| 视角 | 方向 | 置信度 | 核心理由 |")
    lines.append("|:-----|:----:|:------:|:---------|")

    for pr in result.perspective_results:
        icon = _OPINION_ICON[pr.opinion]
        label = OPINION_LABELS[pr.opinion]
        conf_pct = f"{pr.confidence * 100:.0f}%"
        # 取前 2 条理由，用分号连接
        top_reasons = "；".join(pr.reasons[:2]) if pr.reasons else "—"
        # 截断过长的理由
        if len(top_reasons) > 60:
            top_reasons = top_reasons[:57] + "..."

        lines.append(
            f"| {pr.perspective_icon} {pr.perspective_name} "
            f"| {icon} {label} "
            f"| {conf_pct} "
            f"| {top_reasons} |"
        )

    lines.append("")

    # ── 综合判断 ──
    lines.append("### 📋 综合判断")
    lines.append("")

    main_icon = _OPINION_ICON[result.opinion]
    lines.append(f"**方向：{main_icon} {result.opinion_label}**")
    lines.append(f"**置信度：{result.confidence * 100:.0f}%**")
    lines.append("")

    # 得分明细
    lines.append("**得分明细：**")
    lines.append("")
    lines.append(f"- 看多得分：{result.bullish_score:.3f}")
    lines.append(f"- 看空得分：{result.bearish_score:.3f}")
    lines.append(f"- 中性得分：{result.neutral_score:.3f}")
    lines.append("")

    # 得分可视化条
    bar_len = 30
    b_bar = "█" * int(result.bullish_score * bar_len * 3)
    n_bar = "█" * int(result.neutral_score * bar_len * 3)
    r_bar = "█" * int(result.bearish_score * bar_len * 3)
    lines.append(f"```\n"
                 f"🟢 看多 [{b_bar:<{bar_len}}] {result.bullish_score:.1%}\n"
                 f"⚪ 中性 [{n_bar:<{bar_len}}] {result.neutral_score:.1%}\n"
                 f"🔴 看空 [{r_bar:<{bar_len}}] {result.bearish_score:.1%}\n"
                 f"```")
    lines.append("")

    # ── 分歧检测 ──
    div_icon = _DIVERGENCE_ICON.get(result.divergence_level, "⚪")
    div_label = {"low": "低", "medium": "中", "high": "高"}.get(result.divergence_level, "未知")
    lines.append("### 🔍 视角分歧分析")
    lines.append("")
    lines.append(f"**分歧程度：{div_icon} {div_label}**")
    lines.append(f"> {result.divergence_description}")
    lines.append("")

    # ── 风控约束 ──
    ra = result.risk_assessment
    risk_icon = _RISK_LEVEL_ICON.get(ra.risk_level, "⚪")
    lines.append("### 🛡️ 风控约束")
    lines.append("")
    lines.append(f"**风险等级：{risk_icon} {ra.risk_level_label}**")
    lines.append(f"**建议最大仓位：{ra.max_position_pct:.0f}%**")
    lines.append("")

    if ra.constraints:
        lines.append("**风控参数：**")
        lines.append("")
        if "stop_loss_price" in ra.constraints:
            lines.append(f"- 建议止损位：¥{ra.constraints['stop_loss_price']:,.2f}（{ra.constraints.get('stop_loss_pct', 0):.0f}%）")
        if "max_drawdown_pct" in ra.constraints:
            lines.append(f"- 近期最大回撤：{ra.constraints['max_drawdown_pct']:.1f}%")
        if "drop_from_high_pct" in ra.constraints:
            lines.append(f"- 距近期高点：-{ra.constraints['drop_from_high_pct']:.1f}%")
        if "avg_daily_volatility_pct" in ra.constraints:
            lines.append(f"- 日均波动率：{ra.constraints['avg_daily_volatility_pct']:.1f}%")
        lines.append("")

    if ra.warnings:
        lines.append("**风险提示：**")
        lines.append("")
        for w in ra.warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    # ── 风控否决 ──
    if result.vetoed:
        lines.append("> **🚫 风控否决生效**：由于风险等级过高，综合判断已强制调整为「观望」。")
        lines.append(f"> {result.veto_reason}")
        lines.append("")

    # ── 各视角详细分析 ──
    lines.append("### 📖 各视角详细分析")
    lines.append("")

    for pr in result.perspective_results:
        icon = _OPINION_ICON[pr.opinion]
        label = OPINION_LABELS[pr.opinion]
        conf_pct = f"{pr.confidence * 100:.0f}%"

        lines.append(f"#### {pr.perspective_icon} {pr.perspective_name} — {icon} {label}（{conf_pct}）")
        lines.append("")
        for reason in pr.reasons:
            lines.append(f"- {reason}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本综合评估基于量化指标计算，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*")

    return "\n".join(lines)


def format_multi_perspective_brief(
    result: "AggregatedResult",
    stock_name: str = "",
    stock_code: str = "",
) -> str:
    """
    生成精简版的多视角摘要（3-5行），适合插入报告的快速概览区域。

    Args:
        result: 聚合结果
        stock_name: 股票名称
        stock_code: 股票代码

    Returns:
        精简的 Markdown 摘要
    """
    title = f"{stock_name} ({stock_code})" if stock_name else stock_code
    main_icon = _OPINION_ICON[result.opinion]
    risk_icon = _RISK_LEVEL_ICON.get(result.risk_assessment.risk_level, "⚪")

    opinion_counts = {}
    for pr in result.perspective_results:
        key = OPINION_LABELS[pr.opinion]
        opinion_counts[key] = opinion_counts.get(key, 0) + 1

    counts_str = "、".join(f"{v}个{k}" for k, v in opinion_counts.items())

    lines = [
        f"**多视角投票：** {main_icon} {result.opinion_label}（{result.confidence * 100:.0f}%）| "
        f"{counts_str} | {risk_icon} {result.risk_assessment.risk_level_label} | "
        f"建议仓位 ≤{result.risk_assessment.max_position_pct:.0f}%",
    ]

    if result.vetoed:
        lines.append(f"\\> 🚫 风控否决：{result.veto_reason}")

    return "\n".join(lines)
