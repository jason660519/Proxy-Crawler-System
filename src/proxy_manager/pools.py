"""代理池管理器模組

實現分級代理池系統：
- 熱池（Hot Pool）：高品質、快速響應的代理
- 溫池（Warm Pool）：中等品質的代理
- 冷池（Cold Pool）：低品質或未驗證的代理
- 黑名單池（Blacklist Pool）：失效或有問題的代理
"""

import asyncio
import random
import json
from typing import List, Optional, Dict, Any, Set, Iterator
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging
from pathlib import Path
from enum import Enum

from .models import ProxyNode, ProxyStatus, ProxyAnonymity, ProxyProtocol, ProxyFilter
from .validators import ProxyValidator, ValidationResult
from .config import ValidationConfig

logger = logging.getLogger(__name__)


class PoolType(Enum):
    """代理池類型"""
    HOT = "hot"          # 熱池：高品質代理
    WARM = "warm"        # 溫池：中等品質代理
    COLD = "cold"        # 冷池：低品質代理
    BLACKLIST = "blacklist"  # 黑名單：失效代理


@dataclass
class PoolConfig:
    """代理池配置"""
    # 池大小限制
    hot_pool_max_size: int = 100
    warm_pool_max_size: int = 500
    cold_pool_max_size: int = 1000
    blacklist_max_size: int = 2000
    
    # 品質閾值
    hot_pool_min_score: float = 0.8
    warm_pool_min_score: float = 0.5
    cold_pool_min_score: float = 0.2
    
    # 時間閾值
    hot_pool_max_response_time: int = 3000  # 3秒
    warm_pool_max_response_time: int = 8000  # 8秒
    
    # 重新驗證間隔
    hot_pool_revalidate_hours: int = 1
    warm_pool_revalidate_hours: int = 6
    cold_pool_revalidate_hours: int = 24
    
    # 黑名單清理
    blacklist_cleanup_days: int = 7
    
    # 自動平衡
    auto_balance_enabled: bool = True
    balance_check_interval_minutes: int = 30


@dataclass
class PoolStats:
    """代理池統計信息"""
    pool_type: PoolType
    total_count: int = 0
    active_count: int = 0
    average_score: float = 0.0
    average_response_time: float = 0.0
    last_updated: Optional[datetime] = None
    success_rate: float = 0.0
    
    # 按協議分組統計
    protocol_distribution: Dict[str, int] = field(default_factory=dict)
    # 按匿名度分組統計
    anonymity_distribution: Dict[str, int] = field(default_factory=dict)
    # 按國家分組統計
    country_distribution: Dict[str, int] = field(default_factory=dict)


