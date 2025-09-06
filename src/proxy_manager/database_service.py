"""代理管理器數據庫服務模組

提供從數據庫讀取代理數據的功能：
- 代理查詢與篩選
- 統計信息獲取
- 數據庫連接管理
- 分頁查詢支持
"""

import asyncio
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

import asyncpg
from loguru import logger

from .models import ProxyNode, ProxyStatus, ProxyAnonymity, ProxyProtocol, ProxyFilter
from database_config import DatabaseConfig


@dataclass
class ProxyQueryResult:
    """代理查詢結果"""
    proxies: List[ProxyNode]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class DatabaseService:
    """數據庫服務類
    
    提供代理數據的數據庫操作功能
    """
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.logger = logger.bind(component='DatabaseService')
        self.db_pool: Optional[asyncpg.Pool] = None
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """初始化數據庫連接"""
        try:
            database_url = self.db_config.get_database_url('async')
            self.db_pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            self.logger.info("數據庫服務初始化完成")
        except Exception as e:
            self.logger.error(f"數據庫服務初始化失敗: {e}")
            raise
    
    async def cleanup(self) -> None:
        """清理資源"""
        if self.db_pool:
            await self.db_pool.close()
            self.logger.info("數據庫連接池已關閉")
    
    async def get_proxies(
        self,
        filter_criteria: Optional[ProxyFilter] = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = 'score',
        order_desc: bool = True
    ) -> ProxyQueryResult:
        """獲取代理列表
        
        Args:
            filter_criteria: 篩選條件
            page: 頁碼（從1開始）
            page_size: 每頁大小
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            ProxyQueryResult: 查詢結果
        """
        if not self.db_pool:
            raise RuntimeError("數據庫連接池未初始化")
        
        # 構建查詢條件
        where_conditions = []
        params = []
        param_count = 0
        
        if filter_criteria:
            if filter_criteria.protocols:
                protocol_values = [p.value for p in filter_criteria.protocols]
                param_count += 1
                where_conditions.append(f"protocol = ANY(${param_count})")
                params.append(protocol_values)
            
            if filter_criteria.anonymity_levels:
                anonymity_values = [a.value for a in filter_criteria.anonymity_levels]
                param_count += 1
                where_conditions.append(f"anonymity = ANY(${param_count})")
                params.append(anonymity_values)
            
            if filter_criteria.countries:
                param_count += 1
                where_conditions.append(f"country = ANY(${param_count})")
                params.append(filter_criteria.countries)
            
            if filter_criteria.min_score is not None:
                param_count += 1
                where_conditions.append(f"score >= ${param_count}")
                params.append(filter_criteria.min_score)
            
            if filter_criteria.max_response_time is not None:
                param_count += 1
                where_conditions.append(f"response_time_ms <= ${param_count}")
                params.append(filter_criteria.max_response_time)
        
        # 構建WHERE子句
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 構建ORDER BY子句
        order_direction = "DESC" if order_desc else "ASC"
        order_clause = f"ORDER BY {order_by} {order_direction}"
        
        # 計算偏移量
        offset = (page - 1) * page_size
        
        try:
            async with self.db_pool.acquire() as conn:
                # 獲取總數
                count_query = f"""
                    SELECT COUNT(*) FROM proxy_nodes
                    {where_clause}
                """
                total_count = await conn.fetchval(count_query, *params)
                
                # 獲取數據
                param_count += 1
                limit_param = param_count
                param_count += 1
                offset_param = param_count
                
                data_query = f"""
                    SELECT 
                        id, host, port, protocol, anonymity,
                        country, region, city, latitude, longitude,
                        isp, organization, source, source_url,
                        response_time_ms, score, 
                        first_seen, last_checked, last_successful,
                        created_at, updated_at, metadata
                    FROM proxy_nodes
                    {where_clause}
                    {order_clause}
                    LIMIT ${limit_param} OFFSET ${offset_param}
                """
                
                rows = await conn.fetch(data_query, *params, page_size, offset)
                
                # 轉換為ProxyNode對象
                proxies = []
                for row in rows:
                    try:
                        proxy = self._row_to_proxy_node(row)
                        proxies.append(proxy)
                    except Exception as e:
                        self.logger.warning(f"轉換代理數據失敗: {e}")
                        continue
                
                # 計算分頁信息
                has_next = (page * page_size) < total_count
                has_prev = page > 1
                
                return ProxyQueryResult(
                    proxies=proxies,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    has_next=has_next,
                    has_prev=has_prev
                )
                
        except Exception as e:
            self.logger.error(f"查詢代理數據失敗: {e}")
            raise
    
    async def get_proxy_by_id(self, proxy_id: str) -> Optional[ProxyNode]:
        """根據ID獲取代理
        
        Args:
            proxy_id: 代理ID
            
        Returns:
            Optional[ProxyNode]: 代理對象或None
        """
        if not self.db_pool:
            raise RuntimeError("數據庫連接池未初始化")
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT 
                        id, host, port, protocol, anonymity,
                        country, region, city, latitude, longitude,
                        isp, organization, source, source_url,
                        response_time_ms, score, 
                        first_seen, last_checked, last_successful,
                        created_at, updated_at, metadata
                    FROM proxy_nodes
                    WHERE id = $1
                    """,
                    proxy_id
                )
                
                if row:
                    return self._row_to_proxy_node(row)
                return None
                
        except Exception as e:
            self.logger.error(f"根據ID查詢代理失敗: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """獲取代理統計信息
        
        Returns:
            Dict[str, Any]: 統計信息
        """
        if not self.db_pool:
            raise RuntimeError("數據庫連接池未初始化")
        
        try:
            async with self.db_pool.acquire() as conn:
                # 基本統計
                basic_stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_proxies,
                        COUNT(CASE WHEN last_checked > NOW() - INTERVAL '1 hour' THEN 1 END) as recently_checked,
                        COUNT(CASE WHEN score > 80 THEN 1 END) as high_quality,
                        COUNT(CASE WHEN score > 60 THEN 1 END) as medium_quality,
                        COUNT(CASE WHEN score <= 60 THEN 1 END) as low_quality,
                        AVG(score) as avg_score,
                        AVG(response_time_ms) as avg_response_time
                    FROM proxy_nodes
                    """
                )
                
                # 協議分布
                protocol_stats = await conn.fetch(
                    """
                    SELECT protocol, COUNT(*) as count
                    FROM proxy_nodes
                    GROUP BY protocol
                    ORDER BY count DESC
                    """
                )
                
                # 匿名度分布
                anonymity_stats = await conn.fetch(
                    """
                    SELECT anonymity, COUNT(*) as count
                    FROM proxy_nodes
                    GROUP BY anonymity
                    ORDER BY count DESC
                    """
                )
                
                # 國家分布（前10）
                country_stats = await conn.fetch(
                    """
                    SELECT country, COUNT(*) as count
                    FROM proxy_nodes
                    WHERE country IS NOT NULL
                    GROUP BY country
                    ORDER BY count DESC
                    LIMIT 10
                    """
                )
                
                return {
                    'basic': dict(basic_stats) if basic_stats else {},
                    'protocol_distribution': [dict(row) for row in protocol_stats],
                    'anonymity_distribution': [dict(row) for row in anonymity_stats],
                    'country_distribution': [dict(row) for row in country_stats],
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"獲取統計信息失敗: {e}")
            raise
    
    def _row_to_proxy_node(self, row) -> ProxyNode:
        """將數據庫行轉換為ProxyNode對象
        
        Args:
            row: 數據庫行
            
        Returns:
            ProxyNode: 代理對象
        """
        try:
            # 解析metadata
            metadata = {}
            if row['metadata']:
                if isinstance(row['metadata'], str):
                    metadata = json.loads(row['metadata'])
                else:
                    metadata = row['metadata']
            
            # 創建ProxyNode對象
            proxy = ProxyNode(
                host=row['host'],
                port=row['port'],
                protocol=ProxyProtocol(row['protocol']),
                anonymity=ProxyAnonymity(row['anonymity']),
                country=row['country'],
                region=row['region'],
                city=row['city'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                isp=row['isp'],
                organization=row['organization'],
                source=row['source'],
                source_url=row['source_url'],
                score=float(row['score']) if row['score'] else 0.0,
                first_seen=row['first_seen'],
                last_checked=row['last_checked'],
                last_successful=row['last_successful'],
                metadata=metadata
            )
            
            # 設置響應時間
            if row['response_time_ms'] and proxy.metrics:
                proxy.metrics.avg_response_time = row['response_time_ms']
            
            return proxy
            
        except Exception as e:
            self.logger.error(f"轉換數據庫行為ProxyNode失敗: {e}")
            raise


# 全局數據庫服務實例
_db_service: Optional[DatabaseService] = None


async def get_database_service() -> DatabaseService:
    """獲取數據庫服務實例
    
    Returns:
        DatabaseService: 數據庫服務實例
    """
    global _db_service
    
    if _db_service is None:
        _db_service = DatabaseService()
        await _db_service.initialize()
    
    return _db_service


async def cleanup_database_service() -> None:
    """清理數據庫服務實例"""
    global _db_service
    
    if _db_service:
        await _db_service.cleanup()
        _db_service = None