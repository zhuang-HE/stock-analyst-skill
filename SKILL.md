---
name: stock-analyst
version: 5.1.0
description: 'Load when: 用户要求分析某只股票的技术面、问K线形态、缠论买卖点、信号共振、情绪指数、五维分析、综合评分、投资建议、决策仪表盘、买卖点位、狙击点。 不加载：用户只想查实时行情、财报数据、资金流向等数据获取需求（→ tushare-data）。提供Tushare/AkShare双数据源。'
author: zhuang-HE
tags:
- 技术分析
- K线形态
- 缠论
- 买卖点
- 信号共振
- 情绪指数
- 形态识别
- 五维分析
- 综合分析
- 股票评分
- 投资建议
- MA
- RSI
- KDJ
- MACD
- 布林带
- 均线系统
- 决策仪表盘
- 狙击点
- 止损位
- 仓位建议
- 风险收益比
- 斐波那契
- 早晨之星
- 黄昏之星
- 锤头线
- 一买
- 二买
- 三买
- 中枢
- 笔
- 贪婪恐慌指数
- 共振评分
created: 2026-04-10
updated: 2026-06-10
allowed-tools: Edit, PowerShell, Skill
triggers:
- 技术分析
- K线形态
- 缠论买卖点
- 信号共振
- 股票评分
- 投资建议
- 五维分析
- stock analyst
- technical analysis
- 形态识别
- 决策仪表盘
- 分析一下
- 买卖点位
- 狙击点
- 止损
- 仓位
- 综合分析
---

# Stock Analyst v5.0 — 决策仪表盘版

**架构变更（v5.0）**：新增决策仪表盘输出格式（四段式：核心结论→数据透视→情报解读→作战计划），集成买卖点位计算，保留 v4 兼容 JSON 输出。

## 协作模式

```
tushare-data (数据层) → JSON 数据文件 → stock-analyst (分析+决策层) → 决策仪表盘 / 完整JSON
```

**数据获取** → `tushare-data` Skill
**分析+决策** → 本 Skill（算法计算 + AI agent 生成 LLM 解读文字）

## 什么时候用本 Skill

- 用户要求**技术分析**（MA/RSI/KDJ/MACD/布林带）
- 用户要求**K线形态识别**（60+种形态）
- 用户要求**缠论买卖点**分析
- 用户要求**信号共振评分**
- 用户要求**情绪指数**计算
- 用户要求**五维分析**或**综合分析**
- 用户要求**投资建议**、**买卖点位**、**止损位**、**仓位建议**
- 用户要求**决策仪表盘**、**狙击点**、**风险收益比**

## 什么时候不用本 Skill

- 用户只想**查行情** → tushare-data
- 用户只想**查财报** → tushare-data
- 用户只想**看资金流向** → tushare-data
- 用户要求**数据导出** → tushare-data

## 执行流程

### 完整分析流程

当用户要求"分析XXX"时，按以下步骤执行：

1. **调用 tushare-data** 获取数据（Tushare优先，AkShare备选），保存为 JSON 文件
2. **调用本 Skill** 执行分析脚本，输出决策仪表盘
3. **AI agent 执行新闻搜索**，通过 WebSearch 获取舆情补充
4. **AI agent 生成 LLM 解读**，基于仪表盘的 `llm_context` + 新闻搜索结果生成完整报告

#### Step 1: 数据获取（Tushare 优先 + AkShare Fallback）

用 Python 脚本一次性获取所有需要的数据，Tushare 失败时自动降级到 AkShare：

