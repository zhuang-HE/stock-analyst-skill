# -*- coding: utf-8 -*-
"""
决策仪表盘报告生成器 v1.0

将算法分析结果组织为四段式决策仪表盘：

1. core_conclusion  — 一句话判词、信号类型、仓位建议
2. data_perspective — 趋势状态、价格位置、量能评估、技术指标
3. intelligence     — 消息面舆情、风险警报、利好催化
4. battle_plan      — 狙击点（买卖目标价）、仓位策略、风控清单

本模块输出结构化 JSON，由调用方（AI agent）负责人性化渲染和 LLM 解读。
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional


class DashboardReportBuilder:
    """决策仪表盘报告生成器"""

    def __init__(self):
        pass

    def build(self, analysis_result: dict, trade_plan: Optional[dict] = None,
              stock_name: str = '', stock_code: str = '') -> dict:
        """
        构建决策仪表盘

        Args:
            analysis_result: StockAnalyzer.analyze() 的完整输出
            trade_plan: TradePointCalculator.calculate() 的输出（可选）
            stock_name: 股票名称
            stock_code: 股票代码
        """
        # 提取各模块结果
        quote = analysis_result.get('quote', {})
        technical = analysis_result.get('technical', {})
        patterns = analysis_result.get('patterns', {})
        chanlun = analysis_result.get('chanlun', {})
        signal_resonance = analysis_result.get('signal_resonance', {})
        sentiment = analysis_result.get('sentiment', {})
        fundamental = analysis_result.get('fundamental', {})
        money_flow = analysis_result.get('money_flow', {})
        news = analysis_result.get('news', {})
        forecast = analysis_result.get('forecast', {})
        suggestion = analysis_result.get('suggestion', {})

        dashboard = {
            'meta': {
                'version': '5.0',
                'report_type': '决策仪表盘',
                'stock_code': stock_code,
                'stock_name': stock_name,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_date': quote.get('date', ''),
                'current_price': quote.get('price', 0),
                'change_pct': quote.get('pct_change', 0),
                'change': quote.get('change', 0),
            },
            'core_conclusion': self._build_core_conclusion(
                quote, technical, signal_resonance, sentiment, suggestion
            ),
            'data_perspective': self._build_data_perspective(
                quote, technical, patterns, chanlun, money_flow, fundamental
            ),
            'intelligence': self._build_intelligence(
                news, sentiment, forecast, fundamental
            ),
            'battle_plan': self._build_battle_plan(
                trade_plan, suggestion, quote, technical, chanlun, signal_resonance
            ),
            # 保留底层详细数据供高级用户查阅
            'raw_data': {
                'technical': technical,
                'patterns': patterns,
                'chanlun': chanlun,
                'signal_resonance': signal_resonance,
                'sentiment': sentiment,
                'fundamental': fundamental,
                'money_flow': money_flow,
                'news': news,
                'forecast': forecast
            }
        }

        return dashboard

    # ==================== 一、核心结论 ====================

    def _build_core_conclusion(self, quote: dict, technical: dict,
                                resonance: dict, sentiment: dict,
                                suggestion: dict) -> dict:
        """构建核心结论区块"""
        price = quote.get('price', 0)
        change_pct = quote.get('pct_change', 0)
        trend = technical.get('trend', '')
        total_score = suggestion.get('total_score', 50)
        action = suggestion.get('action', '观望')
        level = suggestion.get('level', '谨慎')

        # 信号类型
        signal_type = self._classify_signal_type(total_score, change_pct, trend)

        # 一句话判词
        verdict = self._generate_verdict(total_score, trend, sentiment, resonance)

        # 仓位建议
        position = suggestion.get('position', '10%')

        # LLM 解读提示（供 AI agent 生成人性化文字）
        llm_context = {
            'style': '专业投资分析',
            'tone': '客观冷静',
            'key_points': self._collect_conclusion_highlights(
                total_score, trend, resonance, sentiment
            ),
            'template': (
                f"该股当前综合评分 {total_score}/100，"
                f"技术面判断为 {trend}，信号共振 {resonance.get('resonance_level', '')}级别。"
                f"情绪指数 {sentiment.get('index_value','N/A')}"
                f"（{sentiment.get('level','N/A')}）。"
                f"综合建议：{action}，{position}仓位。"
            )
        }

        return {
            'action': action,
            'level': level,
            'total_score': total_score,
            'signal_type': signal_type,
            'verdict': verdict,
            'position': position,
            'score_breakdown': suggestion.get('score_breakdown', {}),
            'llm_context': llm_context
        }

    def _classify_signal_type(self, total_score: float, change_pct: float,
                               trend: str) -> str:
        """分类信号类型"""
        signals = []
        if total_score >= 70:
            signals.append('强做多信号')
        elif total_score >= 58:
            signals.append('做多信号')
        elif total_score >= 45:
            signals.append('中性信号')
        elif total_score >= 30:
            signals.append('谨慎信号')
        else:
            signals.append('风险信号')

        if '上升' in trend:
            signals.append('趋势向上')
        elif '下降' in trend:
            signals.append('趋势向下')

        if change_pct > 3:
            signals.append('当日大涨')
        elif change_pct < -3:
            signals.append('当日大跌')

        return ' · '.join(signals) if signals else '无明确信号'

    def _generate_verdict(self, total_score: float, trend: str,
                          sentiment: dict, resonance: dict) -> str:
        """生成一句话判词"""
        res_level = resonance.get('resonance_level', '')
        if total_score >= 70:
            return f"技术面与基本面共振 {res_level}，上升趋势确立，做多信号明确"
        elif total_score >= 58:
            return f"多头信号占优，{trend}结构完整，可逢低布局"
        elif total_score >= 45:
            return f"多空力量趋于平衡，{trend}格局，宜观望等待方向选择"
        elif total_score >= 30:
            return f"空头力量渐强，{trend}格局，应控制仓位规避风险"
        else:
            return f"多重风险信号共振，{trend}格局，建议回避或轻仓观望"

    def _collect_conclusion_highlights(self, total_score: float, trend: str,
                                        resonance: dict, sentiment: dict) -> list:
        """收集核心结论要点"""
        highlights = []
        if total_score >= 70:
            highlights.append('综合评分优秀，各项指标共振向上')
        elif total_score >= 58:
            highlights.append('综合评分良好，做多信号明确但需注意仓位')
        elif total_score <= 30:
            highlights.append('综合评分偏低，风险信号较多，建议回避')

        if resonance.get('total_score', 0) > 5:
            highlights.append(f"信号共振增强（{resonance.get('resonance_level','')}级）")

        if sentiment.get('index_value', 50) > 70:
            highlights.append('市场情绪偏向贪婪，警惕追高风险')

        return highlights

    # ==================== 二、数据透视 ====================

    def _build_data_perspective(self, quote: dict, technical: dict,
                                 patterns: dict, chanlun: dict,
                                 money_flow: dict, fundamental: dict) -> dict:
        """构建数据透视区块"""
        price = quote.get('price', 0)

        return {
            'price_position': {
                'current': price,
                'change_today': f"{quote.get('change', 0):+.2f} ({quote.get('pct_change', 0):+.2f}%)",
                'open': quote.get('open', 0),
                'high': quote.get('high', 0),
                'low': quote.get('low', 0),
                'volume': quote.get('volume', 0),
                'amount_wan': quote.get('amount', 0),  # 万
                'turnover_rate': quote.get('turnover_rate', 0),
            },
            'trend_system': self._build_trend_system(technical, price),
            'tech_indicators': self._build_tech_indicators(technical),
            'pattern_alerts': self._build_pattern_alerts(patterns),
            'chanlun_status': self._build_chanlun_status(chanlun),
            'money_flow_trend': self._build_money_flow_trend(money_flow),
            'fundamental_snapshot': self._build_fundamental_snapshot(fundamental, quote)
        }

    def _build_trend_system(self, technical: dict, price: float) -> dict:
        """趋势系统"""
        return {
            'trend_type': technical.get('trend', ''),
            'ma5': technical.get('ma5'),
            'ma10': technical.get('ma10'),
            'ma20': technical.get('ma20'),
            'ma60': technical.get('ma60'),
            'price_vs_ma': {
                'ma5': f"{'上方' if technical.get('price_above_ma5') else '下方'} (△{round(abs(price - technical.get('ma5', price)),2)})",
                'ma20': f"{'上方' if technical.get('price_above_ma20') else '下方'} (△{round(abs(price - technical.get('ma20', price)),2)})",
                'ma60': f"{'上方' if technical.get('price_above_ma60') else '下方'} (△{round(abs(price - technical.get('ma60', price)) if technical.get('ma60') else 0,2)})" if technical.get('ma60') else 'N/A',
            },
            'bollinger': {
                'upper': technical.get('boll_upper'),
                'mid': technical.get('boll_mid'),
                'lower': technical.get('boll_lower'),
                'position': self._bollinger_position(price, technical)
            }
        }

    def _bollinger_position(self, price: float, tech: dict) -> str:
        """布林带位置判断"""
        upper = tech.get('boll_upper')
        lower = tech.get('boll_lower')
        if upper and lower and lower > 0:
            ratio = (price - lower) / (upper - lower) * 100
            if ratio > 80:
                return f'上轨附近 ({ratio:.0f}%)'
            elif ratio < 20:
                return f'下轨附近 ({ratio:.0f}%)'
            else:
                return f'中轨区域 ({ratio:.0f}%)'
        return 'N/A'

    def _build_tech_indicators(self, technical: dict) -> dict:
        """技术指标摘要"""
        return {
            'rsi': {
                'value': technical.get('rsi'),
                'signal': technical.get('rsi_signal'),
            },
            'kdj': {
                'k': technical.get('k'), 'd': technical.get('d'), 'j': technical.get('j'),
                'signal': technical.get('kdj_signal'),
            },
            'macd': {
                'dif': technical.get('macd_dif'),
                'dea': technical.get('macd_dea'),
                'hist': technical.get('macd_hist'),
                'signal': technical.get('macd_signal'),
            },
            'scores': technical.get('scores', {})
        }

    def _build_pattern_alerts(self, patterns: dict) -> dict:
        """K线形态警报"""
        if not patterns or 'error' in patterns:
            return {'status': '无形态数据'}

        bullish = patterns.get('top_bullish', [])
        bearish = patterns.get('top_bearish', [])

        alert_level = 'normal'
        if len(bearish) > 2 and any(p.get('confidence', 0) > 0.7 for p in bearish):
            alert_level = 'warning'
        elif len(bullish) > 2 and any(p.get('confidence', 0) > 0.7 for p in bullish):
            alert_level = 'positive'

        return {
            'alert_level': alert_level,
            'bullish_signals': [
                {'name': p.get('name_cn', ''), 'desc': p.get('description', ''),
                 'confidence': p.get('confidence', 0), 'reliability': p.get('reliability', '')}
                for p in bullish[:3]
            ],
            'bearish_signals': [
                {'name': p.get('name_cn', ''), 'desc': p.get('description', ''),
                 'confidence': p.get('confidence', 0), 'reliability': p.get('reliability', '')}
                for p in bearish[:3]
            ],
            'summary': f"看涨形态 {patterns.get('bullish_count',0)} 个，看跌形态 {patterns.get('bearish_count',0)} 个"
        }

    def _build_chanlun_status(self, chanlun: dict) -> dict:
        """缠论状态"""
        if not chanlun or 'error' in chanlun:
            return {'status': '缠论分析不可用'}

        buy_points = chanlun.get('buy_points', [])
        return {
            'fenxing': chanlun.get('fenxing_count', 0),
            'bi': chanlun.get('bi_count', 0),
            'zhongshu': chanlun.get('zhongshu_count', 0),
            'current_trend': chanlun.get('current_trend', ''),
            'nearest_zhongshu': chanlun.get('nearest_zhongshu'),
            'buy_signals': [
                {'type': bp.get('type', ''), 'desc': bp.get('description', ''),
                 'price': bp.get('price'), 'confidence': bp.get('confidence', 0)}
                for bp in buy_points[:3]
            ],
            'signal_count': len(buy_points)
        }

    def _build_money_flow_trend(self, money_flow: dict) -> dict:
        """资金流向趋势"""
        if not money_flow or 'error' in money_flow:
            return {'status': '资金数据不可用'}

        latest = money_flow.get('latest', {})
        return {
            'date': latest.get('date', ''),
            'net_amount_wan': latest.get('net_mf_amount', 0),  # 万元
            'buy_elg_wan': latest.get('buy_elg', 0),
            'sell_elg_wan': latest.get('sell_elg', 0),
            'recent_5d_net': money_flow.get('recent_5d_net', 0),
            'recent_5d_positive_days': money_flow.get('recent_5d_positive_days', 0),
            'score': money_flow.get('score', 50),
        }

    def _build_fundamental_snapshot(self, fundamental: dict, quote: dict) -> dict:
        """基本面快照"""
        if not fundamental:
            return {'status': '基本面数据不可用'}

        fin = fundamental.get('financial', {})
        val = fundamental.get('valuation', {})
        latest = fin.get('latest', {})

        snapshot = {
            'industry': fundamental.get('industry', {}).get('identified_industry', []),
            'industry_outlook': fundamental.get('industry', {}).get('industry_outlook', ''),
            'valuation': {
                'pe_ttm': quote.get('pe_ttm', 0),
                'pb': quote.get('pb', 0),
                'pe_eval': val.get('PE评价', '未知'),
                'pb_eval': val.get('PB评价', '未知'),
                'total_mv_yi': round(quote.get('total_mv', 0) / 10000, 1) if quote.get('total_mv') else 0,
            },
            'financial_health': {
                'roe': latest.get('roe', 0),
                'revenue_yoy': latest.get('revenue_yoy', 0),
                'net_profit_yoy': latest.get('net_profit_yoy', 0),
                'gross_margin': latest.get('gross_margin', 0),
                'debt_ratio': latest.get('debt_ratio', 0),
                'eps': latest.get('eps', 0),
            },
            'trend': fin.get('trend', {}),
            'score': fundamental.get('fundamental_score', 50),
            'score_reasons': fundamental.get('fundamental_reasons', []),
        }

        return snapshot

    # ==================== 三、情报解读 ====================

    def _build_intelligence(self, news: dict, sentiment: dict,
                            forecast: dict, fundamental: dict) -> dict:
        """构建情报解读区块（消息面 + 风险 + 催化）"""
        intelligence = {
            'news_brief': self._build_news_brief(news),
            'sentiment_overview': self._build_sentiment_overview(sentiment),
            'risk_alerts': self._collect_risk_alerts(news, fundamental),
            'catalysts': self._collect_catalysts(news, forecast),
            'forecast_outlook': self._build_forecast_outlook(forecast),
        }

        # LLM 解读提示
        intelligence['llm_context'] = {
            'task': '基于以下数据生成200字以内的情报解读',
            'key_points': [
                f"消息面情绪：{news.get('sentiment', '中性')}（得分{news.get('sentiment_score',0)}）",
                f"市场情绪：{sentiment.get('level','未知')}（指数{sentiment.get('index_value','N/A')}）",
            ],
            'guidance': (
                '请用专业、客观的语气解读以上信息。'
                '重点关注：近期消息面的多空博弈、情绪指标的信号含义、潜在的风险点。'
                '避免使用绝对化语言（如"必然上涨""肯定大跌"）。'
            )
        }

        return intelligence

    def _build_news_brief(self, news: dict) -> dict:
        """消息面简报"""
        if not news or 'error' in news:
            return {'status': '无消息数据'}

        items = news.get('items', [])
        return {
            'sentiment': news.get('sentiment', '中性'),
            'sentiment_score': news.get('sentiment_score', 0),
            'item_count': len(items),
            'recent_3': [
                {'title': item.get('title', ''), 'date': item.get('date', ''),
                 'channel': item.get('channels', '')}
                for item in items[:3]
            ]
        }

    def _build_sentiment_overview(self, sentiment: dict) -> dict:
        """情绪概览"""
        if not sentiment or 'error' in sentiment:
            return {'status': '无情绪数据'}

        return {
            'index_value': sentiment.get('index_value', 50),
            'level': sentiment.get('level', '中性'),
            'description': sentiment.get('description', ''),
            'trend': sentiment.get('trend', ''),
            'signal': sentiment.get('signal', ''),
            'components': sentiment.get('components', {})
        }

    def _collect_risk_alerts(self, news: dict, fundamental: dict) -> list:
        """收集风险警报"""
        alerts = []

        # 消息面风险
        if news and 'error' not in news:
            if news.get('sentiment') == '偏空':
                alerts.append({
                    'level': 'warning',
                    'type': '消息面',
                    'content': '近期消息面偏空，存在负面舆情',
                })

        # 财务风险
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})

        # 估值风险
        val = fundamental.get('valuation', {})
        pe_eval = val.get('PE评价', '')
        if '高估' in pe_eval:
            alerts.append({
                'level': 'warning',
                'type': '估值风险',
                'content': f'当前估值{pe_eval}，存在估值回归风险',
            })

        # 财务健康风险
        fin_score = fundamental.get('fundamental_score', 50)
        if fin_score < 30:
            alerts.append({
                'level': 'danger',
                'type': '财务风险',
                'content': f'基本面评分仅{fin_score}/100，财务状况堪忧',
            })

        revenue_yoy = load_float(latest.get('revenue_yoy', 0))
        if revenue_yoy < -20:
            alerts.append({
                'level': 'danger',
                'type': '经营风险',
                'content': f'营收同比下滑{abs(revenue_yoy)}%，经营面临挑战',
            })

        if not alerts:
            alerts.append({
                'level': 'info',
                'type': '综合',
                'content': '暂未发现显著风险信号',
            })

        return alerts

    def _collect_catalysts(self, news: dict, forecast: dict) -> list:
        """收集利好催化因素"""
        catalysts = []

        if news and 'error' not in news:
            if news.get('sentiment') == '偏多':
                catalysts.append({
                    'type': '消息面',
                    'content': '近期消息面偏多，存在正面舆情催化',
                })

        if forecast and 'error' not in forecast:
            growth = forecast.get('expected_growth', '')
            direction = forecast.get('growth_direction', '')
            if direction == '上升' and growth:
                catalysts.append({
                    'type': '盈利预期',
                    'content': f'分析师预期未来盈利增长 {growth}',
                })

            coverage = forecast.get('coverage_level', '')
            if '高关注' in coverage:
                catalysts.append({
                    'type': '市场关注',
                    'content': f'分析师{coverage}（{forecast.get("analyst_coverage", 0)}人覆盖），市场关注度高',
                })

        if not catalysts:
            catalysts.append({
                'type': '一般',
                'content': '暂未发现明确催化因素，需持续跟踪',
            })

        return catalysts

    def _build_forecast_outlook(self, forecast: dict) -> dict:
        """盈利预测展望"""
        if not forecast or 'error' in forecast:
            return {'status': '无盈利预测数据'}

        return {
            'forecasts': forecast.get('forecasts', []),
            'expected_growth': forecast.get('expected_growth', ''),
            'growth_direction': forecast.get('growth_direction', ''),
            'analyst_coverage': forecast.get('analyst_coverage', 0),
            'coverage_level': forecast.get('coverage_level', ''),
        }

    # ==================== 四、作战计划 ====================

    def _build_battle_plan(self, trade_plan: Optional[dict], suggestion: dict,
                           quote: dict, technical: dict, chanlun: dict,
                           resonance: dict) -> dict:
        """构建作战计划区块"""
        current_price = quote.get('price', 0)

        plan = {
            'direction': suggestion.get('action', '观望'),
            'current_price': current_price,
            'position_advice': {
                'suggested_pct': suggestion.get('position', '10%'),
                'level': suggestion.get('level', '谨慎'),
                'total_score': suggestion.get('total_score', 50),
            }
        }

        # 集成 trade_points 计算结果
        if trade_plan:
            plan['strike_points'] = {
                'buy_entry': self._extract_trade_points(trade_plan.get('buy_points', []), 'buy'),
                'sell_targets': self._extract_trade_points(trade_plan.get('sell_points', []), 'sell'),
                'stop_loss': self._extract_trade_points(
                    [trade_plan['stop_loss']] if trade_plan.get('stop_loss') else [], 'stop'
                ),
                'risk_reward_ratio': trade_plan.get('risk_reward_ratio', 0),
            }
            plan['position_strategy'] = {
                'suggestion': trade_plan.get('position_suggestion', ''),
                'pct': trade_plan.get('position_pct', 0),
            }
        else:
            # 降级方案：基于传统建议
            plan['strike_points'] = self._build_fallback_strike_points(
                current_price, technical, chanlun, suggestion
            )
            plan['position_strategy'] = {
                'suggestion': suggestion.get('action', '观望'),
                'pct': int(suggestion.get('position', '10').replace('%', '')),
            }

        # 风险控制清单
        plan['risk_control'] = self._build_risk_control(
            current_price, resonance, suggestion
        )

        # LLM 解读提示
        plan['llm_context'] = {
            'task': '基于以下数据生成操作建议',
            'guidance': (
                '请用客观专业的语言描述当前的操作建议。'
                '必须包含：买入点位和条件、卖出目标、止损线、建议仓位比例。'
                '注意：必须强调"投资有风险""本分析仅供参考"。'
                '避免给出过于具体的交易指令（如"立即全仓买入"）。'
            )
        }

        return plan

    def _extract_trade_points(self, points: list, ptype: str) -> list:
        """提取交易点位"""
        result = []
        for p in points:
            if isinstance(p, dict):
                result.append({
                    'type': p.get('point_type', ''),
                    'price': p.get('price', 0),
                    'source': p.get('source', ''),
                    'description': p.get('description', ''),
                    'confidence': p.get('confidence', 0),
                    'conditions': p.get('trigger_conditions', []),
                    'risk_note': p.get('risk_note', ''),
                })
        return result

    def _build_fallback_strike_points(self, current_price: float,
                                       technical: dict, chanlun: dict,
                                       suggestion: dict) -> dict:
        """降级方案：基于传统技术分析的买卖点"""
        # 基于布林带
        boll_lower = technical.get('boll_lower', current_price * 0.9)
        boll_mid = technical.get('boll_mid', current_price)
        boll_upper = technical.get('boll_upper', current_price * 1.1)

        # 基于MA
        ma20 = technical.get('ma20', current_price)

        buy_entry = None
        sell_targets = []
        stop_loss = None

        # 入买点
        if current_price > boll_mid:
            buy_entry = {
                'type': 'buy_entry',
                'price': round(boll_mid, 2),
                'source': '布林中轨',
                'description': f'回踩布林中轨 ¥{round(boll_mid,2)} 可试探性建仓',
                'confidence': 55,
                'conditions': ['价格回踩布林中轨', '成交量萎缩'],
                'risk_note': '若跌破中轨转弱，应止损'
            }
        else:
            buy_entry = {
                'type': 'buy_entry',
                'price': round(boll_lower, 2),
                'source': '布林下轨',
                'description': f'触及布林下轨 ¥{round(boll_lower,2)} 可考虑建仓',
                'confidence': 60,
                'conditions': ['价格触及下轨', '出现超卖信号'],
                'risk_note': '下轨破位则继续观望'
            }

        # 卖出目标
        target1 = round(max(boll_mid * 1.02, current_price * 0.99), 2)
        target2 = round(boll_upper, 2)
        if target2 > target1 * 1.03:
            sell_targets = [
                {
                    'type': 'sell_target',
                    'price': target1,
                    'source': '短期目标',
                    'description': f'第一目标 ¥{target1}（短期技术阻力）',
                    'confidence': 50,
                    'conditions': ['触及目标价', '分批止盈']
                },
                {
                    'type': 'sell_target',
                    'price': target2,
                    'source': '布林上轨',
                    'description': f'保守目标 ¥{target2}（上轨压力）',
                    'confidence': 40,
                    'conditions': ['触及上轨', '出现超买信号']
                }
            ]
        else:
            sell_targets = [{
                'type': 'sell_target',
                'price': target2,
                'source': '布林上轨',
                'description': f'目标价 ¥{target2}（上轨）',
                'confidence': 45,
                'conditions': ['触及目标', '配合超买信号减仓']
            }]

        # 止损
        stop_price = round(max(ma20 * 0.95, boll_lower * 0.98, current_price * 0.93), 2)
        stop_loss = {
            'type': 'stop_loss',
            'price': stop_price,
            'source': '综合止损',
            'description': f'止损线 ¥{stop_price}',
            'confidence': 70,
            'conditions': ['收盘价确认跌破', '严格执行'],
            'risk_note': '跌破止损位必须离场'
        }

        return {
            'buy_entry': [buy_entry],
            'sell_targets': sell_targets,
            'stop_loss': [stop_loss],
            'risk_reward_ratio': round(
                (sell_targets[0]['price'] - current_price) / (current_price - stop_price), 2
            ) if (current_price - stop_price) > 0 else 0,
        }

    def _build_risk_control(self, current_price: float, resonance: dict,
                            suggestion: dict) -> list:
        """构建风险控制清单"""
        controls = [
            {
                'rule': '单票仓位上限',
                'detail': '不超过总资金的30%',
                'priority': 'must'
            },
            {
                'rule': '止损纪律',
                'detail': '严格执行止损线，到达即离场，不加仓摊平',
                'priority': 'must'
            },
        ]

        total_score = suggestion.get('total_score', 50)
        if total_score < 45:
            controls.append({
                'rule': '轻仓或观望',
                'detail': f'当前评分{total_score}偏低，建议控制仓位在10%以内',
                'priority': 'recommend'
            })

        controls.append({
            'rule': '跟踪关键位',
            'detail': '每日复盘：关注是否突破关键支撑/压力位',
            'priority': 'suggest'
        })

        return controls


# ==================== 工具函数 ====================

def load_float(val, default=0.0):
    """安全浮点数转换"""
    if val is None:
        return default
    try:
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '')
        return float(val)
    except (ValueError, TypeError):
        return default


def build_dashboard(analysis_result: dict, trade_plan: dict = None,
                    stock_name: str = '', stock_code: str = '') -> dict:
    """便捷函数：构建决策仪表盘"""
    builder = DashboardReportBuilder()
    return builder.build(analysis_result, trade_plan, stock_name, stock_code)
