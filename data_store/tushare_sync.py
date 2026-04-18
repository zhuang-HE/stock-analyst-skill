# -*- coding: utf-8 -*-
"""
Tushare 数据源 — 回填与增量更新

Tushare 的核心价值（Baostock 不覆盖的数据）：
1. 财务报表：income / balancesheet / cashflow（高质量、标准化）
2. 指数成分股及权重：index_weight
3. 龙虎榜：top_list / top_inst
4. 股票基础信息增强：stock_basic（行业、上市日期等）

Token 配置（优先级从高到低）：
1. 环境变量 TUSHARE_TOKEN
2. .tushare_token 文件（项目根目录或用户目录）
3. tushare 已保存的 token（ts.get_token()）

用法：
    # 回填财报数据（最近4年）
    python -m data_store.tushare_sync income --years 4

    # 回填指数成分股权重
    python -m data_store.tushare_sync index_weight --index 000300.SH

    # 回填龙虎榜
    python -m data_store.tushare_sync top_list --start 20250101

    # 全量同步
    python -m data_store.tushare_sync --all

    # 增量更新（今日数据）
    python -m data_store.tushare_sync --daily-update
"""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

try:
    from .database import Database
except ImportError:
    from database import Database


logger = __name__


# ═══════════════════════════════════════════════════════════════
#  Token 管理
# ═══════════════════════════════════════════════════════════════

def get_tushare_token() -> Optional[str]:
    """按优先级获取 Tushare Token"""
    # 1. 环境变量
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if token:
        return token

    # 2. 项目根目录的 .tushare_token 文件
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for search_dir in [project_root, os.path.expanduser("~")]:
        token_file = os.path.join(search_dir, ".tushare_token")
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                token = f.read().strip()
            if token:
                return token

    # 3. tushare 已保存的 token
    try:
        import tushare as ts
        token = ts.get_token()
        if token and len(token) == 40:
            return token
    except Exception:
        pass

    return None


def get_pro_api():
    """获取 Tushare Pro API 实例"""
    import tushare as ts

    token = get_tushare_token()
    if not token:
        raise ValueError(
            "Tushare Token 未配置！请通过以下方式之一设置：\n"
            "  1. 环境变量: set TUSHARE_TOKEN=your_token\n"
            "  2. 项目根目录创建 .tushare_token 文件\n"
            "  3. tushare.set_token('your_token')\n"
            "注册地址: https://tushare.pro/register?reg=7"
        )

    ts.set_token(token)
    return ts.pro_api()


# ═══════════════════════════════════════════════════════════════
#  股票基础信息增强
# ═══════════════════════════════════════════════════════════════

def sync_stock_basic(db: Database) -> int:
    """
    使用 Tushare 增强 stock_basic 表。
    补充：行业、上市日期、沪深港通标识等。
    """
    pro = get_pro_api()
    print("[Tushare] 同步股票基础信息...")

    df = pro.stock_basic(
        exchange="",
        list_status="L",
        fields="ts_code,symbol,name,area,industry,list_date,delist_date,is_hs,market,enname,fullname"
    )
    if df is None or df.empty:
        print("  ⚠ 无数据")
        return 0

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "ts_code": r["ts_code"],
            "bs_code": Database.akshare_to_bs(r["ts_code"]),
            "name": r.get("name", ""),
            "industry": r.get("industry", ""),
            "market": r["ts_code"].split(".")[1] if "." in r["ts_code"] else "",
            "list_date": str(r.get("list_date", "")),
            "delist_date": str(r.get("delist_date", "")) if r.get("delist_date") else None,
            "is_hs": r.get("is_hs", "N"),
        })

    count = db.upsert_batch("stock_basic", rows, conflict_keys=["ts_code"])
    print(f"  ✓ 同步 {count} 条股票基础信息")
    db.log_operation(
        table_name="stock_basic",
        action="FULL_REFRESH",
        record_count=count,
        source="tushare",
    )
    return count


# ═══════════════════════════════════════════════════════════════
#  财务报表
# ═══════════════════════════════════════════════════════════════

