# Stock Analyst - 股票分析Skill v3.3 Pro

基于多源金融数据的智能股票分析工具，支持 **五维分析体系**（技术面、基本面、资金面、消息面、形态面）。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Tushare](https://img.shields.io/badge/Data-Tushare%20Pro-red.svg)
![AkShare](https://img.shields.io/badge/Data-AkShare-orange.svg)
![Version](https://img.shields.io/badge/Version-3.3--Pro-brightgreen.svg)

---

## ✨ 功能特性

### 📊 五维分析体系

| 分析维度 | 指标 | 说明 |
|:---------|:-----|:-----|
| **技术面** | KDJ、MACD、RSI、MA均线、布林带 | 价格趋势判断 |
| **基本面** | 利润表/资产负债表/现金流量表、PE-PB、财务指标 | 中长期价值判断 |
| **资金面** | 主力净流入/流出、北向资金、20日资金流向趋势 | 资金动向分析 |
| **消息面** | 新闻、公告、大宗交易 + 基本面影响评估 | 影响因子分析 |
| **形态面** | K线形态（60+种）、缠论、信号共振、情绪指数 | 交易形态识别与策略建议 |

### 🔄 多源数据降级机制

V3.3 核心升级 —— 数据获取不再依赖单一来源，自动降级确保高可用性：

| 市场区域 | 主数据源 | 备用1 | 备用2 | 兜底 |
|:---------|:---------|:------|:------|:-----|
| **A股（沪/深）** | **Tushare Pro** ⭐ | AkShare | Baostock | 本地缓存 |
| 港股 | YFinance | AkShare | — | 本地缓存 |
| 美股 | YFinance | AkShare | — | 本地缓存 |

---

## 🆕 V3.3 Pro 核心升级

### 1️⃣ Tushare Pro 作为 A 股主数据源

**为什么选择 Tushare？**
- ✅ 数据质量高，覆盖全市场 A 股标的
- ✅ API 稳定可靠，响应速度快
- ✅ 支持日线行情、财务报表（利润表/资产负债表/现金流量表）、资金流向、新闻等
- ✅ Token 权限管理灵活，积分体系可控

**已集成的 Tushare 接口：**

| 功能 | 接口 | 说明 |
|:-----|:-----|:-----|
| 日线行情 | `daily` | OHLCV + 前复权价格 |
| 实时行情 | `realtime_quote` / `daily_basic` | 当日快照 + PE/PB/市值 |
| 全面基本面 | `income` / `balancesheet` / `cashflow` / `fina_indicator` | 四表联动，支持多期对比 |
| 资金流向 | `moneyflow` / `moneyflow_hsgt` | 个股主力资金 + 北向资金 |
| 新闻资讯 | `news` | 公司相关新闻 |

### 2️⃣ 安全的 Token 管理

```python
# ❌ 禁止硬编码
token = "29bbbd6e..."  # 绝对不要这样做！

# ✅ 正确方式：环境变量
# 方式一：系统环境变量
set TUSHARE_TOKEN=你的Token

# 方式二：代码中读取（已内置）
# DataProvider 自动从 TUSHARE_TOKEN 环境变量读取
```

**安全架构设计：**

```
┌─────────────────────────────┐
│  环境变量 TUSHARE_TOKEN      │  ← 生产环境推荐
│  (或 .env 文件)              │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  _get_tushare_token()       │  ← 静态方法，安全读取
│  优先级：TUSHARE_TOKEN      │
│        > TUSHARE_TOKEN_FALLBACK │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  @property pro              │  ← 懒加载，首次调用时初始化
│  ts.pro_api() 实例          │
└─────────────────────────────┘
```

### 3️⃣ data_provider 模块

统一的数据提供层，封装所有数据源交互逻辑：

```python
from data_provider.data_provider import DataProvider

provider = DataProvider()

# A股数据（Tushare -> AkShare -> Baostock 自动降级）
df = provider.get_daily_data('sh', '600519', days=60)

# 实时行情（Tushare/AkShare）
quote = provider.get_realtime_data('sz', '000001')

# 全面基本面（Tushare 四表联动）
fundamental = provider.get_fundamental_data('600519.SH')

# 资金流向（Tushare/AkShare）
flow = provider.get_money_flow('600519.SH')

# 新闻资讯（Tushare）
news = provider.get_news_data('600519.SH')
```

**懒加载模式**：Tushare Pro API 仅在首次调用时初始化，避免不必要的连接开销。

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
# 或手动安装核心依赖：
pip install tushare akshare pandas numpy yfinance
```

### 配置 Tushare Token（必需）

**Windows PowerShell：**
```powershell
$env:TUSHARE_TOKEN = "your_token_here"
```

**Linux/macOS：**
```bash
export TUSHARE_TOKEN="your_token_here"
```

**Python 代码内设置：**
```python
import os
os.environ['TUSHARE_TOKEN'] = 'your_token_here'
```

> 💡 **没有 Tushare Token？** 免费注册：https://tushare.pro/register  
> 注册后在个人中心 → 接口-Token 即可获取

### 使用方法

#### 方式1：使用 data_provider（推荐 V3.3+）

```python
from data_provider.data_provider import DataProvider
from templates.unified_report_template import generate_unified_report

# 创建提供者（自动初始化所有数据源）
provider = DataProvider()

# 获取完整数据（A股优先使用 Tushare，自动降级到 AkShare/Baostock）
data, pattern_data = provider.get_complete_data('002149', '西部材料')

# 生成报告
report = generate_unified_report(data, pattern_data, output_format='text')
print(report['text'])
```

#### 方式2：使用 data_adapter（V3.3 保留兼容）

无需直接依赖具体数据源：

```python
from data_adapter.adapter import DataAdapter
from templates.unified_report_template import generate_unified_report

adapter = DataAdapter()
data, pattern_data = adapter.get_complete_data('002149', '西部材料')
report = generate_unified_report(data, pattern_data, output_format='markdown')
print(report['markdown'])
```

#### 方式3：WorkBuddy 中使用

```
分析 000001              # 分析平安银行（含形态识别）
查询贵州茅台              # 查询600519
帮我看看招商银行           # 查询600036
分析西部材料的交易形态      # 形态专项分析
查看市场情绪指数           # 查看大盘情绪
```

#### 命令行使用

```bash
# 设置 Token 后执行完整分析
$env:TUSHARE_TOKEN="your_token"
python scripts/full_analysis.py 000001

# 形态专项分析
python -c "from patterns.candlestick import analyze_stock_patterns; analyze_stock_patterns('000001.SZ')"

# 缠论分析
python -c "from patterns.chanlun import ChanLunAnalyzer; ChanLunAnalyzer().analyze('000001.SZ')"

# 使用 data_provider 直接测试
python -c "
import os; os.environ['TUSHARE_TOKEN']='your_token'
from data_provider.data_provider import DataProvider
p = DataProvider()
print(p.get_daily_data('sh', '600519', days=5))
"
```

#### 报告格式选择（Token优化）

| 格式 | 函数 | Token消耗 | 适用场景 |
|:-----|:-----|:----------|:---------|
| **Markdown** | `output_format='markdown'` | ⭐⭐ 低 | 日常使用（默认） |
| **纯文本** | `output_format='text'` | ⭐ 最低 | 快速预览 |
| **极简HTML** | `output_format='html'` | ⭐⭐⭐ 中等 | 需要网页展示 |
| **完整HTML** | `output_format='html_full'` | ⭐⭐⭐⭐ 高 | 需要精美样式 |
| **双格式** | `output_format='both'` | ⭐⭐⭐⭐⭐ 最高 | 完整需求 |

---

## 📋 支持的股票

### A股

| 交易所 | 代码范围 | 示例 | Tushare代码格式 |
|:-------|:---------|:-----|:---------------|
| 沪市 | 600xxx, 601xxx, 603xxx | 600519(茅台) | `600519.SH` |
| 深市 | 000xxx, 002xxx, 300xxx | 000001(平安)、002149(西部材料) | `000001.SZ` |
| 科创板 | 688xxx | 688981(中芯国际) | `688981.SH` |
| 北交所 | 430xxx, 830xxx | 430047(诺思兰德) | `430047.BJ` |

> **注意**：Tushare 接口需要带交易所后缀（`.SH` / `.SZ` / `.BJ`），data_provider 会自动转换。

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

---

## 📁 项目结构

```
stock-analyst/
├── SKILL.md                        # Skill 定义文件
├── README.md                       # 使用说明（本文件）
├── requirements.txt                # 依赖清单
├── LICENSE                         # MIT 许可证
│
├── data_provider/                   # 🆕 V3.3 核心数据提供层
│   ├── __init__.py
│   └── data_provider.py            # 多源降级数据提供者（主文件）
│
├── data_adapter/                    # V3.3 数据适配层
│   ├── __init__.py
│   ├── adapter.py                  # 核心适配器（数据转换）
│   ├── fallback.py                 # 多数据源备用管理
│   └── sources.py                  # 数据源接口定义
│
├── patterns/                        # 形态识别模块
│   ├── __init__.py
│   ├── candlestick.py             # K线形态识别（60+种）
│   └── chanlun.py                 # 缠论分析（笔/中枢/买卖点）
│
├── signals/                         # 信号系统
│   ├── __init__.py
│   ├── crossover.py               # 交叉验证
│   └── scoring.py                 # 信号共振评分
│
├── ai_models/                       # AI模型
│   ├── __init__.py
│   └── sentiment_index.py         # 情绪指数计算
│
├── templates/                       # 报告模板
│   ├── dashboard_template.py      # 决策仪表盘
│   ├── pattern_report.py          # 形态分析报告
│   ├── technical_report.py        # 技术面报告
│   └── unified_report_template.py # V3.2 统一报告模板
│
├── cache/                           # 本地数据缓存
├── examples/                        # 示例代码
├── docs/                            # 文档
└── scripts/
    ├── full_analysis.py            # 完整五维分析
    ├── stock_analysis.py           # 标准分析
    └── stock_analyzer.py           # 核心分析器
```

---

## ⚙️ 依赖

### 必需依赖

| 包名 | 版本 | 用途 |
|:-----|:-----|:-----|
| `tushare` | >= 1.4.0 | **A股主数据源**（日线/财务/资金流/新闻） |
| `akshare` | >= 1.10.0 | A股备用数据源 + 港美股辅助 |
| `pandas` | >= 1.3.0 | 数据处理 |
| `numpy` | >= 1.21.0 | 数值计算 |

### 可选依赖

| 包名 | 版本 | 用途 |
|:-----|:-----|:-----|
| `yfinance` | >= 0.2.0 | 港股/美股数据 |
| `baostock` | >= 0.8.0 | A股兜底数据源 |
| `matplotlib` | >= 3.5.0 | 图表绘制 |
| `plotly` | >= 5.0.0 | 交互式图表 |
| `openpyxl` | >= 3.0.0 | Excel 输出 |

---

## 🔑 Tushare 配置指南

### 注册与获取 Token

1. 访问 [Tushare Pro](https://tushare.pro/) 注册账号
2. 登录后进入 **个人中心** → **接口** → **Token**
3. 复制您的 Token 字符串

### 积分说明

Tushare 采用积分制控制 API 调用频率：

| 积分等级 | 日调用次数 | 升级方式 |
|:---------|:----------|:---------|
| 0 分（注册即有） | 120 次/日 | — |
| 2000 分 | 2000 次/日 | 每日登录 +10 分 |
| 5000+ 分 | 更高频次 | 贡献数据/邀请用户 |

> 💡 新用户每日登录即可积累积分，基本满足个人分析需求。

### 环境变量配置详情

| 变量名 | 是否必需 | 说明 |
|:-------|:---------|:-----|
| `TUSHARE_TOKEN` | ✅ **必需** | 您的 Tushare Token |
| `TUSHARE_TOKEN_FALLBACK` | ❌ 可选 | 开发环境备用 Token |

---

## 📝 输出示例

### V3.3 Pro 统一报告结构

```
📋 报告概览
├── 股票信息、综合评分、评级、操作建议

📈 一、实时行情与走势分析
├── 行情概览、涨跌分析、估值分析、成交分析

💼 二、财务深度分析（🆕 Tushare四表联动）
├── 利润表（营业收入、净利润、毛利率...）
├── 资产负债表（总资产、负债率、流动比率...）
├── 现金流量表（经营现金流、投资现金流...）
├── 财务指标（ROE、ROA、净利润率...）
└── 估值分析（PE-TTM、PB、PS）

📰 三、新闻舆情与市场情绪
├── 情感分析、新闻列表、基本面影响评估

📊 四、技术指标深度解析
├── KDJ、MACD、RSI、均线系统、布林带、趋势判断

📐 五、形态面专业分析【核心板块】⭐
├── 5.1 K线形态识别结果（60+形态库）
├── 5.2 缠论结构分析（笔/中枢/趋势）
├── 5.3 买卖点信号系统（一买二买三买）
└── 5.4 信号共振评分系统（7维度加权）

💰 六、资金面深度分析【独立板块】⭐
├── 6.1 资金流向概览（Tushare主力资金）
├── 6.2 北向资金分析（沪深港通）
├── 6.3 近20日资金流向趋势
└── 6.4 资金面综合判断

🎯 七、综合投资决策建议
├── 决策总览、关键价位、核心优势、风险因素、交易策略

⚠️ 附录：风险提示与免责声明
```

### JSON 输出示例（精简版）

```json
{
  "success": true,
  "code": "002149",
  "stock_name": "西部材料",
  "version": "3.3-Pro",
  "data_source": {
    "primary": "tushare",
    "fallback_used": false,
    "market": "SZ"
  },
  "quote": {
    "price": 45.65,
    "pct_change": -2.02,
    "volume": 39554476
  },
  "fundamental": {
    "revenue": 2850000000,
    "net_profit": 320000000,
    "roe": 9.56,
    "pe_ttm": 28.5
  },
  "technical": {
    "kdj_signal": "死叉",
    "rsi": 54.59,
    "trend": "震荡偏强"
  },
  "patterns": {
    "candlestick": {"bullish_count": 2, "bearish_count": 1},
    "chanlun": {"bi_count": 5, "current_trend": "向上笔"},
    "signal_resonance": {"total_score": 72, "level": "强共振"}
  },
  "suggestion": {
    "action": "买入",
    "target_price": 49.30,
    "stop_loss": 43.37,
    "position": "50%"
  }
}
```

---

## 🔄 版本历史

| 版本 | 日期 | 更新内容 |
|:-----|:-----|:---------|
| **v3.3 Pro** | 2026-04-17 | 🚀 **集成 Tushare Pro 为 A 股主数据源**、新增 data_provider 多源降级模块、安全 Token 管理（环境变量）、Tushare 全量接口覆盖（日线/基本面四表/资金流/新闻）、A 股降级链调整为 Tushare→AkShare→Baostock |
| **v3.2 Ultra** | 2026-04-17 | 🆕 强化形态面分析（数据来源验证、置信度评估）、优化资金面分析（20日时效性）、新增独立资金面板块 |
| v3.2.1 | 2026-04-17 | ⚡ Token 优化：新增 `output_format` 参数按需生成报告、极简 HTML 样式、纯文本简化版 |
| v3.1 | 2026-04-16 | 新增交易形态识别和建议策略板块（K线形态 60+种、缠论、信号共振评分、情绪指数） |
| v3.0 | 2026-04-15 | 新增决策仪表盘、多数据源降级、基本面四维分析、批量导入、交易纪律 |
| v2.0 | 2026-04-10 | 增强版四维分析体系、财务分析、估值评估、行业识别、业绩趋势判断 |
| v1.0 | 2026-04-01 | 基础股票分析功能 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

### 代码规范

- Python 遵循 PEP 8
- 所有外部凭证必须通过环境变量传入，禁止硬编码
- 新增数据源请实现 DataSource 枚举并加入降级链

---

## ⚠️ 免责声明

本工具仅供学习和研究使用，数据仅供参考，不构成投资建议。股市有风险，投资需谨慎。

- 所有分析结果基于历史数据，不保证未来收益
- 信号共振评分和情绪指数仅供参考，不构成买卖依据
- 缠论买卖点识别为算法自动计算，可能存在误差
- K线形态识别基于算法自动计算，存在误判可能
- 资金面数据基于最近20个交易日，市场情况可能随时变化
- Tushare 数据受其 API 调用限制约束
- 请结合自身风险承受能力谨慎决策

---

## 📜 License

MIT License

---

## 🙏 致谢

- [Tushare Pro](https://tushare.pro/) - **A股主数据源**，高质量金融数据接口
- [AkShare](https://www.akshare.xyz/) - 开源金融数据接口库（备用数据源）
- [YFinance](https://github.com/ranaroussi/yfinance) - 港股/美股数据
- [Baostock](http://baostock.com/) - 免费开源证券数据平台
- [abu量化交易系统](https://github.com/bbfamily/abu) - 形态识别和交易策略参考
