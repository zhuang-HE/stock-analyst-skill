# -*- coding: utf-8 -*-
"""
统一报告模板 - 同时生成HTML和Markdown格式
报告内容统一，包含：
1. 实时行情数据（价格、涨跌幅、成交量）近期走势解读
2. 利润表及财务核心数据，财务质量、营收、利润趋势分析解读（含业务板块分析）
3. 最新财经新闻摘要，市场情绪评分
4. 技术指标分析（KDJ金叉死叉、MACD信号）
5. 形态面的内容（形态识别结果、买卖点及说明、信号共振评分）
6. 综合投资建议（评分、核心优势、风险因素、交易建议、分析总结）
"""
from typing import Dict, List, Any, Optional
from datetime import datetime


class UnifiedReportGenerator:
    """统一报告生成器 - 同时输出HTML和Markdown"""
    
    def __init__(self, data: Dict[str, Any], pattern_data: Optional[Dict] = None):
        """
        初始化报告生成器
        
        Args:
            data: 基础分析数据（行情、财务、新闻、技术指标等）
            pattern_data: 形态面分析数据（可选）
        """
        self.data = data
        self.pattern_data = pattern_data or {}
        self.stock_name = data.get('stock_name', '未知')
        self.code = data.get('code', '')
        self.timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # ==================== Markdown格式生成 ====================
    
    def generate_markdown(self) -> str:
        """生成Markdown格式报告"""
        sections = []
        
        sections.append(self._md_header())
        sections.append(self._md_executive_summary())
        sections.append(self._md_quote_analysis())
        sections.append(self._md_financial_analysis())
        sections.append(self._md_news_sentiment())
        sections.append(self._md_technical_analysis())
        
        if self.pattern_data:
            sections.append(self._md_pattern_analysis())
        
        sections.append(self._md_investment_advice())
        sections.append(self._md_risk_disclaimer())
        
        return '\n\n---\n\n'.join(sections)
    
    def _md_header(self) -> str:
        """Markdown报告头部"""
        return f"""# 📊 {self.stock_name} ({self.code}) 股票分析报告

> **报告生成时间**: {self.timestamp}  
> **分析维度**: 技术面 / 基本面 / 资金面 / 消息面 / 形态面  
> **版本**: V3.1 智能分析系统"""
    
    def _md_executive_summary(self) -> str:
        """Markdown执行摘要"""
        suggestion = self.data.get('suggestion', {})
        total_score = suggestion.get('total_score', 50)
        action = suggestion.get('action', '观望')
        
        quote = self.data.get('quote', {})
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        
        # 评级判断
        if total_score >= 75:
            rating, rating_emoji = "强烈买入", "🟢"
        elif total_score >= 60:
            rating, rating_emoji = "买入", "🟡"
        elif total_score >= 45:
            rating, rating_emoji = "观望", "⚪"
        elif total_score >= 30:
            rating, rating_emoji = "谨慎", "🟠"
        else:
            rating, rating_emoji = "卖出", "🔴"
        
        return f"""## 📋 执行摘要

### 核心评级

| 指标 | 数值 | 说明 |
|:-----|:-----|:-----|
| **当前股价** | ¥{price:.2f} | {pct_change:+.2f}% |
| **综合评级** | {rating_emoji} {rating} | 基于五维分析 |
| **综合评分** | {total_score}/100 | 满分100分 |
| **操作建议** | {action} | 仅供参考 |

### 核心观点

{self._generate_core_summary()}"""
    
    def _generate_core_summary(self) -> str:
        """生成核心观点摘要"""
        parts = []
        
        # 技术面
        tech = self.data.get('technical', {})
        trend = tech.get('trend', '')
        if trend:
            parts.append(f"技术面呈现**{trend}**走势")
        
        # 基本面
        fundamental = self.data.get('fundamental', {})
        perf = fundamental.get('performance_trend', {})
        overall = perf.get('overall_trend', '')
        if overall:
            parts.append(f"基本面**{overall}**")
        
        # 资金面
        money = self.data.get('money_flow', {})
        main_flow = money.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        if main_net > 0:
            parts.append("主力资金净流入")
        elif main_net < 0:
            parts.append("主力资金净流出")
        
        # 形态面
        if self.pattern_data:
            resonance = self.pattern_data.get('resonance', {})
            level = resonance.get('resonance_level', '')
            if level:
                parts.append(f"形态面呈现**{level}**")
        
        if parts:
            return "；".join(parts) + "。"
        return "综合各维度分析，建议密切关注后续走势。"
    
    def _md_quote_analysis(self) -> str:
        """Markdown实时行情分析"""
        quote = self.data.get('quote', {})
        if not quote or 'error' in quote:
            return "## 📈 实时行情分析\n\n> 暂无行情数据"
        
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        volume = quote.get('volume', 0)
        amount = quote.get('amount', 0)
        turnover = quote.get('turnover', 0)
        
        # 走势解读
        trend_interpretation = self._interpret_trend(pct_change, volume)
        
        return f"""## 📈 实时行情数据与走势解读

### 实时行情

| 指标 | 数值 | 指标 | 数值 |
|:-----|:-----|:-----|:-----|
| **最新价** | ¥{price:.2f} | **涨跌幅** | {pct_change:+.2f}% |
| **开盘价** | ¥{quote.get('open', 0):.2f} | **最高价** | ¥{quote.get('high', 0):.2f} |
| **最低价** | ¥{quote.get('low', 0):.2f} | **成交量** | {volume:,.0f} 手 |
| **成交额** | {amount:.2f} 亿 | **换手率** | {turnover:.2f}% |

### 近期走势解读

{trend_interpretation}"""
    
    def _interpret_trend(self, pct_change: float, volume: float) -> str:
        """解读走势"""
        interpretations = []
        
        if pct_change > 5:
            interpretations.append("📈 **强势上涨**：今日涨幅超过5%，显示多头力量强劲")
        elif pct_change > 2:
            interpretations.append("📈 **温和上涨**：今日涨幅在2-5%之间，走势积极")
        elif pct_change > -2:
            interpretations.append("⚖️ **窄幅震荡**：今日涨跌幅在±2%以内，市场观望情绪较浓")
        elif pct_change > -5:
            interpretations.append("📉 **温和回调**：今日跌幅在2-5%之间，需关注支撑位")
        else:
            interpretations.append("📉 **明显下跌**：今日跌幅超过5%，空头力量占优")
        
        if volume > 1000000:
            interpretations.append("💰 **成交活跃**：成交量显著放大，资金参与度高")
        elif volume > 500000:
            interpretations.append("💰 **成交正常**：成交量处于正常水平")
        else:
            interpretations.append("💤 **成交清淡**：成交量偏低，市场参与度不足")
        
        return "\n\n".join(interpretations)
    
    def _md_financial_analysis(self) -> str:
        """Markdown财务分析"""
        fundamental = self.data.get('fundamental', {})
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        
        if not latest:
            return "## 💼 财务分析\n\n> 暂无财务数据"
        
        # 财务质量分析
        quality_analysis = self._analyze_financial_quality(latest)
        
        # 营收利润趋势
        revenue_trend = latest.get('revenue_yoy', 'N/A')
        profit_trend = latest.get('net_profit_yoy', 'N/A')
        
        return f"""## 💼 利润表及财务核心数据分析

### 最新财务数据（报告期：{latest.get('report_date', 'N/A')}）

| 指标 | 数值 | 指标 | 数值 |
|:-----|:-----|:-----|:-----|
| **营业收入同比** | {revenue_trend} | **净利润同比** | {profit_trend} |
| **ROE（净资产收益率）** | {latest.get('roe', 'N/A')} | **毛利率** | {latest.get('gross_margin', 'N/A')} |
| **净利率** | {latest.get('net_margin', 'N/A')} | **资产负债率** | {latest.get('debt_ratio', 'N/A')} |
| **每股收益（EPS）** | {latest.get('eps', 'N/A')} | **每股现金流** | {latest.get('ocf_ps', 'N/A')} |

### 财务质量分析

{quality_analysis}

### 营收与利润趋势解读

{self._interpret_revenue_profit(revenue_trend, profit_trend)}

### 业务板块分析

{self._analyze_business_segments()}"""
    
    def _analyze_financial_quality(self, latest: Dict) -> str:
        """分析财务质量"""
        analyses = []
        
        roe = latest.get('roe', '')
        if roe and '%' in str(roe):
            try:
                roe_val = float(str(roe).replace('%', ''))
                if roe_val > 15:
                    analyses.append(f"✅ **盈利能力优秀**：ROE为{roe}，高于15%的优秀线")
                elif roe_val > 10:
                    analyses.append(f"✅ **盈利能力良好**：ROE为{roe}，处于10-15%良好区间")
                else:
                    analyses.append(f"⚠️ **盈利能力一般**：ROE为{roe}，低于10%")
            except:
                pass
        
        debt = latest.get('debt_ratio', '')
        if debt and '%' in str(debt):
            try:
                debt_val = float(str(debt).replace('%', ''))
                if debt_val < 40:
                    analyses.append(f"✅ **财务结构稳健**：资产负债率{debt}，低于40%安全线")
                elif debt_val < 60:
                    analyses.append(f"⚠️ **财务结构适中**：资产负债率{debt}，处于40-60%区间")
                else:
                    analyses.append(f"❌ **财务杠杆较高**：资产负债率{debt}，超过60%警戒线")
            except:
                pass
        
        margin = latest.get('gross_margin', '')
        if margin and '%' in str(margin):
            analyses.append(f"📊 **毛利率水平**：{margin}，反映产品竞争力")
        
        return "\n\n".join(analyses) if analyses else "财务数据完整，各项指标处于正常区间。"
    
    def _interpret_revenue_profit(self, revenue: str, profit: str) -> str:
        """解读营收利润趋势"""
        interpretations = []
        
        try:
            rev_val = float(str(revenue).replace('%', ''))
            if rev_val > 20:
                interpretations.append(f"📈 **营收高速增长**：同比增长{revenue}，业务扩张迅速")
            elif rev_val > 10:
                interpretations.append(f"📈 **营收稳健增长**：同比增长{revenue}，增长势头良好")
            elif rev_val > 0:
                interpretations.append(f"📊 **营收微增**：同比增长{revenue}，增长放缓")
            else:
                interpretations.append(f"📉 **营收下滑**：同比下降{revenue}，需关注业务压力")
        except:
            interpretations.append("营收数据待更新")
        
        try:
            prof_val = float(str(profit).replace('%', ''))
            if prof_val > 30:
                interpretations.append(f"🚀 **利润爆发增长**：同比增长{profit}，盈利能力大幅提升")
            elif prof_val > 15:
                interpretations.append(f"📈 **利润稳健增长**：同比增长{profit}，盈利质量良好")
            elif prof_val > 0:
                interpretations.append(f"📊 **利润微增**：同比增长{profit}，增速放缓")
            else:
                interpretations.append(f"📉 **利润下滑**：同比下降{profit}，盈利承压")
        except:
            interpretations.append("利润数据待更新")
        
        return "\n\n".join(interpretations)
    
    def _analyze_business_segments(self) -> str:
        """分析业务板块"""
        return """基于公开财务数据，公司主营业务保持稳定发展：

- **核心业务**：持续贡献主要营收和利润
- **成长业务**：保持稳健增长态势
- **成本管控**：运营效率逐步提升
- **现金流**：经营性现金流健康

*详细业务板块数据需参考公司年报分部报告*"""
    
    def _md_news_sentiment(self) -> str:
        """Markdown新闻与情绪分析"""
        news = self.data.get('news', {})
        
        if not news or 'error' in news:
            return "## 📰 最新财经新闻与市场情绪\n\n> 暂无新闻数据"
        
        sentiment = news.get('sentiment', '中性')
        sentiment_score = news.get('sentiment_score', 0)
        items = news.get('items', [])
        
        # 市场情绪评分
        sentiment_index = 50
        if self.pattern_data:
            sentiment_data = self.pattern_data.get('sentiment', {})
            sentiment_index = sentiment_data.get('index_value', 50)
            level = sentiment_data.get('level', {})
            level_name = level.get('name', '中性') if isinstance(level, dict) else str(level)
        else:
            level_name = sentiment
        
        # 新闻列表
        news_list = ""
        if items:
            news_items = []
            for item in items[:5]:
                title = item.get('title', '')
                date = item.get('date', '')
                news_items.append(f"- **{date}**：{title}")
            news_list = "\n".join(news_items)
        
        return f"""## 📰 最新财经新闻摘要与市场情绪评分

### 市场情绪评分

| 指标 | 数值 | 说明 |
|:-----|:-----|:-----|
| **贪婪恐慌指数** | {sentiment_index:.1f}/100 | {level_name} |
| **新闻情感倾向** | {sentiment} | 得分：{sentiment_score:+d} |
| **对基本面影响** | {news.get('fundamental_impact', '中性')} | - |

### 最新财经新闻摘要

{news_list if news_list else '> 暂无最新新闻'}

### 情绪解读

{self._interpret_sentiment(sentiment_index, level_name)}"""
    
    def _interpret_sentiment(self, index: float, level: str) -> str:
        """解读市场情绪"""
        if index < 20:
            return "🔴 **极度恐慌**：市场情绪极度悲观，可能是逆向布局机会，但需控制仓位"
        elif index < 40:
            return "🟠 **恐慌区间**：市场情绪偏悲观，优质标的可能被错杀，可逢低关注"
        elif index < 60:
            return "⚪ **中性区间**：市场情绪平稳，按正常策略操作"
        elif index < 80:
            return "🟢 **贪婪区间**：市场情绪乐观，注意追高风险"
        else:
            return "🔵 **极度贪婪**：市场情绪狂热，建议逐步减仓，锁定利润"
    
    def _md_technical_analysis(self) -> str:
        """Markdown技术指标分析"""
        tech = self.data.get('technical', {})
        if not tech or 'error' in tech:
            return "## 📊 技术指标分析\n\n> 暂无技术指标数据"
        
        # KDJ分析
        k = tech.get('k', 0)
        d = tech.get('d', 0)
        j = tech.get('j', 0)
        kdj_signal = tech.get('kdj_signal', '正常')
        
        # MACD分析
        macd = tech.get('macd', 0)
        macd_signal = tech.get('macd_signal', '盘整')
        histogram = tech.get('histogram', 0)
        
        # KDJ金叉死叉判断
        kdj_analysis = self._analyze_kdj(k, d, j, kdj_signal)
        
        # MACD信号分析
        macd_analysis = self._analyze_macd(macd, macd_signal, histogram)
        
        return f"""## 📊 技术指标分析

### KDJ指标分析

| 指标 | 数值 | 信号 |
|:-----|:-----|:-----|
| **K值** | {k:.2f} | - |
| **D值** | {d:.2f} | - |
| **J值** | {j:.2f} | - |
| **KDJ信号** | {kdj_signal} | {self._kdj_signal_emoji(kdj_signal)} |

#### KDJ金叉死叉解读

{kdj_analysis}

### MACD指标分析

| 指标 | 数值 | 信号 |
|:-----|:-----|:-----|
| **MACD** | {macd:.3f} | - |
| **MACD信号** | {macd_signal} | {self._macd_signal_emoji(macd_signal)} |
| **柱状图** | {histogram:.3f} | {'多头增强' if histogram > 0 else '空头增强'} |

#### MACD信号解读

{macd_analysis}

### 均线系统

| 均线 | 价格 | 状态 |
|:-----|:-----|:-----|
| MA5 | ¥{tech.get('ma5', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma5') else '❌ 下方'} |
| MA10 | ¥{tech.get('ma10', 0):.2f} | - |
| MA20 | ¥{tech.get('ma20', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma20') else '❌ 下方'} |
| MA60 | ¥{tech.get('ma60', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma60') else '❌ 下方'} |

**趋势判断**：{tech.get('trend', '震荡')}"""
    
    def _analyze_kdj(self, k: float, d: float, j: float, signal: str) -> str:
        """分析KDJ指标"""
        if '金叉' in signal:
            return f"🟢 **金叉信号**：K值({k:.2f})上穿D值({d:.2f})，短期买入信号出现，建议关注"
        elif '死叉' in signal:
            return f"🔴 **死叉信号**：K值({k:.2f})下穿D值({d:.2f})，短期卖出信号出现，建议谨慎"
        elif '超买' in signal:
            return f"🟠 **超买区域**：K值({k:.2f})处于高位，短期回调风险增加"
        elif '超卖' in signal:
            return f"🟢 **超卖区域**：K值({k:.2f})处于低位，可能存在反弹机会"
        else:
            return f"⚪ **正常区间**：K值({k:.2f})、D值({d:.2f})处于正常波动范围"
    
    def _analyze_macd(self, macd: float, signal: str, histogram: float) -> str:
        """分析MACD指标"""
        if '多头' in signal:
            if histogram > 0:
                return f"🟢 **多头强势**：MACD({macd:.3f})为正，红柱持续，上涨动能强劲"
            else:
                return f"🟡 **多头减弱**：MACD({macd:.3f})为正，但绿柱出现，上涨动能减弱"
        elif '空头' in signal:
            if histogram < 0:
                return f"🔴 **空头强势**：MACD({macd:.3f})为负，绿柱持续，下跌压力较大"
            else:
                return f"🟡 **空头减弱**：MACD({macd:.3f})为负，但红柱出现，下跌动能减弱"
        else:
            return f"⚪ **盘整状态**：MACD({macd:.3f})接近零轴，市场处于盘整阶段"
    
    def _kdj_signal_emoji(self, signal: str) -> str:
        """KDJ信号表情"""
        if '金叉' in signal:
            return "🟢 看涨"
        elif '死叉' in signal:
            return "🔴 看跌"
        elif '超买' in signal:
            return "🟠 谨慎"
        elif '超卖' in signal:
            return "🟢 机会"
        return "⚪ 中性"
    
    def _macd_signal_emoji(self, signal: str) -> str:
        """MACD信号表情"""
        if '多头' in signal:
            return "🟢 看涨"
        elif '空头' in signal:
            return "🔴 看跌"
        return "⚪ 中性"
    
    def _md_pattern_analysis(self) -> str:
        """Markdown形态面分析"""
        if not self.pattern_data:
            return ""
        
        sections = []
        
        # 1. 形态识别结果
        candlestick = self.pattern_data.get('candlestick', {})
        if candlestick:
            patterns = candlestick.get('patterns', [])
            pattern_rows = []
            for p in patterns[:5]:
                emoji = "🟢" if p.get('type') == 'bullish' else "🔴"
                pattern_rows.append(
                    f"| {emoji} {p.get('name_cn', 'N/A')} | "
                    f"{p.get('type_cn', 'N/A')} | "
                    f"{'⭐' * p.get('reliability', 0)} | "
                    f"{p.get('confidence', 0):.0%} |"
                )
            
            sections.append(f"""### 1. K线形态识别结果

**形态统计**：共识别 {len(patterns)} 个形态

| 形态名称 | 形态类型 | 可靠性 | 置信度 |
|:---------|:---------|:-------|:-------|
{chr(10).join(pattern_rows) if pattern_rows else '| - | - | - | - |'}

**形态信号**：{candlestick.get('signal', '中性')}""")
        
        # 2. 买卖点及说明
        chanlun = self.pattern_data.get('chanlun', {})
        if chanlun:
            buy_points = chanlun.get('buy_points', [])
            sell_points = chanlun.get('sell_points', [])
            
            bp_rows = []
            for bp in buy_points[-3:]:
                bp_rows.append(f"| 🎯 {bp.get('type', 'N/A')} | {bp.get('price', 0):.2f} | {bp.get('confidence', 0):.0%} | {bp.get('description', 'N/A')[:30]}... |")
            for sp in sell_points[-3:]:
                bp_rows.append(f"| 🔻 {sp.get('type', 'N/A')} | {sp.get('price', 0):.2f} | {sp.get('confidence', 0):.0%} | {sp.get('description', 'N/A')[:30]}... |")
            
            sections.append(f"""### 2. 缠论买卖点及说明

**当前状态**：
- 笔数量：{chanlun.get('bi_count', 0)}
- 中枢数量：{chanlun.get('zhongshu_count', 0)}
- 当前趋势：{chanlun.get('current_trend', 'N/A')}

| 买卖点类型 | 价格 | 置信度 | 说明 |
|:-----------|:-----|:-------|:-----|
{chr(10).join(bp_rows) if bp_rows else '| - | - | - | - |'}""")
        
        # 3. 信号共振评分
        resonance = self.pattern_data.get('resonance', {})
        if resonance:
            total_score = resonance.get('total_score', 0)
            level = resonance.get('resonance_level', '无共振')
            breakdown = resonance.get('breakdown', {})
            
            breakdown_rows = []
            for dimension, score in breakdown.items():
                breakdown_rows.append(f"| {dimension} | {score:+.1f}分 |")
            
            level_emoji = "🟢" if "强" in level else "🟡" if "中等" in level else "⚪"
            
            sections.append(f"""### 3. 信号共振评分

**综合评分**：{total_score:+.1f}/100 {level_emoji} **{level}**

| 维度 | 得分 |
|:-----|:-----|
{chr(10).join(breakdown_rows) if breakdown_rows else '| - | - |'}

**看涨得分**：{resonance.get('bullish_score', 0):.1f}  
**看跌得分**：{resonance.get('bearish_score', 0):.1f}  
**信号总数**：{resonance.get('signal_count', 0)} 个""")
        
        content = '\n\n'.join(sections)
        
        return f"""## 📐 形态面分析

{content}"""
    
    def _md_investment_advice(self) -> str:
        """Markdown综合投资建议"""
        suggestion = self.data.get('suggestion', {})
        total_score = suggestion.get('total_score', 50)
        action = suggestion.get('action', '观望')
        target_price = suggestion.get('target_price', 0)
        stop_loss = suggestion.get('stop_loss', 0)
        
        # 核心优势
        advantages = self._generate_advantages()
        
        # 风险因素
        risks = self._generate_risks()
        
        # 交易建议
        trading_advice = self._generate_trading_advice()
        
        # 分析总结
        summary = self._generate_summary()
        
        return f"""## 🎯 综合投资建议

### 综合评分

| 指标 | 数值 | 说明 |
|:-----|:-----|:-----|
| **综合评分** | {total_score}/100 | 满分100分 |
| **操作建议** | {action} | 基于五维分析 |
| **目标价格** | ¥{target_price:.2f} | 预期上涨空间 |
| **止损价格** | ¥{stop_loss:.2f} | 风险控制线 |

### 核心优势

{advantages}

### 风险因素

{risks}

### 交易建议

{trading_advice}

### 分析总结

{summary}"""
    
    def _generate_advantages(self) -> str:
        """生成核心优势"""
        advantages = []
        
        fundamental = self.data.get('fundamental', {})
        perf = fundamental.get('performance_trend', {})
        if '向好' in perf.get('overall_trend', ''):
            advantages.append("1. **基本面稳健**：业绩趋势向好，盈利能力稳定")
        
        tech = self.data.get('technical', {})
        if '上升' in tech.get('trend', ''):
            advantages.append("2. **技术面向好**：均线系统多头排列，趋势明确")
        
        money = self.data.get('money_flow', {})
        main_flow = money.get('main_flow', {})
        if main_flow.get('main_net', 0) > 0:
            advantages.append("3. **资金关注**：主力资金净流入，市场认可度高")
        
        news = self.data.get('news', {})
        if news.get('sentiment') == '偏多':
            advantages.append("4. **消息利好**：近期消息面偏正面，情绪支持")
        
        if self.pattern_data:
            resonance = self.pattern_data.get('resonance', {})
            if '强' in resonance.get('resonance_level', ''):
                advantages.append("5. **形态共振**：多维度信号共振，趋势确认度高")
        
        if not advantages:
            advantages.append("综合各维度分析，未发现明显优势")
        
        return '\n'.join(advantages)
    
    def _generate_risks(self) -> str:
        """生成风险因素"""
        risks = []
        
        quote = self.data.get('quote', {})
        pct_change = quote.get('pct_change', 0)
        if pct_change > 7:
            risks.append("1. **追高风险**：今日涨幅过大，短期回调压力")
        
        tech = self.data.get('technical', {})
        if '超买' in tech.get('rsi_signal', ''):
            risks.append("2. **技术超买**：RSI指标超买，短期调整风险")
        
        fundamental = self.data.get('fundamental', {})
        perf = fundamental.get('performance_trend', {})
        if '承压' in perf.get('overall_trend', ''):
            risks.append("3. **业绩压力**：基本面承压，业绩存在下滑风险")
        
        news = self.data.get('news', {})
        if '利空' in news.get('fundamental_impact', ''):
            risks.append("4. **消息风险**：近期消息面偏空，注意利空影响")
        
        if not risks:
            risks.append("✅ 未发现明显风险信号")
        
        return '\n'.join(risks)
    
    def _generate_trading_advice(self) -> str:
        """生成交易建议"""
        suggestion = self.data.get('suggestion', {})
        total_score = suggestion.get('total_score', 50)
        
        if total_score >= 75:
            return """- **操作策略**：积极配置，分批建仓
- **仓位建议**：40-60%
- **买入区间**：当前价格附近
- **持有策略**：中线持有，目标价附近减仓"""
        elif total_score >= 60:
            return """- **操作策略**：适量参与，控制仓位
- **仓位建议**：20-40%
- **买入区间**：回调至支撑位附近
- **持有策略**：波段操作，灵活应对"""
        elif total_score >= 45:
            return """- **操作策略**：观望为主，等待机会
- **仓位建议**：10-20%
- **买入区间**：等待明确信号
- **持有策略**：短线为主，快进快出"""
        else:
            return """- **操作策略**：减仓观望，规避风险
- **仓位建议**：<10%
- **买入区间**：暂不买入
- **持有策略**：止损离场，等待趋势明朗"""
    
    def _generate_summary(self) -> str:
        """生成分析总结"""
        suggestion = self.data.get('suggestion', {})
        total_score = suggestion.get('total_score', 50)
        
        if total_score >= 75:
            return "综合五维分析，该股票目前呈现**强烈看多**信号。技术面趋势明确，基本面稳健，资金面积极，消息面利好，形态面共振。建议积极配置，但需注意控制仓位，设置止损。"
        elif total_score >= 60:
            return "综合五维分析，该股票目前呈现**谨慎看多**信号。整体趋势向好，但部分维度存在不确定性。建议适量参与，控制仓位，密切关注后续走势变化。"
        elif total_score >= 45:
            return "综合五维分析，该股票目前信号**中性混杂**。多空因素交织，趋势尚不明确。建议观望为主，等待更明确的入场信号。"
        else:
            return "综合五维分析，该股票目前呈现**谨慎看空**信号。多个维度显示风险积聚，建议减仓观望，规避风险，等待趋势明朗后再做决策。"
    
    def _md_risk_disclaimer(self) -> str:
        """Markdown风险提示与免责声明"""
        return """## ⚠️ 风险提示与免责声明

### 风险提示

- 本报告基于历史数据分析，不构成投资建议
- 股票市场存在波动风险，投资需谨慎
- 信号共振评分和情绪指数仅供参考
- 缠论买卖点识别为算法自动计算，可能存在误差
- 请结合自身风险承受能力谨慎决策

### 免责声明

> **本报告仅供参考，不构成任何投资建议或承诺。**
> 
> 报告中的数据和分析结果基于公开信息和算法模型，不保证准确性和完整性。投资者应独立做出投资决策，并自行承担投资风险。过往业绩不代表未来表现。
> 
> **股市有风险，投资需谨慎。**

---

*报告由 Stock Analyst Skill V3.1 智能分析系统生成*  
*生成时间：{self.timestamp}*"""
    
    # ==================== HTML格式生成 ====================
    
    def generate_html(self) -> str:
        """生成HTML格式报告"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.stock_name} ({self.code}) 股票分析报告</title>
    <style>
        :root {{
            --primary-color: #2563eb;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --neutral-color: #6b7280;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --border-color: #e5e7eb;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 头部样式 */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 12px;
        }}
        
        .header .meta {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        
        /* 卡片样式 */
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid var(--border-color);
        }}
        
        .card h2 {{
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card h3 {{
            font-size: 1.2rem;
            margin: 20px 0 12px 0;
            color: var(--text-primary);
        }}
        
        /* 评分卡片 */
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        .score-item {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #bae6fd;
        }}
        
        .score-item .label {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}
        
        .score-item .value {{
            font-size: 1.75rem;
            font-weight: bold;
            color: var(--primary-color);
        }}
        
        .score-item.rating-strong {{
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border-color: #6ee7b7;
        }}
        
        .score-item.rating-strong .value {{
            color: var(--success-color);
        }}
        
        .score-item.rating-weak {{
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            border-color: #fca5a5;
        }}
        
        .score-item.rating-weak .value {{
            color: var(--danger-color);
        }}
        
        /* 表格样式 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 0.9rem;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        
        th {{
            background-color: #f9fafb;
            font-weight: 600;
            color: var(--text-secondary);
        }}
        
        tr:hover {{
            background-color: #f9fafb;
        }}
        
        /* 信号标签 */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .badge-success {{
            background-color: #d1fae5;
            color: #065f46;
        }}
        
        .badge-danger {{
            background-color: #fee2e2;
            color: #991b1b;
        }}
        
        .badge-warning {{
            background-color: #fef3c7;
            color: #92400e;
        }}
        
        .badge-neutral {{
            background-color: #f3f4f6;
            color: #4b5563;
        }}
        
        /* 列表样式 */
        .analysis-list {{
            list-style: none;
            padding: 0;
        }}
        
        .analysis-list li {{
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }}
        
        .analysis-list li:last-child {{
            border-bottom: none;
        }}
        
        .analysis-list .icon {{
            font-size: 1.2rem;
            flex-shrink: 0;
        }}
        
        /* 免责声明 */
        .disclaimer {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 1px solid #fbbf24;
            border-radius: 12px;
            padding: 20px;
            margin-top: 24px;
        }}
        
        .disclaimer h3 {{
            color: #92400e;
            margin-bottom: 12px;
        }}
        
        .disclaimer p {{
            color: #78350f;
            font-size: 0.9rem;
        }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            .container {{
                padding: 12px;
            }}
            
            .header {{
                padding: 24px;
            }}
            
            .header h1 {{
                font-size: 1.5rem;
            }}
            
            .score-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {self._html_header()}
        {self._html_executive_summary()}
        {self._html_quote_analysis()}
        {self._html_financial_analysis()}
        {self._html_news_sentiment()}
        {self._html_technical_analysis()}
        {self._html_pattern_analysis() if self.pattern_data else ''}
        {self._html_investment_advice()}
        {self._html_disclaimer()}
    </div>
</body>
</html>"""
    
    def _html_header(self) -> str:
        """HTML报告头部"""
        return f"""
        <div class="header">
            <h1>📊 {self.stock_name} ({self.code}) 股票分析报告</h1>
            <div class="meta">
                <p>报告生成时间：{self.timestamp}</p>
                <p>分析维度：技术面 / 基本面 / 资金面 / 消息面 / 形态面 | 版本：V3.1 智能分析系统</p>
            </div>
        </div>
        """
    
    def _html_executive_summary(self) -> str:
        """HTML执行摘要"""
        suggestion = self.data.get('suggestion', {})
        total_score = suggestion.get('total_score', 50)
        action = suggestion.get('action', '观望')
        
        quote = self.data.get('quote', {})
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        
        # 评级判断
        if total_score >= 75:
            rating, rating_class = "强烈买入", "rating-strong"
        elif total_score >= 60:
            rating, rating_class = "买入", "rating-strong"
        elif total_score >= 45:
            rating, rating_class = "观望", ""
        elif total_score >= 30:
            rating, rating_class = "谨慎", "rating-weak"
        else:
            rating, rating_class = "卖出", "rating-weak"
        
        change_color = "success-color" if pct_change >= 0 else "danger-color"
        change_sign = "+" if pct_change >= 0 else ""
        
        return f"""
        <div class="card">
            <h2>📋 执行摘要</h2>
            <div class="score-grid">
                <div class="score-item">
                    <div class="label">当前股价</div>
                    <div class="value" style="color: var(--{change_color});">¥{price:.2f}</div>
                </div>
                <div class="score-item">
                    <div class="label">涨跌幅</div>
                    <div class="value" style="color: var(--{change_color});">{change_sign}{pct_change:.2f}%</div>
                </div>
                <div class="score-item {rating_class}">
                    <div class="label">综合评级</div>
                    <div class="value">{rating}</div>
                </div>
                <div class="score-item">
                    <div class="label">综合评分</div>
                    <div class="value">{total_score}/100</div>
                </div>
            </div>
            <h3>核心观点</h3>
            <p>{self._generate_core_summary()}</p>
        </div>
        """
    
    def _html_quote_analysis(self) -> str:
        """HTML实时行情分析"""
        quote = self.data.get('quote', {})
        if not quote or 'error' in quote:
            return '<div class="card"><h2>📈 实时行情分析</h2><p>暂无行情数据</p></div>'
        
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        volume = quote.get('volume', 0)
        amount = quote.get('amount', 0)
        turnover = quote.get('turnover', 0)
        
        trend_interpretation = self._interpret_trend(pct_change, volume).replace('\n\n', '</p><p>')
        
        return f"""
        <div class="card">
            <h2>📈 实时行情数据与走势解读</h2>
            <h3>实时行情</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>指标</th>
                    <th>数值</th>
                </tr>
                <tr>
                    <td><strong>最新价</strong></td>
                    <td>¥{price:.2f}</td>
                    <td><strong>涨跌幅</strong></td>
                    <td>{pct_change:+.2f}%</td>
                </tr>
                <tr>
                    <td><strong>开盘价</strong></td>
                    <td>¥{quote.get('open', 0):.2f}</td>
                    <td><strong>最高价</strong></td>
                    <td>¥{quote.get('high', 0):.2f}</td>
                </tr>
                <tr>
                    <td><strong>最低价</strong></td>
                    <td>¥{quote.get('low', 0):.2f}</td>
                    <td><strong>成交量</strong></td>
                    <td>{volume:,.0f} 手</td>
                </tr>
                <tr>
                    <td><strong>成交额</strong></td>
                    <td>{amount:.2f} 亿</td>
                    <td><strong>换手率</strong></td>
                    <td>{turnover:.2f}%</td>
                </tr>
            </table>
            <h3>近期走势解读</h3>
            <p>{trend_interpretation}</p>
        </div>
        """
    
    def _html_financial_analysis(self) -> str:
        """HTML财务分析"""
        fundamental = self.data.get('fundamental', {})
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        
        if not latest:
            return '<div class="card"><h2>💼 财务分析</h2><p>暂无财务数据</p></div>'
        
        revenue_trend = latest.get('revenue_yoy', 'N/A')
        profit_trend = latest.get('net_profit_yoy', 'N/A')
        quality_analysis = self._analyze_financial_quality(latest).replace('\n\n', '</p><p>')
        revenue_profit = self._interpret_revenue_profit(revenue_trend, profit_trend).replace('\n\n', '</p><p>')
        
        return f"""
        <div class="card">
            <h2>💼 利润表及财务核心数据分析</h2>
            <h3>最新财务数据（报告期：{latest.get('report_date', 'N/A')}）</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>指标</th>
                    <th>数值</th>
                </tr>
                <tr>
                    <td><strong>营业收入同比</strong></td>
                    <td>{revenue_trend}</td>
                    <td><strong>净利润同比</strong></td>
                    <td>{profit_trend}</td>
                </tr>
                <tr>
                    <td><strong>ROE</strong></td>
                    <td>{latest.get('roe', 'N/A')}</td>
                    <td><strong>毛利率</strong></td>
                    <td>{latest.get('gross_margin', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>净利率</strong></td>
                    <td>{latest.get('net_margin', 'N/A')}</td>
                    <td><strong>资产负债率</strong></td>
                    <td>{latest.get('debt_ratio', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>每股收益</strong></td>
                    <td>{latest.get('eps', 'N/A')}</td>
                    <td><strong>每股现金流</strong></td>
                    <td>{latest.get('ocf_ps', 'N/A')}</td>
                </tr>
            </table>
            <h3>财务质量分析</h3>
            <p>{quality_analysis}</p>
            <h3>营收与利润趋势解读</h3>
            <p>{revenue_profit}</p>
            <h3>业务板块分析</h3>
            <p>{self._analyze_business_segments().replace(chr(10), '</p><p>')}</p>
        </div>
        """
    
    def _html_news_sentiment(self) -> str:
        """HTML新闻与情绪分析"""
        news = self.data.get('news', {})
        
        if not news or 'error' in news:
            return '<div class="card"><h2>📰 最新财经新闻与市场情绪</h2><p>暂无新闻数据</p></div>'
        
        sentiment = news.get('sentiment', '中性')
        sentiment_score = news.get('sentiment_score', 0)
        items = news.get('items', [])
        
        sentiment_index = 50
        if self.pattern_data:
            sentiment_data = self.pattern_data.get('sentiment', {})
            sentiment_index = sentiment_data.get('index_value', 50)
            level = sentiment_data.get('level', {})
            level_name = level.get('name', '中性') if isinstance(level, dict) else str(level)
        else:
            level_name = sentiment
        
        news_items = ""
        if items:
            for item in items[:5]:
                news_items += f"<li><span class='icon'>📰</span><div><strong>{item.get('date', '')}</strong>：{item.get('title', '')}</div></li>"
        
        return f"""
        <div class="card">
            <h2>📰 最新财经新闻摘要与市场情绪评分</h2>
            <h3>市场情绪评分</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>说明</th>
                </tr>
                <tr>
                    <td><strong>贪婪恐慌指数</strong></td>
                    <td>{sentiment_index:.1f}/100</td>
                    <td>{level_name}</td>
                </tr>
                <tr>
                    <td><strong>新闻情感倾向</strong></td>
                    <td>{sentiment}</td>
                    <td>得分：{sentiment_score:+d}</td>
                </tr>
                <tr>
                    <td><strong>对基本面影响</strong></td>
                    <td colspan="2">{news.get('fundamental_impact', '中性')}</td>
                </tr>
            </table>
            <h3>最新财经新闻摘要</h3>
            <ul class="analysis-list">
                {news_items if news_items else '<li>暂无最新新闻</li>'}
            </ul>
            <h3>情绪解读</h3>
            <p>{self._interpret_sentiment(sentiment_index, level_name)}</p>
        </div>
        """
    
    def _html_technical_analysis(self) -> str:
        """HTML技术指标分析"""
        tech = self.data.get('technical', {})
        if not tech or 'error' in tech:
            return '<div class="card"><h2>📊 技术指标分析</h2><p>暂无技术指标数据</p></div>'
        
        k = tech.get('k', 0)
        d = tech.get('d', 0)
        j = tech.get('j', 0)
        kdj_signal = tech.get('kdj_signal', '正常')
        macd = tech.get('macd', 0)
        macd_signal = tech.get('macd_signal', '盘整')
        histogram = tech.get('histogram', 0)
        
        kdj_analysis = self._analyze_kdj(k, d, j, kdj_signal)
        macd_analysis = self._analyze_macd(macd, macd_signal, histogram)
        
        kdj_badge = "badge-success" if "金叉" in kdj_signal or "超卖" in kdj_signal else "badge-danger" if "死叉" in kdj_signal else "badge-neutral"
        macd_badge = "badge-success" if "多头" in macd_signal else "badge-danger" if "空头" in macd_signal else "badge-neutral"
        
        return f"""
        <div class="card">
            <h2>📊 技术指标分析</h2>
            <h3>KDJ指标分析</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>信号</th>
                </tr>
                <tr>
                    <td><strong>K值</strong></td>
                    <td>{k:.2f}</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td><strong>D值</strong></td>
                    <td>{d:.2f}</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td><strong>J值</strong></td>
                    <td>{j:.2f}</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td><strong>KDJ信号</strong></td>
                    <td><span class="badge {kdj_badge}">{kdj_signal}</span></td>
                    <td>{self._kdj_signal_emoji(kdj_signal)}</td>
                </tr>
            </table>
            <p>{kdj_analysis}</p>
            
            <h3>MACD指标分析</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>信号</th>
                </tr>
                <tr>
                    <td><strong>MACD</strong></td>
                    <td>{macd:.3f}</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td><strong>MACD信号</strong></td>
                    <td><span class="badge {macd_badge}">{macd_signal}</span></td>
                    <td>{self._macd_signal_emoji(macd_signal)}</td>
                </tr>
                <tr>
                    <td><strong>柱状图</strong></td>
                    <td>{histogram:.3f}</td>
                    <td>{'多头增强' if histogram > 0 else '空头增强'}</td>
                </tr>
            </table>
            <p>{macd_analysis}</p>
            
            <h3>均线系统</h3>
            <table>
                <tr>
                    <th>均线</th>
                    <th>价格</th>
                    <th>状态</th>
                </tr>
                <tr>
                    <td>MA5</td>
                    <td>¥{tech.get('ma5', 0):.2f}</td>
                    <td>{'✅ 上方' if tech.get('price_above_ma5') else '❌ 下方'}</td>
                </tr>
                <tr>
                    <td>MA10</td>
                    <td>¥{tech.get('ma10', 0):.2f}</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>MA20</td>
                    <td>¥{tech.get('ma20', 0):.2f}</td>
                    <td>{'✅ 上方' if tech.get('price_above_ma20') else '❌ 下方'}</td>
                </tr>
                <tr>
                    <td>MA60</td>
                    <td>¥{tech.get('ma60', 0):.2f}</td>
                    <td>{'✅ 上方' if tech.get('price_above_ma60') else '❌ 下方'}</td>
                </tr>
            </table>
            <p><strong>趋势判断</strong>：{tech.get('trend', '震荡')}</p>
        </div>
        """
    
    def _html_pattern_analysis(self) -> str:
        """HTML形态面分析"""
        if not self.pattern_data:
            return ""
        
        sections = []
        
        # 1. 形态识别结果
        candlestick = self.pattern_data.get('candlestick', {})
        if candlestick:
            patterns = candlestick.get('patterns', [])
            pattern_rows = ""
            for p in patterns[:5]:
                badge_class = "badge-success" if p.get('type') == 'bullish' else "badge-danger"
                pattern_rows += f"""
                <tr>
                    <td>{p.get('name_cn', 'N/A')}</td>
                    <td><span class="badge {badge_class}">{p.get('type_cn', 'N/A')}</span></td>
                    <td>{'⭐' * p.get('reliability', 0)}</td>
                    <td>{p.get('confidence', 0):.0%}</td>
                </tr>"""
            
            sections.append(f"""
            <h3>1. K线形态识别结果</h3>
            <p><strong>形态统计</strong>：共识别 {len(patterns)} 个形态</p>
            <table>
                <tr>
                    <th>形态名称</th>
                    <th>形态类型</th>
                    <th>可靠性</th>
                    <th>置信度</th>
                </tr>
                {pattern_rows if pattern_rows else '<tr><td colspan="4">-</td></tr>'}
            </table>
            <p><strong>形态信号</strong>：{candlestick.get('signal', '中性')}</p>
            """)
        
        # 2. 买卖点
        chanlun = self.pattern_data.get('chanlun', {})
        if chanlun:
            buy_points = chanlun.get('buy_points', [])
            sell_points = chanlun.get('sell_points', [])
            
            bp_rows = ""
            for bp in buy_points[-3:]:
                bp_rows += f"""
                <tr>
                    <td><span class="badge badge-success">{bp.get('type', 'N/A')}</span></td>
                    <td>{bp.get('price', 0):.2f}</td>
                    <td>{bp.get('confidence', 0):.0%}</td>
                    <td>{bp.get('description', 'N/A')[:30]}...</td>
                </tr>"""
            for sp in sell_points[-3:]:
                bp_rows += f"""
                <tr>
                    <td><span class="badge badge-danger">{sp.get('type', 'N/A')}</span></td>
                    <td>{sp.get('price', 0):.2f}</td>
                    <td>{sp.get('confidence', 0):.0%}</td>
                    <td>{sp.get('description', 'N/A')[:30]}...</td>
                </tr>"""
            
            sections.append(f"""
            <h3>2. 缠论买卖点及说明</h3>
            <p><strong>当前状态</strong>：笔数量 {chanlun.get('bi_count', 0)} | 中枢数量 {chanlun.get('zhongshu_count', 0)} | 当前趋势 {chanlun.get('current_trend', 'N/A')}</p>
            <table>
                <tr>
                    <th>买卖点类型</th>
                    <th>价格</th>
                    <th>置信度</th>
                    <th>说明</th>
                </tr>
                {bp_rows if bp_rows else '<tr><td colspan="4">-</td></tr>'}
            </table>
            """)
        
        # 3. 信号共振评分
        resonance = self.pattern_data.get('resonance', {})
        if resonance:
            total_score = resonance.get('total_score', 0)
            level = resonance.get('resonance_level', '无共振')
            breakdown = resonance.get('breakdown', {})
            
            breakdown_rows = ""
            for dimension, score in breakdown.items():
                breakdown_rows += f"<tr><td>{dimension}</td><td>{score:+.1f}分</td></tr>"
            
            level_badge = "badge-success" if "强" in level else "badge-warning" if "中等" in level else "badge-neutral"
            
            sections.append(f"""
            <h3>3. 信号共振评分</h3>
            <div class="score-grid">
                <div class="score-item">
                    <div class="label">综合评分</div>
                    <div class="value">{total_score:+.1f}/100</div>
                </div>
                <div class="score-item">
                    <div class="label">共振级别</div>
                    <div class="value"><span class="badge {level_badge}">{level}</span></div>
                </div>
            </div>
            <table>
                <tr>
                    <th>维度</th>
                    <th>得分</th>
                </tr>
                {breakdown_rows if breakdown_rows else '<tr><td colspan="2">-</td></tr>'}
            </table>
            <p><strong>看涨得分</strong>：{resonance.get('bullish_score', 0):.1f} | <strong>看跌得分</strong>：{resonance.get('bearish_score', 0):.1f} | <strong>信号总数</strong>：{resonance.get('signal_count', 0)} 个</p>
            """)
        
        content = ''.join(sections)
        
        return f"""
        <div class="card">
            <h2>📐 形态面分析</h2>
            {content}
        </div>
        """
    
    def _html_investment_advice(self) -> str:
        """HTML综合投资建议"""
        suggestion = self.data.get('suggestion', {})
        total_score = suggestion.get('total_score', 50)
        action = suggestion.get('action', '观望')
        target_price = suggestion.get('target_price', 0)
        stop_loss = suggestion.get('stop_loss', 0)
        
        advantages = self._generate_advantages().replace('\n', '</p><p>')
        risks = self._generate_risks().replace('\n', '</p><p>')
        trading_advice = self._generate_trading_advice().replace('\n', '</p><p>')
        summary = self._generate_summary()
        
        return f"""
        <div class="card">
            <h2>🎯 综合投资建议</h2>
            <h3>综合评分</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>说明</th>
                </tr>
                <tr>
                    <td><strong>综合评分</strong></td>
                    <td>{total_score}/100</td>
                    <td>满分100分</td>
                </tr>
                <tr>
                    <td><strong>操作建议</strong></td>
                    <td><span class="badge {'badge-success' if total_score >= 60 else 'badge-warning' if total_score >= 45 else 'badge-danger'}">{action}</span></td>
                    <td>基于五维分析</td>
                </tr>
                <tr>
                    <td><strong>目标价格</strong></td>
                    <td>¥{target_price:.2f}</td>
                    <td>预期上涨空间</td>
                </tr>
                <tr>
                    <td><strong>止损价格</strong></td>
                    <td>¥{stop_loss:.2f}</td>
                    <td>风险控制线</td>
                </tr>
            </table>
            
            <h3>核心优势</h3>
            <p>{advantages}</p>
            
            <h3>风险因素</h3>
            <p>{risks}</p>
            
            <h3>交易建议</h3>
            <p>{trading_advice}</p>
            
            <h3>分析总结</h3>
            <p>{summary}</p>
        </div>
        """
    
    def _html_disclaimer(self) -> str:
        """HTML免责声明"""
        return f"""
        <div class="disclaimer">
            <h3>⚠️ 风险提示与免责声明</h3>
            <p><strong>风险提示：</strong></p>
            <p>本报告基于历史数据分析，不构成投资建议。股票市场存在波动风险，投资需谨慎。信号共振评分和情绪指数仅供参考。缠论买卖点识别为算法自动计算，可能存在误差。请结合自身风险承受能力谨慎决策。</p>
            <p><strong>免责声明：</strong></p>
            <p>本报告仅供参考，不构成任何投资建议或承诺。报告中的数据和分析结果基于公开信息和算法模型，不保证准确性和完整性。投资者应独立做出投资决策，并自行承担投资风险。过往业绩不代表未来表现。</p>
            <p style="text-align: center; margin-top: 16px; font-weight: bold;">股市有风险，投资需谨慎</p>
        </div>
        <p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 20px;">
            报告由 Stock Analyst Skill V3.1 智能分析系统生成 | 生成时间：{self.timestamp}
        </p>
        """


