# -*- coding: utf-8 -*-
""" 多数据源备用管理器 V2
基于 OpenClaw 架构思想，增强以下能力：
1. 指数退避重试（非固定重试）
2. 熔断器模式（自动恢复）
3. 多源数据校验与融合
4. 详细的降级日志与指标

支持的数据源：
1. LocalDB - 本地SQLite数据库（最高优先级，零延迟）
2. Tushare - 高质量数据源（需 token，财报/龙虎榜最强）
3. AkShare (finance-data-retrieval) - 免费主数据源
4. Baostock - 免费备用
5. LocalCache - 离线兜底
"""

import logging
import time
import json
import os
import hashlib
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourceStatus(Enum):
    """数据源状态"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    CIRCUIT_OPEN = "circuit_open"   # 熔断器打开（拒绝请求）
    CIRCUIT_HALF = "circuit_half"  # 半开（允许探测）
    FAILED = "failed"


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3                # 最大重试次数
    base_delay: float = 1.0             # 基础延迟（秒）
    max_delay: float = 30.0             # 最大延迟（秒）
    exponential_base: float = 2.0       # 指数基数
    jitter: bool = True                 # 是否添加随机抖动


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 3          # 触发熔断的连续失败次数
    recovery_timeout: int = 60          # 熔断恢复超时（秒）
    half_open_max_calls: int = 1        # 半开状态允许的探测请求数


@dataclass
class SourceMetrics:
    """数据源指标"""
    total_calls: int = 0
    success_count: int = 0
    fail_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_success_time: Optional[float] = None
    last_fail_time: Optional[float] = None
    last_error: Optional[str] = None
    avg_response_time: float = 0.0
    total_response_time: float = 0.0
    circuit_open_count: int = 0


class RetryStrategy:
    """指数退避重试策略"""

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()

    def get_delay(self, attempt: int) -> float:
        """计算第 N 次重试的等待时间"""
        import random

        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )

        if self.config.jitter:
            delay = delay * (0.5 + random.random())

        return round(delay, 2)

    def should_retry(self, attempt: int, error: Exception = None) -> bool:
        """判断是否应该重试"""
        # 超过最大重试次数
        if attempt >= self.config.max_retries:
            return False

        # 对于某些错误不重试（如参数错误）
        non_retryable = (ValueError, TypeError, KeyError)
        if isinstance(error, non_retryable):
            return False

        return True


class CircuitBreaker:
    """熔断器"""

    def __init__(self, config: CircuitBreakerConfig = None, source_name: str = ""):
        self.config = config or CircuitBreakerConfig()
        self.source_name = source_name
        self.status = SourceStatus.ACTIVE
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    def can_execute(self) -> bool:
        """检查是否允许执行请求"""
        if self.status == SourceStatus.ACTIVE:
            return True

        if self.status == SourceStatus.CIRCUIT_OPEN:
            # 检查是否过了恢复超时
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    self.status = SourceStatus.CIRCUIT_HALF
                    self._half_open_calls = 0
                    logger.info(f"[{self.source_name}] 熔断器进入半开状态，允许探测")
                    return True
            return False

        if self.status == SourceStatus.CIRCUIT_HALF:
            # 半开状态只允许有限探测
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

        return False

    def record_success(self):
        """记录成功"""
        if self.status == SourceStatus.CIRCUIT_HALF:
            self.status = SourceStatus.ACTIVE
            logger.info(f"[{self.source_name}] 熔断器恢复，回到正常状态")

    def record_failure(self):
        """记录失败"""
        self._last_failure_time = time.time()

        if self.status == SourceStatus.CIRCUIT_HALF:
            # 半开探测失败，重新打开熔断器
            self.status = SourceStatus.CIRCUIT_OPEN
            logger.warning(f"[{self.source_name}] 半开探测失败，重新打开熔断器")
        elif self.status == SourceStatus.ACTIVE:
            # 将在 FallbackManager 中根据连续失败次数决定是否触发
            pass


class FallbackManagerV2:
    """数据源备用管理器 V2

    相比 V1 的增强：
    1. 指数退避重试（非简单计数失败）
    2. 熔断器模式（自动探测恢复）
    3. 每个数据源独立配置
    4. 降级事件日志
    5. 数据新鲜度追踪
    """

    def __init__(
        self,
        cache_dir: str = './cache',
        retry_config: RetryConfig = None,
        circuit_config: CircuitBreakerConfig = None,
    ):
        self.cache_dir = cache_dir
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()

        self.sources: Dict[str, dict] = {}
        self.priority_order: List[str] = []
        self.fallback_events: List[dict] = []  # 降级事件日志

        # 数据新鲜度配置（不同数据类型的缓存有效期）
        self.cache_ttl = {
            'quote': 300,         # 实时行情：5分钟
            'kline': 3600,        # K线数据：1小时
            'financial': 86400,   # 财务数据：1天
            'news': 1800,         # 新闻：30分钟
            'money_flow': 600,    # 资金流向：10分钟
            'default': 3600,      # 默认：1小时
        }

        os.makedirs(cache_dir, exist_ok=True)

    def register_source(
        self,
        name: str,
        source,
        priority: int = 0,
        retry_config: RetryConfig = None,
        circuit_config: CircuitBreakerConfig = None,
    ):
        """注册数据源（支持独立配置）"""
        self.sources[name] = {
            'instance': source,
            'priority': priority,
            'status': SourceStatus.ACTIVE,
            'metrics': SourceMetrics(),
            'retry_strategy': RetryStrategy(retry_config or self.retry_config),
            'circuit_breaker': CircuitBreaker(
                circuit_config or self.circuit_config,
                source_name=name
            ),
        }

        self.priority_order = sorted(
            self.sources.keys(),
            key=lambda x: self.sources[x]['priority']
        )
        logger.info(f"注册数据源: {name}, 优先级: {priority}")

    def get_data(self, data_type: str, code: str, **kwargs) -> Optional[Dict]:
        """获取数据（带降级链路）"""
        # 1. 先查缓存
        cached = self._get_from_cache(data_type, code)
        if cached is not None:
            cached['meta'] = cached.get('meta', {})
            cached['meta']['from_cache'] = True
            logger.info(f"[缓存命中] {data_type}/{code}")
            return cached

        # 2. 按优先级尝试各数据源
        result = None
        for source_name in self.priority_order:
            source_info = self.sources[source_name]

            if not source_info['circuit_breaker'].can_execute():
                logger.info(f"[熔断跳过] {source_name} 熔断器开启，跳过")
                continue

            result = self._try_source(source_name, source_info, data_type, code, **kwargs)
            if result is not None:
                break

        # 3. 所有源失败，返回过期缓存作为兜底
        if result is None:
            stale = self._get_from_cache(data_type, code, allow_stale=True)
            if stale is not None:
                stale['meta'] = stale.get('meta', {})
                stale['meta']['from_cache'] = True
                stale['meta']['stale'] = True
                stale['meta']['cache_warning'] = '所有数据源不可用，使用过期缓存'
                logger.warning(f"[过期缓存兜底] {data_type}/{code}")
                return stale

        return result

    def _try_source(
        self, source_name: str, source_info: dict,
        data_type: str, code: str, **kwargs
    ) -> Optional[Dict]:
        """尝试从单个数据源获取数据（带重试和熔断）"""
        retry = source_info['retry_strategy']
        cb = source_info['circuit_breaker']
        metrics = source_info['metrics']

        for attempt in range(retry.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = retry.get_delay(attempt)
                    logger.info(f"[重试] {source_name}/{data_type} 第{attempt}次，等待 {delay}s")
                    time.sleep(delay)

                start_time = time.time()
                method = getattr(source_info['instance'], f'get_{data_type}', None)
                if method is None:
                    logger.debug(f"[跳过] {source_name} 不支持 {data_type}")
                    break

                data = method(code, **kwargs)
                elapsed = time.time() - start_time

                if data is not None and self._validate_data(data):
                    # 成功
                    metrics.total_calls += 1
                    metrics.success_count += 1
                    metrics.consecutive_successes += 1
                    metrics.consecutive_failures = 0
                    metrics.last_success_time = time.time()
                    metrics.total_response_time += elapsed
                    metrics.avg_response_time = metrics.total_response_time / metrics.success_count

                    cb.record_success()
                    source_info['status'] = SourceStatus.ACTIVE

                    # 包装元数据
                    if isinstance(data, dict):
                        data['meta'] = data.get('meta', {})
                        data['meta']['source'] = source_name
                        data['meta']['response_time'] = round(elapsed, 3)
                        data['meta']['fetch_time'] = datetime.now().isoformat()

                    # 缓存成功数据
                    self._save_to_cache(data_type, code, data)

                    logger.info(
                        f"[成功] {source_name}/{data_type}/{code} "
                        f"耗时 {elapsed:.2f}s, 连续成功 {metrics.consecutive_successes}次"
                    )
                    return data

                # 数据为空或无效
                metrics.total_calls += 1
                logger.warning(f"[数据为空] {source_name}/{data_type}/{code}")

            except Exception as e:
                metrics.total_calls += 1
                metrics.fail_count += 1
                metrics.consecutive_failures += 1
                metrics.consecutive_successes = 0
                metrics.last_fail_time = time.time()
                metrics.last_error = str(e)

                logger.warning(f"[失败] {source_name}/{data_type}/{code}: {e}")

                # 熔断检查
                if metrics.consecutive_failures >= cb.config.failure_threshold:
                    cb.record_failure()
                    metrics.circuit_open_count += 1
                    source_info['status'] = SourceStatus.CIRCUIT_OPEN
                    logger.error(
                        f"[熔断触发] {source_name} 连续失败 {metrics.consecutive_failures}次，"
                        f"熔断器打开"
                    )

                    # 记录降级事件
                    self._log_fallback_event(
                        source_name=source_name,
                        data_type=data_type,
                        code=code,
                        reason=f"熔断触发: {e}",
                        action="跳过，切换下一个数据源"
                    )

                # 不应重试的错误类型
                if not retry.should_retry(attempt, e):
                    break

        return None

    def _validate_data(self, data: Any) -> bool:
        """基础数据校验"""
        if data is None:
            return False
        if isinstance(data, dict) and len(data) == 0:
            return False
        if isinstance(data, (list,)) and len(data) == 0:
            return False
        return True

    def _get_from_cache(self, data_type: str, code: str, allow_stale: bool = False) -> Optional[Dict]:
        """从缓存获取数据"""
        cache_key = self._cache_key(data_type, code)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            mtime = os.path.getmtime(cache_file)
            age = time.time() - mtime
            ttl = self.cache_ttl.get(data_type, self.cache_ttl['default'])

            if not allow_stale and age > ttl:
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 追加缓存元信息
            if isinstance(data, dict):
                data['meta'] = data.get('meta', {})
                data['meta']['cache_age_seconds'] = round(age)
                data['meta']['cache_ttl'] = ttl
                data['meta']['is_stale'] = age > ttl

            return data

        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None

    def _save_to_cache(self, data_type: str, code: str, data: Dict):
        """保存到缓存"""
        cache_key = self._cache_key(data_type, code)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    @staticmethod
    def _cache_key(data_type: str, code: str) -> str:
        """生成缓存文件名（避免特殊字符）"""
        raw = f"{data_type}_{code}"
        return hashlib.md5(raw.encode()).hexdigest()[:12] + "_" + raw.replace('.', '_')

    def _log_fallback_event(self, source_name: str, data_type: str,
                            code: str, reason: str, action: str):
        """记录降级事件"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'source': source_name,
            'data_type': data_type,
            'code': code,
            'reason': reason,
            'action': action,
        }
        self.fallback_events.append(event)
        # 只保留最近 100 条
        if len(self.fallback_events) > 100:
            self.fallback_events = self.fallback_events[-100:]

    def get_source_status(self) -> Dict:
        """获取所有数据源状态和指标"""
        return {
            name: {
                'status': info['status'].value,
                'total_calls': info['metrics'].total_calls,
                'success_count': info['metrics'].success_count,
                'fail_count': info['metrics'].fail_count,
                'consecutive_failures': info['metrics'].consecutive_failures,
                'avg_response_time': round(info['metrics'].avg_response_time, 3),
                'last_error': info['metrics'].last_error,
                'circuit_open_count': info['metrics'].circuit_open_count,
                'success_rate': (
                    round(info['metrics'].success_count / info['metrics'].total_calls * 100, 1)
                    if info['metrics'].total_calls > 0
                    else 0
                ),
            }
            for name, info in self.sources.items()
        }

    def get_fallback_report(self) -> Dict:
        """获取降级报告"""
        return {
            'generated_at': datetime.now().isoformat(),
            'total_events': len(self.fallback_events),
            'recent_events': self.fallback_events[-10:],
            'source_status': self.get_source_status(),
        }

    def reset_source(self, source_name: str):
        """重置数据源状态（手动恢复）"""
        if source_name in self.sources:
            info = self.sources[source_name]
            info['status'] = SourceStatus.ACTIVE
            info['metrics'].consecutive_failures = 0
            info['metrics'].last_error = None
            info['circuit_breaker'].status = SourceStatus.ACTIVE
            info['circuit_breaker']._half_open_calls = 0
            logger.info(f"手动重置数据源: {source_name}")

    def clear_cache(self, data_type: str = None, code: str = None):
        """清除缓存"""
        import glob

        if data_type and code:
            pattern = os.path.join(self.cache_dir, f"*{data_type}_{code}*.json")
        elif data_type:
            pattern = os.path.join(self.cache_dir, f"*{data_type}*.json")
        else:
            pattern = os.path.join(self.cache_dir, "*.json")

        count = 0
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                count += 1
            except Exception:
                pass
        logger.info(f"清除缓存 {count} 个文件")
        return count


