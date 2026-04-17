"""
多视角投资分析 - 5个投资视角分析器

借鉴 ai-hedge-fund 的多 Agent 投票机制，但采用「本地量化计算为主、LLM 为辅」的策略，
所有视角分析基于纯 Python 计算，零 Token 成本。

视角列表：
  1. 价值派 (ValuePerspective)    - PE/PB/ROE/股息率/安全边际
  2. 成长派 (GrowthPerspective)   - 营收增速/利润增速/毛利率趋势
  3. 技术派 (TechPerspective)     - 均线/MACD/RSI/量价（复用信号体系）
  4. 逆向派 (ContrarianPerspective) - 情绪指数/市场一致性
  5. 风控派 (RiskPerspective)     - 回撤/波动率/盈亏比（约束层）
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd


# ═══════════════════════════════════════════════════════════════
#  公共数据结构
# ═══════════════════════════════════════════════════════════════

class Opinion(str, Enum):
    """投资观点方向"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


OPINION_LABELS = {
    Opinion.BULLISH: "看多",
    Opinion.BEARISH: "看空",
    Opinion.NEUTRAL: "中性",
}


@dataclass
class PerspectiveResult:
    """单个视角的分析结果"""
    perspective_name: str          # 视角名称
    perspective_icon: str          # 图标 emoji
    opinion: Opinion               # 看多/看空/中性
    confidence: float              # 置信度 0.0-1.0
    weight: float                  # 在聚合中的权重
    reasons: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "perspective_name": self.perspective_name,
            "perspective_icon": self.perspective_icon,
            "opinion": self.opinion.value,
            "opinion_label": OPINION_LABELS[self.opinion],
            "confidence": round(self.confidence, 3),
            "weight": self.weight,
            "reasons": self.reasons,
            "details": self.details,
        }


@dataclass
class RiskAssessment:
    """风控视角的独立输出"""
    risk_level: str                # low / medium / high
    risk_level_label: str          # 低风险 / 中风险 / 高风险
    max_position_pct: float        # 建议最大仓位 %
    warnings: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "risk_level_label": self.risk_level_label,
            "max_position_pct": self.max_position_pct,
            "warnings": self.warnings,
            "constraints": self.constraints,
        }


# ═══════════════════════════════════════════════════════════════
#  抽象基类
# ═══════════════════════════════════════════════════════════════

class BasePerspective(ABC):
    """投资视角基类"""

    def __init__(self, name: str, icon: str, weight: float):
        self.name = name
        self.icon = icon
        self.weight = weight

    @abstractmethod
    def analyze(self, **kwargs) -> PerspectiveResult:
        """执行分析，返回结构化结果"""
        ...

    # ---------- 工具方法 ----------

    @staticmethod
    def _safe_float(val: Any, default: float = 0.0) -> float:
        """安全转换为 float"""
        try:
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return default
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _classify_score(score: float, bullish_th: float, bearish_th: float) -> Opinion:
        """
        将 0-100 的得分转换为 Opinion。
        score > bullish_th → bullish, score < bearish_th → bearish, else neutral
        """
        if score >= bullish_th:
            return Opinion.BULLISH
        elif score <= bearish_th:
            return Opinion.BEARISH
        return Opinion.NEUTRAL

    @staticmethod
    def _confidence_from_score(score: float) -> float:
        """
        从 0-100 的偏离中心程度计算置信度。
        50 → 0.3, 0 或 100 → 0.95
        """
        deviation = abs(score - 50) / 50.0  # 0-1
        return round(min(0.95, 0.3 + deviation * 0.65), 3)


# ═══════════════════════════════════════════════════════════════
#  视角1：价值派
# ═══════════════════════════════════════════════════════════════

