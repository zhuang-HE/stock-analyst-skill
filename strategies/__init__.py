"""
策略配置系统 v1.0

YAML 驱动的策略定义和加载，支持热修改策略参数无需改代码。
"""

from .loader import StrategyLoader, load_strategies

__all__ = ['StrategyLoader', 'load_strategies']
