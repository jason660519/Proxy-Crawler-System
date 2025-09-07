#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy ETL 數據管道

實現代理數據的完整 ETL 流程：
1. Extract: 從多種來源提取代理數據
2. Transform: 數據清洗、驗證和標準化
3. Load: 載入到 PostgreSQL 和 Redis

作者: JasonSpider 專案
日期: 2024
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

import aiohttp
import asyncpg
import redis.asyncio as redis
from loguru import logger

# 導入現有模型
from ..proxy_manager.models import (
    ProxyNode, ProxyProtocol, ProxyAnonymity, ProxySpeed, ProxyStatus, ProxyMetrics
)
from database_config import DatabaseConfig, db_config


class ETLStage(Enum):
    """ETL 階段枚舉"""
    EXTRACT = "extract"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    LOAD = "load"


class DataSource(Enum):
    """數據來源類型"""
    JSON_FILE = "json_file"
    CSV_FILE = "csv_file"
    MARKDOWN_FILE = "markdown_file"
    WEB_SCRAPER = "web_scraper"
    API_ENDPOINT = "api_endpoint"
    DATABASE = "database"


@dataclass
class ETLConfig:
    """ETL 配置"""
    # 數據來源配置
    input_directory: str = "data/raw"
    output_directory: str = "data/processed"
    validated_directory: str = "data/validated"
    reports_directory: str = "data/reports"
    
    # 處理配置
    batch_size: int = 100
    max_concurrent_validations: int = 50
    validation_timeout: int = 10
    
    # 數據庫配置
    enable_database_storage: bool = True
    enable_redis_cache: bool = True
    
    # 品質控制
    min_success_rate: float = 0.7
    enable_data_validation: bool = True
    
    # 重試配置
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """確保目錄存在"""
        for directory in [self.input_directory, self.output_directory, 
                         self.validated_directory, self.reports_directory]:
            Path(directory).mkdir(parents=True, exist_ok=True)


@dataclass
class ETLMetrics:
    """ETL 處理指標"""
    stage: ETLStage
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.processed_records == 0:
            return 0.0
        return self.successful_records / self.processed_records
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)


@dataclass
class ETLResult:
    """ETL 處理結果"""
    pipeline_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_processing_time: float = 0.0
    stage_metrics: Dict[ETLStage, ETLMetrics] = field(default_factory=dict)
    output_files: List[str] = field(default_factory=list)
    database_records: int = 0
    cache_records: int = 0
    overall_success: bool = False
    
    @property
    def overall_success_rate(self) -> float:
        """整體成功率"""
        if not self.stage_metrics:
            return 0.0
        
        total_processed = sum(m.processed_records for m in self.stage_metrics.values())
        total_successful = sum(m.successful_records for m in self.stage_metrics.values())
        
        if total_processed == 0:
            return 0.0
        return total_successful / total_processed
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        result = asdict(self)
        result['stage_metrics'] = {k.value: v.to_dict() for k, v in self.stage_metrics.items()}
        return result


