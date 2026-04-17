"""
A股市场数据库 — 历史数据回填脚本

使用 Baostock 拉取全A股历史日K线 + 复权因子，批量写入本地 SQLite 数据库。
数据存储路径：D:/stock-data/a_market.db（可通过环境变量 STOCK_DATA_DIR 修改）

用法：
    # 首次全量回填（约 5000 只股票，耗时 1-3 小时）
    python backfill.py

    # 只回填指定股票
    python backfill.py --codes 600519.SH,000001.SZ

    # 指定起止日期
    python backfill.py --start 20200101 --end 20260417

    # 只回填股票列表（不拉K线）
    python backfill.py --stock-list-only

    # 调整并发和批大小
    python backfill.py --batch-size 100 --delay 0.3
"""

from __future__ import annotations

import argparse
import time
import sys
from datetime import datetime, timedelta
from typing import List, Optional

import baostock as bs

from database import Database


# ═══════════════════════════════════════════════════════════════
#  Baostock 登录管理
# ═══════════════════════════════════════════════════════════════

class BaoStockSession:
    """Baostock 登录会话管理器"""

    def __init__(self):
        self._logged_in = False

    def __enter__(self):
        lg = bs.login()
        if lg.error_code != "0":
            raise ConnectionError(f"Baostock 登录失败: {lg.error_msg}")
        self._logged_in = True
        print(f"[Baostock] 登录成功")
        return self

    def __exit__(self, *args):
        if self._logged_in:
            bs.logout()
            print(f"[Baostock] 已登出")


# ═══════════════════════════════════════════════════════════════
#  数据拉取
# ═══════════════════════════════════════════════════════════════

def fetch_stock_list() -> List[dict]:
    """
    拉取全A股股票列表（含已退市）。
    返回 AkShare 格式的 ts_code。
    """
    print("[1/1] 拉取全A股股票列表...")
    rs = bs.query_stock_basic(
        code_name="",
    )  # 全量
    # 注意：baostock 的 query_stock_basic 不支持直接拉全量
    # 改用 query_all_stock 取当日全量
    today = datetime.now().strftime("%Y-%m-%d")
    rs = bs.query_all_stock(day=today)

    stocks = []
    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        bs_code = row[0]  # sh.600519
        code_num = bs_code.split(".")[1] if "." in bs_code else bs_code

        # 过滤：只要 A 股（沪深主板+创业板+科创板+北交所）
        if not (code_num.startswith("6") or    # 沪市主板
                code_num.startswith("0") or    # 深市主板
                code_num.startswith("3") or    # 创业板
                code_num.startswith("688") or  # 科创板
                code_num.startswith("8") or    # 北交所
                code_num.startswith("4")):     # 北交所/老三板
            continue

        ts_code = Database.bs_to_akshare(bs_code)
        stocks.append({
            "ts_code": ts_code,
            "bs_code": bs_code,
            "name": row[1] if len(row) > 1 else "",
        })

    print(f"  → 获取到 {len(stocks)} 只 A 股")
    return stocks


def fetch_stock_daily(bs_code: str, start_date: str, end_date: str) -> List[dict]:
    """
    拉取单只股票的日K线数据（不复权）。

    Args:
        bs_code: Baostock 格式代码，如 sh.600519
        start_date: 起始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
    """
    rs = bs.query_history_k_data_plus(
        bs_code,
        "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="3",  # 不复权
    )

    rows = []
    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        ts_code = Database.bs_to_akshare(bs_code)
        trade_date = row[0].replace("-", "")  # 2026-04-17 → 20260417

        rows.append({
            "ts_code": ts_code,
            "trade_date": trade_date,
            "open": _safe_float(row[1]),
            "high": _safe_float(row[2]),
            "low": _safe_float(row[3]),
            "close": _safe_float(row[4]),
            "pre_close": _safe_float(row[5]),
            "vol": _safe_float(row[6]),
            "amount": _safe_float(row[7]),
            "turnover": _safe_float(row[8]),
            "pct_chg": _safe_float(row[9]),
        })

    return rows


def fetch_adj_factor(bs_code: str, start_date: str, end_date: str) -> List[dict]:
    """
    拉取单只股票的复权因子。

    Args:
        bs_code: Baostock 格式代码
        start_date: 起始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
    """
    rs = bs.query_adjust_factor(
        code=bs_code,
        start_date=start_date,
        end_date=end_date,
    )

    rows = []
    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        ts_code = Database.bs_to_akshare(bs_code)
        trade_date = row[1].replace("-", "")

        rows.append({
            "ts_code": ts_code,
            "trade_date": trade_date,
            "adj_factor": _safe_float(row[3]) if len(row) > 3 else _safe_float(row[2]),
        })

    return rows


