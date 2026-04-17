"""
data_store 包的命令行入口。

用法：
    python -m data_store backfill [--codes ...]
    python -m data_store updater [--all]
    python -m data_store tushare [--all|income|top_list|...]
    python -m data_store tech-calc [--codes ...|--all] [--force]
    python -m data_store stats
"""

import sys


def main():
    if len(sys.argv) < 2:
        print("用法: python -m data_store <backfill|updater|tushare|tech-calc|stats> [options]")
        print()
        print("命令:")
        print("  backfill   历史数据回填（Baostock）")
        print("  updater    每日增量更新（Baostock + AkShare）")
        print("  tushare    Tushare 数据同步（财报/龙虎榜/指数成分股）")
        print("  tech-calc  技术指标预计算（MA/MACD/RSI/KDJ/布林带等）")
        print("  stats      数据库统计信息")
        sys.exit(1)

    command = sys.argv[1]
    # 把剩余参数传给子命令
    sys.argv = sys.argv[:1] + sys.argv[2:]

    if command == "backfill":
        from data_store.backfill import main as backfill_main
        backfill_main()
    elif command == "updater":
        from data_store.updater import main as updater_main
        updater_main()
    elif command == "tushare":
        from data_store.tushare_sync import main as tushare_main
        tushare_main()
    elif command == "tech-calc":
        from data_store.tech_calc import main as tech_calc_main
        tech_calc_main()
    elif command == "stats":
        from data_store.database import Database
        db = Database()
        db.connect()
        if not db.is_initialized():
            print("数据库未初始化，请先运行 backfill")
            db.close()
            return
        stats = db.get_db_stats()
        print("\n📊 数据库统计:")
        print("-" * 40)
        for table, count in stats.items():
            if isinstance(count, int) and count >= 0:
                print(f"  {table}: {count:,} 行")
            elif table == "db_size_mb":
                print(f"  数据库大小: {count} MB")
        db.close()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
