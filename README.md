# Stock Analyst Skill - v5.1

纯分析层股票分析 Skill，与 [tushare-data](https://github.com/zhuang-HE/tushare-data) 配合使用。支持决策仪表盘输出、买卖点位计算、YAML 策略配置和双数据源 Fallback。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Tushare](https://img.shields.io/badge/Data-Tushare%20Pro-red.svg)
![AkShare](https://img.shields.io/badge/Data-AkShare%20Fallback-orange.svg)
![Version](https://img.shields.io/badge/Version-5.1-brightgreen.svg)

---

## v5.x 架构演进

### v5.1 (P1): 策略 YAML 化 + 数据源 Fallback

| 变更 | 说明 |
|------|------|
| **策略 YAML 化** | 技术指标信号规则从硬编码迁移至 `strategies/indicators.yaml`，可热修改无需改代码 |
| **策略加载器** | `StrategyLoader` 负责加载 YAML 并评估信号条件 |
| **评分配置化** | 7 维度权重和 5 级共振定义移至 `strategies/scoring.yaml` |
| **数据源 Fallback** | Tushare 失败时自动降级到 AkShare（免费无需 Token） |
| **新闻搜索工作流** | AI agent 使用 WebSearch 补充舆情（SKILL.md Step 3） |

### v5.0 (P0): 决策仪表盘 + 买卖点位

| 变更 | 说明 |
|------|------|
| **决策仪表盘** | 四段式输出：核心结论 → 数据透视 → 情报解读 → 作战计划 |
| **买卖点位计算** | `TradePointCalculator` — 缠论/布林带/均线/斐波那契多维度综合计算狙击点和止损位 |
| **LLM 辅助解读** | 仪表盘各区块内置 `llm_context`，供 AI agent 生成人性化解读文字 |
| **向后兼容** | `--format json` 保留 v4 完整 JSON 输出 |

### v4.0: 分析层纯净化

```
tushare-data (数据层) → JSON 数据文件 → stock-analyst (分析层) → 决策仪表盘 / 完整JSON
```

---

## 分析维度

| 维度 | 内容 | 模块 |
|------|------|------|
| **技术面** | MA/RSI/KDJ/MACD/布林带 + YAML 策略信号评估 | full_analysis.py, strategies/ |
| **基本面** | ROE/毛利率/营收净利增速/PE-PB/资产负债率 | full_analysis.py |
| **资金面** | 主力净流入/净流出/近5日趋势 | full_analysis.py |
| **形态面** | K线形态识别（60+种）、缠论（笔/中枢/买卖点） | patterns/candlestick.py, patterns/chanlun.py |
| **信号面** | 7维度信号共振评分 | signals/scoring.py |
| **情绪面** | 市场情绪指数（贪婪恐慌） | ai_models/sentiment_index.py |
| **买卖点** ⭐ | 狙击点/止损位/仓位建议/风险收益比 | signals/trade_points.py |
| **决策输出** ⭐ | 四段式决策仪表盘 | scripts/dashboard_report.py |
| **综合建议** | 总评分 + 操作建议 + 仓位 | full_analysis.py |

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# pandas>=1.3.0, numpy>=1.21.0, pyyaml>=6.0
```

### 2. 获取数据

```bash
# Tushare 优先（需 Token），失败自动降级 AkShare
export TUSHARE_TOKEN=your_token_here
python scripts/fetch_data.py 300263
# → ~/stock_data_300263.json
```

### 3. 执行分析

```bash
# 默认输出决策仪表盘（推荐）
python scripts/full_analysis.py ~/stock_data_300263.json 300263

# 输出完整 JSON（v4 兼容格式）
python scripts/full_analysis.py ~/stock_data_300263.json 300263 --format json
```

---

## 决策仪表盘结构

```
{
  "core_conclusion": 核心结论（评分/判词/信号/仓位）
  "data_perspective": 数据透视（趋势/指标/形态/缠论/资金/基本面）
  "intelligence":      情报解读（消息面/情绪/风险/催化/盈利预测）
  "battle_plan":       作战计划（狙击点/止损/仓位/风控清单）
}
```

每个区块内置 `llm_context` 字段（template + key_points + guidance），供 AI agent 生成人性化解读。

---

## 项目结构

```
stock-analyst/
├── scripts/
│   ├── full_analysis.py        # 统一分析入口（v5.1）
│   ├── dashboard_report.py     # 决策仪表盘生成器 ⭐ v5.0
│   └── fetch_data.py           # 数据获取（Tushare/AkShare）
├── patterns/
│   ├── __init__.py
│   ├── candlestick.py          # K线形态识别（60+种）
│   └── chanlun.py              # 缠论分析（笔/中枢/买卖点）
├── signals/
│   ├── __init__.py
│   ├── scoring.py              # 信号共振评分系统
│   └── trade_points.py         # 买卖点位计算 ⭐ v5.0
├── strategies/                 # ⭐ v5.1 策略配置系统
│   ├── __init__.py
│   ├── loader.py               # YAML 加载和信号评估引擎
│   ├── indicators.yaml         # 技术指标信号规则（可热修改）
│   ├── scoring.yaml            # 评分配置（可热修改）
│   └── chanlun.yaml            # 缠论策略配置（可热修改）
├── ai_models/
│   ├── __init__.py
│   └── sentiment_index.py      # 情绪指数计算
├── references/
│   └── gotchas.md              # Agent 踩坑记录
├── SKILL.md                    # WorkBuddy Skill 定义
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

---

## 模块接口

### patterns/candlestick.py

```python
from patterns.candlestick import CandlestickPatternRecognizer
recognizer = CandlestickPatternRecognizer()
results = recognizer.recognize_all(df, lookback=5)  # 60+种形态
```

### patterns/chanlun.py

```python
from patterns.chanlun import ChanlunAnalyzer
analyzer = ChanlunAnalyzer()
result = analyzer.analyze(df)
# → {fenxing_count, bi_count, zhongshu_count, buy_points, current_trend}
```

### signals/scoring.py

```python
from signals.scoring import SignalResonanceScorer
scorer = SignalResonanceScorer()
signals = scorer.analyze_technical_signals(df)
result = scorer.calculate_resonance(signals)  # 7维度加权评分
```

### signals/trade_points.py ⭐

```python
from signals.trade_points import TradePointCalculator
calc = TradePointCalculator()
plan = calc.calculate(df, chanlun_result, sentiment, resonance, current_price, code)
# → TradePlan(buy_points, sell_points, stop_loss, position_suggestion, risk_reward_ratio)
```

### strategies/loader.py ⭐

```python
from strategies import StrategyLoader, load_strategies
loader = load_strategies()
signals = loader.evaluate_all_signals(indicator_data)
# → {signals, total_bullish, total_bearish, net_score, resonance_level}
# 修改 indicators.yaml / scoring.yaml 即可调整策略参数
```

### ai_models/sentiment_index.py

```python
from ai_models.sentiment_index import SentimentIndexCalculator
calc = SentimentIndexCalculator()
result = calc.calculate(df)
# → {index_value, level, description, components, trend, signal}
```

---

## 踩坑经验

- `CandlestickPatternRecognizer.recognize_all()` 不是 `recognize()`
- `ChanlunAnalyzer` 不是 `ChanLunAnalyzer`
- `SignalResonanceScorer.calculate_resonance()` 不是 `calculate()`
- `SentimentIndexCalculator.calculate()` — 类名和方法名注意区分
- `TradePointCalculator.calculate()` — 需传入 df + chanlun/sentiment/resonance + current_price
- `DashboardReportBuilder.build(analysis_result, trade_plan, stock_name, stock_code)` → dict
- `StrategyLoader.evaluate_all_signals()` — YAML 热修改后自动生效
- LLM 解读不由 Python 脚本生成，AI agent 基于 `llm_context` 生成

---

## 免责声明

本工具仅供学习和研究使用，数据仅供参考，不构成投资建议。股市有风险，投资需谨慎。