class ValuePerspective(BasePerspective):
    """
    价值派视角 — 寻找价格低于内在价值的标的，注重安全边际。

    核心指标：PE、PB、ROE、股息率、营业利润率
    """

    def __init__(self):
        super().__init__(
            name="价值派",
            icon="💼",
            weight=0.25,
        )

    def analyze(self, *, quote: dict = None, fundamental: dict = None, **kwargs) -> PerspectiveResult:
        reasons: List[str] = []
        scores: List[float] = []

        q = quote or {}
        f = fundamental or {}

        # ---- PE 估值 ----
        pe = self._safe_float(q.get("pe") or q.get("pe_ttm"))
        if pe > 0:
            if pe < 15:
                scores.append(85)
                reasons.append(f"PE {pe:.1f}x 处于低估区间（<15）")
            elif pe <= 30:
                scores.append(55)
                reasons.append(f"PE {pe:.1f}x 估值合理（15-30）")
            elif pe <= 50:
                scores.append(35)
                reasons.append(f"PE {pe:.1f}x 偏高（30-50）")
            else:
                scores.append(15)
                reasons.append(f"PE {pe:.1f}x 明显高估（>50）")

        # ---- PB 估值 ----
        pb = self._safe_float(q.get("pb"))
        if pb > 0:
            if pb < 1.5:
                scores.append(80)
                reasons.append(f"PB {pb:.2f} 破净或低PB")
            elif pb <= 3.0:
                scores.append(55)
                reasons.append(f"PB {pb:.2f} 估值合理")
            elif pb <= 5.0:
                scores.append(35)
                reasons.append(f"PB {pb:.2f} 偏高")
            else:
                scores.append(15)
                reasons.append(f"PB {pb:.2f} 明显高估")

        # ---- ROE ----
        roe = self._safe_float(f.get("roe") or f.get("weighted_roe"))
        if roe > 0:
            if roe > 15:
                scores.append(80)
                reasons.append(f"ROE {roe:.1f}% 盈利能力优秀")
            elif roe >= 8:
                scores.append(55)
                reasons.append(f"ROE {roe:.1f}% 盈利能力尚可")
            else:
                scores.append(25)
                reasons.append(f"ROE {roe:.1f}% 盈利能力偏弱")

        # ---- 股息率 ----
        dividend_yield = self._safe_float(q.get("dividend_yield"))
        if dividend_yield > 0:
            if dividend_yield > 4:
                scores.append(80)
                reasons.append(f"股息率 {dividend_yield:.2f}% 高股息")
            elif dividend_yield >= 2:
                scores.append(60)
                reasons.append(f"股息率 {dividend_yield:.2f}% 股息尚可")
            else:
                scores.append(35)
                reasons.append(f"股息率 {dividend_yield:.2f}% 股息偏低")

        # ---- 营业利润率 ----
        op_margin = self._safe_float(f.get("operate_margin") or f.get("gross_profit_margin"))
        if op_margin > 0:
            if op_margin > 20:
                scores.append(75)
                reasons.append(f"营业利润率 {op_margin:.1f}% 利润丰厚")
            elif op_margin >= 10:
                scores.append(55)
                reasons.append(f"营业利润率 {op_margin:.1f}% 利润尚可")

        # ---- 聚合 ----
        if not scores:
            return PerspectiveResult(
                perspective_name=self.name, perspective_icon=self.icon,
                opinion=Opinion.NEUTRAL, confidence=0.2, weight=self.weight,
                reasons=["价值数据不足，无法判断"], details={"available_metrics": 0},
            )

        avg_score = sum(scores) / len(scores)
        opinion = self._classify_score(avg_score, bullish_th=65, bearish_th=35)
        confidence = self._confidence_from_score(avg_score)

        return PerspectiveResult(
            perspective_name=self.name, perspective_icon=self.icon,
            opinion=opinion, confidence=confidence, weight=self.weight,
            reasons=reasons, details={"avg_score": round(avg_score, 1), "metrics_count": len(scores)},
        )


# ═══════════════════════════════════════════════════════════════
#  视角2：成长派
# ═══════════════════════════════════════════════════════════════

