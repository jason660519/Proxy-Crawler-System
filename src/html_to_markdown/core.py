"""HTML to Markdown 轉換核心模組

提供轉換器的抽象基類、配置類和核心枚舉定義。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
from datetime import datetime
from loguru import logger


class ConversionEngine(Enum):
    """轉換引擎類型枚舉"""
    MARKDOWNIFY = "markdownify"
    HTML2TEXT = "html2text"
    TRAFILATURA = "trafilatura"
    READABILITY = "readability"
    BEAUTIFULSOUP = "beautifulsoup"
    CUSTOM = "custom"


class ContentScope(Enum):
    """內容範圍枚舉"""
    FULL_PAGE = "full_page"  # 完整頁面
    MAIN_CONTENT = "main_content"  # 主要內容
    SELECTED_CONTENT = "selected_content"  # 選定內容
    CUSTOM_SELECTOR = "custom_selector"  # 自定義選擇器


class OutputFormat(Enum):
    """輸出格式枚舉"""
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    STRUCTURED_JSON = "structured_json"


@dataclass
class ConversionConfig:
    """轉換配置類
    
    定義 HTML to Markdown 轉換的各種參數和選項。
    """
    # 基本配置
    engine: ConversionEngine = ConversionEngine.MARKDOWNIFY
    scope: ContentScope = ContentScope.MAIN_CONTENT
    output_format: OutputFormat = OutputFormat.MARKDOWN
    
    # 內容包含選項
    include_images: bool = True
    include_links: bool = True
    include_tables: bool = True
    include_title: bool = True
    include_metadata: bool = False
    
    # 自定義選擇器
    custom_selectors: Optional[Dict[str, str]] = None
    
    # 內容過濾
    strip_tags: Optional[List[str]] = field(default_factory=lambda: ["script", "style", "nav", "footer"])
    strip_attributes: Optional[List[str]] = field(default_factory=lambda: ["onclick", "onload", "style"])
    
    # 內容限制
    max_content_length: int = 1000000  # 1MB
    min_content_length: int = 100
    
    # LLM 整合
    enable_llm_processing: bool = False
    llm_model: str = "gpt-3.5-turbo"
    llm_prompt_template: Optional[str] = None
    
    # 輸出格式化
    heading_style: str = "ATX"  # ATX (#) 或 Setext (===)
    bullet_style: str = "-"  # -, *, +
    code_block_style: str = "fenced"  # fenced (```) 或 indented
    
    # 性能配置
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_caching: bool = True
    
    # 調試選項
    debug_mode: bool = False
    save_intermediate_files: bool = False
    
    def __post_init__(self):
        """初始化後的驗證"""
        if self.custom_selectors is None:
            self.custom_selectors = {}
        
        # 驗證配置合理性
        if self.max_content_length < self.min_content_length:
            raise ValueError("max_content_length 不能小於 min_content_length")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds 必須大於 0")
        
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts 不能為負數")


@dataclass
class ConversionResult:
    """轉換結果類
    
    包含轉換後的內容和相關元數據。
    """
    success: bool
    content: str
    original_length: int
    converted_length: int
    processing_time: float
    engine_used: ConversionEngine
    url: str = ""
    title: str = ""
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def compression_ratio(self) -> float:
        """計算壓縮比例"""
        if self.original_length == 0:
            return 0.0
        return self.converted_length / self.original_length
    
    @property
    def is_valid(self) -> bool:
        """檢查結果是否有效"""
        return self.success and len(self.content.strip()) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'success': self.success,
            'content': self.content,
            'original_length': self.original_length,
            'converted_length': self.converted_length,
            'compression_ratio': self.compression_ratio,
            'processing_time': self.processing_time,
            'engine_used': self.engine_used.value,
            'url': self.url,
            'title': self.title,
            'error_message': self.error_message,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'is_valid': self.is_valid
        }


class HTMLToMarkdownConverter(ABC):
    """HTML to Markdown 轉換器抽象基類
    
    定義所有轉換器必須實現的介面。
    """
    
    def __init__(self, config: ConversionConfig):
        """初始化轉換器
        
        Args:
            config: 轉換配置
        """
        self.config = config
        self.logger = logger.bind(converter=self.__class__.__name__)
        self._cache: Dict[str, ConversionResult] = {}
    
    @abstractmethod
    async def convert(self, html_content: str, url: str = "") -> ConversionResult:
        """轉換 HTML 到 Markdown
        
        Args:
            html_content: HTML 內容
            url: 來源 URL (用於相對路徑處理和快取)
            
        Returns:
            ConversionResult: 轉換結果
        """
        pass
    
    @abstractmethod
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容有效性
        
        Args:
            html_content: HTML 內容
            
        Returns:
            bool: 是否有效
        """
        pass
    
    async def preprocess_html(self, html_content: str) -> str:
        """HTML 預處理
        
        Args:
            html_content: 原始 HTML 內容
            
        Returns:
            str: 預處理後的 HTML 內容
        """
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 移除不需要的標籤
            if self.config.strip_tags:
                for tag_name in self.config.strip_tags:
                    for element in soup.find_all(tag_name):
                        element.decompose()
            
            # 移除不需要的屬性
            if self.config.strip_attributes:
                for element in soup.find_all():
                    for attr in self.config.strip_attributes:
                        if attr in element.attrs:
                            del element.attrs[attr]
            
            # 清理空白標籤
            for element in soup.find_all():
                if not element.get_text(strip=True) and not element.find_all(['img', 'br', 'hr']):
                    element.decompose()
            
            processed_html = str(soup)
            
            if self.config.debug_mode:
                self.logger.debug(f"HTML 預處理完成，原始長度: {len(html_content)}, 處理後長度: {len(processed_html)}")
            
            return processed_html
            
        except Exception as e:
            self.logger.warning(f"HTML 預處理失敗，使用原始內容: {e}")
            return html_content
    
    async def postprocess_markdown(self, markdown: str) -> str:
        """Markdown 後處理
        
        Args:
            markdown: 原始 Markdown 內容
            
        Returns:
            str: 後處理的 Markdown 內容
        """
        try:
            # 清理多餘的空行
            lines = markdown.split('\n')
            cleaned_lines = []
            prev_empty = False
            
            for line in lines:
                is_empty = line.strip() == ''
                # 避免連續的空行
                if not (is_empty and prev_empty):
                    cleaned_lines.append(line)
                prev_empty = is_empty
            
            # 確保文檔結尾只有一個換行
            while cleaned_lines and cleaned_lines[-1].strip() == '':
                cleaned_lines.pop()
            
            processed_markdown = '\n'.join(cleaned_lines)
            
            # 修正標題格式
            if self.config.heading_style == "ATX":
                processed_markdown = self._normalize_atx_headings(processed_markdown)
            
            # 修正列表格式
            processed_markdown = self._normalize_lists(processed_markdown)
            
            if self.config.debug_mode:
                self.logger.debug(f"Markdown 後處理完成，原始長度: {len(markdown)}, 處理後長度: {len(processed_markdown)}")
            
            return processed_markdown
            
        except Exception as e:
            self.logger.warning(f"Markdown 後處理失敗，使用原始內容: {e}")
            return markdown
    
    def _normalize_atx_headings(self, markdown: str) -> str:
        """標準化 ATX 標題格式"""
        import re
        
        # 確保標題前後有空行
        lines = markdown.split('\n')
        normalized_lines = []
        
        for i, line in enumerate(lines):
            if re.match(r'^#{1,6}\s+', line):
                # 標題前加空行 (除非是第一行)
                if i > 0 and lines[i-1].strip() != '':
                    normalized_lines.append('')
                normalized_lines.append(line)
                # 標題後加空行 (除非是最後一行)
                if i < len(lines) - 1 and lines[i+1].strip() != '':
                    normalized_lines.append('')
            else:
                normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)
    
    def _normalize_lists(self, markdown: str) -> str:
        """標準化列表格式"""
        import re
        
        lines = markdown.split('\n')
        normalized_lines = []
        
        for line in lines:
            # 統一列表符號
            if re.match(r'^\s*[*+]\s+', line):
                line = re.sub(r'^(\s*)[*+](\s+)', f'\\1{self.config.bullet_style}\\2', line)
            normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)
    
    async def extract_title(self, html_content: str) -> str:
        """提取頁面標題
        
        Args:
            html_content: HTML 內容
            
        Returns:
            str: 頁面標題
        """
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 嘗試多種方式提取標題
            title_candidates = [
                soup.find('title'),
                soup.find('h1'),
                soup.find('h2'),
                soup.find('[property="og:title"]'),
                soup.find('[name="twitter:title"]')
            ]
            
            for candidate in title_candidates:
                if candidate:
                    title = candidate.get_text(strip=True) if hasattr(candidate, 'get_text') else candidate.get('content', '')
                    if title:
                        return title
            
            return "Untitled"
            
        except Exception as e:
            self.logger.warning(f"標題提取失敗: {e}")
            return "Untitled"
    
    def _get_cache_key(self, html_content: str, url: str) -> str:
        """生成快取鍵值"""
        import hashlib
        
        content_hash = hashlib.md5(html_content.encode()).hexdigest()
        config_hash = hashlib.md5(str(self.config).encode()).hexdigest()
        
        return f"{url}:{content_hash}:{config_hash}"
    
    async def get_cached_result(self, html_content: str, url: str) -> Optional[ConversionResult]:
        """獲取快取結果"""
        if not self.config.enable_caching:
            return None
        
        cache_key = self._get_cache_key(html_content, url)
        return self._cache.get(cache_key)
    
    async def cache_result(self, html_content: str, url: str, result: ConversionResult):
        """快取結果"""
        if not self.config.enable_caching:
            return
        
        cache_key = self._get_cache_key(html_content, url)
        self._cache[cache_key] = result
        
        # 限制快取大小
        if len(self._cache) > 1000:
            # 移除最舊的條目
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
    
    async def convert_with_retry(self, html_content: str, url: str = "") -> ConversionResult:
        """帶重試機制的轉換
        
        Args:
            html_content: HTML 內容
            url: 來源 URL
            
        Returns:
            ConversionResult: 轉換結果
        """
        # 檢查快取
        cached_result = await self.get_cached_result(html_content, url)
        if cached_result:
            self.logger.debug(f"使用快取結果: {url}")
            return cached_result
        
        last_error = None
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                result = await asyncio.wait_for(
                    self.convert(html_content, url),
                    timeout=self.config.timeout_seconds
                )
                
                # 快取成功結果
                await self.cache_result(html_content, url, result)
                
                return result
                
            except asyncio.TimeoutError as e:
                last_error = f"轉換超時 (嘗試 {attempt + 1}/{self.config.retry_attempts + 1})"
                self.logger.warning(last_error)
                
            except Exception as e:
                last_error = f"轉換失敗: {e} (嘗試 {attempt + 1}/{self.config.retry_attempts + 1})"
                self.logger.warning(last_error)
            
            # 重試前等待
            if attempt < self.config.retry_attempts:
                await asyncio.sleep(2 ** attempt)  # 指數退避
        
        # 所有重試都失敗
        return ConversionResult(
            success=False,
            content="",
            original_length=len(html_content),
            converted_length=0,
            processing_time=0.0,
            engine_used=self.config.engine,
            url=url,
            error_message=last_error or "未知錯誤"
        )