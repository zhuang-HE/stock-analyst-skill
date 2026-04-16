# Stock Analyst 完整数据需求指南

## 问题诊断

当前报告内容缺失的根本原因：**传入的数据结构不完整**

| 缺失模块 | 缺失内容 | 需要补充的数据 |
|---------|---------|--------------|
| 形态面 | K线形态、缠论、信号共振 | K线序列数据（60+根） |
| 基本面 | 营收、利润、业务板块 | 利润表、资产负债表多期数据 |
| 消息面 | 新闻列表、情感分析 | 新闻数据、情感评分 |
| 技术面 | KDJ/MACD/RSI数值 | 基于K线计算技术指标 |

---

## 解决方案

### 1. 形态面数据（最复杂）

**需求**：至少60根K线数据（OHLCV）

**获取方式**：
```python
# 使用 finance-data-retrieval 获取K线
from finance_data_retrieval import get_daily_data

klines = get_daily_data('002402', start_date='20260101', end_date='20260417')
# 返回: [{date, open, high, low, close, volume}, ...]
```

**分析流程**：
```python
from patterns.candlestick import CandlestickAnalyzer
from patterns.chanlun import ChanLunAnalyzer
from signals.scoring import SignalResonanceScorer

# 1. K线形态识别
candlestick = CandlestickAnalyzer().analyze(klines)
# 返回: {patterns, bullish_count, bearish_count, signal, ...}

# 2. 缠论分析
chanlun = ChanLunAnalyzer().analyze(klines)
# 返回: {bi_count, zhongshu_count, buy_points, sell_points, ...}

# 3. 信号共振评分
resonance = SignalResonanceScorer().calculate(
    candlestick=candlestick,
    chanlun=chanlun,
    technical=technical_data
)
# 返回: {total_score, bullish_score, bearish_score, breakdown, ...}

pattern_data = {
    'candlestick': candlestick,
    'chanlun': chanlun,
    'resonance': resonance
}
```

---

### 2. 基本面数据

**需求**：最新一期 + 历史3-4期财务数据

**获取方式**：
```python
# 使用 finance-data-retrieval 获取财务数据
from finance_data_retrieval import get_income, get_balance_sheet

income_data = get_income('002402')  # 利润表
balance_data = get_balance_sheet('002402')  # 资产负债表
```

**数据结构**：
```python
fundamental = {
    'financial': {
        'latest': {
            'report_date': '2025-12-31',
            'revenue': '50.5亿',           # 营业收入
            'revenue_yoy': '+15.2%',       # 营收同比
            'net_profit': '3.2亿',         # 净利润
            'net_profit_yoy': '+8.5%',     # 净利润同比
            'roe': '8.5%',                 # 净资产收益率
            'gross_margin': '22%',         # 毛利率
            'net_margin': '6.3%',          # 净利率
            'debt_ratio': '45%',           # 资产负债率
            'pe': '80.99',
            'pb': '5.62'
        },
        'history': [
            {'report_date': '2025-09-30', 'revenue': '35.2亿', 'net_profit': '2.1亿'},
            {'report_date': '2025-06-30', 'revenue': '22.8亿', 'net_profit': '1.3亿'},
            {'report_date': '2025-03-31', 'revenue': '10.5亿', 'net_profit': '0.6亿'},
        ]
    },
    'performance_trend': {
        'overall_trend': '稳健增长',
        'revenue_trend': '持续增长',      # 持续增长/增速放缓/下滑
        'profit_trend': '增速放缓'
    },
    'industry': '电子元器件',
    'business_segments': [              # 业务板块分析
        {'name': '智能控制器', 'revenue_pct': 75, 'growth': '+18%', 'margin': '20%'},
        {'name': '射频芯片', 'revenue_pct': 20, 'growth': '+25%', 'margin': '35%'},
        {'name': '其他', 'revenue_pct': 5, 'growth': '-5%', 'margin': '10%'}
    ]
}
```

---

### 3. 消息面数据

**需求**：近期新闻列表 + 情感分析

**获取方式**：
```python
# 如果有新闻接口
news_data = get_stock_news('002402', limit=10)

# 情感分析（简化规则）
def analyze_sentiment(news_items):
    positive_keywords = ['增长', '盈利', '突破', '订单', '扩张']
    negative_keywords = ['下滑', '亏损', '减持', '诉讼', '处罚']
    
    score = 50  # 中性基准
    for news in news_items:
        title = news['title']
        if any(kw in title for kw in positive_keywords):
            score += 5
        if any(kw in title for kw in negative_keywords):
            score -= 5
    
    return max(0, min(100, score))

sentiment_score = analyze_sentiment(news_data)
```

