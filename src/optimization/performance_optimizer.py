#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能優化器模組

此模組提供系統性能優化功能，包括：
- 緩存策略管理
- 並發處理優化
- 資源管理和池化
- 記憶體優化
- 網路連接優化
- 任務調度優化
"""

import asyncio
import time
import weakref
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Callable, TypeVar, Generic,
    Union, Tuple, Set, Coroutine
)
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import gc
from functools import wraps, lru_cache
import hashlib
import pickle
import json


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class CacheStrategy(Enum):
    """緩存策略枚舉"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用頻率
    FIFO = "fifo"  # 先進先出
    TTL = "ttl"  # 時間過期
    ADAPTIVE = "adaptive"  # 自適應


class OptimizationLevel(Enum):
    """優化級別枚舉"""
    CONSERVATIVE = "conservative"  # 保守優化
    BALANCED = "balanced"  # 平衡優化
    AGGRESSIVE = "aggressive"  # 激進優化


class ResourceType(Enum):
    """資源類型枚舉"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DISK = "disk"
    CONNECTION = "connection"


@dataclass
class CacheEntry(Generic[V]):
    """緩存條目"""
    value: V
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    size: int = 0
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """更新訪問時間和次數"""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheConfig:
    """緩存配置"""
    max_size: int = 1000
    strategy: CacheStrategy = CacheStrategy.LRU
    default_ttl: Optional[float] = None
    max_memory_mb: int = 100
    cleanup_interval: float = 60.0
    enable_statistics: bool = True


@dataclass
class CacheStatistics:
    """緩存統計信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    memory_usage: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class SmartCache(Generic[K, V]):
    """智能緩存實現"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[K, CacheEntry[V]] = {}
        self._access_order: OrderedDict[K, None] = OrderedDict()
        self._frequency: defaultdict[K, int] = defaultdict(int)
        self._lock = asyncio.Lock()
        self._stats = CacheStatistics()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # 啟動清理任務
        if config.cleanup_interval > 0:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def get(self, key: K, default: V = None) -> Optional[V]:
        """獲取緩存值"""
        async with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return default
            
            entry = self._cache[key]
            
            # 檢查是否過期
            if entry.is_expired():
                await self._remove_key(key)
                self._stats.misses += 1
                return default
            
            # 更新訪問信息
            entry.touch()
            self._update_access_order(key)
            self._stats.hits += 1
            
            return entry.value
    
    async def set(self, key: K, value: V, ttl: Optional[float] = None) -> bool:
        """設置緩存值"""
        async with self._lock:
            # 計算值的大小
            size = self._calculate_size(value)
            
            # 檢查記憶體限制
            if not await self._ensure_memory_limit(size):
                return False
            
            # 創建緩存條目
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl or self.config.default_ttl,
                size=size
            )
            
            # 如果鍵已存在，更新統計
            if key in self._cache:
                old_entry = self._cache[key]
                self._stats.memory_usage -= old_entry.size
            else:
                self._stats.size += 1
            
            # 設置緩存
            self._cache[key] = entry
            self._update_access_order(key)
            self._stats.memory_usage += size
            
            # 檢查大小限制
            await self._ensure_size_limit()
            
            return True
    
    async def delete(self, key: K) -> bool:
        """刪除緩存值"""
        async with self._lock:
            if key in self._cache:
                await self._remove_key(key)
                return True
            return False
    
    async def clear(self):
        """清空緩存"""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._frequency.clear()
            self._stats = CacheStatistics()
    
    def get_statistics(self) -> CacheStatistics:
        """獲取統計信息"""
        return self._stats
    
    async def _ensure_size_limit(self):
        """確保大小限制"""
        while len(self._cache) > self.config.max_size:
            await self._evict_one()
    
    async def _ensure_memory_limit(self, new_size: int) -> bool:
        """確保記憶體限制"""
        max_memory_bytes = self.config.max_memory_mb * 1024 * 1024
        
        while (self._stats.memory_usage + new_size) > max_memory_bytes:
            if not await self._evict_one():
                return False
        
        return True
    
    async def _evict_one(self) -> bool:
        """驅逐一個條目"""
        if not self._cache:
            return False
        
        key_to_evict = None
        
        if self.config.strategy == CacheStrategy.LRU:
            key_to_evict = next(iter(self._access_order))
        elif self.config.strategy == CacheStrategy.LFU:
            key_to_evict = min(self._cache.keys(), 
                             key=lambda k: self._frequency[k])
        elif self.config.strategy == CacheStrategy.FIFO:
            key_to_evict = next(iter(self._cache))
        elif self.config.strategy == CacheStrategy.TTL:
            # 找到最早過期的條目
            now = time.time()
            expired_keys = [
                k for k, entry in self._cache.items()
                if entry.ttl and (now - entry.created_at) > entry.ttl
            ]
            if expired_keys:
                key_to_evict = expired_keys[0]
            else:
                key_to_evict = next(iter(self._access_order))
        elif self.config.strategy == CacheStrategy.ADAPTIVE:
            # 自適應策略：結合LRU和LFU
            key_to_evict = self._adaptive_eviction()
        
        if key_to_evict:
            await self._remove_key(key_to_evict)
            self._stats.evictions += 1
            return True
        
        return False
    
    def _adaptive_eviction(self) -> Optional[K]:
        """自適應驅逐策略"""
        if not self._cache:
            return None
        
        # 計算每個鍵的分數（結合訪問頻率和最近性）
        now = time.time()
        scores = {}
        
        for key, entry in self._cache.items():
            # 時間衰減因子
            time_factor = 1.0 / (1.0 + (now - entry.last_accessed) / 3600)
            # 頻率因子
            freq_factor = entry.access_count / max(1, max(e.access_count for e in self._cache.values()))
            # 綜合分數
            scores[key] = time_factor * 0.6 + freq_factor * 0.4
        
        # 返回分數最低的鍵
        return min(scores.keys(), key=lambda k: scores[k])
    
    async def _remove_key(self, key: K):
        """移除鍵"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._access_order.pop(key, None)
            self._frequency.pop(key, None)
            self._stats.size -= 1
            self._stats.memory_usage -= entry.size
    
    def _update_access_order(self, key: K):
        """更新訪問順序"""
        if key in self._access_order:
            self._access_order.move_to_end(key)
        else:
            self._access_order[key] = None
        
        self._frequency[key] += 1
    
    def _calculate_size(self, value: V) -> int:
        """計算值的大小"""
        try:
            return len(pickle.dumps(value))
        except:
            # 如果無法序列化，使用估算
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, (list, tuple)):
                return sum(self._calculate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._calculate_size(k) + self._calculate_size(v) 
                          for k, v in value.items())
            else:
                return 64  # 默認估算
    
    async def _cleanup_loop(self):
        """清理循環"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"緩存清理錯誤: {e}")
    
    async def _cleanup_expired(self):
        """清理過期條目"""
        async with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                await self._remove_key(key)
    
    async def close(self):
        """關閉緩存"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