class ProxyPool:
    """單個代理池"""
    
    def __init__(self, pool_type: PoolType, config: PoolConfig):
        self.pool_type = pool_type
        self.config = config
        self.proxies: Dict[str, ProxyNode] = {}  # key: proxy_id
        self.usage_queue: deque = deque()  # 使用順序隊列
        self.last_used: Dict[str, datetime] = {}  # 最後使用時間
        self._lock = asyncio.Lock()
    
    @property
    def max_size(self) -> int:
        """獲取池最大容量"""
        size_map = {
            PoolType.HOT: self.config.hot_pool_max_size,
            PoolType.WARM: self.config.warm_pool_max_size,
            PoolType.COLD: self.config.cold_pool_max_size,
            PoolType.BLACKLIST: self.config.blacklist_max_size
        }
        return size_map.get(self.pool_type, 1000)
    
    async def add_proxy(self, proxy: ProxyNode) -> bool:
        """添加代理到池中"""
        async with self._lock:
            if len(self.proxies) >= self.max_size:
                # 池已滿，移除最舊的代理
                await self._remove_oldest()
            
            self.proxies[proxy.proxy_id] = proxy
            self.usage_queue.append(proxy.proxy_id)
            logger.debug(f"✅ 代理 {proxy.url} 已添加到 {self.pool_type.value} 池")
            return True
    
    async def remove_proxy(self, proxy_id: str) -> bool:
        """從池中移除代理"""
        async with self._lock:
            if proxy_id in self.proxies:
                del self.proxies[proxy_id]
                # 從使用隊列中移除
                try:
                    self.usage_queue.remove(proxy_id)
                except ValueError:
                    pass
                # 從最後使用記錄中移除
                self.last_used.pop(proxy_id, None)
                logger.debug(f"🗑️ 代理 {proxy_id} 已從 {self.pool_type.value} 池移除")
                return True
            return False
    
    async def get_proxy(self, filter_criteria: Optional[ProxyFilter] = None) -> Optional[ProxyNode]:
        """從池中獲取代理"""
        async with self._lock:
            available_proxies = []
            
            # 篩選可用代理
            for proxy in self.proxies.values():
                if proxy.status == ProxyStatus.ACTIVE:
                    if filter_criteria is None or filter_criteria.matches(proxy):
                        available_proxies.append(proxy)
            
            if not available_proxies:
                return None
            
            # 根據池類型選擇策略
            if self.pool_type == PoolType.HOT:
                # 熱池：選擇最快的代理
                proxy = min(available_proxies, key=lambda p: p.metrics.avg_response_time or float('inf'))
            elif self.pool_type == PoolType.WARM:
                # 溫池：輪詢選擇
                proxy = self._round_robin_select(available_proxies)
            else:
                # 冷池：隨機選擇
                proxy = random.choice(available_proxies)
            
            # 更新使用記錄
            self.last_used[proxy.proxy_id] = datetime.now()
            proxy.metrics.total_requests += 1
            
            return proxy
    
    def _round_robin_select(self, proxies: List[ProxyNode]) -> ProxyNode:
        """輪詢選擇代理"""
        if not proxies:
            return None
        
        # 按最後使用時間排序，選擇最久未使用的
        proxies_with_time = []
        for proxy in proxies:
            last_time = self.last_used.get(proxy.proxy_id, datetime.min)
            proxies_with_time.append((proxy, last_time))
        
        # 排序並選擇最久未使用的
        proxies_with_time.sort(key=lambda x: x[1])
        return proxies_with_time[0][0]
    
    async def _remove_oldest(self):
        """移除最舊的代理"""
        if self.usage_queue:
            oldest_id = self.usage_queue.popleft()
            self.proxies.pop(oldest_id, None)
            self.last_used.pop(oldest_id, None)
    
    def get_stats(self) -> PoolStats:
        """獲取池統計信息"""
        total_count = len(self.proxies)
        active_proxies = [p for p in self.proxies.values() if p.status == ProxyStatus.ACTIVE]
        active_count = len(active_proxies)
        
        # 計算平均分數和響應時間
        if active_proxies:
            avg_score = sum(p.score for p in active_proxies) / active_count
            response_times = [p.metrics.avg_response_time for p in active_proxies if p.metrics.avg_response_time]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # 成功率
            total_requests = sum(p.metrics.total_requests for p in active_proxies)
            successful_requests = sum(p.metrics.successful_requests for p in active_proxies)
            success_rate = successful_requests / total_requests if total_requests > 0 else 0
        else:
            avg_score = 0
            avg_response_time = 0
            success_rate = 0
        
        # 分佈統計
        protocol_dist = defaultdict(int)
        anonymity_dist = defaultdict(int)
        country_dist = defaultdict(int)
        
        for proxy in active_proxies:
            protocol_dist[proxy.protocol.value] += 1
            anonymity_dist[proxy.anonymity.value] += 1
            if proxy.country:
                country_dist[proxy.country] += 1
        
        return PoolStats(
            pool_type=self.pool_type,
            total_count=total_count,
            active_count=active_count,
            average_score=avg_score,
            average_response_time=avg_response_time,
            last_updated=datetime.now(),
            success_rate=success_rate,
            protocol_distribution=dict(protocol_dist),
            anonymity_distribution=dict(anonymity_dist),
            country_distribution=dict(country_dist)
        )
    
    def get_proxies_for_revalidation(self) -> List[ProxyNode]:
        """獲取需要重新驗證的代理"""
        revalidate_hours_map = {
            PoolType.HOT: self.config.hot_pool_revalidate_hours,
            PoolType.WARM: self.config.warm_pool_revalidate_hours,
            PoolType.COLD: self.config.cold_pool_revalidate_hours,
            PoolType.BLACKLIST: 24 * 7  # 黑名單一週檢查一次
        }
        
        revalidate_hours = revalidate_hours_map.get(self.pool_type, 24)
        cutoff_time = datetime.now() - timedelta(hours=revalidate_hours)
        
        return [
            proxy for proxy in self.proxies.values()
            if proxy.last_checked is None or proxy.last_checked < cutoff_time
        ]


