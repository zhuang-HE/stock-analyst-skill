# -*- coding: utf-8 -*-
"""
买卖点位计算器 v1.0

基于多个维度的支撑/压力位综合计算目标买卖价格：
- 缠论买卖点（中枢/笔确定的精确位置）
- 布林带（超买/超卖边界）
- 均线系统（MA5/MA10/MA20/MA60 支撑）
- 近期高低点
- 斐波那契回撤位

输出：狙击点（最佳买卖目标价）及其置信度
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PriceLevel:
    """价格关卡"""
    price: float
    level_type: str  # support / resistance
    source: str  # chanlun / bollinger / ma / fib / recent_high_low
    strength: float  # 0-100, 此关卡的强度评分
    description: str
    is_key: bool = False  # 是否为关键关卡


@dataclass
class TradePoint:
    """买卖操作点"""
    point_type: str  # buy_entry / buy_add / sell_target / stop_loss
    price: float
    confidence: int  # 0-100
    source: str  # 计算来源
    description: str
    trigger_conditions: List[str] = field(default_factory=list)
    risk_note: str = ''


@dataclass
class TradePlan:
    """交易计划"""
    stock_code: str
    current_price: float
    direction: str  # long / short / neutral
    buy_points: List[TradePoint] = field(default_factory=list)
    sell_points: List[TradePoint] = field(default_factory=list)
    stop_loss: Optional[TradePoint] = None
    position_suggestion: str = ''
    position_pct: int = 0  # 建议仓位百分比
    risk_reward_ratio: float = 0.0
    key_support: List[PriceLevel] = field(default_factory=list)
    key_resistance: List[PriceLevel] = field(default_factory=list)
    summary: str = ''


class TradePointCalculator:
    """买卖点位计算器"""

    def __init__(self):
        pass

    def calculate(self, df: pd.DataFrame, chanlun_result: dict = None,
                  sentiment: dict = None, signal_resonance: dict = None,
                  current_price: float = 0.0, stock_code: str = '') -> TradePlan:
        """
        综合计算买卖点和交易计划

        Args:
            df: 含技术指标的日线DataFrame（需已计算MA/布林带等）
            chanlun_result: 缠论分析结果
            sentiment: 情绪指数结果
            signal_resonance: 信号共振结果
            current_price: 当前价格
            stock_code: 股票代码
        """
        if current_price == 0 and len(df) > 0:
            current_price = float(df.iloc[-1]['close'])

        plan = TradePlan(
            stock_code=stock_code,
            current_price=round(current_price, 2)
        )

        # 1. 收集所有支撑/压力位
        supports, resistances = self._collect_levels(df, chanlun_result, current_price)

        # 2. 筛选关键关卡
        plan.key_support = self._select_key_levels(supports, 'support', current_price)
        plan.key_resistance = self._select_key_levels(resistances, 'resistance', current_price)

        # 3. 生成买入点
        plan.buy_points = self._generate_buy_points(
            plan.key_support, current_price, chanlun_result, signal_resonance
        )

        # 4. 生成卖出点
        plan.sell_points = self._generate_sell_points(
            plan.key_resistance, current_price, chanlun_result, sentiment
        )

        # 5. 止损点
        plan.stop_loss = self._generate_stop_loss(
            plan.key_support, current_price
        )

        # 6. 方向判断
        plan.direction = self._determine_direction(
            plan.buy_points, plan.sell_points, sentiment, signal_resonance
        )

        # 7. 仓位建议
        plan.position_pct, plan.position_suggestion = self._suggest_position(
            plan.direction, sentiment, signal_resonance
        )

        # 8. 风险收益比
        plan.risk_reward_ratio = self._calc_risk_reward(plan, current_price)

        # 9. 生成摘要
        plan.summary = self._generate_summary(plan)

        return plan

    # ==================== 关卡收集 ====================

    def _collect_levels(self, df: pd.DataFrame, chanlun: dict,
                        current_price: float) -> tuple:
        """收集所有支撑/压力位"""
        supports = []
        resistances = []

        # 1. 布林带支撑/压力
        supports.extend(self._bollinger_levels(df))
        resistances.extend(self._bollinger_levels(df))

        # 2. 均线支撑
        supports.extend(self._ma_levels(df, current_price))
        resistances.extend(self._ma_levels(df, current_price))

        # 3. 近期高低点
        supports.extend(self._recent_high_low(df, current_price))
        resistances.extend(self._recent_high_low(df, current_price))

        # 4. 缠论中枢
        if chanlun and 'error' not in chanlun:
            cl_supports, cl_resistances = self._chanlun_levels(chanlun, current_price)
            supports.extend(cl_supports)
            resistances.extend(cl_resistances)

        # 5. 斐波那契回撤
        fib_levels = self._fibonacci_levels(df, current_price)
        supports.extend(fib_levels)
        resistances.extend(fib_levels)

        # 按价格排序并去重
        supports = self._deduplicate_levels(supports)
        resistances = self._deduplicate_levels(resistances)

        return supports, resistances

    def _bollinger_levels(self, df: pd.DataFrame) -> list:
        """布林带支撑/压力位"""
        levels = []
        latest = df.iloc[-1]

        if all(k in latest.index for k in ['boll_lower', 'boll_mid', 'boll_upper']):
            mid = float(latest['boll_mid'])
            upper = float(latest['boll_upper'])
            lower = float(latest['boll_lower'])

            if not pd.isna(upper):
                levels.append(PriceLevel(
                    price=round(upper, 2), level_type='resistance',
                    source='布林上轨', strength=65,
                    description='布林上轨压力位，2倍标准差'
                ))
            if not pd.isna(mid):
                levels.append(PriceLevel(
                    price=round(mid, 2), level_type='support',
                    source='布林中轨', strength=55,
                    description='布林中轨（20日均线），动态平衡位'
                ))
            if not pd.isna(lower):
                levels.append(PriceLevel(
                    price=round(lower, 2), level_type='support',
                    source='布林下轨', strength=70,
                    description='布林下轨支撑位，2倍标准差', is_key=True
                ))

            # 布林带宽度（波动率信息）
            if upper > 0 and mid > 0:
                bandwidth = (upper - lower) / mid * 100
                # 如果布林带压缩（带宽<10%），中轨可能成为强支撑/压力
                if bandwidth < 10:
                    for lv in levels:
                        if lv.source == '布林中轨':
                            lv.strength = 70
                            lv.description += '（带宽压缩，变盘预警）'

        return levels

    def _ma_levels(self, df: pd.DataFrame, current_price: float) -> list:
        """均线支撑/压力位"""
        levels = []
        latest = df.iloc[-1]

        ma_configs = [
            ('ma5', 'MA5', 40, '5日均线'),
            ('ma10', 'MA10', 45, '10日均线'),
            ('ma20', 'MA20', 55, '20日均线'),
            ('ma60', 'MA60', 70, '60日均线（中期趋势分界线）'),
        ]

        for col, name, strength, desc in ma_configs:
            if col in latest.index:
                val = float(latest[col])
                if not pd.isna(val):
                    is_key = (col == 'ma60')
                    lt = 'support' if val < current_price else 'resistance'
                    levels.append(PriceLevel(
                        price=round(val, 2), level_type=lt,
                        source=name, strength=strength,
                        description=desc, is_key=is_key
                    ))

        return levels

    def _recent_high_low(self, df: pd.DataFrame, current_price: float) -> list:
        """近期高低点"""
        levels = []

        for period, label, strength in [
            (20, '20日', 50),
            (60, '60日', 65),
            (120, '120日', 75),
        ]:
            if len(df) >= period:
                recent = df.tail(period)
                high = float(recent['high'].max())
                low = float(recent['low'].min())

                levels.append(PriceLevel(
                    price=round(high, 2), level_type='resistance',
                    source=f'{label}最高', strength=strength,
                    description=f'{label}内最高价，关键压力位', is_key=(period >= 60)
                ))
                levels.append(PriceLevel(
                    price=round(low, 2), level_type='support',
                    source=f'{label}最低', strength=strength,
                    description=f'{label}内最低价，关键支撑位', is_key=(period >= 60)
                ))

        return levels

    def _chanlun_levels(self, chanlun: dict, current_price: float) -> tuple:
        """从缠论分析结果提取支撑/压力位"""
        supports = []
        resistances = []

        nearest_zs = chanlun.get('nearest_zhongshu')
        if nearest_zs and isinstance(nearest_zs, dict):
            zs_high = nearest_zs.get('high', 0)
            zs_low = nearest_zs.get('low', 0)
            if zs_high > 0 and zs_low > 0:
                resistances.append(PriceLevel(
                    price=round(zs_high, 2), level_type='resistance',
                    source='缠论中枢上沿', strength=75,
                    description='最近中枢上沿，突破后转为支撑', is_key=True
                ))
                supports.append(PriceLevel(
                    price=round(zs_low, 2), level_type='support',
                    source='缠论中枢下沿', strength=80,
                    description='最近中枢下沿，破位则走势转弱', is_key=True
                ))

        # 缠论买卖点自身就是明确的交易位置
        buy_points = chanlun.get('buy_points', [])
        for bp in buy_points:
            if bp.get('price') and bp['price'] > 0:
                bp_price = round(bp['price'], 2)
                label = f"缠论{bp.get('type','')}"
                supports.append(PriceLevel(
                    price=bp_price, level_type='support',
                    source=label, strength=85,
                    description=f"缠论{bp.get('description','买点')}",
                    is_key=(bp.get('confidence', 0) > 0.6)
                ))

        return supports, resistances

    def _fibonacci_levels(self, df: pd.DataFrame, current_price: float) -> list:
        """斐波那契回撤位"""
        levels = []
        if len(df) < 30:
            return levels

        recent_60 = df.tail(60)
        high = float(recent_60['high'].max())
        low = float(recent_60['low'].min())
        diff = high - low

        if diff <= 0 or current_price / diff < 0.001:
            return levels

        fib_ratios = {
            0.236: '斐波那契23.6%',
            0.382: '斐波那契38.2%',
            0.500: '斐波那契50%',
            0.618: '斐波那契61.8%（黄金分割）',
            0.786: '斐波那契78.6%',
        }

        for ratio, label in fib_ratios.items():
            price = round(low + diff * ratio, 2)
            # 决定是支撑还是压力
            if price < current_price * 0.99:
                lt = 'support'
            elif price > current_price * 1.01:
                lt = 'resistance'
            else:
                lt = 'support'  # 接近当前价，当作支撑

            levels.append(PriceLevel(
                price=price, level_type=lt,
                source=label, strength=45,
                description=f'从60日区间计算的回撤位',
                is_key=(abs(ratio - 0.618) < 0.01)
            ))

        return levels

    def _deduplicate_levels(self, levels: List[PriceLevel]) -> List[PriceLevel]:
        """去重合并相近价格关卡（1%内视为同一位）"""
        if not levels:
            return []
        # 按价格排序
        sorted_levels = sorted(levels, key=lambda x: x.price)
        merged = []
        for lv in sorted_levels:
            if merged and abs(lv.price - merged[-1].price) / merged[-1].price < 0.01:
                # 合并：取更高强度
                if lv.strength > merged[-1].strength:
                    merged[-1] = lv
                elif lv.strength == merged[-1].strength:
                    merged[-1].source += '/' + lv.source
            else:
                merged.append(lv)
        return merged

    def _select_key_levels(self, levels: List[PriceLevel], ltype: str,
                           current_price: float) -> List[PriceLevel]:
        """筛选关键关卡"""
        # 标记 is_key 的 + 强度 >= 60 的
        key_levels = [lv for lv in levels if lv.is_key or lv.strength >= 60]
        # 按与当前价的距离排序（最近的优先）
        key_levels.sort(key=lambda x: abs(x.price - current_price))
        return key_levels[:5]  # 最多5个

    # ==================== 买卖点生成 ====================

    def _generate_buy_points(self, supports: List[PriceLevel],
                             current_price: float, chanlun: dict,
                             resonance: dict) -> List[TradePoint]:
        """生成买入点"""
        points = []

        # 按支撑位强度排序
        sorted_supports = sorted(supports, key=lambda x: x.strength, reverse=True)

        # 入场买点：最接近当前价且在其下方的强支撑
        below_supports = [s for s in sorted_supports if s.price < current_price * 0.99]
        if below_supports:
            entry = below_supports[0]
            points.append(TradePoint(
                point_type='buy_entry',
                price=entry.price,
                confidence=min(80, entry.strength + 10),
                source=entry.source,
                description=f'入场狙击位：{entry.description}',
                trigger_conditions=[
                    f'价格回踩至 ¥{entry.price} 附近',
                    '成交量萎缩至近期均量60%以下',
                    'KDJ/RSI 出现底背离或超卖信号'
                ],
                risk_note='若放量跌破此位，应止损观望'
            ))

            # 加仓位：更低的强支撑
            if len(below_supports) >= 2:
                add = below_supports[1]
                points.append(TradePoint(
                    point_type='buy_add',
                    price=add.price,
                    confidence=add.strength,
                    source=add.source,
                    description=f'加仓位置：{add.description}',
                    trigger_conditions=[
                        f'价格触及 ¥{add.price} 附近',
                        '出现底分型或长下影线'
                    ]
                ))

        return points

    def _generate_sell_points(self, resistances: List[PriceLevel],
                               current_price: float, chanlun: dict,
                               sentiment: dict) -> List[TradePoint]:
        """生成卖出点"""
        points = []

        sorted_resistances = sorted(resistances, key=lambda x: x.strength, reverse=True)

        above_resistances = [r for r in sorted_resistances
                             if r.price > current_price * 1.01]
        if above_resistances:
            # 第一目标：最近的强压力
            target1 = above_resistances[0]
            points.append(TradePoint(
                point_type='sell_target',
                price=target1.price,
                confidence=min(75, target1.strength),
                source=target1.source,
                description=f'第一目标位：{target1.description}',
                trigger_conditions=[
                    f'价格接近 ¥{target1.price} 时可分批减仓',
                    '若放量突破此位则可继续持有'
                ]
            ))

            # 第二目标：更远的强压力
            if len(above_resistances) >= 2:
                target2 = above_resistances[1]
                points.append(TradePoint(
                    point_type='sell_target',
                    price=target2.price,
                    confidence=target2.strength - 10,
                    source=target2.source,
                    description=f'第二目标位：{target2.description}',
                    trigger_conditions=[
                        f'若突破第一目标位，可将获利目标上移至 ¥{target2.price}'
                    ]
                ))

        return points

    def _generate_stop_loss(self, supports: List[PriceLevel],
                            current_price: float) -> Optional[TradePoint]:
        """生成止损点"""
        below_supports = [s for s in supports if s.price < current_price * 0.97]
        # 取最强者中较近的那个（-3%到-10%之间）
        candidates = [s for s in below_supports
                      if s.price > current_price * 0.90]
        sorted_candidates = sorted(candidates, key=lambda x: x.strength, reverse=True)

        if sorted_candidates:
            stop = sorted_candidates[0]
            stop_pct = round((current_price - stop.price) / current_price * 100, 1)
            return TradePoint(
                point_type='stop_loss',
                price=stop.price,
                confidence=min(90, stop.strength + 15),
                source=f'{stop.source} + 风险控制',
                description=f'止损位：{stop.description}（-{stop_pct}%）',
                trigger_conditions=[
                    f'收盘价确认跌破 ¥{stop.price}',
                    '严格执行止损，不可犹豫'
                ],
                risk_note='跌破此位意味着短期趋势走坏，必须离场'
            )

        # 如果没有找到合适的，按-5%设置硬止损
        hard_stop = round(current_price * 0.95, 2)
        return TradePoint(
            point_type='stop_loss',
            price=hard_stop,
            confidence=60,
            source='硬止损规则',
            description='硬止损位（-5%）',
            trigger_conditions=['价格跌破 ¥{:.2f} 时无条件止损'.format(hard_stop)],
            risk_note='未找到可靠技术支撑，使用保守止损'
        )

    # ==================== 综合判断 ====================

    def _determine_direction(self, buy_points: list, sell_points: list,
                              sentiment: dict, resonance: dict) -> str:
        """判断交易方向"""
        bullish_score = 0
        bearish_score = 0

        # 买入点质量
        for bp in buy_points:
            if bp.point_type == 'buy_entry':
                bullish_score += bp.confidence * 1.5

        # 卖出目标距当前价越远，多头越有信心
        for sp in sell_points:
            if sp.point_type == 'sell_target':
                bullish_score += sp.confidence * 0.3

        # 信号共振
        if resonance and 'error' not in resonance:
            res_total = resonance.get('total_score', 0)
            if res_total > 0:
                bullish_score += abs(res_total) * 0.5
            else:
                bearish_score += abs(res_total) * 0.5

        # 情绪
        if sentiment and 'error' not in sentiment:
            sent_idx = sentiment.get('index_value', 50)
            if sent_idx < 25:
                bullish_score += 20  # 极端恐惧时逆向加仓
            elif sent_idx > 75:
                bearish_score += 15  # 极端贪婪时警惕

        score_diff = bullish_score - bearish_score
        if score_diff > 30:
            return 'long'
        elif score_diff < -20:
            return 'short'
        else:
            return 'neutral'

    def _suggest_position(self, direction: str, sentiment: dict,
                          resonance: dict) -> tuple:
        """建议仓位"""
        if direction == 'long':
            base_pct = 30
            # 信号共振加分
            if resonance and 'error' not in resonance:
                confidence = resonance.get('confidence', 0.5)
                base_pct += int(confidence * 20)
            # 情绪调整
            if sentiment and 'error' not in sentiment:
                sent_idx = sentiment.get('index_value', 50)
                if sent_idx < 30:
                    base_pct += 15  # 恐慌时可适当加仓
                elif sent_idx > 70:
                    base_pct -= 10  # 贪婪时降低仓位
            position_pct = max(5, min(80, base_pct))
            if position_pct >= 50:
                suggestion = f'重仓（{position_pct}%），信号共振明显，建议分批建仓'
            elif position_pct >= 20:
                suggestion = f'中等仓位（{position_pct}%），谨慎乐观，建议逢低介入'
            else:
                suggestion = f'轻仓（{position_pct}%），试探性建仓，等待更明确信号'
        elif direction == 'short':
            position_pct = max(5, min(30, 10))
            suggestion = f'不建议做多，当前空头信号占优。若已持仓，建议降低至{position_pct}%以内'
        else:
            position_pct = 10
            suggestion = '方向不明，建议保持低仓位或观望，等待信号明朗'

        return position_pct, suggestion

    def _calc_risk_reward(self, plan: TradePlan, current_price: float) -> float:
        """计算风险收益比"""
        if not plan.sell_points or not plan.stop_loss:
            return 0.0

        # 取第一目标位
        first_target = plan.sell_points[0].price
        reward = abs(first_target - current_price)

        stop = plan.stop_loss.price
        risk = abs(current_price - stop)

        if risk > 0:
            ratio = round(reward / risk, 2)
        else:
            ratio = 0.0

        return ratio

    def _generate_summary(self, plan: TradePlan) -> str:
        """生成交易计划摘要"""
        parts = [f"当前价 ¥{plan.current_price}，方向: {'做多' if plan.direction=='long' else ('做空' if plan.direction=='short' else '观望')}"]

        if plan.buy_points:
            bp_entry = [bp for bp in plan.buy_points if bp.point_type == 'buy_entry']
            if bp_entry:
                parts.append(f"入场狙击点: ¥{bp_entry[0].price}（{bp_entry[0].source}）")

        if plan.sell_points:
            parts.append(f"第一目标: ¥{plan.sell_points[0].price}")

        if plan.stop_loss:
            parts.append(f"止损: ¥{plan.stop_loss.price}")

        if plan.risk_reward_ratio > 0:
            quality = '优秀' if plan.risk_reward_ratio > 2.5 else ('良好' if plan.risk_reward_ratio > 1.5 else '一般')
            parts.append(f"风险收益比: {plan.risk_reward_ratio} ({quality})")

        parts.append(f"建议仓位: {plan.position_suggestion}")

        return '；'.join(parts)