@dataclass
class ResourcePoolConfig:
    """資源池配置"""
    min_size: int = 1
    max_size: int = 10
    max_idle_time: float = 300.0  # 5分鐘
    creation_timeout: float = 30.0
    validation_interval: float = 60.0
    enable_monitoring: bool = True


class ResourcePool(Generic[T], ABC):
    """通用資源池基類"""
    
    def __init__(self, config: ResourcePoolConfig):
        self.config = config
        self._pool: List[T] = []
        self._in_use: Set[T] = set()
        self._created_at: Dict[T, float] = {}
        self._last_used: Dict[T, float] = {}
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._closed = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        if config.enable_monitoring:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    @abstractmethod
    async def _create_resource(self) -> T:
        """創建新資源"""
        pass
    
    @abstractmethod
    async def _validate_resource(self, resource: T) -> bool:
        """驗證資源是否有效"""
        pass
    
    @abstractmethod
    async def _destroy_resource(self, resource: T):
        """銷毀資源"""
        pass
    
    async def acquire(self, timeout: Optional[float] = None) -> T:
        """獲取資源"""
        if self._closed:
            raise RuntimeError("資源池已關閉")
        
        async with self._condition:
            # 等待可用資源或創建新資源
            deadline = time.time() + (timeout or self.config.creation_timeout)
            
            while True:
                # 嘗試從池中獲取資源
                if self._pool:
                    resource = self._pool.pop()
                    
                    # 驗證資源
                    if await self._validate_resource(resource):
                        self._in_use.add(resource)
                        self._last_used[resource] = time.time()
                        return resource
                    else:
                        # 資源無效，銷毀它
                        await self._destroy_resource(resource)
                        self._cleanup_resource_tracking(resource)
                
                # 檢查是否可以創建新資源
                total_resources = len(self._pool) + len(self._in_use)
                if total_resources < self.config.max_size:
                    try:
                        resource = await asyncio.wait_for(
                            self._create_resource(),
                            timeout=self.config.creation_timeout
                        )
                        
                        now = time.time()
                        self._created_at[resource] = now
                        self._last_used[resource] = now
                        self._in_use.add(resource)
                        
                        return resource
                    
                    except asyncio.TimeoutError:
                        raise TimeoutError("創建資源超時")
                
                # 等待資源釋放
                if time.time() >= deadline:
                    raise TimeoutError("獲取資源超時")
                
                try:
                    await asyncio.wait_for(
                        self._condition.wait(),
                        timeout=deadline - time.time()
                    )
                except asyncio.TimeoutError:
                    raise TimeoutError("獲取資源超時")
    
    async def release(self, resource: T):
        """釋放資源"""
        async with self._condition:
            if resource in self._in_use:
                self._in_use.remove(resource)
                
                # 驗證資源是否仍然有效
                if await self._validate_resource(resource):
                    self._pool.append(resource)
                    self._last_used[resource] = time.time()
                else:
                    # 資源無效，銷毀它
                    await self._destroy_resource(resource)
                    self._cleanup_resource_tracking(resource)
                
                # 通知等待的協程
                self._condition.notify()
    
    async def close(self):
        """關閉資源池"""
        self._closed = True
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        async with self._lock:
            # 銷毀所有資源
            all_resources = list(self._pool) + list(self._in_use)
            
            for resource in all_resources:
                try:
                    await self._destroy_resource(resource)
                except Exception as e:
                    print(f"銷毀資源時出錯: {e}")
            
            self._pool.clear()
            self._in_use.clear()
            self._created_at.clear()
            self._last_used.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取池統計信息"""
        return {
            'pool_size': len(self._pool),
            'in_use': len(self._in_use),
            'total_resources': len(self._pool) + len(self._in_use),
            'max_size': self.config.max_size,
            'min_size': self.config.min_size
        }
    
    def _cleanup_resource_tracking(self, resource: T):
        """清理資源追蹤信息"""
        self._created_at.pop(resource, None)
        self._last_used.pop(resource, None)
    
    async def _monitor_loop(self):
        """監控循環"""
        while not self._closed:
            try:
                await asyncio.sleep(self.config.validation_interval)
                await self._cleanup_idle_resources()
                await self._ensure_min_size()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"資源池監控錯誤: {e}")
    
    async def _cleanup_idle_resources(self):
        """清理空閒資源"""
        async with self._lock:
            now = time.time()
            idle_resources = []
            
            for resource in self._pool[:]:
                last_used = self._last_used.get(resource, 0)
                if (now - last_used) > self.config.max_idle_time:
                    idle_resources.append(resource)
            
            # 保持最小大小
            total_after_cleanup = len(self._pool) - len(idle_resources) + len(self._in_use)
            if total_after_cleanup < self.config.min_size:
                keep_count = self.config.min_size - len(self._in_use)
                idle_resources = idle_resources[:-keep_count] if keep_count > 0 else idle_resources
            
            # 移除空閒資源
            for resource in idle_resources:
                self._pool.remove(resource)
                await self._destroy_resource(resource)
                self._cleanup_resource_tracking(resource)
    
    async def _ensure_min_size(self):
        """確保最小大小"""
        async with self._lock:
            total_resources = len(self._pool) + len(self._in_use)
            
            while total_resources < self.config.min_size:
                try:
                    resource = await self._create_resource()
                    now = time.time()
                    self._created_at[resource] = now
                    self._last_used[resource] = now
                    self._pool.append(resource)
                    total_resources += 1
                except Exception as e:
                    print(f"創建最小資源時出錯: {e}")
                    break


class ConnectionPool(ResourcePool[Any]):
    """連接池實現"""
    
    def __init__(self, config: ResourcePoolConfig, 
                 connection_factory: Callable[[], Coroutine[Any, Any, Any]]):
        super().__init__(config)
        self._connection_factory = connection_factory
    
    async def _create_resource(self) -> Any:
        """創建新連接"""
        return await self._connection_factory()
    
    async def _validate_resource(self, resource: Any) -> bool:
        """驗證連接是否有效"""
        try:
            # 這裡應該根據具體的連接類型實現驗證邏輯
            # 例如，對於HTTP連接，可以發送一個簡單的請求
            # 對於數據庫連接，可以執行一個簡單的查詢
            return hasattr(resource, 'closed') and not resource.closed
        except:
            return False
    
    async def _destroy_resource(self, resource: Any):
        """銷毀連接"""
        try:
            if hasattr(resource, 'close'):
                if asyncio.iscoroutinefunction(resource.close):
                    await resource.close()
                else:
                    resource.close()
        except Exception as e:
            print(f"關閉連接時出錯: {e}")


@dataclass
class ConcurrencyConfig:
    """並發配置"""
    max_workers: int = 10
    max_concurrent_tasks: int = 100
    task_timeout: float = 30.0
    enable_backpressure: bool = True
    backpressure_threshold: float = 0.8
    use_process_pool: bool = False


class ConcurrencyManager:
    """並發管理器"""
    
    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        self._active_tasks: Set[asyncio.Task] = set()
        self._task_results: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        
        # 線程池和進程池
        self._thread_pool = ThreadPoolExecutor(max_workers=config.max_workers)
        self._process_pool = ProcessPoolExecutor(max_workers=config.max_workers) if config.use_process_pool else None
    
    async def submit_task(self, coro: Coroutine, task_id: Optional[str] = None) -> str:
        """提交異步任務"""
        if task_id is None:
            task_id = f"task_{int(time.time() * 1000000)}"
        
        # 檢查背壓
        if self.config.enable_backpressure:
            current_load = len(self._active_tasks) / self.config.max_concurrent_tasks
            if current_load > self.config.backpressure_threshold:
                raise RuntimeError(f"系統負載過高: {current_load:.2f}")
        
        async with self._semaphore:
            task = asyncio.create_task(self._execute_with_timeout(coro, task_id))
            
            async with self._lock:
                self._active_tasks.add(task)
            
            # 設置任務完成回調
            task.add_done_callback(lambda t: asyncio.create_task(self._task_done(t, task_id)))
        
        return task_id
    
    async def submit_cpu_bound_task(self, func: Callable, *args, **kwargs) -> str:
        """提交CPU密集型任務"""
        task_id = f"cpu_task_{int(time.time() * 1000000)}"
        
        if self.config.use_process_pool and self._process_pool:
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self._process_pool, func, *args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self._thread_pool, func, *args, **kwargs)
        
        # 包裝為協程
        async def wrapper():
            return await future
        
        return await self.submit_task(wrapper(), task_id)
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """獲取任務結果"""
        deadline = time.time() + (timeout or self.config.task_timeout)
        
        while time.time() < deadline:
            if task_id in self._task_results:
                result = self._task_results.pop(task_id)
                if isinstance(result, Exception):
                    raise result
                return result
            
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"獲取任務結果超時: {task_id}")
    
    async def wait_for_tasks(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
        """等待多個任務完成"""
        results = {}
        
        for task_id in task_ids:
            try:
                result = await self.get_task_result(task_id, timeout)
                results[task_id] = result
            except Exception as e:
                results[task_id] = e
        
        return results
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任務"""
        async with self._lock:
            for task in self._active_tasks:
                if task.get_name() == task_id:
                    task.cancel()
                    return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取並發統計"""
        return {
            'active_tasks': len(self._active_tasks),
            'max_concurrent_tasks': self.config.max_concurrent_tasks,
            'current_load': len(self._active_tasks) / self.config.max_concurrent_tasks,
            'pending_results': len(self._task_results)
        }
    
    async def _execute_with_timeout(self, coro: Coroutine, task_id: str) -> Any:
        """執行帶超時的協程"""
        try:
            return await asyncio.wait_for(coro, timeout=self.config.task_timeout)
        except Exception as e:
            self._task_results[task_id] = e
            raise
    
    async def _task_done(self, task: asyncio.Task, task_id: str):
        """任務完成回調"""
        async with self._lock:
            self._active_tasks.discard(task)
        
        try:
            result = task.result()
            self._task_results[task_id] = result
        except Exception as e:
            self._task_results[task_id] = e
    
    async def close(self):
        """關閉並發管理器"""
        # 取消所有活動任務
        async with self._lock:
            for task in self._active_tasks:
                task.cancel()
        
        # 等待任務完成
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        
        # 關閉執行器
        self._thread_pool.shutdown(wait=True)
        if self._process_pool:
            self._process_pool.shutdown(wait=True)


class PerformanceOptimizer:
    """性能優化器主類"""
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.BALANCED):
        self.optimization_level = optimization_level
        self._caches: Dict[str, SmartCache] = {}
        self._resource_pools: Dict[str, ResourcePool] = {}
        self._concurrency_manager: Optional[ConcurrencyManager] = None
        self._metrics: Dict[str, Any] = defaultdict(float)
        self._optimization_history: List[Dict[str, Any]] = []
        
        # 根據優化級別設置默認配置
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """設置默認配置"""
        if self.optimization_level == OptimizationLevel.CONSERVATIVE:
            self._default_cache_config = CacheConfig(
                max_size=500,
                strategy=CacheStrategy.LRU,
                max_memory_mb=50,
                cleanup_interval=120.0
            )
            self._default_concurrency_config = ConcurrencyConfig(
                max_workers=5,
                max_concurrent_tasks=50,
                task_timeout=60.0
            )
        elif self.optimization_level == OptimizationLevel.BALANCED:
            self._default_cache_config = CacheConfig(
                max_size=1000,
                strategy=CacheStrategy.ADAPTIVE,
                max_memory_mb=100,
                cleanup_interval=60.0
            )
            self._default_concurrency_config = ConcurrencyConfig(
                max_workers=10,
                max_concurrent_tasks=100,
                task_timeout=30.0
            )
        else:  # AGGRESSIVE
            self._default_cache_config = CacheConfig(
                max_size=2000,
                strategy=CacheStrategy.ADAPTIVE,
                max_memory_mb=200,
                cleanup_interval=30.0
            )
            self._default_concurrency_config = ConcurrencyConfig(
                max_workers=20,
                max_concurrent_tasks=200,
                task_timeout=15.0,
                use_process_pool=True
            )
    
    def create_cache(self, name: str, config: Optional[CacheConfig] = None) -> SmartCache:
        """創建緩存"""
        if config is None:
            config = self._default_cache_config
        
        cache = SmartCache(config)
        self._caches[name] = cache
        return cache
    
    def get_cache(self, name: str) -> Optional[SmartCache]:
        """獲取緩存"""
        return self._caches.get(name)
    
    def create_concurrency_manager(self, config: Optional[ConcurrencyConfig] = None) -> ConcurrencyManager:
        """創建並發管理器"""
        if config is None:
            config = self._default_concurrency_config
        
        self._concurrency_manager = ConcurrencyManager(config)
        return self._concurrency_manager
    
    def get_concurrency_manager(self) -> Optional[ConcurrencyManager]:
        """獲取並發管理器"""
        return self._concurrency_manager
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """記憶體優化"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 強制垃圾回收
        collected = gc.collect()
        
        # 清理緩存中的過期條目
        for cache in self._caches.values():
            await cache._cleanup_expired()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_freed = initial_memory - final_memory
        
        optimization_result = {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_freed_mb': memory_freed,
            'objects_collected': collected,
            'timestamp': time.time()
        }
        
        self._optimization_history.append(optimization_result)
        return optimization_result
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        metrics = {
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
            },
            'caches': {},
            'concurrency': {},
            'optimization_level': self.optimization_level.value
        }
        
        # 緩存指標
        for name, cache in self._caches.items():
            metrics['caches'][name] = {
                'statistics': cache.get_statistics().__dict__,
                'config': cache.config.__dict__
            }
        
        # 並發指標
        if self._concurrency_manager:
            metrics['concurrency'] = self._concurrency_manager.get_stats()
        
        return metrics
    
    async def auto_optimize(self) -> Dict[str, Any]:
        """自動優化"""
        optimization_results = {}
        
        # 記憶體優化
        memory_result = await self.optimize_memory()
        optimization_results['memory'] = memory_result
        
        # 緩存優化
        cache_results = {}
        for name, cache in self._caches.items():
            stats = cache.get_statistics()
            
            # 如果命中率低，調整策略
            if stats.hit_rate < 0.5 and cache.config.strategy != CacheStrategy.ADAPTIVE:
                cache.config.strategy = CacheStrategy.ADAPTIVE
                cache_results[name] = {'action': 'strategy_changed', 'new_strategy': 'adaptive'}
            
            # 如果記憶體使用過高，減少緩存大小
            if stats.memory_usage > cache.config.max_memory_mb * 1024 * 1024 * 0.9:
                cache.config.max_size = int(cache.config.max_size * 0.8)
                cache_results[name] = {'action': 'size_reduced', 'new_size': cache.config.max_size}
        
        optimization_results['caches'] = cache_results
        
        # 並發優化
        if self._concurrency_manager:
            stats = self._concurrency_manager.get_stats()
            concurrency_result = {}
            
            # 如果負載持續很高，可能需要調整配置
            if stats['current_load'] > 0.9:
                concurrency_result['high_load_warning'] = True
            
            optimization_results['concurrency'] = concurrency_result
        
        return optimization_results
    
    async def close(self):
        """關閉優化器"""
        # 關閉所有緩存
        for cache in self._caches.values():
            await cache.close()
        
        # 關閉資源池
        for pool in self._resource_pools.values():
            await pool.close()
        
        # 關閉並發管理器
        if self._concurrency_manager:
            await self._concurrency_manager.close()


