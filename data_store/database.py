"""
A股市场数据库 — 核心模块

提供数据库连接、表初始化、事务管理等基础设施。
数据文件默认存储在 D 盘（可通过环境变量或参数自定义）。
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════════════════════

# 默认数据目录：D 盘
DEFAULT_DATA_DIR = Path("D:/stock-data")

# 数据库文件名
DB_FILENAME = "a_market.db"

# Schema 文件路径（与 database.py 同目录）
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db_path(data_dir: Optional[str] = None) -> Path:
    """
    获取数据库文件路径。

    优先级：
    1. 参数传入的 data_dir
    2. 环境变量 STOCK_DATA_DIR
    3. 默认 D:/stock-data
    """
    if data_dir:
        dir_path = Path(data_dir)
    else:
        env_dir = os.environ.get("STOCK_DATA_DIR")
        dir_path = Path(env_dir) if env_dir else DEFAULT_DATA_DIR

    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / DB_FILENAME


# ═══════════════════════════════════════════════════════════════
#  数据库连接管理
# ═══════════════════════════════════════════════════════════════

class Database:
    """
    A股市场数据库连接管理器。

    用法：
        db = Database()
        db.initialize()  # 首次使用时创建表

        # 查询
        df = db.query_df("SELECT * FROM stock_daily WHERE ts_code = ? LIMIT 10", ("600519.SH",))

        # 写入（自动 UPSERT 逻辑）
        db.upsert_batch("stock_daily", rows, conflict_keys=["ts_code", "trade_date"])

        # 关闭
        db.close()
    """

    def __init__(self, data_dir: Optional[str] = None, read_only: bool = False):
        self.db_path = get_db_path(data_dir)
        self._conn: Optional[sqlite3.Connection] = None
        self._read_only = read_only

    # ---------- 连接管理 ----------

    def connect(self) -> sqlite3.Connection:
        """获取数据库连接（懒加载）"""
        if self._conn is None:
            uri = f"file:{self.db_path}"
            if self._read_only:
                uri += "?mode=ro"
            else:
                uri += "?mode=rw"
            self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            # 性能优化
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = NORMAL")
            self._conn.execute("PRAGMA cache_size = -64000")  # 64MB 缓存
            self._conn.execute("PRAGMA temp_store = MEMORY")
        return self._conn

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        return self.connect()

    # ---------- 初始化 ----------

    def initialize(self, schema_path: Optional[str] = None):
        """
        初始化数据库：执行 schema.sql 创建所有表。

        Args:
            schema_path: 自定义 schema 文件路径（默认使用内置的 schema.sql）
        """
        sql_path = Path(schema_path) if schema_path else _SCHEMA_PATH
        if not sql_path.exists():
            raise FileNotFoundError(f"Schema 文件不存在: {sql_path}")

        sql = sql_path.read_text(encoding="utf-8")
        self.conn.executescript(sql)
        self.conn.commit()

        self.log_operation(
            table_name="db_meta",
            action="FULL_REFRESH",
            source="schema.sql",
        )

    def is_initialized(self) -> bool:
        """检查数据库是否已初始化"""
        try:
            result = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='stock_daily'"
            ).fetchone()
            return result is not None
        except Exception:
            return False

    # ---------- 查询 ----------

    def query_df(self, sql: str, params: tuple = (), chunksize: Optional[int] = None):
        """
        执行查询并返回 pandas DataFrame。

        Args:
            sql: SQL 查询语句
            params: 查询参数
            chunksize: 分块大小（用于大结果集）

        Returns:
            pandas DataFrame 或 Iterator[DataFrame]
        """
        import pandas as pd
        return pd.read_sql_query(sql, self.conn, params=params, chunksize=chunksize)

    def query_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """查询单条记录"""
        return self.conn.execute(sql, params).fetchone()

    def query_all(self, sql: str, params: tuple = ()) -> list:
        """查询所有记录"""
        return self.conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()):
        """执行单条 SQL"""
        return self.conn.execute(sql, params)

    # ---------- 批量写入 ----------

    def upsert_batch(
        self,
        table: str,
        rows: list,
        conflict_keys: list,
        columns: Optional[list] = None,
        batch_size: int = 5000,
    ) -> int:
        """
        批量 UPSERT（INSERT OR REPLACE）。

        Args:
            table: 表名
            rows: 数据行列表（list of dict 或 list of tuple）
            conflict_keys: 冲突检测的主键列
            columns: 列名列表（rows 是 tuple 时必须提供）
            batch_size: 每批写入行数

        Returns:
            总写入行数
        """
        if not rows:
            return 0

        # 确定列名
        if columns is None:
            if isinstance(rows[0], dict):
                columns = list(rows[0].keys())
            else:
                raise ValueError("rows 是 tuple 时必须提供 columns 参数")

        # 构建 UPSERT 语句
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        conflict_str = ", ".join(conflict_keys)
        update_str = ", ".join(
            f"{c}=excluded.{c}" for c in columns if c not in conflict_keys
        )

        sql = f"""
            INSERT INTO {table} ({col_str})
            VALUES ({placeholders})
            ON CONFLICT({conflict_str}) DO UPDATE SET {update_str}
        """

        total = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            if isinstance(batch[0], dict):
                values = [tuple(row.get(c) for c in columns) for row in batch]
            else:
                values = batch
            self.conn.executemany(sql, values)
            total += len(batch)

        self.conn.commit()
        return total

    # ---------- 数据日志 ----------

    def log_operation(
        self,
        table_name: str,
        action: str,
        record_count: int = 0,
        start_date: str = "",
        end_date: str = "",
        source: str = "",
        duration_ms: int = 0,
        status: str = "success",
        error_msg: str = "",
    ):
        """记录数据操作日志"""
        self.conn.execute(
            """INSERT INTO data_log
               (table_name, action, record_count, start_date, end_date,
                source, duration_ms, status, error_msg)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (table_name, action, record_count, start_date, end_date,
             source, duration_ms, status, error_msg),
        )
        self.conn.commit()

    def get_last_update(self, table_name: str) -> Optional[str]:
        """获取指定表的最后更新日期"""
        row = self.conn.execute(
            """SELECT end_date, created_at FROM data_log
               WHERE table_name = ? AND status = 'success'
               ORDER BY created_at DESC LIMIT 1""",
            (table_name,),
        ).fetchone()
        return row["end_date"] if row else None

    def get_db_stats(self) -> dict:
        """获取数据库统计信息"""
        stats = {}
        tables = [
            "stock_basic", "stock_daily", "adj_factor", "index_daily",
            "index_weight", "moneyflow_hsgt", "margin_detail",
            "income", "balancesheet", "tech_indicators",
        ]
        for t in tables:
            try:
                count = self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                stats[t] = count
            except Exception:
                stats[t] = -1

        # 数据库文件大小
        if self.db_path.exists():
            stats["db_size_mb"] = round(self.db_path.stat().st_size / 1024 / 1024, 2)
        else:
            stats["db_size_mb"] = 0

        return stats

    # ---------- 股票代码转换 ----------

    @staticmethod
    def bs_to_akshare(bs_code: str) -> str:
        """Baostock 格式转 AkShare 格式: sh.600519 → 600519.SH"""
        if "." in bs_code:
            parts = bs_code.split(".")
            return f"{parts[1]}.{parts[0].upper()}"
        return bs_code

    @staticmethod
    def akshare_to_bs(ak_code: str) -> str:
        """AkShare 格式转 Baostock 格式: 600519.SH → sh.600519"""
        if "." in ak_code:
            parts = ak_code.split(".")
            return f"{parts[1].lower()}.{parts[0]}"
        return ak_code


# ═══════════════════════════════════════════════════════════════
#  便捷函数
# ═══════════════════════════════════════════════════════════════

_default_db: Optional[Database] = None


def get_db(data_dir: Optional[str] = None) -> Database:
    """获取全局默认数据库连接（单例）"""
    global _default_db
    if _default_db is None:
        _default_db = Database(data_dir=data_dir)
        _default_db.connect()
    return _default_db


def close_db():
    """关闭全局数据库连接"""
    global _default_db
    if _default_db:
        _default_db.close()
        _default_db = None
