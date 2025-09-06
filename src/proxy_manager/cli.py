"""代理爬蟲命令行介面

提供簡單易用的命令行工具來運行代理爬蟲系統

使用範例:
    python -m proxy_manager.cli --sources sslproxies geonode --validate --output json markdown
    python -m proxy_manager.cli --all-sources --no-validate --output csv
    python -m proxy_manager.cli --list-crawlers
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from loguru import logger

from .crawler_manager import CrawlerManager


def setup_logging(verbose: bool = False):
    """設置日誌記錄
    
    Args:
        verbose: 是否啟用詳細日誌
    """
    logger.remove()  # 移除默認處理器
    
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


def create_parser() -> argparse.ArgumentParser:
    """創建命令行參數解析器
    
    Returns:
        配置好的參數解析器
    """
    parser = argparse.ArgumentParser(
        description="代理爬蟲管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s --sources sslproxies geonode --validate --output json markdown
  %(prog)s --all-sources --no-validate --output csv
  %(prog)s --list-crawlers
  %(prog)s --sources free_proxy_list --timeout 15 --concurrent 30
"""
    )
    
    # 基本選項
    parser.add_argument(
        "--sources",
        nargs="+",
        help="指定要爬取的代理源 (sslproxies, geonode, free_proxy_list)"
    )
    
    parser.add_argument(
        "--all-sources",
        action="store_true",
        help="爬取所有可用的代理源"
    )
    
    parser.add_argument(
        "--list-crawlers",
        action="store_true",
        help="列出所有可用的爬蟲並退出"
    )
    
    # 驗證選項
    validation_group = parser.add_mutually_exclusive_group()
    validation_group.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="啟用代理驗證 (默認)"
    )
    
    validation_group.add_argument(
        "--no-validate",
        action="store_true",
        help="禁用代理驗證"
    )
    
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="驗證超時時間 (秒，默認: 10.0)"
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=50,
        help="最大並發驗證數 (默認: 50)"
    )
    
    # 輸出選項
    parser.add_argument(
        "--output",
        nargs="+",
        choices=["json", "markdown", "csv"],
        default=["json", "markdown"],
        help="輸出格式 (默認: json markdown)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="輸出目錄 (默認: data/proxy_manager)"
    )
    
    # 其他選項
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="禁用代理去重"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="啟用詳細日誌輸出"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="靜默模式，只輸出錯誤信息"
    )
    
    return parser


async def run_crawler_manager(args: argparse.Namespace) -> int:
    """運行爬蟲管理器
    
    Args:
        args: 命令行參數
        
    Returns:
        退出代碼 (0表示成功)
    """
    try:
        # 創建管理器
        manager = CrawlerManager(
            output_dir=args.output_dir,
            enable_validation=not args.no_validate,
            validation_timeout=args.timeout,
            max_concurrent_validation=args.concurrent,
            enable_deduplication=not args.no_dedup
        )
        
        # 列出爬蟲
        if args.list_crawlers:
            crawlers = manager.list_available_crawlers()
            logger.info("可用的代理爬蟲:")
            for crawler in crawlers:
                logger.info(f"  - {crawler}")
            return 0
        
        # 確定要爬取的源
        sources = None
        if args.all_sources:
            sources = None  # 使用所有源
            logger.info("將爬取所有可用的代理源")
        elif args.sources:
            sources = args.sources
            logger.info(f"將爬取指定的代理源: {', '.join(sources)}")
        else:
            logger.error("請指定 --sources 或 --all-sources")
            return 1
        
        # 驗證源名稱
        if sources:
            available_crawlers = manager.list_available_crawlers()
            invalid_sources = [s for s in sources if s not in available_crawlers]
            if invalid_sources:
                logger.error(f"無效的代理源: {', '.join(invalid_sources)}")
                logger.error(f"可用的源: {', '.join(available_crawlers)}")
                return 1
        
        # 運行爬蟲
        logger.info("開始代理爬取任務...")
        result = await manager.crawl_all_sources(
            sources=sources,
            validate_proxies=not args.no_validate,
            output_formats=args.output
        )
        
        # 顯示結果摘要
        stats = result['stats']
        logger.info("\n=== 爬取結果摘要 ===")
        logger.info(f"總爬取代理數: {stats['total_crawled']}")
        logger.info(f"去重後代理數: {stats['total_unique']}")
        
        if stats['total_validated'] > 0:
            logger.info(f"驗證代理數: {stats['total_validated']}")
            logger.info(f"可用代理數: {stats['total_working']}")
            success_rate = (stats['total_working'] / stats['total_validated']) * 100
            logger.info(f"成功率: {success_rate:.1f}%")
        
        logger.info(f"總耗時: {stats.get('end_time', 0) - stats.get('start_time', 0):.2f}s")
        
        # 顯示輸出文件
        if result['output_files']:
            logger.info("\n=== 輸出文件 ===")
            for format_type, file_path in result['output_files'].items():
                logger.info(f"{format_type.upper()}: {file_path}")
        
        # 顯示按源統計
        if stats['by_source']:
            logger.info("\n=== 按源統計 ===")
            for source, info in stats['by_source'].items():
                if 'error' in info:
                    logger.warning(f"{source}: 錯誤 - {info['error']}")
                else:
                    logger.info(f"{source}: {info['count']} 個代理")
        
        logger.info("\n代理爬取任務完成!")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n用戶中斷操作")
        return 130
    except Exception as e:
        logger.error(f"運行時發生錯誤: {str(e)}")
        if args.verbose:
            logger.exception("詳細錯誤信息:")
        return 1


def main() -> int:
    """主函數
    
    Returns:
        退出代碼
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # 設置日誌
    if args.quiet:
        logger.remove()
        logger.add(sys.stderr, level="ERROR")
    else:
        setup_logging(args.verbose)
    
    # 運行異步任務
    try:
        return asyncio.run(run_crawler_manager(args))
    except KeyboardInterrupt:
        logger.warning("\n用戶中斷操作")
        return 130
    except Exception as e:
        logger.error(f"程序啟動失敗: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())