```python
import json, os, sys
from datetime import datetime, timedelta

code = sys.argv[1]  # 如 "300263"
ts_code = f"{code}.SZ" if code.startswith(('0','3')) else f"{code}.SH"
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=400)).strftime('%Y%m%d')

data = {'code': code, 'ts_code': ts_code}
use_tushare = False

# --- 尝试 Tushare ---
try:
    import tushare as ts
    token = os.environ.get('TUSHARE_TOKEN', '')
    if token:
        pro = ts.pro_api(token)
        # 测试连接
        df = pro.daily(ts_code=ts_code, start_date=end_date, end_date=end_date)
        if df is not None and len(df) > 0:
            use_tushare = True
            print("数据源: Tushare")
except Exception:
    pass

if use_tushare:
    # 使用 Tushare 获取全部数据
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        data['daily'] = df.to_dict('records') if df is not None else []
    except: data['daily'] = []
    try:
        df = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        data['daily_basic'] = df.to_dict('records') if df is not None else []
    except: data['daily_basic'] = []
    try:
        df = pro.income(ts_code=ts_code, period_type='1')
        data['income'] = df.to_dict('records')[:8] if df is not None else []
    except: data['income'] = []
    try:
        df = pro.fina_indicator(ts_code=ts_code)
        data['fina_indicator'] = df.to_dict('records')[:8] if df is not None else []
    except: data['fina_indicator'] = []
    try:
        df = pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
        data['moneyflow'] = df.to_dict('records') if df is not None else []
    except: data['moneyflow'] = []
    try:
        df = pro.news(src='sina', start_date=(datetime.now()-timedelta(days=7)).strftime('%Y%m%d'))
        data['news'] = df.to_dict('records')[:10] if df is not None else []
    except: data['news'] = []
    try:
        df = pro.forecast(ts_code=ts_code)
        data['forecast'] = df.to_dict('records')[:5] if df is not None else []
    except: data['forecast'] = []
else:
    # Fallback: AkShare（免费开源，无需 Token）
    print("Tushare不可用，降级到 AkShare")
    try:
        import akshare as ak
        # A股日线
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                start_date=start_date, end_date=end_date,
                                adjust="qfq")
        if df is not None and len(df) > 0:
            # 列名映射 AkShare -> 标准名
            col_map = {
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount',
                '涨跌幅': 'pct_change'
            }
            df = df.rename(columns=col_map)
            if 'date' in df.columns:
                df['date'] = df['date'].astype(str).str.replace('-', '')
            data['daily'] = df.to_dict('records')
        else:
            data['daily'] = []
    except:
        data['daily'] = []
        print("AkShare 日线获取失败，请检查网络")

    # AkShare 不提供 PE/PB/财务等详细数据，这些字段留空
    data['daily_basic'] = []
    data['income'] = []
    data['fina_indicator'] = []
    data['moneyflow'] = []
    data['news'] = []
    data['forecast'] = []

# 保存
out_path = os.path.join(os.environ.get('TEMP', '/tmp'), f'stock_data_{code}.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, default=str)
print(f"DATA_FILE={out_path}")
```

#### Step 2: 执行分析

```bash
# 默认输出决策仪表盘（推荐）
python <skill_dir>/scripts/full_analysis.py <data_json_path> <code>

# 输出完整 JSON（v4 兼容格式）
python <skill_dir>/scripts/full_analysis.py <data_json_path> <code> --format json
```

#### Step 3: 新闻舆情补充（AI agent 执行）

分析完成后，AI agent 应使用 **WebSearch** 工具搜索近期舆情：

```
搜索关键词："{股票名称} {股票代码} 最新消息 新闻"
搜索关键词："{股票名称} 公告 财报 研报"
```

将搜索结果整合到仪表盘 `intelligence.news_brief` 中，补充 Tushare 新闻以外的舆情信息。

> **注意**：WebSearch 结果需要去重和时效性过滤（7天内）。

#### Step 4: LLM 解读生成

分析脚本输出的 `dashboard` JSON 中，`core_conclusion`、`intelligence`、`battle_plan` 三个区块各包含一个 `llm_context` 字段。AI agent 应：
1. 读取各区块的 `llm_context.template` 和 `llm_context.key_points`
2. 基于 `llm_context.guidance` 中的指引生成专业的人性化解读文字
3. 将解读与结构化数据合并，形成完整的分析报告

## 决策仪表盘结构（v5.0 核心输出）

### 第一段：核心结论 (core_conclusion)

