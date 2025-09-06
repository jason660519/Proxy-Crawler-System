# HTML to Markdown 轉換技術整合方案

## 1. 技術概述

本文檔詳細說明如何將 HTML to Markdown 轉換技術整合到代理爬蟲系統中，提供多種轉換方案以滿足不同場景需求。

## 2. 核心技術棧

### 2.1 Python 庫選擇 (按優先級排序)

1. **markdownify** (首選)
   - 簡單易用，API 清晰
   - 支援自定義轉換規則
   - 輕量級，依賴少
   - 適用場景：一般網頁內容轉換

2. **html2text** (功能豐富)
   - 功能最全面，選項最多
   - 支援表格、圖片、連結處理
   - 可配置輸出格式
   - 適用場景：複雜 HTML 結構轉換

3. **trafilatura** (生產環境推薦)
   - 專業的網頁內容提取工具
   - 內建去噪算法
   - 支援多種輸出格式
   - 適用場景：新聞文章、部落格內容提取

4. **readability-lxml** (智能提取)
   - 基於 Mozilla Readability 算法
   - 自動識別主要內容
   - 過濾廣告和導航元素
   - 適用場景：複雜網頁的主要內容提取

5. **newspaper3k** (新聞特化)
   - 專門針對新聞網站優化
   - 自動提取標題、作者、發布時間
   - 內建 Markdown 輸出
   - 適用場景：新聞網站爬取

### 2.2 JavaScript 技術參考

- **TurndownService** (LLMFeeder 使用)
  - 高品質 HTML to Markdown 轉換
  - 可配置轉換規則
  - 支援插件擴展
  - 瀏覽器端實現參考

## 3. 架構設計

### 3.1 轉換器介面設計

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class ConversionMode(Enum):
    """轉換模式枚舉"""
    SIMPLE = "simple"  # 簡單轉換
    FULL = "full"      # 完整轉換
    CLEAN = "clean"    # 清理轉換
    NEWS = "news"      # 新聞模式

@dataclass
class ConversionOptions:
    """轉換選項配置"""
    mode: ConversionMode = ConversionMode.SIMPLE
    include_images: bool = True
    include_links: bool = True
    include_tables: bool = True
    strip_tags: Optional[list] = None
    custom_rules: Optional[Dict[str, Any]] = None
    max_content_length: int = 1000000  # 1MB

