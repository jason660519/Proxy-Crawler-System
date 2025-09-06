#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL 數據管道測試套件

提供全面的 ETL 流程測試，包括：
1. 單元測試
2. 整合測試
3. 性能測試
4. 數據品質測試
5. 錯誤處理測試

作者: JasonSpider 專案
日期: 2024
"""

import pytest
import asyncio
import tempfile
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import aiohttp
from pathlib import Path

# 導入要測試的模組
from .proxy_etl_pipeline import (
    ProxyETLPipeline, ETLConfig, ETLMetrics, ETLResult,
    ETLStage, ETLStatus
)
from .data_validator import (
    ProxyDataValidator, ValidationConfig, ValidationLevel,
    ValidationResult, ValidationReport
)
from .database_schema import DatabaseSchemaManager
from ..proxy_manager.models import (
    ProxyNode, ProxyProtocol, ProxyAnonymity, ProxySpeed, ProxyStatus
)
from database_config import get_db_config


class TestProxyETLPipeline:
    """ETL 管道測試類"""
    
    @pytest.fixture
    async def etl_config(self):
        """測試用 ETL 配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ETLConfig(
                batch_size=10,
                max_concurrent=5,
                retry_attempts=2,
                retry_delay=1,
                output_directory=temp_dir,
                enable_validation=True,
                enable_deduplication=True,
                enable_monitoring=True
            )
            yield config
    
    @pytest.fixture
    def sample_proxies(self):
        """測試用代理數據"""
        return [
            ProxyNode(
                host="192.168.1.1",
                port=8080,
                protocol=ProxyProtocol.HTTP,
                anonymity=ProxyAnonymity.ANONYMOUS,
                speed=ProxySpeed.FAST,
                status=ProxyStatus.ACTIVE,
                source="test_source_1",
                country="US",
                last_checked=datetime.now()
            ),
            ProxyNode(
                host="10.0.0.1",
                port=3128,
                protocol=ProxyProtocol.HTTPS,
                anonymity=ProxyAnonymity.ELITE,
                speed=ProxySpeed.MEDIUM,
                status=ProxyStatus.ACTIVE,
                source="test_source_2",
                country="UK",
                last_checked=datetime.now()
            ),
            ProxyNode(
                host="invalid-host",
                port=99999,
                protocol=ProxyProtocol.HTTP,
                source="test_source_3"
            )
        ]
    
    @pytest.fixture
    async def etl_pipeline(self, etl_config):
        """ETL 管道實例"""
        pipeline = ProxyETLPipeline(etl_config)
        await pipeline.initialize()
        yield pipeline
        await pipeline.cleanup()
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, etl_config):
        """測試管道初始化"""
        pipeline = ProxyETLPipeline(etl_config)
        
        # 測試初始化前狀態
        assert pipeline.status == ETLStatus.IDLE
        assert pipeline.current_stage == ETLStage.IDLE
        
        # 測試初始化
        await pipeline.initialize()
        
        # 驗證初始化後狀態
        assert pipeline.validator is not None
        assert pipeline.db_manager is not None
        
        await pipeline.cleanup()
    
    @pytest.mark.asyncio
    async def test_extract_stage(self, etl_pipeline, sample_proxies):
        """測試提取階段"""
        # 模擬數據源
        async def mock_data_source():
            for proxy in sample_proxies:
                yield proxy
        
        # 執行提取
        extracted_data = []
        async for proxy in etl_pipeline._extract_from_source(mock_data_source()):
            extracted_data.append(proxy)
        
        # 驗證結果
        assert len(extracted_data) == len(sample_proxies)
        assert all(isinstance(proxy, ProxyNode) for proxy in extracted_data)
    
    @pytest.mark.asyncio
    async def test_transform_stage(self, etl_pipeline, sample_proxies):
        """測試轉換階段"""
        # 執行轉換
        transformed_data = await etl_pipeline._transform_data(sample_proxies)
        
        # 驗證轉換結果
        assert len(transformed_data) <= len(sample_proxies)  # 可能過濾掉無效數據
        
        # 檢查數據標準化
        for proxy in transformed_data:
            assert proxy.host is not None
            assert 1 <= proxy.port <= 65535
            assert proxy.protocol in ProxyProtocol
    
    @pytest.mark.asyncio
    async def test_validation_integration(self, etl_pipeline, sample_proxies):
        """測試驗證整合"""
        # 執行驗證
        validation_reports = await etl_pipeline._validate_data(sample_proxies)
        
        # 驗證報告
        assert len(validation_reports) == len(sample_proxies)
        assert all(isinstance(report, ValidationReport) for report in validation_reports)
        
        # 檢查無效數據被標記
        invalid_reports = [r for r in validation_reports if not r.is_valid]
        assert len(invalid_reports) > 0  # 應該有無效的測試數據
    
    @pytest.mark.asyncio
    async def test_deduplication(self, etl_pipeline):
        """測試去重功能"""
        # 創建重複數據
        duplicate_proxies = [
            ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="test"),
            ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="test"),
            ProxyNode(host="192.168.1.2", port=8080, protocol=ProxyProtocol.HTTP, source="test")
        ]
        
        # 執行去重
        unique_proxies = await etl_pipeline._deduplicate_data(duplicate_proxies)
        
        # 驗證去重結果
        assert len(unique_proxies) == 2
        unique_signatures = {f"{p.host}:{p.port}" for p in unique_proxies}
        assert len(unique_signatures) == 2
    
    @pytest.mark.asyncio
    async def test_load_stage_mock(self, etl_pipeline, sample_proxies):
        """測試載入階段（模擬數據庫）"""
        # 模擬數據庫操作
        with patch.object(etl_pipeline.db_manager, 'bulk_insert_proxies', new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = len(sample_proxies)
            
            # 執行載入
            loaded_count = await etl_pipeline._load_to_database(sample_proxies)
            
            # 驗證載入
            assert loaded_count == len(sample_proxies)
            mock_insert.assert_called_once_with(sample_proxies)
    
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, etl_pipeline, sample_proxies):
        """測試完整管道執行"""
        # 模擬數據源
        async def mock_data_source():
            for proxy in sample_proxies:
                yield proxy
        
        # 模擬數據庫操作
        with patch.object(etl_pipeline.db_manager, 'bulk_insert_proxies', new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = 2  # 假設只有2個有效代理
            
            # 執行完整管道
            result = await etl_pipeline.process_data_source(mock_data_source())
            
            # 驗證結果
            assert isinstance(result, ETLResult)
            assert result.status == ETLStatus.COMPLETED
            assert result.total_processed > 0
            assert result.successful_records >= 0
            assert result.failed_records >= 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, etl_pipeline):
        """測試錯誤處理"""
        # 模擬會拋出異常的數據源
        async def failing_data_source():
            yield ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="test")
            raise Exception("模擬數據源錯誤")
        
        # 執行管道並捕獲錯誤
        result = await etl_pipeline.process_data_source(failing_data_source())
        
        # 驗證錯誤處理
        assert result.status in [ETLStatus.FAILED, ETLStatus.COMPLETED_WITH_ERRORS]
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, etl_pipeline, sample_proxies):
        """測試指標收集"""
        # 模擬數據源
        async def mock_data_source():
            for proxy in sample_proxies:
                yield proxy
        
        # 模擬數據庫操作
        with patch.object(etl_pipeline.db_manager, 'bulk_insert_proxies', new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = 2
            
            # 執行管道
            result = await etl_pipeline.process_data_source(mock_data_source())
            
            # 驗證指標
            metrics = result.metrics
            assert isinstance(metrics, ETLMetrics)
            assert metrics.total_processing_time > 0
            assert metrics.records_per_second >= 0
            assert metrics.validation_success_rate >= 0


class TestDataValidator:
    """數據驗證器測試類"""
    
    @pytest.fixture
    def validation_config(self):
        """測試用驗證配置"""
        return ValidationConfig(
            validation_level=ValidationLevel.BASIC,
            connection_timeout=5,
            enable_duplicate_detection=True
        )
    
    @pytest.fixture
    async def validator(self, validation_config):
        """驗證器實例"""
        validator = ProxyDataValidator(validation_config)
        await validator.initialize()
        yield validator
        await validator.cleanup()
    
    @pytest.mark.asyncio
    async def test_format_validation(self, validator):
        """測試格式驗證"""
        # 有效代理
        valid_proxy = ProxyNode(
            host="192.168.1.1",
            port=8080,
            protocol=ProxyProtocol.HTTP,
            source="test"
        )
        
        # 無效代理
        invalid_proxy = ProxyNode(
            host="invalid-host",
            port=99999,
            protocol=ProxyProtocol.HTTP,
            source="test"
        )
        
        # 驗證有效代理
        valid_report = await validator.validate_proxy(valid_proxy)
        format_errors = [issue for issue in valid_report.issues 
                        if issue.field in ['host', 'port'] and issue.severity == 'error']
        assert len(format_errors) == 0
        
        # 驗證無效代理
        invalid_report = await validator.validate_proxy(invalid_proxy)
        format_errors = [issue for issue in invalid_report.issues 
                        if issue.field in ['host', 'port'] and issue.severity == 'error']
        assert len(format_errors) > 0
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, validator):
        """測試重複檢測"""
        proxy1 = ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="test")
        proxy2 = ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="test")
        
        # 第一次驗證
        report1 = await validator.validate_proxy(proxy1)
        duplicate_issues1 = [issue for issue in report1.issues if issue.issue_type == 'duplicate_proxy']
        assert len(duplicate_issues1) == 0
        
        # 第二次驗證（應該檢測到重複）
        report2 = await validator.validate_proxy(proxy2)
        duplicate_issues2 = [issue for issue in report2.issues if issue.issue_type == 'duplicate_proxy']
        assert len(duplicate_issues2) > 0
    
    @pytest.mark.asyncio
    async def test_batch_validation(self, validator):
        """測試批量驗證"""
        proxies = [
            ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="test"),
            ProxyNode(host="192.168.1.2", port=3128, protocol=ProxyProtocol.HTTPS, source="test"),
            ProxyNode(host="invalid", port=99999, protocol=ProxyProtocol.HTTP, source="test")
        ]
        
        # 執行批量驗證
        reports = await validator.validate_batch(proxies, max_concurrent=2)
        
        # 驗證結果
        assert len(reports) == len(proxies)
        assert all(isinstance(report, ValidationReport) for report in reports)
        
        # 檢查統計
        stats = validator.get_validation_statistics()
        assert stats['total_validated'] >= len(proxies)
    
    def test_quality_score_calculation(self, validation_config):
        """測試品質評分計算"""
        validator = ProxyDataValidator(validation_config)
        
        # 創建測試報告
        report = ValidationReport(
            proxy_id="test",
            validation_level=ValidationLevel.BASIC,
            overall_result=ValidationResult.VALID,
            quality_score=0.0
        )
        
        # 添加測試元數據
        report.metadata = {
            'connectivity_success_rate': 0.8,
            'avg_response_time': 2000,
            'anonymity_verified': True,
            'performance_stability': 0.9
        }
        
        # 計算品質評分
        proxy = ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="test")
        validator._calculate_quality_score(proxy, report)
        
        # 驗證評分
        assert 0.0 <= report.quality_score <= 1.0
        assert 'quality_breakdown' in report.metadata


