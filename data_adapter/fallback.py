# -*- coding: utf-8 -*-
"""
多数据源备用管理器

当主数据源失败时，自动切换到备用数据源
支持的数据源：
1. AkShare (finance-data-retrieval) - 主数据源
2. Tushare - 备用1
3. Baostock - 备用2
4. 本地缓存 - 离线使用
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FallbackManager:
    """
    数据源备用管理器
    
    职责：
    1. 管理多个数据源的优先级
    2. 主源失败时自动切换到备用源
    3. 数据融合（多源数据校验）
    4. 本地缓存管理
    """
    
    def __init__(self, cache_dir: str = './cache'):
        """
        初始化备用管理器
        
        Args:
            cache_dir: 本地缓存目录
        """
        self.cache_dir = cache_dir
        self.sources = {}
        self.priority_order = []
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
    def register_source(self, name: str, source, priority: int = 0):
        """
        注册数据源
        
        Args:
            name: 数据源名称
            source: 数据源实例
            priority: 优先级（数字越小优先级越高）
        """
        self.sources[name] = {
            'instance': source,
            'priority': priority,
            'status': 'active',  # active, failed, degraded
            'last_error': None,
            'success_count': 0,
            'fail_count': 0
        }
        
        # 按优先级排序
        self.priority_order = sorted(
            self.sources.keys(),
            key=lambda x: self.sources[x]['priority']
        )
        
        logger.info(f"注册数据源: {name}, 优先级: {priority}")
    
    def get_data(self, data_type: str, code: str, **kwargs) -> Optional[Dict]:
        """
        获取数据（带备用切换）
        
        Args:
            data_type: 数据类型 (quote, kline, financial, news, money_flow)
            code: 股票代码
            **kwargs: 额外参数
            
        Returns:
            数据字典或None
        """
        # 1. 先尝试从缓存获取
        cached_data = self._get_from_cache(data_type, code)
        if cached_data:
            logger.info(f"从缓存获取 {data_type} 数据: {code}")
            return cached_data
        
        # 2. 按优先级尝试各数据源
        for source_name in self.priority_order:
            source_info = self.sources[source_name]
            
            if source_info['status'] == 'failed':
                continue
                
            try:
                logger.info(f"尝试从 {source_name} 获取 {data_type} 数据...")
                
                # 调用数据源方法
                method = getattr(source_info['instance'], f'get_{data_type}', None)
                if method is None:
                    continue
                    
                data = method(code, **kwargs)
                
                if data:
                    # 成功获取
                    source_info['success_count'] += 1
                    source_info['status'] = 'active'
                    
                    # 缓存数据
                    self._save_to_cache(data_type, code, data)
                    
                    logger.info(f"从 {source_name} 成功获取 {data_type} 数据")
                    return data
                    
            except Exception as e:
                logger.warning(f"{source_name} 获取 {data_type} 失败: {e}")
                source_info['fail_count'] += 1
                source_info['last_error'] = str(e)
                
                # 连续失败3次标记为failed
                if source_info['fail_count'] >= 3:
                    source_info['status'] = 'failed'
                    logger.error(f"{source_name} 标记为失败状态")
        
        # 3. 所有数据源都失败
        logger.error(f"所有数据源都无法获取 {data_type} 数据: {code}")
        return None
    
    def get_data_with_fallback(self, data_type: str, code: str, 
                               primary_source: str = None, **kwargs) -> Dict:
        """
        获取数据（指定主源，失败时自动切换）
        
        Args:
            data_type: 数据类型
            code: 股票代码
            primary_source: 指定主数据源（不指定则使用优先级最高的）
            **kwargs: 额外参数
            
        Returns:
            {'data': ..., 'source': ..., 'status': ...}
        """
        sources_to_try = self.priority_order.copy()
        
        # 如果指定了主源，将其移到最前面
        if primary_source and primary_source in sources_to_try:
            sources_to_try.remove(primary_source)
            sources_to_try.insert(0, primary_source)
        
        for source_name in sources_to_try:
            source_info = self.sources[source_name]
            
            if source_info['status'] == 'failed':
                continue
            
            try:
                method = getattr(source_info['instance'], f'get_{data_type}', None)
                if method is None:
                    continue
                
                data = method(code, **kwargs)
                
                if data:
                    source_info['success_count'] += 1
                    self._save_to_cache(data_type, code, data)
                    
                    return {
                        'data': data,
                        'source': source_name,
                        'status': 'success',
                        'is_fallback': source_name != sources_to_try[0]
                    }
                    
            except Exception as e:
                logger.warning(f"{source_name} 失败: {e}")
                source_info['fail_count'] += 1
        
        # 所有源都失败，尝试缓存
        cached = self._get_from_cache(data_type, code)
        if cached:
            return {
                'data': cached,
                'source': 'cache',
                'status': 'cached',
                'is_fallback': True,
                'warning': '使用缓存数据，可能不是最新的'
            }
        
        return {
            'data': None,
            'source': None,
            'status': 'failed',
            'error': '所有数据源都不可用'
        }
    
    def _get_from_cache(self, data_type: str, code: str) -> Optional[Dict]:
        """从本地缓存获取数据"""
        cache_file = os.path.join(
            self.cache_dir, 
            f"{data_type}_{code}.json"
        )
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            # 检查缓存是否过期（默认24小时）
            mtime = os.path.getmtime(cache_file)
            if datetime.now().timestamp() - mtime > 86400:
                logger.info(f"缓存已过期: {cache_file}")
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def _save_to_cache(self, data_type: str, code: str, data: Dict):
        """保存数据到本地缓存"""
        cache_file = os.path.join(
            self.cache_dir,
            f"{data_type}_{code}.json"
        )
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"数据已缓存: {cache_file}")
            
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def get_source_status(self) -> Dict:
        """获取所有数据源状态"""
        return {
            name: {
                'status': info['status'],
                'success_count': info['success_count'],
                'fail_count': info['fail_count'],
                'last_error': info['last_error']
            }
            for name, info in self.sources.items()
        }
    
    def reset_source(self, source_name: str):
        """重置数据源状态"""
        if source_name in self.sources:
            self.sources[source_name]['status'] = 'active'
            self.sources[source_name]['fail_count'] = 0
            self.sources[source_name]['last_error'] = None
            logger.info(f"重置数据源: {source_name}")
    
    def clear_cache(self, data_type: str = None, code: str = None):
        """
        清除缓存
        
        Args:
            data_type: 指定数据类型（None则清除所有）
            code: 指定股票代码（None则清除所有）
        """
        import glob
        
        if data_type and code:
            pattern = os.path.join(self.cache_dir, f"{data_type}_{code}.json")
        elif data_type:
            pattern = os.path.join(self.cache_dir, f"{data_type}_*.json")
        else:
            pattern = os.path.join(self.cache_dir, "*.json")
        
        files = glob.glob(pattern)
        for f in files:
            try:
                os.remove(f)
                logger.info(f"删除缓存: {f}")
            except Exception as e:
                logger.warning(f"删除缓存失败 {f}: {e}")


# 便捷函数
def create_fallback_manager() -> FallbackManager:
    """
    创建配置好的备用管理器
    
    自动注册常用数据源
    """
    from .sources import AkShareSource, LocalCacheSource
    
    manager = FallbackManager()
    
    # 注册主数据源
    manager.register_source('akshare', AkShareSource(), priority=0)
    
    # 注册本地缓存（最低优先级，作为最后手段）
    manager.register_source('local_cache', LocalCacheSource(), priority=999)
    
    return manager