class HTMLToMarkdownConverter(ABC):
    """HTML to Markdown 轉換器抽象基類"""
    
    @abstractmethod
    def convert(self, html_content: str, options: ConversionOptions) -> str:
        """轉換 HTML 到 Markdown
        
        Args:
            html_content: HTML 內容
            options: 轉換選項
            
        Returns:
            轉換後的 Markdown 內容
        """
        pass
    
    @abstractmethod
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容有效性"""
        pass
```

### 3.2 具體實現類

#### 3.2.1 Markdownify 實現

```python
from markdownify import markdownify as md
import re
from bs4 import BeautifulSoup

class MarkdownifyConverter(HTMLToMarkdownConverter):
    """基於 markdownify 的轉換器實現"""
    
    def __init__(self):
        self.name = "markdownify"
    
    def convert(self, html_content: str, options: ConversionOptions) -> str:
        """使用 markdownify 轉換 HTML 到 Markdown"""
        try:
            # 預處理 HTML
            cleaned_html = self._preprocess_html(html_content, options)
            
            # 配置轉換選項
            convert_options = self._build_convert_options(options)
            
            # 執行轉換
            markdown = md(cleaned_html, **convert_options)
            
            # 後處理 Markdown
            return self._postprocess_markdown(markdown, options)
            
        except Exception as e:
            raise ConversionError(f"Markdownify 轉換失敗: {e}")
    
    def _preprocess_html(self, html: str, options: ConversionOptions) -> str:
        """預處理 HTML 內容"""
        soup = BeautifulSoup(html, 'lxml')
        
        # 移除不需要的標籤
        if options.strip_tags:
            for tag in options.strip_tags:
                for element in soup.find_all(tag):
                    element.decompose()
        
        # 清理模式：移除廣告、導航等
        if options.mode == ConversionMode.CLEAN:
            self._remove_noise_elements(soup)
        
        return str(soup)
    
    def _build_convert_options(self, options: ConversionOptions) -> Dict[str, Any]:
        """構建 markdownify 轉換選項"""
        convert_options = {
            'heading_style': 'ATX',
            'bullets': '-',
            'strip': ['script', 'style'] if options.mode == ConversionMode.CLEAN else None
        }
        
        if not options.include_images:
            convert_options['convert'] = ['img']
        
        return convert_options
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            return len(soup.get_text().strip()) > 0
        except:
            return False
```

#### 3.2.2 HTML2Text 實現

```python
import html2text

class HTML2TextConverter(HTMLToMarkdownConverter):
    """基於 html2text 的轉換器實現"""
    
    def __init__(self):
        self.name = "html2text"
        self.converter = html2text.HTML2Text()
    
    def convert(self, html_content: str, options: ConversionOptions) -> str:
        """使用 html2text 轉換 HTML 到 Markdown"""
        try:
            # 配置轉換器
            self._configure_converter(options)
            
            # 執行轉換
            markdown = self.converter.handle(html_content)
            
            return self._postprocess_markdown(markdown, options)
            
        except Exception as e:
            raise ConversionError(f"HTML2Text 轉換失敗: {e}")
    
    def _configure_converter(self, options: ConversionOptions):
        """配置 html2text 轉換器"""
        self.converter.ignore_links = not options.include_links
        self.converter.ignore_images = not options.include_images
        self.converter.ignore_tables = not options.include_tables
        self.converter.body_width = 0  # 不限制行寬
        
        if options.mode == ConversionMode.CLEAN:
            self.converter.ignore_emphasis = False
            self.converter.mark_code = True
```

### 3.3 轉換器工廠

```python
class ConverterFactory:
    """轉換器工廠類"""
    
    _converters = {
        'markdownify': MarkdownifyConverter,
        'html2text': HTML2TextConverter,
        'trafilatura': TrafilaturaConverter,
        'readability': ReadabilityConverter,
        'newspaper': NewspaperConverter
    }
    
    @classmethod
    def create_converter(cls, converter_type: str) -> HTMLToMarkdownConverter:
        """創建指定類型的轉換器"""
        if converter_type not in cls._converters:
            raise ValueError(f"不支援的轉換器類型: {converter_type}")
        
        return cls._converters[converter_type]()
    
    @classmethod
    def get_available_converters(cls) -> list:
        """獲取可用的轉換器列表"""
        return list(cls._converters.keys())
```

## 4. 整合到爬蟲系統

### 4.1 爬蟲模組整合

```python
from typing import Optional
from .html_to_markdown import ConverterFactory, ConversionOptions, ConversionMode

class ProxyCrawlerWithMarkdown:
    """整合 Markdown 轉換功能的代理爬蟲"""
    
    def __init__(self, converter_type: str = 'markdownify'):
        self.converter = ConverterFactory.create_converter(converter_type)
        self.conversion_options = ConversionOptions(
            mode=ConversionMode.CLEAN,
            include_images=False,  # 代理列表通常不需要圖片
            include_tables=True,   # 保留表格結構
            strip_tags=['script', 'style', 'nav', 'footer']
        )
    
    async def crawl_and_convert(self, url: str) -> Dict[str, Any]:
        """爬取網頁並轉換為 Markdown"""
        try:
            # 爬取 HTML 內容
            html_content = await self._fetch_html(url)
            
            # 轉換為 Markdown
            markdown_content = self.converter.convert(html_content, self.conversion_options)
            
            return {
                'url': url,
                'html': html_content,
                'markdown': markdown_content,
                'timestamp': datetime.now().isoformat(),
                'converter': self.converter.name
            }
            
        except Exception as e:
            logger.error(f"爬取轉換失敗 {url}: {e}")
            raise
```

### 4.2 輸出格式標準化

```python
@dataclass
class MarkdownOutput:
    """Markdown 輸出標準格式"""
    source_url: str
    title: str
    content: str
    metadata: Dict[str, Any]
    conversion_info: Dict[str, str]
    timestamp: str
    
    def to_file(self, filepath: str) -> None:
        """輸出到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {self.title}\n\n")
            f.write(f"**來源:** {self.source_url}\n\n")
            f.write(f"**轉換時間:** {self.timestamp}\n\n")
            f.write(f"**轉換器:** {self.conversion_info.get('converter', 'unknown')}\n\n")
            f.write("---\n\n")
            f.write(self.content)
```

## 5. 使用範例

### 5.1 基本使用

```python
# 創建轉換器
converter = ConverterFactory.create_converter('markdownify')

# 配置選項
options = ConversionOptions(
    mode=ConversionMode.CLEAN,
    include_images=False,
    include_tables=True
)

# 轉換 HTML
html_content = "<h1>標題</h1><p>內容</p>"
markdown = converter.convert(html_content, options)
print(markdown)
```

### 5.2 整合到現有爬蟲

```python
# 在現有的代理爬蟲中添加 Markdown 轉換
class FreeProxyListCrawler(ProxyCrawlerWithMarkdown):
    def __init__(self):
        super().__init__(converter_type='trafilatura')  # 使用 trafilatura
        
    async def extract_proxies_with_markdown(self, url: str):
        # 爬取並轉換
        result = await self.crawl_and_convert(url)
        
        # 從 Markdown 中提取代理信息
        proxies = self._parse_proxies_from_markdown(result['markdown'])
        
        return {
            'proxies': proxies,
            'markdown_content': result['markdown'],
            'source_info': result
        }
```

## 6. 性能優化建議

1. **緩存機制**: 對轉換結果進行緩存，避免重複轉換
2. **異步處理**: 使用異步方式處理大量 HTML 轉換
3. **內容大小限制**: 設置合理的內容大小上限
4. **錯誤處理**: 實現完善的錯誤處理和降級機制
5. **監控指標**: 監控轉換成功率、耗時等指標

## 7. 測試策略

1. **單元測試**: 測試各個轉換器的基本功能
2. **整合測試**: 測試與爬蟲系統的整合
3. **性能測試**: 測試大量內容轉換的性能
4. **兼容性測試**: 測試不同 HTML 結構的兼容性

## 8. 部署注意事項

1. **依賴管理**: 確保所有依賴包正確安裝
2. **配置管理**: 提供靈活的配置選項
3. **日誌記錄**: 記錄轉換過程和錯誤信息
4. **資源監控**: 監控內存和 CPU 使用情況

這個技術整合方案提供了完整的 HTML to Markdown 轉換解決方案，可以根據具體需求選擇合適的轉換器和配置選項。