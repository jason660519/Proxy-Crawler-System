#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 轉換命令行工具

這個模組提供命令行界面，讓使用者可以直接使用 HTML to Markdown 轉換功能。
支援單檔案轉換、批次處理、URL 爬取轉換等多種操作模式。

Author: JasonSpider Team
Date: 2024
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.text import Text
from loguru import logger

# 導入核心模組
from .core import ConversionConfig, ConversionEngine, ContentScope, OutputFormat
from .etl_processor import HTMLToMarkdownETLProcessor, ETLConfig
from .utils import HTMLCleaner, ContentExtractor, QualityAssessment
from . import quick_convert, batch_convert_directory

# 設置 Rich Console
console = Console()


class CLIConfig:
    """命令行配置類"""
    
    def __init__(self):
        self.verbose: bool = False
        self.output_dir: Optional[Path] = None
        self.engine: ConversionEngine = ConversionEngine.AUTO
        self.quality_threshold: float = 0.5
        self.enable_caching: bool = True
        self.max_workers: int = 4


# 全局配置實例
cli_config = CLIConfig()


def setup_logging(verbose: bool = False):
    """設置日誌配置"""
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
            format="<level>{level: <8}</level> | <level>{message}</level>",
            level="INFO"
        )


def print_banner():
    """顯示程式橫幅"""
    banner = Text()
    banner.append("\n🔄 HTML to Markdown 轉換工具\n", style="bold blue")
    banner.append("基於 LLMFeeder 技術的通用網頁內容轉換系統\n", style="dim")
    banner.append("支援多網站適配、智能內容提取、品質評估\n", style="dim")
    
    console.print(Panel(banner, border_style="blue"))


def print_conversion_result(result, source: str):
    """顯示轉換結果"""
    if result.success:
        # 成功結果
        table = Table(title=f"轉換結果 - {source}")
        table.add_column("項目", style="cyan")
        table.add_column("值", style="green")
        
        table.add_row("狀態", "✅ 成功")
        table.add_row("品質評分", f"{result.quality_score:.2f}")
        table.add_row("處理時間", f"{result.processing_time:.2f}s")
        table.add_row("內容長度", f"{len(result.markdown_content)} 字符")
        
        if hasattr(result, 'structured_data') and result.structured_data:
            if 'title' in result.structured_data:
                table.add_row("標題", result.structured_data['title'])
            if 'website' in result.structured_data:
                table.add_row("網站類型", result.structured_data['website'])
        
        console.print(table)
        
        # 顯示 Markdown 預覽（前 200 字符）
        if result.markdown_content:
            preview = result.markdown_content[:200]
            if len(result.markdown_content) > 200:
                preview += "..."
            
            console.print("\n📄 Markdown 預覽:")
            console.print(Panel(preview, border_style="green"))
    else:
        # 失敗結果
        console.print(f"❌ 轉換失敗: {result.error_message}", style="red")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='啟用詳細日誌輸出')
@click.option('--output-dir', '-o', type=click.Path(), help='輸出目錄路徑')
@click.option('--engine', '-e', 
              type=click.Choice(['auto', 'markdownify', 'trafilatura', 'html2text', 'readability']),
              default='auto', help='指定轉換引擎')
