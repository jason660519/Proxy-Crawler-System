#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一服務器啟動腳本

此腳本用於啟動代理管理系統的所有服務，包括：
- 主 API 服務器 (端口 8000)
- ETL API 服務器 (端口 8001)
- 監控儀表板 (端口 8002)

作者: Assistant
創建時間: 2024
"""

import asyncio
import multiprocessing
import signal
import sys
import time
from pathlib import Path
from typing import List, Optional

import uvicorn
from loguru import logger

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 導入配置加載器
try:
    from src.config.config_loader import get_config, AppConfig
    CONFIG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ 無法導入配置加載器: {e}")
    CONFIG_AVAILABLE = False


class ServerManager:
    """服務器管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化服務器管理器
        
        Args:
            config_path: 配置文件路徑
        """
        self.processes: List[multiprocessing.Process] = []
        self.running = False
        self.config: Optional[AppConfig] = None
        
        # 加載配置
        if CONFIG_AVAILABLE:
            try:
                self.config = get_config()
                logger.info("✅ 配置加載成功")
            except Exception as e:
                logger.error(f"❌ 配置加載失敗: {e}")
                self.config = None
        
        # 配置日誌
        self._setup_logging()
    
    def _setup_logging(self):
        """設置日誌配置"""
        logger.remove()
        
        # 控制台日誌
        if self.config and hasattr(self.config, 'logging'):
            log_config = self.config.logging
            if log_config.console.enabled:
                logger.add(
                    sys.stdout,
                    format=log_config.format,
                    level=log_config.level,
                    colorize=log_config.console.colorize
                )
            
            # 文件日誌
            if log_config.file.enabled:
                # 確保日誌目錄存在
                Path(log_config.file.path).mkdir(exist_ok=True)
                
                logger.add(
                    f"{log_config.file.path}/servers.log",
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                    level="DEBUG",
                    rotation=log_config.file.rotation,
                    retention=log_config.file.retention,
                    compression=log_config.file.compression
                )
        else:
            # 默認日誌配置
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level="INFO"
            )
            logger.add(
                "logs/servers.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level="DEBUG",
                rotation="1 day",
                retention="7 days"
            )
    
    def start_main_api_server(self, host: str = "0.0.0.0", port: int = 8000):
        """啟動主 API 服務器"""
        try:
            logger.info(f"🚀 啟動主 API 服務器 - {host}:{port}")
            uvicorn.run(
                "src.proxy_manager.api:app",
                host=host,
                port=port,
                log_level="info",
                access_log=True,
                reload=False
            )
        except Exception as e:
            logger.error(f"❌ 主 API 服務器啟動失敗: {e}")
            raise
    
    def start_etl_api_server(self, host: str = "0.0.0.0", port: int = 8001):
        """啟動 ETL API 服務器"""
        try:
            logger.info(f"🚀 啟動 ETL API 服務器 - {host}:{port}")
            uvicorn.run(
                "etl.etl_api:etl_app",
                host=host,
                port=port,
                log_level="info",
                access_log=True,
                reload=False
            )
        except Exception as e:
            logger.error(f"❌ ETL API 服務器啟動失敗: {e}")
            raise
    
    def start_monitoring_dashboard(self, host: str = "0.0.0.0", port: int = 8002):
        """啟動監控儀表板服務器"""
        try:
            logger.info(f"🚀 啟動監控儀表板服務器 - {host}:{port}")
            # 這裡可以啟動監控儀表板的 Web 服務器
            # 目前先用一個簡單的佔位符
            import time
            while True:
                time.sleep(1)
        except Exception as e:
            logger.error(f"❌ 監控儀表板服務器啟動失敗: {e}")
            raise
    
    def start_api_servers(self, host: Optional[str] = None, main_api_port: Optional[int] = None, etl_api_port: Optional[int] = None):
        """只啟動 API 服務器（不包括監控儀表板）"""
        try:
            # 從配置文件獲取設定，如果沒有則使用默認值
            if self.config:
                actual_host = host or self.config.server.host
                actual_main_port = main_api_port or self.config.main_api.port
                actual_etl_port = etl_api_port or self.config.etl_api.port
            else:
                actual_host = host or "0.0.0.0"
                actual_main_port = main_api_port or 8000
                actual_etl_port = etl_api_port or 8001
            
            logger.info("🚀 啟動 API 服務器...")
            logger.info(f"📡 主機地址: {actual_host}")
            logger.info(f"🔧 主 API 端口: {actual_main_port}")
            logger.info(f"📊 ETL API 端口: {actual_etl_port}")
            
            # 創建日誌目錄
            if self.config and hasattr(self.config, 'logging'):
                Path(self.config.logging.file.path).mkdir(exist_ok=True)
            else:
                Path("logs").mkdir(exist_ok=True)
            
            # 啟動主 API 服務器
            main_api_process = multiprocessing.Process(
                target=self.start_main_api_server,
                args=(actual_host, actual_main_port),
                name="MainAPI"
            )
            main_api_process.start()
            self.processes.append(main_api_process)
            logger.info(f"✅ 主 API 服務器進程已啟動 (PID: {main_api_process.pid})")
            
            # 等待一下確保主服務器啟動
            time.sleep(2)
            
            # 啟動 ETL API 服務器
            etl_api_process = multiprocessing.Process(
                target=self.start_etl_api_server,
                args=(actual_host, actual_etl_port),
                name="ETL_API"
            )
            etl_api_process.start()
            self.processes.append(etl_api_process)
            logger.info(f"✅ ETL API 服務器進程已啟動 (PID: {etl_api_process.pid})")
            
            self.running = True
            
            # 顯示服務信息（不包括監控）
            logger.info("\n" + "="*60)
            logger.info("🎯 代理管理系統 API 服務已啟動")
            logger.info("="*60)
            logger.info(f"📡 主 API 服務: http://{actual_host}:{actual_main_port}")
            logger.info(f"📊 ETL API 服務: http://{actual_host}:{actual_etl_port}")
            logger.info(f"📚 API 文檔: http://{actual_host}:{actual_main_port}/docs")
            logger.info("="*60)
            logger.info("💡 按 Ctrl+C 停止所有服務")
            logger.info("="*60 + "\n")
            
            # 設置信號處理
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # 監控進程狀態
            self.monitor_processes()
            
        except Exception as e:
            logger.error(f"❌ 啟動 API 服務器失敗: {e}")
            self.stop_all_servers()
            raise
    
    def start_all_servers(
        self,
        main_api_port: Optional[int] = None,
        etl_api_port: Optional[int] = None,
        monitoring_port: Optional[int] = None,
        host: Optional[str] = None
    ):
        """啟動所有服務器"""
        try:
            # 從配置文件獲取設定，如果沒有則使用默認值
            if self.config:
                actual_host = host or self.config.server.host
                actual_main_port = main_api_port or self.config.main_api.port
                actual_etl_port = etl_api_port or self.config.etl_api.port
                actual_monitoring_port = monitoring_port or self.config.monitoring.port
            else:
                actual_host = host or "0.0.0.0"
                actual_main_port = main_api_port or 8000
                actual_etl_port = etl_api_port or 8001
                actual_monitoring_port = monitoring_port or 8002
            
            logger.info("🌟 啟動代理管理系統所有服務...")
            logger.info(f"📡 主機地址: {actual_host}")
            logger.info(f"🔧 主 API 端口: {actual_main_port}")
            logger.info(f"📊 ETL API 端口: {actual_etl_port}")
            logger.info(f"📈 監控端口: {actual_monitoring_port}")
            
            # 創建日誌目錄
            if self.config and hasattr(self.config, 'logging'):
                Path(self.config.logging.file.path).mkdir(exist_ok=True)
            else:
                Path("logs").mkdir(exist_ok=True)
            
            # 啟動主 API 服務器
            main_api_process = multiprocessing.Process(
                target=self.start_main_api_server,
                args=(actual_host, actual_main_port),
                name="MainAPI"
            )
            main_api_process.start()
            self.processes.append(main_api_process)
            logger.info(f"✅ 主 API 服務器進程已啟動 (PID: {main_api_process.pid})")
            
            # 等待一下確保主服務器啟動
            time.sleep(2)
            
            # 啟動 ETL API 服務器
            etl_api_process = multiprocessing.Process(
                target=self.start_etl_api_server,
                args=(actual_host, actual_etl_port),
                name="ETL_API"
            )
            etl_api_process.start()
            self.processes.append(etl_api_process)
            logger.info(f"✅ ETL API 服務器進程已啟動 (PID: {etl_api_process.pid})")
            
            # 等待一下
            time.sleep(2)
            
            # 啟動監控儀表板（可選）
            monitoring_process = multiprocessing.Process(
                target=self.start_monitoring_dashboard,
                args=(actual_host, actual_monitoring_port),
                name="Monitoring"
            )
            monitoring_process.start()
            self.processes.append(monitoring_process)
            logger.info(f"✅ 監控儀表板進程已啟動 (PID: {monitoring_process.pid})")
            
            self.running = True
            
            # 顯示服務信息
            self.show_service_info(actual_main_port, actual_etl_port, actual_monitoring_port, actual_host)
            
            # 設置信號處理
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # 監控進程狀態
            self.monitor_processes()
            
        except Exception as e:
            logger.error(f"❌ 啟動服務器失敗: {e}")
            self.stop_all_servers()
            raise
    
    def show_service_info(
        self,
        main_api_port: int,
        etl_api_port: int,
        monitoring_port: int,
        host: str
    ):
        """顯示服務信息"""
        logger.info("\n" + "="*60)
        logger.info("🎉 代理管理系統服務已啟動")
        logger.info("="*60)
        logger.info(f"📡 主 API 服務器:     http://{host}:{main_api_port}")
        logger.info(f"📊 API 文檔:          http://{host}:{main_api_port}/docs")
        logger.info(f"🔧 ETL API 服務器:    http://{host}:{etl_api_port}")
        logger.info(f"📋 ETL API 文檔:      http://{host}:{etl_api_port}/docs")
        logger.info(f"📈 監控儀表板:        http://{host}:{monitoring_port}")
        logger.info("="*60)
        logger.info("💡 使用 Ctrl+C 停止所有服務")
        logger.info("="*60 + "\n")
    
    def monitor_processes(self):
        """監控進程狀態"""
        try:
            while self.running:
                time.sleep(5)
                
                # 檢查進程狀態
                for process in self.processes:
                    if not process.is_alive():
                        logger.warning(f"⚠️ 進程 {process.name} (PID: {process.pid}) 已停止")
                        
                        # 可以在這裡添加自動重啟邏輯
                        # self.restart_process(process)
                
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信號，正在關閉所有服務...")
            self.stop_all_servers()
    
    def stop_all_servers(self):
        """停止所有服務器"""
        try:
            logger.info("🛑 正在停止所有服務器...")
            self.running = False
            
            for process in self.processes:
                if process.is_alive():
                    logger.info(f"🔄 停止進程 {process.name} (PID: {process.pid})")
                    process.terminate()
                    
                    # 等待進程優雅關閉
                    process.join(timeout=5)
                    
                    # 如果進程仍在運行，強制終止
                    if process.is_alive():
                        logger.warning(f"⚠️ 強制終止進程 {process.name}")
                        process.kill()
                        process.join()
            
            self.processes.clear()
            logger.info("✅ 所有服務器已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止服務器時發生錯誤: {e}")
    
    def _signal_handler(self, signum, frame):
        """信號處理器"""
        logger.info(f"🔔 收到信號 {signum}，正在關閉服務...")
        self.stop_all_servers()
        sys.exit(0)


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="代理管理系統服務器啟動器")
    parser.add_argument(
        "--config",
        "-c",
        help="配置文件路徑 (YAML 格式)"
    )
    parser.add_argument(
        "--host",
        help="服務器主機地址 (覆蓋配置文件設定)"
    )
    parser.add_argument(
        "--main-port",
        type=int,
        help="主 API 服務器端口 (覆蓋配置文件設定)"
    )
    parser.add_argument(
        "--etl-port",
        type=int,
        help="ETL API 服務器端口 (覆蓋配置文件設定)"
    )
    parser.add_argument(
        "--monitoring-port",
        type=int,
        help="監控儀表板端口 (覆蓋配置文件設定)"
    )
    parser.add_argument(
        "--single",
        choices=["main", "etl", "monitoring"],
        help="只啟動單個服務"
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="創建默認配置文件並退出"
    )
    
    args = parser.parse_args()
    
    # 如果要求創建配置文件
    if args.create_config:
        config_path = args.config or "config/server_config.yaml"
        if CONFIG_AVAILABLE:
            try:
                from src.config.config_loader import ConfigLoader
                ConfigLoader.create_default_config(config_path)
                print(f"✅ 默認配置文件已創建: {config_path}")
                return
            except Exception as e:
                print(f"❌ 創建配置文件失敗: {e}")
                return
        else:
            print("❌ 配置加載器不可用，無法創建配置文件")
            return
    
    server_manager = ServerManager(config_path=args.config)
    
    try:
        if args.single:
            # 啟動單個服務
            if args.single == "main":
                host = args.host or "0.0.0.0"
                port = args.main_port or 8000
                server_manager.start_main_api_server(host, port)
            elif args.single == "etl":
                host = args.host or "0.0.0.0"
                port = args.etl_port or 8001
                server_manager.start_etl_api_server(host, port)
            elif args.single == "monitoring":
                host = args.host or "0.0.0.0"
                port = args.monitoring_port or 8002
                server_manager.start_monitoring_dashboard(host, port)
        else:
            # 啟動所有服務
            server_manager.start_all_servers(
                main_api_port=args.main_port,
                etl_api_port=args.etl_port,
                monitoring_port=args.monitoring_port,
                host=args.host
            )
    
    except KeyboardInterrupt:
        logger.info("👋 用戶中斷，正在退出...")
        server_manager.stop_all_servers()
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}")
        server_manager.stop_all_servers()
        sys.exit(1)


if __name__ == "__main__":
    # 設置多進程啟動方法
    multiprocessing.set_start_method('spawn', force=True)
    main()