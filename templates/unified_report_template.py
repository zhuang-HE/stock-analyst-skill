# -*- coding: utf-8 -*-
"""
================================================================================
统一专业股票分析报告模板 V3.1 Pro
================================================================================
同时生成HTML和Markdown格式，内容统一、专业、功能完备

报告结构：
├── 封面与概览
├── 一、实时行情与走势分析（价格、涨跌幅、成交量、技术走势）
├── 二、财务深度分析（利润表、财务质量、趋势、业务板块）
├── 三、新闻舆情与市场情绪（新闻摘要、情绪指数、舆情分析）
├── 四、技术指标深度解析（KDJ/MACD/均线/量价）
├── 五、形态面专业分析【重点强化】
│   ├── 5.1 K线形态识别结果（60+形态库、形态详情、可靠性评估）
│   ├── 5.2 缠论结构分析（笔/中枢/趋势、买卖点识别）
│   ├── 5.3 买卖点信号系统（一买二买三买/一卖二卖三卖、置信度）
│   └── 5.4 信号共振评分（7维度加权、共振级别、信号明细）
├── 六、综合投资决策建议（评分、优势、风险、策略、总结）
└── 附录：风险提示与免责声明

作者：Stock Analyst Skill V3.1
================================================================================
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json


class UnifiedReportGenerator:
    """
    统一专业报告生成器
    
    特性：
    - 双格式输出：HTML（可视化）+ Markdown（可读性）
    - 五维分析体系：技术/基本面/资金/消息/形态
    - 形态面深度强化：K线形态+缠论+买卖点+共振评分
    - 专业级内容：财务解读、技术指标、投资策略
    """
    
    # 评级标准
    RATING_LEVELS = {
        (85, 100): ('强烈买入', '🟢', 'rating-strong', '多维度强烈共振，建议积极配置'),
        (70, 84): ('买入', '🟢', 'rating-strong', '机会大于风险，建议适量参与'),
        (55, 69): ('谨慎乐观', '🟡', '', '信号偏正面，控制仓位参与'),
        (45, 54): ('观望', '⚪', '', '信号混杂，建议等待明确机会'),
        (30, 44): ('谨慎', '🟠', 'rating-weak', '风险积聚，建议减仓观望'),
        (0, 29): ('卖出', '🔴', 'rating-weak', '趋势恶化，建议规避风险'),
    }
    
    # 共振级别
    RESONANCE_LEVELS = {
        (75, 100): ('强共振', '🟢', '多维度信号高度一致，趋势确认度高'),
        (50, 74): ('中等共振', '🟡', '多数维度信号同向，趋势较为明确'),
        (25, 49): ('弱共振', '⚪', '部分维度信号同向，趋势待确认'),
        (0, 24): ('无共振', '⚫', '各维度信号分散，趋势不明确'),
    }
    
    def __init__(self, data: Dict[str, Any], pattern_data: Optional[Dict] = None):
        """
        初始化报告生成器
        
        Args:
            data: 基础分析数据（行情、财务、新闻、技术指标等）
            pattern_data: 形态面分析数据（K线形态、缠论、共振评分等）
        """
        self.data = data
        self.pattern_data = pattern_data or {}
        self.stock_name = data.get('stock_name', '未知')
        self.code = data.get('code', '')
        self.timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 计算综合评分
        self.suggestion = data.get('suggestion', {})
        self.total_score = self.suggestion.get('total_score', 50)
        self.rating, self.rating_emoji, self.rating_class, self.rating_summary = self._get_rating(self.total_score)
    
    def _get_rating(self, score: int) -> Tuple[str, str, str, str]:
        """根据评分获取评级信息"""
        for (min_s, max_s), (rating, emoji, css_class, summary) in self.RATING_LEVELS.items():
            if min_s <= score <= max_s:
                return rating, emoji, css_class, summary
        return '观望', '⚪', '', '信号中性，建议观望'
    
    def _get_resonance_level(self, score: float) -> Tuple[str, str, str]:
        """根据共振评分获取级别"""
        abs_score = abs(score)
        for (min_s, max_s), (level, emoji, desc) in self.RESONANCE_LEVELS.items():
            if min_s <= abs_score <= max_s:
                direction = '看涨' if score > 0 else '看跌' if score < 0 else '中性'
                return f"{emoji} {level}({direction})", emoji, desc
        return '⚫ 无共振', '⚫', '各维度信号分散'
    
    # ==================== Markdown格式生成 ====================
    
    def generate_markdown(self) -> str:
        """生成专业Markdown格式报告"""
        sections = [
            self._md_header(),
            self._md_executive_summary(),
            self._md_quote_analysis(),
            self._md_financial_analysis(),
            self._md_news_sentiment(),
            self._md_technical_analysis(),
        ]
        
        # 形态面分析（重点强化）
        if self.pattern_data:
            sections.append(self._md_pattern_analysis_enhanced())
        
        sections.extend([
            self._md_investment_advice(),
            self._md_risk_disclaimer(),
        ])
        
        return '\n\n---\n\n'.join(sections)
    
    def _md_header(self) -> str:
        """Markdown报告头部"""
        return f"""# 📊 {self.stock_name} ({self.code}) 深度分析报告

<div align="center">

**专业版股票分析报告** | **五维分析体系** | **V3.1 Pro**

📅 报告生成时间：{self.timestamp}

</div>

---

## 📋 报告概览

| 项目 | 内容 |
|:-----|:-----|
| **股票名称** | {self.stock_name} ({self.code}) |
| **分析维度** | 技术面 / 基本面 / 资金面 / 消息面 / **形态面** |
| **报告版本** | V3.1 Pro 专业版 |
| **数据时效** | 实时行情 + 最新财报 + 近期新闻 |"""
    
    def _md_executive_summary(self) -> str:
        """Markdown执行摘要"""
        quote = self.data.get('quote', {})
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        action = self.suggestion.get('action', '观望')
        target_price = self.suggestion.get('target_price', 0)
        stop_loss = self.suggestion.get('stop_loss', 0)
        
        # 形态面共振信息
        resonance_info = ""
        if self.pattern_data:
            resonance = self.pattern_data.get('resonance', {})
            res_score = resonance.get('total_score', 0)
            res_level, _, _ = self._get_resonance_level(res_score)
            resonance_info = f"| **形态面共振** | {res_level} | 信号共振评分 |\n"
        
        return f"""## 🎯 执行摘要

### 核心投资评级

<div align="center">

### {self.rating_emoji} {self.rating} | 综合评分：{self.total_score}/100

*{self.rating_summary}*

</div>

### 关键指标速览

| 指标 | 数值 | 指标 | 数值 |
|:-----|:-----|:-----|:-----|
| **当前股价** | ¥{price:.2f} | **涨跌幅** | {pct_change:+.2f}% |
| **综合评级** | {self.rating_emoji} {self.rating} | **操作建议** | {action} |
| **目标价格** | ¥{target_price:.2f} | **止损价格** | ¥{stop_loss:.2f} |
| **综合评分** | {self.total_score}/100 | **风险等级** | {self.suggestion.get('level', '中等')} |
{resonance_info}
### 核心观点

{self._generate_core_summary()}"""
    
    def _generate_core_summary(self) -> str:
        """生成核心观点摘要"""
        parts = []
        
        # 技术面
        tech = self.data.get('technical', {})
        trend = tech.get('trend', '')
        kdj_signal = tech.get('kdj_signal', '')
        macd_signal = tech.get('macd_signal', '')
        
        tech_parts = []
        if trend:
            tech_parts.append(f"技术呈现**{trend}**走势")
        if '金叉' in kdj_signal:
            tech_parts.append("KDJ金叉")
        elif '死叉' in kdj_signal:
            tech_parts.append("KDJ死叉")
        if '多头' in macd_signal:
            tech_parts.append("MACD多头")
        elif '空头' in macd_signal:
            tech_parts.append("MACD空头")
        
        if tech_parts:
            parts.append('，'.join(tech_parts))
        
        # 基本面
        fundamental = self.data.get('fundamental', {})
        perf = fundamental.get('performance_trend', {})
        overall = perf.get('overall_trend', '')
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        revenue_yoy = latest.get('revenue_yoy', '')
        profit_yoy = latest.get('net_profit_yoy', '')
        
        if overall:
            parts.append(f"基本面**{overall}**")
        if revenue_yoy and profit_yoy:
            parts.append(f"营收同比{revenue_yoy}、净利润同比{profit_yoy}")
        
        # 资金面
        money = self.data.get('money_flow', {})
        main_flow = money.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        if main_net > 0.5:
            parts.append(f"主力资金净流入{main_net:.2f}亿")
        elif main_net < -0.5:
            parts.append(f"主力资金净流出{abs(main_net):.2f}亿")
        
        # 形态面（重点）
        if self.pattern_data:
            candlestick = self.pattern_data.get('candlestick', {})
            patterns = candlestick.get('patterns', [])
            bullish_count = candlestick.get('bullish_count', 0)
            bearish_count = candlestick.get('bearish_count', 0)
            
            if patterns:
                top_pattern = patterns[0]
                pattern_info = f"识别出**{top_pattern.get('name_cn', '关键形态')}**"
                if bullish_count > bearish_count:
                    pattern_info += f"等{bullish_count}个看涨形态"
                elif bearish_count > bullish_count:
                    pattern_info += f"等{bearish_count}个看跌形态"
                parts.append(pattern_info)
            
            # 买卖点
            chanlun = self.pattern_data.get('chanlun', {})
            buy_points = chanlun.get('buy_points', [])
            sell_points = chanlun.get('sell_points', [])
            if buy_points:
                parts.append(f"缠论识别出**{buy_points[-1].get('type', '买')}点**")
            
            # 共振
            resonance = self.pattern_data.get('resonance', {})
            res_score = resonance.get('total_score', 0)
            if abs(res_score) > 50:
                direction = "看涨" if res_score > 0 else "看跌"
                parts.append(f"信号呈现**{direction}共振**")
        
        if parts:
            return '；'.join(parts) + '。建议' + self.suggestion.get('action', '观望') + '。'
        return "综合五维分析，建议密切关注后续走势变化。"
    
    def _md_quote_analysis(self) -> str:
        """Markdown实时行情分析"""
        quote = self.data.get('quote', {})
        if not quote or 'error' in quote:
            return "## 📈 一、实时行情与走势分析\n\n> 暂无行情数据"
        
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        volume = quote.get('volume', 0)
        amount = quote.get('amount', 0)
        turnover = quote.get('turnover', 0)
        open_p = quote.get('open', 0)
        high = quote.get('high', 0)
        low = quote.get('low', 0)
        
        # 计算振幅
        amplitude = ((high - low) / open_p * 100) if open_p > 0 else 0
        
        # 走势解读
        trend_analysis = self._analyze_trend_detailed(pct_change, volume, amplitude)
        
        return f"""## 📈 一、实时行情与走势分析