class TestDatabaseSchema:
    """數據庫架構測試類"""
    
    @pytest.fixture
    def schema_manager(self):
        """架構管理器實例"""
        return DatabaseSchemaManager()
    
    def test_table_creation_sql(self, schema_manager):
        """測試表格創建 SQL"""
        # 測試代理表格 SQL
        proxy_sql = schema_manager.get_create_proxy_table_sql()
        assert 'CREATE TABLE IF NOT EXISTS proxies' in proxy_sql
        assert 'host VARCHAR(255) NOT NULL' in proxy_sql
        assert 'port INTEGER NOT NULL' in proxy_sql
        
        # 測試統計表格 SQL
        stats_sql = schema_manager.get_create_proxy_stats_table_sql()
        assert 'CREATE TABLE IF NOT EXISTS proxy_statistics' in stats_sql
    
    def test_index_creation_sql(self, schema_manager):
        """測試索引創建 SQL"""
        indexes_sql = schema_manager.get_create_indexes_sql()
        assert isinstance(indexes_sql, list)
        assert len(indexes_sql) > 0
        assert all('CREATE INDEX' in sql for sql in indexes_sql)
    
    def test_view_creation_sql(self, schema_manager):
        """測試視圖創建 SQL"""
        views_sql = schema_manager.get_create_views_sql()
        assert isinstance(views_sql, list)
        assert len(views_sql) > 0
        assert all('CREATE VIEW' in sql for sql in views_sql)