class ProxyPoolManager:
    """代理池管理器"""
    
    def __init__(self, config: Optional[PoolConfig] = None):
        self.config = config or PoolConfig()
        self.pools: Dict[PoolType, ProxyPool] = {
            PoolType.HOT: ProxyPool(PoolType.HOT, self.config),
            PoolType.WARM: ProxyPool(PoolType.WARM, self.config),
            PoolType.COLD: ProxyPool(PoolType.COLD, self.config),
            PoolType.BLACKLIST: ProxyPool(PoolType.BLACKLIST, self.config)
        }
        self.validator: Optional[ProxyValidator] = None
        self._balance_task: Optional[asyncio.Task] = None
        self._running = False
    # 租借機制: proxy_id -> (leased_at, lease_seconds)
    self._leases: Dict[str, tuple[datetime, int]] = {}
    self._default_lease_seconds = 30
    
    async def start(self):
        """啟動池管理器"""
        if not self._running:
            self.validator = ProxyValidator(ValidationConfig())
            # ProxyValidator 不需要 start 方法，直接初始化即可
            
            if self.config.auto_balance_enabled:
                self._balance_task = asyncio.create_task(self._auto_balance_loop())
            
            self._running = True
            logger.info("🚀 代理池管理器已啟動")
    
    async def stop(self):
        """停止池管理器"""
        if self._running:
            self._running = False
            
            if self._balance_task:
                self._balance_task.cancel()
                try:
                    await self._balance_task
                except asyncio.CancelledError:
                    pass
            
            if self.validator:
                await self.validator.close()
            
            logger.info("🛑 代理池管理器已停止")
    
    async def add_proxies(self, proxies: List[ProxyNode]):
        """批量添加代理到適當的池中"""
        logger.info(f"📥 添加 {len(proxies)} 個代理到池中...")
        
        for proxy in proxies:
            pool_type = self._determine_pool_type(proxy)
            await self.pools[pool_type].add_proxy(proxy)
        
        logger.info(f"✅ 代理添加完成")
    
    def _determine_pool_type(self, proxy: ProxyNode) -> PoolType:
        """根據代理品質決定放入哪個池"""
        if proxy.status != ProxyStatus.ACTIVE:
            return PoolType.BLACKLIST
        
        score = proxy.score
        response_time = proxy.metrics.avg_response_time or float('inf')
        
        # 熱池條件：高分數 + 快速響應
        if (score >= self.config.hot_pool_min_score and 
            response_time <= self.config.hot_pool_max_response_time):
            return PoolType.HOT
        
        # 溫池條件：中等分數 + 可接受響應時間
        elif (score >= self.config.warm_pool_min_score and 
              response_time <= self.config.warm_pool_max_response_time):
            return PoolType.WARM
        
        # 冷池條件：低分數但仍可用
        elif score >= self.config.cold_pool_min_score:
            return PoolType.COLD
        
        # 其他情況放入黑名單
        else:
            return PoolType.BLACKLIST
    
    async def get_proxy(self, 
                       pool_preference: List[PoolType] = None,
                       filter_criteria: Optional[ProxyFilter] = None) -> Optional[ProxyNode]:
        """獲取代理（按池優先級）"""
        if pool_preference is None:
            pool_preference = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        
        # 清理過期租借
        now = datetime.now()
        expired = [pid for pid,(ts,ttl) in self._leases.items() if (now - ts).total_seconds() > ttl]
        for pid in expired:
            self._leases.pop(pid, None)

        for pool_type in pool_preference:
            if pool_type in self.pools:
                # 嘗試取得符合條件且未租借 / 租借過期的代理
                for _ in range(5):  # 最多嘗試幾次避免全是租借中的代理
                    proxy = await self.pools[pool_type].get_proxy(filter_criteria)
                    if not proxy:
                        break
                    lease = self._leases.get(proxy.proxy_id)
                    if lease is None:
                        # 掛上租借
                        self._leases[proxy.proxy_id] = (datetime.now(), self._default_lease_seconds)
                        logger.debug(f"🎯 從 {pool_type.value} 池租借代理: {proxy.url}")
                        return proxy
                # 若該池全是租借中的代理則繼續下一個池
        
        logger.warning("⚠️ 沒有可用的代理")
        return None

    async def return_proxy(self, proxy: ProxyNode):
        """歸還租借代理，提前釋放 lease。"""
        if proxy and proxy.proxy_id in self._leases:
            self._leases.pop(proxy.proxy_id, None)
            logger.debug(f"↩️ 代理歸還: {proxy.url}")
    
    async def validate_and_rebalance(self):
        """驗證代理並重新平衡池"""
        logger.info("🔄 開始驗證和重新平衡代理池...")
        
        # 收集需要重新驗證的代理
        all_proxies_to_validate = []
        for pool in self.pools.values():
            proxies = pool.get_proxies_for_revalidation()
            all_proxies_to_validate.extend(proxies)
        
        if not all_proxies_to_validate:
            logger.info("✅ 沒有需要重新驗證的代理")
            return
        
        logger.info(f"🔍 重新驗證 {len(all_proxies_to_validate)} 個代理...")
        
        # 批量驗證
        results = await self.validator.validate_proxies(all_proxies_to_validate)
        
        # 重新分配到適當的池
        moves = defaultdict(int)
        for result in results:
            proxy = result.proxy
            current_pool = self._find_proxy_pool(proxy.proxy_id)
            new_pool_type = self._determine_pool_type(proxy)
            
            if current_pool and current_pool.pool_type != new_pool_type:
                # 移動代理到新池
                await current_pool.remove_proxy(proxy.proxy_id)
                await self.pools[new_pool_type].add_proxy(proxy)
                moves[f"{current_pool.pool_type.value}->{new_pool_type.value}"] += 1
        
        # 記錄移動統計
        if moves:
            move_summary = ", ".join([f"{k}: {v}" for k, v in moves.items()])
            logger.info(f"🔄 代理池重新平衡完成: {move_summary}")
        else:
            logger.info("✅ 代理池重新平衡完成，無需移動")
    
    def _find_proxy_pool(self, proxy_id: str) -> Optional[ProxyPool]:
        """查找代理所在的池"""
        for pool in self.pools.values():
            if proxy_id in pool.proxies:
                return pool
        return None
    
    async def _auto_balance_loop(self):
        """自動平衡循環"""
        while self._running:
            try:
                await asyncio.sleep(self.config.balance_check_interval_minutes * 60)
                if self._running:
                    await self.validate_and_rebalance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 自動平衡出錯: {e}")
                await asyncio.sleep(60)  # 出錯後等待1分鐘再試
    
    async def cleanup_blacklist(self):
        """清理黑名單中的舊代理"""
        blacklist_pool = self.pools[PoolType.BLACKLIST]
        cutoff_time = datetime.now() - timedelta(days=self.config.blacklist_cleanup_days)
        
        to_remove = []
        for proxy in blacklist_pool.proxies.values():
            if proxy.updated_at and proxy.updated_at < cutoff_time:
                to_remove.append(proxy.proxy_id)
        
        for proxy_id in to_remove:
            await blacklist_pool.remove_proxy(proxy_id)
        
        if to_remove:
            logger.info(f"🗑️ 清理黑名單：移除 {len(to_remove)} 個舊代理")
    
    def get_all_stats(self) -> Dict[str, PoolStats]:
        """獲取所有池的統計信息"""
        return {
            pool_type.value: pool.get_stats()
            for pool_type, pool in self.pools.items()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取管理器摘要"""
        stats = self.get_all_stats()
        
        total_proxies = sum(s.total_count for s in stats.values())
        total_active = sum(s.active_count for s in stats.values())
        
        return {
            'total_proxies': total_proxies,
            'total_active_proxies': total_active,
            'pool_distribution': {
                pool_type: stats[pool_type].active_count
                for pool_type in stats.keys()
            },
            'overall_success_rate': sum(s.success_rate * s.active_count for s in stats.values()) / total_active if total_active > 0 else 0,
            'config': {
                'auto_balance_enabled': self.config.auto_balance_enabled,
                'balance_interval_minutes': self.config.balance_check_interval_minutes
            },
            'last_updated': datetime.now().isoformat()
        }
    
    async def save_to_file(self, file_path: Path):
        """保存池狀態到文件"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config.__dict__,
            'pools': {}
        }
        
        for pool_type, pool in self.pools.items():
            data['pools'][pool_type.value] = {
                'proxies': [proxy.to_dict() for proxy in pool.proxies.values()],
                'stats': pool.get_stats().__dict__
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"💾 代理池狀態已保存到: {file_path}")
    
    async def load_from_file(self, file_path: Path):
        """從文件載入池狀態"""
        if not file_path.exists():
            logger.warning(f"⚠️ 文件不存在: {file_path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 載入代理
        for pool_type_str, pool_data in data.get('pools', {}).items():
            try:
                pool_type = PoolType(pool_type_str)
                pool = self.pools[pool_type]
                
                for proxy_dict in pool_data.get('proxies', []):
                    proxy = ProxyNode.from_dict(proxy_dict)
                    await pool.add_proxy(proxy)
                
            except (ValueError, KeyError) as e:
                logger.error(f"❌ 載入池 {pool_type_str} 失敗: {e}")
        
        logger.info(f"📂 代理池狀態已從文件載入: {file_path}")


# 使用示例
if __name__ == "__main__":
    async def main():
        # 創建池管理器
        config = PoolConfig(
            hot_pool_max_size=50,
            warm_pool_max_size=200,
            auto_balance_enabled=True
        )
        
        manager = ProxyPoolManager(config)
        await manager.start()
        
        try:
            # 獲取代理
            proxy = await manager.get_proxy()
            if proxy:
                print(f"獲取到代理: {proxy.url}")
            
            # 獲取統計信息
            summary = manager.get_summary()
            print(f"池摘要: {summary}")
            
        finally:
            await manager.stop()
    
    asyncio.run(main())