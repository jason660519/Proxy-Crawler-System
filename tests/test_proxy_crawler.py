#!/usr/bin/env python3
"""代理爬蟲系統測試腳本

此腳本用於測試代理爬蟲系統的各個組件，包括：
- 單個爬蟲測試
- 爬蟲管理器測試
- 代理驗證測試
- 輸出格式測試

使用方法:
    python test_proxy_crawler.py
    python test_proxy_crawler.py --quick  # 快速測試，不驗證代理
    python test_proxy_crawler.py --source sslproxies  # 測試單個源
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional, List

# 添加src目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from proxy_manager import (
    CrawlerManager, 
    SSLProxiesCrawler, 
    GeonodeCrawler, 
    FreeProxyListCrawler,
    ProxyValidator
)


def setup_logging(verbose: bool = False):
    """設置日誌記錄"""
    logger.remove()
    
    if verbose:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG"
        )
    else:
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="INFO"
        )


async def test_single_crawler(crawler_name: str, limit: int = 10):
    """測試單個爬蟲
    
    Args:
        crawler_name: 爬蟲名稱
        limit: 限制爬取數量
    """
    logger.info(f"\n=== 測試 {crawler_name} 爬蟲 ===")
    
    crawler_classes = {
        'sslproxies': SSLProxiesCrawler,
        'geonode': GeonodeCrawler,
        'free_proxy_list': FreeProxyListCrawler
    }
    
    if crawler_name not in crawler_classes:
        logger.error(f"未知的爬蟲: {crawler_name}")
        return False
    
    try:
        crawler_class = crawler_classes[crawler_name]
        async with crawler_class() as crawler:
            logger.info(f"開始爬取 {crawler_name}...")
            proxies = await crawler.crawl()
            
            if proxies:
                logger.info(f"成功爬取 {len(proxies)} 個代理")
                
                # 顯示前幾個代理作為示例
                show_count = min(limit, len(proxies))
                logger.info(f"前 {show_count} 個代理:")
                
                for i, proxy in enumerate(proxies[:show_count]):
                    logger.info(f"  {i+1}. {proxy.ip}:{proxy.port} ({proxy.protocol}) - {proxy.country}")
                
                return True
            else:
                logger.warning(f"未能從 {crawler_name} 獲取到代理")
                return False
                
    except Exception as e:
        logger.error(f"測試 {crawler_name} 爬蟲時發生錯誤: {str(e)}")
        return False


async def test_proxy_validator(proxies_to_test: int = 5):
    """測試代理驗證器
    
    Args:
        proxies_to_test: 要測試的代理數量
    """
    logger.info(f"\n=== 測試代理驗證器 ===")
    
    try:
        # 先獲取一些代理進行測試
        async with SSLProxiesCrawler() as crawler:
            proxies = await crawler.crawl()
            
        if not proxies:
            logger.warning("沒有代理可供測試驗證器")
            return False
        
        # 取前幾個代理進行驗證
        test_proxies = proxies[:proxies_to_test]
        logger.info(f"將驗證 {len(test_proxies)} 個代理...")
        
        validator = ProxyValidator(timeout=5.0, max_concurrent=10)
        results = await validator.validate_proxies(
            test_proxies, 
            test_anonymity=True, 
            test_geo=False
        )
        
        working_proxies = validator.get_working_proxies(results)
        
        logger.info(f"驗證完成: {len(working_proxies)}/{len(test_proxies)} 個代理可用")
        
        # 顯示驗證結果
        for result in results:
            status_icon = "✅" if result.status.value == "working" else "❌"
            response_time = f"{result.response_time:.2f}s" if result.response_time else "N/A"
            logger.info(
                f"  {status_icon} {result.proxy.ip}:{result.proxy.port} - "
                f"響應時間: {response_time}, 匿名等級: {result.anonymity_level.value}"
            )
        
        return len(working_proxies) > 0
        
    except Exception as e:
        logger.error(f"測試代理驗證器時發生錯誤: {str(e)}")
        return False


async def test_crawler_manager(args, enable_validation: bool = True, sources: Optional[List[str]] = None) -> bool:
    """測試爬蟲管理器
    
    Args:
        args: 命令行參數
        enable_validation: 是否啟用驗證
        sources: 要測試的源列表
    """
    logger.info(f"\n=== 測試爬蟲管理器 ===")
    
    try:
        # 創建測試輸出目錄
        test_output_dir = Path("test_output")
        test_output_dir.mkdir(exist_ok=True)
        
        # 創建管理器
        manager = CrawlerManager(
            output_dir=test_output_dir,
            enable_validation=enable_validation,
            validation_timeout=5.0,
            max_concurrent_validation=20,
            etl_mode=getattr(args, 'etl_mode', False)
        )
        
        # 列出可用爬蟲
        available_crawlers = manager.list_available_crawlers()
        logger.info(f"可用爬蟲: {', '.join(available_crawlers)}")
        
        # 確定要測試的源
        if sources is None:
            sources = available_crawlers
        
        logger.info(f"將測試源: {', '.join(sources)}")
        
        # 運行爬蟲管理器
        result = await manager.crawl_all_sources(
            sources=sources,
            validate_proxies=enable_validation,
            output_formats=['json', 'markdown']
        )
        
        # 顯示結果
        stats = result['stats']
        logger.info(f"\n=== 管理器測試結果 ===")
        logger.info(f"總爬取代理數: {stats['total_crawled']}")
        logger.info(f"去重後代理數: {stats['total_unique']}")
        
        if enable_validation and stats['total_validated'] > 0:
            logger.info(f"驗證代理數: {stats['total_validated']}")
            logger.info(f"可用代理數: {stats['total_working']}")
            success_rate = (stats['total_working'] / stats['total_validated']) * 100
            logger.info(f"成功率: {success_rate:.1f}%")
        
        logger.info(f"總耗時: {stats.get('end_time', 0) - stats.get('start_time', 0):.2f}s")
        
        # 顯示按源統計
        if stats['by_source']:
            logger.info(f"\n按源統計:")
            for source, info in stats['by_source'].items():
                if 'error' in info:
                    logger.warning(f"  {source}: 錯誤 - {info['error']}")
                else:
                    logger.info(f"  {source}: {info['count']} 個代理")
        
        # 顯示輸出文件
        if result['output_files']:
            logger.info(f"\n輸出文件:")
            for format_type, file_path in result['output_files'].items():
                logger.info(f"  {format_type.upper()}: {file_path}")
        
        return stats['total_unique'] > 0
        
    except Exception as e:
        logger.error(f"測試爬蟲管理器時發生錯誤: {str(e)}")
        return False


async def run_tests(args):
    """運行所有測試
    
    Args:
        args: 命令行參數
    """
    logger.info("開始代理爬蟲系統測試...")
    
    test_results = []
    
    # 測試單個爬蟲
    if args.source:
        # 只測試指定的源
        result = await test_single_crawler(args.source, limit=5)
        test_results.append((f"單個爬蟲測試 ({args.source})", result))
    else:
        # 測試所有爬蟲
        for crawler_name in ['sslproxies', 'geonode', 'free_proxy_list']:
            result = await test_single_crawler(crawler_name, limit=3)
            test_results.append((f"單個爬蟲測試 ({crawler_name})", result))
    
    # 測試代理驗證器（除非是快速模式）
    if not args.quick:
        result = await test_proxy_validator(proxies_to_test=3)
        test_results.append(("代理驗證器測試", result))
    
    # 測試爬蟲管理器
    sources = [args.source] if args.source else None
    result = await test_crawler_manager(
        args,
        enable_validation=not args.quick,
        sources=sources
    )
    test_results.append(("爬蟲管理器測試", result))
    
    # 顯示測試總結
    logger.info(f"\n=== 測試總結 ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        logger.info("🎉 所有測試都通過了！代理爬蟲系統運行正常。")
        return 0
    else:
        logger.warning(f"⚠️  有 {total - passed} 個測試失敗，請檢查系統配置。")
        return 1


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="代理爬蟲系統測試工具")
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速測試模式，跳過代理驗證"
    )
    
    parser.add_argument(
        "--source",
        choices=['sslproxies', 'geonode', 'free_proxy_list'],
        help="只測試指定的代理源"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="啟用詳細日誌輸出"
    )
    
    parser.add_argument(
        "--etl-mode",
        action="store_true",
        help="啟用ETL模式，按照ETL流程規範存放檔案"
    )
    
    args = parser.parse_args()
    
    # 設置日誌
    setup_logging(args.verbose)
    
    # 運行測試
    try:
        exit_code = asyncio.run(run_tests(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("\n用戶中斷測試")
        sys.exit(130)
    except Exception as e:
        logger.error(f"測試運行失敗: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()