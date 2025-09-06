# HTML to Markdown 轉換模組
# 通用 HTML to Markdown 轉換程式

from .core import HTMLToMarkdownConverter, ConversionConfig, ConversionEngine, ContentScope
from .converters import MarkdownifyConverter, TrafilaturaConverter, HTML2TextConverter, ReadabilityConverter
from .adapters import SiteAdapter, SiteAdapterManager, GenericSiteAdapter, MediumAdapter, GitHubAdapter
from .seek_adapter import SeekMarkdownAdapter, JobListing
from .etl_processor import HTMLToMarkdownETLProcessor, ETLConfig, ETLResult
from .utils import HTMLCleaner, ContentExtractor, ContentQuality, QualityAssessor, URLUtils, TextUtils

__version__ = "1.0.0"
__author__ = "Jason Spider Team"
__description__ = "通用 HTML to Markdown 轉換程式，支援多網站和 ETL 整合"

__all__ = [
    # 核心類別
    "HTMLToMarkdownConverter",
    "ConversionConfig", 
    "ConversionEngine",
    "ContentScope",
    
    # 轉換器
    "MarkdownifyConverter",
    "TrafilaturaConverter", 
    "HTML2TextConverter",
    
    # 適配器
    "SiteAdapter",
    "SiteAdapterManager",
    "SeekMarkdownAdapter",
    "JobListing",
    
    # ETL 處理器
    "HTMLToMarkdownETLProcessor",
    
    # 工具類
    "PerformanceMonitor",
    "ErrorHandler"
]

# 預設配置
DEFAULT_CONFIG = ConversionConfig(
    engine=ConversionEngine.MARKDOWNIFY,
    scope=ContentScope.MAIN_CONTENT,
    include_images=True,
    include_links=True,
    include_tables=True,
    include_title=True,
    enable_llm_processing=False
)

# 快速創建處理器的便利函數
def create_processor(config_path: str = None) -> HTMLToMarkdownETLProcessor:
    """創建 HTML to Markdown ETL 處理器
    
    Args:
        config_path: 網站適配器配置文件路徑
        
    Returns:
        HTMLToMarkdownETLProcessor 實例
    """
    return HTMLToMarkdownETLProcessor(config_path=config_path)

# 快速轉換函數
async def quick_convert(
    html_content: str, 
    url: str = "",
    engine: ConversionEngine = ConversionEngine.MARKDOWNIFY
) -> str:
    """快速轉換 HTML 到 Markdown
    
    Args:
        html_content: HTML 內容
        url: 來源 URL
        engine: 轉換引擎
        
    Returns:
        Markdown 內容
    """
    config = ConversionConfig(engine=engine)
    
    if engine == ConversionEngine.MARKDOWNIFY:
        converter = MarkdownifyConverter(config)
    elif engine == ConversionEngine.TRAFILATURA:
        converter = TrafilaturaConverter(config)
    elif engine == ConversionEngine.HTML2TEXT:
        converter = HTML2TextConverter(config)
    else:
        raise ValueError(f"不支援的轉換引擎: {engine}")
    
    return await converter.convert(html_content, url)