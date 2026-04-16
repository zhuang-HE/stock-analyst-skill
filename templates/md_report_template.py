# -*- coding: utf-8 -*-
"""
Markdown格式股票分析报告模板
在保留原有MD格式和内容的基础上，增加形态面分析
"""
from typing import Dict, List, Any
from datetime import datetime


class MDReportGenerator:
    """Markdown报告生成器"""
    
    @staticmethod
    def generate_report(data: Dict[str, Any], pattern_data: Dict[str, Any] = None) -> str:
        """
        生成完整的Markdown格式分析报告
        
        Args:
            data: 基础分析数据（四维分析）
            pattern_data: 形态面分析数据（可选）
        """
        lines = []
        
        # ========== 报告头部 ==========
        lines.append(MDReportGenerator._generate_header(data))
        
        # ========== 1. 执行摘要 ==========
        lines.append(MDReportGenerator._generate_executive_summary(data))
        
        # ========== 2. 行情概览 ==========
        lines.append(MDReportGenerator._generate_quote_section(data))
        
        # ========== 3. 技术面分析 ==========
        lines.append(MDReportGenerator._generate_technical_section(data))
        
        # ========== 4. 基本面分析 ==========
        lines.append(MDReportGenerator._generate_fundamental_section(data))
        
        # ========== 5. 资金面分析 ==========
        lines.append(MDReportGenerator._generate_moneyflow_section(data))
        
        # ========== 6. 消息面分析 ==========
        lines.append(MDReportGenerator._generate_news_section(data))
        
        # ========== 7. 形态面分析（新增）==========
        if pattern_data:
            lines.append(MDReportGenerator._generate_pattern_section(pattern_data))
        
        # ========== 8. 综合建议 ==========
        lines.append(MDReportGenerator._generate_suggestion_section(data, pattern_data))
        
        # ========== 9. 风险提示 ==========
        lines.append(MDReportGenerator._generate_risk_section(data))
        
        # ========== 10. 免责声明 ==========
        lines.append(MDReportGenerator._generate_disclaimer())
        
        return '\n'.join(lines)
    
    @staticmethod
    def _generate_header(data: Dict) -> str:
        """生成报告头部"""
        stock_name = data.get('stock_name', '未知')
        code = data.get('code', '')
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return f"""# 📊 {stock_name} ({code}) 股票分析报告

> **报告生成时间**: {timestamp}  
> **分析维度**: 技术面 / 基本面 / 资金面 / 消息面 / **形态面** (V3.1)

---

"""
    
    @staticmethod
    def _generate_executive_summary(data: Dict) -> str:
        """生成执行摘要"""
        suggestion = data.get('suggestion', {})
        action = suggestion.get('action', '观望')
        total_score = suggestion.get('total_score', 50)
        level = suggestion.get('level', '谨慎')
        
        quote = data.get('quote', {})
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        
        # 根据评分确定评级
        if total_score >= 75:
            rating = "🟢 **强烈买入**"
            summary = "多维度共振，趋势明确，建议积极配置"
        elif total_score >= 60:
            rating = "🟡 **买入**"
            summary = "机会大于风险，建议适量参与"
        elif total_score >= 45:
            rating = "⚪ **观望**"
            summary = "信号混杂，建议等待更明确的机会"
        elif total_score >= 30:
            rating = "🟠 **谨慎**"
            summary = "风险积聚，建议减仓观望"
        else:
            rating = "🔴 **卖出**"
            summary = "趋势恶化，建议规避风险"
        
        return f"""## 📋 执行摘要

| 项目 | 内容 |
|:-----|:-----|
| **当前股价** | ¥{price} ({pct_change:+.2f}%) |
| **综合评级** | {rating} |
| **综合评分** | {total_score}/100 |
| **操作建议** | {action} |
| **风险等级** | {level} |

**核心观点**: {summary}

---

"""
    
    @staticmethod
    def _generate_quote_section(data: Dict) -> str:
        """生成行情概览"""
        quote = data.get('quote', {})
        
        if not quote or 'error' in quote:
            return "## 📈 行情概览\n\n> 暂无行情数据\n\n---\n\n"
        
        return f"""## 📈 行情概览

### 实时行情

| 指标 | 数值 | 指标 | 数值 |
|:-----|:-----|:-----|:-----|
| **最新价** | ¥{quote.get('price', 'N/A')} | **涨跌幅** | {quote.get('pct_change', 'N/A')}% |
| **开盘价** | ¥{quote.get('open', 'N/A')} | **最高价** | ¥{quote.get('high', 'N/A')} |
| **最低价** | ¥{quote.get('low', 'N/A')} | **成交量** | {quote.get('volume', 'N/A'):,} |
| **成交额** | {quote.get('amount', 'N/A')}亿 | **换手率** | {quote.get('turnover', 'N/A')}% |

---

"""
    
    @staticmethod
    def _generate_technical_section(data: Dict) -> str:
        """生成技术面分析"""
        tech = data.get('technical', {})
        
        if not tech or 'error' in tech:
            return "## 📊 技术面分析\n\n> 暂无技术分析数据\n\n---\n\n"
        
        # 均线系统
        ma_section = f"""
### 均线系统

| 均线 | 价格 | 状态 |
|:-----|:-----|:-----|
| MA5 | ¥{tech.get('ma5', 'N/A')} | {'✅ 上方' if tech.get('price_above_ma5') else '❌ 下方'} |
| MA10 | ¥{tech.get('ma10', 'N/A')} | - |
| MA20 | ¥{tech.get('ma20', 'N/A')} | {'✅ 上方' if tech.get('price_above_ma20') else '❌ 下方'} |
| MA60 | ¥{tech.get('ma60', 'N/A')} | {'✅ 上方' if tech.get('price_above_ma60') else '❌ 下方'} |

**趋势判断**: {tech.get('trend', 'N/A')}
"""
        
        # 技术指标
        indicator_section = f"""
### 技术指标

| 指标 | 数值 | 信号 |
|:-----|:-----|:-----|
| **RSI(14)** | {tech.get('rsi', 'N/A')} | {tech.get('rsi_signal', 'N/A')} |
| **KDJ-K** | {tech.get('k', 'N/A')} | {tech.get('kdj_signal', 'N/A')} |
| **KDJ-D** | {tech.get('d', 'N/A')} | - |
| **KDJ-J** | {tech.get('j', 'N/A')} | - |
| **MACD** | {tech.get('macd', 'N/A')} | {tech.get('macd_signal', 'N/A')} |
| **柱状图** | {tech.get('histogram', 'N/A')} | - |
"""
        
        # 评分
        scores = tech.get('scores', {})
        score_section = ""
        if scores:
            score_section = f"""
### 技术评分

| 维度 | 得分 | 说明 |
|:-----|:-----|:-----|
| 趋势 | {scores.get('trend', 0):+d} | {tech.get('trend', 'N/A')} |
| KDJ | {scores.get('kdj', 0):+d} | {tech.get('kdj_signal', 'N/A')} |
| RSI | {scores.get('rsi', 0):+d} | {tech.get('rsi_signal', 'N/A')} |
| MACD | {scores.get('macd', 0):+d} | {tech.get('macd_signal', 'N/A')} |
"""
        
        return f"""## 📊 技术面分析

{ma_section}

{indicator_section}
{score_section}

---

"""
    
    @staticmethod
    def _generate_fundamental_section(data: Dict) -> str:
        """生成基本面分析"""
        fundamental = data.get('fundamental', {})
        
        if not fundamental:
            return "## 💼 基本面分析\n\n> 暂无基本面数据\n\n---\n\n"
        
        sections = []
        
        # 财务数据
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        if latest:
            sections.append(f"""
### 财务数据（最近报告期: {latest.get('report_date', 'N/A')}）

| 指标 | 数值 | 指标 | 数值 |
|:-----|:-----|:-----|:-----|
| **净利润同比** | {latest.get('net_profit_yoy', 'N/A')} | **营收同比** | {latest.get('revenue_yoy', 'N/A')} |
| **ROE** | {latest.get('roe', 'N/A')} | **毛利率** | {latest.get('gross_margin', 'N/A')} |
| **净利率** | {latest.get('net_margin', 'N/A')} | **资产负债率** | {latest.get('debt_ratio', 'N/A')} |
| **每股收益** | {latest.get('eps', 'N/A')} | **每股现金流** | {latest.get('ocf_ps', 'N/A')} |
""")
        
        # 估值分析
        val = fundamental.get('valuation', {})
        if val and 'error' not in val:
            sections.append(f"""
### 估值分析

| 指标 | 数值 | 评价 |
|:-----|:-----|:-----|
| **近一年涨跌幅** | {val.get('近一年涨跌幅', 'N/A')}% | - |
| **年化波动率** | {val.get('年化波动率', 'N/A')}% | - |
| **PE(动态)** | {val.get('PE(动态)', 'N/A')} | {val.get('PE评价', 'N/A')} |
| **PB** | {val.get('PB', 'N/A')} | {val.get('PB评价', 'N/A')} |
| **价格历史分位数** | {val.get('价格历史分位数', 'N/A')} | - |
| **60日支撑位** | ¥{val.get('60日支撑位', 'N/A')} | - |
| **60日压力位** | ¥{val.get('60日压力位', 'N/A')} | - |
""")
        
        # 业绩趋势
        perf = fundamental.get('performance_trend', {})
        if perf:
            reasons = perf.get('reasons', [])
            reason_text = '；'.join(reasons[:3]) if reasons else 'N/A'
            sections.append(f"""
### 业绩趋势

| 维度 | 判断 |
|:-----|:-----|
| **整体趋势** | {perf.get('overall_trend', 'N/A')} |
| **财务趋势** | {perf.get('financial_trend', 'N/A')} |
| **估值趋势** | {perf.get('valuation_trend', 'N/A')} |
| **预测趋势** | {perf.get('forecast_trend', 'N/A')} |

**主要依据**: {reason_text}
""")
        
        # 基本面评分
        score = fundamental.get('score', 50)
        score_reasons = fundamental.get('reasons', [])
        if score_reasons:
            sections.append(f"""
### 基本面评分

**综合评分**: {score}/100

**评分依据**:
{chr(10).join(['- ' + r for r in score_reasons[:5]])}
""")
        
        content = '\n'.join(sections) if sections else '> 暂无详细基本面数据'
        
        return f"""## 💼 基本面分析

{content}

---

"""
    
    @staticmethod
    def _generate_moneyflow_section(data: Dict) -> str:
        """生成资金面分析"""
        money = data.get('money_flow', {})
        
        if not money or 'error' in money:
            return "## 💰 资金面分析\n\n> 暂无资金面数据\n\n---\n\n"
        
        main_flow = money.get('main_flow', {})
        
        return f"""## 💰 资金面分析

### 主力资金流向

| 指标 | 数值 |
|:-----|:-----|
| **日期** | {main_flow.get('date', 'N/A')} |
| **主力净流入** | {main_flow.get('main_net', 0):+.2f}亿 |
| **主力净流入占比** | {main_flow.get('main_pct', 0):.2f}% |
| **散户净流入** | {main_flow.get('retail_net', 0):+.2f}亿 |

### 资金评分

**资金面评分**: {money.get('score', 50)}/100

{'✅ 主力资金净流入，资金面积极' if main_flow.get('main_net', 0) > 0 else '❌ 主力资金净流出，资金面谨慎'}

---

"""
    
    @staticmethod
    def _generate_news_section(data: Dict) -> str:
        """生成消息面分析"""
        news = data.get('news', {})
        
        if not news or 'error' in news:
            return "## 📰 消息面分析\n\n> 暂无消息面数据\n\n---\n\n"
        
        # 情感分析
        sentiment = news.get('sentiment', '中性')
        sentiment_score = news.get('sentiment_score', 0)
        fund_impact = news.get('fundamental_impact', '中性')
        
        # 影响分析
        impacts = news.get('impact_on_fundamentals', [])
        impact_table = ""
        if impacts:
            impact_rows = []
            for imp in impacts[:5]:
                emoji = "✅" if imp.get('impact') == '正面' else "❌" if imp.get('impact') == '负面' else "⚪"
                impact_rows.append(f"| {imp.get('area', 'N/A')} | {emoji} {imp.get('impact', 'N/A')} | {imp.get('detail', 'N/A')} |")
            impact_table = "\n".join(impact_rows)
        
        # 最新新闻
        items = news.get('items', [])
        news_list = ""
        if items:
            news_items = []
            for item in items[:3]:
                title = item.get('title', 'N/A')
                date = item.get('date', 'N/A')
                news_items.append(f"- **{date}**: {title}")
            news_list = "\n".join(news_items)
        
        return f"""## 📰 消息面分析

### 情感分析

| 指标 | 内容 |
|:-----|:-----|
| **情感倾向** | {sentiment} (得分: {sentiment_score:+d}) |
| **对基本面影响** | {fund_impact} |

### 基本面影响分析

| 领域 | 影响 | 说明 |
|:-----|:-----|:-----|
{impact_table if impact_table else '| - | - | - |'}

### 最新新闻

{news_list if news_list else '> 暂无新闻'}

---

"""
    
    @staticmethod
    def _generate_pattern_section(pattern_data: Dict) -> str:
        """
        生成形态面分析（新增）
        
        包含：
        1. 形态识别结果（名称、形态类型）
        2. 买卖点及说明
        3. 信号共振评分
        4. 市场情绪评分
        """
        if not pattern_data:
            return ""
        
        sections = []
        
        # 1. K线形态识别
        candlestick = pattern_data.get('candlestick', {})
        if candlestick:
            patterns = candlestick.get('patterns', [])
            bullish_count = candlestick.get('bullish_count', 0)
            bearish_count = candlestick.get('bearish_count', 0)
            
            # 形态列表
            pattern_rows = []
            for p in patterns[:5]:
                emoji = "🟢" if p.get('type') == 'bullish' else "🔴" if p.get('type') == 'bearish' else "⚪"
                pattern_rows.append(
                    f"| {emoji} {p.get('name_cn', 'N/A')} | "
                    f"{p.get('type_cn', 'N/A')} | "
                    f"{'⭐' * p.get('reliability', 0)} | "
                    f"{p.get('confidence', 0):.0%} |"
                )
            
            sections.append(f"""
### 1. K线形态识别

**形态统计**: 共识别 {len(patterns)} 个形态 | 🟢 看涨 {bullish_count} 个 | 🔴 看跌 {bearish_count} 个

| 形态名称 | 类型 | 可靠性 | 置信度 |
|:---------|:-----|:-------|:-------|
{chr(10).join(pattern_rows) if pattern_rows else '| - | - | - | - |'}

**形态信号**: {candlestick.get('signal', '中性')}  
**看涨得分**: {candlestick.get('bullish_score', 0):.1f}  
**看跌得分**: {candlestick.get('bearish_score', 0):.1f}
""")
        
        # 2. 缠论买卖点
        chanlun = pattern_data.get('chanlun', {})
        if chanlun:
            buy_points = chanlun.get('buy_points', [])
            sell_points = chanlun.get('sell_points', [])
            
            # 买卖点列表
            bp_rows = []
            for bp in buy_points[-3:]:
                bp_rows.append(f"| 🎯 {bp.get('type', 'N/A')} | {bp.get('price', 0):.2f} | {bp.get('confidence', 0):.0%} | {bp.get('description', 'N/A')[:20]}... |")
            for sp in sell_points[-3:]:
                bp_rows.append(f"| 🔻 {sp.get('type', 'N/A')} | {sp.get('price', 0):.2f} | {sp.get('confidence', 0):.0%} | {sp.get('description', 'N/A')[:20]}... |")
            
            # 中枢信息
            nearest_zs = chanlun.get('nearest_zhongshu', {})
            zs_info = f"""
**最近中枢**:
- 区间: {nearest_zs.get('range', 'N/A')}
- ZG (中枢高点): {nearest_zs.get('zg', 'N/A')}
- ZD (中枢低点): {nearest_zs.get('zd', 'N/A')}
""" if nearest_zs else ""
            
            sections.append(f"""
### 2. 缠论买卖点

**当前状态**:
- 笔数量: {chanlun.get('bi_count', 0)}
- 中枢数量: {chanlun.get('zhongshu_count', 0)}
- 当前趋势: {chanlun.get('current_trend', 'N/A')}
{zs_info}
**识别买卖点**:

| 类型 | 价格 | 置信度 | 说明 |
|:-----|:-----|:-------|:-----|
{chr(10).join(bp_rows) if bp_rows else '| - | - | - | - |'}
""")
        
        # 3. 信号共振评分
        resonance = pattern_data.get('resonance', {})
        if resonance:
            total_score = resonance.get('total_score', 0)
            level = resonance.get('resonance_level', '无共振')
            
            # 评分详情
            breakdown = resonance.get('breakdown', {})
            breakdown_rows = []
            for dimension, score in breakdown.items():
                breakdown_rows.append(f"| {dimension} | {score:+.1f}分 |")
            
            # 共振级别emoji
            level_emoji = "🟢" if "强" in level else "🟡" if "中等" in level else "⚪"
            
            sections.append(f"""
### 3. 信号共振评分

**综合评分**: {total_score:+.1f}/100 {level_emoji} **{level}**

| 维度 | 得分 |
|:-----|:-----|
{chr(10).join(breakdown_rows) if breakdown_rows else '| - | - |'}

**看涨得分**: {resonance.get('bullish_score', 0):.1f}  
**看跌得分**: {resonance.get('bearish_score', 0):.1f}  
**信号总数**: {resonance.get('signal_count', 0)} 个

**看涨信号**:
{chr(10).join(['- ' + s.get('description', 'N/A') for s in resonance.get('bullish_signals', [])[:3]]) if resonance.get('bullish_signals') else '- 暂无'}

**看跌信号**:
{chr(10).join(['- ' + s.get('description', 'N/A') for s in resonance.get('bearish_signals', [])[:3]]) if resonance.get('bearish_signals') else '- 暂无'}
""")
        
        # 4. 市场情绪评分
        sentiment = pattern_data.get('sentiment', {})
        if sentiment:
            index_value = sentiment.get('index_value', 50)
            level = sentiment.get('level', {})
            level_name = level.get('name', '中性') if isinstance(level, dict) else str(level)
            trend = sentiment.get('trend', '平稳')
            signal = sentiment.get('signal', '观望')
            
            # 等级emoji
            if '极度恐慌' in level_name:
                level_emoji = "🔴"
            elif '恐慌' in level_name:
                level_emoji = "🟠"
            elif '极度贪婪' in level_name:
                level_emoji = "🔵"
            elif '贪婪' in level_name:
                level_emoji = "🟢"
            else:
                level_emoji = "⚪"
            
            # 指数构成
            components = sentiment.get('components', {})
            comp_rows = []
            comp_names = {
                'price_volatility': '价格波动',
                'volume_sentiment': '成交量情绪',
                'momentum_sentiment': '涨跌动量',
                'technical_sentiment': '技术指标'
            }
            for key, value in components.items():
                comp_rows.append(f"| {comp_names.get(key, key)} | {value:.1f}分 |")
            
            sections.append(f"""
### 4. 市场情绪评分（贪婪恐慌指数）

**情绪指数**: {index_value:.1f}/100 {level_emoji} **{level_name}**

| 指标 | 数值 |
|:-----|:-----|
| **情绪等级** | {level_name} |
| **趋势** | {trend} |
| **交易信号** | {signal} |

**指数构成**:

| 因子 | 得分 |
|:-----|:-----|
{chr(10).join(comp_rows) if comp_rows else '| - | - |'}

**情绪解读**: 
{sentiment.get('description', '市场情绪处于正常区间，建议按常规策略操作。')}
""")
        
        content = '\n'.join(sections) if sections else '> 暂无形态面数据'
        
        return f"""## 📐 形态面分析（V3.1 新增）

{content}

---

"""
    
    @staticmethod
    def _generate_suggestion_section(data: Dict, pattern_data: Dict = None) -> str:
        """生成综合建议"""
        suggestion = data.get('suggestion', {})
        
        action = suggestion.get('action', '观望')
        total_score = suggestion.get('total_score', 50)
        target_price = suggestion.get('target_price', 0)
        stop_loss = suggestion.get('stop_loss', 0)
        position = suggestion.get('position', '10%')
        
        # 形态面建议
        pattern_suggestion = ""
        if pattern_data:
            strategy = pattern_data.get('strategy_advice', {})
            if strategy:
                primary_action = strategy.get('primary_action', '')
                confidence = strategy.get('confidence', 0)
                risk_level = strategy.get('risk_level', '中等')
                
                pattern_suggestion = f"""
### 形态面策略建议

| 项目 | 内容 |
|:-----|:-----|
| **形态操作** | {primary_action} |
| **形态置信度** | {confidence:.0%} |
| **形态风险** | {risk_level} |

**形态推理**:
{chr(10).join(['- ' + r for r in strategy.get('reasoning', [])[:3]]) if strategy.get('reasoning') else '- 基于当前形态信号综合判断'}
"""
        
        # 评分权重说明
        breakdown = suggestion.get('score_breakdown', {})
        weight_info = ""
        if breakdown:
            weight_info = f"""
### 评分权重

| 维度 | 权重 |
|:-----|:-----|
| 技术面 | {breakdown.get('tech_weight', '35%')} |
| 基本面 | {breakdown.get('fundamental_weight', '35%')} |
| 资金面 | {breakdown.get('money_flow_weight', '15%')} |
| 消息面 | {breakdown.get('news_sentiment_weight', '15%')} |
| **形态面** | **新增** |
"""
        
        return f"""## 🎯 综合建议

### 操作建议

| 项目 | 内容 |
|:-----|:-----|
| **综合评分** | {total_score}/100 |
| **操作建议** | {action} |
| **目标价格** | ¥{target_price} |
| **止损价格** | ¥{stop_loss} |
| **建议仓位** | {position} |

{pattern_suggestion}
{weight_info}

---

"""
    
    @staticmethod
    def _generate_risk_section(data: Dict) -> str:
        """生成风险提示"""
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
        
        warning_list = '\n'.join([f"- {w}" for w in warnings])
        
        return f"""## ⚠️ 风险提示

{warning_list}

---

"""
    
    @staticmethod
    def _generate_disclaimer() -> str:
        """生成免责声明"""
        return """## 📌 免责声明

> **本报告仅供参考，不构成投资建议。**
> 
> - 所有分析结果基于历史数据，不保证未来收益
> - 信号共振评分和情绪指数仅供参考，不构成买卖依据
> - 缠论买卖点识别为算法自动计算，可能存在误差
> - 请结合自身风险承受能力谨慎决策
> 
> **股市有风险，投资需谨慎。**

---

*报告由 Stock Analyst Skill V3.1 自动生成*
"""