def create_fallback_manager() -> FallbackManagerV2:
    """创建配置好的备用管理器（带真实数据源）

    降级链路（优先级从高到低）：
    1. LocalDB - 本地SQLite数据库（零延迟，数据最可靠）
    2. Tushare - 高质量数据源（需 token，财报/龙虎榜最强）
    3. AkShare - 免费主数据源（全面但偶尔超时）
    4. Baostock - 免费备用（稳定但字段有限）
    5. LocalCache - 离线兜底（过期缓存）
    """
    from .sources import (
        AkShareSource, TushareSource, BaostockSource,
        LocalDBSource, LocalCacheSource,
    )

    manager = FallbackManagerV2()

    # 本地数据库（最高优先级）
    local_db = LocalDBSource()
    if local_db.is_available:
        manager.register_source('local_db', local_db, priority=0)

    # Tushare（高质量数据源）
    tushare = TushareSource()
    if tushare.is_available:
        manager.register_source('tushare', tushare, priority=1)

    # AkShare（免费主数据源）
    akshare = AkShareSource()
    if akshare.is_available:
        manager.register_source('akshare', akshare, priority=2)

    # Baostock（免费备用）
    baostock = BaostockSource()
    if baostock.is_available:
        manager.register_source('baostock', baostock, priority=3)

    # 本地缓存兜底
    manager.register_source('local_cache', LocalCacheSource(), priority=999)

    return manager