class TestPerformance:
    """性能測試類"""
    
    @pytest.mark.asyncio
    async def test_large_batch_processing(self):
        """測試大批量處理性能"""
        # 創建大量測試數據
        large_proxy_list = [
            ProxyNode(
                host=f"192.168.1.{i % 255 + 1}",
                port=8080 + (i % 1000),
                protocol=ProxyProtocol.HTTP,
                source="performance_test"
            )
            for i in range(1000)
        ]
        
        # 配置高性能設定
        config = ValidationConfig(
            validation_level=ValidationLevel.BASIC,
            connection_timeout=1
        )
        
        # 測量處理時間
        start_time = datetime.now()
        
        async with ProxyDataValidator(config) as validator:
            reports = await validator.validate_batch(large_proxy_list, max_concurrent=100)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 驗證性能
        assert len(reports) == len(large_proxy_list)
        assert processing_time < 60  # 應該在60秒內完成
        
        throughput = len(large_proxy_list) / processing_time
        print(f"處理吞吐量: {throughput:.2f} 代理/秒")
        assert throughput > 10  # 至少每秒處理10個代理
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """測試記憶體使用"""
        import psutil
        import gc
        
        # 記錄初始記憶體使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 創建大量數據
        large_proxy_list = [
            ProxyNode(
                host=f"10.0.{i // 255}.{i % 255}",
                port=8080,
                protocol=ProxyProtocol.HTTP,
                source="memory_test"
            )
            for i in range(5000)
        ]
        
        config = ValidationConfig(validation_level=ValidationLevel.BASIC)
        
        async with ProxyDataValidator(config) as validator:
            reports = await validator.validate_batch(large_proxy_list, max_concurrent=50)
        
        # 強制垃圾回收
        del reports
        del large_proxy_list
        gc.collect()
        
        # 檢查記憶體使用
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        print(f"記憶體增長: {memory_increase / 1024 / 1024:.2f} MB")
        
        # 記憶體增長應該合理（小於500MB）
        assert memory_increase < 500 * 1024 * 1024


