# -*- coding: utf-8 -*-
"""
决策仪表盘格式化模块 - 结构化输出模板
借鉴 daily_stock_analysis 项目的 AI 决策仪表盘设计
"""
from typing import Dict, List, Any
from datetime import datetime


class DecisionDashboard:
    """决策仪表盘生成器"""
    
    @staticmethod
    def generate_dashboard(data: Dict[str, Any]) -> str:
        """
        生成完整的决策仪表盘
        
        结构：
        1. 一句话核心结论
        2. 精确买卖点位
        3. 操作检查清单
        4. 四维分析详情
        """
        lines = []
        
        # ========== 头部 ==========
        lines.append(DecisionDashboard._generate_header(data))
        
        # ========== 1. 核心结论 ==========
        lines.append(DecisionDashboard._generate_core_conclusion(data))
        
        # ========== 2. 精确点位 ==========
        lines.append(DecisionDashboard._generate_price_levels(data))
        
        # ========== 3. 操作检查清单 ==========
        lines.append(DecisionDashboard._generate_checklist(data))
        
        # ========== 4. 四维分析摘要 ==========
        lines.append(DecisionDashboard._generate_four_dimension_summary(data))
        
        # ========== 5. 风险警示 ==========
        lines.append(DecisionDashboard._generate_risk_warnings(data))
        
        return '\n'.join(lines)
    
    @staticmethod
    def _generate_header(data: Dict) -> str:
        """生成报告头部"""
        stock_name = data.get('stock_name', '未知')
        code = data.get('code', '')
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║  📊 股票智能决策仪表盘 - {stock_name} ({code})                    ║
║  生成时间: {timestamp}                                          ║
╚══════════════════════════════════════════════════════════════════╝
"""
    
    @staticmethod
    def _generate_core_conclusion(data: Dict) -> str:
        """生成一句话核心结论"""
        suggestion = data.get('suggestion', {})
        action = suggestion.get('action', '观望')
        level = suggestion.get('level', '谨慎')
        total_score = suggestion.get('total_score', 50)
        
        # 根据评分生成核心结论
        if total_score >= 75:
            conclusion = f"🟢 【强烈看多】{action} - 多维度共振，趋势明确"
        elif total_score >= 60:
            conclusion = f"🟡 【谨慎看多】{action} - 机会大于风险，控制仓位"
        elif total_score >= 45:
            conclusion = f"⚪ 【中性观望】{action} - 信号混杂，等待明确"
        elif total_score >= 30:
            conclusion = f"🟠 【谨慎看空】{action} - 风险积聚，减仓观望"
        else:
            conclusion = f"🔴 【强烈看空】{action} - 趋势恶化，规避风险"
        
        fundamental_trend = suggestion.get('fundamental_trend', '中性')
        news_impact = suggestion.get('news_impact', '消息面中性')
        
        return f"""
┌─────────────────────────────────────────────────────────────────┐
│  💡 核心结论                                                     │
├─────────────────────────────────────────────────────────────────┤
│  {conclusion:<63}│
│                                                                  │
│  综合评分: {total_score}/100  |  基本面: {fundamental_trend}  |  消息面: {news_impact:<10}│
└─────────────────────────────────────────────────────────────────┘
"""
    
    @staticmethod
    def _generate_price_levels(data: Dict) -> str:
        """生成精确买卖点位"""
        quote = data.get('quote', {})
        suggestion = data.get('suggestion', {})
        
        current_price = quote.get('price', 0)
        target_price = suggestion.get('target_price', 0)
        stop_loss = suggestion.get('stop_loss', 0)
        position = suggestion.get('position', '10%')
        
        # 计算潜在收益和风险
        if current_price > 0:
            upside = round((target_price - current_price) / current_price * 100, 1)
            downside = round((current_price - stop_loss) / current_price * 100, 1)
            risk_reward = round(upside / downside, 2) if downside > 0 else 0
        else:
            upside = downside = risk_reward = 0
        
        return f"""
