---
name: stock-analyst
version: 1.0.0
description: 基于AkShare的智能股票分析，支持A股/港股/美股四维分析(技术面/基本面/资金面/消息面)
author: zhuang-HE
homepage: https://github.com/zhuang-HE/stock-analyst-skill
tags:
  - 股票
  - 金融
  - 数据分析
  - A股
  - 港股
  - 美股
  - AkShare
created: 2026-04-10
updated: 2026-04-10
---

# Stock Analyst - 股票分析Skill

基于AkShare开源金融数据库的智能股票分析工具，支持四维分析体系（技术面、基本面、资金面、消息面）。

## 功能特性

### 核心能力
- 📊 **实时行情**: 价格、涨跌幅、成交量、成交额
- 📈 **技术分析**: KDJ、MACD、RSI、均线系统
- 💼 **基本面分析**: 估值、波动率、历史表现
- 💰 **资金面分析**: 主力资金流向
- 📰 **消息面分析**: 最新新闻、公告、大宗交易

### 支持市场
- **A股**: 600xxx(沪)、000xxx/002xxx/300xxx(深)
- **港股**: 00700.HK、09988.HK 等
- **美股**: AAPL、TSLA、MSFT 等

## 使用方法

在WorkBuddy中直接输入股票代码即可分析：
- `000001` - 平安银行
- `600519` - 贵州茅台
- `002149` - 西部材料
- `0700.HK` - 腾讯控股
- `AAPL` - 苹果公司

或使用命令行：
```bash
python scripts/full_analysis.py 000001
```

## 依赖

```bash
pip install akshare pandas
```

## 免责声明

本工具仅供学习和研究使用，数据仅供参考，不构成投资建议。股市有风险，投资需谨慎。