def sync_income(
    db: Database,
    start_date: str = "20220101",
    end_date: Optional[str] = None,
    report_type: str = "1",
    ts_codes: Optional[List[str]] = None,
) -> int:
    """
    同步利润表数据。

    Args:
        start_date: 报告期起始 YYYYMMDD
        end_date: 报告期结束，默认今天
        report_type: 1=合并 2=单季
        ts_codes: 指定股票代码列表（如 ['600519.SH']），为空则按报告期拉全市场
    """
    pro = get_pro_api()
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    print(f"[Tushare] 同步利润表 {start_date} ~ {end_date}...")
    total = 0

    # 按股票代码逐只拉取（稳定，不需要高积分权限）
    if ts_codes:
        for i, ts_code in enumerate(ts_codes):
            try:
                df = pro.income(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields="ts_code,end_date,ann_date,f_ann_date,report_type,"
                           "total_revenue,revenue,oper_cost,total_profit,"
                           "n_income,n_income_attr_p,diluted_eps,"
                           "update_flag"
                )
                if df is None or df.empty:
                    print(f"  - {ts_code}: 无数据")
                    time.sleep(0.15)
                    continue

                # 过滤报告类型
                if report_type:
                    df = df[df["report_type"] == report_type]

                rows = _parse_income_rows(df)
                if rows:
                    n = db.upsert_batch("income", rows, conflict_keys=["ts_code", "end_date", "report_type"])
                    total += n
                    print(f"  ✓ {ts_code}: {n} 条")

                time.sleep(0.15)  # 每分钟不超过500次

            except Exception as e:
                print(f"  ✗ {ts_code} 失败: {e}")
                time.sleep(0.5)

    else:
        # 按报告期拉全市场（需要较高积分权限）
        periods = _get_report_periods(start_date, end_date)
        for period in periods:
            try:
                df = pro.income(
                    period=period,
                    fields="ts_code,end_date,ann_date,f_ann_date,report_type,"
                           "total_revenue,revenue,oper_cost,total_profit,"
                           "n_income,n_income_attr_p,diluted_eps,"
                           "update_flag"
                )
                if df is None or df.empty:
                    continue

                if report_type:
                    df = df[df["report_type"] == report_type]

                rows = _parse_income_rows(df)
                if rows:
                    n = db.upsert_batch("income", rows, conflict_keys=["ts_code", "end_date", "report_type"])
                    total += n
                    print(f"  ✓ {period}: {n} 条")

                time.sleep(0.15)

            except Exception as e:
                print(f"  ✗ {period} 失败: {e}")
                time.sleep(0.5)

    db.log_operation(
        table_name="income",
        action="FULL_REFRESH",
        record_count=total,
        start_date=start_date,
        end_date=end_date,
        source="tushare",
    )
    print(f"  📊 利润表总计: {total} 条")
    return total


def sync_balancesheet(
    db: Database,
    start_date: str = "20220101",
    end_date: Optional[str] = None,
    report_type: str = "1",
    ts_codes: Optional[List[str]] = None,
) -> int:
    """同步资产负债表"""
    pro = get_pro_api()
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    print(f"[Tushare] 同步资产负债表 {start_date} ~ {end_date}...")
    total = 0

    if ts_codes:
        # 按股票代码逐只拉取
        for ts_code in ts_codes:
            try:
                df = pro.balancesheet(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields="ts_code,end_date,ann_date,report_type,"
                           "total_assets,total_liab,total_hldr_eqy_exc_min_int,"
                           "monetary_cap,accounts_receiv,inventory,fix_assets"
                )
                if df is None or df.empty:
                    print(f"  - {ts_code}: 无数据")
                    time.sleep(0.15)
                    continue

                if report_type:
                    df = df[df["report_type"] == report_type]

                rows = _parse_balancesheet_rows(df)
                if rows:
                    n = db.upsert_batch("balancesheet", rows, conflict_keys=["ts_code", "end_date", "report_type"])
                    total += n
                    print(f"  ✓ {ts_code}: {n} 条")

                time.sleep(0.15)

            except Exception as e:
                print(f"  ✗ {ts_code} 失败: {e}")
                time.sleep(0.5)
    else:
        # 按报告期拉全市场
        periods = _get_report_periods(start_date, end_date)
        for period in periods:
            try:
                df = pro.balancesheet(
                    period=period,
                    fields="ts_code,end_date,ann_date,report_type,"
                           "total_assets,total_liab,total_hldr_eqy_exc_min_int,"
                           "monetary_cap,accounts_receiv,inventory,fix_assets"
                )
                if df is None or df.empty:
                    continue

                if report_type:
                    df = df[df["report_type"] == report_type]

                rows = _parse_balancesheet_rows(df)
                if rows:
                    n = db.upsert_batch("balancesheet", rows, conflict_keys=["ts_code", "end_date", "report_type"])
                    total += n
                    print(f"  ✓ {period}: {n} 条")

                time.sleep(0.15)

            except Exception as e:
                print(f"  ✗ {period} 失败: {e}")
                time.sleep(0.5)

    db.log_operation(
        table_name="balancesheet",
        action="FULL_REFRESH",
        record_count=total,
        start_date=start_date,
        end_date=end_date,
        source="tushare",
    )
    print(f"  📊 资产负债表总计: {total} 条")
    return total