class ProxyETLPipeline:
    """代理 ETL 數據管道
    
    實現完整的代理數據 ETL 流程，包括：
    - 從多種來源提取代理數據
    - 數據清洗和標準化
    - 代理驗證和品質評估
    - 存儲到數據庫和快取
    """
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = logger.bind(component='ProxyETL')
        self.db_config = DatabaseConfig()
        
        # 數據庫連接
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # HTTP 客戶端
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # 處理統計
        self.current_result: Optional[ETLResult] = None
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """初始化連接"""
        try:
            # 初始化數據庫連接池
            if self.config.enable_database_storage:
                database_url = self.db_config.get_database_url('async')
                self.db_pool = await asyncpg.create_pool(
                    database_url,
                    min_size=5,
                    max_size=20,
                    command_timeout=30
                )
                self.logger.info("數據庫連接池初始化完成")
            
            # 初始化 Redis 連接
            if self.config.enable_redis_cache:
                redis_url = self.db_config.get_redis_url()
                self.redis_client = redis.from_url(redis_url)
                await self.redis_client.ping()
                self.logger.info("Redis 連接初始化完成")
            
            # 初始化 HTTP 會話
            timeout = aiohttp.ClientTimeout(total=self.config.validation_timeout)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            self.logger.info("HTTP 會話初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化失敗: {e}")
            await self.cleanup()
            raise
    
    async def cleanup(self) -> None:
        """清理資源"""
        if self.http_session:
            await self.http_session.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        if self.db_pool:
            await self.db_pool.close()
        
        self.logger.info("資源清理完成")
    
    def generate_pipeline_id(self) -> str:
        """生成管道 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_part = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"etl_{timestamp}_{hash_part}"
    
    async def run_complete_pipeline(
        self, 
        data_sources: List[Tuple[DataSource, str]],
        pipeline_id: Optional[str] = None
    ) -> ETLResult:
        """執行完整的 ETL 管道
        
        Args:
            data_sources: 數據來源列表，格式為 [(DataSource, path/url), ...]
            pipeline_id: 可選的管道 ID
            
        Returns:
            ETLResult: 處理結果
        """
        if pipeline_id is None:
            pipeline_id = self.generate_pipeline_id()
        
        self.current_result = ETLResult(
            pipeline_id=pipeline_id,
            start_time=datetime.now()
        )
        
        self.logger.info(f"開始 ETL 管道處理: {pipeline_id}")
        
        try:
            # 1. Extract 階段
            raw_data = await self._extract_stage(data_sources)
            
            # 2. Transform 階段
            transformed_data = await self._transform_stage(raw_data)
            
            # 3. Validate 階段
            validated_data = await self._validate_stage(transformed_data)
            
            # 4. Load 階段
            await self._load_stage(validated_data)
            
            # 完成處理
            self.current_result.end_time = datetime.now()
            self.current_result.total_processing_time = (
                self.current_result.end_time - self.current_result.start_time
            ).total_seconds()
            
            # 判斷整體成功
            self.current_result.overall_success = (
                self.current_result.overall_success_rate >= self.config.min_success_rate
            )
            
            self.logger.info(
                f"ETL 管道完成: {pipeline_id}, "
                f"成功率: {self.current_result.overall_success_rate:.2%}, "
                f"處理時間: {self.current_result.total_processing_time:.2f}s"
            )
            
            return self.current_result
            
        except Exception as e:
            self.logger.error(f"ETL 管道失敗: {pipeline_id}, 錯誤: {e}")
            if self.current_result:
                self.current_result.end_time = datetime.now()
                self.current_result.overall_success = False
            raise
    
    async def _extract_stage(self, data_sources: List[Tuple[DataSource, str]]) -> List[Dict[str, Any]]:
        """Extract 階段：從多種來源提取數據"""
        stage_start = time.time()
        metrics = ETLMetrics(stage=ETLStage.EXTRACT)
        
        raw_data = []
        
        for source_type, source_path in data_sources:
            try:
                if source_type == DataSource.JSON_FILE:
                    data = await self._extract_from_json(source_path)
                elif source_type == DataSource.CSV_FILE:
                    data = await self._extract_from_csv(source_path)
                elif source_type == DataSource.MARKDOWN_FILE:
                    data = await self._extract_from_markdown(source_path)
                else:
                    self.logger.warning(f"不支援的數據來源類型: {source_type}")
                    continue
                
                raw_data.extend(data)
                metrics.successful_records += len(data)
                
            except Exception as e:
                error_msg = f"提取數據失敗 {source_path}: {e}"
                self.logger.error(error_msg)
                metrics.errors.append(error_msg)
                metrics.failed_records += 1
        
        metrics.total_records = len(data_sources)
        metrics.processed_records = metrics.successful_records + metrics.failed_records
        metrics.processing_time = time.time() - stage_start
        
        self.current_result.stage_metrics[ETLStage.EXTRACT] = metrics
        
        self.logger.info(
            f"Extract 階段完成: 提取 {len(raw_data)} 條記錄, "
            f"成功率: {metrics.success_rate:.2%}"
        )
        
        return raw_data
    
    async def _extract_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """從 JSON 檔案提取數據"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON 檔案不存在: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 確保返回列表格式
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError(f"不支援的 JSON 格式: {type(data)}")
    
    async def _extract_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """從 CSV 檔案提取數據"""
        import pandas as pd
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV 檔案不存在: {file_path}")
        
        df = pd.read_csv(path)
        return df.to_dict('records')
    
    async def _extract_from_markdown(self, file_path: str) -> List[Dict[str, Any]]:
        """從 Markdown 檔案提取數據（簡化實現）"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Markdown 檔案不存在: {file_path}")
        
        # 這裡可以整合現有的 HTML to Markdown 解析器
        # 暫時返回空列表，待後續實現
        self.logger.warning(f"Markdown 提取功能待實現: {file_path}")
        return []
    
    async def _transform_stage(self, raw_data: List[Dict[str, Any]]) -> List[ProxyNode]:
        """Transform 階段：數據清洗和標準化"""
        stage_start = time.time()
        metrics = ETLMetrics(stage=ETLStage.TRANSFORM)
        
        transformed_proxies = []
        
        for record in raw_data:
            try:
                proxy = await self._transform_record(record)
                if proxy:
                    transformed_proxies.append(proxy)
                    metrics.successful_records += 1
                else:
                    metrics.failed_records += 1
                    
            except Exception as e:
                error_msg = f"轉換記錄失敗: {e}"
                self.logger.error(error_msg)
                metrics.errors.append(error_msg)
                metrics.failed_records += 1
        
        metrics.total_records = len(raw_data)
        metrics.processed_records = len(raw_data)
        metrics.processing_time = time.time() - stage_start
        
        self.current_result.stage_metrics[ETLStage.TRANSFORM] = metrics
        
        self.logger.info(
            f"Transform 階段完成: 轉換 {len(transformed_proxies)} 條記錄, "
            f"成功率: {metrics.success_rate:.2%}"
        )
        
        return transformed_proxies
    
    async def _transform_record(self, record: Dict[str, Any]) -> Optional[ProxyNode]:
        """轉換單條記錄為 ProxyNode"""
        try:
            # 提取基本資訊
            host = record.get('host') or record.get('ip')
            port = record.get('port')
            
            if not host or not port:
                return None
            
            # 標準化協議
            protocol_str = record.get('protocol', 'http').lower()
            try:
                protocol = ProxyProtocol(protocol_str)
            except ValueError:
                protocol = ProxyProtocol.HTTP
            
            # 標準化匿名度
            anonymity_str = record.get('anonymity', 'unknown').lower()
            try:
                anonymity = ProxyAnonymity(anonymity_str)
            except ValueError:
                anonymity = ProxyAnonymity.UNKNOWN
            
            # 創建代理節點
            proxy = ProxyNode(
                host=str(host).strip(),
                port=int(port),
                protocol=protocol,
                anonymity=anonymity,
                country=record.get('country'),
                region=record.get('region'),
                city=record.get('city'),
                isp=record.get('isp'),
                source=record.get('source', 'etl_pipeline'),
                tags=record.get('tags', []),
                metadata=record.get('metadata', {})
            )
            
            return proxy
            
        except Exception as e:
            self.logger.error(f"轉換記錄失敗: {record}, 錯誤: {e}")
            return None
    
    async def _validate_stage(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """Validate 階段：驗證代理可用性"""
        stage_start = time.time()
        metrics = ETLMetrics(stage=ETLStage.VALIDATE)
        
        # 分批處理
        validated_proxies = []
        
        for i in range(0, len(proxies), self.config.batch_size):
            batch = proxies[i:i + self.config.batch_size]
            
            # 並發驗證
            semaphore = asyncio.Semaphore(self.config.max_concurrent_validations)
            tasks = [self._validate_proxy(proxy, semaphore) for proxy in batch]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for proxy, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    error_msg = f"驗證代理失敗 {proxy.url}: {result}"
                    self.logger.error(error_msg)
                    metrics.errors.append(error_msg)
                    metrics.failed_records += 1
                else:
                    validated_proxies.append(result)
                    if result.is_available:
                        metrics.successful_records += 1
                    else:
                        metrics.failed_records += 1
        
        metrics.total_records = len(proxies)
        metrics.processed_records = len(proxies)
        metrics.processing_time = time.time() - stage_start
        
        self.current_result.stage_metrics[ETLStage.VALIDATE] = metrics
        
        self.logger.info(
            f"Validate 階段完成: 驗證 {len(validated_proxies)} 條記錄, "
            f"可用代理: {metrics.successful_records}, "
            f"成功率: {metrics.success_rate:.2%}"
        )
        
        return validated_proxies
    
    async def _validate_proxy(self, proxy: ProxyNode, semaphore: asyncio.Semaphore) -> ProxyNode:
        """驗證單個代理"""
        async with semaphore:
            try:
                # 測試 URL
                test_urls = [
                    'http://httpbin.org/ip',
                    'https://api.ipify.org?format=json'
                ]
                
                proxy_url = proxy.url
                start_time = time.time()
                
                # 嘗試連接
                async with self.http_session.get(
                    test_urls[0],
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.config.validation_timeout)
                ) as response:
                    if response.status == 200:
                        response_time = int((time.time() - start_time) * 1000)
                        
                        # 更新代理狀態
                        proxy.status = ProxyStatus.ACTIVE
                        proxy.metrics.update_success(response_time)
                        proxy.last_checked = datetime.now()
                        
                        # 檢查匿名性（簡化實現）
                        data = await response.json()
                        if 'origin' in data:
                            # 這裡可以添加更複雜的匿名性檢測邏輯
                            pass
                    else:
                        proxy.status = ProxyStatus.INACTIVE
                        proxy.metrics.update_failure()
                        proxy.last_checked = datetime.now()
                
            except Exception as e:
                proxy.status = ProxyStatus.INACTIVE
                proxy.metrics.update_failure()
                proxy.last_checked = datetime.now()
                self.logger.debug(f"代理驗證失敗 {proxy.url}: {e}")
            
            return proxy
    
    async def _load_stage(self, proxies: List[ProxyNode]) -> None:
        """Load 階段：載入到數據庫和快取"""
        stage_start = time.time()
        metrics = ETLMetrics(stage=ETLStage.LOAD)
        
        try:
            # 載入到數據庫
            if self.config.enable_database_storage and self.db_pool:
                db_count = await self._load_to_database(proxies)
                self.current_result.database_records = db_count
                self.logger.info(f"載入到數據庫: {db_count} 條記錄")
            
            # 載入到 Redis 快取
            if self.config.enable_redis_cache and self.redis_client:
                cache_count = await self._load_to_cache(proxies)
                self.current_result.cache_records = cache_count
                self.logger.info(f"載入到快取: {cache_count} 條記錄")
            
            # 生成報告
            await self._generate_reports(proxies)
            
            metrics.total_records = len(proxies)
            metrics.processed_records = len(proxies)
            metrics.successful_records = len(proxies)
            
        except Exception as e:
            error_msg = f"載入階段失敗: {e}"
            self.logger.error(error_msg)
            metrics.errors.append(error_msg)
            metrics.failed_records = len(proxies)
        
        metrics.processing_time = time.time() - stage_start
        self.current_result.stage_metrics[ETLStage.LOAD] = metrics
        
        self.logger.info(
            f"Load 階段完成: 處理 {len(proxies)} 條記錄, "
            f"成功率: {metrics.success_rate:.2%}"
        )
    
    async def _load_to_database(self, proxies: List[ProxyNode]) -> int:
        """載入到 PostgreSQL 數據庫"""
        if not self.db_pool:
            self.logger.warning("數據庫連接池未初始化，跳過數據庫載入")
            return 0
        
        if not proxies:
            self.logger.info("沒有代理數據需要載入")
            return 0
        
        loaded_count = 0
        failed_count = 0
        
        try:
            async with self.db_pool.acquire() as conn:
                # 開始事務
                async with conn.transaction():
                    for proxy in proxies:
                        try:
                            # 檢查代理是否已存在
                            existing_proxy = await conn.fetchrow(
                                """
                                SELECT id FROM proxy_nodes 
                                WHERE host = $1 AND port = $2 AND protocol = $3
                                """,
                                proxy.host, proxy.port, proxy.protocol.value
                            )
                            
                            if existing_proxy:
                                # 更新現有代理
                                await conn.execute(
                                    """
                                    UPDATE proxy_nodes SET
                                        anonymity = $1,
                                        country = $2,
                                        region = $3,
                                        city = $4,
                                        latitude = $5,
                                        longitude = $6,
                                        isp = $7,
                                        organization = $8,
                                        source = $9,
                                        source_url = $10,
                                        response_time_ms = $11,
                                        score = $12,
                                        last_checked = $13,
                                        updated_at = NOW(),
                                        metadata = $14
                                    WHERE host = $15 AND port = $16 AND protocol = $17
                                    """,
                                    proxy.anonymity.value,
                                    proxy.country,
                                    proxy.region,
                                    proxy.city,
                                    proxy.latitude,
                                    proxy.longitude,
                                    proxy.isp,
                                    proxy.organization,
                                    proxy.source,
                                    proxy.source_url,
                                    proxy.metrics.avg_response_time if proxy.metrics else None,
                                    proxy.score,
                                    proxy.last_checked,
                                    json.dumps(proxy.metadata) if proxy.metadata else '{}',
                                    proxy.host,
                                    proxy.port,
                                    proxy.protocol.value
                                )
                                self.logger.debug(f"更新代理: {proxy.host}:{proxy.port}")
                            else:
                                # 插入新代理
                                await conn.execute(
                                    """
                                    INSERT INTO proxy_nodes (
                                        host, port, protocol, anonymity,
                                        country, region, city, latitude, longitude,
                                        isp, organization, source, source_url,
                                        response_time_ms, score, last_checked,
                                        metadata, created_at, updated_at
                                    ) VALUES (
                                        $1, $2, $3, $4, $5, $6, $7, $8, $9,
                                        $10, $11, $12, $13, $14, $15, $16,
                                        $17, NOW(), NOW()
                                    )
                                    """,
                                    proxy.host,
                                    proxy.port,
                                    proxy.protocol.value,
                                    proxy.anonymity.value,
                                    proxy.country,
                                    proxy.region,
                                    proxy.city,
                                    proxy.latitude,
                                    proxy.longitude,
                                    proxy.isp,
                                    proxy.organization,
                                    proxy.source,
                                    proxy.source_url,
                                    proxy.metrics.avg_response_time if proxy.metrics else None,
                                    proxy.score,
                                    proxy.last_checked,
                                    json.dumps(proxy.metadata) if proxy.metadata else '{}'
                                )
                                self.logger.debug(f"插入新代理: {proxy.host}:{proxy.port}")
                            
                            loaded_count += 1
                            
                        except Exception as e:
                            failed_count += 1
                            self.logger.error(f"載入代理失敗 {proxy.host}:{proxy.port}: {e}")
                            continue
                    
                    self.logger.info(
                        f"數據庫載入完成: 成功 {loaded_count} 條，失敗 {failed_count} 條"
                    )
                    
        except Exception as e:
            self.logger.error(f"數據庫載入過程中發生錯誤: {e}")
            raise
        
        return loaded_count
    
    async def _load_to_cache(self, proxies: List[ProxyNode]) -> int:
        """載入到 Redis 快取"""
        if not self.redis_client:
            return 0
        
        cached_count = 0
        
        for proxy in proxies:
            if proxy.is_available:
                # 快取可用代理
                key = f"proxy:{proxy.host}:{proxy.port}"
                value = json.dumps(proxy.to_dict(), default=str)
                
                await self.redis_client.setex(
                    key, 
                    timedelta(hours=24).total_seconds(), 
                    value
                )
                
                # 添加到可用代理集合
                await self.redis_client.zadd(
                    "available_proxies",
                    {key: proxy.score}
                )
                
                cached_count += 1
        
        return cached_count
    
    async def _generate_reports(self, proxies: List[ProxyNode]) -> None:
        """生成處理報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 報告
        json_report_path = Path(self.config.reports_directory) / f"etl_report_{timestamp}.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_result.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        # Markdown 報告
        md_report_path = Path(self.config.reports_directory) / f"etl_report_{timestamp}.md"
        with open(md_report_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_report(proxies))
        
        self.current_result.output_files.extend([
            str(json_report_path),
            str(md_report_path)
        ])
    
    def _generate_markdown_report(self, proxies: List[ProxyNode]) -> str:
        """生成 Markdown 格式報告"""
        lines = [
            f"# ETL 處理報告",
            f"",
            f"**管道 ID**: {self.current_result.pipeline_id}",
            f"**處理時間**: {self.current_result.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**總處理時間**: {self.current_result.total_processing_time:.2f} 秒",
            f"**整體成功率**: {self.current_result.overall_success_rate:.2%}",
            f"",
            f"## 階段統計",
            f""
        ]
        
        for stage, metrics in self.current_result.stage_metrics.items():
            lines.extend([
                f"### {stage.value.title()} 階段",
                f"",
                f"- **總記錄數**: {metrics.total_records}",
                f"- **處理記錄數**: {metrics.processed_records}",
                f"- **成功記錄數**: {metrics.successful_records}",
                f"- **失敗記錄數**: {metrics.failed_records}",
                f"- **成功率**: {metrics.success_rate:.2%}",
                f"- **處理時間**: {metrics.processing_time:.2f} 秒",
                f""
            ])
            
            if metrics.errors:
                lines.extend([
                    f"**錯誤記錄**:",
                    f""
                ])
                for error in metrics.errors[:5]:  # 只顯示前5個錯誤
                    lines.append(f"- {error}")
                lines.append("")
        
        # 代理統計
        available_proxies = [p for p in proxies if p.is_available]
        lines.extend([
            f"## 代理統計",
            f"",
            f"- **總代理數**: {len(proxies)}",
            f"- **可用代理數**: {len(available_proxies)}",
            f"- **可用率**: {len(available_proxies)/len(proxies)*100:.1f}%" if proxies else "0%",
            f""
        ])
        
        if available_proxies:
            # 按協議分組
            protocol_stats = {}
            for proxy in available_proxies:
                protocol = proxy.protocol.value
                protocol_stats[protocol] = protocol_stats.get(protocol, 0) + 1
            
            lines.extend([
                f"### 按協議分佈",
                f""
            ])
            for protocol, count in protocol_stats.items():
                lines.append(f"- **{protocol.upper()}**: {count}")
            lines.append("")
        
        return '\n'.join(lines)


# 便利函數
async def run_etl_pipeline(
    data_sources: List[Tuple[DataSource, str]],
    config: Optional[ETLConfig] = None
) -> ETLResult:
    """執行 ETL 管道的便利函數
    
    Args:
        data_sources: 數據來源列表
        config: ETL 配置，如果為 None 則使用默認配置
        
    Returns:
        ETLResult: 處理結果
    """
    if config is None:
        config = ETLConfig()
    
    async with ProxyETLPipeline(config) as pipeline:
        return await pipeline.run_complete_pipeline(data_sources)


if __name__ == "__main__":
    # 測試用例
    async def main():
        # 配置
        config = ETLConfig(
            batch_size=50,
            max_concurrent_validations=20,
            validation_timeout=5
        )
        
        # 數據來源
        data_sources = [
            (DataSource.JSON_FILE, "data/raw/proxies.json"),
            (DataSource.CSV_FILE, "data/raw/proxies.csv")
        ]
        
        # 執行 ETL
        result = await run_etl_pipeline(data_sources, config)
        
        print(f"ETL 完成: {result.pipeline_id}")
        print(f"整體成功率: {result.overall_success_rate:.2%}")
        print(f"處理時間: {result.total_processing_time:.2f}s")
    
    asyncio.run(main())