@click.option('--quality-threshold', '-q', type=float, default=0.5, help='品質評分閾值')
@click.option('--no-cache', is_flag=True, help='禁用快取')
@click.option('--max-workers', '-w', type=int, default=4, help='最大並發工作數')
def cli(verbose, output_dir, engine, quality_threshold, no_cache, max_workers):
    """HTML to Markdown 轉換工具
    
    支援單檔案轉換、批次處理、URL 爬取等多種操作模式。
    """
    setup_logging(verbose)
    
    cli_config.verbose = verbose
    cli_config.output_dir = Path(output_dir) if output_dir else None
    cli_config.engine = ConversionEngine[engine.upper()] if engine != 'auto' else ConversionEngine.AUTO
    cli_config.quality_threshold = quality_threshold
    cli_config.enable_caching = not no_cache
    cli_config.max_workers = max_workers
    
    if not verbose:
        print_banner()


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='輸出檔案路徑')
@click.option('--url', help='原始 URL（用於網站檢測）')
def convert_file(input_file, output, url):
    """轉換單個 HTML 檔案為 Markdown
    
    INPUT_FILE: 要轉換的 HTML 檔案路徑
    """
    async def _convert():
        try:
            input_path = Path(input_file)
            
            # 讀取 HTML 內容
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            console.print(f"📖 正在轉換檔案: {input_path.name}")
            
            # 執行轉換
            result = await quick_convert(
                html_content,
                url=url,
                engine=cli_config.engine,
                enable_caching=cli_config.enable_caching
            )
            
            # 顯示結果
            print_conversion_result(result, input_path.name)
            
            # 保存結果
            if output:
                output_path = Path(output)
            else:
                output_path = input_path.with_suffix('.md')
                if cli_config.output_dir:
                    output_path = cli_config.output_dir / output_path.name
            
            if result.success and result.quality_score >= cli_config.quality_threshold:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.markdown_content)
                
                console.print(f"💾 結果已保存到: {output_path}", style="green")
            else:
                console.print("⚠️  品質評分過低，未保存結果", style="yellow")
                
        except Exception as e:
            logger.error(f"轉換失敗: {str(e)}")
            console.print(f"❌ 轉換失敗: {str(e)}", style="red")
            sys.exit(1)
    
    asyncio.run(_convert())


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.option('--pattern', '-p', default='*.html', help='檔案匹配模式')
@click.option('--recursive', '-r', is_flag=True, help='遞歸處理子目錄')
def batch_convert(input_dir, pattern, recursive):
    """批次轉換目錄中的 HTML 檔案
    
    INPUT_DIR: 包含 HTML 檔案的目錄路徑
    """
    async def _batch_convert():
        try:
            input_path = Path(input_dir)
            output_dir = cli_config.output_dir or input_path / 'markdown_output'
            
            console.print(f"📁 正在批次處理目錄: {input_path}")
            console.print(f"📤 輸出目錄: {output_dir}")
            
            # 查找檔案
            if recursive:
                html_files = list(input_path.rglob(pattern))
            else:
                html_files = list(input_path.glob(pattern))
            
            if not html_files:
                console.print(f"⚠️  未找到匹配的檔案: {pattern}", style="yellow")
                return
            
            console.print(f"🔍 找到 {len(html_files)} 個檔案")
            
            # 執行批次轉換
            with Progress() as progress:
                task = progress.add_task("[green]轉換中...", total=len(html_files))
                
                results = await batch_convert_directory(
                    str(input_path),
                    str(output_dir),
                    file_pattern=pattern,
                    recursive=recursive,
                    engine=cli_config.engine,
                    quality_threshold=cli_config.quality_threshold,
                    max_workers=cli_config.max_workers
                )
                
                progress.update(task, completed=len(html_files))
            
            # 統計結果
            successful = sum(1 for r in results if r.success)
            high_quality = sum(1 for r in results if r.success and r.quality_score >= cli_config.quality_threshold)
            
            # 顯示統計表
            stats_table = Table(title="批次轉換統計")
            stats_table.add_column("項目", style="cyan")
            stats_table.add_column("數量", style="green")
            
            stats_table.add_row("總檔案數", str(len(html_files)))
            stats_table.add_row("轉換成功", str(successful))
            stats_table.add_row("高品質結果", str(high_quality))
            stats_table.add_row("成功率", f"{successful/len(html_files)*100:.1f}%")
            
            console.print(stats_table)
            
        except Exception as e:
            logger.error(f"批次轉換失敗: {str(e)}")
            console.print(f"❌ 批次轉換失敗: {str(e)}", style="red")
            sys.exit(1)
    
    asyncio.run(_batch_convert())