### 1.1 实时行情数据

| 指标 | 数值 | 指标 | 数值 | 指标 | 数值 |
|:-----|:-----|:-----|:-----|:-----|:-----|
| **最新价** | ¥{price:.2f} | **涨跌幅** | {pct_change:+.2f}% | **涨跌额** | ¥{price * pct_change / 100:.2f} |
| **开盘价** | ¥{open_p:.2f} | **最高价** | ¥{high:.2f} | **最低价** | ¥{low:.2f} |
| **成交量** | {volume:,.0f} 手 | **成交额** | {amount:.2f} 亿 | **换手率** | {turnover:.2f}% |
| **振幅** | {amplitude:.2f}% | **量比** | {quote.get('volume_ratio', '-')} | **市盈率** | {quote.get('pe', '-')} |

### 1.2 技术走势分析

{trend_analysis}

### 1.3 关键价位

| 价位类型 | 价格 | 说明 |
|:---------|:-----|:-----|
| **当日支撑** | ¥{low:.2f} | 日内最低点 |
| **当日阻力** | ¥{high:.2f} | 日内最高点 |
| **开盘价** | ¥{open_p:.2f} | 多空分水岭 |"""
    
    def _analyze_trend_detailed(self, pct_change: float, volume: float, amplitude: float) -> str:
        """详细走势分析"""
        analysis = []
        
        # 涨跌分析
        if pct_change > 7:
            analysis.append("📈 **强势上涨**：涨幅超过7%，多头力量强劲，可能受重大利好消息刺激")
        elif pct_change > 4:
            analysis.append("📈 **明显上涨**：涨幅4-7%，走势积极，市场认可度较高")
        elif pct_change > 2:
            analysis.append("📈 **温和上涨**：涨幅2-4%，稳步上行，趋势健康")
        elif pct_change > 0:
            analysis.append("📊 **小幅上涨**：涨幅0-2%，上涨动能一般")
        elif pct_change > -2:
            analysis.append("📊 **小幅回调**：跌幅0-2%，正常波动范围")
        elif pct_change > -4:
            analysis.append("📉 **温和回调**：跌幅2-4%，需关注支撑位承接力度")
        elif pct_change > -7:
            analysis.append("📉 **明显下跌**：跌幅4-7%，空头占优，谨慎观望")
        else:
            analysis.append("📉 **大幅下跌**：跌幅超过7%，恐慌情绪蔓延，建议避险")
        
        # 振幅分析
        if amplitude > 7:
            analysis.append("⚡ **高波动**：日内振幅超过7%，多空分歧激烈，短线操作机会与风险并存")
        elif amplitude > 4:
            analysis.append("📊 **中等波动**：日内振幅4-7%，正常交易波动")
        else:
            analysis.append("💤 **低波动**：日内振幅小于4%，市场观望情绪较浓")
        
        # 成交量分析
        if volume > 2000000:
            analysis.append("💰 **成交活跃**：成交量显著放大，资金参与度高，趋势可信度强")
        elif volume > 800000:
            analysis.append("💰 **成交正常**：成交量处于正常水平")
        else:
            analysis.append("💤 **成交清淡**：成交量偏低，市场参与度不足，趋势持续性存疑")
        
        return '\n\n'.join(f"{i+1}. {a}" for i, a in enumerate(analysis))
    
    def _md_financial_analysis(self) -> str:
        """Markdown财务深度分析"""
        fundamental = self.data.get('fundamental', {})
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        
        if not latest:
            return "## 💼 二、财务深度分析\n\n> 暂无财务数据"
        
        report_date = latest.get('report_date', 'N/A')
        revenue_yoy = latest.get('revenue_yoy', 'N/A')
        profit_yoy = latest.get('net_profit_yoy', 'N/A')
        roe = latest.get('roe', 'N/A')
        gross_margin = latest.get('gross_margin', 'N/A')
        net_margin = latest.get('net_margin', 'N/A')
        debt_ratio = latest.get('debt_ratio', 'N/A')
        eps = latest.get('eps', 'N/A')
        ocf_ps = latest.get('ocf_ps', 'N/A')
        
        # 财务质量深度分析
        quality_analysis = self._analyze_financial_quality_detailed(latest)
        
        # 趋势解读
        trend_analysis = self._interpret_financial_trend(revenue_yoy, profit_yoy, roe)
        
        return f"""## 💼 二、财务深度分析

### 2.1 核心财务数据（报告期：{report_date}）

#### 利润表关键指标

| 指标 | 数值 | 同比变化 | 指标 | 数值 | 健康度 |
|:-----|:-----|:---------|:-----|:-----|:-------|
| **营业收入** | - | {revenue_yoy} | **毛利率** | {gross_margin} | {self._rate_indicator(gross_margin, 30, 20)} |
| **净利润** | - | {profit_yoy} | **净利率** | {net_margin} | {self._rate_indicator(net_margin, 15, 8)} |
| **ROE** | {roe} | - | **资产负债率** | {debt_ratio} | {self._rate_debt(debt_ratio)} |
| **每股收益** | {eps} 元 | - | **每股现金流** | {ocf_ps} 元 | - |

### 2.2 财务质量深度评估

{quality_analysis}

### 2.3 营收与利润趋势解读

{trend_analysis}

### 2.4 业务板块分析

基于财务数据分析，公司业务呈现以下特征：

