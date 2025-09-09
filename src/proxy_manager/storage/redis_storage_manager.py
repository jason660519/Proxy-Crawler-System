"""Redis存儲管理器

提供代理數據的Redis存儲功能，包括：
- 代理數據的持久化存儲
- 驗證結果的緩存管理
- 系統狀態的實時更新
- 性能指標的數據收集
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from .connection_manager import RedisConnectionManager


@dataclass
class StorageConfig:
    """Redis存儲配置類
    
    Args:
        host: Redis主機地址
        port: Redis端口
        db: 數據庫編號
        password: 密碼
        max_connections: 最大連接數
        socket_timeout: 套接字超時時間
        socket_connect_timeout: 連接超時時間
        retry_on_timeout: 超時重試
        health_check_interval: 健康檢查間隔
    """
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class ProxyData:
    """代理數據模型
    
    Args:
        proxy_id: 代理唯一標識
        host: 代理主機
        port: 代理端口
        protocol: 代理協議
        username: 用戶名
        password: 密碼
        country: 國家
        region: 地區
        city: 城市
        anonymity_level: 匿名度等級
        speed: 速度(ms)
        success_rate: 成功率
        last_checked: 最後檢查時間
        status: 狀態
        created_at: 創建時間
        updated_at: 更新時間
    """
    proxy_id: str
    host: str
    port: int
    protocol: str
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    anonymity_level: Optional[str] = None
    speed: Optional[float] = None
    success_rate: Optional[float] = None
    last_checked: Optional[datetime] = None
    status: str = "unknown"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化後處理"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ValidationData:
    """驗證數據模型
    
    Args:
        validation_id: 驗證唯一標識
        proxy_id: 代理標識
        test_type: 測試類型
        result: 測試結果
        response_time: 響應時間
        error_message: 錯誤信息
        test_url: 測試URL
        timestamp: 時間戳
        metadata: 元數據
    """
    validation_id: str
    proxy_id: str
    test_type: str
    result: bool
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    test_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化後處理"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class RedisStorageManager:
    """Redis存儲管理器
    
    提供代理數據的Redis存儲功能，包括連接池管理、
    數據序列化/反序列化、錯誤處理和重試機制。
    """

    def __init__(self, config: StorageConfig, connection_manager: Optional[RedisConnectionManager] = None):
        """初始化Redis存儲管理器
        
        Args:
            config: 存儲配置
            connection_manager: 可選的連接管理器
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化連接管理器
        if connection_manager:
            self.connection_manager = connection_manager
        else:
            self.connection_manager = RedisConnectionManager(
                host=config.host,
                port=config.port,
                db=config.db,
                password=config.password,
                max_connections=config.max_connections,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                retry_on_timeout=config.retry_on_timeout,
                health_check_interval=30,
                max_retries=3,
                retry_delay=1.0,
                circuit_breaker_enabled=True
            )
        
        # Redis鍵前綴
        self.PROXY_PREFIX = "proxy:"
        self.VALIDATION_PREFIX = "validation:"
        self.STATS_PREFIX = "stats:"
        self.QUEUE_PREFIX = "queue:"
        self.LOCK_PREFIX = "lock:"
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.disconnect()
        
    async def connect(self) -> None:
        """建立Redis連接
        
        Raises:
            ConnectionError: 連接失敗時拋出
        """
        await self.connection_manager.connect()
        self.logger.info(f"Redis存儲管理器連接成功")
    
    async def disconnect(self) -> None:
        """斷開Redis連接"""
        await self.connection_manager.disconnect()
        self.logger.info("Redis存儲管理器連接已斷開")
    
    def _ensure_connected(self) -> None:
        """確保Redis已連接
        
        Raises:
            ConnectionError: 未連接時拋出
        """
        if not self.connection_manager.is_connected:
            raise ConnectionError("Redis未連接，請先調用connect()方法")
    
    def _serialize_data(self, data: Union[ProxyData, ValidationData, Dict]) -> str:
        """序列化數據為JSON字符串
        
        Args:
            data: 要序列化的數據
            
        Returns:
            JSON字符串
        """
        if isinstance(data, (ProxyData, ValidationData)):
            # 轉換dataclass為字典
            data_dict = asdict(data)
            # 處理datetime對象
            for key, value in data_dict.items():
                if isinstance(value, datetime):
                    data_dict[key] = value.isoformat()
            return json.dumps(data_dict, ensure_ascii=False)
        elif isinstance(data, dict):
            # 處理字典中的datetime對象
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    processed_data[key] = value.isoformat()
                else:
                    processed_data[key] = value
            return json.dumps(processed_data, ensure_ascii=False)
        else:
            return json.dumps(data, ensure_ascii=False)
    
    def _deserialize_data(self, data_str: str, data_type: type = dict) -> Union[Dict, ProxyData, ValidationData]:
        """反序列化JSON字符串為數據對象
        
        Args:
            data_str: JSON字符串
            data_type: 目標數據類型
            
        Returns:
            反序列化後的數據對象
        """
        try:
            data_dict = json.loads(data_str)
            
            if data_type == ProxyData:
                # 處理datetime字段
                for field in ['last_checked', 'created_at', 'updated_at']:
                    if field in data_dict and data_dict[field]:
                        data_dict[field] = datetime.fromisoformat(data_dict[field])
                return ProxyData(**data_dict)
            elif data_type == ValidationData:
                # 處理datetime字段
                if 'timestamp' in data_dict and data_dict['timestamp']:
                    data_dict['timestamp'] = datetime.fromisoformat(data_dict['timestamp'])
                return ValidationData(**data_dict)
            else:
                return data_dict
                
        except Exception as e:
            self.logger.error(f"數據反序列化失敗: {e}")
            raise ValueError(f"無法反序列化數據: {e}")
    
    async def save_proxy(self, proxy_data: ProxyData) -> bool:
        """保存代理數據
        
        Args:
            proxy_data: 代理數據對象
            
        Returns:
            保存是否成功
        """
        self._ensure_connected()
        
        try:
            # 更新時間戳
            proxy_data.updated_at = datetime.utcnow()
            
            # 序列化數據
            serialized_data = self._serialize_data(proxy_data)
            
            # 保存到Redis
            key = f"{self.PROXY_PREFIX}{proxy_data.proxy_id}"
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.set, key, serialized_data
            )
            
            # 添加到代理列表
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.sadd, f"{self.PROXY_PREFIX}list", proxy_data.proxy_id
            )
            
            # 按狀態分類
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.sadd, f"{self.PROXY_PREFIX}status:{proxy_data.status}", proxy_data.proxy_id
            )
            
            self.logger.debug(f"代理數據已保存: {proxy_data.proxy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存代理數據失敗: {e}")
            return False
    
    async def get_proxy(self, proxy_id: str) -> Optional[ProxyData]:
        """獲取代理數據
        
        Args:
            proxy_id: 代理ID
            
        Returns:
            代理數據對象，不存在時返回None
        """
        self._ensure_connected()
        
        try:
            key = f"{self.PROXY_PREFIX}{proxy_id}"
            data_str = await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.get, key
            )
            
            if data_str:
                return self._deserialize_data(data_str.decode('utf-8'), ProxyData)
            return None
            
        except Exception as e:
            self.logger.error(f"獲取代理數據失敗: {e}")
            return None
    
    async def delete_proxy(self, proxy_id: str) -> bool:
        """刪除代理數據
        
        Args:
            proxy_id: 代理ID
            
        Returns:
            刪除是否成功
        """
        self._ensure_connected()
        
        try:
            # 獲取代理數據以確定狀態
            proxy_data = await self.get_proxy(proxy_id)
            
            # 刪除主數據
            key = f"{self.PROXY_PREFIX}{proxy_id}"
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.delete, key
            )
            
            # 從列表中移除
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.srem, f"{self.PROXY_PREFIX}list", proxy_id
            )
            
            # 從狀態分類中移除
            if proxy_data:
                await self.connection_manager.execute_with_retry(
                    self.connection_manager.redis.srem, f"{self.PROXY_PREFIX}status:{proxy_data.status}", proxy_id
                )
            
            self.logger.debug(f"代理數據已刪除: {proxy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"刪除代理數據失敗: {e}")
            return False
    
    async def get_proxies_by_status(self, status: str, limit: int = 100) -> List[ProxyData]:
        """根據狀態獲取代理列表
        
        Args:
            status: 代理狀態
            limit: 返回數量限制
            
        Returns:
            代理數據列表
        """
        self._ensure_connected()
        
        try:
            # 獲取指定狀態的代理ID列表
            proxy_ids = await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.srandmember, f"{self.PROXY_PREFIX}status:{status}", limit
            )
            
            if not proxy_ids:
                return []
            
            # 批量獲取代理數據
            proxies = []
            for proxy_id in proxy_ids:
                if isinstance(proxy_id, bytes):
                    proxy_id = proxy_id.decode('utf-8')
                proxy_data = await self.get_proxy(proxy_id)
                if proxy_data:
                    proxies.append(proxy_data)
            
            return proxies
            
        except Exception as e:
            self.logger.error(f"獲取代理列表失敗: {e}")
            return []
    
    async def update_proxy(self, proxy_data: ProxyData) -> bool:
        """更新代理數據
        
        Args:
            proxy_data: 代理數據
            
        Returns:
            更新是否成功
        """
        self._ensure_connected()
        
        try:
            # 更新時間戳
            proxy_data.updated_at = datetime.utcnow()
            
            # 獲取舊數據以更新狀態分類
            old_data = await self.get_proxy(proxy_data.proxy_id)
            
            # 序列化數據
            serialized_data = self._serialize_data(proxy_data)
            
            # 更新主數據
            key = f"{self.PROXY_PREFIX}{proxy_data.proxy_id}"
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.set, key, serialized_data
            )
            
            # 更新狀態分類
            if old_data and old_data.status != proxy_data.status:
                # 從舊狀態分類中移除
                await self.connection_manager.execute_with_retry(
                    self.connection_manager.redis.srem, f"{self.PROXY_PREFIX}status:{old_data.status}", proxy_data.proxy_id
                )
                # 添加到新狀態分類
                await self.connection_manager.execute_with_retry(
                    self.connection_manager.redis.sadd, f"{self.PROXY_PREFIX}status:{proxy_data.status}", proxy_data.proxy_id
                )
            
            self.logger.debug(f"代理數據已更新: {proxy_data.proxy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新代理數據失敗: {e}")
            return False
    
    async def batch_update_proxy_status(self, proxy_ids: List[str], status: str) -> int:
        """批量更新代理狀態
        
        Args:
            proxy_ids: 代理ID列表
            status: 新狀態
            
        Returns:
            成功更新的數量
        """
        self._ensure_connected()
        
        updated_count = 0
        
        try:
            for proxy_id in proxy_ids:
                # 獲取現有數據
                proxy_data = await self.get_proxy(proxy_id)
                if proxy_data:
                    # 更新狀態
                    proxy_data.status = status
                    proxy_data.updated_at = datetime.utcnow()
                    
                    # 保存更新
                    if await self.update_proxy(proxy_data):
                        updated_count += 1
            
            self.logger.info(f"批量更新代理狀態完成: {updated_count}/{len(proxy_ids)}")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"批量更新代理狀態失敗: {e}")
            return updated_count
    
    async def cleanup_expired_data(self, days: int = 7) -> Dict[str, int]:
        """清理過期數據
        
        Args:
            days: 保留天數
            
        Returns:
            清理統計信息
        """
        self._ensure_connected()
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            cleanup_stats = {
                "deleted_proxies": 0,
                "deleted_validations": 0,
                "deleted_stats": 0
            }
            
            # 清理過期的代理數據
            proxy_ids = await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.smembers, f"{self.PROXY_PREFIX}list"
            )
            
            for proxy_id in proxy_ids:
                if isinstance(proxy_id, bytes):
                    proxy_id = proxy_id.decode('utf-8')
                
                proxy_data = await self.get_proxy(proxy_id)
                if proxy_data and proxy_data.updated_at and proxy_data.updated_at < cutoff_time:
                    if await self.delete_proxy(proxy_id):
                        cleanup_stats["deleted_proxies"] += 1
            
            # 清理過期的驗證記錄和統計數據
            # 使用SCAN命令遍歷所有相關鍵
            cursor = 0
            while True:
                cursor, keys = await self.connection_manager.execute_with_retry(
                    self.connection_manager.redis.scan, cursor, match=f"{self.VALIDATION_PREFIX}*", count=100
                )
                
                for key in keys:
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    
                    # 檢查鍵的TTL，如果已過期則計數
                    ttl = await self.connection_manager.execute_with_retry(
                        self.connection_manager.redis.ttl, key
                    )
                    if ttl == -2:  # 鍵不存在（已過期）
                        cleanup_stats["deleted_validations"] += 1
                
                if cursor == 0:
                    break
            
            # 統計過期的統計數據
            cursor = 0
            while True:
                cursor, keys = await self.connection_manager.execute_with_retry(
                    self.connection_manager.redis.scan, cursor, match=f"{self.STATS_PREFIX}*", count=100
                )
                
                for key in keys:
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    
                    ttl = await self.connection_manager.execute_with_retry(
                        self.connection_manager.redis.ttl, key
                    )
                    if ttl == -2:  # 鍵不存在（已過期）
                        cleanup_stats["deleted_stats"] += 1
                
                if cursor == 0:
                    break
            
            self.logger.info(f"數據清理完成: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"數據清理失敗: {e}")
            return {"error": str(e)}
    
    async def save_validation_result(self, validation_data: ValidationData) -> bool:
        """保存驗證結果
        
        Args:
            validation_data: 驗證數據對象
            
        Returns:
            保存是否成功
        """
        self._ensure_connected()
        
        try:
            # 序列化數據
            serialized_data = self._serialize_data(validation_data)
            
            # 保存驗證結果
            key = f"{self.VALIDATION_PREFIX}{validation_data.validation_id}"
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.set, key, serialized_data
            )
            
            # 設置過期時間（7天）
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.expire, key, 7 * 24 * 3600
            )
            
            # 添加到代理的驗證歷史
            history_key = f"{self.VALIDATION_PREFIX}history:{validation_data.proxy_id}"
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.lpush, history_key, validation_data.validation_id
            )
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.ltrim, history_key, 0, 99  # 保留最近100條記錄
            )
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.expire, history_key, 7 * 24 * 3600
            )
            
            self.logger.debug(f"驗證結果已保存: {validation_data.validation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存驗證結果失敗: {e}")
            return False
    
    async def get_validation_history(self, proxy_id: str, limit: int = 10) -> List[ValidationData]:
        """獲取代理的驗證歷史
        
        Args:
            proxy_id: 代理ID
            limit: 返回數量限制
            
        Returns:
            驗證數據列表
        """
        self._ensure_connected()
        
        try:
            # 獲取驗證ID列表
            history_key = f"{self.VALIDATION_PREFIX}history:{proxy_id}"
            validation_ids = await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.lrange, history_key, 0, limit - 1
            )
            
            if not validation_ids:
                return []
            
            # 批量獲取驗證數據
            validations = []
            for validation_id in validation_ids:
                if isinstance(validation_id, bytes):
                    validation_id = validation_id.decode('utf-8')
                
                key = f"{self.VALIDATION_PREFIX}{validation_id}"
                data_str = await self.connection_manager.execute_with_retry(
                    self.connection_manager.redis.get, key
                )
                
                if data_str:
                    validation_data = self._deserialize_data(data_str.decode('utf-8'), ValidationData)
                    validations.append(validation_data)
            
            return validations
            
        except Exception as e:
            self.logger.error(f"獲取驗證歷史失敗: {e}")
            return []
    
    async def update_proxy_stats(self, proxy_id: str, stats: Dict[str, Any]) -> bool:
        """更新代理統計信息
        
        Args:
            proxy_id: 代理ID
            stats: 統計數據
            
        Returns:
            更新是否成功
        """
        self._ensure_connected()
        
        try:
            # 序列化統計數據
            serialized_stats = self._serialize_data(stats)
            
            # 保存統計數據
            key = f"{self.STATS_PREFIX}{proxy_id}"
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.set, key, serialized_stats
            )
            
            # 設置過期時間（24小時）
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.expire, key, 24 * 3600
            )
            
            self.logger.debug(f"代理統計已更新: {proxy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新代理統計失敗: {e}")
            return False
    
    async def get_proxy_stats(self, proxy_id: str) -> Optional[Dict[str, Any]]:
        """獲取代理統計信息
        
        Args:
            proxy_id: 代理ID
            
        Returns:
            統計數據字典，不存在時返回None
        """
        self._ensure_connected()
        
        try:
            key = f"{self.STATS_PREFIX}{proxy_id}"
            data_str = await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.get, key
            )
            
            if data_str:
                return self._deserialize_data(data_str.decode('utf-8'))
            return None
            
        except Exception as e:
            self.logger.error(f"獲取代理統計失敗: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查
        
        Returns:
            健康狀態信息
        """
        try:
            # 獲取連接管理器指標
            connection_metrics = self.connection_manager.get_metrics()
            
            # 執行Redis ping測試
            start_time = datetime.utcnow()
            await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.ping
            )
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # 獲取Redis信息
            info = await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.info
            )
            
            # 統計代理數量
            total_proxies = await self.connection_manager.execute_with_retry(
                self.connection_manager.redis.scard, f"{self.PROXY_PREFIX}list"
            )
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_proxies": total_proxies,
                "connection_metrics": connection_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_metrics": self.connection_manager.get_metrics(),
                "timestamp": datetime.utcnow().isoformat()
            }