# 裝飾器函數
def cached(cache_name: str = "default", ttl: Optional[float] = None, 
          key_func: Optional[Callable] = None):
    """緩存裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成緩存鍵
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默認鍵生成策略
                key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # 獲取緩存
            cache = _get_default_cache(cache_name)
            
            # 嘗試從緩存獲取
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # 執行函數
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 存入緩存
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# 全局優化器實例
_global_optimizer: Optional[PerformanceOptimizer] = None
_default_caches: Dict[str, SmartCache] = {}


def get_global_optimizer() -> PerformanceOptimizer:
    """獲取全局優化器"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = PerformanceOptimizer()
    return _global_optimizer


def _get_default_cache(name: str) -> SmartCache:
    """獲取默認緩存"""
    if name not in _default_caches:
        optimizer = get_global_optimizer()
        _default_caches[name] = optimizer.create_cache(name)
    return _default_caches[name]


if __name__ == "__main__":
    """測試性能優化器"""
    
    async def test_performance_optimizer():
        """測試性能優化器功能"""
        print("開始測試性能優化器...")
        
        # 創建優化器
        optimizer = PerformanceOptimizer(OptimizationLevel.BALANCED)
        
        # 測試緩存
        cache = optimizer.create_cache("test_cache")
        
        # 測試緩存操作
        await cache.set("key1", "value1")
        await cache.set("key2", {"data": "complex_value"})
        
        value1 = await cache.get("key1")
        value2 = await cache.get("key2")
        
        print(f"緩存測試: key1={value1}, key2={value2}")
        
        # 測試並發管理器
        concurrency_manager = optimizer.create_concurrency_manager()
        
        async def test_task(n):
            await asyncio.sleep(0.1)
            return n * 2
        
        # 提交任務
        task_ids = []
        for i in range(10):
            task_id = await concurrency_manager.submit_task(test_task(i))
            task_ids.append(task_id)
        
        # 等待結果
        results = await concurrency_manager.wait_for_tasks(task_ids)
        print(f"並發測試結果: {results}")
        
        # 獲取性能指標
        metrics = optimizer.get_performance_metrics()
        print(f"性能指標: {json.dumps(metrics, indent=2, default=str)}")
        
        # 自動優化
        optimization_result = await optimizer.auto_optimize()
        print(f"優化結果: {optimization_result}")
        
        # 清理
        await optimizer.close()
        
        print("性能優化器測試完成！")
    
    asyncio.run(test_performance_optimizer())