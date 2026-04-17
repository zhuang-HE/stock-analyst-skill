# -*- coding: utf-8 -*-
"""
技术指标预计算模块

从 stock_daily 表读取原始K线，批量计算技术指标并写入 tech_indicators 表。
避免每次查询时重复计算，提升报告生成速度。

支持计算的指标：
- 均线：MA5/MA10/MA20/MA60/MA120/MA250
- MACD：DIF/DEA/Histogram
- RSI：6日/14日/24日
- KDJ：K/D/J
- 布林带：Upper/Mid/Lower
- ATR：14日
- OBV：能量潮

用法：
    # 计算指定股票
    python -m data_store.tech_calc --codes 600519.SH,000001.SZ

    # 计算全部股票（增量，只算最新未计算的日期）
    python -m data_store.tech_calc --all

    # 强制全量重算
    python -m data_store.tech_calc --all --force
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd

try:
    from .database import Database
except ImportError:
    from database import Database


# ═══════════════════════════════════════════════════════════════
#  核心计算函数
# ═══════════════════════════════════════════════════════════════

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    给定日K线 DataFrame，计算所有技术指标。

    输入 df 必须包含列：trade_date, open, high, low, close, vol, amount
    返回带有技术指标列的 DataFrame。
    """
    if df is None or len(df) < 5:
        return pd.DataFrame()

    # 确保按日期升序排列
    df = df.sort_values("trade_date", ascending=True).reset_index(drop=True)

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["vol"].astype(float) if "vol" in df.columns else pd.Series(0, index=df.index)

    # ─── 均线 ───
    for period in [5, 10, 20, 60, 120, 250]:
        df[f"ma{period}"] = close.rolling(window=period, min_periods=1).mean().round(4)

    # ─── MACD ───
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = (ema12 - ema26).round(4)
    dea = dif.ewm(span=9, adjust=False).mean().round(4)
    hist = ((dif - dea) * 2).round(4)
    df["macd_dif"] = dif
    df["macd_dea"] = dea
    df["macd_hist"] = hist

    # ─── RSI ───
    for period in [6, 14, 24]:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        # 用 EWM 平滑
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df[f"rsi_{period}"] = (100 - (100 / (1 + rs))).round(2)

    # ─── KDJ ───
    n = 9
    low_n = low.rolling(window=n, min_periods=n).min()
    high_n = high.rolling(window=n, min_periods=n).max()
    rsv = ((close - low_n) / (high_n - low_n) * 100).fillna(50)
    k = rsv.ewm(com=2, adjust=False).mean()
    d = k.ewm(com=2, adjust=False).mean()
    j = (3 * k - 2 * d)
    df["kdj_k"] = k.round(2)
    df["kdj_d"] = d.round(2)
    df["kdj_j"] = j.round(2)

    # ─── 布林带 ───
    ma20 = close.rolling(20, min_periods=1).mean()
    std20 = close.rolling(20, min_periods=1).std()
    df["boll_upper"] = (ma20 + 2 * std20).round(4)
    df["boll_mid"] = ma20.round(4)
    df["boll_lower"] = (ma20 - 2 * std20).round(4)

    # ─── ATR ───
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14, min_periods=1).mean().round(4)

    # ─── OBV ───
    obv = pd.Series(0.0, index=df.index)
    for i in range(1, len(df)):
        if close.iloc[i] > close.iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i - 1]
    df["obv"] = obv.round(0)

    return df


# ═══════════════════════════════════════════════════════════════
#  批量计算与入库
# ═══════════════════════════════════════════════════════════════

# 技术指标列名（对应 tech_indicators 表）
TECH_COLUMNS = [
    "ts_code", "trade_date",
    "ma5", "ma10", "ma20", "ma60", "ma120", "ma250",
    "macd_dif", "macd_dea", "macd_hist",
    "rsi_6", "rsi_14", "rsi_24",
    "kdj_k", "kdj_d", "kdj_j",
    "boll_upper", "boll_mid", "boll_lower",
    "atr_14", "obv",
]


