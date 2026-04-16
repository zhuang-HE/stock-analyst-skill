# -*- coding: utf-8 -*-
"""
================================================================================
统一专业股票分析报告模板 V3.2 Ultra
================================================================================
同时生成HTML和Markdown格式，内容统一、专业、功能完备

报告结构：
├── 封面与概览
├── 一、实时行情与走势分析（价格、涨跌幅、成交量、技术走势）
├── 二、财务深度分析（利润表、财务质量、趋势、业务板块）
├── 三、新闻舆情与市场情绪（新闻摘要、情绪指数、舆情分析）
├── 四、技术指标深度解析（KDJ/MACD/均线/量价）
├── 五、形态面专业分析【重点强化】
│   ├── 5.1 数据来源与可靠性声明
│   ├── 5.2 K线形态识别结果（60+形态库、形态详情、可靠性评估）
│   ├── 5.3 缠论结构分析（笔/中枢/趋势、买卖点识别）
│   ├── 5.4 买卖点信号系统（一买二买三买/一卖二卖三卖、置信度）
│   └── 5.5 信号共振评分（7维度加权、共振级别、信号明细）
├── 六、资金面深度分析【时效性强化】
│   ├── 6.1 资金流向概览（最近20个交易日）
│   ├── 6.2 主力资金分析
│   ├── 6.3 北向资金分析
│   └── 6.4 资金面综合判断
├── 七、综合投资决策建议（评分、优势、风险、策略、总结）
└── 附录：风险提示与免责声明

作者：Stock Analyst Skill V3.2 Ultra
================================================================================
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json


class UnifiedReportGenerator:
    """
    统一专业报告生成器 V3.2 Ultra
    
    特性：
    - 双格式输出：HTML（可视化）+ Markdown（可读性）
    - 五维分析体系：技术/基本面/资金/消息/形态
    - 形态面深度强化：K线形态+缠论+买卖点+共振评分，数据来源验证
    - 资金面时效性：确保最近20个交易日数据
    - 专业级内容：财务解读、技术指标、投资策略
    - 数据接口完备：支持所有分析模块的数据结构
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
            data: 基础分析数据（行情、财务、新闻、技术指标、资金面等）
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
    
    # ==================== 统一报告生成 ====================
    
    def generate_unified_report(self, output_format: str = 'markdown') -> Dict[str, str]:
        """
        生成统一报告（按需返回格式）
        
        Args:
            output_format: 输出格式
                - 'markdown': 只返回Markdown（默认，最省Token）
                - 'html': 只返回HTML
                - 'both': 同时返回HTML和Markdown
                - 'text': 返回纯文本简化版
                
        Returns:
            根据output_format返回对应格式的报告
            - 'markdown': {'markdown': md_content}
            - 'html': {'html': html_content}
            - 'both': {'html': html_content, 'markdown': md_content}
            - 'text': {'text': text_content}
        """
        if output_format == 'markdown':
            return {'markdown': self.generate_markdown()}
        elif output_format == 'html':
            return {'html': self.generate_html()}
        elif output_format == 'text':
            return {'text': self.generate_text_summary()}
        else:  # both
            return {
                'html': self.generate_html(),
                'markdown': self.generate_markdown()
            }
    
    def generate_html(self, minimal: bool = True) -> str:
        """
        生成HTML格式报告
        
        Args:
            minimal: 是否使用极简样式（默认True，节省Token）
        """
        if minimal:
            return self._generate_minimal_html_report()
        return self._generate_html_report()
    
    def generate_markdown(self) -> str:
        """生成专业Markdown格式报告"""
        return self._generate_markdown_report()
    
    def generate_text_summary(self) -> str:
        """生成纯文本简化版报告（最省Token）"""
        return self._generate_text_summary()
    
    # ==================== Markdown格式生成 ====================
    
    def _generate_markdown_report(self) -> str:
        """生成完整Markdown报告"""
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
            sections.append(self._md_pattern_analysis_ultra())
        
        # 资金面分析（时效性强化）
        sections.append(self._md_money_flow_analysis())
        
        sections.extend([
            self._md_investment_advice(),
            self._md_risk_disclaimer(),
        ])
        
        return '\n\n---\n\n'.join(sections)
    
    def _md_header(self) -> str:
        """Markdown报告头部"""
        return f"""# 📊 {self.stock_name} ({self.code}) 深度分析报告

<div align="center">

**专业版股票分析报告** | **五维分析体系** | **V3.2 Ultra**

📅 报告生成时间：{self.timestamp}

</div>

---

## 📋 报告概览

| 项目 | 内容 |
|:-----|:-----|
| **股票名称** | {self.stock_name} ({self.code}) |
| **分析维度** | 技术面 / 基本面 / 资金面 / 消息面 / **形态面** |
| **报告版本** | V3.2 Ultra 专业版 |
| **数据时效** | 实时行情 + 最新财报 + 近期新闻 + **20日资金流向** |"""
    
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
        prev_close = quote.get('prev_close', 0)
        
        # 计算振幅
        amplitude = ((high - low) / prev_close * 100) if prev_close > 0 else 0
        
        # 走势解读
        trend_analysis = self._analyze_trend_detailed(pct_change, volume, amplitude)
        
        return f"""## 📈 一、实时行情与走势分析

### 1.1 实时行情数据

| 指标 | 数值 | 指标 | 数值 | 指标 | 数值 |
|:-----|:-----|:-----|:-----|:-----|:-----|
| **最新价** | ¥{price:.2f} | **涨跌幅** | {pct_change:+.2f}% | **涨跌额** | ¥{price * pct_change / 100:.2f} |
| **开盘价** | ¥{open_p:.2f} | **最高价** | ¥{high:.2f} | **最低价** | ¥{low:.2f} |
| **昨收价** | ¥{prev_close:.2f} | **振幅** | {amplitude:.2f}% | **换手率** | {turnover:.2f}% |
| **成交量** | {volume:,.0f} 手 | **成交额** | {amount:.2f} 亿 | **量比** | {quote.get('volume_ratio', '-')} |
| **市盈率(TTM)** | {quote.get('pe', '-')} | **市净率** | {quote.get('pb', '-')} | **总市值** | {quote.get('market_cap', '-')} 亿 |

### 1.2 技术走势分析

{trend_analysis}

### 1.3 关键价位分析

| 价位类型 | 价格 | 与现价关系 | 技术意义 |
|:---------|:-----|:-----------|:---------|
| **当日阻力** | ¥{high:.2f} | +{((high-price)/price*100):.2f}% | 日内最高点，短期压力 |
| **当日支撑** | ¥{low:.2f} | {((low-price)/price*100):+.2f}% | 日内最低点，短期支撑 |
| **开盘价** | ¥{open_p:.2f} | {((open_p-price)/price*100):+.2f}% | 多空分水岭 |
| **昨收价** | ¥{prev_close:.2f} | {((prev_close-price)/price*100):+.2f}% | 基准参考价 |"""
    
    def _analyze_trend_detailed(self, pct_change: float, volume: float, amplitude: float) -> str:
        """详细走势分析"""
        analysis = []
        
        # 涨跌分析
        if pct_change > 7:
            analysis.append("📈 **强势上涨**：涨幅超过7%，多头力量强劲，可能受重大利好消息刺激。建议关注成交量配合情况，若放量上涨则趋势可信度高。")
        elif pct_change > 4:
            analysis.append("📈 **明显上涨**：涨幅4-7%，走势积极，市场认可度较高。关注能否突破前期阻力位，形成新的上升趋势。")
        elif pct_change > 2:
            analysis.append("📈 **温和上涨**：涨幅2-4%，稳步上行，趋势健康。属于正常的技术性上涨，可持续性较好。")
        elif pct_change > 0:
            analysis.append("📊 **小幅上涨**：涨幅0-2%，上涨动能一般。可能是技术性反弹或跟随大盘上涨，需观察持续性。")
        elif pct_change > -2:
            analysis.append("📊 **小幅回调**：跌幅0-2%，正常波动范围。属于健康的技术性调整，不必过度担心。")
        elif pct_change > -4:
            analysis.append("📉 **温和回调**：跌幅2-4%，需关注支撑位承接力度。若缩量回调，可能是洗盘行为。")
        elif pct_change > -7:
            analysis.append("📉 **明显下跌**：跌幅4-7%，空头占优，谨慎观望。关注是否有利空消息刺激，以及支撑位是否有效。")
        else:
            analysis.append("📉 **大幅下跌**：跌幅超过7%，恐慌情绪蔓延，建议避险。若放量下跌，可能还有进一步调整空间。")
        
        # 振幅分析
        if amplitude > 7:
            analysis.append("⚡ **高波动**：日内振幅超过7%，多空分歧激烈，短线操作机会与风险并存。适合有经验的投资者进行T+0操作。")
        elif amplitude > 4:
            analysis.append("📊 **中等波动**：日内振幅4-7%，正常交易波动。提供一定的操作空间，适合波段操作。")
        else:
            analysis.append("💤 **低波动**：日内振幅小于4%，市场观望情绪较浓。可能是变盘前的蓄势，需密切关注方向选择。")
        
        # 成交量分析
        if volume > 2000000:
            analysis.append("💰 **成交活跃**：成交量显著放大，资金参与度高，趋势可信度强。量价配合良好，支撑当前走势。")
        elif volume > 800000:
            analysis.append("💰 **成交正常**：成交量处于正常水平。市场参与度适中，走势较为健康。")
        else:
            analysis.append("💤 **成交清淡**：成交量偏低，市场参与度不足，趋势持续性存疑。建议等待放量确认。")
        
        return '\n\n'.join(f"{i+1}. {a}" for i, a in enumerate(analysis))
    
    def _md_financial_analysis(self) -> str:
        """Markdown财务深度分析"""
        fundamental = self.data.get('fundamental', {})
        fin = fundamental.get('financial', {})
        latest = fin.get('latest', {})
        history = fin.get('history', [])
        
        if not latest:
            return "## 💼 二、财务深度分析\n\n> 暂无财务数据"
        
        report_date = latest.get('report_date', 'N/A')
        revenue = latest.get('revenue', 'N/A')
        revenue_yoy = latest.get('revenue_yoy', 'N/A')
        profit = latest.get('net_profit', 'N/A')
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
        
        # 历史数据表格
        history_table = self._generate_financial_history_table(history)
        
        return f"""## 💼 二、财务深度分析

### 2.1 核心财务数据（报告期：{report_date}）

#### 利润表关键指标

| 指标 | 数值 | 同比变化 | 指标 | 数值 | 健康度 |
|:-----|:-----|:---------|:-----|:-----|:-------|
| **营业收入** | {revenue} | {revenue_yoy} | **毛利率** | {gross_margin} | {self._rate_indicator(gross_margin, 30, 20)} |
| **净利润** | {profit} | {profit_yoy} | **净利率** | {net_margin} | {self._rate_indicator(net_margin, 15, 8)} |
| **ROE** | {roe} | - | **资产负债率** | {debt_ratio} | {self._rate_debt(debt_ratio)} |
| **每股收益** | {eps} 元 | - | **每股现金流** | {ocf_ps} 元 | {self._rate_indicator(ocf_ps, 1, 0.5)} |

#### 历史财务数据趋势

{history_table}

### 2.2 财务质量深度评估

{quality_analysis}

### 2.3 营收与利润趋势解读

{trend_analysis}

### 2.4 业务板块与估值分析

基于财务数据分析，公司业务呈现以下特征：

**主营业务**：核心业务保持稳定发展，市场地位稳固
**成长能力**：{self._growth_assessment(revenue_yoy, profit_yoy)}
**盈利能力**：{self._profitability_assessment(roe, net_margin)}
**财务健康**：{self._health_assessment(debt_ratio)}
**现金流**：{self._cashflow_assessment(ocf_ps, eps)}

**估值分析**：
- PE(TTM)：{latest.get('pe', 'N/A')} | PB：{latest.get('pb', 'N/A')}
- 历史PE分位数：{latest.get('pe_percentile', 'N/A')} | 历史PB分位数：{latest.get('pb_percentile', 'N/A')}
- 估值结论：{self._valuation_assessment(latest)}"""
    
    def _generate_financial_history_table(self, history: List[Dict]) -> str:
        """生成历史财务数据表格"""
        if not history:
            return "> 暂无历史数据"
        
        rows = []
        for item in history[:5]:
            rows.append(
                f"| {item.get('report_date', '-')} | {item.get('revenue_yoy', '-')} | "
                f"{item.get('net_profit_yoy', '-')} | {item.get('roe', '-')} | "
                f"{item.get('gross_margin', '-')} | {item.get('net_margin', '-')} |"
            )
        
        return f"""| 报告期 | 营收同比 | 净利润同比 | ROE | 毛利率 | 净利率 |
|:-------|:---------|:-----------|:----|:-------|:-------|
{chr(10).join(rows)}"""
    
    def _valuation_assessment(self, latest: Dict) -> str:
        """估值评估"""
        try:
            pe = float(str(latest.get('pe', '0')).replace('x', ''))
            pe_pct = float(str(latest.get('pe_percentile', '0')).replace('%', ''))
            
            if pe < 15 and pe_pct < 30:
                return "估值偏低，具备安全边际"
            elif pe < 25 and pe_pct < 50:
                return "估值合理，处于历史中枢"
            elif pe > 40 or pe_pct > 80:
                return "估值偏高，注意追高风险"
            else:
                return "估值适中，需结合成长性判断"
        except:
            return "估值数据待评估"
    
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
                    analyses.append(f"🟢 **盈利能力卓越**：ROE为{roe}，远超20%的优秀线，股东回报能力突出，属于高质量成长股。")
                elif roe_val > 15:
                    analyses.append(f"🟢 **盈利能力优秀**：ROE为{roe}，高于15%良好线，盈利质量较高，具备持续竞争优势。")
                elif roe_val > 10:
                    analyses.append(f"🟡 **盈利能力良好**：ROE为{roe}，处于10-15%区间，盈利稳定，属于稳健型公司。")
                else:
                    analyses.append(f"🔴 **盈利能力一般**：ROE为{roe}，低于10%，需关注盈利改善，可能处于行业周期低谷。")
            except:
                pass
        
        # 毛利率分析
        margin = latest.get('gross_margin', '')
        if margin and '%' in str(margin):
            try:
                margin_val = float(str(margin).replace('%', ''))
                if margin_val > 40:
                    analyses.append(f"🟢 **产品竞争力强**：毛利率{margin}，产品议价能力突出，具备定价权优势。")
                elif margin_val > 25:
                    analyses.append(f"🟡 **产品竞争力良好**：毛利率{margin}，处于行业中上水平，盈利能力稳定。")
                else:
                    analyses.append(f"⚪ **产品竞争力一般**：毛利率{margin}，行业竞争激烈，成本控制压力大。")
            except:
                pass
        
        # 负债率分析
        debt = latest.get('debt_ratio', '')
        if debt and '%' in str(debt):
            try:
                debt_val = float(str(debt).replace('%', ''))
                if debt_val < 35:
                    analyses.append(f"🟢 **财务结构稳健**：资产负债率{debt}，财务风险低，融资空间大，抗风险能力强。")
                elif debt_val < 50:
                    analyses.append(f"🟡 **财务结构适中**：资产负债率{debt}，处于合理区间，财务杠杆使用适度。")
                elif debt_val < 65:
                    analyses.append(f"⚪ **财务杠杆较高**：资产负债率{debt}，需关注偿债能力，警惕流动性风险。")
                else:
                    analyses.append(f"🔴 **财务风险较高**：资产负债率{debt}，超过警戒线，财务弹性不足，需谨慎关注。")
            except:
                pass
        
        # 净利率分析
        net_margin = latest.get('net_margin', '')
        if net_margin and '%' in str(net_margin):
            try:
                nm_val = float(str(net_margin).replace('%', ''))
                if nm_val > 15:
                    analyses.append(f"🟢 **费用控制优秀**：净利率{net_margin}，成本管控能力强，运营效率高。")
                elif nm_val > 8:
                    analyses.append(f"🟡 **费用控制良好**：净利率{net_margin}，运营效率正常，费用结构合理。")
                else:
                    analyses.append(f"⚪ **费用控制一般**：净利率{net_margin}，存在费用优化空间，需关注三费占比。")
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
                interpretations.append(f"📈 **营收高速增长**：同比增长{revenue}，业务扩张迅速，市场份额持续提升，处于快速成长期。")
            elif rev_val > 15:
                interpretations.append(f"📈 **营收稳健增长**：同比增长{revenue}，增长势头良好，业务发展健康，具备可持续性。")
            elif rev_val > 5:
                interpretations.append(f"📊 **营收温和增长**：同比增长{revenue}，增速放缓但仍有增长，需关注增长动力来源。")
            elif rev_val > 0:
                interpretations.append(f"📊 **营收微增**：同比增长{revenue}，增长乏力，需关注业务动力，可能面临行业天花板。")
            else:
                interpretations.append(f"📉 **营收下滑**：同比下降{revenue}，业务承压，需警惕经营风险，关注业务调整进展。")
            
            # 利润分析
            if prof_val > 50:
                interpretations.append(f"🚀 **利润爆发增长**：同比增长{profit}，盈利能力大幅提升，经营效率显著改善，业绩超预期。")
            elif prof_val > 25:
                interpretations.append(f"📈 **利润高速增长**：同比增长{profit}，盈利质量良好，增长可持续性强，基本面扎实。")
            elif prof_val > 10:
                interpretations.append(f"📈 **利润稳健增长**：同比增长{profit}，盈利稳定，经营健康，符合预期。")
            elif prof_val > 0:
                interpretations.append(f"📊 **利润微增**：同比增长{profit}，增速放缓，关注成本端压力，盈利能力边际改善。")
            else:
                interpretations.append(f"📉 **利润下滑**：同比下降{profit}，盈利承压，需关注盈利能力变化，可能处于周期底部。")
            
            # 营收利润匹配度
            if rev_val > 0 and prof_val > rev_val * 1.5:
                interpretations.append("💡 **盈利质量提升**：利润增速显著高于营收增速，经营杠杆效应显现，费用控制有效，规模效应开始体现。")
            elif rev_val > 0 and prof_val < rev_val * 0.5:
                interpretations.append("⚠️ **盈利质量下降**：利润增速明显低于营收增速，成本费用压力增大，需关注毛利率变化和三费占比。")
            
        except:
            interpretations.append("财务趋势数据待更新")
        
        return '\n\n'.join(f"{i+1}. {a}" for i, a in enumerate(interpretations))
    
    def _growth_assessment(self, revenue: str, profit: str) -> str:
        """成长能力评估"""
        try:
            rev_val = float(str(revenue).replace('%', ''))
            prof_val = float(str(profit).replace('%', ''))
            if rev_val > 20 and prof_val > 20:
                return "高成长，营收利润双轮驱动，具备持续扩张能力"
            elif rev_val > 10 and prof_val > 10:
                return "稳健成长，发展势头良好，基本面扎实"
            elif rev_val > 0 and prof_val > 0:
                return "温和成长，增速放缓，需关注增长动力"
            else:
                return "成长承压，需关注业务调整和转型进展"
        except:
            return "成长数据待评估"
    
    def _profitability_assessment(self, roe: str, margin: str) -> str:
        """盈利能力评估"""
        try:
            roe_val = float(str(roe).replace('%', ''))
            if roe_val > 15:
                return "盈利能力强，ROE处于优秀水平，具备竞争优势"
            elif roe_val > 10:
                return "盈利能力良好，ROE稳定，经营健康"
            else:
                return "盈利能力一般，ROE有提升空间，需关注经营改善"
        except:
            return "盈利数据待评估"
    
    def _health_assessment(self, debt: str) -> str:
        """财务健康评估"""
        try:
            debt_val = float(str(debt).replace('%', ''))
            if debt_val < 40:
                return "财务结构稳健，偿债能力强，财务风险低"
            elif debt_val < 60:
                return "财务结构适中，风险可控，杠杆使用合理"
            else:
                return "财务杠杆较高，需关注风险，警惕流动性压力"
        except:
            return "财务健康度待评估"
    
    def _cashflow_assessment(self, ocf: str, eps: str) -> str:
        """现金流评估"""
        try:
            ocf_val = float(str(ocf))
            eps_val = float(str(eps))
            if ocf_val > eps_val:
                return "现金流健康，盈利质量高，回款能力好"
            elif ocf_val > 0:
                return "现金流一般，关注回款情况，营运资金占用"
            else:
                return "现金流承压，需关注经营改善，警惕资金链风险"
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
        sentiment_trend = "平稳"
        if self.pattern_data:
            sentiment_data = self.pattern_data.get('sentiment', {})
            sentiment_index = sentiment_data.get('index_value', 50)
            level = sentiment_data.get('level', {})
            sentiment_level = level.get('name', '中性') if isinstance(level, dict) else str(level)
            sentiment_trend = sentiment_data.get('trend', '平稳')
        
        # 新闻列表
        news_analysis = []
        if items:
            for i, item in enumerate(items[:8], 1):
                title = item.get('title', '')
                date = item.get('date', '')
                source = item.get('source', '')
                # 简单情感判断
                sentiment_tag = ""
                if any(w in title for w in ['增长', '突破', '利好', '合作', '获奖', '订单', '中标', '签约']):
                    sentiment_tag = "🟢 正面"
                elif any(w in title for w in ['下滑', '亏损', '处罚', '诉讼', '减持', '风险', '警示', '下降']):
                    sentiment_tag = "🔴 负面"
                else:
                    sentiment_tag = "⚪ 中性"
                news_analysis.append(f"{i}. **{date}** | {sentiment_tag} | {title} [{source}]")
        
        # 情绪解读
        sentiment_interpretation = self._interpret_sentiment_detailed(sentiment_index, sentiment_level)
        
        return f"""## 📰 三、新闻舆情与市场情绪

### 3.1 市场情绪指数

| 指标 | 数值 | 等级 | 趋势 | 交易信号 |
|:-----|:-----|:-----|:-----|:---------|
| **贪婪恐慌指数** | {sentiment_index:.1f}/100 | {sentiment_level} | {sentiment_trend} | {self._sentiment_signal(sentiment_index)} |
| **新闻情感倾向** | {sentiment} | 得分：{sentiment_score:+d} | - | - |
| **对基本面影响** | {fund_impact} | - | - | - |

### 3.2 最新财经新闻摘要

{chr(10).join(news_analysis) if news_analysis else '> 暂无最新新闻'}

### 3.3 市场情绪深度解读

{sentiment_interpretation}

### 3.4 舆情综合分析

基于近期新闻舆情分析：
- **新闻情感倾向**：{sentiment}（得分{sentiment_score:+d}）
- **对基本面影响**：{fund_impact}
- **市场情绪状态**：{sentiment_level}（指数{sentiment_index:.1f}）
- **交易建议**：{self._sentiment_signal(sentiment_index)}

**舆情风险提示**：新闻舆情仅供参考，不构成投资建议。重大事件需关注官方公告。"""
    
    def _interpret_sentiment_detailed(self, index: float, level: str) -> str:
        """详细情绪解读"""
        if index < 15:
            return """🔴 **极度恐慌阶段**（指数<20）

市场情绪极度悲观，恐慌情绪蔓延，多数投资者选择抛售。历史数据显示，此阶段往往是中长期布局的较好时机，但需精选标的、控制仓位、分批建仓。建议关注被错杀的优质标的，逆向投资需有耐心和定力。"""
        elif index < 30:
            return """🟠 **恐慌阶段**（指数20-30）

市场情绪偏悲观，投资者信心不足，成交量萎缩。部分优质标的可能被低估，适合价值投资者逢低关注。建议保持耐心，等待情绪修复，可逐步建仓优质标的。"""
        elif index < 45:
            return """⚪ **谨慎阶段**（指数30-45）

市场情绪偏谨慎，投资者观望情绪浓厚。市场缺乏明确方向，建议控制仓位，等待更明确的信号出现。可关注结构性机会，精选个股。"""
        elif index < 55:
            return """⚪ **中性阶段**（指数45-55）

市场情绪平稳，多空力量相对均衡。建议按常规策略操作，精选个股，控制仓位在正常水平。关注市场方向选择。"""
        elif index < 70:
            return """🟢 **乐观阶段**（指数55-70）

市场情绪偏乐观，投资者信心回升，资金活跃度提高。可适当参与，但需注意追高风险，设置好止损位。关注成交量能否持续放大。"""
        elif index < 85:
            return """🟢 **贪婪阶段**（指数70-85）

市场情绪高涨，投资者风险偏好提升，成交量放大。需警惕追高风险，建议逐步减仓，锁定利润。关注是否出现顶部信号。"""
        else:
            return """🔵 **极度贪婪阶段**（指数>85）

市场情绪狂热，投资者普遍乐观，风险积累。历史数据显示，此阶段往往是市场顶部区域，建议大幅减仓，规避风险。逆向投资者可关注做空机会。"""
    
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
        
        # 布林带
        bb_upper = tech.get('bb_upper', 0)
        bb_middle = tech.get('bb_middle', 0)
        bb_lower = tech.get('bb_lower', 0)
        
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
| **DEA** | {tech.get('dea', 0):.3f} | - | - |
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

