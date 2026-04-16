# -*- coding: utf-8 -*-
"""
Stock Analyst 数据适配层

将多种数据源的输出统一转换为 stock-analyst 需要的格式
支持数据源：
- finance-data-retrieval (AkShare) - 主要数据源
- 备用数据源1: Tushare (待接入)
- 备用数据源2: Baostock (待接入)
- 备用数据源3: 本地缓存 (离线使用)
"""

from .adapter import DataAdapter, get_stock_analysis_data
from .sources import DataSource, AkShareSource, TushareSource, BaostockSource, LocalCacheSource
from .fallback import FallbackManager

__all__ = [
    'DataAdapter',
    'get_stock_analysis_data',
    'DataSource',
    'AkShareSource',
    'TushareSource', 
    'BaostockSource',
    'LocalCacheSource',
    'FallbackManager'
]
