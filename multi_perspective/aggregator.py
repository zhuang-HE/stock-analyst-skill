"""
多视角投票聚合器

将 5 个投资视角的分析结果进行加权投票、分歧检测和风控约束过滤，
输出最终的 AggregatedResult。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .perspectives import (
    Opinion,
    PerspectiveResult,
    RiskAssessment,
    OPINION_LABELS,
)


@dataclass
class AggregatedResult:
    """多视角聚合结果"""

    # 综合判断
    opinion: Opinion
    opinion_label: str
    confidence: float

    # 得分明细
    bullish_score: float
    bearish_score: float
    neutral_score: float

    # 风控约束
    risk_assessment: RiskAssessment

    # 分歧信息
    divergence_level: str           # low / medium / high
    divergence_description: str

    # 各视角原始结果
    perspective_results: List[PerspectiveResult] = field(default_factory=list)

    # 风控是否否决
    vetoed: bool = False
    veto_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "opinion": self.opinion.value,
            "opinion_label": self.opinion_label,
            "confidence": round(self.confidence, 3),
            "bullish_score": round(self.bullish_score, 4),
            "bearish_score": round(self.bearish_score, 4),
            "neutral_score": round(self.neutral_score, 4),
            "risk_assessment": self.risk_assessment.to_dict(),
            "divergence_level": self.divergence_level,
            "divergence_description": self.divergence_description,
            "vetoed": self.vetoed,
            "veto_reason": self.veto_reason,
            "perspectives": [p.to_dict() for p in self.perspective_results],
        }


class ViewAggregator:
    """多视角投票聚合器"""

    def aggregate(
        self,
        perspective_results: List[PerspectiveResult],
        risk_assessment: Optional[RiskAssessment] = None,
    ) -> AggregatedResult:
        """
        聚合所有视角的分析结果。

        Args:
            perspective_results: 各视角的分析结果列表
            risk_assessment: 风控视角的独立评估（可选）

        Returns:
            AggregatedResult 聚合后的结果
        """
        if not perspective_results:
            return AggregatedResult(
                opinion=Opinion.NEUTRAL, opinion_label="中性", confidence=0.0,
                bullish_score=0, bearish_score=0, neutral_score=0,
                risk_assessment=risk_assessment or RiskAssessment(
                    risk_level="medium", risk_level_label="中风险",
                    max_position_pct=20, warnings=["无视角数据"],
                ),
                divergence_level="low", divergence_description="无数据",
            )

        # ---- 1. 加权投票计算 ----
        bullish_score = 0.0
        bearish_score = 0.0
        neutral_score = 0.0

        for pr in perspective_results:
            w = pr.weight
            c = pr.confidence
            if pr.opinion == Opinion.BULLISH:
                bullish_score += w * c
            elif pr.opinion == Opinion.BEARISH:
                bearish_score += w * c
            else:
                neutral_score += w * c

        # 归一化到 0-1
        total = bullish_score + bearish_score + neutral_score
        if total > 0:
            bullish_score /= total
            bearish_score /= total
            neutral_score /= total

        # ---- 2. 确定综合方向 ----
        if bullish_score > bearish_score and bullish_score > neutral_score:
            opinion = Opinion.BULLISH
        elif bearish_score > bullish_score and bearish_score > neutral_score:
            opinion = Opinion.BEARISH
        else:
            opinion = Opinion.NEUTRAL

        # 置信度 = 得分优势 / 总分
        max_score = max(bullish_score, bearish_score, neutral_score)
        confidence = max_score if total > 0 else 0.0

        # ---- 3. 风控一票否决 ----
        vetoed = False
        veto_reason = ""

        if risk_assessment and risk_assessment.risk_level == "high":
            # 高风险时强制观望，降低置信度
            if opinion != Opinion.NEUTRAL:
                vetoed = True
                veto_reason = f"风控否决：{risk_assessment.risk_level_label}，强制建议观望"
                opinion = Opinion.NEUTRAL
            confidence *= 0.5

        opinion_label = OPINION_LABELS[opinion]

        # ---- 4. 分歧检测 ----
        opinions = [pr.opinion for pr in perspective_results]
        bullish_count = sum(1 for o in opinions if o == Opinion.BULLISH)
        bearish_count = sum(1 for o in opinions if o == Opinion.BEARISH)
        neutral_count = sum(1 for o in opinions if o == Opinion.NEUTRAL)

        # 分歧判定：多空双方都有 ≥2 个视角支持
        if bullish_count >= 2 and bearish_count >= 2:
            divergence_level = "high"
            divergence_description = (
                f"多空分歧严重：{bullish_count}个看多 vs {bearish_count}个看空，"
                f"建议等待方向明确"
            )
        elif bullish_count >= 1 and bearish_count >= 1:
            divergence_level = "medium"
            divergence_description = (
                f"多空存在分歧：{bullish_count}个看多 vs {bearish_count}个看空，"
                f"操作需谨慎"
            )
        else:
            divergence_level = "low"
            dominant = "看多" if bullish_count > bearish_count else (
                "看空" if bearish_count > bullish_count else "中性"
            )
            consistent_count = max(bullish_count, bearish_count, neutral_count)
            divergence_description = f"视角一致度较高：{consistent_count}/{len(opinions)} 倾向{dominant}"

        return AggregatedResult(
            opinion=opinion,
            opinion_label=opinion_label,
            confidence=round(confidence, 3),
            bullish_score=round(bullish_score, 4),
            bearish_score=round(bearish_score, 4),
            neutral_score=round(neutral_score, 4),
            risk_assessment=risk_assessment or RiskAssessment(
                risk_level="low", risk_level_label="低风险",
                max_position_pct=30, warnings=["未进行风控评估"],
            ),
            divergence_level=divergence_level,
            divergence_description=divergence_description,
            perspective_results=perspective_results,
            vetoed=vetoed,
            veto_reason=veto_reason,
        )