**主营业务**：核心业务保持稳定发展，市场地位稳固
**成长能力**：{self._growth_assessment(revenue_yoy, profit_yoy)}
**盈利能力**：{self._profitability_assessment(roe, net_margin)}
**财务健康**：{self._health_assessment(debt_ratio)}
**现金流**：{self._cashflow_assessment(ocf_ps, eps)}"""
    
    def _rate_indicator(self, value: str, good_threshold: float, fair_threshold: float) -> str:
        """评级指标"""
        try:
            val = float(str(value).replace('%', ''))
            if val >= good_threshold:
                return "🟢 优秀"
            elif val >= fair_threshold:
                return "🟡 良好"
            else:
                return "🔴 一般"
        except:
            return "⚪ 待评估"
    
    def _rate_debt(self, value: str) -> str:
        """评级负债率"""
        try:
            val = float(str(value).replace('%', ''))
            if val < 40:
                return "🟢 稳健"
            elif val < 60:
                return "🟡 适中"
            else:
                return "🔴 偏高"
        except:
            return "⚪ 待评估"
    
    def _analyze_financial_quality_detailed(self, latest: Dict) -> str:
        """详细财务质量分析"""
        analyses = []
        
        # ROE分析
        roe = latest.get('roe', '')
        if roe and '%' in str(roe):
            try:
                roe_val = float(str(roe).replace('%', ''))
                if roe_val > 20:
                    analyses.append(f"🟢 **盈利能力卓越**：ROE为{roe}，远超20%的优秀线，股东回报能力突出")
                elif roe_val > 15:
                    analyses.append(f"🟢 **盈利能力优秀**：ROE为{roe}，高于15%良好线，盈利质量较高")
                elif roe_val > 10:
                    analyses.append(f"🟡 **盈利能力良好**：ROE为{roe}，处于10-15%区间，盈利稳定")
                else:
                    analyses.append(f"🔴 **盈利能力一般**：ROE为{roe}，低于10%，需关注盈利改善")
            except:
                pass
        
        # 毛利率分析
        margin = latest.get('gross_margin', '')
        if margin and '%' in str(margin):
            try:
                margin_val = float(str(margin).replace('%', ''))
                if margin_val > 40:
                    analyses.append(f"🟢 **产品竞争力强**：毛利率{margin}，产品议价能力突出")
                elif margin_val > 25:
                    analyses.append(f"🟡 **产品竞争力良好**：毛利率{margin}，处于行业中上水平")
                else:
                    analyses.append(f"⚪ **产品竞争力一般**：毛利率{margin}，行业竞争激烈")
            except:
                pass
        
        # 负债率分析
        debt = latest.get('debt_ratio', '')
        if debt and '%' in str(debt):
            try:
                debt_val = float(str(debt).replace('%', ''))
                if debt_val < 35:
                    analyses.append(f"🟢 **财务结构稳健**：资产负债率{debt}，财务风险低，融资空间大")
                elif debt_val < 50:
                    analyses.append(f"🟡 **财务结构适中**：资产负债率{debt}，处于合理区间")
                elif debt_val < 65:
                    analyses.append(f"⚪ **财务杠杆较高**：资产负债率{debt}，需关注偿债能力")
                else:
                    analyses.append(f"🔴 **财务风险较高**：资产负债率{debt}，超过警戒线，谨慎关注")
            except:
                pass
        
        # 净利率分析
        net_margin = latest.get('net_margin', '')
        if net_margin and '%' in str(net_margin):
            try:
                nm_val = float(str(net_margin).replace('%', ''))
                if nm_val > 15:
                    analyses.append(f"🟢 **费用控制优秀**：净利率{net_margin}，成本管控能力强")
                elif nm_val > 8:
                    analyses.append(f"🟡 **费用控制良好**：净利率{net_margin}，运营效率正常")
                else:
                    analyses.append(f"⚪ **费用控制一般**：净利率{net_margin}，存在费用优化空间")
            except:
                pass
        
        return '\n\n'.join(f"{i+1}. {a}" for i, a in enumerate(analyses)) if analyses else "财务指标处于正常区间，整体财务状况稳健。"
    
    def _interpret_financial_trend(self, revenue: str, profit: str, roe: str) -> str:
        """解读财务趋势"""
        interpretations = []
        
        try:
            rev_val = float(str(revenue).replace('%', ''))
            prof_val = float(str(profit).replace('%', ''))
            
            # 营收分析
            if rev_val > 30:
                interpretations.append(f"📈 **营收高速增长**：同比增长{revenue}，业务扩张迅速，市场份额持续提升")
            elif rev_val > 15:
                interpretations.append(f"📈 **营收稳健增长**：同比增长{revenue}，增长势头良好，业务发展健康")
            elif rev_val > 5:
                interpretations.append(f"📊 **营收温和增长**：同比增长{revenue}，增速放缓但仍有增长")
            elif rev_val > 0:
                interpretations.append(f"📊 **营收微增**：同比增长{revenue}，增长乏力，需关注业务动力")
            else:
                interpretations.append(f"📉 **营收下滑**：同比下降{revenue}，业务承压，需警惕经营风险")
            
            # 利润分析
            if prof_val > 50:
                interpretations.append(f"🚀 **利润爆发增长**：同比增长{profit}，盈利能力大幅提升，经营效率显著改善")
            elif prof_val > 25:
                interpretations.append(f"📈 **利润高速增长**：同比增长{profit}，盈利质量良好，增长可持续性强")
            elif prof_val > 10:
                interpretations.append(f"📈 **利润稳健增长**：同比增长{profit}，盈利稳定，经营健康")
            elif prof_val > 0:
                interpretations.append(f"📊 **利润微增**：同比增长{profit}，增速放缓，关注成本端压力")
            else:
                interpretations.append(f"📉 **利润下滑**：同比下降{profit}，盈利承压，需关注盈利能力变化")
            
            # 营收利润匹配度
            if rev_val > 0 and prof_val > rev_val * 1.5:
                interpretations.append("💡 **盈利质量提升**：利润增速显著高于营收增速，经营杠杆效应显现，费用控制有效")
            elif rev_val > 0 and prof_val < rev_val * 0.5:
                interpretations.append("⚠️ **盈利质量下降**：利润增速明显低于营收增速，成本费用压力增大")
            
        except:
            interpretations.append("财务趋势数据待更新")
        
        return '\n\n'.join(f"{i+1}. {a}" for i, a in enumerate(interpretations))
    
    def _growth_assessment(self, revenue: str, profit: str) -> str:
        """成长能力评估"""
        try:
            rev_val = float(str(revenue).replace('%', ''))
            prof_val = float(str(profit).replace('%', ''))
            if rev_val > 20 and prof_val > 20:
                return "高成长，营收利润双轮驱动"
            elif rev_val > 10 and prof_val > 10:
                return "稳健成长，发展势头良好"
            elif rev_val > 0 and prof_val > 0:
                return "温和成长，增速放缓"
            else:
                return "成长承压，需关注业务调整"
        except:
            return "成长数据待评估"
    
    def _profitability_assessment(self, roe: str, margin: str) -> str:
        """盈利能力评估"""
        try:
            roe_val = float(str(roe).replace('%', ''))
            if roe_val > 15:
                return "盈利能力强，ROE处于优秀水平"
            elif roe_val > 10:
                return "盈利能力良好，ROE稳定"
            else:
                return "盈利能力一般，ROE有提升空间"
        except:
            return "盈利数据待评估"
    
    def _health_assessment(self, debt: str) -> str:
        """财务健康评估"""
        try:
            debt_val = float(str(debt).replace('%', ''))
            if debt_val < 40:
                return "财务结构稳健，偿债能力强"
            elif debt_val < 60:
                return "财务结构适中，风险可控"
            else:
                return "财务杠杆较高，需关注风险"
        except:
            return "财务健康度待评估"
    
    def _cashflow_assessment(self, ocf: str, eps: str) -> str:
        """现金流评估"""
        try:
            ocf_val = float(str(ocf))
            eps_val = float(str(eps))
            if ocf_val > eps_val:
                return "现金流健康，盈利质量高"
            else:
                return "现金流一般，关注回款情况"
        except:
            return "现金流数据待评估"
    
    def _md_news_sentiment(self) -> str:
        """Markdown新闻与情绪分析"""
        news = self.data.get('news', {})
        
        if not news or 'error' in news:
            return "## 📰 三、新闻舆情与市场情绪\n\n> 暂无新闻数据"
        
        sentiment = news.get('sentiment', '中性')
        sentiment_score = news.get('sentiment_score', 0)
        items = news.get('items', [])
        fund_impact = news.get('fundamental_impact', '中性')
        
        # 市场情绪指数
        sentiment_index = 50
        sentiment_level = "中性"
        if self.pattern_data:
            sentiment_data = self.pattern_data.get('sentiment', {})
            sentiment_index = sentiment_data.get('index_value', 50)
            level = sentiment_data.get('level', {})
            sentiment_level = level.get('name', '中性') if isinstance(level, dict) else str(level)
        
        # 新闻列表
        news_analysis = []
        if items:
            for i, item in enumerate(items[:5], 1):
                title = item.get('title', '')
                date = item.get('date', '')
                # 简单情感判断
                sentiment_tag = ""
                if any(w in title for w in ['增长', '突破', '利好', '合作', '获奖', '订单']):
                    sentiment_tag = "🟢 正面"
                elif any(w in title for w in ['下滑', '亏损', '处罚', '诉讼', '减持', '风险']):
                    sentiment_tag = "🔴 负面"
                else:
                    sentiment_tag = "⚪ 中性"
                news_analysis.append(f"{i}. **{date}** | {sentiment_tag} | {title}")
        
        # 情绪解读
        sentiment_interpretation = self._interpret_sentiment_detailed(sentiment_index, sentiment_level)
        
        return f"""## 📰 三、新闻舆情与市场情绪

### 3.1 市场情绪指数

| 指标 | 数值 | 等级 | 交易信号 |
|:-----|:-----|:-----|:---------|
| **贪婪恐慌指数** | {sentiment_index:.1f}/100 | {sentiment_level} | {self._sentiment_signal(sentiment_index)} |
| **新闻情感倾向** | {sentiment} | 得分：{sentiment_score:+d} | - |
| **对基本面影响** | {fund_impact} | - | - |

### 3.2 最新财经新闻摘要

{chr(10).join(news_analysis) if news_analysis else '> 暂无最新新闻'}

### 3.3 市场情绪深度解读

{sentiment_interpretation}"""
    
    def _interpret_sentiment_detailed(self, index: float, level: str) -> str:
        """详细情绪解读"""
        if index < 15:
            return """🔴 **极度恐慌阶段**（指数<20）

市场情绪极度悲观，恐慌情绪蔓延，多数投资者选择抛售。历史数据显示，此阶段往往是中长期布局的较好时机，但需精选标的、控制仓位、分批建仓。建议关注被错杀的优质标的。"""
        elif index < 30:
            return """🟠 **恐慌阶段**（指数20-30）

市场情绪偏悲观，投资者信心不足，成交量萎缩。部分优质标的可能被低估，适合价值投资者逢低关注。建议保持耐心，等待情绪修复。"""
        elif index < 45:
            return """⚪ **谨慎阶段**（指数30-45）

