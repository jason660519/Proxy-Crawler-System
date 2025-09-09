#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy Crawler System - 主啟動腳本

這是代理爬蟲系統的主要啟動腳本，提供了多種啟動模式和配置選項。

使用方式：
    python main.py --mode quick                    # 快速啟動模式
    python main.py --mode full --config config.yaml  # 完整模式
    python main.py --mode demo                     # 演示模式
    python main.py --mode test                     # 測試模式
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# 添加src目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 導入系統模組
from src import (
    create_system,
    quick_start,
    get_system_status,
    health_check,
    cleanup,
    SystemIntegrator,
    Config,
    load_config,
    get_config
)

from src.optimization import OptimizationLevel
from src.monitoring import setup_monitoring


class ProxyCrawlerSystemLauncher:
    """代理爬蟲系統啟動器"""
    
    def __init__(self):
        self.system: Optional[SystemIntegrator] = None
        self.logger = logging.getLogger(__name__)
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """設置信號處理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信號處理函數"""
        self.logger.info(f"接收到信號 {signum}，正在關閉系統...")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """關閉系統"""
        if self.system:
            try:
                await self.system.stop()
                self.logger.info("系統已正常關閉")
            except Exception as e:
                self.logger.error(f"關閉系統時發生錯誤: {e}")
        
        await cleanup()
        sys.exit(0)
    
    async def quick_mode(self, args):
        """快速啟動模式"""
        self.logger.info("啟動快速模式...")
        
        # 設置基本的代理源
        proxy_sources = [
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://api.proxyscrape.com/v2/?request=get&protocol=http"
        ]
        
        self.system = await quick_start(
            proxy_sources=proxy_sources,
            redis_url=args.redis_url,
            api_port=args.port,
            enable_web_ui=True
        )
        
        self.logger.info(f"系統已啟動，API服務運行在端口 {args.port}")
        
        # 保持運行
        await self._keep_running()
    
    async def full_mode(self, args):
        """完整啟動模式"""
        self.logger.info("啟動完整模式...")
        
        # 載入配置
        if args.config:
            config = load_config(args.config)
        else:
            config = get_config()
        
        # 設置優化級別
        optimization_level = {
            "conservative": "conservative",
            "balanced": "balanced",
            "aggressive": "aggressive"
        }.get(args.optimization, "balanced")
        
        # 創建系統
        self.system = await create_system(
            config_path=args.config,
            optimization_level=optimization_level,
            enable_monitoring=args.enable_monitoring,
            enable_optimization=args.enable_optimization
        )
        
        # 啟動系統
        await self.system.start()
        
        self.logger.info("完整系統已啟動")
        
        # 顯示系統狀態
        await self._show_system_status()
        
        # 保持運行
        await self._keep_running()
    
    async def demo_mode(self, args):
        """演示模式"""
        self.logger.info("啟動演示模式...")
        
        # 創建演示配置
        config = Config()
        config.crawlers.sources = [
            "https://www.proxy-list.download/api/v1/get?type=http"
        ]
        config.crawlers.max_concurrent = 5
        config.validators.timeout = 10
        config.redis.url = args.redis_url
        config.api.port = args.port
        
        # 創建系統
        self.system = await create_system(
            config_path=None,
            optimization_level="balanced",
            enable_monitoring=True,
            enable_optimization=True
        )
        
        # 啟動系統
        await self.system.start()
        
        self.logger.info("演示系統已啟動")
        
        # 運行演示流程
        await self._run_demo()
        
        # 保持運行
        await self._keep_running()
    
    async def test_mode(self, args):
        """測試模式"""
        self.logger.info("啟動測試模式...")
        
        # 運行系統測試
        from tests.test_integration import main as run_integration_tests
        
        try:
            await run_integration_tests()
            self.logger.info("所有測試通過")
        except Exception as e:
            self.logger.error(f"測試失敗: {e}")
            sys.exit(1)
    
    async def _run_demo(self):
        """運行演示流程"""
        self.logger.info("開始演示流程...")
        
        try:
            # 1. 顯示系統狀態
            status = await get_system_status()
            self.logger.info(f"系統狀態: {status['system_performance']['cpu']['percent']:.1f}% CPU, "
                           f"{status['system_performance']['memory']['percent']:.1f}% 記憶體")
            
            # 2. 健康檢查
            health = await health_check()
            self.logger.info(f"健康檢查: {health['status']}")
            
            # 3. 啟動代理爬取（模擬）
            self.logger.info("開始爬取代理...")
            await asyncio.sleep(2)  # 模擬爬取時間
            
            # 4. 代理驗證（模擬）
            self.logger.info("開始驗證代理...")
            await asyncio.sleep(3)  # 模擬驗證時間
            
            # 5. 顯示結果
            self.logger.info("演示完成！系統正在運行中...")
            
        except Exception as e:
            self.logger.error(f"演示過程中發生錯誤: {e}")
    
    async def _show_system_status(self):
        """顯示系統狀態"""
        try:
            status = await get_system_status()
            
            print("\n" + "="*50)
            print("系統狀態")
            print("="*50)
            print(f"版本: {status.get('version', 'Unknown')}")
            
            # CPU信息
            cpu = status['system_performance']['cpu']
            print(f"CPU: {cpu['percent']:.1f}% ({cpu['count']} 核心)")
            
            # 記憶體信息
            memory = status['system_performance']['memory']
            memory_gb = memory['total'] / (1024**3)
            used_gb = memory['used'] / (1024**3)
            print(f"記憶體: {memory['percent']:.1f}% ({used_gb:.1f}GB / {memory_gb:.1f}GB)")
            
            # 磁碟信息
            disk = status['system_performance']['disk']
            if disk['total'] > 0:
                disk_gb = disk['total'] / (1024**3)
                used_disk_gb = disk['used'] / (1024**3)
                print(f"磁碟: {disk['percent']:.1f}% ({used_disk_gb:.1f}GB / {disk_gb:.1f}GB)")
            
            print("="*50 + "\n")
            
        except Exception as e:
            self.logger.error(f"無法獲取系統狀態: {e}")
    
    async def _keep_running(self):
        """保持系統運行"""
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.shutdown()


