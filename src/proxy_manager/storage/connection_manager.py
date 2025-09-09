"""Redis連接池管理器

提供高級的Redis連接管理功能，包括：
- 連接池管理
- 自動重連機制
- 熔斷器模式
- 連接健康監控
- 錯誤處理和重試
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis
from redis.asyncio import ConnectionPool


class CircuitState(Enum):
    """熔斷器狀態枚舉"""
    CLOSED = "closed"      # 正常狀態
    OPEN = "open"          # 熔斷狀態
    HALF_OPEN = "half_open" # 半開狀態


@dataclass
class ConnectionMetrics:
    """連接指標數據
    
    Args:
        total_requests: 總請求數
        successful_requests: 成功請求數
        failed_requests: 失敗請求數
        avg_response_time: 平均響應時間
        last_error: 最後錯誤
        last_success: 最後成功時間
        circuit_state: 熔斷器狀態
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None
    circuit_state: CircuitState = CircuitState.CLOSED


class CircuitBreaker:
    """熔斷器實現
    
    當錯誤率超過閾值時自動熔斷，防止系統雪崩。
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """初始化熔斷器
        
        Args:
            failure_threshold: 失敗閾值
            recovery_timeout: 恢復超時時間(秒)
            expected_exception: 預期異常類型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        
        self.logger = logging.getLogger(__name__)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """通過熔斷器調用函數
        
        Args:
            func: 要調用的函數
            *args: 位置參數
            **kwargs: 關鍵字參數
            
        Returns:
            函數執行結果
            
        Raises:
            Exception: 熔斷器開啟時或函數執行失敗時
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("熔斷器進入半開狀態")
            else:
                raise Exception("熔斷器開啟，拒絕請求")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """檢查是否應該嘗試重置熔斷器"""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self) -> None:
        """成功時的處理"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.logger.info("熔斷器已關閉")

    def _on_failure(self) -> None:
        """失敗時的處理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(f"熔斷器已開啟，失敗次數: {self.failure_count}")


class RedisConnectionManager:
    """Redis連接管理器
    
    提供高級的Redis連接管理功能，包括連接池、
    自動重連、熔斷器和健康監控。
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 20,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        circuit_breaker_enabled: bool = True
    ):
        """初始化連接管理器
        
        Args:
            host: Redis主機
            port: Redis端口
            db: 數據庫編號
            password: 密碼
            max_connections: 最大連接數
            socket_timeout: 套接字超時
            socket_connect_timeout: 連接超時
            retry_on_timeout: 超時重試
            health_check_interval: 健康檢查間隔
            max_retries: 最大重試次數
            retry_delay: 重試延遲
            circuit_breaker_enabled: 是否啟用熔斷器
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.logger = logging.getLogger(__name__)
        
        # 連接池和客戶端
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[redis.Redis] = None
        self._is_connected = False
        
        # 熔斷器
        self.circuit_breaker = None
        if circuit_breaker_enabled:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=60,
                expected_exception=redis.RedisError
            )
        
        # 指標和監控
        self.metrics = ConnectionMetrics()
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> None:
        """建立Redis連接
        
        Raises:
            ConnectionError: 連接失敗時拋出
        """
        try:
            await self._create_connection_pool()
            await self._test_connection()
            self._is_connected = True
            
            # 啟動健康檢查
            if self.health_check_interval > 0:
                self._health_check_task = asyncio.create_task(
                    self._health_check_loop()
                )
            
            self.logger.info(f"Redis連接成功: {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Redis連接失敗: {e}")
            raise ConnectionError(f"無法連接到Redis: {e}")
    
    async def disconnect(self) -> None:
        """斷開Redis連接"""
        try:
            # 停止健康檢查
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 關閉連接
            if self._redis:
                await self._redis.close()
            if self._pool:
                await self._pool.disconnect()
            
            self._is_connected = False
            self.logger.info("Redis連接已斷開")
            
        except Exception as e:
            self.logger.error(f"斷開Redis連接時發生錯誤: {e}")
    
    async def _create_connection_pool(self) -> None:
        """創建連接池"""
        self._pool = ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=self.retry_on_timeout,
            health_check_interval=self.health_check_interval
        )
        
        self._redis = redis.Redis(connection_pool=self._pool)
    
    async def _test_connection(self) -> None:
        """測試連接"""
        if not self._redis:
            raise ConnectionError("Redis客戶端未初始化")
        
        await self._redis.ping()
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """帶重試機制的執行函數
        
        Args:
            func: 要執行的函數
            *args: 位置參數
            **kwargs: 關鍵字參數
            
        Returns:
            函數執行結果
        """
        if not self._is_connected:
            raise ConnectionError("Redis未連接")
        
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 更新指標
                self.metrics.total_requests += 1
                
                # 通過熔斷器執行
                if self.circuit_breaker:
                    result = await self.circuit_breaker.call(func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                # 更新成功指標
                self.metrics.successful_requests += 1
                self.metrics.last_success = datetime.utcnow()
                
                # 更新平均響應時間
                response_time = time.time() - start_time
                self._update_avg_response_time(response_time)
                
                return result
                
            except (redis.ConnectionError, redis.TimeoutError) as e:
                last_exception = e
                self.metrics.failed_requests += 1
                self.metrics.last_error = str(e)
                
                if attempt < self.max_retries:
                    self.logger.warning(
                        f"Redis操作失敗，第{attempt + 1}次重試: {e}"
                    )
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指數退避
                    
                    # 嘗試重新連接
                    try:
                        await self._test_connection()
                    except Exception:
                        # 重新創建連接
                        await self._recreate_connection()
                else:
                    self.logger.error(f"Redis操作失敗，已達最大重試次數: {e}")
                    
            except Exception as e:
                last_exception = e
                self.metrics.failed_requests += 1
                self.metrics.last_error = str(e)
                self.logger.error(f"Redis操作發生未預期錯誤: {e}")
                break
        
        raise last_exception or Exception("Redis操作失敗")
    
    async def _recreate_connection(self) -> None:
        """重新創建連接"""
        try:
            self.logger.info("嘗試重新創建Redis連接")
            
            # 關閉現有連接
            if self._redis:
                await self._redis.close()
            if self._pool:
                await self._pool.disconnect()
            
            # 創建新連接
            await self._create_connection_pool()
            await self._test_connection()
            
            self.logger.info("Redis連接重新創建成功")
            
        except Exception as e:
            self.logger.error(f"重新創建Redis連接失敗: {e}")
            self._is_connected = False
            raise
    
    def _update_avg_response_time(self, response_time: float) -> None:
        """更新平均響應時間"""
        if self.metrics.successful_requests == 1:
            self.metrics.avg_response_time = response_time
        else:
            # 使用指數移動平均
            alpha = 0.1
            self.metrics.avg_response_time = (
                alpha * response_time + 
                (1 - alpha) * self.metrics.avg_response_time
            )
    
    async def _health_check_loop(self) -> None:
        """健康檢查循環"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # 執行健康檢查
                start_time = time.time()
                await self._redis.ping()
                response_time = time.time() - start_time
                
                # 記錄健康狀態
                if response_time > 1.0:  # 響應時間超過1秒
                    self.logger.warning(f"Redis響應緩慢: {response_time:.2f}s")
                
                # 更新熔斷器狀態
                if self.circuit_breaker:
                    self.metrics.circuit_state = self.circuit_breaker.state
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康檢查失敗: {e}")
                # 嘗試重新連接
                try:
                    await self._recreate_connection()
                except Exception:
                    self._is_connected = False
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取連接指標
        
        Returns:
            指標數據字典
        """
        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = self.metrics.successful_requests / self.metrics.total_requests
        
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": success_rate,
            "avg_response_time": self.metrics.avg_response_time,
            "last_error": self.metrics.last_error,
            "last_success": self.metrics.last_success.isoformat() if self.metrics.last_success else None,
            "circuit_state": self.metrics.circuit_state.value,
            "is_connected": self._is_connected,
            "connection_info": {
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "max_connections": self.max_connections
            }
        }
    
    @property
    def redis(self) -> redis.Redis:
        """獲取Redis客戶端
        
        Returns:
            Redis客戶端實例
            
        Raises:
            ConnectionError: 未連接時拋出
        """
        if not self._is_connected or not self._redis:
            raise ConnectionError("Redis未連接")
        return self._redis
    
    @property
    def is_connected(self) -> bool:
        """檢查是否已連接"""
        return self._is_connected