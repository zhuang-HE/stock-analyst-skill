-- ============================================================
-- A股市场数据库 — 表结构定义 (SQLite)
-- 
-- Phase 1: 日K线 + 复权因子 + 指数 + 北向资金
-- Phase 2: 财报 + 龙虎榜 + 技术指标预计算
-- Phase 3: 分析报告存档 + 策略回测结果
-- ============================================================

-- 启用 WAL 模式（并发读性能更好）
PRAGMA journal_mode = WAL;

-- ============================================================
-- 1. 股票基础信息
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_basic (
    ts_code     TEXT PRIMARY KEY,           -- 600519.SH (AkShare格式)
    bs_code     TEXT,                       -- sh.600519 (Baostock格式)
    name        TEXT,                       -- 贵州茅台
    industry    TEXT,                       -- 申万行业
    market      TEXT,                       -- SH/SZ/BJ
    list_date   TEXT,                       -- 上市日期 20010827
    delist_date TEXT,                       -- 退市日期(如有)
    is_hs       TEXT DEFAULT 'N',           -- 沪深港通标的 H:沪股通 S:深股通 N:否
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_basic_market ON stock_basic(market);

-- ============================================================
-- 2. 日K线（核心表 — 最重要）
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_daily (
    ts_code     TEXT NOT NULL,
    trade_date  TEXT NOT NULL,              -- YYYYMMDD
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    pre_close   REAL,
    change      REAL,                       -- 涨跌额
    pct_chg     REAL,                       -- 涨跌幅(%)
    vol         REAL,                       -- 成交量(手)
    amount      REAL,                       -- 成交额(千元)
    turnover    REAL,                       -- 换手率(%)
    PRIMARY KEY (ts_code, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_daily_date ON stock_daily(trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_code ON stock_daily(ts_code);

-- ============================================================
-- 3. 复权因子
-- ============================================================
CREATE TABLE IF NOT EXISTS adj_factor (
    ts_code     TEXT NOT NULL,
    trade_date  TEXT NOT NULL,
    adj_factor  REAL NOT NULL,              -- 复权因子
    PRIMARY KEY (ts_code, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_adj_code ON adj_factor(ts_code);

-- ============================================================
-- 4. 指数日K
-- ============================================================
CREATE TABLE IF NOT EXISTS index_daily (
    ts_code     TEXT NOT NULL,              -- 000300.SH
    trade_date  TEXT NOT NULL,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    pre_close   REAL,
    change      REAL,
    pct_chg     REAL,
    vol         REAL,
    amount      REAL,
    PRIMARY KEY (ts_code, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_idxdaily_date ON index_daily(trade_date);

-- ============================================================
-- 5. 指数成分股及权重
-- ============================================================
CREATE TABLE IF NOT EXISTS index_weight (
    index_code  TEXT NOT NULL,
    con_code    TEXT NOT NULL,
    con_name    TEXT,
    trade_date  TEXT NOT NULL,
    weight      REAL,
    PRIMARY KEY (index_code, con_code, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_weight_index ON index_weight(index_code, trade_date);

-- ============================================================
-- 6. 北向资金
-- ============================================================
CREATE TABLE IF NOT EXISTS moneyflow_hsgt (
    trade_date  TEXT PRIMARY KEY,
    north_money REAL,                       -- 北向资金净买入(亿)
    sh_money    REAL,                       -- 沪股通净买入(亿)
    sz_money    REAL,                       -- 深股通净买入(亿)
    north_hold  REAL,                       -- 北向资金持股总市值(亿)
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 7. 融资融券
-- ============================================================
CREATE TABLE IF NOT EXISTS margin_detail (
    ts_code     TEXT NOT NULL,
    trade_date  TEXT NOT NULL,
    rzye        REAL,                       -- 融资余额(亿)
    rzmre       REAL,                       -- 融资买入额(亿)
    rzche       REAL,                       -- 融资偿还额(亿)
    rqye        REAL,                       -- 融券余额(亿)
    rqmcl       REAL,                       -- 融券余量(万股)
    rzrqye      REAL,                       -- 融资融券余额(亿)
    PRIMARY KEY (ts_code, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_margin_date ON margin_detail(trade_date);

-- ============================================================
-- 8. 财务报表 — 利润表
-- ============================================================
CREATE TABLE IF NOT EXISTS income (
    ts_code     TEXT NOT NULL,
    end_date    TEXT NOT NULL,              -- 报告期 20260331
    ann_date    TEXT,                       -- 公告日期
    report_type TEXT DEFAULT '1',           -- 1:合并 2:单季
    revenue     REAL,                       -- 营业总收入
    operate_cost REAL,                      -- 营业成本
    total_profit REAL,                      -- 利润总额
    net_profit  REAL,                       -- 净利润
    net_profit_attr REAL,                   -- 归母净利润
    diluted_eps REAL,                       -- 稀释EPS
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ts_code, end_date, report_type)
);

-- ============================================================
-- 9. 财务报表 — 资产负债表(关键字段)
-- ============================================================
CREATE TABLE IF NOT EXISTS balancesheet (
    ts_code     TEXT NOT NULL,
    end_date    TEXT NOT NULL,
    ann_date    TEXT,
    report_type TEXT DEFAULT '1',
    total_assets  REAL,                     -- 总资产
    total_liab    REAL,                     -- 总负债
    total_equity  REAL,                     -- 所有者权益
    money_cap     REAL,                     -- 货币资金
    accounts_recv REAL,                     -- 应收账款
    inventory     REAL,                     -- 存货
    fixed_assets  REAL,                     -- 固定资产
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ts_code, end_date, report_type)
);

-- ============================================================
-- 10. 预计算技术指标（避免每次重复计算）
-- ============================================================
CREATE TABLE IF NOT EXISTS tech_indicators (
    ts_code     TEXT NOT NULL,
    trade_date  TEXT NOT NULL,
    ma5         REAL,
    ma10        REAL,
    ma20        REAL,
    ma60        REAL,
    ma120       REAL,
    ma250       REAL,
    macd_dif    REAL,
    macd_dea    REAL,
    macd_hist   REAL,
    rsi_6       REAL,
    rsi_14      REAL,
    rsi_24      REAL,
    kdj_k       REAL,
    kdj_d       REAL,
    kdj_j       REAL,
    boll_upper  REAL,
    boll_mid    REAL,
    boll_lower  REAL,
    atr_14      REAL,                       -- 14日ATR
    obv         REAL,                       -- 能量潮
    PRIMARY KEY (ts_code, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_tech_date ON tech_indicators(trade_date);

-- ============================================================
-- 11. 数据更新日志
-- ============================================================
CREATE TABLE IF NOT EXISTS data_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name  TEXT NOT NULL,
    action      TEXT NOT NULL,              -- INSERT / UPSERT / FULL_REFRESH / DELTA
    record_count INTEGER DEFAULT 0,
    start_date  TEXT,
    end_date    TEXT,
    source      TEXT,                       -- baostock / akshare
    duration_ms INTEGER,                    -- 耗时毫秒
    status      TEXT DEFAULT 'success',     -- success / failed
    error_msg   TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 12. 数据库元信息
-- ============================================================
CREATE TABLE IF NOT EXISTS db_meta (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 初始化元信息
INSERT OR REPLACE INTO db_meta (key, value) VALUES ('schema_version', '1.0');
INSERT OR REPLACE INTO db_meta (key, value) VALUES ('created_at', CURRENT_TIMESTAMP);
