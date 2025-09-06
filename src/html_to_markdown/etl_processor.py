"""ETL 處理器

整合 HTML to Markdown 轉換功能到 ETL 流程中，
提供完整的提取、轉換、載入功能。
"""

import asyncio
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger

from .core import (
    HTMLToMarkdownConverter, ConversionConfig, ConversionResult, 
    ConversionEngine, ContentScope, OutputFormat
)
from .converters import (
    MarkdownifyConverter, TrafilaturaConverter, 
    HTML2TextConverter, ReadabilityConverter
)
from .adapters import SiteAdapterManager, site_adapter_manager


@dataclass
class ETLConfig:
    """ETL 處理配置"""
    # 輸入配置
    input_directory: str = "data/raw/html"
    input_pattern: str = "*.html"
    
    # 輸出配置
    output_directory: str = "data/processed/markdown"
    intermediate_directory: str = "data/intermediate"
    
    # 轉換配置
    conversion_config: ConversionConfig = None
    primary_engine: ConversionEngine = ConversionEngine.TRAFILATURA
    fallback_engines: List[ConversionEngine] = None
    
    # 處理配置
    batch_size: int = 10
    max_concurrent: int = 5
    enable_caching: bool = True
    cache_directory: str = "data/cache"
    
    # 品質控制
    min_success_rate: float = 0.8
    enable_validation: bool = True
    
    # 檔案命名
    output_filename_template: str = "{source}_{timestamp}_{engine}.md"
    
    def __post_init__(self):
        if self.conversion_config is None:
            self.conversion_config = ConversionConfig()
        
        if self.fallback_engines is None:
            self.fallback_engines = [
                ConversionEngine.MARKDOWNIFY,
                ConversionEngine.HTML2TEXT
            ]


@dataclass
class ETLResult:
    """ETL 處理結果"""
    total_files: int
    successful_conversions: int
    failed_conversions: int
    processing_time: float
    output_files: List[str]
    errors: List[str]
    conversion_results: List[ConversionResult]
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_files == 0:
            return 0.0
        return self.successful_conversions / self.total_files
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)


