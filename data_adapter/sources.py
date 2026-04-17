# -*- coding: utf-8 -*-
""" 数据源接口定义与实现
支持的真实数据源：
1. AkShareSource - 主数据源（免费，数据全面）
2. BaostockSource - 备用1（免费，稳定，需登录）
3. SinaFinanceSource - 备用2（新浪财经，免费但不太稳定）
4. LocalCacheSource - 本地缓存（离线兜底）

注意：Tushare 需要 token，已移除。推荐使用 Baostock 作为免费备用。
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源抽象基类"""

    def __init__(self, name: str):
        self.name = name
        self.is_available = True

    @abstractmethod
    def get_quote(self, code: str) -> Optional[Dict]:
        """获取实时行情"""
        pass

    @abstractmethod
    def get_kline(self, code: str, days: int = 60) -> Optional[Dict]:
        """获取K线数据"""
        pass

    @abstractmethod
    def get_financial(self, code: str) -> Optional[Dict]:
        """获取财务数据"""
        pass

    @abstractmethod
    def get_money_flow(self, code: str) -> Optional[Dict]:
        """获取资金流向"""
        pass

    @abstractmethod
    def get_news(self, code: str, limit: int = 5) -> Optional[Dict]:
        """获取新闻"""
        pass

    def health_check(self) -> bool:
        """健康检查"""
        return self.is_available

    def _normalize_code(self, code: str) -> tuple:
        """标准化股票代码 → (market, symbol)"""
        code = str(code).strip().upper()

        if code.endswith('.SH') or code.startswith('6'):
            market = 'sh'
            symbol = code.replace('.SH', '')
        elif code.endswith('.SZ') or code.startswith(('0', '3')):
            market = 'sz'
            symbol = code.replace('.SZ', '')
        else:
            market = 'sz'
            symbol = code

        return market, symbol


