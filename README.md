# Stock Analyst - 股票分析Skill

基于AkShare开源金融数据库的智能股票分析工具，支持四维分析体系（技术面、基本面、资金面、消息面）。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![AkShare](https://img.shields.io/badge/Data-AkShare-orange.svg)

## ✨ 功能特性

### 📊 四维分析体系

| 分析维度 | 指标 | 说明 |
|:---------|:-----|:-----|
| **技术面** | KDJ、MACD、RSI、MA均线 | 价格趋势判断 |
| **基本面** | 涨跌幅、波动率、估值 | 中长期价值判断 |
| **资金面** | 主力净流入/流出 | 资金动向分析 |
| **消息面** | 新闻、公告、大宗交易 | 影响因子分析 |

### 📈 输出内容

- 实时行情数据（价格、涨跌幅、成交量）
- 技术指标分析（KDJ金叉死叉、MACD信号）
- 综合投资建议（评分、目标价、止损价、仓位）
- 最新财经新闻摘要

## 🚀 快速开始

### 安装依赖

```bash
pip install akshare pandas
```

### 使用方法

在WorkBuddy中直接输入股票代码：

```
分析 000001      # 分析平安银行
查询贵州茅台      # 查询600519
帮我看看招商银行    # 查询600036
```

或使用命令行：

```bash
python scripts/full_analysis.py 000001
```

## 📋 支持的股票

### A股
| 交易所 | 代码范围 | 示例 |
|:-------|:---------|:-----|
| 沪市 | 600xxx, 601xxx, 688xxx | 600519(茅台) |
| 深市 | 000xxx, 002xxx, 300xxx | 000001(平安)、002149(西部材料) |

### 港股
```python
00700.HK  # 腾讯控股
09988.HK  # 阿里巴巴
```

### 美股
```python
AAPL      # 苹果
TSLA      # 特斯拉
MSFT      # 微软
```

## 📁 项目结构

```
stock-analyst/
├── SKILL.md           # Skill定义文件
├── README.md          # 使用说明
└── scripts/
    ├── full_analysis.py    # 完整四维分析
    ├── stock_analysis.py   # 标准分析
    └── stock_analyzer.py   # 核心分析器
```

## ⚙️ 依赖

- `akshare >= 1.10.0` - 金融数据接口
- `pandas >= 1.3.0` - 数据处理

## 📝 输出示例

```json
{
  "success": true,
  "code": "002149",
  "stock_name": "西部材料",
  "quote": {
    "price": 45.65,
    "pct_change": -2.02,
    "volume": 39554476
  },
  "technical": {
    "kdj_signal": "死叉",
    "rsi": 54.59,
    "trend": "震荡偏强"
  },
  "fundamental": {
    "近一年涨跌幅": 131.96,
    "score": 50
  },
  "suggestion": {
    "total_score": 60,
    "action": "适量买入",
    "target_price": 49.30,
    "stop_loss": 43.37
  }
}
```

## ⚠️ 免责声明

本工具仅供学习和研究使用，数据仅供参考，不构成投资建议。股市有风险，投资需谨慎。

## 📜 License

MIT License