class GrowthPerspective(BasePerspective):
    """
    成长派视角 — 关注未来增长潜力，愿意为成长支付溢价。

    核心指标：营收增速、净利润增速、毛利率趋势
    """

    def __init__(self):
        super().__init__(
            name="成长派",
            icon="🚀",
            weight=0.25,
        )

    def analyze(self, *, fundamental: dict = None, **kwargs) -> PerspectiveResult:
        reasons: List[str] = []
        scores: List[float] = []

        f = fundamental or {}

        # ---- 营收增长率 ----
        rev_growth = self._safe_float(
            f.get("revenue_growth") or f.get("revenue_yoy") or f.get("or_yoy")
        )
        if rev_growth != 0:
            if rev_growth > 20:
                scores.append(85)
                reasons.append(f"营收同比增长 {rev_growth:.1f}%，高增长")
            elif rev_growth > 10:
                scores.append(65)
                reasons.append(f"营收同比增长 {rev_growth:.1f}%，稳健增长")
            elif rev_growth > 0:
                scores.append(50)
                reasons.append(f"营收同比增长 {rev_growth:.1f}%，增速放缓")
            else:
                scores.append(20)
                reasons.append(f"营收同比下降 {abs(rev_growth):.1f}%，负增长")

        # ---- 净利润增长率 ----
        profit_growth = self._safe_float(
            f.get("net_profit_growth") or f.get("netprofit_yoy") or f.get("np_yoy")
        )
        if profit_growth != 0:
            if profit_growth > 25:
                scores.append(85)
                reasons.append(f"净利润同比增长 {profit_growth:.1f}%，业绩爆发")
            elif profit_growth > 10:
                scores.append(65)
                reasons.append(f"净利润同比增长 {profit_growth:.1f}%，稳步提升")
            elif profit_growth > 0:
                scores.append(50)
                reasons.append(f"净利润同比增长 {profit_growth:.1f}%，增速一般")
            else:
                scores.append(15)
                reasons.append(f"净利润同比下降 {abs(profit_growth):.1f}%，业绩下滑")

        # ---- 毛利率趋势 ----
        gross_margin = self._safe_float(f.get("gross_profit_margin") or f.get("gross_margin"))
        prev_gross_margin = self._safe_float(f.get("prev_gross_margin"))
        if gross_margin > 0 and prev_gross_margin > 0:
            margin_change = gross_margin - prev_gross_margin
            if margin_change > 2:
                scores.append(80)
                reasons.append(f"毛利率 {gross_margin:.1f}% 较上期提升 {margin_change:.1f}pp")
            elif margin_change > 0:
                scores.append(60)
                reasons.append(f"毛利率 {gross_margin:.1f}% 较上期微升")
            elif margin_change > -2:
                scores.append(40)
                reasons.append(f"毛利率 {gross_margin:.1f}% 较上期微降 {abs(margin_change):.1f}pp")
            else:
                scores.append(20)
                reasons.append(f"毛利率 {gross_margin:.1f}% 较上期下降 {abs(margin_change):.1f}pp")

        # ---- 聚合 ----
        if not scores:
            return PerspectiveResult(
                perspective_name=self.name, perspective_icon=self.icon,
                opinion=Opinion.NEUTRAL, confidence=0.2, weight=self.weight,
                reasons=["成长数据不足，无法判断"], details={"available_metrics": 0},
            )

        avg_score = sum(scores) / len(scores)
        opinion = self._classify_score(avg_score, bullish_th=65, bearish_th=35)
        confidence = self._confidence_from_score(avg_score)

        return PerspectiveResult(
            perspective_name=self.name, perspective_icon=self.icon,
            opinion=opinion, confidence=confidence, weight=self.weight,
            reasons=reasons, details={"avg_score": round(avg_score, 1), "metrics_count": len(scores)},
        )


# ═══════════════════════════════════════════════════════════════
#  视角3：技术派
# ═══════════════════════════════════════════════════════════════