class HTMLToMarkdownETLProcessor:
    """HTML to Markdown ETL 處理器
    
    提供完整的 ETL 流程：
    1. Extract: 從檔案系統或 URL 提取 HTML 內容
    2. Transform: 使用多種引擎轉換為 Markdown
    3. Load: 儲存轉換結果到指定位置
    """
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = logger.bind(component='ETLProcessor')
        
        # 初始化轉換器
        self.converters: Dict[ConversionEngine, HTMLToMarkdownConverter] = {}
        self._initialize_converters()
        
        # 初始化適配器管理器
        self.adapter_manager = site_adapter_manager
        
        # 創建必要的目錄
        self._ensure_directories()
        
        # 快取
        self.cache: Dict[str, ConversionResult] = {}
    
    def _initialize_converters(self):
        """初始化轉換器"""
        try:
            self.converters[ConversionEngine.MARKDOWNIFY] = MarkdownifyConverter(self.config.conversion_config)
        except ImportError:
            self.logger.warning("Markdownify 不可用")
        
        try:
            self.converters[ConversionEngine.TRAFILATURA] = TrafilaturaConverter(self.config.conversion_config)
        except ImportError:
            self.logger.warning("Trafilatura 不可用")
        
        try:
            self.converters[ConversionEngine.HTML2TEXT] = HTML2TextConverter(self.config.conversion_config)
        except ImportError:
            self.logger.warning("HTML2Text 不可用")
        
        try:
            self.converters[ConversionEngine.READABILITY] = ReadabilityConverter(self.config.conversion_config)
        except ImportError:
            self.logger.warning("Readability 不可用")
        
        if not self.converters:
            raise RuntimeError("沒有可用的轉換器，請安裝相關依賴")
        
        self.logger.info(f"已初始化 {len(self.converters)} 個轉換器")
    
    def _ensure_directories(self):
        """確保必要的目錄存在"""
        directories = [
            self.config.output_directory,
            self.config.intermediate_directory,
            self.config.cache_directory
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, html_content: str, url: str, engine: ConversionEngine) -> str:
        """生成快取鍵"""
        content_hash = hashlib.md5(html_content.encode()).hexdigest()
        return f"{engine.value}_{content_hash}_{hashlib.md5(url.encode()).hexdigest()[:8]}"
    
    async def process_single_file(self, file_path: str, url: str = "") -> ConversionResult:
        """處理單個檔案"""
        try:
            # 讀取 HTML 內容
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return await self.process_html_content(html_content, url or file_path)
            
        except Exception as e:
            self.logger.error(f"處理檔案失敗 {file_path}: {e}")
            return ConversionResult(
                success=False,
                content="",
                original_length=0,
                converted_length=0,
                processing_time=0,
                engine_used=self.config.primary_engine,
                url=url or file_path,
                error_message=str(e)
            )
    
    async def process_html_content(self, html_content: str, url: str = "") -> ConversionResult:
        """處理 HTML 內容"""
        start_time = time.time()
        
        # 檢查快取
        if self.config.enable_caching:
            cache_key = self._get_cache_key(html_content, url, self.config.primary_engine)
            if cache_key in self.cache:
                self.logger.info(f"使用快取結果: {url}")
                return self.cache[cache_key]
        
        # 使用網站適配器預處理
        try:
            processed_html, metadata = await self.adapter_manager.extract_content(html_content, url)
        except Exception as e:
            self.logger.warning(f"適配器處理失敗，使用原始內容: {e}")
            processed_html = html_content
            metadata = {}
        
        # 嘗試主要轉換引擎
        result = await self._try_conversion(processed_html, url, self.config.primary_engine)
        
        # 如果主要引擎失敗，嘗試備用引擎
        if not result.success:
            self.logger.warning(f"主要引擎 {self.config.primary_engine.value} 失敗，嘗試備用引擎")
            
            for fallback_engine in self.config.fallback_engines:
                if fallback_engine in self.converters:
                    result = await self._try_conversion(processed_html, url, fallback_engine)
                    if result.success:
                        self.logger.info(f"備用引擎 {fallback_engine.value} 成功")
                        break
        
        # 添加適配器元數據
        if result.metadata:
            result.metadata.update(metadata)
        else:
            result.metadata = metadata
        
        # 更新處理時間
        result.processing_time = time.time() - start_time
        
        # 快取結果
        if self.config.enable_caching and result.success:
            cache_key = self._get_cache_key(html_content, url, result.engine_used)
            self.cache[cache_key] = result
        
        return result
    
    async def _try_conversion(self, html_content: str, url: str, engine: ConversionEngine) -> ConversionResult:
        """嘗試使用指定引擎轉換"""
        if engine not in self.converters:
            return ConversionResult(
                success=False,
                content="",
                original_length=len(html_content),
                converted_length=0,
                processing_time=0,
                engine_used=engine,
                url=url,
                error_message=f"轉換器 {engine.value} 不可用"
            )
        
        try:
            converter = self.converters[engine]
            return await converter.convert(html_content, url)
        except Exception as e:
            self.logger.error(f"轉換失敗 {engine.value} {url}: {e}")
            return ConversionResult(
                success=False,
                content="",
                original_length=len(html_content),
                converted_length=0,
                processing_time=0,
                engine_used=engine,
                url=url,
                error_message=str(e)
            )
    
    async def process_batch(self, file_paths: List[str]) -> ETLResult:
        """批次處理檔案"""
        start_time = time.time()
        
        self.logger.info(f"開始批次處理 {len(file_paths)} 個檔案")
        
        # 分批處理
        all_results = []
        errors = []
        output_files = []
        
        for i in range(0, len(file_paths), self.config.batch_size):
            batch = file_paths[i:i + self.config.batch_size]
            
            # 並發處理批次
            semaphore = asyncio.Semaphore(self.config.max_concurrent)
            
            async def process_with_semaphore(file_path):
                async with semaphore:
                    return await self.process_single_file(file_path)
            
            batch_results = await asyncio.gather(
                *[process_with_semaphore(fp) for fp in batch],
                return_exceptions=True
            )
            
            # 處理結果
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    error_msg = f"處理檔案 {batch[j]} 時發生異常: {result}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
                else:
                    all_results.append(result)
                    
                    # 儲存成功的轉換結果
                    if result.success:
                        try:
                            output_file = await self._save_result(result, batch[j])
                            output_files.append(output_file)
                        except Exception as e:
                            error_msg = f"儲存結果失敗 {batch[j]}: {e}"
                            errors.append(error_msg)
                            self.logger.error(error_msg)
            
            self.logger.info(f"已處理批次 {i//self.config.batch_size + 1}/{(len(file_paths)-1)//self.config.batch_size + 1}")
        
        # 統計結果
        successful_conversions = sum(1 for r in all_results if r.success)
        failed_conversions = len(all_results) - successful_conversions
        
        etl_result = ETLResult(
            total_files=len(file_paths),
            successful_conversions=successful_conversions,
            failed_conversions=failed_conversions,
            processing_time=time.time() - start_time,
            output_files=output_files,
            errors=errors,
            conversion_results=all_results
        )
        
        self.logger.info(f"批次處理完成: 成功 {successful_conversions}/{len(file_paths)} (成功率: {etl_result.success_rate:.2%})")
        
        # 品質檢查
        if self.config.enable_validation and etl_result.success_rate < self.config.min_success_rate:
            self.logger.warning(f"成功率 {etl_result.success_rate:.2%} 低於最低要求 {self.config.min_success_rate:.2%}")
        
        return etl_result
    
    async def _save_result(self, result: ConversionResult, source_file: str) -> str:
        """儲存轉換結果"""
        # 生成輸出檔案名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(source_file).stem
        
        filename = self.config.output_filename_template.format(
            source=source_name,
            timestamp=timestamp,
            engine=result.engine_used.value
        )
        
        output_path = Path(self.config.output_directory) / filename
        
        # 準備內容
        content_lines = []
        
        # 添加元數據標頭
        if result.metadata:
            content_lines.append("---")
            content_lines.append(f"title: {result.title or 'Untitled'}")
            content_lines.append(f"url: {result.url}")
            content_lines.append(f"engine: {result.engine_used.value}")
            content_lines.append(f"processing_time: {result.processing_time:.2f}s")
            content_lines.append(f"original_length: {result.original_length}")
            content_lines.append(f"converted_length: {result.converted_length}")
            content_lines.append(f"timestamp: {datetime.now().isoformat()}")
            
            # 添加其他元數據
            for key, value in result.metadata.items():
                if value and key not in ['title', 'url']:
                    content_lines.append(f"{key}: {value}")
            
            content_lines.append("---")
            content_lines.append("")
        
        # 添加主要內容
        content_lines.append(result.content)
        
        # 寫入檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        self.logger.info(f"已儲存轉換結果: {output_path}")
        return str(output_path)
    
    async def process_directory(self, input_dir: str = None) -> ETLResult:
        """處理整個目錄"""
        input_directory = input_dir or self.config.input_directory
        input_path = Path(input_directory)
        
        if not input_path.exists():
            raise FileNotFoundError(f"輸入目錄不存在: {input_directory}")
        
        # 查找匹配的檔案
        file_paths = list(input_path.glob(self.config.input_pattern))
        
        if not file_paths:
            self.logger.warning(f"在 {input_directory} 中未找到匹配 {self.config.input_pattern} 的檔案")
            return ETLResult(
                total_files=0,
                successful_conversions=0,
                failed_conversions=0,
                processing_time=0,
                output_files=[],
                errors=[],
                conversion_results=[]
            )
        
        self.logger.info(f"找到 {len(file_paths)} 個檔案待處理")
        
        # 轉換為字符串路徑
        file_paths_str = [str(fp) for fp in file_paths]
        
        return await self.process_batch(file_paths_str)
    
    def generate_report(self, etl_result: ETLResult) -> str:
        """生成處理報告"""
        report_lines = [
            "# HTML to Markdown ETL 處理報告",
            "",
            f"**處理時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**總檔案數**: {etl_result.total_files}",
            f"**成功轉換**: {etl_result.successful_conversions}",
            f"**失敗轉換**: {etl_result.failed_conversions}",
            f"**成功率**: {etl_result.success_rate:.2%}",
            f"**處理時間**: {etl_result.processing_time:.2f} 秒",
            "",
            "## 輸出檔案",
            ""
        ]
        
        for output_file in etl_result.output_files:
            report_lines.append(f"- {output_file}")
        
        if etl_result.errors:
            report_lines.extend([
                "",
                "## 錯誤記錄",
                ""
            ])
            
            for error in etl_result.errors:
                report_lines.append(f"- {error}")
        
        # 引擎使用統計
        engine_stats = {}
        for result in etl_result.conversion_results:
            if result.success:
                engine = result.engine_used.value
                engine_stats[engine] = engine_stats.get(engine, 0) + 1
        
        if engine_stats:
            report_lines.extend([
                "",
                "## 轉換引擎使用統計",
                ""
            ])
            
            for engine, count in engine_stats.items():
                percentage = (count / etl_result.successful_conversions) * 100
                report_lines.append(f"- {engine}: {count} 次 ({percentage:.1f}%)")
        
        return '\n'.join(report_lines)
    
    async def save_report(self, etl_result: ETLResult, report_path: str = None) -> str:
        """儲存處理報告"""
        if report_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = Path(self.config.output_directory) / f"etl_report_{timestamp}.md"
        
        report_content = self.generate_report(etl_result)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"已儲存處理報告: {report_path}")
        return str(report_path)


# 便利函數
async def quick_convert(html_content: str, url: str = "", engine: ConversionEngine = ConversionEngine.TRAFILATURA) -> ConversionResult:
    """快速轉換 HTML 內容"""
    config = ETLConfig(primary_engine=engine)
    processor = HTMLToMarkdownETLProcessor(config)
    return await processor.process_html_content(html_content, url)


async def batch_convert_directory(input_dir: str, output_dir: str, engine: ConversionEngine = ConversionEngine.TRAFILATURA) -> ETLResult:
    """批次轉換目錄中的 HTML 檔案"""
    config = ETLConfig(
        input_directory=input_dir,
        output_directory=output_dir,
        primary_engine=engine
    )
    processor = HTMLToMarkdownETLProcessor(config)
    return await processor.process_directory()