# 便捷函数
def generate_md_report(data: Dict[str, Any], pattern_data: Dict[str, Any] = None) -> str:
    """便捷函数：生成Markdown格式报告"""
    return MDReportGenerator.generate_report(data, pattern_data)


# 测试代码
if __name__ == '__main__':
    # 测试数据
    test_data = {
        'stock_name': '测试股票',
        'code': '000001',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'quote': {
            'price': 45.65,
            'pct_change': -2.02,
            'open': 46.50,
            'high': 46.80,
            'low': 45.20,
            'volume': 39554476,
            'amount': 18.05,
            'turnover': 2.15
        },
        'technical': {
            'ma5': 46.20,
            'ma10': 46.50,
            'ma20': 45.80,
            'ma60': 44.20,
            'price_above_ma5': False,
            'price_above_ma20': True,
            'price_above_ma60': True,
            'rsi': 54.59,
            'rsi_signal': '正常',
            'k': 45.20,
            'd': 48.30,
            'j': 39.00,
            'kdj_signal': '死叉',
            'macd': 0.15,
            'macd_signal': '多头',
            'histogram': 0.05,
            'trend': '震荡偏强',
            'scores': {
                'trend': 10,
                'kdj': -5,
                'rsi': 0,
                'macd': 10
            }
        },
        'fundamental': {
            'score': 65,
            'reasons': ['ROE良好(18%)', '净利润稳健增长(15%)', '估值合理'],
            'financial': {
                'latest': {
                    'report_date': '2024-09-30',
                    'net_profit_yoy': '15.2%',
                    'revenue_yoy': '12.5%',
                    'roe': '18.5%',
                    'gross_margin': '35.2%',
                    'net_margin': '18.5%',
                    'debt_ratio': '45.2%',
                    'eps': '2.35',
                    'ocf_ps': '2.80'
                }
            },
            'valuation': {
                '近一年涨跌幅': 25.5,
                '年化波动率': 32.5,
                'PE(动态)': 19.4,
                'PE评价': '合理',
                'PB': 2.8,
                'PB评价': '合理',
                '价格历史分位数': '65%',
                '60日支撑位': 42.50,
                '60日压力位': 48.20
            },
            'performance_trend': {
                'overall_trend': '基本面向好',
                'financial_trend': '向好',
                'valuation_trend': '合理',
                'forecast_trend': '预期平稳',
                'reasons': ['营收持续增长', '利润稳健增长', 'PE合理']
            }
        },
        'money_flow': {
            'score': 55,
            'main_flow': {
                'date': '2024-12-20',
                'main_net': 1.25,
                'main_pct': 3.5,
                'retail_net': -0.85
            }
        },
        'news': {
            'sentiment': '偏多',
            'sentiment_score': 8,
            'fundamental_impact': '消息面利好基本面',
            'impact_on_fundamentals': [
                {'area': '业绩表现', 'impact': '正面', 'detail': '新闻显示业绩向好'},
                {'area': '业务拓展', 'impact': '正面', 'detail': '新订单有望提升营收'}
            ],
            'items': [
                {'title': '公司发布新产品，市场反应积极', 'date': '2024-12-19'},
                {'title': '获得重要客户大单', 'date': '2024-12-18'}
            ]
        },
        'suggestion': {
            'total_score': 62,
            'action': '适量买入',
            'level': '谨慎乐观',
            'target_price': 50.22,
            'stop_loss': 43.37,
            'position': '20%',
            'fundamental_trend': '基本面向好',
            'news_impact': '消息面利好基本面',
            'score_breakdown': {
                'tech_weight': '35%',
                'fundamental_weight': '35%',
                'money_flow_weight': '15%',
                'news_sentiment_weight': '15%'
            }
        }
    }
    
    # 测试形态数据
    test_pattern_data = {
        'candlestick': {
            'patterns': [
                {'name_cn': '早晨之星', 'type': 'bullish', 'type_cn': '看涨反转', 'reliability': 5, 'confidence': 0.85},
                {'name_cn': '阳包阴', 'type': 'bullish', 'type_cn': '看涨反转', 'reliability': 4, 'confidence': 0.75}
            ],
            'bullish_count': 2,
            'bearish_count': 0,
            'bullish_score': 35.5,
            'bearish_score': 0,
            'signal': '看涨'
        },
        'chanlun': {
            'bi_count': 5,
            'zhongshu_count': 2,
            'current_trend': '向上笔进行中',
            'nearest_zhongshu': {'range': '42.80-45.20', 'zg': 45.20, 'zd': 42.80},
            'buy_points': [
                {'type': '一买', 'price': 41.50, 'confidence': 0.80, 'description': '趋势背驰点'}
            ],
            'sell_points': []
        },
        'resonance': {
            'total_score': 72.5,
            'resonance_level': '强共振',
            'bullish_score': 85.0,
            'bearish_score': 12.5,
            'signal_count': 8,
            'breakdown': {
                'K线形态': 18.0,
                '技术指标': 16.0,
                '趋势信号': 12.0,
                '成交量': 8.0,
                '基本面': 12.0,
                '情绪面': 6.5
            },
            'bullish_signals': [
                {'signal_type': '形态', 'description': '早晨之星形态确认'},
                {'signal_type': '缠论', 'description': '一买信号出现'}
            ],
            'bearish_signals': []
        },
        'sentiment': {
            'index_value': 35.5,
            'level': {'name': '恐慌'},
            'trend': '上升',
            'signal': '考虑买入',
            'components': {
                'price_volatility': 30.0,
                'volume_sentiment': 40.0,
                'momentum_sentiment': 35.0,
                'technical_sentiment': 37.0
            },
            'description': '市场情绪处于恐慌区间，可能是买入机会。'
        },
        'strategy_advice': {
            'primary_action': '买入',
            'confidence': 0.85,
            'risk_level': '中等',
            'position_suggestion': '30-40%',
            'reasoning': [
                'K线形态显示看涨反转信号',
                '缠论一买信号确认',
                '信号共振评分强共振',
                '情绪指数处于恐慌区间，适合逆向布局'
            ]
        }
    }
    
    report = generate_md_report(test_data, test_pattern_data)
    print(report)