class TestIntegration:
    """整合測試類"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self):
        """端到端管道測試"""
        # 創建臨時配置
        with tempfile.TemporaryDirectory() as temp_dir:
            etl_config = ETLConfig(
                batch_size=5,
                max_concurrent=3,
                output_directory=temp_dir,
                enable_validation=True,
                enable_deduplication=True
            )
            
            # 創建測試數據
            test_proxies = [
                ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="integration_test"),
                ProxyNode(host="192.168.1.2", port=3128, protocol=ProxyProtocol.HTTPS, source="integration_test"),
                ProxyNode(host="invalid", port=99999, protocol=ProxyProtocol.HTTP, source="integration_test"),
                ProxyNode(host="192.168.1.1", port=8080, protocol=ProxyProtocol.HTTP, source="integration_test"),  # 重複
            ]
            
            # 模擬數據源
            async def test_data_source():
                for proxy in test_proxies:
                    yield proxy
            
            # 執行完整管道
            pipeline = ProxyETLPipeline(etl_config)
            await pipeline.initialize()
            
            try:
                with patch.object(pipeline.db_manager, 'bulk_insert_proxies', new_callable=AsyncMock) as mock_insert:
                    mock_insert.return_value = 2
                    
                    result = await pipeline.process_data_source(test_data_source())
                    
                    # 驗證結果
                    assert result.status in [ETLStatus.COMPLETED, ETLStatus.COMPLETED_WITH_ERRORS]
                    assert result.total_processed == len(test_proxies)
                    assert result.duplicate_records > 0  # 應該檢測到重複
                    
                    # 檢查輸出文件
                    output_files = list(Path(temp_dir).glob('*.json'))
                    assert len(output_files) > 0
                    
                    # 驗證輸出內容
                    with open(output_files[0], 'r', encoding='utf-8') as f:
                        output_data = json.load(f)
                        assert 'result' in output_data
                        assert 'metrics' in output_data
            
            finally:
                await pipeline.cleanup()


# 測試配置
pytest_plugins = ['pytest_asyncio']


if __name__ == "__main__":
    # 運行測試
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])