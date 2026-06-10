# Stock Analyst Gotchas

> Perplexity 方法论：Gotcha 是 Skill 的最高价值内容。每次 agent 翻车 → 追加一条到这里。
> 规则：凡经过 2 次及以上尝试才成功的情况必须追加。格式：`- 模块：经验要点`

---

## K线形态识别 (patterns/candlestick.py)

- **方法名**：`recognize_all()` 不是 `recognize()`
- **锤头 vs 倒锤**：形状相似但含义相反，必须结合成交量判断
- **上影线**：超过实体2倍时，模型经常错误判断为「射击之星」

## 缠论分析 (patterns/chanlun.py)

- **类名**：`ChanlunAnalyzer` 不是 `ChanLunAnalyzer`（注意大小写）
- **次级别中枢**：未完成时不可提示背驰，否则模型会误判
- **第三类买卖点**：必须在次级别回调确认后才能标注

## 信号共振 (signals/scoring.py)

- **方法名**：`calculate_resonance()` 不是 `calculate()`
- **多信号冲突**：当技术指标信号矛盾时，优先参考缠论结构

## 情绪指数 (ai_models/sentiment_index.py)

- **类名**：`SentimentIndexCalculator`，方法名是 `calculate()`
- **新闻情感**：需过滤重复新闻，否则会放大某条消息的影响

## 数据输入/输出 (full_analysis.py)

- **v4.0 架构变更**：不再自行获取数据，通过 JSON 文件接收 tushare-data 预取数据
- **Tushare 数据格式**：日线字段名用 `trade_date`/`open`/`high`/`low`/`close`/`vol`/`amount`，需映射为标准名
- **Windows PowerShell**：Python 命令中多行代码会解析错误，复杂逻辑写入 .py 脚本执行

## 协作边界 (tushare-data)

- **数据获取**：找 tushare-data；本 Skill 只做分析
- **查行情**：→ tushare-data
- **查财报**：→ tushare-data
- **看资金流向**：→ tushare-data
- **数据导出**：→ tushare-data

---

*最后更新：2026-06-10（v5.0 P0 决策仪表盘改造）*

## v5.0 架构升级要点

- **决策仪表盘**：四段式输出（core_conclusion → data_perspective → intelligence → battle_plan），每个区块内置 `llm_context` 供 AI agent 生成解读
- **买卖点位**：`TradePointCalculator` 综合缠论+布林带+均线+斐波那契+近期高低点计算狙击点、止损位
- **LLM 解读分层**：分析脚本只输出结构化 JSON + llm_context，AI agent（非 Python 脚本）负责生成人性化文字
- **DashBoardReportBuilder**：类名注意大小写，`build(analysis_result, trade_plan, stock_name, stock_code)` → dict
- **TradePointCalculator**：`calculate(df, chanlun, sentiment, resonance, current_price, code)` → TradePlan
- **输出格式**：默认 `dashboard`，`--format json` 回退到 v4 格式
