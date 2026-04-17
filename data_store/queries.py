"""
A股市场数据库 — 常用查询封装

提供面向业务的高级查询接口，屏蔽 SQL 细节。
stock-analyst-skill 的其他模块通过此文件获取数据。

用法：
    from data_store.queries import StockQueries

    q = StockQueries()
    df = q.get_daily("600519.SH", days=120)
    df = q.get_index_daily("000300.SH", days=60)
    info = q.get_stock_info("600519.SH")
    df = q.get_moneyflow(days=30)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

try:
    from .database import Database
except ImportError:
    from database import Database


class StockQueries:
    """
    A股市场数据库查询封装。

    所有方法返回 pandas DataFrame，方便直接对接分析流程。
    """

    def __init__(self, data_dir: Optional[str] = None, db: Optional[Database] = None):
        """
        Args:
            data_dir: 数据目录（默认 D:/stock-data）
            db: 已有的数据库连接（优先使用）
        """
        self._db = db or Database(data_dir=data_dir)
        self._own_conn = db is None  # 是否自己创建的连接

    def _ensure_conn(self) -> Database:
        if not self._db._conn:
            self._db.connect()
        return self._db

    def close(self):
        if self._own_conn:
            self._db.close()

    def __enter__(self):
        self._ensure_conn()
        return self

    def __exit__(self, *args):
        self.close()

    # ──────────────────────────────────────
    #  日K线查询
    # ──────────────────────────────────────

    def get_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        获取股票日K线数据。

        Args:
            ts_code: 股票代码 AkShare 格式，如 600519.SH
            start_date: 起始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            days: 最近 N 个交易日（与 start_date 互斥）

        Returns:
            DataFrame，按 trade_date 升序
        """
        db = self._ensure_conn()

        if days and not start_date:
            # 计算大致的起始日期（交易日约占日历日的 70%）
            approx_start = (datetime.now() - timedelta(days=int(days / 0.7))).strftime("%Y%m%d")
            sql = """
                SELECT * FROM stock_daily
                WHERE ts_code = ? AND trade_date >= ?
                ORDER BY trade_date ASC
                LIMIT ?
            """
            return db.query_df(sql, (ts_code, approx_start, days))

        conditions = ["ts_code = ?"]
        params: list = [ts_code]

        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)

        sql = f"""
            SELECT * FROM stock_daily
            WHERE {' AND '.join(conditions)}
            ORDER BY trade_date ASC
        """
        return db.query_df(sql, tuple(params))

    def get_daily_multi(
        self,
        ts_codes: list,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """批量获取多只股票的日K线"""
        db = self._ensure_conn()
        placeholders = ", ".join(["?"] * len(ts_codes))
        conditions = [f"ts_code IN ({placeholders})"]
        params: list = list(ts_codes)

        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)

        sql = f"""
            SELECT * FROM stock_daily
            WHERE {' AND '.join(conditions)}
            ORDER BY ts_code, trade_date ASC
        """
        return db.query_df(sql, tuple(params))

    # ──────────────────────────────────────
    #  复权数据查询
    # ──────────────────────────────────────

    def get_adj_factor(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取复权因子"""
        db = self._ensure_conn()
        conditions = ["ts_code = ?"]
        params: list = [ts_code]

        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)

        sql = f"""
            SELECT * FROM adj_factor
            WHERE {' AND '.join(conditions)}
            ORDER BY trade_date ASC
        """
        return db.query_df(sql, tuple(params))

    def get_daily_adjusted(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        adjust: str = "hfq",
    ) -> pd.DataFrame:
        """
        获取复权后的日K线数据。

        Args:
            adjust: "hfq" 后复权 / "qfq" 前复权
        """
        db = self._ensure_conn()

        # 拉不复权数据 + 复权因子
        daily = self.get_daily(ts_code, start_date, end_date, days)
        if daily.empty:
            return daily

        adj = self.get_adj_factor(ts_code, daily["trade_date"].min(), daily["trade_date"].max())
        if adj.empty:
            return daily

        merged = daily.merge(adj[["trade_date", "adj_factor"]], on="trade_date", how="left")
        merged["adj_factor"] = merged["adj_factor"].fillna(1.0)

        price_cols = ["open", "high", "low", "close", "pre_close"]

        if adjust == "hfq":
            # 后复权：最新一天不变，历史价格 * 因子比
            last_factor = merged["adj_factor"].iloc[-1]
            ratio = merged["adj_factor"] / last_factor
            for col in price_cols:
                if col in merged.columns:
                    merged[col] = merged[col] * ratio
        elif adjust == "qfq":
            # 前复权：最早一天不变，后续价格 * 因子比
            first_factor = merged["adj_factor"].iloc[0]
            ratio = merged["adj_factor"] / first_factor
            for col in price_cols:
                if col in merged.columns:
                    merged[col] = merged[col] * ratio

        return merged

    # ──────────────────────────────────────
    #  指数查询
    # ──────────────────────────────────────

    def get_index_daily(
        self,
        ts_code: str = "000300.SH",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> pd.DataFrame:
        """获取指数日K线"""
        db = self._ensure_conn()

        if days and not start_date:
            approx_start = (datetime.now() - timedelta(days=int(days / 0.7))).strftime("%Y%m%d")
            sql = """
                SELECT * FROM index_daily
                WHERE ts_code = ? AND trade_date >= ?
                ORDER BY trade_date ASC
                LIMIT ?
            """
            return db.query_df(sql, (ts_code, approx_start, days))

        conditions = ["ts_code = ?"]
        params: list = [ts_code]

        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)

        sql = f"""
            SELECT * FROM index_daily
            WHERE {' AND '.join(conditions)}
            ORDER BY trade_date ASC
        """
        return db.query_df(sql, tuple(params))

    # ──────────────────────────────────────
    #  股票信息
    # ──────────────────────────────────────

    def get_stock_info(self, ts_code: str) -> Optional[dict]:
        """获取单只股票的基础信息"""
        db = self._ensure_conn()
        row = db.query_one("SELECT * FROM stock_basic WHERE ts_code = ?", (ts_code,))
        if row:
            return dict(row)
        return None

    def search_stocks(self, keyword: str) -> pd.DataFrame:
        """按名称或代码搜索股票"""
        db = self._ensure_conn()
        sql = """
            SELECT * FROM stock_basic
            WHERE name LIKE ? OR ts_code LIKE ? OR bs_code LIKE ?
            LIMIT 20
        """
        pattern = f"%{keyword}%"
        return db.query_df(sql, (pattern, pattern, pattern))

    # ──────────────────────────────────────
    #  资金流向
    # ──────────────────────────────────────

    def get_moneyflow(self, days: int = 30) -> pd.DataFrame:
        """获取北向资金数据（最近 N 天）"""
        db = self._ensure_conn()
        approx_start = (datetime.now() - timedelta(days=int(days / 0.7))).strftime("%Y%m%d")
        sql = """
            SELECT * FROM moneyflow_hsgt
            WHERE trade_date >= ?
            ORDER BY trade_date ASC
        """
        return db.query_df(sql, (approx_start,))

    def get_margin(self, ts_code: str, days: int = 30) -> pd.DataFrame:
        """获取融资融券数据"""
        db = self._ensure_conn()
        approx_start = (datetime.now() - timedelta(days=int(days / 0.7))).strftime("%Y%m%d")
        sql = """
            SELECT * FROM margin_detail
            WHERE ts_code = ? AND trade_date >= ?
            ORDER BY trade_date ASC
        """
        return db.query_df(sql, (ts_code, approx_start))

    # ──────────────────────────────────────
    #  技术指标（预计算值）
    # ──────────────────────────────────────

    def get_tech_indicators(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> pd.DataFrame:
        """获取预计算的技术指标"""
        db = self._ensure_conn()

        if days and not start_date:
            approx_start = (datetime.now() - timedelta(days=int(days / 0.7))).strftime("%Y%m%d")
            sql = """
                SELECT * FROM tech_indicators
                WHERE ts_code = ? AND trade_date >= ?
                ORDER BY trade_date ASC
            """
            return db.query_df(sql, (ts_code, approx_start))

        conditions = ["ts_code = ?"]
        params: list = [ts_code]
        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)

        sql = f"""
            SELECT * FROM tech_indicators
            WHERE {' AND '.join(conditions)}
            ORDER BY trade_date ASC
        """
        return db.query_df(sql, tuple(params))

    # ──────────────────────────────────────
    #  财报数据
    # ──────────────────────────────────────

    def get_income(self, ts_code: str, periods: int = 8) -> pd.DataFrame:
        """获取利润表（最近 N 个报告期）"""
        db = self._ensure_conn()
        sql = """
            SELECT * FROM income
            WHERE ts_code = ? AND report_type = '1'
            ORDER BY end_date DESC
            LIMIT ?
        """
        return db.query_df(sql, (ts_code, periods))

    def get_balancesheet(self, ts_code: str, periods: int = 8) -> pd.DataFrame:
        """获取资产负债表（最近 N 个报告期）"""
        db = self._ensure_conn()
        sql = """
            SELECT * FROM balancesheet
            WHERE ts_code = ? AND report_type = '1'
            ORDER BY end_date DESC
            LIMIT ?
        """
        return db.query_df(sql, (ts_code, periods))

    # ──────────────────────────────────────
    #  市场概况
    # ──────────────────────────────────────

    def get_market_overview(self, trade_date: Optional[str] = None) -> dict:
        """
        获取市场概况统计。

        Returns:
            {
                "trade_date": "...",
                "total_stocks": 5000,
                "up_count": 2000,
                "down_count": 2500,
                "flat_count": 500,
                "limit_up": 50,
                "limit_down": 10,
                "avg_turnover": 2.5,
            }
        """
        db = self._ensure_conn()

        if not trade_date:
            row = db.query_one(
                "SELECT MAX(trade_date) as max_date FROM stock_daily"
            )
            trade_date = row["max_date"] if row else None

        if not trade_date:
            return {}

        sql = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                SUM(CASE WHEN pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                SUM(CASE WHEN pct_chg = 0 THEN 1 ELSE 0 END) as flat_count,
                SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down,
                AVG(turnover) as avg_turnover
            FROM stock_daily
            WHERE trade_date = ?
        """
        row = db.query_one(sql, (trade_date,))
        if row:
            return {
                "trade_date": trade_date,
                **{k: row[k] for k in row.keys()},
            }
        return {}

    # ──────────────────────────────────────
    #  数据库状态
    # ──────────────────────────────────────

    def get_db_stats(self) -> dict:
        """获取数据库统计信息"""
        return self._ensure_conn().get_db_stats()

    def get_last_update(self, table_name: str) -> Optional[str]:
        """获取指定表的最后更新日期"""
        return self._ensure_conn().get_last_update(table_name)