# ═══════════════════════════════════════════════════════════════
#  指数成分股及权重
# ═══════════════════════════════════════════════════════════════

MAJOR_INDEX_CODES = {
    "000300.SH": "沪深300",
    "000905.SH": "中证500",
    "000852.SH": "中证1000",
    "000016.SH": "上证50",
    "000001.SH": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
}


def sync_index_weight(
    db: Database,
    index_code: Optional[str] = None,
    trade_date: Optional[str] = None,
) -> int:
    """
    同步指数成分股权重。

    Args:
        index_code: 指数代码，如 000300.SH。None=全量
        trade_date: 交易日期 YYYYMMDD。None=最新
    """
    pro = get_pro_api()

    if index_code:
        indices = {index_code: MAJOR_INDEX_CODES.get(index_code, index_code)}
    else:
        indices = MAJOR_INDEX_CODES

    total = 0

    for idx_code, idx_name in indices.items():
        print(f"[Tushare] 同步 {idx_name} ({idx_code}) 成分股...")

        try:
            if trade_date:
                df = pro.index_weight(
                    index_code=idx_code,
                    trade_date=trade_date,
                )
            else:
                # 获取最新一期
                df = pro.index_weight(index_code=idx_code, start_date="20250101")

            if df is None or df.empty:
                print(f"  ⚠ {idx_name}: 无数据")
                continue

            rows = []
            for _, r in df.iterrows():
                rows.append({
                    "index_code": r.get("index_code", idx_code),
                    "con_code": r.get("con_code", ""),
                    "con_name": r.get("con_name", ""),
                    "trade_date": str(r.get("trade_date", "")),
                    "weight": _safe_float(r.get("weight", None)),
                })

            if rows:
                n = db.upsert_batch(
                    "index_weight", rows,
                    conflict_keys=["index_code", "con_code", "trade_date"]
                )
                total += n
                print(f"  ✓ {idx_name}: {n} 条")

            time.sleep(0.5)

        except Exception as e:
            print(f"  ✗ {idx_name} 失败: {e}")
            time.sleep(1)

    db.log_operation(
        table_name="index_weight",
        action="FULL_REFRESH",
        record_count=total,
        source="tushare",
    )
    return total


# ═══════════════════════════════════════════════════════════════
#  龙虎榜
# ═══════════════════════════════════════════════════════════════

