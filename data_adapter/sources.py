# -*- coding: utf-8 -*-
"""
数据源接口定义

定义各种数据源的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_available = True
    
    @abstractmethod
    def get_quote(self, code: str) -> Optional[Dict]:
        """获取行情数据"""
        pass
    
    @abstractmethod
    def get_kline(self, code: str, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
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
    def get_news(self, code: str, limit: int = 10) -> Optional[Dict]:
        """获取新闻数据"""
        pass
    
    def check_availability(self) -> bool:
        """检查数据源是否可用"""
        return self.is_available


class AkShareSource(DataSource):
    """
    AkShare数据源（通过finance-data-retrieval）
    
    主数据源，数据全面但网络不稳定
    """
    
    def __init__(self):
        super().__init__('akshare')
        self._init_connection()
    
    def _init_connection(self):
        """初始化连接"""
        try:
            # 尝试导入finance-data-retrieval
            # 实际使用时取消注释
            # import finance_data_retrieval as fdr
            # self.fdr = fdr
            self.is_available = True
            logger.info("AkShare数据源初始化成功")
        except Exception as e:
            logger.warning(f"AkShare数据源初始化失败: {e}")
            self.is_available = False
    
    def get_quote(self, code: str) -> Optional[Dict]:
        """获取行情数据"""
        try:
            # 实际调用：
            # return self.fdr.get_real_time_quote(code)
            
            # 模拟数据
            logger.info(f"AkShare获取行情: {code}")
            return {
                'price': 31.91,
                'pct_change': 1.88,
                'volume': 2690000,
                'amount': 8.58,
                'turnover': 3.31,
                'open': 31.35,
                'high': 32.15,
                'low': 31.20,
                'prev_close': 31.32,
                'pe': 80.99,
                'pb': 5.62,
                'market_cap': 295.0
            }
        except Exception as e:
            logger.error(f"AkShare获取行情失败: {e}")
            return None
    
    def get_kline(self, code: str, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """获取K线数据"""
        try:
            # 实际调用：
            # return self.fdr.get_daily_data(code, start_date, end_date)
            
            logger.info(f"AkShare获取K线: {code}")
            # 返回模拟数据
            return self._generate_sample_klines()
        except Exception as e:
            logger.error(f"AkShare获取K线失败: {e}")
            return None
    
    def get_financial(self, code: str) -> Optional[Dict]:
        """获取财务数据"""
        try:
            logger.info(f"AkShare获取财务数据: {code}")
            return {
                'latest': {
                    'report_date': '2025-12-31',
                    'revenue': '50.5亿',
                    'revenue_yoy': '+15.2%',
                    'net_profit': '3.2亿',
                    'net_profit_yoy': '+8.5%',
                    'roe': '8.5%',
                    'gross_margin': '22%',
                    'net_margin': '6.3%',
                    'pe': '80.99',
                    'pb': '5.62'
                },
                'history': []
            }
        except Exception as e:
            logger.error(f"AkShare获取财务数据失败: {e}")
            return None
    
    def get_money_flow(self, code: str) -> Optional[Dict]:
        """获取资金流向"""
        try:
            logger.info(f"AkShare获取资金流向: {code}")
            return {
                'main_net': 5.2,
                'main_in': 12.5,
                'main_out': 7.3,
                'retail_net': -2.1,
                'north_net': 3.8
            }
        except Exception as e:
            logger.error(f"AkShare获取资金流向失败: {e}")
            return None
    
    def get_news(self, code: str, limit: int = 10) -> Optional[Dict]:
        """获取新闻数据"""
        try:
            logger.info(f"AkShare获取新闻: {code}")
            return {
                'sentiment': '中性偏正面',
                'sentiment_score': 65,
                'items': []
            }
        except Exception as e:
            logger.error(f"AkShare获取新闻失败: {e}")
            return None
    
    def _generate_sample_klines(self) -> List[Dict]:
        """生成示例K线数据"""
        import random
        from datetime import datetime, timedelta
        
        klines = []
        base_price = 30.0
        
        for i in range(100):
            change = random.uniform(-0.03, 0.03)
            close = base_price * (1 + change)
            high = close * (1 + random.uniform(0, 0.02))
            low = close * (1 - random.uniform(0, 0.02))
            open_price = base_price * (1 + random.uniform(-0.01, 0.01))
            volume = random.randint(1000000, 5000000)
            
            date = (datetime.now() - timedelta(days=100-i)).strftime('%Y-%m-%d')
            
            klines.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
            
            base_price = close
        
        return klines


class TushareSource(DataSource):
    """
    Tushare数据源
    
    备用数据源1，需要注册token
    官网：https://tushare.pro
    """
    
    def __init__(self, token: str = None):
        super().__init__('tushare')
        self.token = token
        self._init_connection()
    
    def _init_connection(self):
        """初始化连接"""
        try:
            import tushare as ts
            if self.token:
                ts.set_token(self.token)
                self.pro = ts.pro_api()
                self.is_available = True
                logger.info("Tushare数据源初始化成功")
            else:
                logger.warning("Tushare token未设置")
                self.is_available = False
        except Exception as e:
            logger.warning(f"Tushare数据源初始化失败: {e}")
            self.is_available = False
    
    def get_quote(self, code: str) -> Optional[Dict]:
        """获取行情数据"""
        if not self.is_available:
            return None
        
        try:
            # Tushare接口调用
            # df = self.pro.daily(ts_code=code)
            logger.info(f"Tushare获取行情: {code}")
            return {}  # 返回实际数据
        except Exception as e:
            logger.error(f"Tushare获取行情失败: {e}")
            return None
    
    def get_kline(self, code: str, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """获取K线数据"""
        if not self.is_available:
            return None
        
        try:
            logger.info(f"Tushare获取K线: {code}")
            return []
        except Exception as e:
            logger.error(f"Tushare获取K线失败: {e}")
            return None
    
    def get_financial(self, code: str) -> Optional[Dict]:
        """获取财务数据"""
        if not self.is_available:
            return None
        
        try:
            logger.info(f"Tushare获取财务数据: {code}")
            return {}
        except Exception as e:
            logger.error(f"Tushare获取财务数据失败: {e}")
            return None
    
    def get_money_flow(self, code: str) -> Optional[Dict]:
        """获取资金流向"""
        # Tushare资金流向数据需要额外权限
        return None
    
    def get_news(self, code: str, limit: int = 10) -> Optional[Dict]:
        """获取新闻数据"""
        return None


class BaostockSource(DataSource):
    """
    Baostock数据源
    
    备用数据源2，免费但需要登录
    官网：http://www.baostock.com
    """
    
    def __init__(self):
        super().__init__('baostock')
        self._init_connection()
    
    def _init_connection(self):
        """初始化连接"""
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code == '0':
                self.is_available = True
                logger.info("Baostock数据源初始化成功")
            else:
                logger.warning(f"Baostock登录失败: {lg.error_msg}")
                self.is_available = False
        except Exception as e:
            logger.warning(f"Baostock数据源初始化失败: {e}")
            self.is_available = False
    
    def get_quote(self, code: str) -> Optional[Dict]:
        """获取行情数据"""
        if not self.is_available:
            return None
        
        try:
            logger.info(f"Baostock获取行情: {code}")
            return {}
        except Exception as e:
            logger.error(f"Baostock获取行情失败: {e}")
            return None
    
    def get_kline(self, code: str, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """获取K线数据"""
        if not self.is_available:
            return None
        
        try:
            logger.info(f"Baostock获取K线: {code}")
            return []
        except Exception as e:
            logger.error(f"Baostock获取K线失败: {e}")
            return None
    
    def get_financial(self, code: str) -> Optional[Dict]:
        """获取财务数据"""
        return None
    
    def get_money_flow(self, code: str) -> Optional[Dict]:
        """获取资金流向"""
        return None
    
    def get_news(self, code: str, limit: int = 10) -> Optional[Dict]:
        """获取新闻数据"""
        return None


class LocalCacheSource(DataSource):
    """
    本地缓存数据源
    
    最后手段，用于离线场景
    """
    
    def __init__(self, cache_dir: str = './cache'):
        super().__init__('local_cache')
        self.cache_dir = cache_dir
        self.is_available = True
    
    def get_quote(self, code: str) -> Optional[Dict]:
        """从缓存获取行情"""
        return self._read_cache(f'quote_{code}')
    
    def get_kline(self, code: str, start_date: str = None, end_date: str = None) -> Optional[List[Dict]]:
        """从缓存获取K线"""
        return self._read_cache(f'kline_{code}')
    
    def get_financial(self, code: str) -> Optional[Dict]:
        """从缓存获取财务数据"""
        return self._read_cache(f'financial_{code}')
    
    def get_money_flow(self, code: str) -> Optional[Dict]:
        """从缓存获取资金流向"""
        return self._read_cache(f'money_flow_{code}')
    
    def get_news(self, code: str, limit: int = 10) -> Optional[Dict]:
        """从缓存获取新闻"""
        return self._read_cache(f'news_{code}')
    
    def _read_cache(self, key: str) -> Optional[Dict]:
        """读取缓存文件"""
        import os
        import json
        
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