class TechPerspective(BasePerspective):
    """
    技术派视角 — 价格包含一切信息，趋势是朋友。

    核心指标：均线系统、MACD、RSI、KDJ、量价配合
    复用 signals/scoring.py 的信号体系
    """

    def __init__(self):
        super().__init__(
            name="技术派",
            icon="📈",
            weight=0.25,
        )

    def analyze(
        self,
        *,
        kline_df: pd.DataFrame = None,
        signal_resonance: dict = None,
        technical_indicators: dict = None,
        **kwargs,
    ) -> PerspectiveResult:
        reasons: List[str] = []
        scores: List[float] = []

        # ---- 优先从信号共振结果提取（复用 scoring.py） ----
        if signal_resonance:
            res_level = signal_resonance.get("resonance_level", "")
            total_score = self._safe_float(signal_resonance.get("total_score"))

            if "强共振" in res_level:
                if total_score > 0:
                    scores.append(85)
                    reasons.append(f"信号强共振看涨（综合得分 {total_score}）")
                else:
                    scores.append(15)
                    reasons.append(f"信号强共振看跌（综合得分 {total_score}）")
            elif "中等共振" in res_level:
                if total_score > 0:
                    scores.append(65)
                    reasons.append(f"信号中等共振看涨（综合得分 {total_score}）")
                else:
                    scores.append(35)
                    reasons.append(f"信号中等共振看跌（综合得分 {total_score}）")
            elif "弱共振" in res_level:
                if total_score > 0:
                    scores.append(55)
                    reasons.append(f"信号弱共振偏多（综合得分 {total_score}）")
                else:
                    scores.append(45)
                    reasons.append(f"信号弱共振偏空（综合得分 {total_score}）")
            else:
                scores.append(50)
                reasons.append("信号无共振，方向不明")

        # ---- 从技术指标直接计算（备用） ----
        ti = technical_indicators or {}

        # MACD
        macd_hist = self._safe_float(ti.get("macd_hist") or ti.get("macd_histogram"))
        macd_signal_val = self._safe_float(ti.get("macd_signal"))
        macd_dif = self._safe_float(ti.get("macd_dif") or ti.get("macd"))
        if macd_dif != 0 or macd_signal_val != 0:
            if macd_dif > macd_signal_val and macd_hist > 0:
                scores.append(70)
                reasons.append("MACD 金叉/多头运行")
            elif macd_dif < macd_signal_val and macd_hist < 0:
                scores.append(30)
                reasons.append("MACD 死叉/空头运行")

        # RSI
        rsi = self._safe_float(ti.get("rsi") or ti.get("rsi_14"))
        if rsi > 0:
            if rsi < 30:
                scores.append(80)
                reasons.append(f"RSI {rsi:.1f} 超卖区域，反弹预期")
            elif rsi < 45:
                scores.append(60)
                reasons.append(f"RSI {rsi:.1f} 偏弱但未超卖")
            elif rsi > 70:
                scores.append(25)
                reasons.append(f"RSI {rsi:.1f} 超买区域，回调风险")
            elif rsi > 55:
                scores.append(60)
                reasons.append(f"RSI {rsi:.1f} 偏强运行")
            else:
                scores.append(50)
                reasons.append(f"RSI {rsi:.1f} 中性区域")

        # 均线多头/空头排列
        ma5 = self._safe_float(ti.get("ma5"))
        ma10 = self._safe_float(ti.get("ma10"))
        ma20 = self._safe_float(ti.get("ma20"))
        ma60 = self._safe_float(ti.get("ma60"))
        if ma5 > 0 and ma20 > 0 and ma60 > 0:
            if ma5 > ma10 > ma20 > ma60:
                scores.append(75)
                reasons.append("均线多头排列（MA5>MA10>MA20>MA60）")
            elif ma5 < ma10 < ma20 < ma60:
                scores.append(25)
                reasons.append("均线空头排列（MA5<MA10<MA20<MA60）")
            else:
                scores.append(45)
                reasons.append("均线交织，趋势不明")

        # KDJ
        kdj_j = self._safe_float(ti.get("kdj_j") or ti.get("j"))
        if kdj_j != 0:
            if kdj_j < 0:
                scores.append(70)
                reasons.append(f"KDJ J值 {kdj_j:.1f} 超卖区间")
            elif kdj_j > 100:
                scores.append(30)
                reasons.append(f"KDJ J值 {kdj_j:.1f} 超买区间")

        # ---- 聚合 ----
        if not scores:
            return PerspectiveResult(
                perspective_name=self.name, perspective_icon=self.icon,
                opinion=Opinion.NEUTRAL, confidence=0.2, weight=self.weight,
                reasons=["技术指标数据不足"], details={"available_metrics": 0},
            )

        avg_score = sum(scores) / len(scores)
        opinion = self._classify_score(avg_score, bullish_th=60, bearish_th=40)
        confidence = self._confidence_from_score(avg_score)

        return PerspectiveResult(
            perspective_name=self.name, perspective_icon=self.icon,
            opinion=opinion, confidence=confidence, weight=self.weight,
            reasons=reasons, details={"avg_score": round(avg_score, 1), "metrics_count": len(scores)},
        )


