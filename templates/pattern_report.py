"""
交易形态识别和建议策略报告模块
整合K线形态、信号共振、情绪指数、缠论买卖点
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

# 导入分析模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patterns import analyze_candlestick_patterns, analyze_chanlun
from signals import analyze_signal_resonance
from ai_models import calculate_sentiment_index


class PatternAnalysisReport:
    """交易形态分析报告生成器"""
    
    def __init__(self):
        self.report_data = {}
    
    def generate_report(self, df: pd.DataFrame, stock_info: Dict = None) -> Dict:
        """
        生成完整的形态分析报告
        
        Args:
            df: 价格数据
            stock_info: 股票信息
            
        Returns:
            报告数据字典
        """
        # 1. K线形态分析
        candlestick_result = analyze_candlestick_patterns(df)
        
        # 2. 缠论分析
        chanlun_result = analyze_chanlun(df)
        
        # 3. 信号共振分析
        resonance_result = analyze_signal_resonance(
            df=df,
            pattern_result=candlestick_result,
            chanlun_result=chanlun_result
        )
        
        # 4. 情绪指数
        sentiment_result = calculate_sentiment_index(df)
        
        # 5. 生成策略建议
        strategy_advice = self._generate_strategy_advice(
            candlestick_result, chanlun_result, resonance_result, sentiment_result
        )
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stock_info': stock_info or {},
            'candlestick': candlestick_result,
            'chanlun': chanlun_result,
            'resonance': resonance_result,
            'sentiment': sentiment_result,
            'strategy_advice': strategy_advice,
            'summary': self._generate_summary(
                candlestick_result, chanlun_result, resonance_result, sentiment_result
            )
        }
    
    def _generate_strategy_advice(self, candlestick: Dict, chanlun: Dict,
                                  resonance: object, sentiment: object) -> Dict:
        """生成策略建议"""
        advice = {
            'primary_action': '观望',
            'confidence': 0,
            'entry_points': [],
            'exit_points': [],
            'risk_level': '中等',
            'position_suggestion': '',
            'reasoning': []
        }
        
        # 基于共振评分确定主要操作
        if resonance.total_score > 50:
            advice['primary_action'] = '强烈买入'
            advice['confidence'] = min(0.95, resonance.confidence)
        elif resonance.total_score > 25:
            advice['primary_action'] = '买入'
            advice['confidence'] = min(0.85, resonance.confidence)
        elif resonance.total_score < -50:
            advice['primary_action'] = '强烈卖出'
            advice['confidence'] = min(0.95, resonance.confidence)
        elif resonance.total_score < -25:
            advice['primary_action'] = '卖出'
            advice['confidence'] = min(0.85, resonance.confidence)
        else:
            advice['primary_action'] = '观望'
            advice['confidence'] = 0.5
        
        # 缠论买卖点
        chanlun_advice = chanlun.get('buy_points', [])
        for bp in chanlun_advice[-2:]:  # 最近2个买卖点
            if '买' in bp.bp_type.value:
                advice['entry_points'].append({
                    'type': f"缠论{bp.bp_type.value}",
                    'price': round(bp.price, 2),
                    'confidence': bp.confidence
                })
            else:
                advice['exit_points'].append({
                    'type': f"缠论{bp.bp_type.value}",
                    'price': round(bp.price, 2),
                    'confidence': bp.confidence
                })
        
        # 情绪指数建议
        if sentiment.index_value <= 25:
            advice['entry_points'].append({
                'type': '情绪极端恐慌',
                'price': '当前价附近',
                'confidence': 0.8
            })
        elif sentiment.index_value >= 75:
            advice['exit_points'].append({
                'type': '情绪极端贪婪',
                'price': '当前价附近',
                'confidence': 0.8
            })
        
        # 仓位建议
        if resonance.total_score > 40:
            advice['position_suggestion'] = '重仓（70-80%）'
            advice['risk_level'] = '中高'
        elif resonance.total_score > 20:
            advice['position_suggestion'] = '中等仓位（50-60%）'
            advice['risk_level'] = '中等'
        elif resonance.total_score < -40:
            advice['position_suggestion'] = '空仓或轻仓（<20%）'
            advice['risk_level'] = '高'
        elif resonance.total_score < -20:
            advice['position_suggestion'] = '减仓（30-40%）'
            advice['risk_level'] = '中高'
        else:
            advice['position_suggestion'] = '轻仓观望（20-30%）'
            advice['risk_level'] = '中等'
        
        # 推理逻辑
        advice['reasoning'] = self._generate_reasoning(
            candlestick, chanlun, resonance, sentiment
        )
        
        return advice
    
    def _generate_reasoning(self, candlestick: Dict, chanlun: Dict,
                           resonance: object, sentiment: object) -> List[str]:
        """生成推理逻辑"""
        reasoning = []
        
        # K线形态推理
        if candlestick.get('top_bullish'):
            top_pattern = candlestick['top_bullish'][0]
            reasoning.append(f"K线形态：出现{top_pattern.name_cn}，{top_pattern.description}")
        elif candlestick.get('top_bearish'):
            top_pattern = candlestick['top_bearish'][0]
            reasoning.append(f"K线形态：出现{top_pattern.name_cn}，{top_pattern.description}")
        
        # 缠论推理
        if chanlun.get('buy_points'):
            latest_bp = chanlun['buy_points'][-1]
            reasoning.append(f"缠论分析：出现{latest_bp.bp_type.value}信号，{latest_bp.description}")
        
        # 共振推理
        reasoning.append(f"信号共振：{resonance.summary}")
        
        # 情绪推理
        reasoning.append(f"市场情绪：{sentiment.level.value}（指数{sentiment.index_value}），{sentiment.description}")
        
        return reasoning
    
    def _generate_summary(self, candlestick: Dict, chanlun: Dict,
                         resonance: object, sentiment: object) -> str:
        """生成总体摘要"""
        parts = []
        
        # 形态识别
        pattern_count = candlestick.get('bullish_count', 0) + candlestick.get('bearish_count', 0)
        parts.append(f"识别出{pattern_count}个K线形态")
        
        # 缠论
        if chanlun.get('buy_points'):
            parts.append(f"缠论出现{chanlun['buy_points'][-1].bp_type.value}")
        
        # 共振
        parts.append(f"信号{resonance.resonance_level}")
        
        # 情绪
        parts.append(f"情绪{sentiment.level.value}")
        
        return "；".join(parts)
    
    def format_report_text(self, report: Dict) -> str:
        """
        格式化报告为文本
        
        Args:
            report: 报告数据
            
        Returns:
            格式化文本
        """
        lines = []
        
        # 标题
        stock_name = report['stock_info'].get('name', '未知')
        stock_code = report['stock_info'].get('code', '')
        lines.append(f"\n{'='*60}")
        lines.append(f"📊 交易形态识别和建议策略报告")
        lines.append(f"{'='*60}")
        lines.append(f"股票：{stock_name} ({stock_code})")
        lines.append(f"时间：{report['timestamp']}")
        lines.append(f"{'='*60}\n")
        
        # 一、K线形态识别
        lines.append(f"【一、K线形态识别】")
        candlestick = report['candlestick']
        lines.append(f"识别形态总数：{len(candlestick.get('patterns', []))}个")
        lines.append(f"看涨形态：{candlestick.get('bullish_count', 0)}个 | 看跌形态：{candlestick.get('bearish_count', 0)}个")
        
        if candlestick.get('top_bullish'):
            lines.append(f"\n主要看涨形态：")
            for p in candlestick['top_bullish'][:3]:
                lines.append(f"  ✅ {p.name_cn}（可靠性{p.reliability}/5，置信度{p.confidence:.0%}）")
                lines.append(f"     {p.description}")
        
        if candlestick.get('top_bearish'):
            lines.append(f"\n主要看跌形态：")
            for p in candlestick['top_bearish'][:3]:
                lines.append(f"  ❌ {p.name_cn}（可靠性{p.reliability}/5，置信度{p.confidence:.0%}）")
                lines.append(f"     {p.description}")
        
        lines.append(f"\n形态评分：看涨{candlestick.get('bullish_score', 0):.1f}分 vs 看跌{candlestick.get('bearish_score', 0):.1f}分")
        lines.append(f"信号方向：{candlestick.get('signal', '中性')}\n")
        
        # 二、缠论分析
        lines.append(f"【二、缠论分析】")
        chanlun = report['chanlun']
        lines.append(f"笔数量：{chanlun.get('bi_count', 0)} | 中枢数量：{chanlun.get('zhongshu_count', 0)}")
        lines.append(f"当前趋势：{chanlun.get('current_trend', '未知')}")
        
        nearest_zs = chanlun.get('nearest_zhongshu')
        if nearest_zs:
            lines.append(f"最近中枢区间：{nearest_zs['range']}（ZG:{nearest_zs['zg']}, ZD:{nearest_zs['zd']}）")
        
        if chanlun.get('buy_points'):
            lines.append(f"\n识别到买卖点：")
            for bp in chanlun['buy_points'][-3:]:
                emoji = "🔴" if "买" in bp.bp_type.value else "🟢"
                lines.append(f"  {emoji} {bp.bp_type.value} @ {bp.price:.2f}（置信度{bp.confidence:.0%}）")
        else:
            lines.append(f"\n暂无明确买卖点信号")
        lines.append()
        
        # 三、信号共振评分
        lines.append(f"【三、信号共振评分】")
        resonance = report['resonance']
        lines.append(f"综合评分：{resonance.total_score:+.1f}分（-100到+100）")
        lines.append(f"共振级别：{resonance.resonance_level}")
        lines.append(f"看涨得分：{resonance.bullish_score:.1f}分 | 看跌得分：{resonance.bearish_score:.1f}分")
        lines.append(f"信号数量：共{resonance.signal_count}个信号")
        
        if resonance.bullish_signals:
            lines.append(f"\n看涨信号（{len(resonance.bullish_signals)}个）：")
            for s in resonance.bullish_signals[:3]:
                lines.append(f"  📈 {s.signal_type.value}：{s.description}（强度{s.strength:.0%}）")
        
        if resonance.bearish_signals:
            lines.append(f"\n看跌信号（{len(resonance.bearish_signals)}个）：")
            for s in resonance.bearish_signals[:3]:
                lines.append(f"  📉 {s.signal_type.value}：{s.description}（强度{s.strength:.0%}）")
        lines.append()
        
        # 四、情绪指数
        lines.append(f"【四、市场情绪指数】")
        sentiment = report['sentiment']
        lines.append(f"情绪指数：{sentiment.index_value:.1f}/100")
        lines.append(f"情绪等级：{sentiment.level.value}")
        lines.append(f"情绪趋势：{sentiment.trend}")
        lines.append(f"交易信号：{sentiment.signal}")
        lines.append(f"\n指数构成：")
        for component, value in sentiment.components.items():
            lines.append(f"  • {component}：{value:.1f}分")
        lines.append(f"\n情绪解读：{sentiment.description}\n")
        
        # 五、策略建议
        lines.append(f"【五、策略建议】")
        strategy = report['strategy_advice']
        
        action_emoji = {
            '强烈买入': '🚀',
            '买入': '⬆️',
            '观望': '➡️',
            '卖出': '⬇️',
            '强烈卖出': '🔻'
        }
        emoji = action_emoji.get(strategy['primary_action'], '➡️')
        lines.append(f"主要操作：{emoji} {strategy['primary_action']}（置信度{strategy['confidence']:.0%}）")
        lines.append(f"风险等级：{strategy['risk_level']}")
        lines.append(f"仓位建议：{strategy['position_suggestion']}")
        
        if strategy['entry_points']:
            lines.append(f"\n建议买入点：")
            for ep in strategy['entry_points']:
                lines.append(f"  💰 {ep['type']} @ {ep['price']}（置信度{ep['confidence']:.0%}）")
        
        if strategy['exit_points']:
            lines.append(f"\n建议卖出点：")
            for ep in strategy['exit_points']:
                lines.append(f"  💸 {ep['type']} @ {ep['price']}（置信度{ep['confidence']:.0%}）")
        
        lines.append(f"\n推理逻辑：")
        for i, reason in enumerate(strategy['reasoning'], 1):
            lines.append(f"  {i}. {reason}")
        
        lines.append(f"\n{'='*60}")
        lines.append(f"总结：{report['summary']}")
        lines.append(f"{'='*60}\n")
        
        return '\n'.join(lines)


def generate_pattern_report(df: pd.DataFrame, stock_info: Dict = None) -> str:
    """
    生成交易形态报告的便捷函数
    
    Args:
        df: 价格数据
        stock_info: 股票信息
        
    Returns:
        格式化报告文本
    """
    generator = PatternAnalysisReport()
    report = generator.generate_report(df, stock_info)
    return generator.format_report_text(report)
