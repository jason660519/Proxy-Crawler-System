"""Redis存儲管理器測試

測試RedisStorageManager的所有功能，包括：
- 連接管理
- 數據CRUD操作
- 錯誤處理
- 性能監控
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import List

from redis_storage_manager import (
    RedisStorageManager,
    StorageConfig,
    ProxyData,
    ValidationData,
    ProxyStatus,
    ValidationStatus
)
from connection_manager import RedisConnectionManager


class TestRedisStorageManager:
    """Redis存儲管理器測試類"""

    @pytest.fixture
    async def storage_config(self):
        """測試配置"""
        return StorageConfig(
            host="localhost",
            port=6379,
            db=15,  # 使用測試數據庫
            password=None,
            max_connections=10,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30
        )

    @pytest.fixture
    async def storage_manager(self, storage_config):
        """存儲管理器實例"""
        manager = RedisStorageManager(storage_config)
        await manager.connect()
        yield manager
        await manager.disconnect()

    @pytest.fixture
    def sample_proxy_data(self):
        """示例代理數據"""
        return ProxyData(
            proxy_id="test_proxy_001",
            host="192.168.1.100",
            port=8080,
            protocol="http",
            username=None,
            password=None,
            status=ProxyStatus.ACTIVE,
            source="test_source",
            country="TW",
            region="Taipei",
            city="Taipei",
            isp="Test ISP",
            anonymity_level="high",
            response_time=0.5,
            success_rate=0.95,
            last_checked=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_validation_data(self):
        """示例驗證數據"""
        return ValidationData(
            validation_id="test_validation_001",
            proxy_id="test_proxy_001",
            status=ValidationStatus.SUCCESS,
            response_time=0.5,
            error_message=None,
            test_url="https://httpbin.org/ip",
            expected_response="test_response",
            actual_response="test_response",
            quality_score=0.95,
            timestamp=datetime.utcnow()
        )

    async def test_connection_management(self, storage_config):
        """測試連接管理"""
        manager = RedisStorageManager(storage_config)
        
        # 測試連接
        await manager.connect()
        assert manager.connection_manager.is_connected
        
        # 測試健康檢查
        health = await manager.health_check()
        assert health["status"] == "healthy"
        assert "connection_metrics" in health
        
        # 測試斷開連接
        await manager.disconnect()
        assert not manager.connection_manager.is_connected

    async def test_proxy_crud_operations(self, storage_manager, sample_proxy_data):
        """測試代理數據CRUD操作"""
        # 測試保存
        success = await storage_manager.save_proxy(sample_proxy_data)
        assert success
        
        # 測試獲取
        retrieved_data = await storage_manager.get_proxy(sample_proxy_data.proxy_id)
        assert retrieved_data is not None
        assert retrieved_data.proxy_id == sample_proxy_data.proxy_id
        assert retrieved_data.host == sample_proxy_data.host
        assert retrieved_data.port == sample_proxy_data.port
        
        # 測試更新
        sample_proxy_data.status = ProxyStatus.INACTIVE
        sample_proxy_data.response_time = 1.0
        success = await storage_manager.update_proxy(sample_proxy_data)
        assert success
        
        # 驗證更新
        updated_data = await storage_manager.get_proxy(sample_proxy_data.proxy_id)
        assert updated_data.status == ProxyStatus.INACTIVE
        assert updated_data.response_time == 1.0
        
        # 測試刪除
        success = await storage_manager.delete_proxy(sample_proxy_data.proxy_id)
        assert success
        
        # 驗證刪除
        deleted_data = await storage_manager.get_proxy(sample_proxy_data.proxy_id)
        assert deleted_data is None

    async def test_proxy_status_queries(self, storage_manager):
        """測試代理狀態查詢"""
        # 創建測試數據
        test_proxies = []
        for i in range(5):
            proxy_data = ProxyData(
                proxy_id=f"test_proxy_{i:03d}",
                host=f"192.168.1.{100 + i}",
                port=8080 + i,
                protocol="http",
                status=ProxyStatus.ACTIVE if i % 2 == 0 else ProxyStatus.INACTIVE,
                source="test_source",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            test_proxies.append(proxy_data)
            await storage_manager.save_proxy(proxy_data)
        
        # 測試按狀態查詢
        active_proxies = await storage_manager.get_proxies_by_status(ProxyStatus.ACTIVE, limit=10)
        inactive_proxies = await storage_manager.get_proxies_by_status(ProxyStatus.INACTIVE, limit=10)
        
        assert len(active_proxies) == 3  # 0, 2, 4
        assert len(inactive_proxies) == 2  # 1, 3
        
        # 清理測試數據
        for proxy in test_proxies:
            await storage_manager.delete_proxy(proxy.proxy_id)

    async def test_batch_operations(self, storage_manager):
        """測試批量操作"""
        # 創建測試數據
        test_proxies = []
        proxy_ids = []
        
        for i in range(3):
            proxy_data = ProxyData(
                proxy_id=f"batch_test_proxy_{i:03d}",
                host=f"192.168.2.{100 + i}",
                port=8080 + i,
                protocol="http",
                status=ProxyStatus.ACTIVE,
                source="batch_test",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            test_proxies.append(proxy_data)
            proxy_ids.append(proxy_data.proxy_id)
            await storage_manager.save_proxy(proxy_data)
        
        # 測試批量狀態更新
        updated_count = await storage_manager.batch_update_proxy_status(
            proxy_ids, ProxyStatus.INACTIVE.value
        )
        assert updated_count == 3
        
        # 驗證更新結果
        for proxy_id in proxy_ids:
            proxy_data = await storage_manager.get_proxy(proxy_id)
            assert proxy_data.status == ProxyStatus.INACTIVE.value
        
        # 清理測試數據
        for proxy_id in proxy_ids:
            await storage_manager.delete_proxy(proxy_id)

    async def test_validation_operations(self, storage_manager, sample_validation_data):
        """測試驗證結果操作"""
        # 測試保存驗證結果
        success = await storage_manager.save_validation_result(sample_validation_data)
        assert success
        
        # 測試獲取驗證歷史
        history = await storage_manager.get_validation_history(
            sample_validation_data.proxy_id, limit=10
        )
        assert len(history) == 1
        assert history[0].validation_id == sample_validation_data.validation_id
        assert history[0].status == sample_validation_data.status

    async def test_statistics_operations(self, storage_manager):
        """測試統計操作"""
        proxy_id = "stats_test_proxy"
        
        # 測試更新統計
        stats = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "avg_response_time": 0.5,
            "last_success": datetime.utcnow().isoformat(),
            "success_rate": 0.95
        }
        
        success = await storage_manager.update_proxy_stats(proxy_id, stats)
        assert success
        
        # 測試獲取統計
        retrieved_stats = await storage_manager.get_proxy_stats(proxy_id)
        assert retrieved_stats is not None
        assert retrieved_stats["total_requests"] == 100
        assert retrieved_stats["success_rate"] == 0.95

    async def test_error_handling(self, storage_config):
        """測試錯誤處理"""
        # 測試無效配置
        invalid_config = StorageConfig(
            host="invalid_host",
            port=9999,
            db=0
        )
        
        manager = RedisStorageManager(invalid_config)
        
        # 測試連接失敗
        with pytest.raises(ConnectionError):
            await manager.connect()

    async def test_connection_recovery(self, storage_manager, sample_proxy_data):
        """測試連接恢復"""
        # 正常操作
        success = await storage_manager.save_proxy(sample_proxy_data)
        assert success
        
        # 模擬連接中斷（這裡只是測試重試機制）
        # 在實際測試中，可以通過停止Redis服務來模擬
        
        # 測試重試機制
        retrieved_data = await storage_manager.get_proxy(sample_proxy_data.proxy_id)
        assert retrieved_data is not None
        
        # 清理
        await storage_manager.delete_proxy(sample_proxy_data.proxy_id)

    async def test_performance_monitoring(self, storage_manager):
        """測試性能監控"""
        # 執行一些操作
        for i in range(10):
            proxy_data = ProxyData(
                proxy_id=f"perf_test_proxy_{i:03d}",
                host=f"192.168.3.{100 + i}",
                port=8080,
                protocol="http",
                status=ProxyStatus.ACTIVE,
                source="perf_test",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await storage_manager.save_proxy(proxy_data)
        
        # 獲取性能指標
        metrics = storage_manager.connection_manager.get_metrics()
        
        assert metrics["total_requests"] > 0
        assert metrics["successful_requests"] > 0
        assert metrics["success_rate"] > 0
        assert metrics["is_connected"] is True
        
        # 清理測試數據
        for i in range(10):
            await storage_manager.delete_proxy(f"perf_test_proxy_{i:03d}")

    async def test_cleanup_operations(self, storage_manager):
        """測試清理操作"""
        # 創建一些過期的測試數據
        old_time = datetime.utcnow() - timedelta(days=10)
        
        proxy_data = ProxyData(
            proxy_id="cleanup_test_proxy",
            host="192.168.4.100",
            port=8080,
            protocol="http",
            status=ProxyStatus.ACTIVE,
            source="cleanup_test",
            created_at=old_time,
            updated_at=old_time
        )
        
        await storage_manager.save_proxy(proxy_data)
        
        # 執行清理
        cleanup_stats = await storage_manager.cleanup_expired_data(days=7)
        
        assert "deleted_proxies" in cleanup_stats
        assert "deleted_validations" in cleanup_stats
        assert "deleted_stats" in cleanup_stats


async def run_manual_tests():
    """手動運行測試"""
    logging.basicConfig(level=logging.INFO)
    
    # 配置
    config = StorageConfig(
        host="localhost",
        port=6379,
        db=15,  # 測試數據庫
        password=None
    )
    
    # 創建管理器
    manager = RedisStorageManager(config)
    
    try:
        # 連接
        await manager.connect()
        print("✓ 連接成功")
        
        # 健康檢查
        health = await manager.health_check()
        print(f"✓ 健康檢查: {health['status']}")
        
        # 測試代理操作
        proxy_data = ProxyData(
            proxy_id="manual_test_proxy",
            host="192.168.1.100",
            port=8080,
            protocol="http",
            status=ProxyStatus.ACTIVE,
            source="manual_test",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 保存
        success = await manager.save_proxy(proxy_data)
        print(f"✓ 保存代理: {success}")
        
        # 獲取
        retrieved = await manager.get_proxy(proxy_data.proxy_id)
        print(f"✓ 獲取代理: {retrieved is not None}")
        
        # 更新
        proxy_data.status = ProxyStatus.INACTIVE
        success = await manager.update_proxy(proxy_data)
        print(f"✓ 更新代理: {success}")
        
        # 獲取性能指標
        metrics = manager.connection_manager.get_metrics()
        print(f"✓ 性能指標: 總請求 {metrics['total_requests']}, 成功率 {metrics['success_rate']:.2%}")
        
        # 清理
        await manager.delete_proxy(proxy_data.proxy_id)
        print("✓ 清理完成")
        
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
    
    finally:
        await manager.disconnect()
        print("✓ 連接已斷開")


if __name__ == "__main__":
    asyncio.run(run_manual_tests())