```
{
  "action": "适量买入",
  "total_score": 65,
  "signal_type": "做多信号 · 趋势向上",
  "verdict": "多头信号占优，上升趋势结构完整，可逢低布局",
  "position": "20%",
  "score_breakdown": {"tech_weight": "35%", ...},
  "llm_context": {
    "template": "该股当前综合评分 65/100...",
    "guidance": "请用专业客观的语气..."
  }
}
```

### 第二段：数据透视 (data_perspective)

包含 6 个子模块：
- `price_position`: 当前价位、涨跌幅、成交量、换手率
- `trend_system`: 均线排列、布林带位置、趋势判断
- `tech_indicators`: RSI/KDJ/MACD 值及信号
- `pattern_alerts`: K线形态分类（看涨/看跌）及可靠度
- `chanlun_status`: 分型/笔/中枢数量、缠论买卖信号
- `money_flow_trend`: 近5日资金流向趋势
- `fundamental_snapshot`: PE/PB、ROE、营收增速、基本面评分

### 第三段：情报解读 (intelligence)

包含 5 个子模块：
- `news_brief`: 消息面情绪、近期重要新闻
- `sentiment_overview`: 市场情绪指数及趋势
- `risk_alerts`: 风险警报列表（分级：info/warning/danger）
- `catalysts`: 利好催化因素列表
- `forecast_outlook`: 分析师盈利预测及关注度
- `llm_context`: AI agent 生成解读的指引

### 第四段：作战计划 (battle_plan)

包含 4 个子模块：
- `strike_points`: 买入狙击点、卖出目标位、止损线（含触发条件和置信度）
- `position_strategy`: 建议仓位比例及说明
- `risk_control`: 风控规则清单（must/recommend/suggest 三级）
- `llm_context`: AI agent 生成操作建议的指引

## 核心模块

### 1. 技术指标计算
- MA(5/10/20/60)
- RSI(14)
- KDJ(9,3,3)
- MACD(12,26,9)
- 布林带(20,2)

### 2. K线形态识别 (patterns/candlestick.py)
- 60+ 种形态
- 类名: `CandlestickPatternRecognizer`
- 方法: `recognize_all(df, lookback=5)` → `List[PatternResult]`

### 3. 缠论分析 (patterns/chanlun.py)
- 笔/中枢/买卖点
- 类名: `ChanlunAnalyzer`（注意不是 ChanLunAnalyzer）
- 方法: `analyze(df)` → `dict`

### 4. 信号共振评分 (signals/scoring.py)
- 7维度加权评分
- 类名: `SignalResonanceScorer`
- 方法: `calculate_resonance(signals)` → `ResonanceResult`

### 5. 情绪指数 (ai_models/sentiment_index.py)
- 4组件综合情绪
- 类名: `SentimentIndexCalculator`
- 方法: `calculate(df)` → `SentimentResult`

### 6. 买卖点位计算 (signals/trade_points.py) ⭐ v5.0 新增
- 多维度支撑/压力位综合计算
- 类名: `TradePointCalculator`
- 方法: `calculate(df, chanlun, sentiment, resonance, current_price, code)` → `TradePlan`
- 数据源：缠论中枢 + 布林带 + 均线 + 斐波那契 + 近期高低点
- 输出：买入狙击点、卖出目标、止损线、风报比、仓位建议

### 7. 决策仪表盘生成 (scripts/dashboard_report.py) ⭐ v5.0 新增
- 四段式结构化报告
- 类名: `DashboardReportBuilder`
- 方法: `build(analysis_result, trade_plan, stock_name, stock_code)` → `dict`
- 每个区块内置 `llm_context` 供 AI agent 生成人性化解读

### 8. 策略配置系统 (strategies/) ⭐ v5.1 新增
- YAML 驱动的策略定义，支持热修改参数无需改代码
- `indicators.yaml` — 技术指标参数和信号规则（MA/RSI/KDJ/MACD/布林带/成交量）
- `scoring.yaml` — 评分权重和共振级别定义
- `chanlun.yaml` — 缠论买卖点判定规则和仓位建议
- `loader.py` — 策略加载器和信号评估引擎

## 项目结构