**数据结构**：
```python
news = {
    'sentiment': '中性偏正面',          # 基于sentiment_score判断
    'sentiment_score': 65,              # 0-100
    'fundamental_impact': '中性',        # 利好/利空/中性
    'items': [
        {
            'title': '和而泰发布一季度业绩预告',
            'date': '2026-04-10',
            'source': '证券时报',
            'sentiment': '正面',
            'summary': '预计净利润同比增长10-15%'
        },
        {
            'title': '电子元器件行业景气度回升',
            'date': '2026-04-08',
            'source': '上海证券报',
            'sentiment': '正面',
            'summary': '下游需求回暖，订单量增加'
        }
    ],
    'key_events': [                     # 关键事件提炼
        '4月10日发布一季度业绩预告',
        '智能控制器业务订单饱满'
    ]
}
```

---

### 4. 技术面数据

**需求**：基于K线计算技术指标

**计算代码**：
```python
import pandas as pd
import numpy as np

def calculate_technical_indicators(klines):
    df = pd.DataFrame(klines)
    
    # KDJ计算
    n = 9
    low_list = df['low'].rolling(window=n, min_periods=n).min()
    high_list = df['high'].rolling(window=n, min_periods=n).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    k = rsv.ewm(com=2, adjust=False).mean()
    d = k.ewm(com=2, adjust=False).mean()
    j = 3 * k - 2 * d
    
    # MACD计算
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    # RSI计算
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # 均线
    ma5 = df['close'].rolling(5).mean()
    ma10 = df['close'].rolling(10).mean()
    ma20 = df['close'].rolling(20).mean()
    ma60 = df['close'].rolling(60).mean()
    
    latest = df.index[-1]
    
    return {
        'k': k.iloc[-1],
        'd': d.iloc[-1],
        'j': j.iloc[-1],
        'kdj_signal': '金叉' if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2] 
                     else '死叉' if k.iloc[-1] < d.iloc[-1] and k.iloc[-2] >= d.iloc[-2]
                     else '正常',
        'macd': macd.iloc[-1],
        'dea': signal.iloc[-1],
        'histogram': histogram.iloc[-1],
        'macd_signal': '多头' if macd.iloc[-1] > 0 else '空头',
        'rsi': rsi.iloc[-1],
        'rsi_signal': '超买' if rsi.iloc[-1] > 70 else '超卖' if rsi.iloc[-1] < 30 else '正常',
        'ma5': ma5.iloc[-1],
        'ma10': ma10.iloc[-1],
        'ma20': ma20.iloc[-1],
        'ma60': ma60.iloc[-1],
        'price_above_ma5': df['close'].iloc[-1] > ma5.iloc[-1],
        'price_above_ma20': df['close'].iloc[-1] > ma20.iloc[-1],
        'price_above_ma60': df['close'].iloc[-1] > ma60.iloc[-1],
        'trend': '上升趋势' if df['close'].iloc[-1] > ma20.iloc[-1] > ma60.iloc[-1] 
                else '下降趋势' if df['close'].iloc[-1] < ma20.iloc[-1] < ma60.iloc[-1]
                else '震荡',
        'ma_alignment': '多头排列' if ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1]
                       else '空头排列' if ma5.iloc[-1] < ma10.iloc[-1] < ma20.iloc[-1]
                       else '纠缠'
    }

technical = calculate_technical_indicators(klines)
```

---

## 完整数据组装示例

```python
from templates.unified_report_template import generate_unified_report

# 组装完整数据
complete_data = {
    'code': '002402',
    'stock_name': '和而泰',
    'timestamp': '2026-04-17 03:45:00',
    'quote': quote,                    # 行情数据
    'technical': technical,            # 技术指标（基于K线计算）
    'fundamental': fundamental,        # 基本面（多期财务数据）
    'news': news,                      # 消息面（新闻+情感）
    'money_flow': money_flow,          # 资金面（20日流向）
    'suggestion': suggestion           # 综合建议
}

# 组装形态面数据
complete_pattern_data = {
    'candlestick': candlestick,        # K线形态识别结果
    'chanlun': chanlun,                # 缠论分析结果
    'resonance': resonance,            # 信号共振评分
    'sentiment': sentiment             # 市场情绪指数
}

# 生成完整报告
report = generate_unified_report(
    complete_data, 
    complete_pattern_data,
    output_format='markdown'  # 或 'html', 'text'
)

print(report['markdown'])
```

---

## 快速检查清单

在调用报告模板前，确认以下数据是否齐全：

- [ ] **K线数据**：至少60根日线（OHLCV）
- [ ] **财务数据**：最新1期 + 历史3期
- [ ] **新闻数据**：至少5条近期新闻
- [ ] **资金流向**：近20日主力/散户/北向数据

缺少任意一项，对应板块就会显示"暂无数据"。

---

## 建议

如果希望 **finance-data-retrieval** 和 **stock-analyst** 无缝衔接，建议：

1. **创建数据转换层**：将 finance-data-retrieval 的输出格式转换为 stock-analyst 需要的格式
2. **封装完整分析流程**：一键获取数据 → 计算指标 → 生成报告
3. **降级处理**：当某类数据缺失时，优雅地跳过对应板块而不是报错

这样可以实现：**finance-data-retrieval 作为唯一数据源** 的完整股票分析流程。