市场情绪偏谨慎，投资者观望情绪浓厚。市场缺乏明确方向，建议控制仓位，等待更明确的信号出现。可关注结构性机会。"""
        elif index < 55:
            return """⚪ **中性阶段**（指数45-55）

市场情绪平稳，多空力量相对均衡。建议按常规策略操作，精选个股，控制仓位在正常水平。"""
        elif index < 70:
            return """🟢 **乐观阶段**（指数55-70）

市场情绪偏乐观，投资者信心回升，资金活跃度提高。可适当参与，但需注意追高风险，设置好止损位。"""
        elif index < 85:
            return """🟢 **贪婪阶段**（指数70-85）

市场情绪高涨，投资者风险偏好提升，成交量放大。需警惕追高风险，建议逐步减仓，锁定利润。"""
        else:
            return """🔵 **极度贪婪阶段**（指数>85）

市场情绪狂热，投资者普遍乐观，风险积累。历史数据显示，此阶段往往是市场顶部区域，建议大幅减仓，规避风险。"""
    
    def _sentiment_signal(self, index: float) -> str:
        """情绪交易信号"""
        if index < 20:
            return "逆向买入"
        elif index < 40:
            return "逢低关注"
        elif index < 60:
            return "正常操作"
        elif index < 80:
            return "谨慎持有"
        else:
            return "逐步减仓"
    
    def _md_technical_analysis(self) -> str:
        """Markdown技术指标深度分析"""
        tech = self.data.get('technical', {})
        if not tech or 'error' in tech:
            return "## 📊 四、技术指标深度解析\n\n> 暂无技术指标数据"
        
        k = tech.get('k', 0)
        d = tech.get('d', 0)
        j = tech.get('j', 0)
        kdj_signal = tech.get('kdj_signal', '正常')
        macd = tech.get('macd', 0)
        macd_signal = tech.get('macd_signal', '盘整')
        histogram = tech.get('histogram', 0)
        rsi = tech.get('rsi', 0)
        rsi_signal = tech.get('rsi_signal', '正常')
        
        # 详细分析
        kdj_detail = self._analyze_kdj_detailed(k, d, j, kdj_signal)
        macd_detail = self._analyze_macd_detailed(macd, macd_signal, histogram)
        rsi_detail = self._analyze_rsi_detailed(rsi, rsi_signal)
        
        return f"""## 📊 四、技术指标深度解析

### 4.1 KDJ随机指标分析

| 指标 | 数值 | 状态 | 信号 |
|:-----|:-----|:-----|:-----|
| **K值** | {k:.2f} | {'超买区' if k > 80 else '超卖区' if k < 20 else '正常区'} | - |
| **D值** | {d:.2f} | {'超买区' if d > 80 else '超卖区' if d < 20 else '正常区'} | - |
| **J值** | {j:.2f} | {'极强' if j > 100 else '极弱' if j < 0 else '正常'} | - |
| **KDJ信号** | {kdj_signal} | {self._kdj_status(kdj_signal)} | {self._kdj_recommendation(kdj_signal)} |

#### KDJ深度解读

{kdj_detail}

### 4.2 MACD趋势指标分析

| 指标 | 数值 | 状态 | 信号 |
|:-----|:-----|:-----|:-----|
| **DIF** | {macd:.3f} | {'零轴上' if macd > 0 else '零轴下'} | - |
| **MACD柱状** | {histogram:.3f} | {'扩张' if abs(histogram) > 0.1 else '收缩'} | - |
| **MACD信号** | {macd_signal} | {self._macd_status(macd_signal)} | {self._macd_recommendation(macd_signal)} |

#### MACD深度解读

{macd_detail}

### 4.3 RSI相对强弱指标分析

| 指标 | 数值 | 状态 | 信号 |
|:-----|:-----|:-----|:-----|
| **RSI(14)** | {rsi:.2f} | {rsi_signal} | {self._rsi_recommendation(rsi)} |

#### RSI深度解读

{rsi_detail}

### 4.4 均线系统分析

