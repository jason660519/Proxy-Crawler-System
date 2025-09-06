#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高級代理整合示例

此示例展示如何使用新的高級代理獲取器、掃描器和配置系統。
演示了第一階段代理整合的核心功能。

作者: Jason
日期: 2024-01-20
"""

import asyncio
import logging
from pathlib import Path
from typing import List

from src.proxy_manager import (
    ProxyManager,
    ProxyManagerConfig,
    ApiConfig,
    ScannerConfig,
    ProxyNode,
    ProxyFilter,
    ProxyProtocol,
    ProxyAnonymity
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_integration():
    """基本整合示例"""
    logger.info("🚀 開始基本代理整合示例")
    
    # 創建配置
    config = ProxyManagerConfig(
        data_dir=Path("data/demo_proxy_manager"),
        
        # API 配置
        api_config=ApiConfig(
            proxyscrape_api_key="your_api_key_here",  # 請替換為實際 API 密鑰
            shodan_api_key="your_shodan_key_here",
            enable_proxyscrape=True,
            enable_github_sources=True,
            enable_shodan=False  # 需要付費 API
        ),
        
        # 掃描器配置
        scanner_config=ScannerConfig(
            enable_fast_scan=True,
            scan_timeout=5.0,
            max_concurrent_scans=100,
            port_scan_method="connect",  # 使用連接掃描而非原始套接字
            enable_anonymity_detection=True
        ),
        
        # 自動任務
        auto_fetch_enabled=True,
        auto_fetch_interval_hours=2,  # 更頻繁的獲取
        auto_cleanup_enabled=True
    )
    
    # 創建管理器
    manager = ProxyManager(config)
    
    try:
        # 啟動管理器
        await manager.start()
        
        # 獲取代理（包含高級來源）
        logger.info("📡 開始獲取代理...")
        proxies = await manager.fetch_proxies()
        
        logger.info(f"✅ 獲取到 {len(proxies)} 個有效代理")
        
        # 展示統計信息
        stats = manager.get_stats()
        logger.info(f"📊 管理器統計: {stats['manager_stats']}")
        logger.info(f"🏊 代理池摘要: {stats['pool_summary']}")
        
        # 測試不同類型的代理獲取
        await demo_proxy_filtering(manager)
        
        # 導出代理
        export_path = Path("data/demo_exported_proxies.json")
        exported_count = await manager.export_proxies(export_path)
        logger.info(f"📤 已導出 {exported_count} 個代理到 {export_path}")
        
    except Exception as e:
        logger.error(f"❌ 示例執行失敗: {e}")
        raise
    finally:
        await manager.stop()
        logger.info("🛑 管理器已停止")


async def demo_proxy_filtering(manager: ProxyManager):
    """代理過濾示例"""
    logger.info("🔍 開始代理過濾示例")
    
    # 獲取高匿名代理
    high_anon_filter = ProxyFilter(
        anonymity=[ProxyAnonymity.HIGH_ANONYMOUS],
        min_score=0.7
    )
    
    high_anon_proxies = await manager.get_proxies(
        count=5,
        filter_criteria=high_anon_filter
    )
    
    logger.info(f"🎭 獲取到 {len(high_anon_proxies)} 個高匿名代理")
    for proxy in high_anon_proxies:
        logger.info(f"  - {proxy.url} (匿名度: {proxy.anonymity.value}, 評分: {proxy.score:.2f})")
    
    # 獲取 HTTPS 代理
    https_filter = ProxyFilter(
        protocols=[ProxyProtocol.HTTPS],
        min_score=0.5
    )
    
    https_proxies = await manager.get_proxies(
        count=3,
        filter_criteria=https_filter
    )
    
    logger.info(f"🔒 獲取到 {len(https_proxies)} 個 HTTPS 代理")
    for proxy in https_proxies:
        logger.info(f"  - {proxy.url} (協議: {proxy.protocol.value})")


async def demo_advanced_features():
    """高級功能示例"""
    logger.info("⚡ 開始高級功能示例")
    
    # 創建高性能配置
    config = ProxyManagerConfig(
        data_dir=Path("data/advanced_proxy_manager"),
        
        # 啟用所有高級功能
        api_config=ApiConfig(
            enable_proxyscrape=True,
            enable_github_sources=True,
            github_update_interval_hours=6,
            proxyscrape_formats=["textplain", "json"]
        ),
        
        # 高性能掃描配置
        scanner_config=ScannerConfig(
            enable_fast_scan=True,
            scan_timeout=3.0,
            max_concurrent_scans=200,
            enable_anonymity_detection=True,
            enable_geolocation=True,
            batch_size=50
        ),
        
        # 優化的驗證配置
        validation_config={
            'timeout': 8,
            'test_urls': [
                'http://httpbin.org/ip',
                'https://api.ipify.org',
                'http://icanhazip.com'
            ],
            'max_retries': 1,
            'verify_anonymity': True
        },
        
        # 自動化配置
        auto_fetch_enabled=True,
        auto_fetch_interval_hours=1,
        auto_cleanup_enabled=True,
        auto_cleanup_interval_hours=6
    )
    
    manager = ProxyManager(config)
    
    try:
        await manager.start()
        
        # 執行多輪獲取以測試性能
        for round_num in range(3):
            logger.info(f"🔄 第 {round_num + 1} 輪代理獲取")
            
            proxies = await manager.fetch_proxies()
            
            # 驗證代理池
            await manager.validate_pools()
            
            # 獲取詳細統計
            stats = manager.get_stats()
            logger.info(f"📈 第 {round_num + 1} 輪統計:")
            logger.info(f"  - 總獲取: {stats['manager_stats']['total_fetched']}")
            logger.info(f"  - 總驗證: {stats['manager_stats']['total_validated']}")
            logger.info(f"  - 當前活躍: {stats['manager_stats']['total_active']}")
            
            # 短暫等待
            await asyncio.sleep(2)
        
        # 最終導出
        final_export = Path("data/final_advanced_proxies.json")
        final_count = await manager.export_proxies(final_export)
        logger.info(f"🎯 最終導出 {final_count} 個優質代理")
        
    except Exception as e:
        logger.error(f"❌ 高級功能示例失敗: {e}")
        raise
    finally:
        await manager.stop()


async def demo_import_export():
    """導入導出示例"""
    logger.info("💾 開始導入導出示例")
    
    config = ProxyManagerConfig(
        data_dir=Path("data/import_export_demo")
    )
    
    manager = ProxyManager(config)
    
    try:
        await manager.start()
        
        # 創建測試代理列表
        test_proxies_file = Path("data/test_proxies.txt")
        test_proxies_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 寫入測試代理
        test_proxy_list = [
            "8.8.8.8:8080",
            "1.1.1.1:3128",
            "9.9.9.9:8888"
        ]
        
        with open(test_proxies_file, 'w') as f:
            f.write('\n'.join(test_proxy_list))
        
        logger.info(f"📝 創建測試代理文件: {test_proxies_file}")
        
        # 導入代理
        imported_count = await manager.import_proxies(
            test_proxies_file,
            validate=False  # 跳過驗證以加快示例速度
        )
        
        logger.info(f"📥 導入了 {imported_count} 個代理")
        
        # 導出為不同格式
        formats = {
            "json": "data/exported_proxies.json",
            "txt": "data/exported_proxies.txt",
            "csv": "data/exported_proxies.csv"
        }
        
        for format_type, file_path in formats.items():
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            exported = await manager.export_proxies(export_path, format_type)
            logger.info(f"📤 導出 {exported} 個代理為 {format_type.upper()} 格式: {export_path}")
        
    except Exception as e:
        logger.error(f"❌ 導入導出示例失敗: {e}")
        raise
    finally:
        await manager.stop()


async def main():
    """主函數"""
    logger.info("🎬 開始高級代理整合示例")
    
    try:
        # 基本整合示例
        await demo_basic_integration()
        
        logger.info("\n" + "="*50 + "\n")
        
        # 高級功能示例
        await demo_advanced_features()
        
        logger.info("\n" + "="*50 + "\n")
        
        # 導入導出示例
        await demo_import_export()
        
        logger.info("🎉 所有示例執行完成！")
        
    except Exception as e:
        logger.error(f"❌ 示例執行失敗: {e}")
        raise


if __name__ == "__main__":
    # 確保數據目錄存在
    Path("data").mkdir(exist_ok=True)
    
    # 運行示例
    asyncio.run(main())