def fetch_index_daily(bs_code: str, start_date: str, end_date: str) -> List[dict]:
    """拉取指数日K线"""
    rs = bs.query_history_k_data_plus(
        bs_code,
        "date,open,high,low,close,preclose,volume,amount,pctChg",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="3",
    )

    rows = []
    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        ts_code = Database.bs_to_akshare(bs_code)
        trade_date = row[0].replace("-", "")

        rows.append({
            "ts_code": ts_code,
            "trade_date": trade_date,
            "open": _safe_float(row[1]),
            "high": _safe_float(row[2]),
            "low": _safe_float(row[3]),
            "close": _safe_float(row[4]),
            "pre_close": _safe_float(row[5]),
            "vol": _safe_float(row[6]),
            "amount": _safe_float(row[7]),
            "pct_chg": _safe_float(row[8]),
        })

    return rows


# ═══════════════════════════════════════════════════════════════
#  回填流程
# ═══════════════════════════════════════════════════════════════

# 主要指数的 Baostock 代码
MAJOR_INDICES = {
    "sh.000001": "上证指数",
    "sz.399001": "深证成指",
    "sh.000300": "沪深300",
    "sz.399006": "创业板指",
    "sh.000016": "上证50",
    "sh.000905": "中证500",
    "sh.000852": "中证1000",
}


def backfill_stock_list(db: Database) -> int:
    """回填股票基础信息列表"""
    print("\n" + "=" * 60)
    print("  Step 1: 回填股票基础信息")
    print("=" * 60)

    stocks = fetch_stock_list()
    if not stocks:
        print("  ⚠ 未获取到股票列表，跳过")
        return 0

    # 补充行业信息（通过 Baostock 的 stock_basic 接口）
    stock_rows = []
    for s in stocks:
        stock_rows.append({
            "ts_code": s["ts_code"],
            "bs_code": s["bs_code"],
            "name": s["name"],
            "market": s["ts_code"].split(".")[1],
        })

    count = db.upsert_batch(
        "stock_basic",
        stock_rows,
        conflict_keys=["ts_code"],
    )
    print(f"  ✓ 写入 {count} 条股票基础信息")
    return count


def backfill_daily(
    db: Database,
    stocks: List[dict],
    start_date: str = "2000-01-01",
    end_date: Optional[str] = None,
    batch_size: int = 50,
    delay: float = 0.2,
) -> int:
    """
    回填日K线 + 复权因子。

    Args:
        db: 数据库连接
        stocks: 股票列表 [{"ts_code": ..., "bs_code": ...}, ...]
        start_date: 起始日期 YYYY-MM-DD
        end_date: 结束日期，默认今天
        batch_size: 每批写入的股票数
        delay: 每只股票之间的延迟（秒），避免被限流
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    total_daily = 0
    total_adj = 0
    failed = []

    print(f"\n  日K线回填范围: {start_date} ~ {end_date}")
    print(f"  股票数量: {len(stocks)}")
    print(f"  预计耗时: {len(stocks) * delay / 60:.0f} 分钟\n")

    for i, stock in enumerate(stocks):
        bs_code = stock["bs_code"]
        ts_code = stock.get("ts_code", Database.bs_to_akshare(bs_code))

        try:
            # 拉日K线
            daily_rows = fetch_stock_daily(bs_code, start_date, end_date)
            if daily_rows:
                n = db.upsert_batch(
                    "stock_daily", daily_rows, conflict_keys=["ts_code", "trade_date"]
                )
                total_daily += n

            # 拉复权因子
            adj_rows = fetch_adj_factor(bs_code, start_date, end_date)
            if adj_rows:
                n = db.upsert_batch(
                    "adj_factor", adj_rows, conflict_keys=["ts_code", "trade_date"]
                )
                total_adj += n

        except Exception as e:
            failed.append((ts_code, str(e)))
            print(f"  ✗ [{i+1}/{len(stocks)}] {ts_code} 失败: {e}")
            continue

        # 进度显示
        if (i + 1) % 50 == 0 or i == len(stocks) - 1:
            print(f"  ✓ [{i+1}/{len(stocks)}] {ts_code} "
                  f"日K {len(daily_rows)}条 | 复权 {len(adj_rows)}条 | "
                  f"累计日K {total_daily} / 复权 {total_adj}")

        # 延迟防限流
        if delay > 0:
            time.sleep(delay)

    # 记录日志
    db.log_operation(
        table_name="stock_daily",
        action="FULL_REFRESH",
        record_count=total_daily,
        start_date=start_date.replace("-", ""),
        end_date=end_date.replace("-", ""),
        source="baostock",
    )
    db.log_operation(
        table_name="adj_factor",
        action="FULL_REFRESH",
        record_count=total_adj,
        start_date=start_date.replace("-", ""),
        end_date=end_date.replace("-", ""),
        source="baostock",
    )

    print(f"\n  📊 日K线总计: {total_daily} 条")
    print(f"  📊 复权因子总计: {total_adj} 条")
    if failed:
        print(f"  ⚠ 失败 {len(failed)} 只: {[f[0] for f in failed[:10]]}")

    return total_daily + total_adj


def backfill_indices(
    db: Database,
    start_date: str = "2000-01-01",
    end_date: Optional[str] = None,
) -> int:
    """回填主要指数日K线"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "=" * 60)
    print("  Step 3: 回填主要指数日K线")
    print("=" * 60)

    total = 0
    for bs_code, name in MAJOR_INDICES.items():
        try:
            rows = fetch_index_daily(bs_code, start_date, end_date)
            if rows:
                n = db.upsert_batch(
                    "index_daily", rows, conflict_keys=["ts_code", "trade_date"]
                )
                total += n
                print(f"  ✓ {name} ({bs_code}): {n} 条")
            else:
                print(f"  ⚠ {name} ({bs_code}): 无数据")
        except Exception as e:
            print(f"  ✗ {name} ({bs_code}) 失败: {e}")

    db.log_operation(
        table_name="index_daily",
        action="FULL_REFRESH",
        record_count=total,
        start_date=start_date.replace("-", ""),
        end_date=end_date.replace("-", ""),
        source="baostock",
    )

    return total


