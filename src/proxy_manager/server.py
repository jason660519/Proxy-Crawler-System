#!/usr/bin/env python3
"""代理管理器服務啟動腳本

提供便捷的服務啟動方式，支持不同的運行模式：
- 開發模式：自動重載，詳細日誌
- 生產模式：優化性能，簡潔日誌
- 調試模式：最詳細的日誌輸出
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from loguru import logger

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.proxy_manager.api import app
from src.proxy_manager.manager import ProxyManagerConfig


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """設置日誌配置
    
    Args:
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日誌文件路徑，None 表示只輸出到控制台
    """
    # 移除默認的 loguru 處理器
    logger.remove()
    
    # 設置控制台日誌格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 添加控制台處理器
    logger.add(
        sys.stderr,
        format=console_format,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 如果指定了日誌文件，添加文件處理器
    if log_file:
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        )
        
        logger.add(
            log_file,
            format=file_format,
            level=level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    # 設置標準庫日誌級別
    logging.getLogger("uvicorn").setLevel(getattr(logging, level))
    logging.getLogger("uvicorn.access").setLevel(getattr(logging, level))


def create_data_directories():
    """創建必要的數據目錄"""
    directories = [
        "data/proxy_manager",
        "data/exports",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 確保目錄存在: {directory}")


def validate_environment():
    """驗證運行環境"""
    logger.info("🔍 驗證運行環境...")
    
    # 檢查 Python 版本
    if sys.version_info < (3, 8):
        logger.error("❌ Python 版本過低，需要 3.8 或更高版本")
        sys.exit(1)
    
    logger.info(f"✅ Python 版本: {sys.version}")
    
    # 檢查必要的依賴
    try:
        import fastapi
        import uvicorn
        import aiohttp
        import loguru
        logger.info("✅ 核心依賴檢查通過")
    except ImportError as e:
        logger.error(f"❌ 缺少必要依賴: {e}")
        logger.error("請運行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 創建數據目錄
    create_data_directories()
    
    logger.info("✅ 環境驗證完成")


def print_banner():
    """打印啟動橫幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                     🌐 代理管理器服務                        ║
║                   Proxy Manager Service                     ║
╠══════════════════════════════════════════════════════════════╣
║  版本: 1.0.0                                                ║
║  作者: Jason Spider Team                                     ║
║  描述: 智能代理獲取、驗證和管理系統                           ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_startup_info(host: str, port: int, mode: str):
    """打印啟動信息"""
    logger.info("🚀 代理管理器服務啟動中...")
    logger.info(f"📍 運行模式: {mode}")
    logger.info(f"🌐 服務地址: http://{host}:{port}")
    logger.info(f"📚 API 文檔: http://{host}:{port}/api/docs")
    logger.info(f"🎛️  管理界面: http://{host}:{port}/")
    logger.info(f"❤️  健康檢查: http://{host}:{port}/api/health")
    logger.info("" + "="*60)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="代理管理器服務啟動腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python server.py                          # 開發模式啟動
  python server.py --mode production        # 生產模式啟動
  python server.py --host 0.0.0.0 --port 8080  # 自定義地址和端口
  python server.py --debug                  # 調試模式啟動
        """
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="服務器主機地址 (默認: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服務器端口 (默認: 8000)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["development", "production", "debug"],
        default="development",
        help="運行模式 (默認: development)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日誌級別 (默認根據模式自動選擇)"
    )
    
    parser.add_argument(
        "--log-file",
        help="日誌文件路徑 (可選)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作進程數量 (僅生產模式，默認: 1)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="啟用自動重載 (開發模式)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="啟用調試模式 (等同於 --mode debug --log-level DEBUG)"
    )
    
    args = parser.parse_args()
    
    # 處理調試模式
    if args.debug:
        args.mode = "debug"
        args.log_level = "DEBUG"
        args.reload = True
    
    # 根據模式設置默認日誌級別
    if not args.log_level:
        if args.mode == "debug":
            args.log_level = "DEBUG"
        elif args.mode == "development":
            args.log_level = "INFO"
        else:  # production
            args.log_level = "WARNING"
    
    # 設置日誌文件
    log_file = args.log_file
    if not log_file and args.mode == "production":
        log_file = "logs/proxy_manager.log"
    
    # 設置日誌
    setup_logging(args.log_level, log_file)
    
    # 打印橫幅
    print_banner()
    
    # 驗證環境
    validate_environment()
    
    # 打印啟動信息
    print_startup_info(args.host, args.port, args.mode)
    
    # 設置 uvicorn 配置
    uvicorn_config = {
        "app": "src.proxy_manager.api:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.lower(),
    }
    
    # 根據模式調整配置
    if args.mode == "development" or args.mode == "debug":
        uvicorn_config.update({
            "reload": args.reload or True,
            "reload_dirs": ["src"],
            "access_log": True,
        })
    elif args.mode == "production":
        uvicorn_config.update({
            "workers": args.workers,
            "access_log": False,
            "reload": False,
        })
    
    try:
        # 啟動服務器
        logger.info("🎯 正在啟動 uvicorn 服務器...")
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 收到中斷信號，正在關閉服務...")
    except Exception as e:
        logger.error(f"❌ 服務啟動失敗: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 代理管理器服務已關閉")


if __name__ == "__main__":
    main()