# ═══════════════════════════════════════════════════════════════
#  视角4：逆向派
# ═══════════════════════════════════════════════════════════════

class ContrarianPerspective(BasePerspective):
    """
    逆向派视角 — 当市场一致看多时要警惕，极度恐慌时寻找机会。

    核心指标：情绪指数、市场一致性
    复用 ai_models/sentiment_index.py 的 SentimentResult
    """

    def __init__(self):
        super().__init__(
            name="逆向派",
            icon="🔄",
            weight=0.15,
        )

    def analyze(
        self,
        *,
        sentiment_index: dict = None,
        money_flow: dict = None,
        quote: dict = None,
        **kwargs,
    ) -> PerspectiveResult:
        reasons: List[str] = []
        scores: List[float] = []

        si = sentiment_index or {}
        mf = money_flow or {}

        # ---- 情绪指数（复用 sentiment_index.py） ----
        index_value = self._safe_float(si.get("index_value"))
        level = si.get("level", "")
        signal = si.get("signal", "")
        trend = si.get("trend", "")

        if index_value > 0:
            if index_value < 20:
                # 极度恐慌 → 逆向看多
                scores.append(80)
                reasons.append(f"情绪指数 {index_value:.0f}（{level}），极度恐慌中孕育机会")
            elif index_value < 35:
                scores.append(65)
                reasons.append(f"情绪指数 {index_value:.0f}（{level}），恐慌区间逆向偏多")
            elif index_value > 80:
                # 极度贪婪 → 逆向看空
                scores.append(20)
                reasons.append(f"情绪指数 {index_value:.0f}（{level}），极度贪婪需警惕")
            elif index_value > 65:
                scores.append(35)
                reasons.append(f"情绪指数 {index_value:.0f}（{level}），偏贪婪注意风险")
            else:
                scores.append(50)
                reasons.append(f"情绪指数 {index_value:.0f}（{level}），情绪中性")

            # 情绪趋势
            if "上升" in trend:
                scores.append(40)
                reasons.append("情绪持续升温，追高风险增加")
            elif "下降" in trend:
                scores.append(60)
                reasons.append("情绪降温，可能接近阶段性底部")

        # ---- 北向资金 ----
        north_flow = self._safe_float(mf.get("north_flow") or mf.get("hsgt_net"))
        if north_flow != 0:
            if north_flow < -50:
                scores.append(65)
                reasons.append(f"北向资金大幅流出 {abs(north_flow):.1f}亿，过度恐慌可能是机会")
            elif north_flow > 80:
                scores.append(40)
                reasons.append(f"北向资金大幅流入 {north_flow:.1f}亿，一致性过高需警惕")

        # ---- 融资余额 ----
        margin_balance_change = self._safe_float(mf.get("margin_balance_change"))
        if margin_balance_change != 0:
            if margin_balance_change < -5:
                scores.append(60)
                reasons.append("融资余额骤降，杠杆出清可能接近尾声")
            elif margin_balance_change > 5:
                scores.append(40)
                reasons.append("融资余额激增，杠杆拥挤风险")

        # ---- 聚合 ----
        if not scores:
            return PerspectiveResult(
                perspective_name=self.name, perspective_icon=self.icon,
                opinion=Opinion.NEUTRAL, confidence=0.2, weight=self.weight,
                reasons=["情绪/资金数据不足"], details={"available_metrics": 0},
            )

        avg_score = sum(scores) / len(scores)
        opinion = self._classify_score(avg_score, bullish_th=60, bearish_th=40)
        confidence = self._confidence_from_score(avg_score)

        return PerspectiveResult(
            perspective_name=self.name, perspective_icon=self.icon,
            opinion=opinion, confidence=confidence, weight=self.weight,
            reasons=reasons, details={"avg_score": round(avg_score, 1), "metrics_count": len(scores)},
        )


