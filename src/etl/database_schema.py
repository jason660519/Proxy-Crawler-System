#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據庫架構設計

定義代理管理系統的完整數據庫模式，包括：
1. 代理數據表
2. 統計資訊表
3. 監控指標表
4. ETL 處理記錄表

作者: JasonSpider 專案
日期: 2024
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import asyncpg
from loguru import logger

from database_config import DatabaseConfig, db_config


class DatabaseSchemaManager:
    """數據庫架構管理器
    
    負責創建、更新和維護代理管理系統的數據庫架構
    """
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.logger = logger.bind(component='DatabaseSchema')
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
            self.logger.info("數據庫連接池初始化完成")
        except Exception as e:
            self.logger.error(f"數據庫初始化失敗: {e}")
            raise
    
    async def cleanup(self) -> None:
        """清理資源"""
        if self.db_pool:
            await self.db_pool.close()
            self.logger.info("數據庫連接池已關閉")
    
    async def create_all_tables(self, drop_existing: bool = False) -> None:
        """創建所有數據表
        
        Args:
            drop_existing: 是否刪除現有表格
        """
        self.logger.info("開始創建數據庫架構")
        
        try:
            async with self.db_pool.acquire() as conn:
                # 創建擴展
                await self._create_extensions(conn)
                
                # 如果需要，刪除現有表格
                if drop_existing:
                    await self._drop_all_tables(conn)
                
                # 創建枚舉類型
                await self._create_enums(conn)
                
                # 創建表格
                await self._create_proxy_nodes_table(conn)
                await self._create_proxy_metrics_table(conn)
                await self._create_proxy_validation_history_table(conn)
                await self._create_etl_pipeline_runs_table(conn)
                await self._create_etl_stage_metrics_table(conn)
                await self._create_system_monitoring_table(conn)
                await self._create_proxy_sources_table(conn)
                await self._create_proxy_tags_table(conn)
                await self._create_proxy_node_tags_table(conn)
                
                # 創建索引
                await self._create_indexes(conn)
                
                # 創建視圖
                await self._create_views(conn)
                
                # 創建函數和觸發器
                await self._create_functions_and_triggers(conn)
                
            self.logger.info("數據庫架構創建完成")
            
        except Exception as e:
            self.logger.error(f"創建數據庫架構失敗: {e}")
            raise
    
    async def _create_extensions(self, conn: asyncpg.Connection) -> None:
        """創建 PostgreSQL 擴展"""
        extensions = [
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
            'CREATE EXTENSION IF NOT EXISTS "pg_trgm";',
            'CREATE EXTENSION IF NOT EXISTS "btree_gin";'
        ]
        
        for ext in extensions:
            await conn.execute(ext)
        
        self.logger.info("PostgreSQL 擴展創建完成")
    
    async def _create_enums(self, conn: asyncpg.Connection) -> None:
        """創建枚舉類型"""
        enums = [
            # 代理協議
            '''
            DO $$ BEGIN
                CREATE TYPE proxy_protocol AS ENUM (
                    'http', 'https', 'socks4', 'socks5'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            ''',
            
            # 代理匿名度
            '''
            DO $$ BEGIN
                CREATE TYPE proxy_anonymity AS ENUM (
                    'transparent', 'anonymous', 'elite', 'unknown'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            ''',
            
            # 代理狀態
            '''
            DO $$ BEGIN
                CREATE TYPE proxy_status AS ENUM (
                    'active', 'inactive', 'testing', 'banned', 'unknown'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            ''',
            
            # 代理速度等級
            '''
            DO $$ BEGIN
                CREATE TYPE proxy_speed AS ENUM (
                    'fast', 'medium', 'slow', 'unknown'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            ''',
            
            # ETL 階段
            '''
            DO $$ BEGIN
                CREATE TYPE etl_stage AS ENUM (
                    'extract', 'transform', 'validate', 'load'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            '''
        ]
        
        for enum_sql in enums:
            await conn.execute(enum_sql)
        
        self.logger.info("枚舉類型創建完成")
    
    async def _create_proxy_nodes_table(self, conn: asyncpg.Connection) -> None:
        """創建代理節點主表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS proxy_nodes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            host VARCHAR(255) NOT NULL,
            port INTEGER NOT NULL,
            protocol proxy_protocol NOT NULL DEFAULT 'http',
            anonymity proxy_anonymity NOT NULL DEFAULT 'unknown',
            status proxy_status NOT NULL DEFAULT 'unknown',
            speed proxy_speed NOT NULL DEFAULT 'unknown',
            
            -- 地理位置資訊
            country VARCHAR(100),
            region VARCHAR(100),
            city VARCHAR(100),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            
            -- ISP 資訊
            isp VARCHAR(255),
            organization VARCHAR(255),
            
            -- 來源資訊
            source VARCHAR(255) NOT NULL,
            source_url TEXT,
            
            -- 性能指標
            response_time_ms INTEGER,
            success_rate DECIMAL(5, 4) DEFAULT 0.0,
            total_requests INTEGER DEFAULT 0,
            successful_requests INTEGER DEFAULT 0,
            failed_requests INTEGER DEFAULT 0,
            
            -- 評分
            score DECIMAL(5, 2) DEFAULT 0.0,
            
            -- 時間戳
            first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_checked TIMESTAMP WITH TIME ZONE,
            last_successful TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- 元數據
            metadata JSONB DEFAULT '{}',
            
            -- 約束
            CONSTRAINT unique_proxy UNIQUE (host, port, protocol),
            CONSTRAINT valid_port CHECK (port > 0 AND port <= 65535),
            CONSTRAINT valid_success_rate CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
            CONSTRAINT valid_score CHECK (score >= 0.0 AND score <= 100.0)
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("proxy_nodes 表創建完成")
    
    async def _create_proxy_metrics_table(self, conn: asyncpg.Connection) -> None:
        """創建代理指標歷史表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS proxy_metrics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            proxy_id UUID NOT NULL REFERENCES proxy_nodes(id) ON DELETE CASCADE,
            
            -- 測試結果
            test_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_successful BOOLEAN NOT NULL,
            response_time_ms INTEGER,
            status_code INTEGER,
            error_message TEXT,
            
            -- 測試配置
            test_url TEXT,
            timeout_ms INTEGER,
            user_agent TEXT,
            
            -- 檢測到的資訊
            detected_ip INET,
            detected_country VARCHAR(100),
            detected_anonymity proxy_anonymity,
            
            -- 元數據
            metadata JSONB DEFAULT '{}',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("proxy_metrics 表創建完成")
    
    async def _create_proxy_validation_history_table(self, conn: asyncpg.Connection) -> None:
        """創建代理驗證歷史表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS proxy_validation_history (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            proxy_id UUID NOT NULL REFERENCES proxy_nodes(id) ON DELETE CASCADE,
            
            -- 驗證批次資訊
            batch_id VARCHAR(255),
            validation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- 驗證結果
            is_valid BOOLEAN NOT NULL,
            validation_duration_ms INTEGER,
            
            -- 測試詳情
            tests_performed JSONB DEFAULT '[]',
            test_results JSONB DEFAULT '{}',
            
            -- 錯誤資訊
            error_type VARCHAR(100),
            error_details TEXT,
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("proxy_validation_history 表創建完成")
    
    async def _create_etl_pipeline_runs_table(self, conn: asyncpg.Connection) -> None:
        """創建 ETL 管道運行記錄表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS etl_pipeline_runs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            pipeline_id VARCHAR(255) UNIQUE NOT NULL,
            
            -- 運行資訊
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time TIMESTAMP WITH TIME ZONE,
            duration_seconds DECIMAL(10, 3),
            
            -- 狀態
            status VARCHAR(50) NOT NULL DEFAULT 'running',
            is_successful BOOLEAN,
            
            -- 統計
            total_records_processed INTEGER DEFAULT 0,
            successful_records INTEGER DEFAULT 0,
            failed_records INTEGER DEFAULT 0,
            database_records_inserted INTEGER DEFAULT 0,
            cache_records_inserted INTEGER DEFAULT 0,
            
            -- 成功率
            overall_success_rate DECIMAL(5, 4),
            
            -- 配置
            config JSONB DEFAULT '{}',
            
            -- 數據來源
            data_sources JSONB DEFAULT '[]',
            
            -- 輸出檔案
            output_files JSONB DEFAULT '[]',
            
            -- 錯誤資訊
            error_message TEXT,
            error_details JSONB DEFAULT '{}',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("etl_pipeline_runs 表創建完成")
    
    async def _create_etl_stage_metrics_table(self, conn: asyncpg.Connection) -> None:
        """創建 ETL 階段指標表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS etl_stage_metrics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            pipeline_run_id UUID NOT NULL REFERENCES etl_pipeline_runs(id) ON DELETE CASCADE,
            
            -- 階段資訊
            stage etl_stage NOT NULL,
            stage_order INTEGER NOT NULL,
            
            -- 時間資訊
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time TIMESTAMP WITH TIME ZONE,
            duration_seconds DECIMAL(10, 3),
            
            -- 統計
            total_records INTEGER DEFAULT 0,
            processed_records INTEGER DEFAULT 0,
            successful_records INTEGER DEFAULT 0,
            failed_records INTEGER DEFAULT 0,
            
            -- 成功率
            success_rate DECIMAL(5, 4),
            
            -- 錯誤
            errors JSONB DEFAULT '[]',
            
            -- 詳細指標
            detailed_metrics JSONB DEFAULT '{}',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("etl_stage_metrics 表創建完成")
    
    async def _create_system_monitoring_table(self, conn: asyncpg.Connection) -> None:
        """創建系統監控表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS system_monitoring (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            
            -- 時間戳
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- 系統指標
            cpu_usage_percent DECIMAL(5, 2),
            memory_usage_percent DECIMAL(5, 2),
            disk_usage_percent DECIMAL(5, 2),
            
            -- 數據庫指標
            active_connections INTEGER,
            total_queries INTEGER,
            slow_queries INTEGER,
            
            -- 代理統計
            total_proxies INTEGER DEFAULT 0,
            active_proxies INTEGER DEFAULT 0,
            inactive_proxies INTEGER DEFAULT 0,
            testing_proxies INTEGER DEFAULT 0,
            
            -- ETL 統計
            running_etl_pipelines INTEGER DEFAULT 0,
            completed_etl_pipelines_today INTEGER DEFAULT 0,
            failed_etl_pipelines_today INTEGER DEFAULT 0,
            
            -- Redis 指標
            redis_memory_usage_mb DECIMAL(10, 2),
            redis_connected_clients INTEGER,
            redis_keys_count INTEGER,
            
            -- 自定義指標
            custom_metrics JSONB DEFAULT '{}',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("system_monitoring 表創建完成")
    
    async def _create_proxy_sources_table(self, conn: asyncpg.Connection) -> None:
        """創建代理來源表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS proxy_sources (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) UNIQUE NOT NULL,
            url TEXT,
            description TEXT,
            
            -- 來源類型
            source_type VARCHAR(100) NOT NULL,
            
            -- 狀態
            is_active BOOLEAN DEFAULT true,
            last_crawled TIMESTAMP WITH TIME ZONE,
            next_crawl TIMESTAMP WITH TIME ZONE,
            crawl_interval_hours INTEGER DEFAULT 24,
            
            -- 統計
            total_proxies_found INTEGER DEFAULT 0,
            valid_proxies_found INTEGER DEFAULT 0,
            last_crawl_success BOOLEAN,
            
            -- 配置
            crawl_config JSONB DEFAULT '{}',
            
            -- 元數據
            metadata JSONB DEFAULT '{}',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("proxy_sources 表創建完成")
    
    async def _create_proxy_tags_table(self, conn: asyncpg.Connection) -> None:
        """創建代理標籤表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS proxy_tags (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            color VARCHAR(7), -- HEX 顏色代碼
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("proxy_tags 表創建完成")
    
    async def _create_proxy_node_tags_table(self, conn: asyncpg.Connection) -> None:
        """創建代理節點標籤關聯表"""
        sql = '''
        CREATE TABLE IF NOT EXISTS proxy_node_tags (
            proxy_id UUID NOT NULL REFERENCES proxy_nodes(id) ON DELETE CASCADE,
            tag_id UUID NOT NULL REFERENCES proxy_tags(id) ON DELETE CASCADE,
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            PRIMARY KEY (proxy_id, tag_id)
        );
        '''
        
        await conn.execute(sql)
        self.logger.info("proxy_node_tags 表創建完成")
    
    async def _create_indexes(self, conn: asyncpg.Connection) -> None:
        """創建索引"""
        indexes = [
            # proxy_nodes 表索引
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_host_port ON proxy_nodes(host, port);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_status ON proxy_nodes(status);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_protocol ON proxy_nodes(protocol);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_country ON proxy_nodes(country);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_source ON proxy_nodes(source);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_last_checked ON proxy_nodes(last_checked);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_score ON proxy_nodes(score DESC);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_success_rate ON proxy_nodes(success_rate DESC);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_response_time ON proxy_nodes(response_time_ms);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_metadata_gin ON proxy_nodes USING gin(metadata);',
            
            # proxy_metrics 表索引
            'CREATE INDEX IF NOT EXISTS idx_proxy_metrics_proxy_id ON proxy_metrics(proxy_id);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_metrics_timestamp ON proxy_metrics(test_timestamp);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_metrics_successful ON proxy_metrics(is_successful);',
            
            # proxy_validation_history 表索引
            'CREATE INDEX IF NOT EXISTS idx_proxy_validation_proxy_id ON proxy_validation_history(proxy_id);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_validation_batch ON proxy_validation_history(batch_id);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_validation_timestamp ON proxy_validation_history(validation_timestamp);',
            
            # etl_pipeline_runs 表索引
            'CREATE INDEX IF NOT EXISTS idx_etl_runs_pipeline_id ON etl_pipeline_runs(pipeline_id);',
            'CREATE INDEX IF NOT EXISTS idx_etl_runs_start_time ON etl_pipeline_runs(start_time);',
            'CREATE INDEX IF NOT EXISTS idx_etl_runs_status ON etl_pipeline_runs(status);',
            
            # etl_stage_metrics 表索引
            'CREATE INDEX IF NOT EXISTS idx_etl_stage_pipeline_run ON etl_stage_metrics(pipeline_run_id);',
            'CREATE INDEX IF NOT EXISTS idx_etl_stage_stage ON etl_stage_metrics(stage);',
            
            # system_monitoring 表索引
            'CREATE INDEX IF NOT EXISTS idx_system_monitoring_timestamp ON system_monitoring(timestamp);',
            
            # proxy_sources 表索引
            'CREATE INDEX IF NOT EXISTS idx_proxy_sources_active ON proxy_sources(is_active);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_sources_next_crawl ON proxy_sources(next_crawl);',
            
            # 複合索引
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_status_score ON proxy_nodes(status, score DESC);',
            'CREATE INDEX IF NOT EXISTS idx_proxy_nodes_protocol_country ON proxy_nodes(protocol, country);'
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        self.logger.info("索引創建完成")
    
    async def _create_views(self, conn: asyncpg.Connection) -> None:
        """創建視圖"""
        views = [
            # 活躍代理視圖
            '''
            CREATE OR REPLACE VIEW active_proxies AS
            SELECT 
                id, host, port, protocol, anonymity, country, 
                response_time_ms, success_rate, score,
                last_checked, last_successful
            FROM proxy_nodes 
            WHERE status = 'active' 
              AND last_checked > NOW() - INTERVAL '24 hours'
              AND success_rate > 0.5
            ORDER BY score DESC, response_time_ms ASC;
            ''',
            
            # 代理統計視圖
            '''
            CREATE OR REPLACE VIEW proxy_statistics AS
            SELECT 
                COUNT(*) as total_proxies,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_proxies,
                COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_proxies,
                COUNT(CASE WHEN status = 'testing' THEN 1 END) as testing_proxies,
                COUNT(CASE WHEN protocol = 'http' THEN 1 END) as http_proxies,
                COUNT(CASE WHEN protocol = 'https' THEN 1 END) as https_proxies,
                COUNT(CASE WHEN protocol = 'socks4' THEN 1 END) as socks4_proxies,
                COUNT(CASE WHEN protocol = 'socks5' THEN 1 END) as socks5_proxies,
                AVG(CASE WHEN status = 'active' THEN response_time_ms END) as avg_response_time,
                AVG(CASE WHEN status = 'active' THEN success_rate END) as avg_success_rate
            FROM proxy_nodes;
            ''',
            
            # ETL 運行統計視圖
            '''
            CREATE OR REPLACE VIEW etl_run_statistics AS
            SELECT 
                DATE(start_time) as run_date,
                COUNT(*) as total_runs,
                COUNT(CASE WHEN is_successful = true THEN 1 END) as successful_runs,
                COUNT(CASE WHEN is_successful = false THEN 1 END) as failed_runs,
                AVG(duration_seconds) as avg_duration,
                SUM(total_records_processed) as total_records,
                AVG(overall_success_rate) as avg_success_rate
            FROM etl_pipeline_runs 
            WHERE start_time > NOW() - INTERVAL '30 days'
            GROUP BY DATE(start_time)
            ORDER BY run_date DESC;
            '''
        ]
        
        for view_sql in views:
            await conn.execute(view_sql)
        
        self.logger.info("視圖創建完成")
    
    async def _create_functions_and_triggers(self, conn: asyncpg.Connection) -> None:
        """創建函數和觸發器"""
        # 更新時間戳函數
        update_timestamp_function = '''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        '''
        
        await conn.execute(update_timestamp_function)
        
        # 觸發器
        triggers = [
            '''
            DROP TRIGGER IF EXISTS update_proxy_nodes_updated_at ON proxy_nodes;
            CREATE TRIGGER update_proxy_nodes_updated_at
                BEFORE UPDATE ON proxy_nodes
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            ''',
            
            '''
            DROP TRIGGER IF EXISTS update_proxy_sources_updated_at ON proxy_sources;
            CREATE TRIGGER update_proxy_sources_updated_at
                BEFORE UPDATE ON proxy_sources
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            ''',
            
            '''
            DROP TRIGGER IF EXISTS update_etl_pipeline_runs_updated_at ON etl_pipeline_runs;
            CREATE TRIGGER update_etl_pipeline_runs_updated_at
                BEFORE UPDATE ON etl_pipeline_runs
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            '''
        ]
        
        for trigger_sql in triggers:
            await conn.execute(trigger_sql)
        
        self.logger.info("函數和觸發器創建完成")
    
    async def _drop_all_tables(self, conn: asyncpg.Connection) -> None:
        """刪除所有表格（謹慎使用）"""
        tables = [
            'proxy_node_tags',
            'proxy_tags',
            'proxy_sources',
            'system_monitoring',
            'etl_stage_metrics',
            'etl_pipeline_runs',
            'proxy_validation_history',
            'proxy_metrics',
            'proxy_nodes'
        ]
        
        for table in tables:
            await conn.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
        
        # 刪除枚舉類型
        enums = [
            'proxy_protocol',
            'proxy_anonymity',
            'proxy_status',
            'proxy_speed',
            'etl_stage'
        ]
        
        for enum in enums:
            await conn.execute(f'DROP TYPE IF EXISTS {enum} CASCADE;')
        
        self.logger.info("所有表格已刪除")
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """獲取架構資訊"""
        async with self.db_pool.acquire() as conn:
            # 獲取表格資訊
            tables_query = '''
            SELECT 
                table_name,
                table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            '''
            
            tables = await conn.fetch(tables_query)
            
            # 獲取索引資訊
            indexes_query = '''
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
            '''
            
            indexes = await conn.fetch(indexes_query)
            
            return {
                'tables': [dict(row) for row in tables],
                'indexes': [dict(row) for row in indexes],
                'created_at': datetime.now().isoformat()
            }
    
    async def validate_schema(self) -> Dict[str, Any]:
        """驗證架構完整性"""
        validation_results = {
            'is_valid': True,
            'missing_tables': [],
            'missing_indexes': [],
            'issues': []
        }
        
        expected_tables = [
            'proxy_nodes', 'proxy_metrics', 'proxy_validation_history',
            'etl_pipeline_runs', 'etl_stage_metrics', 'system_monitoring',
            'proxy_sources', 'proxy_tags', 'proxy_node_tags'
        ]
        
        async with self.db_pool.acquire() as conn:
            # 檢查表格是否存在
            for table in expected_tables:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                
                if not exists:
                    validation_results['missing_tables'].append(table)
                    validation_results['is_valid'] = False
        
        return validation_results


# 便利函數
async def initialize_database_schema(drop_existing: bool = False) -> None:
    """初始化數據庫架構的便利函數
    
    Args:
        drop_existing: 是否刪除現有表格
    """
    async with DatabaseSchemaManager() as schema_manager:
        await schema_manager.create_all_tables(drop_existing=drop_existing)


async def validate_database_schema() -> Dict[str, Any]:
    """驗證數據庫架構的便利函數
    
    Returns:
        Dict: 驗證結果
    """
    async with DatabaseSchemaManager() as schema_manager:
        return await schema_manager.validate_schema()


if __name__ == "__main__":
    # 測試用例
    async def main():
        # 初始化架構
        await initialize_database_schema(drop_existing=False)
        
        # 驗證架構
        validation = await validate_database_schema()
        print(f"架構驗證結果: {validation}")
        
        # 獲取架構資訊
        async with DatabaseSchemaManager() as schema_manager:
            info = await schema_manager.get_schema_info()
            print(f"找到 {len(info['tables'])} 個表格")
            print(f"找到 {len(info['indexes'])} 個索引")
    
    asyncio.run(main())