class AkShareSource(DataSource):
    """AkShare 数据源（主数据源）"""

    def __init__(self):
        super().__init__("AkShare")
        try:
            import akshare as ak
            self._ak = ak
            self.is_available = True
        except ImportError:
            logger.error("akshare 未安装，AkShare 数据源不可用")
            self.is_available = False

    def get_quote(self, code: str) -> Optional[Dict]:
        try:
            market, symbol = self._normalize_code(code)
            df = self._ak.stock_zh_a_spot_em()

            if df is None or df.empty:
                return None

            row = df[df['代码'] == symbol]
            if row.empty:
                return None

            row = row.iloc[0]
            return {
                'code': code,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'change_amt': float(row.get('涨跌额', 0)),
                'volume': float(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
                'turnover': float(row.get('换手率', 0)),
                'pe': float(row.get('市盈率-动态', 0)) if '市盈率-动态' in row.index else 0,
                'pb': float(row.get('市净率', 0)) if '市净率' in row.index else 0,
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'open': float(row.get('开盘', 0)),
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"AkShare get_quote 失败: {e}")
            return None

    def get_kline(self, code: str, days: int = 60) -> Optional[Dict]:
        try:
            _, symbol = self._normalize_code(code)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')

            df = self._ak.stock_zh_a_hist(
                symbol=symbol, period='daily',
                start_date=start_date, end_date=end_date
            )

            if df is None or df.empty:
                return None

            return {
                'code': code,
                'data': df.to_dict('records'),
                'count': len(df),
                'start_date': start_date,
                'end_date': end_date,
            }
        except Exception as e:
            logger.error(f"AkShare get_kline 失败: {e}")
            return None

    def get_financial(self, code: str) -> Optional[Dict]:
        try:
            _, symbol = self._normalize_code(code)
            df = self._ak.stock_financial_abstract_ths(symbol=symbol)

            if df is None or df.empty:
                return None

            return {
                'code': code,
                'data': df.head(4).to_dict('records'),
            }
        except Exception as e:
            logger.error(f"AkShare get_financial 失败: {e}")
            return None

    def get_money_flow(self, code: str) -> Optional[Dict]:
        try:
            _, symbol = self._normalize_code(code)
            df = self._ak.stock_individual_fund_flow(stock=symbol, market='sz')

            if df is None or df.empty:
                return None

            latest = df.iloc[-1]
            return {
                'code': code,
                'main_net_inflow': float(latest.get('主力净流入-净额', 0)),
                'retail_net_inflow': float(latest.get('散户净流入-净额', 0)),
                'date': str(latest.get('日期', '')),
            }
        except Exception as e:
            logger.error(f"AkShare get_money_flow 失败: {e}")
            return None

    def get_news(self, code: str, limit: int = 5) -> Optional[Dict]:
        try:
            _, symbol = self._normalize_code(code)
            df = self._ak.stock_news_em(symbol=symbol)

            if df is None or df.empty:
                return None

            news_list = df.head(limit)[['关键证券', '新闻标题', '新闻内容', '发布日期']].to_dict('records')
            return {
                'code': code,
                'news': news_list,
                'count': len(news_list),
            }
        except Exception as e:
            logger.error(f"AkShare get_news 失败: {e}")
            return None


class BaostockSource(DataSource):
    """Baostock 数据源（免费备用，无需 token）

    优势：免费、稳定、数据质量好
    限制：无实时行情（仅日线）、需要登录/登出
    """

    def __init__(self):
        super().__init__("Baostock")
        self._bs = None
        try:
            import baostock as bs
            self._bs_module = bs
            self.is_available = True
        except ImportError:
            logger.warning("baostock 未安装，Baostock 数据源不可用 (pip install baostock)")
            self.is_available = False

    def _login(self):
        """登录 Baostock"""
        if self._bs is None:
            lg = self._bs_module.login()
            if lg.error_code != '0':
                logger.error(f"Baostock 登录失败: {lg.error_msg}")
                return False
            self._bs = self._bs_module
        return True

    def _code_for_bs(self, code: str) -> str:
        """转换为 Baostock 代码格式：sh.600519 / sz.000001"""
        market, symbol = self._normalize_code(code)
        return f"{market}.{symbol}"

    def get_quote(self, code: str) -> Optional[Dict]:
        """Baostock 无实时行情，返回最新日线作为替代"""
        try:
            if not self._login():
                return None

            bs_code = self._code_for_bs(code)
            rs = self._bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,turn",
                start_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                frequency="d",
                adjustflag="3"
            )

            rows = []
            while rs.error_code == '0' and rs.next():
                rows.append(rs.get_row_data())

            if not rows:
                return None

            latest = rows[-1]
            prev = rows[-2] if len(rows) > 1 else latest

            price = float(latest[4]) if latest[4] else 0
            prev_price = float(prev[4]) if prev[4] else 0
            change_pct = round((price - prev_price) / prev_price * 100, 2) if prev_price > 0 else 0

            return {
                'code': code,
                'price': price,
                'open': float(latest[1]) if latest[1] else 0,
                'high': float(latest[2]) if latest[2] else 0,
                'low': float(latest[3]) if latest[3] else 0,
                'change_pct': change_pct,
                'volume': float(latest[5]) if latest[5] else 0,
                'amount': float(latest[6]) if latest[6] else 0,
                'date': latest[0],
                'source': 'baostock_latest_daily',
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Baostock get_quote 失败: {e}")
            return None

    def get_kline(self, code: str, days: int = 60) -> Optional[Dict]:
        try:
            if not self._login():
                return None

            bs_code = self._code_for_bs(code)
            rs = self._bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,turn,pctChg",
                start_date=(datetime.now() - timedelta(days=days * 2)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                frequency="d",
                adjustflag="3"
            )

            rows = []
            while rs.error_code == '0' and rs.next():
                rows.append(rs.get_row_data())

            if not rows:
                return None

            # 转换为标准格式
            data = []
            for row in rows:
                data.append({
                    'date': row[0],
                    'open': float(row[1]) if row[1] else None,
                    'high': float(row[2]) if row[2] else None,
                    'low': float(row[3]) if row[3] else None,
                    'close': float(row[4]) if row[4] else None,
                    'volume': float(row[5]) if row[5] else None,
                    'amount': float(row[6]) if row[6] else None,
                    'turnover': float(row[7]) if row[7] else None,
                    'pct_chg': float(row[8]) if row[8] else None,
                })

            return {
                'code': code,
                'data': data,
                'count': len(data),
                'source': 'baostock',
            }
        except Exception as e:
            logger.error(f"Baostock get_kline 失败: {e}")
            return None

    def get_financial(self, code: str) -> Optional[Dict]:
        try:
            if not self._login():
                return None

            bs_code = self._code_for_bs(code)

            # 获取利润表
            rs = self._bs.query_profit_data(code=bs_code, year=2025, quarter=1)
            rows = []
            while rs.error_code == '0' and rs.next():
                rows.append(rs.get_row_data())

            if rows:
                latest = rows[-1]
                return {
                    'code': code,
                    'data': [{
                        'report_date': latest[0] if len(latest) > 0 else '',
                        'roe': float(latest[16]) if len(latest) > 16 and latest[16] else 0,
                        'net_profit': float(latest[18]) if len(latest) > 18 and latest[18] else 0,
                        'revenue': float(latest[4]) if len(latest) > 4 and latest[4] else 0,
                    }],
                    'source': 'baostock',
                }
            return None
        except Exception as e:
            logger.error(f"Baostock get_financial 失败: {e}")
            return None

    def get_money_flow(self, code: str) -> Optional[Dict]:
        """Baostock 不提供资金流向数据"""
        return None

    def get_news(self, code: str, limit: int = 5) -> Optional[Dict]:
        """Baostock 不提供新闻数据"""
        return None


class SinaFinanceSource(DataSource):
    """新浪财经数据源（备用2，轻量级）

    优势：速度快、无需登录
    限制：字段有限、偶尔超时
    """

    def __init__(self):
        super().__init__("SinaFinance")
        try:
            import akshare as ak
            self._ak = ak
            self.is_available = True
        except ImportError:
            self.is_available = False

    def get_quote(self, code: str) -> Optional[Dict]:
        """通过 AkShare 的新浪接口获取实时行情"""
        try:
            market, symbol = self._normalize_code(code)
            full_code = f"{market}{symbol}"

            df = self._ak.stock_bid_ask_em(symbol=full_code)
            if df is not None and not df.empty:
                return {
                    'code': code,
                    'source': 'sina',
                    'timestamp': datetime.now().isoformat(),
                    'raw_data': df.to_dict('records')[:5],
                }
            return None
        except Exception as e:
            logger.error(f"SinaFinance get_quote 失败: {e}")
            return None

    def get_kline(self, code: str, days: int = 60) -> Optional[Dict]:
        """新浪财经分钟线（仅支持近5天），不推荐用于日线"""
        try:
            market, symbol = self._normalize_code(code)
            full_code = f"{market}{symbol}"

            df = self._ak.stock_zh_a_minute(symbol=full_code, period='1', adjust='qfq')
            if df is not None and not df.empty:
                return {
                    'code': code,
                    'data': df.tail(days * 240).to_dict('records'),  # 近N个交易日
                    'count': len(df),
                    'source': 'sina',
                    'warning': '新浪数据为分钟线，非标准日线',
                }
            return None
        except Exception as e:
            logger.error(f"SinaFinance get_kline 失败: {e}")
            return None

    def get_financial(self, code: str) -> Optional[Dict]:
        """新浪财经不直接提供财报，返回 None"""
        return None

    def get_money_flow(self, code: str) -> Optional[Dict]:
        return None

    def get_news(self, code: str, limit: int = 5) -> Optional[Dict]:
        return None


class LocalCacheSource(DataSource):
    """本地缓存数据源（最后兜底）"""

    def __init__(self, cache_dir: str = './cache'):
        super().__init__("LocalCache")
        self.cache_dir = cache_dir
        import os
        os.makedirs(cache_dir, exist_ok=True)

    def get_quote(self, code: str) -> Optional[Dict]:
        return self._read_cache('quote', code)

    def get_kline(self, code: str, days: int = 60) -> Optional[Dict]:
        return self._read_cache('kline', code)

    def get_financial(self, code: str) -> Optional[Dict]:
        return self._read_cache('financial', code)

    def get_money_flow(self, code: str) -> Optional[Dict]:
        return self._read_cache('money_flow', code)

    def get_news(self, code: str, limit: int = 5) -> Optional[Dict]:
        return self._read_cache('news', code)

    def _read_cache(self, data_type: str, code: str) -> Optional[Dict]:
        import json, os, glob

        pattern = os.path.join(self.cache_dir, f"*{data_type}_{code}*.json")
        files = glob.glob(pattern)

        if not files:
            return None

        # 取最新的缓存文件
        files.sort(key=os.path.getmtime, reverse=True)
        try:
            with open(files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['meta'] = data.get('meta', {})
                data['meta']['from_local_cache'] = True
                return data
        except Exception:
            return None
