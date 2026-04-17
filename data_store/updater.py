"""
A股市场数据库 — 增量更新脚本

每日收盘后执行，增量拉取当日最新数据并更新数据库。
支持通过 cron / 任务计划程序 / WorkBuddy Automation 自动执行。

用法：
    # 更新今日数据
    python updater.py

    # 更新指定日期（补漏）
    python updater.py --date 20260416

    # 只更新日K线（跳过其他）
    python updater.py --daily-only

    # 更新北向资金
    python updater.py --moneyflow

    # 更新融资融券
    python updater.py --margin

    # 全量更新（日K + 复权 + 北向 + 融资）
    python updater.py --all
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta
from typing import Optional

import baostock as bs

from database import Database
from backfill import (
    BaoStockSession,
    fetch_stock_daily,
    fetch_adj_factor,
    fetch_index_daily,
    MAJOR_INDICES,
    _safe_float,
)


# ═══════════════════════════════════════════════════════════════
#  AkShare 增量拉取（北向资金、融资融券）
# ═══════════════════════════════════════════════════════════════

def update_moneyflow_hsgt(db: Database, trade_date: str) -> int:
    """
    更新北向资金数据（使用 AkShare）。

    Args:
        trade_date: YYYYMMDD 格式
    """
    try:
        import akshare as ak
    except ImportError:
        print("  ⚠ 未安装 akshare，跳过北向资金更新。pip install akshare")
        return 0

    print(f"  拉取北向资金数据 {trade_date}...")
    try:
        df = ak.moneyflow_hsgt_em(symbol="北向")
        if df is None or df.empty:
            print("  ⚠ 北向资金无数据")
            return 0

        # 转换日期格式
        df["trade_date"] = df["日期"].astype(str).str.replace("-", "")

        # 过滤到目标日期
        target_df = df[df["trade_date"] == trade_date]

        if target_df.empty:
            # 也尝试拉最近几天的
            recent_df = df.head(5)
            target_df = recent_df

        rows = []
        for _, r in target_df.iterrows():
            rows.append({
                "trade_date": r.get("trade_date", ""),
                "north_money": _safe_float(r.get("当日成交净买额", r.get("北向资金", None))),
                "sh_money": _safe_float(r.get("沪股通净买额", None)),
                "sz_money": _safe_float(r.get("深股通净买额", None)),
                "north_hold": _safe_float(r.get("当日资金余额", None)),
            })

        if rows:
            count = db.upsert_batch(
                "moneyflow_hsgt", rows, conflict_keys=["trade_date"]
            )
            print(f"  ✓ 北向资金更新 {count} 条")
            db.log_operation(
                table_name="moneyflow_hsgt",
                action="DELTA",
                record_count=count,
                end_date=trade_date,
                source="akshare",
            )
            return count

    except Exception as e:
        print(f"  ✗ 北向资金更新失败: {e}")
        db.log_operation(
            table_name="moneyflow_hsgt",
            action="DELTA",
            status="failed",
            error_msg=str(e),
            source="akshare",
        )

    return 0


def update_margin_detail(db: Database, trade_date: str) -> int:
    """
    更新融资融券数据（使用 AkShare）。

    Args:
        trade_date: YYYYMMDD 格式
    """
    try:
        import akshare as ak
    except ImportError:
        print("  ⚠ 未安装 akshare，跳过融资融券更新")
        return 0

    print(f"  拉取融资融券数据 {trade_date}...")
    try:
        df = ak.margin_detail_sz_sh(date=trade_date)
        if df is None or df.empty:
            print("  ⚠ 融资融券无数据")
            return 0

        rows = []
        for _, r in df.iterrows():
            raw_code = str(r.get("标的证券代码", r.get("证券代码", "")))
            market = str(r.get("市场", ""))
            if market in ("SH", "sh") or raw_code.startswith("6"):
                ts_code = f"{raw_code}.SH"
            elif market in ("SZ", "sz") or raw_code.startswith(("0", "3")):
                ts_code = f"{raw_code}.SZ"
            else:
                continue

            rows.append({
                "ts_code": ts_code,
                "trade_date": trade_date,
                "rzye": _safe_float(r.get("融资余额", r.get("融资买入额", None))),
                "rzmre": _safe_float(r.get("融资买入额", None)),
                "rzche": _safe_float(r.get("融资偿还额", None)),
                "rqye": _safe_float(r.get("融券余额", None)),
                "rqmcl": _safe_float(r.get("融券余量", None)),
                "rzrqye": _safe_float(r.get("融资融券余额", None)),
            })

        if rows:
            count = db.upsert_batch(
                "margin_detail", rows, conflict_keys=["ts_code", "trade_date"]
            )
            print(f"  ✓ 融资融券更新 {count} 条")
            db.log_operation(
                table_name="margin_detail",
                action="DELTA",
                record_count=count,
                end_date=trade_date,
                source="akshare",
            )
            return count

    except Exception as e:
        print(f"  ✗ 融资融券更新失败: {e}")
        db.log_operation(
            table_name="margin_detail",
            action="DELTA",
            status="failed",
            error_msg=str(e),
            source="akshare",
        )

    return 0


# ═══════════════════════════════════════════════════════════════
#  日K线增量更新
# ═══════════════════════════════════════════════════════════════

def update_daily(db: Database, trade_date: str, delay: float = 0.15) -> int:
    """
    增量更新全A股日K线 + 复权因子。

    Args:
        trade_date: YYYYMMDD 格式
        delay: 每只股票间延迟
    """
    date_hyphen = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"

    rows = db.query_all(
        "SELECT ts_code, bs_code FROM stock_basic "
        "WHERE delist_date IS NULL OR delist_date = ''"
    )
    stocks = [{"ts_code": r[0], "bs_code": r[1]} for r in rows]

    print(f"  更新日K线 {trade_date}，共 {len(stocks)} 只股票...")

    total_daily = 0
    total_adj = 0
    failed = 0

    for i, stock in enumerate(stocks):
        bs_code = stock["bs_code"]
        ts_code = stock["ts_code"]

        try:
            daily_rows = fetch_stock_daily(bs_code, date_hyphen, date_hyphen)
            if daily_rows:
                n = db.upsert_batch(
                    "stock_daily", daily_rows, conflict_keys=["ts_code", "trade_date"]
                )
                total_daily += n

            adj_rows = fetch_adj_factor(bs_code, date_hyphen, date_hyphen)
            if adj_rows:
                n = db.upsert_batch(
                    "adj_factor", adj_rows, conflict_keys=["ts_code", "trade_date"]
                )
                total_adj += n

        except Exception:
            failed += 1

        if (i + 1) % 200 == 0:
            print(f"    [{i+1}/{len(stocks)}] 日K {total_daily} / 复权 {total_adj} / 失败 {failed}")

        if delay > 0:
            time.sleep(delay)

    db.log_operation(
        table_name="stock_daily",
        action="DELTA",
        record_count=total_daily,
        end_date=trade_date,
        source="baostock",
    )
    db.log_operation(
        table_name="adj_factor",
        action="DELTA",
        record_count=total_adj,
        end_date=trade_date,
        source="baostock",
    )

    print(f"  ✓ 日K线 {total_daily} 条 / 复权 {total_adj} 条 / 失败 {failed} 只")
    return total_daily + total_adj


def update_index_daily(db: Database, trade_date: str) -> int:
    """增量更新主要指数日K线"""
    date_hyphen = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"

    total = 0
    for bs_code, name in MAJOR_INDICES.items():
        try:
            rows = fetch_index_daily(bs_code, date_hyphen, date_hyphen)
            if rows:
                n = db.upsert_batch(
                    "index_daily", rows, conflict_keys=["ts_code", "trade_date"]
                )
                total += n
                print(f"  ✓ {name}: {n} 条")
        except Exception as e:
            print(f"  ✗ {name}: {e}")

    db.log_operation(
        table_name="index_daily",
        action="DELTA",
        record_count=total,
        end_date=trade_date,
        source="baostock",
    )
    return total


# ═══════════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="A股市场数据增量更新")
    parser.add_argument("--date", default=None, help="指定日期 YYYYMMDD（默认今天）")
    parser.add_argument("--daily-only", action="store_true", help="只更新日K线")
    parser.add_argument("--moneyflow", action="store_true", help="更新北向资金")
    parser.add_argument("--margin", action="store_true", help="更新融资融券")
    parser.add_argument("--all", action="store_true", help="全量更新")
    parser.add_argument("--delay", type=float, default=0.15, help="每只股票间延迟（秒）")
    parser.add_argument("--data-dir", default=None, help="数据目录")
    args = parser.parse_args()

    # 确定更新日期
    if args.date:
        trade_date = args.date
    else:
        now = datetime.now()
        if now.weekday() < 5 and now.hour >= 16:
            trade_date = now.strftime("%Y%m%d")
        else:
            prev = now - timedelta(days=1)
            while prev.weekday() >= 5:
                prev -= timedelta(days=1)
            trade_date = prev.strftime("%Y%m%d")

    print("╔══════════════════════════════════════════════╗")
    print("║   A股市场数据库 — 增量更新                  ║")
    print(f"║   日期: {trade_date}                          ║")
    print("╚══════════════════════════════════════════════╝")

    db = Database(data_dir=args.data_dir)
    db.connect()

    if not db.is_initialized():
        print("  ⚠ 数据库未初始化，请先运行 backfill.py")
        db.close()
        return

    do_daily = True
    do_moneyflow = args.moneyflow or args.all
    do_margin = args.margin or args.all

    with BaoStockSession():
        if do_daily:
            print(f"\n[1/3] 日K线 + 复权因子")
            update_daily(db, trade_date, delay=args.delay)

            print(f"\n[2/3] 指数日K线")
            update_index_daily(db, trade_date)

        if do_moneyflow:
            print(f"\n[3/3] 北向资金")
            update_moneyflow_hsgt(db, trade_date)

        if do_margin:
            print(f"\n[4/4] 融资融券")
            update_margin_detail(db, trade_date)

    stats = db.get_db_stats()
    print(f"\n✅ 更新完成！数据库大小: {stats.get('db_size_mb', 0)} MB")

    db.close()


if __name__ == "__main__":
    main()
