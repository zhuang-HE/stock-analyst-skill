# Stock Analyst Skill - v4.0

纯分析层股票分析 Skill，与 [tushare-data](https://github.com/zhuang-HE/tushare-data) 配合使用。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Tushare](https://img.shields.io/badge/Data-Tushare%20Pro-red.svg)
![Version](https://img.shields.io/badge/Version-4.0-brightgreen.svg)

---

## V4.0 架构变更

**核心原则：数据层与分析层分离**

```
tushare-data (数据层) → JSON 数据文件 → stock-analyst (分析层) → 分析结果
```

### 为什么重构？

V3.x 存在三个独立的内部数据获取路径（full_analysis.py/AkShare、data_provider/Tushare→AkShare→Baostock、data_adapter/AkShare→Baostock→Sina），互不连通且 adapter.py 返回硬编码假数据，技术指标计算重复3次。导致分析流程频繁失败、Token 消耗极高。

### V4.0 变更

| 变更 | 说明 |
|------|------|
| **移除所有数据获取能力** | 不再自己取数据，由 tushare-data 预取 |
| **删除冗余模块** | data_adapter/、data_provider/、data_store/、cost_tracker/、templates/、multi_perspective/ |
| **统一技术指标计算** | MA/RSI/KDJ/MACD/布林带只算一次，供所有模块共享 |
| **2次脚本执行** | fetch_data.py（取数据）+ full_analysis.py（做分析） |

---

## 分析维度

| 维度 | 内容 | 模块 |
|------|------|------|
| **技术面** | MA/RSI/KDJ/MACD/布林带 + 趋势判断 | full_analysis.py |
| **基本面** | ROE/毛利率/营收净利增速/PE-PB/资产负债率 | full_analysis.py |
| **资金面** | 主力净流入/净流出/净流入率 | full_analysis.py |
| **形态面** | K线形态识别（60+种）、缠论（笔/中枢/买卖点） | patterns/candlestick.py, patterns/chanlun.py |
| **信号面** | 7维度信号共振评分 | signals/scoring.py |
| **情绪面** | 市场情绪指数（贪婪恐慌） | ai_models/sentiment_index.py |
| **综合建议** | 总评分 + 操作建议 + 仓位 | full_analysis.py |

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 获取数据（tushare-data 负责）

```bash
# 设置 Tushare Token
export TUSHARE_TOKEN=your_token_here

# 获取股票数据 → 输出 JSON
python scripts/fetch_data.py 300263
# → ~/stock_data_300263.json
```

### 3. 执行分析

```bash
python scripts/full_analysis.py ~/stock_data_300263.json 300263
# → 输出完整 JSON 分析结果
```

---

## 项目结构

```
stock-analyst/
├── scripts/
│   ├── fetch_data.py           # 数据获取（Tushare → JSON）
│   └── full_analysis.py        # 完整分析（JSON → 分析结果）
├── patterns/
│   ├── __init__.py
│   ├── candlestick.py          # K线形态识别（60+种）
│   └── chanlun.py              # 缠论分析（笔/中枢/买卖点）
├── signals/
│   ├── __init__.py
│   └── scoring.py              # 信号共振评分系统
├── ai_models/
│   ├── __init__.py
│   └── sentiment_index.py      # 情绪指数计算
├── requirements.txt
├── SKILL.md                    # WorkBuddy Skill 定义
├── README.md
├── LICENSE
└── .gitignore
```

---

## 与 tushare-data 的协作

```
用户 "分析300263"
  → tushare-data: 获取 daily/daily_basic/income/fina_indicator/moneyflow/news/forecast → 保存 JSON
  → stock-analyst: 读取 JSON → 执行 full_analysis.py → 输出完整分析结果
```

| 场景 | 使用方式 |
|------|---------|
| 纯数据查询 | 只用 tushare-data |
| 需要分析 | tushare-data 取数据 + stock-analyst 做分析 |
| 禁止 | 不要让 stock-analyst 自己取数据 |

---

## 模块接口

### patterns/candlestick.py

```python
from patterns.candlestick import CandlestickPatternRecognizer
recognizer = CandlestickPatternRecognizer()
results = recognizer.recognize_all(df, lookback=5)  # 注意：是 recognize_all 不是 recognize
```

### patterns/chanlun.py

```python
from patterns.chanlun import ChanlunAnalyzer  # 注意：是 ChanlunAnalyzer 不是 ChanLunAnalyzer
analyzer = ChanlunAnalyzer()
result = analyzer.analyze(df)
# → {fenxing_count, bi_count, zhongshu_count, buy_points, current_trend, nearest_zhongshu}
```

### signals/scoring.py

```python
from signals.scoring import SignalResonanceScorer  # 注意：是 SignalResonanceScorer 不是 SignalScoring
scorer = SignalResonanceScorer()
signals = scorer.analyze_technical_signals(df)
result = scorer.calculate_resonance(signals)  # 注意：是 calculate_resonance 不是 calculate
```

### ai_models/sentiment_index.py

```python
from ai_models.sentiment_index import SentimentIndexCalculator
calc = SentimentIndexCalculator()
result = calc.calculate(df, market_data=None)
# → SentimentResult(value, level, trend, signals, suggestion)
```

---

## 踩坑经验

- `CandlestickPatternRecognizer` 用 `recognize_all()`，不是 `recognize()`
- `ChanlunAnalyzer` 不是 `ChanLunAnalyzer`
- `SignalResonanceScorer` 用 `calculate_resonance()`，不是 `calculate()`
- Tushare fina_indicator 字段：`or_yoy`（营收同比）不是 `revenue_yoy`，`netprofit_yoy`（净利同比）不是 `net_profit_yoy`
- fetch_data.py 数据文件保存到 `~/stock_data_{code}.json`

---

## 免责声明

本工具仅供学习和研究使用，数据仅供参考，不构成投资建议。股市有风险，投资需谨慎。