# ═══════════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="A股市场数据历史回填")
    parser.add_argument("--start", default="2000-01-01", help="起始日期 YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="结束日期（默认今天）")
    parser.add_argument("--codes", default=None, help="指定股票代码（逗号分隔，AkShare格式）")
    parser.add_argument("--stock-list-only", action="store_true", help="只回填股票列表")
    parser.add_argument("--skip-stock-list", action="store_true", help="跳过股票列表回填")
    parser.add_argument("--skip-indices", action="store_true", help="跳过指数回填")
    parser.add_argument("--batch-size", type=int, default=50, help="每批写入股票数")
    parser.add_argument("--delay", type=float, default=0.2, help="每只股票间延迟（秒）")
    parser.add_argument("--data-dir", default=None, help="数据目录（默认 D:/stock-data）")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════╗")
    print("║   A股市场数据库 — 历史数据回填              ║")
    print("╚══════════════════════════════════════════════╝")

    # 初始化数据库
    db = Database(data_dir=args.data_dir)
    db.connect()

    if not db.is_initialized():
        print("\n[初始化] 创建数据库表...")
        db.initialize()
        print("  ✓ 数据库初始化完成")
    else:
        print("\n[初始化] 数据库已存在，跳过建表")

    # 打印当前状态
    stats = db.get_db_stats()
    print(f"\n当前数据库状态:")
    for table, count in stats.items():
        if count >= 0:
            print(f"  {table}: {count:,} 行")

    with BaoStockSession():
        # Step 1: 股票列表
        if not args.skip_stock_list:
            backfill_stock_list(db)
        else:
            print("\n[跳过] 股票列表回填")

        if args.stock_list_only:
            print("\n✅ 仅回填股票列表，完成。")
            db.close()
            return

        # Step 2: 日K线 + 复权因子
        stocks = []
        if args.codes:
            # 指定股票
            codes = [c.strip() for c in args.codes.split(",")]
            stocks = [
                {"ts_code": c, "bs_code": Database.akshare_to_bs(c)}
                for c in codes
            ]
            print(f"\n指定回填: {codes}")
        else:
            # 全量：从 stock_basic 表读取
            rows = db.query_all("SELECT ts_code, bs_code FROM stock_basic")
            stocks = [{"ts_code": r[0], "bs_code": r[1]} for r in rows]

        if not stocks:
            print("  ⚠ 无股票数据，请先回填股票列表")
            db.close()
            return

        print("\n" + "=" * 60)
        print("  Step 2: 回填日K线 + 复权因子")
        print("=" * 60)

        backfill_daily(
            db, stocks,
            start_date=args.start,
            end_date=args.end,
            batch_size=args.batch_size,
            delay=args.delay,
        )

        # Step 3: 指数
        if not args.skip_indices:
            backfill_indices(db, start_date=args.start, end_date=args.end)

    # 最终统计
    stats = db.get_db_stats()
    print("\n" + "=" * 60)
    print("  回填完成！数据库统计:")
    print("=" * 60)
    for table, count in stats.items():
        if isinstance(count, int) and count >= 0:
            print(f"  {table}: {count:,} 行")
        elif table == "db_size_mb":
            print(f"  数据库大小: {count} MB")

    db.close()
    print("\n✅ 全部完成！")


# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def _safe_float(val) -> Optional[float]:
    """安全转换为 float，空值返回 None"""
    if val is None or val == "" or val == "None":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    main()