| 均线 | 价格 | 与现价关系 | 技术意义 |
|:-----|:-----|:-----------|:---------|
| MA5 | ¥{tech.get('ma5', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma5') else '❌ 下方'} | 短期趋势{'向上' if tech.get('price_above_ma5') else '向下'} |
| MA10 | ¥{tech.get('ma10', 0):.2f} | - | 短期支撑/阻力 |
| MA20 | ¥{tech.get('ma20', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma20') else '❌ 下方'} | 中期趋势{'向上' if tech.get('price_above_ma20') else '向下'} |
| MA60 | ¥{tech.get('ma60', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma60') else '❌ 下方'} | 长期趋势{'向上' if tech.get('price_above_ma60') else '向下'} |

**综合趋势判断**：{tech.get('trend', '震荡')}"""
    
    def _analyze_kdj_detailed(self, k: float, d: float, j: float, signal: str) -> str:
        """详细KDJ分析"""
        analysis = []
        
        if '金叉' in signal:
            analysis.append(f"🟢 **金叉买入信号**：K线({k:.2f})上穿D线({d:.2f})，短期动能转强。")
            if k < 50:
                analysis.append("金叉发生在50以下低位，属于低位金叉，信号可靠性较高，建议关注买入机会。")
            else:
                analysis.append("金叉发生在50以上，属于高位金叉，需结合其他指标确认。")
        elif '死叉' in signal:
            analysis.append(f"🔴 **死叉卖出信号**：K线({k:.2f})下穿D线({d:.2f})，短期动能转弱。")
            if k > 50:
                analysis.append("死叉发生在50以上高位，属于高位死叉，调整风险较大，建议谨慎。")
            else:
                analysis.append("死叉发生在50以下，属于低位死叉，可能是最后一跌，关注企稳信号。")
        
        if j > 100:
            analysis.append(f"⚠️ **J值超买**：J值高达{j:.2f}，进入极强区域，短期超买严重，需警惕回调风险。")
        elif j < 0:
            analysis.append(f"💡 **J值超卖**：J值低至{j:.2f}，进入极弱区域，短期超卖严重，可能存在反弹机会。")
        
        if k > 80 and d > 80:
            analysis.append("K、D值均处于80以上超买区，短期上涨动能可能衰竭，建议逢高减仓。")
        elif k < 20 and d < 20:
            analysis.append("K、D值均处于20以下超卖区，短期下跌动能可能衰竭，建议关注反弹机会。")
        
        return '\n\n'.join(analysis) if analysis else "KDJ指标处于正常波动区间，暂无明确信号。"
    
    def _analyze_macd_detailed(self, macd: float, signal: str, histogram: float) -> str:
        """详细MACD分析"""
        analysis = []
        
        if '多头' in signal:
            analysis.append(f"🟢 **多头趋势**：DIF({macd:.3f})处于零轴上方，中长期趋势向上。")
            if histogram > 0.1:
                analysis.append(f"红柱扩张({histogram:.3f})，上涨动能强劲，趋势健康。")
            elif histogram > 0:
                analysis.append(f"红柱收缩({histogram:.3f})，上涨动能减弱，需关注趋势变化。")
        elif '空头' in signal:
            analysis.append(f"🔴 **空头趋势**：DIF({macd:.3f})处于零轴下方，中长期趋势向下。")
            if histogram < -0.1:
                analysis.append(f"绿柱扩张({histogram:.3f})，下跌动能强劲，趋势偏弱。")
            elif histogram < 0:
                analysis.append(f"绿柱收缩({histogram:.3f})，下跌动能减弱，可能企稳。")
        else:
            analysis.append(f"⚪ **盘整趋势**：DIF({macd:.3f})接近零轴，多空力量均衡，趋势不明。")
        
        # 柱状图变化
        if histogram > 0 and abs(histogram) < 0.05:
            analysis.append("柱状图接近零轴，多空力量即将转换，关注方向选择。")
        
        return '\n\n'.join(analysis)
    
    def _analyze_rsi_detailed(self, rsi: float, signal: str) -> str:
        """详细RSI分析"""
        analysis = []
        
        if rsi > 80:
            analysis.append(f"🔴 **严重超买**：RSI高达{rsi:.2f}，远超80超买线，短期回调风险极大。")
        elif rsi > 70:
            analysis.append(f"🟠 **超买区域**：RSI为{rsi:.2f}，进入70-80超买区，上涨空间有限。")
        elif rsi > 50:
            analysis.append(f"🟢 **强势区域**：RSI为{rsi:.2f}，处于50-70强势区，多头占优。")
        elif rsi > 30:
            analysis.append(f"⚪ **弱势区域**：RSI为{rsi:.2f}，处于30-50弱势区，空头占优。")
        elif rsi > 20:
            analysis.append(f"🟠 **超卖区域**：RSI为{rsi:.2f}，进入20-30超卖区，下跌空间有限。")
        else:
            analysis.append(f"🟢 **严重超卖**：RSI低至{rsi:.2f}，低于20超卖线，短期反弹概率大。")
        
        return '\n\n'.join(analysis)
    
    def _kdj_status(self, signal: str) -> str:
        """KDJ状态"""
        if '金叉' in signal:
            return "买入信号"
        elif '死叉' in signal:
            return "卖出信号"
        elif '超买' in signal:
            return "超买区域"
        elif '超卖' in signal:
            return "超卖区域"
        return "正常波动"
    
    def _kdj_recommendation(self, signal: str) -> str:
        """KDJ建议"""
        if '金叉' in signal:
            return "关注买入"
        elif '死叉' in signal:
            return "考虑减仓"
        elif '超买' in signal:
            return "谨慎追高"
        elif '超卖' in signal:
            return "关注反弹"
        return "观望"
    
    def _macd_status(self, signal: str) -> str:
        """MACD状态"""
        if '多头' in signal:
            return "多头市场"
        elif '空头' in signal:
            return "空头市场"
        return "盘整市场"
    
    def _macd_recommendation(self, signal: str) -> str:
        """MACD建议"""
        if '多头' in signal:
            return "趋势向上"
        elif '空头' in signal:
            return "趋势向下"
        return "等待方向"
    
    def _rsi_recommendation(self, rsi: float) -> str:
        """RSI建议"""
        if rsi > 70:
            return "谨慎"
        elif rsi < 30:
            return "关注"
        return "正常"
    
    def _md_pattern_analysis_enhanced(self) -> str:
        """Markdown形态面分析（重点强化版）"""
        if not self.pattern_data:
            return ""
        
        sections = []
        
        # 1. K线形态识别结果（详细版）
        candlestick = self.pattern_data.get('candlestick', {})
        if candlestick:
            sections.append(self._md_candlestick_section(candlestick))
        
        # 2. 缠论结构分析
        chanlun = self.pattern_data.get('chanlun', {})
        if chanlun:
            sections.append(self._md_chanlun_section(chanlun))
        
        # 3. 买卖点信号系统
        if chanlun:
            sections.append(self._md_buysell_points_section(chanlun))
        
        # 4. 信号共振评分（详细版）
        resonance = self.pattern_data.get('resonance', {})
        if resonance:
            sections.append(self._md_resonance_section(resonance))
        
        content = '\n\n'.join(sections)
        
        return f"""## 📐 五、形态面专业分析【核心板块】

> **形态面分析是本报告的核心特色**，整合K线形态识别、缠论结构分析、买卖点识别、信号共振评分四大模块，提供全方位的技术分析视角。

{content}"""
    
    def _md_candlestick_section(self, candlestick: Dict) -> str:
        """K线形态识别详细板块"""
        patterns = candlestick.get('patterns', [])
        bullish_count = candlestick.get('bullish_count', 0)
        bearish_count = candlestick.get('bearish_count', 0)
        bullish_score = candlestick.get('bullish_score', 0)
        bearish_score = candlestick.get('bearish_score', 0)
        signal = candlestick.get('signal', '中性')
        
        # 形态详情表格
        pattern_details = []
        for i, p in enumerate(patterns[:8], 1):
            emoji = "🟢" if p.get('type') == 'bullish' else "🔴" if p.get('type') == 'bearish' else "⚪"
            reliability_stars = '⭐' * p.get('reliability', 0) + '☆' * (5 - p.get('reliability', 0))
            pattern_details.append(
                f"| {i} | {emoji} {p.get('name_cn', 'N/A')} | {p.get('type_cn', 'N/A')} | "
                f"{reliability_stars} | {p.get('confidence', 0):.1%} | {p.get('position', 0)} |"
            )
        
        # 看涨形态列表
        bullish_patterns = [p for p in patterns if p.get('type') == 'bullish'][:3]
        bearish_patterns = [p for p in patterns if p.get('type') == 'bearish'][:3]
        
        bullish_list = '\n'.join([
            f"- **{p.get('name_cn')}**（可靠性{p.get('reliability')}/5，置信度{p.get('confidence'):.1%}）：{p.get('description', '看涨信号')}"
            for p in bullish_patterns
        ]) if bullish_patterns else "- 暂无主要看涨形态"
        
        bearish_list = '\n'.join([
            f"- **{p.get('name_cn')}**（可靠性{p.get('reliability')}/5，置信度{p.get('confidence'):.1%}）：{p.get('description', '看跌信号')}"
            for p in bearish_patterns
        ]) if bearish_patterns else "- 暂无主要看跌形态"
        
        return f"""### 5.1 K线形态识别结果

#### 形态统计概览

| 统计项 | 数值 | 说明 |
|:-------|:-----|:-----|
| **识别形态总数** | {len(patterns)} 个 | 近5个交易日 |
| **看涨形态** | {bullish_count} 个 | 看涨得分：{bullish_score:.1f} |
| **看跌形态** | {bearish_count} 个 | 看跌得分：{bearish_score:.1f} |
| **综合信号** | {signal} | 形态面整体判断 |

#### 形态识别详情

| 序号 | 形态名称 | 形态类型 | 可靠性 | 置信度 | 出现位置 |
|:-----|:---------|:---------|:-------|:-------|:---------|
{chr(10).join(pattern_details) if pattern_details else '| - | - | - | - | - | - |'}

#### 主要看涨形态解读

{bullish_list}

#### 主要看跌形态解读

{bearish_list}

#### 形态综合分析

基于{candlestick.get('total_patterns', len(patterns))}种形态识别结果，形态面呈现**{signal}**信号。看涨形态{bullish_count}个，看跌形态{bearish_count}个，净看涨得分{bullish_score - bearish_score:+.1f}分。

**形态策略建议**：{self._pattern_strategy(signal, bullish_count, bearish_count)}"""
    
    def _pattern_strategy(self, signal: str, bullish: int, bearish: int) -> str:
        """形态策略建议"""
        if '强烈看涨' in signal or bullish >= 3:
            return "多个看涨形态共振，技术面支撑较强，建议积极关注买入机会。"
        elif '看涨' in signal or bullish > bearish:
            return "看涨形态占优，技术面偏正面，可考虑适量参与。"
        elif '强烈看跌' in signal or bearish >= 3:
            return "多个看跌形态共振，技术面压力较大，建议谨慎观望。"
        elif '看跌' in signal or bearish > bullish:
            return "看跌形态占优，技术面偏负面，建议控制仓位。"
        else:
            return "多空形态均衡，技术面信号混杂，建议等待更明确的形态信号。"
    
    def _md_chanlun_section(self, chanlun: Dict) -> str:
        """缠论结构分析板块"""
        bi_count = chanlun.get('bi_count', 0)
        zhongshu_count = chanlun.get('zhongshu_count', 0)
        current_trend = chanlun.get('current_trend', '未知')
        
        # 最近中枢
        nearest_zs = chanlun.get('nearest_zhongshu', {})
        zs_info = ""
        if nearest_zs:
            zs_info = f"""
#### 最近中枢详情

| 属性 | 数值 | 说明 |
|:-----|:-----|:-----|
| **中枢区间** | {nearest_zs.get('range', 'N/A')} | 价格波动中枢 |
| **ZG（中枢高点）** | {nearest_zs.get('zg', 'N/A')} | 中枢上沿，阻力位 |
| **ZD（中枢低点）** | {nearest_zs.get('zd', 'N/A')} | 中枢下沿，支撑位 |
| **中枢中心** | {nearest_zs.get('center', 'N/A')} | 多空平衡价位 |

**中枢意义**：当前中枢为价格提供了明确的支撑和阻力参考。价格在中枢上方运行偏强，在中枢下方运行偏弱。突破中枢上沿可能开启新一轮上涨，跌破中枢下沿可能加速下跌。
"""
        
        # 笔的详情
        bis = chanlun.get('bis', [])
        bi_details = ""
        if bis:
            bi_details = "#### 笔结构详情\n\n| 序号 | 方向 | 起点价格 | 终点价格 | 幅度 |\n|:-----|:-----|:---------|:---------|:-----|\n"
            for i, bi in enumerate(bis[-5:], 1):
                direction = "📈 向上" if bi.get('direction') == 'up' else "📉 向下"
                bi_details += f"| {i} | {direction} | {bi.get('start_price', 0):.2f} | {bi.get('end_price', 0):.2f} | {bi.get('height', 0):.2f} |\n"
        
        return f"""### 5.2 缠论结构分析

#### 缠论核心要素

| 要素 | 数值 | 技术含义 |
|:-----|:-----|:---------|
| **笔数量** | {bi_count} 笔 | 价格走势的基本单位 |
| **中枢数量** | {zhongshu_count} 个 | 价格密集成交区 |
| **当前趋势** | {current_trend} | 当前笔的运行方向 |

{zs_info}

{bi_details}

#### 缠论结构解读

基于缠论分析，当前走势呈现以下特征：

1. **笔结构**：共识别出{bi_count}笔，构成完整的价格走势结构
2. **中枢分布**：{zhongshu_count}个中枢形成，为价格提供支撑阻力参考
3. **当前状态**：{current_trend}，趋势方向明确

**缠论视角建议**：{self._chanlun_advice(current_trend, zhongshu_count)}"""
    
    def _chanlun_advice(self, trend: str, zs_count: int) -> str:
        """缠论建议"""
        if '向上' in trend and zs_count > 0:
            return "当前处于向上笔运行中，且有中枢支撑，趋势较为健康。关注是否形成背驰信号。"
        elif '向下' in trend and zs_count > 0:
            return "当前处于向下笔运行中，关注是否接近中枢下沿或形成买点信号。"
        elif '向上' in trend:
            return "向上笔运行中，但中枢结构尚不明确，需关注后续中枢形成情况。"
        elif '向下' in trend:
            return "向下笔运行中，建议等待企稳信号或买点确认后再考虑介入。"
        else:
            return "趋势方向尚不明确，建议等待笔结构进一步清晰。"
    
    def _md_buysell_points_section(self, chanlun: Dict) -> str:
        """买卖点信号系统板块"""
        buy_points = chanlun.get('buy_points', [])
        sell_points = chanlun.get('sell_points', [])
        
        # 买点详情
        buy_details = []
        for i, bp in enumerate(buy_points, 1):
            bp_type = bp.get('type', 'N/A')
            price = bp.get('price', 0)
            confidence = bp.get('confidence', 0)
            description = bp.get('description', '')
            
            # 买点级别
            level = ""
            if '一买' in bp_type:
                level = "🥇 一级买点（最强）"
            elif '二买' in bp_type:
                level = "🥈 二级买点（较强）"
            elif '三买' in bp_type:
                level = "🥉 三级买点（一般）"
            
            buy_details.append(
                f"| {i} | 🎯 {bp_type} | {level} | ¥{price:.2f} | {confidence:.1%} | {description[:30]}... |"
            )
        
        # 卖点详情
        sell_details = []
        for i, sp in enumerate(sell_points, 1):
            sp_type = sp.get('type', 'N/A')
            price = sp.get('price', 0)
            confidence = sp.get('confidence', 0)
            description = sp.get('description', '')
            
            level = ""
            if '一卖' in sp_type:
                level = "🥇 一级卖点（最强）"
            elif '二卖' in sp_type:
                level = "🥈 二级卖点（较强）"
            elif '三卖' in sp_type:
                level = "🥉 三级卖点（一般）"
            
            sell_details.append(
                f"| {i} | 🔻 {sp_type} | {level} | ¥{price:.2f} | {confidence:.1%} | {description[:30]}... |"
            )
        
        # 买卖点说明
        buy_sell_guide = """
#### 买卖点级别说明

| 级别 | 买点 | 卖点 | 特征 |
|:-----|:-----|:-----|:-----|
| **一级** | 一买 | 一卖 | 趋势转折点，信号最强，成功率最高 |
| **二级** | 二买 | 二卖 | 回撤确认点，信号较强，风险相对较小 |
| **三级** | 三买 | 三卖 | 突破确认点，信号一般，需结合其他指标 |

**注意**：缠论买卖点基于算法自动识别，仅供参考。实际交易中需结合市场环境、资金管理等因素综合判断。
"""
        
        return f"""### 5.3 买卖点信号系统

#### 识别到的买点

| 序号 | 买点类型 | 级别 | 价格 | 置信度 | 说明 |
|:-----|:---------|:-----|:-----|:-------|:-----|
{chr(10).join(buy_details) if buy_details else '| - | - | - | - | - | - |'}

#### 识别到的卖点

| 序号 | 卖点类型 | 级别 | 价格 | 置信度 | 说明 |
|:-----|:---------|:-----|:-----|:-------|:-----|
{chr(10).join(sell_details) if sell_details else '| - | - | - | - | - | - |'}

{buy_sell_guide}

#### 当前买卖点策略

{self._buysell_strategy(buy_points, sell_points)}"""
    
    def _buysell_strategy(self, buy_points: List, sell_points: List) -> str:
        """买卖点策略"""
        if buy_points and not sell_points:
            bp = buy_points[-1]
            return f"当前识别到**{bp.get('type')}**信号，价格¥{bp.get('price', 0):.2f}，置信度{bp.get('confidence', 0):.1%}。建议关注该价位附近的买入机会，设置止损于该买点下方3-5%。"
        elif sell_points and not buy_points:
            sp = sell_points[-1]
            return f"当前识别到**{sp.get('type')}**信号，价格¥{sp.get('price', 0):.2f}，置信度{sp.get('confidence', 0):.1%}。建议关注该价位附近的卖出/减仓机会。"
        elif buy_points and sell_points:
            return f"当前同时存在买点和卖点信号，市场处于震荡格局。建议根据持仓情况灵活操作：接近买点可加仓，接近卖点可减仓，区间内可高抛低吸。"
        else:
            return "当前暂无明确的买卖点信号，建议等待缠论结构进一步清晰后再做决策。"
    
    def _md_resonance_section(self, resonance: Dict) -> str:
        """信号共振评分详细板块"""
        total_score = resonance.get('total_score', 0)
        bullish_score = resonance.get('bullish_score', 0)
        bearish_score = resonance.get('bearish_score', 0)
        signal_count = resonance.get('signal_count', 0)
        breakdown = resonance.get('breakdown', {})
        
        # 共振级别
        resonance_level, res_emoji, res_desc = self._get_resonance_level(total_score)
        
        # 维度得分详情
        dimension_details = []
        dimension_names = {
            'K线形态': 'K线形态',
            '技术指标': '技术指标',
            '趋势信号': '趋势信号',
            '成交量': '成交量',
            '基本面': '基本面',
            '情绪面': '情绪面',
            '缠论': '缠论'
        }
        
        for dim_key, score in breakdown.items():
            dim_name = dimension_names.get(dim_key, dim_key)
            direction = "看涨" if score > 0 else "看跌" if score < 0 else "中性"
            strength = abs(score)
            bar = "█" * int(strength / 5) + "░" * (20 - int(strength / 5))
            dimension_details.append(f"| {dim_name} | {direction} | {score:+.1f} | {bar} |")
        
        # 看涨信号列表
        bullish_signals = resonance.get('bullish_signals', [])
        bullish_list = '\n'.join([
            f"{i+1}. **{s.get('signal_type', '信号')}**：{s.get('description', '')}"
            for i, s in enumerate(bullish_signals[:5])
        ]) if bullish_signals else "- 暂无主要看涨信号"
        
        # 看跌信号列表
        bearish_signals = resonance.get('bearish_signals', [])
        bearish_list = '\n'.join([
            f"{i+1}. **{s.get('signal_type', '信号')}**：{s.get('description', '')}"
            for i, s in enumerate(bearish_signals[:5])
        ]) if bearish_signals else "- 暂无主要看跌信号"
        
        return f"""### 5.4 信号共振评分系统

#### 共振评分概览

<div align="center">

### {res_emoji} 共振级别：{resonance_level}

**综合评分**：{total_score:+.1f}/100 | **看涨得分**：{bullish_score:.1f} | **看跌得分**：{bearish_score:.1f} | **信号总数**：{signal_count} 个

*{res_desc}*

</div>

#### 七维度评分详情

| 维度 | 方向 | 得分 | 强度可视化 |
|:-----|:-----|:-----|:-----------|
{chr(10).join(dimension_details) if dimension_details else '| - | - | - | - |'}

#### 看涨信号明细

{bullish_list}

#### 看跌信号明细

{bearish_list}

#### 共振分析结论

{self._resonance_conclusion(total_score, bullish_score, bearish_score, signal_count)}"""
    
    def _resonance_conclusion(self, total: float, bullish: float, bearish: float, count: int) -> str:
        """共振分析结论"""
        abs_score = abs(total)
        
        if abs_score >= 75:
            direction = "强烈看涨" if total > 0 else "强烈看跌"
            return f"🟢 **{direction}共振**：七维度信号高度一致，综合评分{total:+.1f}分，趋势确认度极高。{bullish:.1f}分看涨信号对{bearish:.1f}分看跌信号形成压倒性优势，建议积极跟进趋势方向。"
        elif abs_score >= 50:
            direction = "看涨" if total > 0 else "看跌"
            return f"🟡 **{direction}共振**：多数维度信号同向，综合评分{total:+.1f}分，趋势较为明确。看涨得分{bullish:.1f}分，看跌得分{bearish:.1f}分，建议顺势而为。"
        elif abs_score >= 25:
            direction = "弱看涨" if total > 0 else "弱看跌"
            return f"⚪ **{direction}共振**：部分维度信号同向，综合评分{total:+.1f}分，趋势初步显现但需确认。建议控制仓位，等待更明确的信号。"
        else:
            return f"⚫ **无共振**：各维度信号分散，综合评分{total:+.1f}分，多空力量均衡。看涨{bullish:.1f}分 vs 看跌{bearish:.1f}分，建议观望等待方向选择。"
    
    def _md_investment_advice(self) -> str:
        """Markdown综合投资建议"""
        action = self.suggestion.get('action', '观望')
        target_price = self.suggestion.get('target_price', 0)
        stop_loss = self.suggestion.get('stop_loss', 0)
        position = self.suggestion.get('position', '10%')
        
        quote = self.data.get('quote', {})
        current_price = quote.get('price', 0)
        
        # 计算盈亏比
        if current_price > 0 and target_price > 0 and stop_loss > 0:
            upside = (target_price - current_price) / current_price * 100
            downside = (current_price - stop_loss) / current_price * 100
            risk_reward = upside / downside if downside > 0 else 0
        else:
            upside = downside = risk_reward = 0
        
        return f"""## 🎯 六、综合投资决策建议

### 6.1 投资决策总览

<div align="center">

### {self.rating_emoji} {self.rating} | 综合评分：{self.total_score}/100

**操作建议**：{action} | **目标价**：¥{target_price:.2f} | **止损价**：¥{stop_loss:.2f}

</div>

### 6.2 关键价位与盈亏分析

| 价位类型 | 价格 | 涨跌幅 | 说明 |
|:---------|:-----|:-------|:-----|
| **当前价格** | ¥{current_price:.2f} | - | 基准价位 |
| **目标价格** | ¥{target_price:.2f} | +{upside:.1f}% | 预期上涨空间 |
| **止损价格** | ¥{stop_loss:.2f} | -{downside:.1f}% | 最大可承受亏损 |
| **盈亏比** | 1:{risk_reward:.1f} | - | {'🟢 优秀' if risk_reward >= 3 else '🟡 良好' if risk_reward >= 2 else '⚪ 一般' if risk_reward >= 1.5 else '🔴 较差'} |

### 6.3 核心投资优势

{self._generate_advantages_enhanced()}

### 6.4 主要风险因素

{self._generate_risks_enhanced()}

### 6.5 交易策略建议

#### 仓位管理
- **建议仓位**：{position}
- **建仓策略**：{self._position_strategy(self.total_score)}

#### 操作计划
{self._trading_plan(current_price, target_price, stop_loss)}

### 6.6 投资分析总结

{self._generate_summary_enhanced()}"""
    
    def _generate_advantages_enhanced(self) -> str:
        """生成增强版核心优势"""
        advantages = []
        
        # 技术面优势
        tech = self.data.get('technical', {})
        trend = tech.get('trend', '')
        kdj_signal = tech.get('kdj_signal', '')
        macd_signal = tech.get('macd_signal', '')
        
        if '上升' in trend:
            advantages.append("1. **技术面趋势向好**：均线系统多头排列，中长期趋势向上，技术支撑较强")
        if '金叉' in kdj_signal:
            advantages.append("2. **KDJ金叉信号**：短期动能转强，技术指标发出买入信号")
        if '多头' in macd_signal:
            advantages.append("3. **MACD多头格局**：DIF处于零轴上方，中长期趋势健康")
        
        # 基本面优势
        fundamental = self.data.get('fundamental', {})
        perf = fundamental.get('performance_trend', {})
        if '向好' in perf.get('overall_trend', ''):
            advantages.append("4. **基本面稳健**：业绩趋势向好，盈利能力稳定，具备基本面支撑")
        
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        try:
            roe_val = float(str(latest.get('roe', '0')).replace('%', ''))
            if roe_val > 15:
                advantages.append(f"5. **ROE优秀**：ROE达{latest.get('roe')}，股东回报能力突出")
        except:
            pass
        
        # 资金面优势
        money = self.data.get('money_flow', {})
        main_flow = money.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        if main_net > 0.5:
            advantages.append(f"6. **主力资金流入**：主力净流入{main_net:.2f}亿，资金面对股价形成支撑")
        
        # 形态面优势（重点）
        if self.pattern_data:
            candlestick = self.pattern_data.get('candlestick', {})
            if candlestick.get('bullish_count', 0) >= 2:
                advantages.append("7. **形态面看涨**：多个K线形态发出看涨信号，技术面支撑明显")
            
            chanlun = self.pattern_data.get('chanlun', {})
            if chanlun.get('buy_points', []):
                advantages.append("8. **缠论买点确认**：缠论结构识别出买点信号，提供精确入场参考")
            
            resonance = self.pattern_data.get('resonance', {})
            res_score = resonance.get('total_score', 0)
            if res_score > 50:
                advantages.append(f"9. **信号共振强劲**：七维度共振评分{res_score:+.1f}分，多维度信号高度一致")
        
        if not advantages:
            advantages.append("综合各维度分析，当前优势不明显，建议谨慎观察")
        
        return '\n'.join(advantages)
    
    def _generate_risks_enhanced(self) -> str:
        """生成增强版风险因素"""
        risks = []
        
        # 技术风险
        quote = self.data.get('quote', {})
        pct_change = quote.get('pct_change', 0)
        if pct_change > 7:
            risks.append("1. **追高风险**：今日涨幅超过7%，短期乖离率过大，存在回调压力")
        
        tech = self.data.get('technical', {})
        rsi = tech.get('rsi', 50)
        kdj_signal = tech.get('kdj_signal', '')
        
        if rsi > 70:
            risks.append(f"2. **技术指标超买**：RSI达{rsi:.1f}，进入超买区，短期调整风险增加")
        if '超买' in kdj_signal:
            risks.append("3. **KDJ超买信号**：KDJ指标显示超买，短期动能可能衰竭")
        
        # 基本面风险
        fundamental = self.data.get('fundamental', {})
        perf = fundamental.get('performance_trend', {})
        if '承压' in perf.get('overall_trend', ''):
            risks.append("4. **基本面压力**：业绩趋势承压，盈利能力存在下滑风险")
        
        # 消息风险
        news = self.data.get('news', {})
        if '利空' in news.get('fundamental_impact', ''):
            risks.append("5. **消息面风险**：近期消息面偏空，可能对股价形成压制")
        
        # 形态面风险
        if self.pattern_data:
            candlestick = self.pattern_data.get('candlestick', {})
            if candlestick.get('bearish_count', 0) >= 2:
                risks.append("6. **形态面压力**：多个K线形态发出看跌信号，技术面存在压力")
            
            resonance = self.pattern_data.get('resonance', {})
            res_score = resonance.get('total_score', 0)
            if res_score < -30:
                risks.append(f"7. **信号共振偏弱**：七维度共振评分{res_score:+.1f}分，多维度信号偏空")
        
        if not risks:
            risks.append("✅ 未发现明显风险信号，但仍需关注市场系统性风险")
        
        return '\n'.join(risks)
    
    def _position_strategy(self, score: int) -> str:
        """仓位策略"""
        if score >= 80:
            return "可重仓参与（60-80%），但建议分批建仓，首次建仓不超过40%"
        elif score >= 65:
            return "可适度参与（40-60%），分2-3批建仓，降低择时风险"
        elif score >= 50:
            return "轻仓试探（20-40%），快进快出，严格止损"
        elif score >= 35:
            return "极小仓位（10-20%）或观望，等待更明确信号"
        else:
            return "空仓观望或清仓，规避风险"
    
    def _trading_plan(self, current: float, target: float, stop: float) -> str:
        """交易计划"""
        if self.total_score >= 70:
            return f"""- **买入区间**：¥{current * 0.98:.2f} - ¥{current * 1.02:.2f}
- **目标价位**：¥{target:.2f}（预期收益{(target/current - 1)*100:.1f}%）
- **止损价位**：¥{stop:.2f}（最大亏损{(1 - stop/current)*100:.1f}%）
- **持有周期**：中线持有（1-3个月）
- **止盈策略**：达到目标价减仓50%，剩余设移动止盈"""
        elif self.total_score >= 50:
            return f"""- **买入区间**：¥{current * 0.97:.2f} - ¥{current:.2f}（不追高）
- **目标价位**：¥{target:.2f}
- **止损价位**：¥{stop:.2f}
- **持有周期**：波段操作（2-4周）
- **止盈策略**：分批止盈，涨5%减1/3，涨10%减1/2"""
        else:
            return f"""- **买入区间**：暂不买入，等待信号改善
- **关注价位**：¥{current * 0.95:.2f}以下（回调后）
- **止损价位**：¥{stop:.2f}
- **持有周期**：短线或观望
- **策略**：等待更明确的入场信号"""
    
    def _generate_summary_enhanced(self) -> str:
        """生成增强版分析总结"""
        if self.total_score >= 75:
            return f"""综合五维分析，该股票目前呈现**{self.rating}**信号，综合评分{self.total_score}/100。

**技术面**：趋势明确，指标配合良好；**基本面**：业绩稳健，财务健康；**资金面**：主力积极；**消息面**：情绪正面；**形态面**：{self._pattern_summary()}。

建议积极配置，但需严格执行止损纪律，控制单一标的仓位不超过总资产的30%。"""
        elif self.total_score >= 60:
            return f"""综合五维分析，该股票目前呈现**{self.rating}**信号，综合评分{self.total_score}/100。

整体趋势向好，但部分维度存在不确定性。{self._pattern_summary()}

建议适量参与，控制仓位，密切关注后续走势变化，及时调整策略。"""
        elif self.total_score >= 45:
            return f"""综合五维分析，该股票目前信号**中性混杂**，综合评分{self.total_score}/100。

多空因素交织，趋势尚不明确。{self._pattern_summary()}

建议观望为主，等待更明确的入场信号，避免在模糊区域操作。"""
        else:
            return f"""综合五维分析，该股票目前呈现**{self.rating}**信号，综合评分{self.total_score}/100。

多个维度显示风险积聚，{self._pattern_summary()}

建议减仓观望，规避风险，等待趋势明朗后再做决策。"""
    
    def _pattern_summary(self) -> str:
        """形态面总结"""
        if not self.pattern_data:
            return "形态面数据待更新"
        
        parts = []
        candlestick = self.pattern_data.get('candlestick', {})
        bullish = candlestick.get('bullish_count', 0)
        bearish = candlestick.get('bearish_count', 0)
        
        if bullish > 0 or bearish > 0:
            parts.append(f"识别出{bullish}个看涨、{bearish}个看跌形态")
        
        chanlun = self.pattern_data.get('chanlun', {})
        if chanlun.get('buy_points', []):
            parts.append("缠论出现买点信号")
        if chanlun.get('sell_points', []):
            parts.append("缠论出现卖点信号")
        
        resonance = self.pattern_data.get('resonance', {})
        res_score = resonance.get('total_score', 0)
        if abs(res_score) > 30:
            parts.append(f"信号共振评分{res_score:+.1f}分")
        
        return "形态面" + ("，".join(parts) if parts else "信号中性")
    
    def _md_risk_disclaimer(self) -> str:
        """Markdown风险提示与免责声明"""
        return f"""---

## ⚠️ 附录：风险提示与免责声明

### 风险提示

1. **市场风险**：股票市场受宏观经济、政策环境、国际形势等多重因素影响，存在系统性风险
2. **个股风险**：个股价格受公司经营、行业竞争、市场情绪等因素影响，波动可能较大
3. **模型风险**：本报告基于算法模型和历史数据，不保证未来收益，信号可能存在误差
4. **形态识别风险**：K线形态和缠论买卖点为算法自动识别，可能存在误判，需人工复核
5. **共振评分风险**：信号共振评分仅供参考，不构成买卖依据
6. **时效性风险**：报告基于历史数据，市场情况可能快速变化，建议及时更新分析

### 免责声明

> **本报告仅供参考，不构成任何投资建议或承诺。**
> 
> 1. 报告中的数据和分析结果基于公开信息和算法模型，作者不保证其准确性、完整性和及时性
> 2. 投资者应独立做出投资决策，并自行承担投资风险
> 3. 过往业绩不代表未来表现，历史回测结果仅供参考
> 4. 本报告版权归作者所有，未经授权不得转载或用于商业用途
> 5. 使用本报告即表示您已阅读并理解上述风险提示和免责声明
> 
> **股市有风险，投资需谨慎。请根据自身风险承受能力谨慎决策。**

---

<div align="center">

**报告由 Stock Analyst Skill V3.1 Pro 智能分析系统生成**

📅 生成时间：{self.timestamp} | 🔄 数据时效：实时

</div>"""
    
    # ==================== HTML格式生成（简化版，核心样式） ====================
    
    def generate_html(self) -> str:
        """生成专业HTML格式报告"""
        # 将Markdown转换为HTML（简化实现）
        md_content = self.generate_markdown()
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.stock_name} ({self.code}) - 专业股票分析报告</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --neutral: #6b7280;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1f2937;
            --border: #e5e7eb;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.8;
        }}
        
        .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 24px;
            text-align: center;
        }}
        
        .header h1 {{ font-size: 2rem; margin-bottom: 12px; }}
        .header .meta {{ opacity: 0.9; font-size: 0.9rem; }}
        
        /* Cards */
        .card {{
            background: var(--card);
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
        }}
        
        .card h2 {{
            font-size: 1.4rem;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid var(--primary);
            color: var(--primary);
        }}
        
        .card h3 {{
            font-size: 1.1rem;
            margin: 24px 0 12px 0;
            color: var(--text);
            font-weight: 600;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 0.9rem;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        th {{
            background: #f9fafb;
            font-weight: 600;
            color: var(--neutral);
        }}
        
        tr:hover {{ background: #f9fafb; }}
        
        /* Score display */
        .score-display {{
            text-align: center;
            padding: 24px;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 12px;
            margin: 16px 0;
        }}
        
        .score-display .score {{
            font-size: 3rem;
            font-weight: bold;
            color: var(--primary);
        }}
        
        .score-display .rating {{
            font-size: 1.5rem;
            margin-top: 8px;
        }}
        
        /* Highlight box */
        .highlight {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 4px solid var(--warning);
            padding: 16px;
            margin: 16px 0;
            border-radius: 0 8px 8px 0;
        }}
        
        /* Pattern section highlight */
        .pattern-highlight {{
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid var(--success);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
        }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        
        /* Lists */
        ul {{ padding-left: 20px; margin: 12px 0; }}
        li {{ margin: 8px 0; }}
        
        /* Disclaimer */
        .disclaimer {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 1px solid var(--warning);
            border-radius: 12px;
            padding: 24px;
            margin-top: 24px;
        }}
        
        .disclaimer h3 {{ color: #92400e; margin-bottom: 12px; }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .container {{ padding: 12px; }}
            .header {{ padding: 24px; }}
            .header h1 {{ font-size: 1.5rem; }}
            table {{ font-size: 0.8rem; }}
            th, td {{ padding: 8px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {self._html_content_from_md()}
    </div>
</body>
</html>"""
    
    def _html_content_from_md(self) -> str:
        """从Markdown生成HTML内容（简化转换）"""
        # 这里简化处理，实际可以使用markdown库转换
        md = self.generate_markdown()
        
        # 基本转换
        html = md
        
        # 转换标题
        html = html.replace('## ', '</div><div class="card"><h2>')
        html = html.replace('### ', '<h3>')
        html = html.replace('\n\n---\n\n', '</div>')
        
        # 包装开头
        html = '<div class="header"><h1>📊 ' + self.stock_name + ' (' + self.code + ') 深度分析报告</h1>' + \
               '<div class="meta">专业版股票分析报告 | 五维分析体系 | V3.1 Pro<br>报告生成时间：' + self.timestamp + '</div></div>' + html
        
        # 添加结尾
        html = html + '</div>'
        
        # 添加免责声明样式
        html = html.replace('## ⚠️ 附录：风险提示与免责声明', '</div><div class="disclaimer"><h3>⚠️ 附录：风险提示与免责声明</h3>')
        
        return html


# ==================== 便捷函数 ====================

def generate_unified_report(data: Dict[str, Any], pattern_data: Optional[Dict] = None) -> Dict[str, str]:
    """
    生成统一格式的专业报告（同时返回HTML和Markdown）
    
    Args:
        data: 基础分析数据（行情、财务、新闻、技术指标等）
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
            'turnover': 3.15,
            'pe': 28.5
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
            'trend': '上升趋势'
        },
        'fundamental': {
            'score': 72,
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
                'overall_trend': '基本面向好'
            }
        },
        'money_flow': {
            'score': 68,
            'main_flow': {
                'date': '2024-12-20',
                'main_net': 0.85,
                'main_pct': 5.2
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
                {'name_cn': '早晨之星', 'type': 'bullish', 'type_cn': '看涨反转', 'reliability': 5, 'confidence': 0.88, 'position': 0, 'description': '底部反转信号'},
                {'name_cn': '阳包阴', 'type': 'bullish', 'type_cn': '看涨反转', 'reliability': 4, 'confidence': 0.82, 'position': 1, 'description': '多头力量增强'},
                {'name_cn': '突破缺口', 'type': 'bullish', 'type_cn': '看涨持续', 'reliability': 4, 'confidence': 0.75, 'position': 2, 'description': '趋势加速信号'}
            ],
            'bullish_count': 3,
            'bearish_count': 0,
            'bullish_score': 42.5,
            'bearish_score': 0,
            'signal': '强烈看涨',
            'total_patterns': 3
        },
        'chanlun': {
            'bi_count': 7,
            'zhongshu_count': 2,
            'current_trend': '向上笔进行中',
            'nearest_zhongshu': {'range': '16.80-17.50', 'zg': 17.50, 'zd': 16.80, 'center': 17.15},
            'bis': [
                {'direction': 'up', 'start_price': 16.50, 'end_price': 17.20, 'height': 0.70},
                {'direction': 'down', 'start_price': 17.20, 'end_price': 16.85, 'height': 0.35},
                {'direction': 'up', 'start_price': 16.85, 'end_price': 18.52, 'height': 1.67}
            ],
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
                '情绪面': 3.5,
                '缠论': 10.0
            },
            'bullish_signals': [
                {'signal_type': 'K线形态', 'description': '早晨之星形态确认'},
                {'signal_type': '缠论', 'description': '一买信号出现'},
                {'signal_type': '趋势', 'description': '突破MA60均线'}
            ],
            'bearish_signals': []
        },
        'sentiment': {
            'index_value': 62.5,
            'level': {'name': '贪婪'},
            'trend': '上升',
            'signal': '谨慎持有'
        }
    }
    
    # 生成报告
    reports = generate_unified_report(test_data, test_pattern_data)
    
    # 保存测试文件
    import os
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, 'professional_report.md'), 'w', encoding='utf-8') as f:
        f.write(reports['markdown'])
    
    with open(os.path.join(output_dir, 'professional_report.html'), 'w', encoding='utf-8') as f:
        f.write(reports['html'])
    
    print("✅ 专业版测试报告已生成：")
    print(f"  📄 Markdown: {os.path.join(output_dir, 'professional_report.md')}")
    print(f"  🌐 HTML: {os.path.join(output_dir, 'professional_report.html')}")
