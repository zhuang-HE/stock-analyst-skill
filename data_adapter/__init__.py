# -*- coding: utf-8 -*-
""" 
Stock Analyst 数据适配层 V2

增强能力（借鉴 OpenClaw 架构）：
- 指数退避重试 + 熔断器模式
- 真实多数据源：AkShare / Baostock / 新浪财经 / 本地缓存
- 数据新鲜度分级缓存
- 降级事件追踪与报告
"""

from .adapter import DataAdapter, get_stock_analysis_data
from .sources import (
    DataSource, AkShareSource, TushareSource, BaostockSource,
    SinaFinanceSource, LocalCacheSource, LocalDBSource
)
from .fallback import (
    FallbackManagerV2, RetryConfig, CircuitBreakerConfig,
    SourceStatus, create_fallback_manager
)

__all__ = [
    # 核心适配
    'DataAdapter',
    'get_stock_analysis_data',
    # 数据源
    'DataSource',
    'AkShareSource',
    'TushareSource',
    'BaostockSource',
    'SinaFinanceSource',
    'LocalCacheSource',
    'LocalDBSource',
    # 降级管理
    'FallbackManagerV2',
    'RetryConfig',
    'CircuitBreakerConfig',
    'SourceStatus',
    'create_fallback_manager',
]