def sync_top_list(
    db: Database,
    start_date: str = "20250101",
    end_date: Optional[str] = None,
) -> int:
    """
    同步龙虎榜数据。

    需要数据库有 top_list 表（schema 中尚未定义，此函数会自动建表）。
    """
    pro = get_pro_api()
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    print(f"[Tushare] 同步龙虎榜 {start_date} ~ {end_date}...")

    # 确保表存在
    _ensure_top_list_table(db)

    # 按日期逐天拉取
    current = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    total = 0

    while current <= end:
        # 跳过周末
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        date_str = current.strftime("%Y%m%d")

        try:
            df = pro.top_list(
                trade_date=date_str,
                fields="ts_code,trade_date,name,close,pct_change,amount,"
                       "sell_amount,buy_amount,net_amount,reason,exalter"
            )
            if df is not None and not df.empty:
                rows = []
                for _, r in df.iterrows():
                    rows.append({
                        "ts_code": r.get("ts_code", ""),
                        "trade_date": str(r.get("trade_date", date_str)),
                        "name": r.get("name", ""),
                        "close": _safe_float(r.get("close", None)),
                        "pct_change": _safe_float(r.get("pct_change", None)),
                        "amount": _safe_float(r.get("amount", None)),
                        "sell_amount": _safe_float(r.get("sell_amount", None)),
                        "buy_amount": _safe_float(r.get("buy_amount", None)),
                        "net_amount": _safe_float(r.get("net_amount", None)),
                        "reason": r.get("reason", ""),
                        "exalter": r.get("exalter", ""),
                    })

                if rows:
                    n = db.upsert_batch(
                        "top_list", rows,
                        conflict_keys=["ts_code", "trade_date", "reason"]
                    )
                    total += n

            time.sleep(0.3)

        except Exception as e:
            if "每分钟" in str(e) or "limit" in str(e).lower():
                print(f"  ⚠ 频率限制，等待 60s...")
                time.sleep(60)
            else:
                print(f"  ✗ {date_str} 失败: {e}")

        # 每周打印进度
        if current.day == 1:
            print(f"  进度: {date_str}, 累计 {total} 条")

        current += timedelta(days=1)

    db.log_operation(
        table_name="top_list",
        action="FULL_REFRESH",
        record_count=total,
        start_date=start_date,
        end_date=end_date,
        source="tushare",
    )
    print(f"  📊 龙虎榜总计: {total} 条")
    return total


def _ensure_top_list_table(db: Database):
    """确保龙虎榜表存在"""
    db.conn.execute("""
        CREATE TABLE IF NOT EXISTS top_list (
            ts_code     TEXT NOT NULL,
            trade_date  TEXT NOT NULL,
            name        TEXT,
            close       REAL,
            pct_change  REAL,
            amount      REAL,
            sell_amount REAL,
            buy_amount  REAL,
            net_amount  REAL,
            reason      TEXT,
            exalter     TEXT,
            PRIMARY KEY (ts_code, trade_date, reason)
        )
    """)
    db.conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_toplist_date ON top_list(trade_date)"
    )
    db.conn.commit()


# ═══════════════════════════════════════════════════════════════
#  增量更新
# ═══════════════════════════════════════════════════════════════

def daily_update(db: Database, trade_date: Optional[str] = None) -> dict:
    """
    每日增量更新（Tushare 数据部分）。

    更新内容：
    - 龙虎榜
    - 指数成分股权重（每月初更新一次）

    财报数据建议按季度回填，不在此处每日更新。
    """
    if trade_date is None:
        trade_date = datetime.now().strftime("%Y%m%d")

    pro = get_pro_api()
    results = {}

    # 1. 龙虎榜
    try:
        count = sync_top_list(db, start_date=trade_date, end_date=trade_date)
        results["top_list"] = count
    except Exception as e:
        results["top_list"] = f"FAILED: {e}"

    # 2. 指数成分股（每月初更新）
    day = int(trade_date[6:8])
    if day <= 5:
        try:
            count = sync_index_weight(db, trade_date=trade_date)
            results["index_weight"] = count
        except Exception as e:
            results["index_weight"] = f"FAILED: {e}"
    else:
        results["index_weight"] = "SKIPPED (非月初)"

    return results


# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def _parse_income_rows(df: pd.DataFrame) -> List[dict]:
    """将 income DataFrame 转换为数据库行列表"""
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "ts_code": r["ts_code"],
            "end_date": str(r.get("end_date", "")),
            "ann_date": str(r.get("ann_date", r.get("f_ann_date", ""))),
            "report_type": str(r.get("report_type", "1")),
            "revenue": _safe_float(r.get("total_revenue", r.get("revenue", None))),
            "operate_cost": _safe_float(r.get("oper_cost", None)),
            "total_profit": _safe_float(r.get("total_profit", None)),
            "net_profit": _safe_float(r.get("n_income", None)),
            "net_profit_attr": _safe_float(r.get("n_income_attr_p", None)),
            "diluted_eps": _safe_float(r.get("diluted_eps", None)),
        })
    return rows