# ═══════════════════════════════════════════════════════════════
#  视角5：风控派
# ═══════════════════════════════════════════════════════════════

class RiskPerspective(BasePerspective):
    """
    风控派视角 — 不亏钱比赚钱重要，控制回撤是第一要务。

    特殊行为：不输出 opinion，只输出风险等级和约束条件。
    拥有一票否决权：高风险时强制建议观望。
    """

    def __init__(self):
        super().__init__(
            name="风控派",
            icon="🛡️",
            weight=0.10,
        )

    def analyze(
        self,
        *,
        kline_df: pd.DataFrame = None,
        quote: dict = None,
        technical_indicators: dict = None,
        **kwargs,
    ) -> tuple:
        """
        返回元组: (PerspectiveResult, RiskAssessment)
        风控派同时返回两个结果，用于聚合器处理。
        """
        warnings: List[str] = []
        constraints: Dict[str, Any] = {}
        risk_score = 0  # 0=低风险, 100=极高风险
        max_position = 30.0  # 默认最大仓位

        q = quote or {}
        ti = technical_indicators or {}

        # ---- 最大回撤（从K线数据计算） ----
        if kline_df is not None and len(kline_df) > 0:
            if "close" in kline_df.columns:
                close = pd.to_numeric(kline_df["close"], errors="coerce").dropna()
                if len(close) > 1:
                    cummax = close.cummax()
                    drawdown = (close - cummax) / cummax * 100
                    max_dd = abs(drawdown.min())
                    constraints["max_drawdown_pct"] = round(max_dd, 2)

                    if max_dd > 25:
                        risk_score += 40
                        warnings.append(f"近{len(close)}日最大回撤 {max_dd:.1f}%，高风险")
                        max_position = 10
                    elif max_dd > 15:
                        risk_score += 25
                        warnings.append(f"近{len(close)}日最大回撤 {max_dd:.1f}%，中风险")
                        max_position = 15
                    elif max_dd > 8:
                        risk_score += 10
                        warnings.append(f"近{len(close)}日最大回撤 {max_dd:.1f}%")
                        max_position = 25

                    # 当前价相对近期高点的位置
                    current_price = close.iloc[-1]
                    recent_high = close.max()
                    drop_from_high = (recent_high - current_price) / recent_high * 100
                    constraints["drop_from_high_pct"] = round(drop_from_high, 2)

                    if drop_from_high > 20:
                        warnings.append(f"当前价距近期高点已下跌 {drop_from_high:.1f}%")

            # ---- 波动率（ATR 近似） ----
            if all(c in kline_df.columns for c in ("high", "low", "close")):
                high = pd.to_numeric(kline_df["high"], errors="coerce")
                low = pd.to_numeric(kline_df["low"], errors="coerce")
                close_s = pd.to_numeric(kline_df["close"], errors="coerce")
                tr = high - low
                avg_tr = tr.tail(20).mean() if len(tr) >= 20 else tr.mean()
                avg_close = close_s.tail(20).mean() if len(close_s) >= 20 else close_s.mean()

                if avg_close > 0:
                    volatility = (avg_tr / avg_close) * 100
                    constraints["avg_daily_volatility_pct"] = round(volatility, 2)

                    if volatility > 5:
                        risk_score += 20
                        warnings.append(f"日均波动率 {volatility:.1f}%，高波动")
                        max_position = min(max_position, 15)
                    elif volatility > 3:
                        risk_score += 10

            # ---- 连涨/连跌天数 ----
            if "close" in kline_df.columns and "pct_chg" in kline_df.columns:
                pct = pd.to_numeric(kline_df["pct_chg"], errors="coerce").dropna()
                # 计算连涨
                consecutive_up = 0
                for v in reversed(pct):
                    if v > 0:
                        consecutive_up += 1
                    else:
                        break
                if consecutive_up >= 5:
                    risk_score += 10
                    warnings.append(f"连续上涨 {consecutive_up} 天，短线回调概率增加")

                # 计算连跌
                consecutive_down = 0
                for v in reversed(pct):
                    if v < 0:
                        consecutive_down += 1
                    else:
                        break
                if consecutive_down >= 5:
                    # 连跌不一定增加风险，但需要警示
                    warnings.append(f"连续下跌 {consecutive_down} 天，注意止损")

            # ---- 成交量异常 ----
            if "vol" in kline_df.columns or "volume" in kline_df.columns:
                vol_col = "vol" if "vol" in kline_df.columns else "volume"
                vol = pd.to_numeric(kline_df[vol_col], errors="coerce").dropna()
                if len(vol) > 20:
                    recent_avg = vol.tail(5).mean()
                    overall_avg = vol.tail(20).mean()
                    if overall_avg > 0:
                        vol_ratio = recent_avg / overall_avg
                        if vol_ratio > 3:
                            risk_score += 15
                            warnings.append(f"近期成交量放大至均量 {vol_ratio:.1f} 倍，天量需警惕")
                        elif vol_ratio < 0.3:
                            warnings.append(f"近期成交量萎缩至均量 {vol_ratio:.1f} 倍")

        # ---- RSI 极端值 ----
        rsi = self._safe_float(ti.get("rsi") or ti.get("rsi_14"))
        if rsi > 85:
            risk_score += 15
            warnings.append(f"RSI {rsi:.1f} 严重超买")
        elif rsi < 15:
            warnings.append(f"RSI {rsi:.1f} 严重超卖（可能反弹）")

        # ---- 止损位计算 ----
        current = self._safe_float(q.get("current") or q.get("price") or q.get("close"))
        if current > 0:
            constraints["stop_loss_price"] = round(current * 0.95, 2)
            constraints["stop_loss_pct"] = -5.0

        # ---- 判定风险等级 ----
        if risk_score >= 40:
            risk_level = "high"
            risk_label = "高风险"
            max_position = min(max_position, 10)
        elif risk_score >= 20:
            risk_level = "medium"
            risk_label = "中风险"
            max_position = min(max_position, 20)
        else:
            risk_level = "low"
            risk_label = "低风险"

        # 风控派的 opinion 基于风险等级反向映射
        if risk_level == "high":
            opinion = Opinion.BEARISH
            confidence = 0.8
            reasons.append("风险过高，建议观望或减仓")
        elif risk_level == "medium":
            opinion = Opinion.NEUTRAL
            confidence = 0.5
            reasons.append("风险适中，可轻仓参与")
        else:
            opinion = Opinion.BULLISH
            confidence = 0.6
            reasons.append("风险可控，可正常操作")

        if not warnings:
            warnings.append("暂无显著风险信号")

        perspective_result = PerspectiveResult(
            perspective_name=self.name, perspective_icon=self.icon,
            opinion=opinion, confidence=confidence, weight=self.weight,
            reasons=reasons, details={"risk_score": risk_score},
        )

        risk_assessment = RiskAssessment(
            risk_level=risk_level,
            risk_level_label=risk_label,
            max_position_pct=max_position,
            warnings=warnings,
            constraints=constraints,
        )

        return perspective_result, risk_assessment