@cli.command()
@click.argument('url')
@click.option('--output', '-o', type=click.Path(), help='輸出檔案路徑')
@click.option('--user-agent', help='自定義 User-Agent')
@click.option('--timeout', type=int, default=30, help='請求超時時間（秒）')
def fetch_convert(url, output, user_agent, timeout):
    """從 URL 獲取網頁並轉換為 Markdown
    
    URL: 要轉換的網頁 URL
    """
    async def _fetch_convert():
        try:
            import aiohttp
            
            console.print(f"🌐 正在獲取網頁: {url}")
            
            # 設置請求頭
            headers = {
                'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 獲取網頁內容
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        console.print(f"❌ HTTP 錯誤: {response.status}", style="red")
                        return
                    
                    html_content = await response.text()
            
            console.print("✅ 網頁獲取成功，開始轉換...")
            
            # 執行轉換
            result = await quick_convert(
                html_content,
                url=url,
                engine=cli_config.engine,
                enable_caching=cli_config.enable_caching
            )
            
            # 顯示結果
            print_conversion_result(result, url)
            
            # 保存結果
            if output:
                output_path = Path(output)
            else:
                # 從 URL 生成檔案名
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                filename = f"{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}.md"
                filename = filename.replace('__', '_').strip('_')
                
                output_path = Path(filename)
                if cli_config.output_dir:
                    output_path = cli_config.output_dir / output_path.name
            
            if result.success and result.quality_score >= cli_config.quality_threshold:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.markdown_content)
                
                console.print(f"💾 結果已保存到: {output_path}", style="green")
            else:
                console.print("⚠️  品質評分過低，未保存結果", style="yellow")
                
        except Exception as e:
            logger.error(f"獲取轉換失敗: {str(e)}")
            console.print(f"❌ 獲取轉換失敗: {str(e)}", style="red")
            sys.exit(1)
    
    asyncio.run(_fetch_convert())


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def analyze(input_file):
    """分析 HTML 檔案的內容品質和結構
    
    INPUT_FILE: 要分析的 HTML 檔案路徑
    """
    try:
        input_path = Path(input_file)
        
        # 讀取 HTML 內容
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        console.print(f"🔍 正在分析檔案: {input_path.name}")
        
        # 執行分析
        cleaner = HTMLCleaner()
        extractor = ContentExtractor()
        assessor = QualityAssessment()
        
        # 清理和提取內容
        cleaned_html = cleaner.clean_html(html_content)
        main_content = extractor.extract_main_content(html_content)
        
        # 品質評估
        quality_score = assessor.assess_content_quality(main_content)
        
        # 提取元數據
        metadata = extractor.extract_page_metadata(html_content)
        
        # 顯示分析結果
        analysis_table = Table(title="HTML 內容分析")
        analysis_table.add_column("項目", style="cyan")
        analysis_table.add_column("值", style="green")
        
        analysis_table.add_row("檔案大小", f"{len(html_content):,} 字符")
        analysis_table.add_row("清理後大小", f"{len(cleaned_html):,} 字符")
        analysis_table.add_row("主要內容大小", f"{len(main_content):,} 字符")
        analysis_table.add_row("品質評分", f"{quality_score:.2f}")
        
        if metadata.get('title'):
            analysis_table.add_row("標題", metadata['title'])
        if metadata.get('description'):
            analysis_table.add_row("描述", metadata['description'][:100] + "..." if len(metadata['description']) > 100 else metadata['description'])
        if metadata.get('language'):
            analysis_table.add_row("語言", metadata['language'])
        
        console.print(analysis_table)
        
        # 顯示內容預覽
        if main_content:
            preview = main_content[:300]
            if len(main_content) > 300:
                preview += "..."
            
            console.print("\n📄 主要內容預覽:")
            console.print(Panel(preview, border_style="blue"))
        
    except Exception as e:
        logger.error(f"分析失敗: {str(e)}")
        console.print(f"❌ 分析失敗: {str(e)}", style="red")
        sys.exit(1)


@cli.command()
def list_engines():
    """列出所有可用的轉換引擎"""
    engines_table = Table(title="可用的轉換引擎")
    engines_table.add_column("引擎", style="cyan")
    engines_table.add_column("描述", style="green")
    engines_table.add_column("適用場景", style="yellow")
    
    engine_info = {
        'MARKDOWNIFY': ('Markdownify', '保持原始 HTML 結構', '代碼文檔、技術文章'),
        'TRAFILATURA': ('Trafilatura', '智能內容提取', '新聞文章、部落格'),
        'HTML2TEXT': ('HTML2Text', '純文本轉換', '簡單網頁、論壇'),
        'READABILITY': ('Readability', '可讀性優化', '複雜網頁、混合內容'),
        'AUTO': ('自動選擇', '根據內容自動選擇最佳引擎', '通用場景')
    }
    
    for engine_name, (display_name, description, use_case) in engine_info.items():
        engines_table.add_row(engine_name.lower(), display_name, description, use_case)
    
    console.print(engines_table)


@cli.command()
def version():
    """顯示版本資訊"""
    version_info = Text()
    version_info.append("HTML to Markdown 轉換工具\n", style="bold blue")
    version_info.append("版本: 1.0.0\n", style="green")
    version_info.append("基於 LLMFeeder 技術\n", style="dim")
    version_info.append("JasonSpider 專案\n", style="dim")
    
    console.print(Panel(version_info, border_style="blue"))


if __name__ == '__main__':
    cli()