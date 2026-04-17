"""
A股市场数据库 (data_store)

提供本地 SQLite 数据库基础设施，支持：
- 全A股日K线 + 复权因子存储
- 指数、北向资金、融资融券数据
- 财报、龙虎榜、指数成分股（Tushare）
- 历史数据回填 (Baostock)
- Tushare 高质量数据同步
- 每日增量更新
- 高级查询接口

数据文件位置：D:/stock-data/a_market.db

快速开始：
    # 1. 初始化并回填历史数据（首次运行）
    python -m data_store.backfill

    # 2. Tushare 数据同步（财报/龙虎榜等）
    python -m data_store.tushare_sync --all

    # 3. 每日增量更新
    python -m data_store.updater

    # 4. 在代码中查询
    from data_store import StockQueries

    q = StockQueries()
    df = q.get_daily("600519.SH", days=120)
"""

try:
    from .database import Database, get_db, close_db, get_db_path
    from .queries import StockQueries
    from .tushare_sync import get_tushare_token, get_pro_api
except ImportError:
    from database import Database, get_db, close_db, get_db_path
    from queries import StockQueries
    from tushare_sync import get_tushare_token, get_pro_api

__all__ = [
    "Database",
    "StockQueries",
    "get_db",
    "close_db",
    "get_db_path",
    "get_tushare_token",
    "get_pro_api",
]

__version__ = "1.1.0"