def setup_logging(level: str = "INFO"):
    """設置日誌"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('proxy_crawler_system.log', encoding='utf-8')
        ]
    )


def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(
        description="Proxy Crawler System - 代理爬蟲系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python main.py --mode quick                    # 快速啟動
  python main.py --mode full --config config.yaml  # 使用配置文件
  python main.py --mode demo                     # 演示模式
  python main.py --mode test                     # 測試模式
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "demo", "test"],
        default="quick",
        help="啟動模式 (默認: quick)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路徑"
    )
    
    parser.add_argument(
        "--redis-url",
        type=str,
        default="redis://localhost:6379",
        help="Redis連接URL (默認: redis://localhost:6379)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API服務端口 (默認: 8000)"
    )
    
    parser.add_argument(
        "--optimization",
        choices=["conservative", "balanced", "aggressive"],
        default="balanced",
        help="性能優化級別 (默認: balanced)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日誌級別 (默認: INFO)"
    )
    
    parser.add_argument(
        "--enable-monitoring",
        action="store_true",
        default=True,
        help="啟用系統監控"
    )
    
    parser.add_argument(
        "--enable-optimization",
        action="store_true",
        default=True,
        help="啟用性能優化"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Proxy Crawler System 1.0.0"
    )
    
    return parser.parse_args()


async def main():
    """主函數"""
    # 解析參數
    args = parse_arguments()
    
    # 設置日誌
    setup_logging(args.log_level)
    
    # 創建啟動器
    launcher = ProxyCrawlerSystemLauncher()
    
    try:
        # 根據模式啟動
        if args.mode == "quick":
            await launcher.quick_mode(args)
        elif args.mode == "full":
            await launcher.full_mode(args)
        elif args.mode == "demo":
            await launcher.demo_mode(args)
        elif args.mode == "test":
            await launcher.test_mode(args)
        
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("接收到中斷信號，正在關閉...")
    except Exception as e:
        logging.getLogger(__name__).error(f"啟動失敗: {e}")
        sys.exit(1)
    finally:
        await launcher.shutdown()


if __name__ == "__main__":
    # 檢查Python版本
    if sys.version_info < (3, 8):
        print("錯誤: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 運行主函數
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已中斷")
    except Exception as e:
        print(f"程序執行失敗: {e}")
        sys.exit(1)