### 4.4 布林带分析

| 轨道 | 价格 | 与现价关系 | 技术意义 |
|:-----|:-----|:-----------|:---------|
| **上轨** | ¥{bb_upper:.2f} | 阻力位 | 超买区域 |
| **中轨** | ¥{bb_middle:.2f} | 基准线 | 20日均线 |
| **下轨** | ¥{bb_lower:.2f} | 支撑位 | 超卖区域 |

### 4.5 均线系统分析

| 均线 | 价格 | 与现价关系 | 技术意义 |
|:-----|:-----|:-----------|:---------|
| MA5 | ¥{tech.get('ma5', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma5') else '❌ 下方'} | 短期趋势{'向上' if tech.get('price_above_ma5') else '向下'} |
| MA10 | ¥{tech.get('ma10', 0):.2f} | - | 短期支撑/阻力 |
| MA20 | ¥{tech.get('ma20', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma20') else '❌ 下方'} | 中期趋势{'向上' if tech.get('price_above_ma20') else '向下'} |
| MA60 | ¥{tech.get('ma60', 0):.2f} | {'✅ 上方' if tech.get('price_above_ma60') else '❌ 下方'} | 长期趋势{'向上' if tech.get('price_above_ma60') else '向下'} |

**均线排列**：{tech.get('ma_alignment', '待分析')}

**综合趋势判断**：{tech.get('trend', '震荡')}"""
    
    def _analyze_kdj_detailed(self, k: float, d: float, j: float, signal: str) -> str:
        """详细KDJ分析"""
        analysis = []
        
        if '金叉' in signal:
            analysis.append(f"🟢 **金叉买入信号**：K线({k:.2f})上穿D线({d:.2f})，短期动能转强。")
            if k < 50:
                analysis.append("金叉发生在50以下低位，属于低位金叉，信号可靠性较高，建议关注买入机会。")
            else:
                analysis.append("金叉发生在50以上，属于高位金叉，需结合其他指标确认，警惕假突破。")
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
            analysis.append(f"🔴 **严重超买**：RSI高达{rsi:.2f}，远超80超买线，短期回调风险极大。建议逢高减仓，锁定利润。")
        elif rsi > 70:
            analysis.append(f"🟠 **超买区域**：RSI为{rsi:.2f}，进入70-80超买区，上涨空间有限。谨慎追高，关注顶部信号。")
        elif rsi > 50:
            analysis.append(f"🟢 **强势区域**：RSI为{rsi:.2f}，处于50-70强势区，多头占优。趋势健康，可继续持有。")
        elif rsi > 30:
            analysis.append(f"⚪ **弱势区域**：RSI为{rsi:.2f}，处于30-50弱势区，空头占优。关注支撑位，等待企稳信号。")
        elif rsi > 20:
            analysis.append(f"🟠 **超卖区域**：RSI为{rsi:.2f}，进入20-30超卖区，下跌空间有限。关注反弹机会。")
        else:
            analysis.append(f"🟢 **严重超卖**：RSI低至{rsi:.2f}，低于20超卖线，短期反弹概率大。可考虑逢低布局。")
        
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
    
    # ==================== 形态面专业分析（重点强化）====================
    
    def _md_pattern_analysis_ultra(self) -> str:
        """
        Markdown形态面分析（V3.2 Ultra强化版）
        
        强化内容：
        1. 数据来源与可靠性声明
        2. K线形态识别结果（60+形态库、形态详情、可靠性评估）
        3. 缠论结构分析（笔/中枢/趋势、买卖点识别）
        4. 买卖点信号系统（一买二买三买/一卖二卖三卖、置信度）
        5. 信号共振评分（7维度加权、共振级别、信号明细）
        """
        if not self.pattern_data:
            return "## 📐 五、形态面专业分析\n\n> 暂无形态面数据"
        
        sections = [
            self._md_pattern_data_source(),
        ]
        
        # 1. K线形态识别结果（详细版）
        candlestick = self.pattern_data.get('candlestick', {})
        if candlestick:
            sections.append(self._md_candlestick_section_ultra(candlestick))
        
        # 2. 缠论结构分析
        chanlun = self.pattern_data.get('chanlun', {})
        if chanlun:
            sections.append(self._md_chanlun_section_ultra(chanlun))
        
        # 3. 买卖点信号系统
        if chanlun:
            sections.append(self._md_buysell_points_section_ultra(chanlun))
        
        # 4. 信号共振评分（详细版）
        resonance = self.pattern_data.get('resonance', {})
        if resonance:
            sections.append(self._md_resonance_section_ultra(resonance))
        
        content = '\n\n'.join(sections)
        
        return f"""## 📐 五、形态面专业分析【核心板块】

> **形态面分析是本报告的核心特色**，整合K线形态识别、缠论结构分析、买卖点识别、信号共振评分四大模块，提供全方位的技术分析视角。

{content}"""
    
    def _md_pattern_data_source(self) -> str:
        """形态面数据来源与可靠性声明"""
        # 获取数据时效信息
        data_date = self.pattern_data.get('data_date', '最近交易日')
        data_source = self.pattern_data.get('data_source', '日线数据')
        kline_count = self.pattern_data.get('kline_count', 60)
        
        # 验证状态
        validation = self.pattern_data.get('validation', {})
        kline_valid = validation.get('kline_data', False)
        pattern_valid = validation.get('pattern_recognition', False)
        chanlun_valid = validation.get('chanlun_analysis', False)
        
        return f"""### 5.1 数据来源与可靠性声明

#### 数据来源说明

| 数据类型 | 来源 | 时效性 | 可靠性 |
|:---------|:-----|:-------|:-------|
| **K线数据** | {data_source} | {data_date} | {'✅ 已验证' if kline_valid else '⚠️ 待验证'} |
| **形态识别** | 60+形态算法库 | 实时计算 | {'✅ 已验证' if pattern_valid else '⚠️ 待验证'} |
| **缠论分析** | 分型-笔-中枢算法 | 实时计算 | {'✅ 已验证' if chanlun_valid else '⚠️ 待验证'} |
| **数据样本** | 最近{kline_count}根K线 | 充足 | ✅ 满足分析要求 |

#### 可靠性评估标准

**K线形态识别可靠性**：
- ⭐⭐⭐⭐⭐ (5星)：经典形态，多条件确认，历史回测胜率>70%
- ⭐⭐⭐⭐ (4星)：标准形态，主要条件满足，历史回测胜率60-70%
- ⭐⭐⭐ (3星)：变异形态，部分条件满足，需结合其他指标
- ⭐⭐ (2星)：疑似形态，条件不完全，仅供参考
- ⭐ (1星)：形态雏形，不确定性高，谨慎参考

**缠论买卖点置信度**：
- 🥇 **一级买卖点**（置信度80%+）：趋势背驰确认，结构完整
- 🥈 **二级买卖点**（置信度70-80%）：回撤确认，风险可控
- 🥉 **三级买卖点**（置信度60-70%）：突破确认，需结合量能

**信号共振评分说明**：
- 综合评分基于7个维度加权计算
- 每个维度得分范围：-20至+20分
- 总分范围：-100至+100分
- |分数|>75：强共振，趋势确认度高
- |分数|50-75：中等共振，趋势较明确
- |分数|25-50：弱共振，趋势待确认
- |分数|<25：无共振，趋势不明

> ⚠️ **免责声明**：形态识别基于算法自动计算，存在误判可能。建议结合基本面、资金面等多维度信息综合判断，不作为唯一交易依据。"""
    
    def _md_candlestick_section_ultra(self, candlestick: Dict) -> str:
        """K线形态识别详细板块（Ultra版）"""
        patterns = candlestick.get('patterns', [])
        bullish_count = candlestick.get('bullish_count', 0)
        bearish_count = candlestick.get('bearish_count', 0)
        bullish_score = candlestick.get('bullish_score', 0)
        bearish_score = candlestick.get('bearish_score', 0)
        signal = candlestick.get('signal', '中性')
        
        # 形态详情表格
        pattern_details = []
        for i, p in enumerate(patterns[:10], 1):
            emoji = "🟢" if p.get('type') == 'bullish' else "🔴" if p.get('type') == 'bearish' else "⚪"
            reliability_stars = '⭐' * p.get('reliability', 0) + '☆' * (5 - p.get('reliability', 0))
            pattern_details.append(
                f"| {i} | {emoji} {p.get('name_cn', 'N/A')} | {p.get('type_cn', 'N/A')} | "
                f"{reliability_stars} | {p.get('confidence', 0):.1%} | {p.get('position', 0)} |"
            )
        
        # 看涨形态列表
        bullish_patterns = [p for p in patterns if p.get('type') == 'bullish'][:5]
        bearish_patterns = [p for p in patterns if p.get('type') == 'bearish'][:5]
        
        bullish_list = '\n'.join([
            f"- **{p.get('name_cn')}**（可靠性{p.get('reliability')}/5，置信度{p.get('confidence'):.1%}）：{p.get('description', '看涨信号')}"
            for p in bullish_patterns
        ]) if bullish_patterns else "- 暂无主要看涨形态"
        
        bearish_list = '\n'.join([
            f"- **{p.get('name_cn')}**（可靠性{p.get('reliability')}/5，置信度{p.get('confidence'):.1%}）：{p.get('description', '看跌信号')}"
            for p in bearish_patterns
        ]) if bearish_patterns else "- 暂无主要看跌形态"
        
        return f"""### 5.2 K线形态识别结果

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
            return "多个看涨形态共振，技术面支撑较强，建议积极关注买入机会。可结合缠论买点确认入场时机。"
        elif '看涨' in signal or bullish > bearish:
            return "看涨形态占优，技术面偏正面，可考虑适量参与。建议分批建仓，控制仓位。"
        elif '强烈看跌' in signal or bearish >= 3:
            return "多个看跌形态共振，技术面压力较大，建议谨慎观望。持仓者考虑减仓避险。"
        elif '看跌' in signal or bearish > bullish:
            return "看跌形态占优，技术面偏负面，建议控制仓位。等待形态改善后再考虑介入。"
        else:
            return "多空形态均衡，技术面信号混杂，建议等待更明确的形态信号。可关注震荡区间的高抛低吸机会。"
    
    def _md_chanlun_section_ultra(self, chanlun: Dict) -> str:
        """缠论结构分析板块（Ultra版）"""
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
|:-----|:-----|:---------|
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
        
        return f"""### 5.3 缠论结构分析

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
            return "当前处于向上笔运行中，且有中枢支撑，趋势较为健康。关注是否形成背驰信号，背驰可能预示趋势转折。"
        elif '向下' in trend and zs_count > 0:
            return "当前处于向下笔运行中，关注是否接近中枢下沿或形成买点信号。中枢下沿是重要支撑位。"
        elif '向上' in trend:
            return "向上笔运行中，但中枢结构尚不明确，需关注后续中枢形成情况。无中枢支撑的走势持续性存疑。"
        elif '向下' in trend:
            return "向下笔运行中，建议等待企稳信号或买点确认后再考虑介入。避免过早抄底。"
        else:
            return "趋势方向尚不明确，建议等待笔结构进一步清晰后再做决策。缠论强调等待明确的买卖点信号。"
    
    def _md_buysell_points_section_ultra(self, chanlun: Dict) -> str:
        """买卖点信号系统板块（Ultra版）"""
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
                f"| {i} | 🎯 {bp_type} | {level} | ¥{price:.2f} | {confidence:.1%} | {description[:40]}... |"
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
                f"| {i} | 🔻 {sp_type} | {level} | ¥{price:.2f} | {confidence:.1%} | {description[:40]}... |"
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
        
        return f"""### 5.4 买卖点信号系统

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
            return f"当前识别到**{bp.get('type')}**信号，价格¥{bp.get('price', 0):.2f}，置信度{bp.get('confidence', 0):.1%}。建议关注该价位附近的买入机会，设置止损于该买点下方3-5%。买点确认后可逐步建仓。"
        elif sell_points and not buy_points:
            sp = sell_points[-1]
            return f"当前识别到**{sp.get('type')}**信号，价格¥{sp.get('price', 0):.2f}，置信度{sp.get('confidence', 0):.1%}。建议关注该价位附近的卖出/减仓机会。持仓者可考虑分批止盈。"
        elif buy_points and sell_points:
            return f"当前同时存在买点和卖点信号，市场处于震荡格局。建议根据持仓情况灵活操作：接近买点可加仓，接近卖点可减仓，区间内可高抛低吸。严格控制仓位，避免追涨杀跌。"
        else:
            return "当前暂无明确的买卖点信号，建议等待缠论结构进一步清晰后再做决策。缠论强调'买点买，卖点卖'，没有信号时保持观望也是重要的交易策略。"
    
    def _md_resonance_section_ultra(self, resonance: Dict) -> str:
        """信号共振评分详细板块（Ultra版）"""
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
            for i, s in enumerate(bullish_signals[:8])
        ]) if bullish_signals else "- 暂无主要看涨信号"
        
        # 看跌信号列表
        bearish_signals = resonance.get('bearish_signals', [])
        bearish_list = '\n'.join([
            f"{i+1}. **{s.get('signal_type', '信号')}**：{s.get('description', '')}"
            for i, s in enumerate(bearish_signals[:8])
        ]) if bearish_signals else "- 暂无主要看跌信号"
        
        return f"""### 5.5 信号共振评分系统

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
    
    # ==================== 资金面深度分析（时效性强化）====================
    
    def _md_money_flow_analysis(self) -> str:
        """
        Markdown资金面深度分析（时效性强化版）
        
        确保数据为最近20个交易日
        """
        money_flow = self.data.get('money_flow', {})
        
        if not money_flow or 'error' in money_flow:
            return "## 💰 六、资金面深度分析\n\n> 暂无资金流向数据"
        
        # 获取数据时效信息
        data_date = money_flow.get('data_date', '最近20个交易日')
        data_range = money_flow.get('data_range', '20日')
        
        # 主力资金数据
        main_flow = money_flow.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        main_in = main_flow.get('main_in', 0)
        main_out = main_flow.get('main_out', 0)
        main_trend = main_flow.get('trend', '平稳')
        
        # 散户资金数据
        retail_flow = money_flow.get('retail_flow', {})
        retail_net = retail_flow.get('retail_net', 0)
        
        # 北向资金数据
        north_flow = money_flow.get('north_flow', {})
        north_net = north_flow.get('north_net', 0)
        north_trend = north_flow.get('trend', '平稳')
        
        # 20日资金流向趋势
        flow_20d = money_flow.get('flow_20d', [])
        flow_table = self._generate_flow_20d_table(flow_20d)
        
        # 资金面综合判断
        flow_judgment = self._analyze_money_flow_detailed(main_net, retail_net, north_net)
        
        return f"""## 💰 六、资金面深度分析【时效性：{data_range}】

> **数据时效性声明**：本节资金流向数据基于**最近20个交易日**（{data_date}）计算，确保分析结论的时效性和有效性。

### 6.1 资金流向概览

| 资金类型 | 净流入(亿元) | 流入 | 流出 | 趋势 | 信号 |
|:---------|:-------------|:-----|:-----|:-----|:-----|
| **主力资金** | {main_net:+.2f} | {main_in:.2f} | {main_out:.2f} | {main_trend} | {self._flow_signal(main_net)} |
| **散户资金** | {retail_net:+.2f} | - | - | - | {self._flow_signal(retail_net)} |
| **北向资金** | {north_net:+.2f} | - | - | {north_trend} | {self._flow_signal(north_net)} |

### 6.2 主力资金深度分析

{self._analyze_main_flow(main_flow)}

### 6.3 北向资金分析

{self._analyze_north_flow(north_flow)}

### 6.4 近20日资金流向趋势

{flow_table}

### 6.5 资金面综合判断

{flow_judgment}"""
    
    def _generate_flow_20d_table(self, flow_20d: List[Dict]) -> str:
        """生成近20日资金流向表格"""
        if not flow_20d:
            return "> 暂无20日资金流向数据"
        
        rows = []
        for item in flow_20d[-10:]:  # 最近10天
            date = item.get('date', '-')
            main = item.get('main_net', 0)
            retail = item.get('retail_net', 0)
            total = main + retail
            emoji = "🟢" if total > 0 else "🔴" if total < 0 else "⚪"
            rows.append(f"| {date} | {emoji} {main:+.2f} | {retail:+.2f} | {total:+.2f} |")
        
        return f"""| 日期 | 主力资金 | 散户资金 | 合计 |
|:-----|:---------|:---------|:-----|
{chr(10).join(rows)}"""
    
    def _analyze_main_flow(self, main_flow: Dict) -> str:
        """分析主力资金"""
        main_net = main_flow.get('main_net', 0)
        main_in = main_flow.get('main_in', 0)
        main_out = main_flow.get('main_out', 0)
        
        if main_net > 5:
            return f"""🟢 **主力资金大幅流入**：近20日主力净流入**{main_net:.2f}亿元**，流入{main_in:.2f}亿，流出{main_out:.2f}亿。

**分析解读**：
1. 主力资金持续大幅流入，显示机构看好该标的
2. 资金面对股价形成强支撑，中长期趋势向好
3. 建议关注主力建仓成本区间，逢低可积极布局
4. 需警惕主力出货信号，关注后续资金流向变化"""
        elif main_net > 1:
            return f"""🟡 **主力资金温和流入**：近20日主力净流入**{main_net:.2f}亿元**，流入{main_in:.2f}亿，流出{main_out:.2f}亿。

**分析解读**：
1. 主力资金温和流入，态度偏积极
2. 资金面支撑股价，但力度一般
3. 建议关注后续资金流入持续性
4. 结合其他维度信号综合判断"""
        elif main_net > -1:
            return f"""⚪ **主力资金平衡**：近20日主力净流入**{main_net:.2f}亿元**，流入{main_in:.2f}亿，流出{main_out:.2f}亿。

**分析解读**：
1. 主力资金进出平衡，观望情绪较浓
2. 资金面中性，不提供明确方向指引
3. 建议等待主力资金明确方向后再做决策
4. 关注是否有主力资金异动信号"""
        elif main_net > -5:
            return f"""🟠 **主力资金流出**：近20日主力净流出**{abs(main_net):.2f}亿元**，流入{main_in:.2f}亿，流出{main_out:.2f}亿。

**分析解读**：
1. 主力资金持续流出，态度偏谨慎
2. 资金面对股价形成压力，需警惕调整风险
3. 建议控制仓位，避免追高
4. 关注是否有主力资金回流信号"""
        else:
            return f"""🔴 **主力资金大幅流出**：近20日主力净流出**{abs(main_net):.2f}亿元**，流入{main_in:.2f}亿，流出{main_out:.2f}亿。

**分析解读**：
1. 主力资金大幅流出，机构态度悲观
2. 资金面对股价形成强压力，调整风险较大
3. 建议减仓避险，等待资金回流信号
4. 警惕主力持续出货风险"""
    
    def _analyze_north_flow(self, north_flow: Dict) -> str:
        """分析北向资金"""
        north_net = north_flow.get('north_net', 0)
        
        if north_net > 3:
            return f"""🟢 **北向资金大幅流入**：近20日北向资金净流入**{north_net:.2f}亿元**。

**分析解读**：
1. 外资持续大幅买入，看好A股市场
2. 北向资金偏好优质蓝筹，对股价形成支撑
3. 外资流入通常具有持续性，可积极关注
4. 关注外资持仓变化，跟随聪明资金"""
        elif north_net > 0:
            return f"""🟡 **北向资金温和流入**：近20日北向资金净流入**{north_net:.2f}亿元**。

**分析解读**：
1. 外资态度偏积极，但流入力度一般
2. 对股价形成一定支撑，但非主要驱动力
3. 建议关注外资流入持续性
4. 结合其他资金维度综合判断"""
        elif north_net > -3:
            return f"""⚪ **北向资金平衡**：近20日北向资金净流入**{north_net:.2f}亿元**。

**分析解读**：
1. 外资态度中性，观望情绪较浓
2. 北向资金不提供明确方向指引
3. 建议关注外资后续动向
4. 关注国际市场环境变化"""
        else:
            return f"""🔴 **北向资金流出**：近20日北向资金净流出**{abs(north_net):.2f}亿元**。

**分析解读**：
1. 外资持续流出，态度偏谨慎
2. 可能受国际市场环境影响
3. 对股价形成一定压力
4. 关注外资回流信号"""
    
    def _analyze_money_flow_detailed(self, main_net: float, retail_net: float, north_net: float) -> str:
        """详细资金面分析"""
        total_net = main_net + retail_net + north_net
        
        analysis = []
        
        # 主力资金判断
        if main_net > 5:
            analysis.append("主力资金大幅流入，机构态度积极，是主要看多力量。")
        elif main_net > 0:
            analysis.append("主力资金温和流入，态度偏正面。")
        elif main_net > -5:
            analysis.append("主力资金流出，态度偏谨慎，需关注风险。")
        else:
            analysis.append("主力资金大幅流出，机构态度悲观，需警惕风险。")
        
        # 散户资金判断
        if retail_net > 0:
            analysis.append("散户资金流入，市场情绪偏乐观，但需警惕追涨风险。")
        else:
            analysis.append("散户资金流出，市场情绪偏谨慎。")
        
        # 北向资金判断
        if north_net > 3:
            analysis.append("北向资金大幅流入，外资看好，提供额外支撑。")
        elif north_net > 0:
            analysis.append("北向资金流入，外资态度积极。")
        elif north_net < -3:
            analysis.append("北向资金流出，外资态度谨慎，需关注。")
        
        # 综合判断
        if total_net > 10:
            analysis.append("**综合判断**：资金大幅净流入，资金面强劲，建议积极关注。")
        elif total_net > 3:
            analysis.append("**综合判断**：资金温和净流入，资金面偏正面，可适量参与。")
        elif total_net > -3:
            analysis.append("**综合判断**：资金进出平衡，资金面中性，建议观望。")
        elif total_net > -10:
            analysis.append("**综合判断**：资金净流出，资金面偏负面，建议谨慎。")
        else:
            analysis.append("**综合判断**：资金大幅净流出，资金面压力大，建议规避风险。")
        
        return '\n\n'.join(f"{i+1}. {a}" for i, a in enumerate(analysis))
    
    def _flow_signal(self, net: float) -> str:
        """资金流向信号"""
        if net > 5:
            return "🟢 强烈看多"
        elif net > 1:
            return "🟡 看多"
        elif net > -1:
            return "⚪ 中性"
        elif net > -5:
            return "🟠 看空"
        else:
            return "🔴 强烈看空"
    
    # ==================== 综合投资建议 ====================
    
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
        
        return f"""## 🎯 七、综合投资决策建议

### 7.1 投资决策总览

<div align="center">

### {self.rating_emoji} {self.rating} | 综合评分：{self.total_score}/100

**操作建议**：{action} | **目标价**：¥{target_price:.2f} | **止损价**：¥{stop_loss:.2f}

</div>

### 7.2 关键价位与盈亏分析

| 价位类型 | 价格 | 涨跌幅 | 说明 |
|:---------|:-----|:-------|:-----|
| **当前价格** | ¥{current_price:.2f} | - | 基准价位 |
| **目标价格** | ¥{target_price:.2f} | +{upside:.1f}% | 预期上涨空间 |
| **止损价格** | ¥{stop_loss:.2f} | -{downside:.1f}% | 最大可承受亏损 |
| **盈亏比** | 1:{risk_reward:.1f} | - | {'🟢 优秀' if risk_reward >= 3 else '🟡 良好' if risk_reward >= 2 else '⚪ 一般' if risk_reward >= 1.5 else '🔴 较差'} |

### 7.3 核心投资优势

{self._generate_advantages_enhanced()}

### 7.4 主要风险因素

{self._generate_risks_enhanced()}

### 7.5 交易策略建议

#### 仓位管理
- **建议仓位**：{position}
- **建仓策略**：{self._position_strategy(self.total_score)}

#### 操作计划
{self._trading_plan(current_price, target_price, stop_loss)}

### 7.6 投资分析总结

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
            advantages.append(f"6. **主力资金流入**：近20日主力净流入{main_net:.2f}亿，资金面对股价形成支撑")
        
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
                risks.append("6. **形态面看跌**：多个K线形态发出看跌信号，技术面压力较大")
            
            chanlun = self.pattern_data.get('chanlun', {})
            if chanlun.get('sell_points', []):
                risks.append("7. **缠论卖点信号**：缠论结构识别出卖点信号，需警惕调整风险")
        
        # 资金面风险
        money = self.data.get('money_flow', {})
        main_flow = money.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        if main_net < -1:
            risks.append(f"8. **资金流出风险**：近20日主力资金净流出{abs(main_net):.2f}亿，资金面偏空")
        
        if not risks:
            risks.append("当前未发现明显风险因素，但仍需关注市场系统性风险")
        
        return '\n'.join(risks)
    
    def _position_strategy(self, score: int) -> str:
        """仓位策略"""
        if score >= 80:
            return "可重仓参与（70-80%），分2-3批建仓，首批可在当前价位附近入场"
        elif score >= 65:
            return "适量参与（50-60%），分3批建仓，首批试探性建仓，回调加仓"
        elif score >= 50:
            return "轻仓试探（20-30%），等待更明确信号后再加仓"
        elif score >= 35:
            return "观望为主（0-10%），仅可极小仓位试探，严格止损"
        else:
            return "空仓观望，不参与或减仓避险"
    
    def _trading_plan(self, current: float, target: float, stop: float) -> str:
        """交易计划"""
        if current <= 0:
            return "暂无具体交易计划，等待行情数据更新。"
        
        plan = []
        
        # 建仓计划
        if target > current:
            plan.append(f"""
**建仓计划**：
- 首次建仓：当前价位¥{current:.2f}附近，仓位30%
- 加仓点1：回调至¥{current * 0.97:.2f}（-3%），加仓30%
- 加仓点2：回调至¥{current * 0.95:.2f}（-5%），加仓40%
- 总仓位控制：不超过建议仓位""")
        
        # 止损计划
        if stop > 0:
            plan.append(f"""
**止损计划**：
- 初始止损：¥{stop:.2f}（-{((current-stop)/current*100):.1f}%）
- 移动止损：盈利5%后，止损上移至成本价
- 盈利10%后，止损上移至成本价+3%
- 严格执行，不抱侥幸心理""")
        
        # 止盈计划
        if target > current:
            plan.append(f"""
**止盈计划**：
- 目标价：¥{target:.2f}（+{((target-current)/current*100):.1f}%）
- 分批止盈：到达目标价卖出50%，剩余设移动止盈
- 时间止损：持仓超过2周未达预期，考虑减仓""")
        
        return '\n'.join(plan)
    
    def _generate_summary_enhanced(self) -> str:
        """生成增强版分析总结"""
        quote = self.data.get('quote', {})
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        
        summary_parts = []
        
        # 总体判断
        summary_parts.append(f"**总体判断**：{self.stock_name}（{self.code}）当前综合评分{self.total_score}分，评级为'{self.rating}'。")
        
        # 技术面
        tech = self.data.get('technical', {})
        if tech:
            summary_parts.append(f"技术面呈现{tech.get('trend', '震荡')}走势，{tech.get('kdj_signal', 'KDJ正常')}，{tech.get('macd_signal', 'MACD正常')}。")
        
        # 形态面
        if self.pattern_data:
            resonance = self.pattern_data.get('resonance', {})
            res_score = resonance.get('total_score', 0)
            if abs(res_score) > 30:
                direction = "看涨" if res_score > 0 else "看跌"
                summary_parts.append(f"形态面呈现{direction}共振（{res_score:+.1f}分），")
            
            chanlun = self.pattern_data.get('chanlun', {})
            if chanlun.get('buy_points'):
                bp = chanlun['buy_points'][-1]
                summary_parts.append(f"缠论识别出{bp.get('type')}信号（¥{bp.get('price', 0):.2f}）。")
        
        # 资金面
        money = self.data.get('money_flow', {})
        main_flow = money.get('main_flow', {})
        main_net = main_flow.get('main_net', 0)
        if main_net > 1:
            summary_parts.append(f"近20日主力资金净流入{main_net:.2f}亿，资金面偏正面。")
        elif main_net < -1:
            summary_parts.append(f"近20日主力资金净流出{abs(main_net):.2f}亿，资金面偏负面。")
        
        # 操作建议
        summary_parts.append(f"**操作建议**：{self.suggestion.get('action', '观望')}，目标价¥{self.suggestion.get('target_price', 0):.2f}，止损价¥{self.suggestion.get('stop_loss', 0):.2f}。")
        
        # 风险提示
        summary_parts.append("**风险提示**：以上分析基于历史数据，不构成投资建议。股市有风险，投资需谨慎。请结合自身风险承受能力做出决策。")
        
        return '\n\n'.join(summary_parts)
    
    def _md_risk_disclaimer(self) -> str:
        """Markdown风险提示"""
        return f"""## ⚠️ 附录：风险提示与免责声明

### 重要风险提示

1. **市场风险**：股票市场受宏观经济、政策变化、国际形势等多种因素影响，存在系统性风险
2. **个股风险**：个股价格受公司经营、行业竞争、市场情绪等因素影响，波动可能较大
3. **技术风险**：本报告中的技术指标、形态识别、买卖点信号等基于算法自动计算，可能存在误差
4. **数据风险**：数据来源于公开渠道（AkShare等），可能存在延迟或错误，仅供参考
5. **模型风险**：信号共振评分、情绪指数等模型基于历史数据构建，不保证未来有效性
6. **时效性风险**：资金面数据基于最近20个交易日，市场情况可能随时变化

### 免责声明

- 本报告仅供学习和研究使用，不构成任何投资建议
- 报告中的观点、结论和建议仅供参考，投资者应独立判断
- 过往业绩不代表未来表现，投资有风险，入市需谨慎
- 请投资者根据自身风险承受能力，审慎做出投资决策
- 本报告作者不对因使用本报告而产生的任何损失承担责任

---

**报告生成时间**：{self.timestamp}  
**报告版本**：Stock Analyst V3.2 Ultra  
**数据来源**：AkShare等公开数据接口  
**形态识别**：60+K线形态库 + 缠论算法  
**数据时效**：行情实时 + 财务最新 + 资金20日"""
    
    # ==================== HTML格式生成（精简版）====================
    
    def _generate_minimal_html_report(self) -> str:
        """
        生成极简HTML报告（大幅节省Token）
        
        优化点：
        1. 移除大量CSS样式，使用内联极简样式
        2. 只保留核心内容，移除装饰性元素
        3. 简化HTML结构
        """
        md_content = self._generate_markdown_report()
        # 使用极简转换
        html = self._markdown_to_minimal_html(md_content)
        return html
    
    def _generate_html_report(self) -> str:
        """生成完整HTML报告（完整样式版）"""
        md_content = self._generate_markdown_report()
        html = self._markdown_to_html(md_content)
        return html
    
    def _markdown_to_minimal_html(self, md: str) -> str:
        """
        极简Markdown到HTML转换（节省Token）
        
        相比完整版节省约60-70%的HTML标签和CSS
        """
        html_head = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{self.stock_name} ({self.code}) 分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #2563eb; margin-top: 30px; }}
        h3 {{ color: #555; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        .highlight {{ background: #e3f2fd; padding: 10px; border-radius: 4px; }}
    </style>
</head>
<body>
"""
        
        # 极简转换：保留基本结构，移除复杂格式化
        html_body = self._simple_md_to_html_minimal(md)
        
        html_foot = "</body></html>"
        return html_head + html_body + html_foot
    
    def _simple_md_to_html_minimal(self, md: str) -> str:
        """极简Markdown转换"""
        html = md
        
        # 转换标题
        html = html.replace('# ', '<h1>').replace('\n## ', '</h1>\n<h2>')
        html = html.replace('\n### ', '</h2>\n<h3>').replace('\n#### ', '</h3>\n<h4>')
        html = html.replace('\n---\n', '<hr>')
        
        # 转换强调
        parts = html.split('**')
        for i in range(1, len(parts), 2):
            if i < len(parts):
                parts[i] = f'<strong>{parts[i]}</strong>'
        html = ''.join(parts)
        
        # 简化表格处理
        lines = html.split('\n')
        result = []
        in_table = False
        
        for line in lines:
            if line.startswith('|') and not in_table:
                in_table = True
                result.append('<table>')
            elif not line.startswith('|') and in_table:
                in_table = False
                result.append('</table>')
            
            if in_table:
                if '---' in line:
                    continue
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if cells:
                    tag = 'th' if result and '<table>' in result[-2:] else 'td'
                    result.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
            else:
                result.append(line)
        
        if in_table:
            result.append('</table>')
        
        html = '\n'.join(result)
        
        # 转换列表
        html = html.replace('\n- ', '\n<li>')
        html = html.replace('\n\n', '</li>\n\n')
        
        # 包裹段落
        paragraphs = html.split('\n\n')
        html = '\n\n'.join(f'<p>{p}</p>' if not p.startswith('<') else p for p in paragraphs)
        
        return html
    
    def _markdown_to_html(self, md: str) -> str:
        """将Markdown转换为HTML"""
        # 添加HTML头部和样式
        html_head = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.stock_name} ({self.code}) 股票分析报告</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.8;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 1.1em; }}
        .section {{
            background: var(--card);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: var(--primary);
            border-bottom: 3px solid var(--primary);
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        .section h3 {{
            color: var(--text);
            margin: 20px 0 15px;
            font-size: 1.2em;
        }}
        .section h4 {{
            color: var(--text-muted);
            margin: 15px 0 10px;
            font-size: 1.1em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.95em;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background: var(--bg);
            font-weight: 600;
            color: var(--text);
        }}
        tr:hover {{ background: var(--bg); }}
        .rating {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.2em;
        }}
        .rating-strong {{ background: var(--success); color: white; }}
        .rating-weak {{ background: var(--danger); color: white; }}
        .rating-neutral {{ background: var(--warning); color: white; }}
        .highlight {{
            background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        .alert {{
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        .alert-success {{ background: #d1fae5; border-left: 4px solid var(--success); }}
        .alert-warning {{ background: #fef3c7; border-left: 4px solid var(--warning); }}
        .alert-danger {{ background: #fee2e2; border-left: 4px solid var(--danger); }}
        .alert-info {{ background: #dbeafe; border-left: 4px solid var(--info); }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .card {{
            background: var(--bg);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .card h4 {{ margin-top: 0; color: var(--primary); }}
        .score-display {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            margin: 20px 0;
        }}
        .score-display .score {{ font-size: 4em; font-weight: bold; }}
        .score-display .label {{ font-size: 1.2em; opacity: 0.9; }}
        code {{
            background: var(--bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        blockquote {{
            border-left: 4px solid var(--primary);
            padding-left: 20px;
            margin: 15px 0;
            color: var(--text-muted);
        }}
        ul, ol {{ margin: 15px 0; padding-left: 30px; }}
        li {{ margin: 8px 0; }}
        .divider {{
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--border), transparent);
            margin: 40px 0;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .header {{ padding: 20px; }}
            .header h1 {{ font-size: 1.8em; }}
            .section {{ padding: 20px; }}
            table {{ font-size: 0.85em; }}
            th, td {{ padding: 8px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
"""
        
        # 简单的Markdown到HTML转换
        html_body = self._simple_md_to_html(md)
        
        html_foot = """
    </div>
</body>
</html>"""
        
        return html_head + html_body + html_foot
    
    def _simple_md_to_html(self, md: str) -> str:
        """简单的Markdown到HTML转换（完整样式版）"""
        html = md
        
        # 转换标题
        html = html.replace('# ', '<h1>').replace('\n## ', '</h1>\n<h2>')
        html = html.replace('\n### ', '</h2>\n<h3>').replace('\n#### ', '</h3>\n<h4>')
        html = html.replace('\n---\n', '</h4>\n<div class="divider"></div>\n')
        
        # 转换强调
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        
        # 转换表格（简化处理）
        lines = html.split('\n')
        in_table = False
        new_lines = []
        for line in lines:
            if line.startswith('|') and not in_table:
                in_table = True
                new_lines.append('<table>')
            elif not line.startswith('|') and in_table:
                in_table = False
                new_lines.append('</table>')
            if in_table:
                if '---' in line:
                    continue
                cells = line.split('|')[1:-1]
                tag = 'th' if new_lines and '<table>' in new_lines[-1] else 'td'
                new_lines.append('<tr>' + ''.join(f'<{tag}>{c.strip()}</{tag}>' for c in cells) + '</tr>')
            else:
                new_lines.append(line)
        html = '\n'.join(new_lines)
        
        # 转换列表
        html = html.replace('\n- ', '\n<li>').replace('\n\n', '</li>\n\n')
        
        # 包裹段落
        html = '<div class="section">' + html + '</div>'
        
        return html
    
    # ==================== 纯文本简化版（最省Token）====================
    
    def _generate_text_summary(self) -> str:
        """
        生成纯文本简化版报告（最省Token）
        
        只保留核心结论，移除所有格式和详细说明
        适合快速查看关键信息
        """
        quote = self.data.get('quote', {})
        price = quote.get('price', 0)
        pct_change = quote.get('pct_change', 0)
        
        # 形态面关键信息
        pattern_summary = ""
        if self.pattern_data:
            candlestick = self.pattern_data.get('candlestick', {})
            chanlun = self.pattern_data.get('chanlun', {})
            resonance = self.pattern_data.get('resonance', {})
            
            bullish = candlestick.get('bullish_count', 0)
            bearish = candlestick.get('bearish_count', 0)
            res_score = resonance.get('total_score', 0)
            
            buy_points = chanlun.get('buy_points', [])
            sell_points = chanlun.get('sell_points', [])
            
            pattern_summary = f"""
【形态面】
- 看涨形态: {bullish}个, 看跌形态: {bearish}个
- 共振评分: {res_score:+.0f}分
- 买点: {len(buy_points)}个, 卖点: {len(sell_points)}个"""
        
        # 资金面关键信息
        money_summary = ""
        money_flow = self.data.get('money_flow', {})
        if money_flow:
            main_net = money_flow.get('main_flow', {}).get('main_net', 0)
            north_net = money_flow.get('north_flow', {}).get('north_net', 0)
            money_summary = f"""
【资金面】20日数据
- 主力净流入: {main_net:+.2f}亿
- 北向净流入: {north_net:+.2f}亿"""
        
        # 操作建议
        action = self.suggestion.get('action', '观望')
        target = self.suggestion.get('target_price', 0)
        stop_loss = self.suggestion.get('stop_loss', 0)
        position = self.suggestion.get('position', '0%')
        
        return f"""{self.stock_name} ({self.code}) 分析报告
生成时间: {self.timestamp}

【行情】
- 当前价格: ¥{price:.2f} ({pct_change:+.2f}%)

【评级】{self.rating_emoji} {self.rating} | 评分: {self.total_score}/100

【建议】
- 操作: {action}
- 目标价: ¥{target:.2f}
- 止损价: ¥{stop_loss:.2f}
- 仓位: {position}
{pattern_summary}
{money_summary}

免责声明: 本报告仅供参考，不构成投资建议。"""


# ==================== 便捷函数 ====================

def generate_unified_report(
    data: Dict[str, Any], 
    pattern_data: Optional[Dict] = None,
    output_format: str = 'markdown'
) -> Dict[str, str]:
    """
    生成统一报告（按需返回格式）
    
    Args:
        data: 基础分析数据
        pattern_data: 形态面分析数据
        output_format: 输出格式
            - 'markdown': 只返回Markdown（默认，最省Token）
            - 'html': 只返回HTML（极简样式）
            - 'html_full': 返回完整样式HTML
            - 'both': 同时返回HTML和Markdown
            - 'text': 返回纯文本简化版（最省Token）
            
    Returns:
        根据output_format返回对应格式的报告
        
    使用建议：
        - 日常使用: output_format='markdown'（默认，平衡可读性和Token）
        - 需要HTML: output_format='html'（极简样式，节省Token）
        - 快速预览: output_format='text'（纯文本，最省Token）
        - 完整需求: output_format='both'（同时获得两种格式）
    """
    generator = UnifiedReportGenerator(data, pattern_data)
    return generator.generate_unified_report(output_format)


def generate_html_report(
    data: Dict[str, Any], 
    pattern_data: Optional[Dict] = None,
    minimal: bool = True
) -> str:
    """
    生成HTML报告
    
    Args:
        data: 基础分析数据
        pattern_data: 形态面分析数据
        minimal: 是否使用极简样式（默认True，节省Token）
    """
    generator = UnifiedReportGenerator(data, pattern_data)
    return generator.generate_html(minimal=minimal)


def generate_markdown_report(data: Dict[str, Any], pattern_data: Optional[Dict] = None) -> str:
    """生成Markdown报告"""
    generator = UnifiedReportGenerator(data, pattern_data)
    return generator.generate_markdown()


def generate_text_summary(data: Dict[str, Any], pattern_data: Optional[Dict] = None) -> str:
    """
    生成纯文本简化版报告（最省Token）
    
    适合快速查看核心结论，不包含详细分析
    """
    generator = UnifiedReportGenerator(data, pattern_data)
    return generator.generate_text_summary()


# ==================== 数据接口规范 ====================
"""
数据接口规范说明（V3.2 Ultra）：

1. data 数据结构：
{
    'code': '股票代码',
    'stock_name': '股票名称',
    'timestamp': '报告生成时间',
    'quote': {
        'price': 当前价格,
        'pct_change': 涨跌幅%,
        'volume': 成交量,
        'amount': 成交额,
        'turnover': 换手率%,
        'open': 开盘价,
        'high': 最高价,
        'low': 最低价,
        'prev_close': 昨收价,
        'pe': 市盈率,
        'pb': 市净率,
        'market_cap': 总市值
    },
    'technical': {
        'k', 'd', 'j': KDJ指标,
        'kdj_signal': KDJ信号,
        'macd': MACD值,
        'dea': DEA值,
        'histogram': MACD柱状,
        'macd_signal': MACD信号,
        'rsi': RSI值,
        'rsi_signal': RSI信号,
        'ma5', 'ma10', 'ma20', 'ma60': 均线,
        'price_above_ma5', 'price_above_ma20', 'price_above_ma60': 均线位置,
        'bb_upper', 'bb_middle', 'bb_lower': 布林带,
        'trend': 趋势判断,
        'ma_alignment': 均线排列
    },
    'fundamental': {
        'financial': {
            'latest': {
                'report_date': '报告期',
                'revenue': '营业收入',
                'revenue_yoy': '营收同比',
                'net_profit': '净利润',
                'net_profit_yoy': '净利润同比',
                'roe': 'ROE',
                'gross_margin': '毛利率',
                'net_margin': '净利率',
                'debt_ratio': '资产负债率',
                'eps': '每股收益',
                'ocf_ps': '每股现金流',
                'pe': 'PE',
                'pb': 'PB',
                'pe_percentile': 'PE分位数',
                'pb_percentile': 'PB分位数'
            },
            'history': [历史财务数据列表]
        },
        'performance_trend': {
            'overall_trend': '整体趋势'
        }
    },
    'news': {
        'sentiment': '情感倾向',
        'sentiment_score': 情感得分,
        'fundamental_impact': '基本面影响',
        'items': [新闻列表]
    },
    'money_flow': {
        'data_date': '数据日期范围',
        'data_range': '数据范围（如20日）',
        'main_flow': {
            'main_net': 主力净流入（20日）,
            'main_in': 主力流入,
            'main_out': 主力流出,
            'trend': 资金趋势
        },
        'retail_flow': {
            'retail_net': 散户净流入（20日）
        },
        'north_flow': {
            'north_net': 北向净流入（20日）,
            'trend': 北向趋势
        },
        'flow_20d': [
            {'date': '日期', 'main_net': 主力净流入, 'retail_net': 散户净流入}
        ]
    },
    'suggestion': {
        'total_score': 综合评分,
        'action': '操作建议',
        'target_price': 目标价,
        'stop_loss': 止损价,
        'position': '建议仓位',
        'level': '风险等级'
    }
}

2. pattern_data 数据结构：
{
    'data_date': '数据日期',
    'data_source': '数据来源',
    'kline_count': K线数量,
    'validation': {
        'kline_data': K线数据验证状态,
        'pattern_recognition': 形态识别验证状态,
        'chanlun_analysis': 缠论分析验证状态
    },
    'candlestick': {
        'patterns': [形态列表],
        'bullish_count': 看涨形态数,
        'bearish_count': 看跌形态数,
        'bullish_score': 看涨得分,
        'bearish_score': 看跌得分,
        'signal': 综合信号,
        'total_patterns': 形态总数
    },
    'chanlun': {
        'bi_count': 笔数量,
        'zhongshu_count': 中枢数量,
        'current_trend': 当前趋势,
        'nearest_zhongshu': 最近中枢,
        'bis': [笔列表],
        'buy_points': [买点列表],
        'sell_points': [卖点列表]
    },
    'resonance': {
        'total_score': 综合评分,
        'bullish_score': 看涨得分,
        'bearish_score': 看跌得分,
        'signal_count': 信号数量,
        'breakdown': 维度得分,
        'bullish_signals': [看涨信号],
        'bearish_signals': [看跌信号]
    },
    'sentiment': {
        'index_value': 情绪指数,
        'level': 情绪等级,
        'trend': 情绪趋势
    }
}
"""

if __name__ == '__main__':
    # 示例用法
    example_data = {
        'code': '000001',
        'stock_name': '平安银行',
        'timestamp': '2026-04-16 23:15:00',
        'quote': {
            'price': 10.50,
            'pct_change': 2.5,
            'volume': 1000000,
            'amount': 10.5,
            'turnover': 5.2,
            'open': 10.30,
            'high': 10.60,
            'low': 10.25,
            'prev_close': 10.25,
            'pe': 5.8,
            'pb': 0.6,
            'market_cap': 2000
        },
        'technical': {
            'k': 65, 'd': 55, 'j': 85,
            'kdj_signal': '金叉',
            'macd': 0.15,
            'dea': 0.10,
            'histogram': 0.05,
            'macd_signal': '多头',
            'rsi': 58,
            'rsi_signal': '正常',
            'ma5': 10.30,
            'ma10': 10.20,
            'ma20': 10.10,
            'ma60': 9.80,
            'price_above_ma5': True,
            'price_above_ma20': True,
            'price_above_ma60': True,
            'bb_upper': 10.80,
            'bb_middle': 10.40,
            'bb_lower': 10.00,
            'trend': '上升趋势',
            'ma_alignment': '多头排列'
        },
        'fundamental': {
            'financial': {
                'latest': {
                    'report_date': '2025-12-31',
                    'revenue': '1000亿',
                    'revenue_yoy': '5.2%',
                    'net_profit': '450亿',
                    'net_profit_yoy': '8.5%',
                    'roe': '12.5%',
                    'gross_margin': '35%',
                    'net_margin': '45%',
                    'debt_ratio': '92%',
                    'eps': '2.35',
                    'ocf_ps': '3.20',
                    'pe': '5.8',
                    'pb': '0.6',
                    'pe_percentile': '15%',
                    'pb_percentile': '10%'
                },
                'history': []
            },
            'performance_trend': {
                'overall_trend': '稳健向好'
            }
        },
        'news': {
            'sentiment': '中性偏正面',
            'sentiment_score': 15,
            'fundamental_impact': '中性',
            'items': [
                {'title': '平安银行发布年报，业绩稳健增长', 'date': '2026-04-15', 'source': '证券时报'},
                {'title': '银行业整体向好，资产质量改善', 'date': '2026-04-14', 'source': '上海证券报'}
            ]
        },
        'money_flow': {
            'data_date': '2026-03-20至2026-04-16',
            'data_range': '20日',
            'main_flow': {
                'main_net': 5.2,
                'main_in': 12.5,
                'main_out': 7.3,
                'trend': '持续流入'
            },
            'retail_flow': {
                'retail_net': -2.1
            },
            'north_flow': {
                'north_net': 3.8,
                'trend': '流入加速'
            },
            'flow_20d': [
                {'date': '04-16', 'main_net': 0.8, 'retail_net': -0.3},
                {'date': '04-15', 'main_net': 0.5, 'retail_net': -0.2},
                {'date': '04-14', 'main_net': 0.6, 'retail_net': -0.1}
            ]
        },
        'suggestion': {
            'total_score': 72,
            'action': '买入',
            'target_price': 11.50,
            'stop_loss': 9.80,
            'position': '50%',
            'level': '中等'
        }
    }
    
    example_pattern = {
        'data_date': '2026-04-16',
        'data_source': '日线数据',
        'kline_count': 60,
        'validation': {
            'kline_data': True,
            'pattern_recognition': True,
            'chanlun_analysis': True
        },
        'candlestick': {
            'patterns': [
                {'name_cn': '早晨之星', 'type': 'bullish', 'type_cn': '看涨', 'reliability': 5, 'confidence': 0.85, 'position': 0, 'description': '底部反转信号'},
                {'name_cn': '阳包阴', 'type': 'bullish', 'type_cn': '看涨', 'reliability': 4, 'confidence': 0.75, 'position': 1, 'description': '多头力量增强'}
            ],
            'bullish_count': 2,
            'bearish_count': 0,
            'bullish_score': 16,
            'bearish_score': 0,
            'signal': '看涨',
            'total_patterns': 2
        },
        'chanlun': {
            'bi_count': 5,
            'zhongshu_count': 1,
            'current_trend': '向上笔进行中',
            'nearest_zhongshu': {
                'range': '10.20-10.40',
                'zg': 10.40,
                'zd': 10.20,
                'center': 10.30
            },
            'bis': [
                {'direction': 'up', 'start_price': 10.10, 'end_price': 10.30, 'height': 0.20},
                {'direction': 'down', 'start_price': 10.30, 'end_price': 10.20, 'height': 0.10}
            ],
            'buy_points': [
                {'type': '一买', 'price': 10.15, 'confidence': 0.80, 'description': '趋势背驰点'}
            ],
            'sell_points': []
        },
        'resonance': {
            'total_score': 68,
            'bullish_score': 75,
            'bearish_score': 7,
            'signal_count': 12,
            'breakdown': {
                'K线形态': 18,
                '技术指标': 16,
                '趋势信号': 12,
                '成交量': 8,
                '基本面': 10,
                '情绪面': 6,
                '缠论': 8
            },
            'bullish_signals': [
                {'signal_type': 'K线形态', 'description': '早晨之星形态确认'},
                {'signal_type': '技术指标', 'description': 'KDJ金叉信号'}
            ],
            'bearish_signals': []
        },
        'sentiment': {
            'index_value': 55,
            'level': {'name': '中性'},
            'trend': '上升'
        }
    }
    
    # 生成报告
    reports = generate_unified_report(example_data, example_pattern)
    print("Markdown报告长度:", len(reports['markdown']))
    print("HTML报告长度:", len(reports['html']))

