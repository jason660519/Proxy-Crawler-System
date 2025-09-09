#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy Crawler System - 快速啟動腳本

這個腳本提供了一個簡化的啟動方式，自動處理依賴檢查、環境設置和系統初始化。
適合快速測試和開發使用。

使用方法：
    python start.py                    # 快速啟動模式
    python start.py --mode full        # 完整功能模式
    python start.py --mode demo        # 演示模式
    python start.py --help             # 顯示幫助信息
"""

import sys
import os
import asyncio
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
except ImportError:
    print("正在安裝必要的依賴...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

console = Console()


class QuickStarter:
    """快速啟動器類"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_path = self.project_root / "src"
        self.config_path = self.project_root / "config"
        self.logs_path = self.project_root / "logs"
        
    def check_dependencies(self) -> bool:
        """檢查必要的依賴是否已安裝"""
        required_packages = [
            "fastapi", "uvicorn", "aiohttp", "redis", "pydantic",
            "loguru", "typer", "rich", "psutil"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            console.print(f"[red]缺少以下依賴包: {', '.join(missing_packages)}[/red]")
            console.print("[yellow]請運行以下命令安裝依賴:[/yellow]")
            console.print(f"[cyan]pip install {' '.join(missing_packages)}[/cyan]")
            return False
        
        return True
    
    def check_redis_connection(self, skip_redis: bool = False) -> bool:
        """檢查 Redis 連接"""
        if skip_redis:
            console.print("[yellow]⚠️  跳過 Redis 檢查（演示模式）[/yellow]")
            return True
            
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
            r.ping()
            return True
        except Exception as e:
            console.print(f"[red]Redis 連接失敗: {e}[/red]")
            console.print("[yellow]請確保 Redis 服務正在運行[/yellow]")
            console.print("[cyan]Windows: 下載並啟動 Redis[/cyan]")
            console.print("[cyan]Linux/Mac: sudo systemctl start redis[/cyan]")
            console.print("[cyan]Docker: docker run -d -p 6379:6379 redis:alpine[/cyan]")
            return False
    
    def setup_directories(self) -> None:
        """創建必要的目錄"""
        directories = [
            self.logs_path,
            self.project_root / "data",
            self.project_root / "temp",
            self.project_root / "cache"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def create_env_file(self) -> None:
        """創建環境變量文件"""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_content = """
# Proxy Crawler System - 環境變量配置

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# 日誌配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 性能配置
MAX_CONCURRENT_TASKS=100
VALIDATION_TIMEOUT=30
RETRY_ATTEMPTS=3

# 功能開關
METRICS_ENABLED=true
MONITORING_ENABLED=true
DEBUG_MODE=false
"""
            env_file.write_text(env_content.strip())
            console.print(f"[green]已創建環境變量文件: {env_file}[/green]")
    
    def display_banner(self) -> None:
        """顯示啟動橫幅"""
        banner_text = Text()
        banner_text.append("Proxy Crawler System\n", style="bold blue")
        banner_text.append("高性能代理爬蟲和管理系統\n", style="cyan")
        banner_text.append("版本: 1.0.0", style="green")
        
        panel = Panel(
            banner_text,
            title="🚀 系統啟動",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
    
    def display_system_info(self) -> None:
        """顯示系統信息"""
        table = Table(title="系統信息")
        table.add_column("項目", style="cyan")
        table.add_column("值", style="green")
        
        table.add_row("Python 版本", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        table.add_row("項目路徑", str(self.project_root))
        table.add_row("配置路徑", str(self.config_path))
        table.add_row("日誌路徑", str(self.logs_path))
        
        console.print(table)
    
    async def start_system(self, mode: str = "quick") -> None:
        """啟動系統"""
        try:
            # 動態導入主模塊
            from main import ProxyCrawlerSystemLauncher
            
            launcher = ProxyCrawlerSystemLauncher()
            
            console.print(f"[green]正在以 '{mode}' 模式啟動系統...[/green]")
            
            # 根據模式啟動
            if mode == "quick":
                await launcher.quick_start()
            elif mode == "full":
                await launcher.full_start()
            elif mode == "demo":
                await launcher.demo_start()
            elif mode == "test":
                await launcher.test_start()
            else:
                console.print(f"[red]未知的啟動模式: {mode}[/red]")
                return
            
            console.print("[green]系統啟動完成！[/green]")
            
        except ImportError as e:
            console.print(f"[red]導入錯誤: {e}[/red]")
            console.print("[yellow]請確保所有必要的模塊都已正確安裝[/yellow]")
        except Exception as e:
            console.print(f"[red]啟動失敗: {e}[/red]")
    
    def run_checks(self, skip_redis: bool = False) -> bool:
        """運行系統檢查"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # 檢查依賴
            task1 = progress.add_task("檢查 Python 依賴...", total=None)
            if not self.check_dependencies():
                return False
            progress.update(task1, description="✅ Python 依賴檢查完成")
            
            # 檢查 Redis
            task2 = progress.add_task("檢查 Redis 連接...", total=None)
            redis_ok = self.check_redis_connection(skip_redis=skip_redis)
            if redis_ok:
                if skip_redis:
                    progress.update(task2, description="⚠️  Redis 檢查已跳過")
                else:
                    progress.update(task2, description="✅ Redis 連接正常")
            else:
                progress.update(task2, description="❌ Redis 連接失敗")
            
            # 設置目錄
            task3 = progress.add_task("創建必要目錄...", total=None)
            self.setup_directories()
            progress.update(task3, description="✅ 目錄創建完成")
            
            # 創建環境文件
            task4 = progress.add_task("檢查環境配置...", total=None)
            self.create_env_file()
            progress.update(task4, description="✅ 環境配置完成")
        
        return redis_ok or skip_redis  # 如果跳過 Redis 檢查，則認為通過
    
    async def main(self, mode: str = "quick", skip_checks: bool = False, skip_redis: bool = False) -> None:
        """主函數"""
        self.display_banner()
        
        if not skip_checks:
            console.print("\n[yellow]正在進行系統檢查...[/yellow]")
            if not self.run_checks(skip_redis=skip_redis):
                console.print("\n[red]系統檢查失敗，請解決上述問題後重試[/red]")
                return
        
        console.print("\n[green]系統檢查通過！[/green]")
        self.display_system_info()
        
        console.print("\n[yellow]正在啟動系統...[/yellow]")
        await self.start_system(mode)


def main():
    """命令行入口點"""
    parser = argparse.ArgumentParser(
        description="Proxy Crawler System 快速啟動腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
啟動模式說明：
  quick    - 快速啟動模式（默認），僅啟動核心功能
  full     - 完整功能模式，啟動所有組件
  demo     - 演示模式，包含示例數據和演示流程
  test     - 測試模式，運行系統測試

示例：
  python start.py                    # 快速啟動
  python start.py --mode full        # 完整啟動
  python start.py --mode demo        # 演示模式
  python start.py --skip-checks      # 跳過系統檢查
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "demo", "test"],
        default="quick",
        help="啟動模式（默認: quick）"
    )
    
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="跳過系統檢查（不推薦）"
    )
    
    parser.add_argument(
        "--skip-redis",
        action="store_true",
        help="跳過 Redis 連接檢查（演示模式）"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Proxy Crawler System 1.0.0"
    )
    
    args = parser.parse_args()
    
    # 創建啟動器並運行
    starter = QuickStarter()
    
    try:
        asyncio.run(starter.main(args.mode, args.skip_checks, args.skip_redis))
    except KeyboardInterrupt:
        console.print("\n[yellow]用戶中斷，正在退出...[/yellow]")
    except Exception as e:
        console.print(f"\n[red]啟動失敗: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()