┌─────────────────────────────────────────────────────────────────┐
│  🎯 精确买卖点位                                                 │
├─────────────────────────────────────────────────────────────────┤
│  当前价格: ¥{current_price:<8}  建议仓位: {position:<10}                    │
│                                                                  │
│  🟢 买入区间: ¥{round(current_price * 0.98, 2):<7} - ¥{round(current_price * 1.02, 2):<7}                              │
│  🎯 目标价格: ¥{target_price:<8}  (潜在收益: +{upside}%)                      │
│  🛑 止损价格: ¥{stop_loss:<8}  (最大亏损: -{downside}%)                      │
│                                                                  │
│  盈亏比: 1:{risk_reward:<5} {'✅ 盈亏比合理' if risk_reward >= 2 else '⚠️ 盈亏比一般' if risk_reward >= 1.5 else '❌ 盈亏比不佳':<20}│
└─────────────────────────────────────────────────────────────────┘
"""
    
    @staticmethod
    def _generate_checklist(data: Dict) -> str:
        """生成操作检查清单"""
        checklist = []
        
        # 技术面检查
        tech = data.get('technical', {})
        trend = tech.get('trend', '')
        kdj_signal = tech.get('kdj_signal', '')
        rsi_signal = tech.get('rsi_signal', '')
        macd_signal = tech.get('macd_signal', '')
        
        checklist.append(('均线排列', '✅ 满足' if '上升' in trend else '⚠️ 注意' if '震荡' in trend else '❌ 不满足', 
                         f"MA5/MA20/MA60: {trend}"))
        
        checklist.append(('KDJ信号', '✅ 满足' if '金叉' in kdj_signal or '超卖' in kdj_signal else '⚠️ 注意' if '正常' in kdj_signal else '❌ 不满足',
                         f"KDJ: {kdj_signal}"))
        
        checklist.append(('RSI状态', '✅ 满足' if '超卖' in rsi_signal else '⚠️ 注意' if '正常' in rsi_signal else '❌ 不满足',
                         f"RSI: {rsi_signal}"))
        
        checklist.append(('MACD信号', '✅ 满足' if '多头' in macd_signal else '⚠️ 注意' if '盘整' in macd_signal else '❌ 不满足',
                         f"MACD: {macd_signal}"))
        
        # 基本面检查
        fundamental = data.get('fundamental', {})
        perf_trend = fundamental.get('performance_trend', {})
        overall_trend = perf_trend.get('overall_trend', '中性')
        
        checklist.append(('基本面趋势', '✅ 满足' if '向好' in overall_trend else '⚠️ 注意' if '中性' in overall_trend else '❌ 不满足',
                         f"基本面: {overall_trend}"))
        
        # 资金面检查
        money_flow = data.get('money_flow', {})
        main_flow = money_flow.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        
        checklist.append(('主力资金', '✅ 满足' if main_net > 0 else '❌ 不满足',
                         f"主力净流入: {main_net:.2f}亿"))
        
        # 消息面检查
        news = data.get('news', {})
        sentiment = news.get('sentiment', '中性')
        fund_impact = news.get('fundamental_impact', '中性')
        
        checklist.append(('消息情绪', '✅ 满足' if sentiment == '偏多' else '⚠️ 注意' if sentiment == '中性' else '❌ 不满足',
                         f"情绪: {sentiment}, 影响: {fund_impact}"))
        
        # 交易纪律检查
        quote = data.get('quote', {})
        pct_change = quote.get('pct_change', 0)
        
        checklist.append(('追涨风险', '✅ 满足' if pct_change < 5 else '⚠️ 注意' if pct_change < 7 else '❌ 不满足',
                         f"今日涨跌: {pct_change}% (乖离率检查)"))
        
        # 生成表格
        lines = ["\n┌─────────────────────────────────────────────────────────────────┐",
                 "│  ✅ 操作检查清单                                                 │",
                 "├──────────────────┬──────────┬──────────────────────────────────┤"]
        
        for item, status, detail in checklist:
            lines.append(f"│  {item:<14} │ {status:<8} │ {detail:<32} │")
        
        # 统计
        passed = sum(1 for _, s, _ in checklist if '✅' in s)
        warning = sum(1 for _, s, _ in checklist if '⚠️' in s)
        failed = sum(1 for _, s, _ in checklist if '❌' in s)
        
        lines.extend([
            "├──────────────────┴──────────┴──────────────────────────────────┤",
            f"│  统计: ✅ 满足 {passed}项  |  ⚠️ 注意 {warning}项  |  ❌ 不满足 {failed}项                    │",
            "└─────────────────────────────────────────────────────────────────┘"
        ])
        
        return '\n'.join(lines)
    
    @staticmethod
    def _generate_four_dimension_summary(data: Dict) -> str:
        """生成四维分析摘要"""
        lines = ["\n┌─────────────────────────────────────────────────────────────────┐",
                 "│  📊 四维分析摘要                                                 │",
                 "├─────────────────────────────────────────────────────────────────┤"]
        
        # 技术面
        tech = data.get('technical', {})
        tech_score = sum(tech.get('scores', {}).values()) if 'scores' in tech else 0
        lines.append(f"│  📈 技术面 (权重35%): 评分 {tech_score:+d}                                    │")
        lines.append(f"│      趋势: {tech.get('trend', 'N/A'):<10}  RSI: {tech.get('rsi', 'N/A'):<6}  KDJ: {tech.get('kdj_signal', 'N/A'):<8}        │")
        
        # 基本面
        fundamental = data.get('fundamental', {})
        fund_score = fundamental.get('score', 50)
        lines.append(f"│  💼 基本面 (权重35%): 评分 {fund_score}/100                                   │")
        
        perf = fundamental.get('performance_trend', {})
        reasons = perf.get('reasons', [])
        reason_str = reasons[0] if reasons else 'N/A'
        lines.append(f"│      趋势: {perf.get('overall_trend', 'N/A'):<10}  原因: {reason_str[:30]:<30}│")
        
        # 资金面
        money = data.get('money_flow', {})
        money_score = money.get('score', 50)
        main_flow = money.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        lines.append(f"│  💰 资金面 (权重15%): 评分 {money_score}/100                                   │")
        lines.append(f"│      主力净流入: {main_net:+.2f}亿                                              │")
        
        # 消息面
        news = data.get('news', {})
        sentiment = news.get('sentiment', '中性')
        sentiment_score = news.get('sentiment_score', 0)
        lines.append(f"│  📰 消息面 (权重15%): 情绪 {sentiment} (得分: {sentiment_score:+d})                              │")
        
        lines.append("└─────────────────────────────────────────────────────────────────┘")
        
        return '\n'.join(lines)
    
    @staticmethod
    def _generate_risk_warnings(data: Dict) -> str:
        """生成风险警示"""
        warnings = []
        
        # 检查各种风险
        quote = data.get('quote', {})
        if quote.get('pct_change', 0) > 7:
            warnings.append("⚠️ 今日涨幅过大(>7%)，谨防追高被套")
        
        tech = data.get('technical', {})
        if '超买' in tech.get('rsi_signal', '') or '超买' in tech.get('kdj_signal', ''):
            warnings.append("⚠️ 技术指标超买，短期回调风险")
        
        fundamental = data.get('fundamental', {})
        perf = fundamental.get('performance_trend', {})
        if '承压' in perf.get('overall_trend', ''):
            warnings.append("⚠️ 基本面承压，业绩存在下滑风险")
        
        news = data.get('news', {})
        if '利空' in news.get('fundamental_impact', ''):
            warnings.append("⚠️ 近期消息面偏空，注意利空影响")
        
        if not warnings:
            warnings.append("✅ 未发现明显风险信号")
        
        lines = ["\n┌─────────────────────────────────────────────────────────────────┐",
                 "│  ⚠️ 风险警示                                                     │",
                 "├─────────────────────────────────────────────────────────────────┤"]
        
        for warning in warnings:
            lines.append(f"│  {warning:<63}│")
        
        lines.extend([
            "├─────────────────────────────────────────────────────────────────┤",
            "│  📌 免责声明: 本分析仅供参考，不构成投资建议。股市有风险，投资需谨慎。    │",
            "└─────────────────────────────────────────────────────────────────┘"
        ])
        
        return '\n'.join(lines)


# 便捷函数
def format_dashboard(data: Dict[str, Any]) -> str:
    """便捷函数：格式化决策仪表盘"""
    return DecisionDashboard.generate_dashboard(data)


# ========== 新增：交易形态识别和建议策略板块 ==========

def generate_pattern_section(pattern_report: Dict) -> str:
    """
    生成交易形态识别和建议策略板块
    
    Args:
        pattern_report: 形态分析报告数据
        
    Returns:
        格式化文本
    """
    lines = []
    
    lines.append("\n╔══════════════════════════════════════════════════════════════════╗")
    lines.append("║  📐 交易形态识别和建议策略                                       ║")
    lines.append("╚══════════════════════════════════════════════════════════════════╝")
    
    # 一、K线形态识别
    lines.append("\n┌─────────────────────────────────────────────────────────────────┐")
    lines.append("│  【一、K线形态识别】                                             │")
    lines.append("├─────────────────────────────────────────────────────────────────┤")
    
    candlestick = pattern_report.get('candlestick', {})
    pattern_count = len(candlestick.get('patterns', []))
    bullish_count = candlestick.get('bullish_count', 0)
    bearish_count = candlestick.get('bearish_count', 0)
    
    lines.append(f"│  识别形态总数：{pattern_count}个  看涨：{bullish_count}个  看跌：{bearish_count}个{' '*28}│")
    
    # 主要看涨形态
    top_bullish = candlestick.get('top_bullish', [])
    if top_bullish:
        lines.append("│                                                                  │")
        lines.append("│  🟢 主要看涨形态：                                               │")
        for p in top_bullish[:2]:
            lines.append(f"│     • {p.name_cn:<10} 可靠性{p.reliability}/5  置信度{p.confidence:.0%}{' '*23}│")
    
    # 主要看跌形态
    top_bearish = candlestick.get('top_bearish', [])
    if top_bearish:
        lines.append("│                                                                  │")
        lines.append("│  🔴 主要看跌形态：                                               │")
        for p in top_bearish[:2]:
            lines.append(f"│     • {p.name_cn:<10} 可靠性{p.reliability}/5  置信度{p.confidence:.0%}{' '*23}│")
    
    # 形态评分
    bullish_score = candlestick.get('bullish_score', 0)
    bearish_score = candlestick.get('bearish_score', 0)
    signal = candlestick.get('signal', '中性')
    lines.append("│                                                                  │")
    lines.append(f"│  形态评分：看涨{bullish_score:.1f}分 vs 看跌{bearish_score:.1f}分  →  {signal}{' '*20}│")
    lines.append("└─────────────────────────────────────────────────────────────────┘")
    
    # 二、缠论买卖点
    lines.append("\n┌─────────────────────────────────────────────────────────────────┐")
    lines.append("│  【二、缠论买卖点】                                              │")
    lines.append("├─────────────────────────────────────────────────────────────────┤")
    
    chanlun = pattern_report.get('chanlun', {})
    bi_count = chanlun.get('bi_count', 0)
    zhongshu_count = chanlun.get('zhongshu_count', 0)
    current_trend = chanlun.get('current_trend', '未知')
    
    lines.append(f"│  笔数量：{bi_count}  中枢数量：{zhongshu_count}  当前趋势：{current_trend}{' '*35}│")
    
    # 最近中枢
    nearest_zs = chanlun.get('nearest_zhongshu')
    if nearest_zs:
        lines.append("│                                                                  │")
        lines.append(f"│  📊 最近中枢区间：{nearest_zs['range']}（ZG:{nearest_zs['zg']}, ZD:{nearest_zs['zd']}）{' '*12}│")
    
    # 买卖点
    buy_points = chanlun.get('buy_points', [])
    if buy_points:
        lines.append("│                                                                  │")
        lines.append("│  🎯 识别到买卖点：                                               │")
        for bp in buy_points[-2:]:
            emoji = "🔴" if "买" in bp.bp_type.value else "🟢"
            lines.append(f"│     {emoji} {bp.bp_type.value} @ {bp.price:.2f}  置信度{bp.confidence:.0%}{' '*32}│")
    else:
        lines.append("│                                                                  │")
        lines.append("│  ⚪ 暂无明确买卖点信号                                           │")
    
    lines.append("└─────────────────────────────────────────────────────────────────┘")
    
    # 三、信号共振评分
    lines.append("\n┌─────────────────────────────────────────────────────────────────┐")
    lines.append("│  【三、信号共振评分】                                            │")
    lines.append("├─────────────────────────────────────────────────────────────────┤")
    
    resonance = pattern_report.get('resonance', {})
    total_score = resonance.get('total_score', 0)
    resonance_level = resonance.get('resonance_level', '无共振')
    bullish_score = resonance.get('bullish_score', 0)
    bearish_score = resonance.get('bearish_score', 0)
    signal_count = resonance.get('signal_count', 0)
    
    # 共振级别颜色
    if '强' in resonance_level:
        level_emoji = "🟢"
    elif '中等' in resonance_level:
        level_emoji = "🟡"
    elif '弱' in resonance_level:
        level_emoji = "⚪"
    else:
        level_emoji = "⚫"
    
    lines.append(f"│  综合评分：{total_score:+.1f}分/100  {level_emoji} {resonance_level}{' '*35}│")
    lines.append(f"│  看涨得分：{bullish_score:.1f}分  |  看跌得分：{bearish_score:.1f}分  |  信号总数：{signal_count}个{' '*20}│")
    
    # 看涨信号
    bullish_signals = resonance.get('bullish_signals', [])
    if bullish_signals:
        lines.append("│                                                                  │")
        lines.append("│  📈 看涨信号：                                                   │")
        for s in bullish_signals[:2]:
            lines.append(f"│     • {s.signal_type.value}：{s.description[:35]:<35}│")
    
    # 看跌信号
    bearish_signals = resonance.get('bearish_signals', [])
    if bearish_signals:
        lines.append("│                                                                  │")
        lines.append("│  📉 看跌信号：                                                   │")
        for s in bearish_signals[:2]:
            lines.append(f"│     • {s.signal_type.value}：{s.description[:35]:<35}│")
    
    lines.append("└─────────────────────────────────────────────────────────────────┘")
    
    # 四、情绪指数
    lines.append("\n┌─────────────────────────────────────────────────────────────────┐")
    lines.append("│  【四、市场情绪指数】                                            │")
    lines.append("├─────────────────────────────────────────────────────────────────┤")
    
    sentiment = pattern_report.get('sentiment', {})
    index_value = sentiment.get('index_value', 50)
    level = sentiment.get('level', {})
    level_name = level.value if hasattr(level, 'value') else str(level)
    trend = sentiment.get('trend', '平稳')
    signal = sentiment.get('signal', '观望')
    
    # 情绪等级颜色
    if '极度恐慌' in level_name:
        level_emoji = "🔴"
    elif '恐慌' in level_name:
        level_emoji = "🟠"
    elif '贪婪' in level_name:
        level_emoji = "🟢"
    elif '极度贪婪' in level_name:
        level_emoji = "🔵"
    else:
        level_emoji = "⚪"
    
    lines.append(f"│  情绪指数：{index_value:.1f}/100  {level_emoji} {level_name}  趋势：{trend}{' '*25}│")
    lines.append(f"│  交易信号：{signal}{' '*52}│")
    
    # 指数构成
    components = sentiment.get('components', {})
    if components:
        lines.append("│                                                                  │")
        lines.append("│  指数构成：                                                      │")
        component_names = {
            'price_volatility': '价格波动',
            'volume_sentiment': '成交量',
            'momentum_sentiment': '涨跌动量',
            'technical_sentiment': '技术指标'
        }
        for key, value in components.items():
            name = component_names.get(key, key)
            lines.append(f"│     • {name}：{value:.1f}分{' '*45}│")
    
    lines.append("└─────────────────────────────────────────────────────────────────┘")
    
    # 五、策略建议
    lines.append("\n┌─────────────────────────────────────────────────────────────────┐")
    lines.append("│  【五、策略建议】                                                │")
    lines.append("├─────────────────────────────────────────────────────────────────┤")
    
    strategy = pattern_report.get('strategy_advice', {})
    primary_action = strategy.get('primary_action', '观望')
    confidence = strategy.get('confidence', 0)
    risk_level = strategy.get('risk_level', '中等')
    position = strategy.get('position_suggestion', '')
    
    # 操作颜色
    action_colors = {
        '强烈买入': '🚀',
        '买入': '⬆️',
        '观望': '➡️',
        '卖出': '⬇️',
        '强烈卖出': '🔻'
    }
    action_emoji = action_colors.get(primary_action, '➡️')
    
    lines.append(f"│  主要操作：{action_emoji} {primary_action}{' '*10}置信度：{confidence:.0%}{' '*20}│")
    lines.append(f"│  风险等级：{risk_level}{' '*50}│")
    lines.append(f"│  仓位建议：{position}{' '*45}│")
    
    # 买卖点
    entry_points = strategy.get('entry_points', [])
    if entry_points:
        lines.append("│                                                                  │")
        lines.append("│  💰 建议买入点：                                                 │")
        for ep in entry_points[:2]:
            lines.append(f"│     • {ep['type']} @ {ep['price']}（置信度{ep['confidence']:.0%}）{' '*30}│")
    
    exit_points = strategy.get('exit_points', [])
    if exit_points:
        lines.append("│                                                                  │")
        lines.append("│  💸 建议卖出点：                                                 │")
        for ep in exit_points[:2]:
            lines.append(f"│     • {ep['type']} @ {ep['price']}（置信度{ep['confidence']:.0%}）{' '*30}│")
    
    # 推理逻辑
    reasoning = strategy.get('reasoning', [])
    if reasoning:
        lines.append("│                                                                  │")
        lines.append("│  📝 推理逻辑：                                                   │")
        for i, reason in enumerate(reasoning[:3], 1):
            truncated = reason[:55]
            lines.append(f"│     {i}. {truncated:<55}│")
    
    lines.append("└─────────────────────────────────────────────────────────────────┘")
    
    return '\n'.join(lines)


def generate_full_dashboard_with_patterns(data: Dict, pattern_report: Dict) -> str:
    """
    生成包含交易形态识别的完整仪表盘
    
    Args:
        data: 原始仪表盘数据
        pattern_report: 形态分析报告
        
    Returns:
        完整仪表盘文本
    """
    # 生成基础仪表盘
    base_dashboard = DecisionDashboard.generate_dashboard(data)
    
    # 生成形态识别板块
    pattern_section = generate_pattern_section(pattern_report)
    
    # 合并
    return base_dashboard + '\n' + pattern_section