def _parse_balancesheet_rows(df: pd.DataFrame) -> List[dict]:
    """将 balancesheet DataFrame 转换为数据库行列表"""
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "ts_code": r["ts_code"],
            "end_date": str(r.get("end_date", "")),
            "ann_date": str(r.get("ann_date", "")),
            "report_type": str(r.get("report_type", "1")),
            "total_assets": _safe_float(r.get("total_assets", None)),
            "total_liab": _safe_float(r.get("total_liab", None)),
            "total_equity": _safe_float(r.get("total_hldr_eqy_exc_min_int", None)),
            "money_cap": _safe_float(r.get("monetary_cap", None)),
            "accounts_recv": _safe_float(r.get("accounts_receiv", None)),
            "inventory": _safe_float(r.get("inventory", None)),
            "fixed_assets": _safe_float(r.get("fix_assets", None)),
        })
    return rows


def _get_report_periods(start_date: str, end_date: str) -> List[str]:
    """
    生成财报期列表（YYYYMMDD → 季度报告期）。

    A股财报期: 0331, 0630, 0930, 1231
    """
    periods = []
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")

    year = start.year
    quarter_ends = [3, 6, 9, 12]

    while year <= end.year:
        for q_month in quarter_ends:
            # 季末日期：0331/0630/0930/1231
            if q_month in [3, 6, 9]:
                day = 30
            else:
                day = 31
            period = f"{year}{q_month:02d}{day}"
            period_dt = datetime.strptime(period, "%Y%m%d")
            if start <= period_dt <= end:
                periods.append(period)
        year += 1

    return periods


def _safe_float(val) -> Optional[float]:
    """安全转换为 float"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Tushare 数据同步")
    parser.add_argument("command", nargs="?", default=None,
                        choices=["income", "balancesheet", "stock_basic",
                                 "index_weight", "top_list"],
                        help="同步命令")
    parser.add_argument("--all", action="store_true", help="全量同步")
    parser.add_argument("--daily-update", action="store_true", help="每日增量更新")
    parser.add_argument("--start", default="20220101", help="起始日期 YYYYMMDD")
    parser.add_argument("--end", default=None, help="结束日期")
    parser.add_argument("--years", type=int, default=4, help="回填年数（默认4年）")
    parser.add_argument("--index", default=None, help="指数代码（如 000300.SH）")
    parser.add_argument("--codes", default=None, help="指定股票代码（逗号分隔，如 600519.SH,000858.SZ）")
    parser.add_argument("--data-dir", default=None, help="数据目录")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════╗")
    print("║   Tushare 数据同步                          ║")
    print("╚══════════════════════════════════════════════╝")

    # 检查 token
    try:
        get_pro_api()
        print("  ✓ Tushare Token 有效")
    except ValueError as e:
        print(f"  ✗ {e}")
        return

    db = Database(data_dir=args.data_dir)
    db.connect()

    if not db.is_initialized():
        print("  ⚠ 数据库未初始化，请先运行 backfill.py")
        db.close()
        return

    end_date = args.end or datetime.now().strftime("%Y%m%d")
    ts_codes = args.codes.split(",") if args.codes else None

    if args.daily_update:
        results = daily_update(db)
        print(f"\n每日更新结果: {results}")

    elif args.all:
        sync_stock_basic(db)
        sync_income(db, start_date=args.start, end_date=end_date, ts_codes=ts_codes)
        sync_balancesheet(db, start_date=args.start, end_date=end_date, ts_codes=ts_codes)
        sync_index_weight(db)
        sync_top_list(db, start_date=args.start, end_date=end_date)

    elif args.command == "income":
        sync_income(db, start_date=args.start, end_date=end_date, ts_codes=ts_codes)

    elif args.command == "balancesheet":
        sync_balancesheet(db, start_date=args.start, end_date=end_date, ts_codes=ts_codes)

    elif args.command == "stock_basic":
        sync_stock_basic(db)

    elif args.command == "index_weight":
        sync_index_weight(db, index_code=args.index)

    elif args.command == "top_list":
        sync_top_list(db, start_date=args.start, end_date=end_date)

    else:
        parser.print_help()

    db.close()
    print("\n✅ 同步完成！")


if __name__ == "__main__":
    main()