def calc_and_save(
    db: Database,
    ts_code: str,
    force: bool = False,
    min_rows: int = 5,
) -> int:
    """
    计算单只股票的技术指标并写入数据库。

    Args:
        db: 数据库连接
        ts_code: 股票代码（AkShare 格式）
        force: 是否强制全量重算
        min_rows: 最少需要多少条K线才开始计算

    Returns:
        写入的指标行数
    """
    # 1. 获取日K线数据
    df = db.query_df(
        "SELECT ts_code, trade_date, open, high, low, close, vol, amount "
        "FROM stock_daily WHERE ts_code = ? ORDER BY trade_date",
        (ts_code,),
    )
    if df is None or len(df) < min_rows:
        return 0

    # 2. 增量模式：只计算未入库的最新日期之后的数据
    if not force:
        last_row = db.query_one(
            "SELECT MAX(trade_date) as max_date FROM tech_indicators WHERE ts_code = ?",
            (ts_code,),
        )
        if last_row and last_row["max_date"]:
            last_date = last_row["max_date"]
            # 需要从更早的日期开始（MA250 需要250天预热）
            df_calc = df[df["trade_date"] >= last_date].copy()
            if len(df_calc) == 0 or (len(df_calc) == 1 and df_calc.iloc[0]["trade_date"] == last_date):
                return 0  # 无新数据

    # 3. 计算
    result = calculate_all_indicators(df)
    if result.empty:
        return 0

    # 4. 增量模式：只写入新计算的行
    if not force:
        existing = db.query_one(
            "SELECT MAX(trade_date) as max_date FROM tech_indicators WHERE ts_code = ?",
            (ts_code,),
        )
        if existing and existing["max_date"]:
            result = result[result["trade_date"] > existing["max_date"]]

    if result.empty:
        return 0

    # 5. 转换为入库格式
    rows = []
    for _, r in result.iterrows():
        row = {}
        for col in TECH_COLUMNS:
            if col in ("ts_code", "trade_date"):
                row[col] = r.get(col, "")
            else:
                val = r.get(col, None)
                row[col] = float(val) if val is not None and not (isinstance(val, float) and np.isnan(val)) else None
        rows.append(row)

    # 6. 写入
    count = db.upsert_batch(
        "tech_indicators", rows,
        conflict_keys=["ts_code", "trade_date"],
    )
    return count


def calc_all_stocks(
    db: Database,
    force: bool = False,
    batch_log: int = 100,
) -> dict:
    """
    批量计算全部股票的技术指标。

    Returns:
        {"total": 总股票数, "calculated": 成功数, "failed": 失败数, "total_rows": 总行数}
    """
    # 获取所有有日K线的股票
    rows = db.query_all(
        "SELECT DISTINCT ts_code FROM stock_daily"
    )
    codes = [r[0] for r in rows]

    print(f"[技术指标] 共 {len(codes)} 只股票待计算 (force={force})")

    total_rows = 0
    calculated = 0
    failed = 0
    start = time.time()

    for i, code in enumerate(codes):
        try:
            n = calc_and_save(db, code, force=force)
            total_rows += n
            calculated += 1
        except Exception as e:
            failed += 1
            if failed <= 5:
                print(f"  ✗ {code} 计算失败: {e}")

        if (i + 1) % batch_log == 0:
            elapsed = time.time() - start
            eta = elapsed / (i + 1) * (len(codes) - i - 1)
            print(f"  [{i+1}/{len(codes)}] 累计 {total_rows} 行, "
                  f"成功 {calculated}, 失败 {failed}, "
                  f"ETA {eta/60:.1f}min")

    elapsed = time.time() - start
    print(f"\n  📊 技术指标计算完成: {total_rows} 行, "
          f"成功 {calculated}, 失败 {failed}, "
          f"耗时 {elapsed:.1f}s")

    db.log_operation(
        table_name="tech_indicators",
        action="FULL_REFRESH" if force else "DELTA",
        record_count=total_rows,
        source="local_calc",
        duration_ms=int(elapsed * 1000),
    )

    return {
        "total": len(codes),
        "calculated": calculated,
        "failed": failed,
        "total_rows": total_rows,
    }


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="技术指标预计算")
    parser.add_argument("--codes", default=None, help="指定股票代码（逗号分隔）")
    parser.add_argument("--all", action="store_true", help="计算全部股票")
    parser.add_argument("--force", action="store_true", help="强制全量重算")
    parser.add_argument("--data-dir", default=None, help="数据目录")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════╗")
    print("║   技术指标预计算                            ║")
    print("╚══════════════════════════════════════════════╝")

    db = Database(data_dir=args.data_dir)
    db.connect()

    if not db.is_initialized():
        print("  ⚠ 数据库未初始化，请先运行 backfill.py")
        db.close()
        return

    if args.codes:
        codes = [c.strip() for c in args.codes.split(",")]
        total = 0
        for code in codes:
            n = calc_and_save(db, code, force=args.force)
            total += n
            print(f"  {code}: {n} 行")
        print(f"\n  ✓ 总计: {total} 行")

    elif args.all:
        result = calc_all_stocks(db, force=args.force)
        print(f"\n  结果: {result}")

    else:
        parser.print_help()

    db.close()
    print("\n✅ 计算完成！")


if __name__ == "__main__":
    main()