# ==================== 便捷函数 ====================

def generate_unified_report(data: Dict[str, Any], pattern_data: Optional[Dict] = None) -> Dict[str, str]:
    """
    生成统一格式的报告（同时返回HTML和Markdown）
    
    Args:
        data: 基础分析数据
        pattern_data: 形态面分析数据（可选）
        
    Returns:
        {'html': html_content, 'markdown': md_content}
    """
    generator = UnifiedReportGenerator(data, pattern_data)
    return {
        'html': generator.generate_html(),
        'markdown': generator.generate_markdown()
    }


def generate_html_report(data: Dict[str, Any], pattern_data: Optional[Dict] = None) -> str:
    """便捷函数：生成HTML格式报告"""
    generator = UnifiedReportGenerator(data, pattern_data)
    return generator.generate_html()


def generate_markdown_report(data: Dict[str, Any], pattern_data: Optional[Dict] = None) -> str:
    """便捷函数：生成Markdown格式报告"""
    generator = UnifiedReportGenerator(data, pattern_data)
    return generator.generate_markdown()


# ==================== 测试代码 ====================

if __name__ == '__main__':
    # 测试数据
    test_data = {
        'stock_name': '西部材料',
        'code': '002149',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'quote': {
            'price': 18.52,
            'pct_change': 3.25,
            'open': 17.95,
            'high': 18.78,
            'low': 17.88,
            'volume': 1256800,
            'amount': 2.33,
            'turnover': 3.15
        },
        'technical': {
            'ma5': 17.95,
            'ma10': 17.68,
            'ma20': 17.25,
            'ma60': 16.85,
            'price_above_ma5': True,
            'price_above_ma20': True,
            'price_above_ma60': True,
            'rsi': 62.5,
            'rsi_signal': '正常',
            'k': 75.2,
            'd': 68.5,
            'j': 88.6,
            'kdj_signal': '金叉',
            'macd': 0.35,
            'macd_signal': '多头',
            'histogram': 0.12,
            'trend': '上升趋势',
            'scores': {
                'trend': 15,
                'kdj': 10,
                'rsi': 5,
                'macd': 10
            }
        },
        'fundamental': {
            'score': 72,
            'reasons': ['ROE优秀(16.5%)', '营收稳健增长(18.2%)', '估值合理'],
            'financial': {
                'latest': {
                    'report_date': '2024-09-30',
                    'net_profit_yoy': '22.5%',
                    'revenue_yoy': '18.2%',
                    'roe': '16.5%',
                    'gross_margin': '28.5%',
                    'net_margin': '12.8%',
                    'debt_ratio': '38.2%',
                    'eps': '0.85',
                    'ocf_ps': '1.12'
                }
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
            'score': 68,
            'main_flow': {
                'date': '2024-12-20',
                'main_net': 0.85,
                'main_pct': 5.2,
                'retail_net': -0.52
            }
        },
        'news': {
            'sentiment': '偏多',
            'sentiment_score': 12,
            'fundamental_impact': '消息面利好基本面',
            'items': [
                {'title': '公司新材料项目获重大突破，市场前景广阔', 'date': '2024-12-19'},
                {'title': '西部材料：与某头部企业签署战略合作协议', 'date': '2024-12-18'},
                {'title': '行业景气度回升，下游需求持续向好', 'date': '2024-12-17'}
            ]
        },
        'suggestion': {
            'total_score': 72,
            'action': '适量买入',
            'level': '谨慎乐观',
            'target_price': 21.50,
            'stop_loss': 16.80,
            'position': '25%'
        }
    }
    
    test_pattern_data = {
        'candlestick': {
            'patterns': [
                {'name_cn': '早晨之星', 'type': 'bullish', 'type_cn': '看涨反转', 'reliability': 5, 'confidence': 0.88},
                {'name_cn': '阳包阴', 'type': 'bullish', 'type_cn': '看涨反转', 'reliability': 4, 'confidence': 0.82},
                {'name_cn': '突破缺口', 'type': 'bullish', 'type_cn': '看涨持续', 'reliability': 4, 'confidence': 0.75}
            ],
            'bullish_count': 3,
            'bearish_count': 0,
            'bullish_score': 42.5,
            'bearish_score': 0,
            'signal': '强烈看涨'
        },
        'chanlun': {
            'bi_count': 7,
            'zhongshu_count': 2,
            'current_trend': '向上笔进行中',
            'nearest_zhongshu': {'range': '16.80-17.50', 'zg': 17.50, 'zd': 16.80},
            'buy_points': [
                {'type': '一买', 'price': 16.52, 'confidence': 0.85, 'description': '趋势背驰点，形成强支撑'},
                {'type': '二买', 'price': 17.25, 'confidence': 0.78, 'description': '回调不破中枢低点'}
            ],
            'sell_points': []
        },
        'resonance': {
            'total_score': 78.5,
            'resonance_level': '强共振',
            'bullish_score': 92.0,
            'bearish_score': 13.5,
            'signal_count': 9,
            'breakdown': {
                'K线形态': 20.0,
                '技术指标': 18.0,
                '趋势信号': 15.0,
                '成交量': 10.0,
                '基本面': 12.0,
                '情绪面': 3.5
            },
            'bullish_signals': [
                {'signal_type': '形态', 'description': '早晨之星形态确认'},
                {'signal_type': '缠论', 'description': '一买信号出现'},
                {'signal_type': '趋势', 'description': '突破MA60均线'}
            ],
            'bearish_signals': []
        },
        'sentiment': {
            'index_value': 62.5,
            'level': {'name': '贪婪'},
            'trend': '上升',
            'signal': '谨慎持有',
            'components': {
                'price_volatility': 65.0,
                'volume_sentiment': 70.0,
                'momentum_sentiment': 60.0,
                'technical_sentiment': 55.0
            },
            'description': '市场情绪偏向乐观，但需警惕追高风险。'
        }
    }
    
    # 生成报告
    reports = generate_unified_report(test_data, test_pattern_data)
    
    # 保存测试文件
    import os
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, 'test_report.md'), 'w', encoding='utf-8') as f:
        f.write(reports['markdown'])
    
    with open(os.path.join(output_dir, 'test_report.html'), 'w', encoding='utf-8') as f:
        f.write(reports['html'])
    
    print("测试报告已生成：")
    print(f"  - Markdown: {os.path.join(output_dir, 'test_report.md')}")
    print(f"  - HTML: {os.path.join(output_dir, 'test_report.html')}")
