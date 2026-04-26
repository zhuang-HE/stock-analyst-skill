---
name: stock-analyst
version: 4.0.0
description: "纯分析层股票分析Skill。与tushare-data配合使用：tushare-data负责数据获取，本Skill负责技术指标计算、K线形态识别、缠论买卖点、信号共振评分、情绪指数、基本面评分和综合建议。触发词：技术分析、K线形态、缠论、买卖点、信号共振、情绪指数、形态识别、五维分析、综合分析、股票评分、投资建议"
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
updated: 2026-04-26
---

# Stock Analyst v4.0 - 纯分析层

**架构变更（v4.0）**：本 Skill 不再自行获取数据，改为接收 tushare-data 预取的 JSON 数据进行分析。

## 协作模式

```
tushare-data (数据层) → JSON 数据文件 → stock-analyst (分析层) → 完整分析结果
```

**数据获取** → `tushare-data` Skill
**分析计算** → 本 Skill

## 什么时候用本 Skill

- 用户要求**技术分析**（MA/RSI/KDJ/MACD/布林带）
- 用户要求**K线形态识别**（60+种形态）
- 用户要求**缠论买卖点**分析
- 用户要求**信号共振评分**
- 用户要求**情绪指数**计算
- 用户要求**五维分析**或**综合分析**
- 用户要求**投资建议**或**股票评分**

## 什么时候不用本 Skill

- 用户只想**查行情** → tushare-data
- 用户只想**查财报** → tushare-data
- 用户只想**看资金流向** → tushare-data
- 用户要求**数据导出** → tushare-data

## 执行流程

### 完整分析流程

当用户要求"分析XXX"时，按以下步骤执行：

1. **调用 tushare-data** 获取数据（一次性），保存为 JSON 文件
2. **调用本 Skill** 执行分析脚本

#### Step 1: 数据获取（tushare-data）

用 Python 脚本一次性获取所有需要的数据：

```python
import tushare as ts
import json
import os
import sys

pro = ts.pro_api(os.environ.get('TUSHARE_TOKEN'))
code = sys.argv[1]  # 如 "300263"
ts_code = f"{code}.SZ" if code.startswith(('0','3')) else f"{code}.SH"

# 获取日期范围
from datetime import datetime, timedelta
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=400)).strftime('%Y%m%d')

data = {'code': code, 'ts_code': ts_code}

# 1. 日线行情
df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
data['daily'] = df.to_dict('records') if df is not None else []

# 2. 每日指标
df = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
data['daily_basic'] = df.to_dict('records') if df is not None else []

# 3. 利润表
df = pro.income(ts_code=ts_code, period_type='1')
data['income'] = df.to_dict('records')[:8] if df is not None else []

# 4. 财务指标
df = pro.fina_indicator(ts_code=ts_code)
data['fina_indicator'] = df.to_dict('records')[:8] if df is not None else []

# 5. 资金流向
df = pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
data['moneyflow'] = df.to_dict('records') if df is not None else []

# 6. 新闻
try:
    df = pro.news(src='sina', start_date=(datetime.now()-timedelta(days=7)).strftime('%Y%m%d'))
    data['news'] = df.to_dict('records')[:10] if df is not None else []
except:
    data['news'] = []

# 7. 盈利预测
try:
    df = pro.forecast(ts_code=ts_code)
    data['forecast'] = df.to_dict('records')[:5] if df is not None else []
except:
    data['forecast'] = []

# 保存
out_path = os.path.join(os.environ.get('TEMP', '/tmp'), f'stock_data_{code}.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, default=str)
print(f"DATA_FILE={out_path}")
```

#### Step 2: 执行分析

```bash
python <skill_dir>/scripts/full_analysis.py <data_json_path> <code>
```

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

## 项目结构

```
stock-analyst/
├── SKILL.md
├── scripts/
│   └── full_analysis.py     # 统一分析入口
├── patterns/
│   ├── candlestick.py        # K线形态识别
│   └── chanlun.py            # 缠论分析
├── signals/
│   └── scoring.py            # 信号共振评分
└── ai_models/
    └── sentiment_index.py    # 情绪指数
```

## 免责声明

本工具仅供学习和研究使用，分析结果仅供参考，不构成投资建议。股市有风险，投资需谨慎。

---

## 🔄 触发词自进化规则

当用户输入某种表述但本 Skill 未被自动激活时，完成任务后**必须**执行：
1. 分析用户原始请求中的关键表述
2. 将其抽象为通用触发词（避免过于具体的个例）
3. 用 replace_in_file 工具将触发词追加到本文件 YAML frontmatter `tags` 字段末尾
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