```
stock-analyst/
├── SKILL.md
├── scripts/
│   ├── full_analysis.py     # 统一分析入口（v5.1 升级）
│   ├── dashboard_report.py  # 决策仪表盘生成器 ⭐ v5.0
│   └── fetch_data.py        # 数据获取脚本（向后兼容）
├── patterns/
│   ├── candlestick.py        # K线形态识别
│   └── chanlun.py           # 缠论分析
├── signals/
│   ├── scoring.py           # 信号共振评分
│   └── trade_points.py      # 买卖点位计算 ⭐ v5.0
├── strategies/              # ⭐ v5.1 策略配置系统
│   ├── __init__.py
│   ├── loader.py            # YAML 加载和信号评估引擎
│   ├── indicators.yaml      # 技术指标信号规则（可热修改）
│   ├── scoring.yaml         # 评分配置（可热修改）
│   └── chanlun.yaml         # 缠论策略配置（可热修改）
├── ai_models/
│   └── sentiment_index.py   # 情绪指数
└── references/
    └── gotchas.md           # ⚠️ agent踩坑记录累积（核心资产）
```

> **重要**：每次 agent 翻车，追加一条到 `references/gotchas.md`，这是 Skill 长期迭代的核心资产。

## 免责声明

本工具仅供学习和研究使用，分析结果仅供参考，不构成投资建议。股市有风险，投资需谨慎。

---

## 🔄 触发词自进化规则

当用户输入某种表述但本 Skill 未被自动激活时，完成任务后**必须**执行：
1. 分析用户原始请求中的关键表述
2. 将其抽象为通用触发词（避免过于具体的个例）
3. 用 Edit 工具将触发词追加到本文件 YAML frontmatter `tags` 字段末尾
4. 不得重复添加已存在的触发词

---

## 📚 踩坑经验

> 由 AI 在实际调用中自动积累，**请勿手动删除**。
> 规则：凡经过 2 次及以上尝试才成功的情况必须追加。格式：`- 场景/模块：经验要点`

- candlestick / K线形态识别：方法名是 `recognize_all()` 不是 `recognize()`
- chanlun / 缠论分析：类名是 `ChanlunAnalyzer` 不是 `ChanLunAnalyzer`
- scoring / 信号共振：方法名是 `calculate_resonance()` 不是 `calculate()`
- sentiment_index / 情绪指数：类名是 `SentimentIndexCalculator`，方法名是 `calculate()`
- full_analysis / 数据输入：v4.0 起不再自行获取数据，通过 JSON 文件接收 tushare-data 预取数据
- full_analysis / Tushare 数据格式：日线字段名用 trade_date/open/high/low/close/vol/amount，需映射为标准名
- full_analysis / Windows PowerShell：Python 命令中多行代码会解析错误，复杂逻辑写入 .py 脚本执行
- trade_points / 买卖点计算：类名 `TradePointCalculator`，方法 `calculate()` 需传入 df + chanlun/sentiment/resonance + current_price
- dashboard_report / 仪表盘生成：类名 `DashboardReportBuilder`，方法 `build(analysis_result, trade_plan, stock_name, stock_code)` 返回 dict，每个区块含 `llm_context` 供 AI 生成解读
- dashboard_report / LLM 解读：分析脚本只输出结构化 JSON + llm_context，AI agent 负责基于 llm_context 生成最终的人性化文字；不要把 LLM 解读逻辑写在 Python 脚本里

---

## 💬 使用示例

```
# 综合分析（默认输出决策仪表盘）
"分析 600036 的技术面"
"招商银行的 K 线形态怎么样"
"给 000001 做一个综合分析"

# 缠论买卖点
"判断一下 600519 现在是一买还是二买"
"帮我找茅台的缠论买卖点"

# 信号共振
"600519 多个周期信号共振了吗"

# 情绪指数
"当前市场情绪指数是多少"

# 买卖点位 + 投资建议（v5.0 新增）
"帮我看看 002402 的买入点和止损位"
"给个狙击点价格"
"现在的仓位应该多少"

# 决策仪表盘
"给我一份完整的决策仪表盘"
```
