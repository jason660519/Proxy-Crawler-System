# 通用 HTML to Markdown 轉換程式實現方案

## 1. 專案概述

基於 LLMFeeder 瀏覽器擴展的成功經驗，開發一個通用的 HTML to Markdown 轉換程式，能夠支援多個指定網站，並無縫整合到代理爬蟲系統的 ETL 流程中。

### 1.1 核心目標

- **通用性**: 支援多個網站的 HTML 內容轉換
- **可擴展性**: 易於添加新網站的支援
- **高品質**: 產生乾淨、結構化的 Markdown 內容
- **ETL 整合**: 無縫整合到現有的 ETL 流程中
- **智能化**: 結合 LLM 進行內容解析與結構化

## 2. 技術架構設計

### 2.1 整體架構

```
通用 HTML to Markdown 轉換系統
├── 核心轉換引擎 (Core Conversion Engine)
│   ├── 多引擎轉換器 (Multi-Engine Converter)
│   ├── 網站特定適配器 (Site-Specific Adapters)
│   └── 內容清理引擎 (Content Cleaning Engine)
├── 智能提取模組 (Smart Extraction Module)
│   ├── Readability 算法實現
│   ├── 自定義選擇器引擎
│   └── LLM 內容解析器
├── 配置管理系統 (Configuration Management)
│   ├── 網站配置檔案
│   ├── 轉換規則定義
│   └── 動態配置載入
└── ETL 整合介面 (ETL Integration Interface)
    ├── 異步處理隊列
    ├── 批次處理支援
    └── 結果快取機制
```

### 2.2 核心技術棧

#### Python 後端技術

```python
# 核心依賴包
DEPENDENCIES = {
    # HTML 解析與轉換
    "beautifulsoup4": "^4.12.0",
    "lxml": "^4.9.0",
    "markdownify": "^0.11.6",
    "html2text": "^2020.1.16",
    "trafilatura": "^1.6.0",
    "readability-lxml": "^0.8.1",
    
    # 異步處理
    "aiohttp": "^3.8.0",
    "asyncio": "內建",
    "aiofiles": "^23.0.0",
    
    # 數據處理與驗證
    "pydantic": "^2.0.0",
    "dataclasses": "內建",
    
    # 瀏覽器自動化 (動態內容)
    "playwright": "^1.40.0",
    "selenium": "^4.15.0",
    
    # LLM 整合
    "openai": "^1.0.0",
    "anthropic": "^0.7.0",
    
    # 配置與日誌
    "pyyaml": "^6.0",
    "loguru": "^0.7.0",
    
    # 快取與存儲
    "redis": "^5.0.0",
    "sqlalchemy": "^2.0.0"
}
```

## 3. 詳細實現方案

### 3.1 核心轉換引擎

#### 3.1.1 多引擎轉換器

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
from loguru import logger

class ConversionEngine(Enum):
    """轉換引擎類型"""
    MARKDOWNIFY = "markdownify"
    HTML2TEXT = "html2text"
    TRAFILATURA = "trafilatura"
    READABILITY = "readability"
    CUSTOM = "custom"

class ContentScope(Enum):
    """內容範圍"""
    FULL_PAGE = "full_page"
    MAIN_CONTENT = "main_content"
    SELECTED_CONTENT = "selected_content"
    CUSTOM_SELECTOR = "custom_selector"

@dataclass
class ConversionConfig:
    """轉換配置"""
    engine: ConversionEngine = ConversionEngine.MARKDOWNIFY
    scope: ContentScope = ContentScope.MAIN_CONTENT
    include_images: bool = True
    include_links: bool = True
    include_tables: bool = True
    include_title: bool = True
    custom_selectors: Optional[Dict[str, str]] = None
    strip_tags: Optional[List[str]] = None
    max_content_length: int = 1000000
    enable_llm_processing: bool = False
    llm_model: str = "gpt-3.5-turbo"

class HTMLToMarkdownConverter(ABC):
    """HTML to Markdown 轉換器抽象基類"""
    
    def __init__(self, config: ConversionConfig):
        self.config = config
        self.logger = logger.bind(converter=self.__class__.__name__)
    
    @abstractmethod
    async def convert(self, html_content: str, url: str = "") -> str:
        """轉換 HTML 到 Markdown
        
        Args:
            html_content: HTML 內容
            url: 來源 URL (用於相對路徑處理)
            
        Returns:
            轉換後的 Markdown 內容
        """
        pass
    
    @abstractmethod
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容有效性"""
        pass
    
    async def preprocess_html(self, html_content: str) -> str:
        """HTML 預處理"""
        # 移除不需要的標籤
        if self.config.strip_tags:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            for tag in self.config.strip_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            html_content = str(soup)
        
        return html_content
    
    async def postprocess_markdown(self, markdown: str) -> str:
        """Markdown 後處理"""
        # 清理多餘的空行
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = line.strip() == ''
            if not (is_empty and prev_empty):
                cleaned_lines.append(line)
            prev_empty = is_empty
        
        return '\n'.join(cleaned_lines)
```

#### 3.1.2 具體轉換器實現

```python
class MarkdownifyConverter(HTMLToMarkdownConverter):
    """基於 markdownify 的轉換器"""
    
    def __init__(self, config: ConversionConfig):
        super().__init__(config)
        import markdownify
        self.markdownify = markdownify
    
    async def convert(self, html_content: str, url: str = "") -> str:
        """使用 markdownify 進行轉換"""
        try:
            # 預處理
            html_content = await self.preprocess_html(html_content)
            
            # 配置轉換選項
            options = {
                'heading_style': 'ATX',
                'bullets': '-',
                'strip': self.config.strip_tags or [],
                'convert': ['a', 'b', 'strong', 'i', 'em', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            }
            
            if self.config.include_tables:
                options['convert'].extend(['table', 'thead', 'tbody', 'tr', 'th', 'td'])
            
            if self.config.include_images:
                options['convert'].append('img')
            
            # 執行轉換
            markdown = self.markdownify.markdownify(
                html_content,
                **options
            )
            
            # 後處理
            markdown = await self.postprocess_markdown(markdown)
            
            # LLM 處理 (如果啟用)
            if self.config.enable_llm_processing:
                markdown = await self.llm_enhance_content(markdown)
            
            return markdown
            
        except Exception as e:
            self.logger.error(f"Markdownify 轉換失敗: {e}")
            raise
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            return len(soup.get_text().strip()) > 0
        except Exception:
            return False
    
    async def llm_enhance_content(self, markdown: str) -> str:
        """使用 LLM 增強內容結構"""
        # 這裡可以整合 OpenAI 或其他 LLM API
        # 進行內容結構化、摘要生成等
        return markdown

class TrafilaturaConverter(HTMLToMarkdownConverter):
    """基於 trafilatura 的轉換器 (專業內容提取)"""
    
    def __init__(self, config: ConversionConfig):
        super().__init__(config)
        import trafilatura
        self.trafilatura = trafilatura
    
    async def convert(self, html_content: str, url: str = "") -> str:
        """使用 trafilatura 進行轉換"""
        try:
            # 使用 trafilatura 提取主要內容
            extracted = self.trafilatura.extract(
                html_content,
                output_format='markdown',
                include_images=self.config.include_images,
                include_links=self.config.include_links,
                include_tables=self.config.include_tables
            )
            
            if not extracted:
                raise ValueError("無法提取內容")
            
            # 後處理
            markdown = await self.postprocess_markdown(extracted)
            
            return markdown
            
        except Exception as e:
            self.logger.error(f"Trafilatura 轉換失敗: {e}")
            raise
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容"""
        try:
            extracted = self.trafilatura.extract(html_content)
            return extracted is not None and len(extracted.strip()) > 0
        except Exception:
            return False
```

### 3.2 網站特定適配器系統

#### 3.2.1 適配器配置

```yaml
# config/site_adapters.yaml
site_adapters:
  sslproxies.org:
    name: "SSL Proxies"
    selectors:
      main_content: "#proxylisttable"
      title: "h1"
      pagination: ".pagination"
    conversion:
      engine: "markdownify"
      include_tables: true
      include_images: false
      custom_rules:
        - remove_ads: true
        - clean_navigation: true
    preprocessing:
      remove_tags: ["script", "style", "nav", "footer"]
      clean_attributes: ["onclick", "onload"]
  
  geonode.com:
    name: "Geonode Free Proxy"
    selectors:
      main_content: ".table-responsive"
      title: "h2.page-title"
    conversion:
      engine: "trafilatura"
      include_tables: true
      enable_llm_processing: true
    dynamic_content:
      enabled: true
      wait_for: ".table-responsive table"
      timeout: 10000
  
  default:
    name: "Default Adapter"
    selectors:
      main_content: "main, article, .content, #content"
      title: "h1, title"
    conversion:
      engine: "readability"
      scope: "main_content"
```

#### 3.2.2 適配器實現

```python
from typing import Dict, Any
import yaml
from pathlib import Path

class SiteAdapter:
    """網站特定適配器"""
    
    def __init__(self, site_config: Dict[str, Any]):
        self.config = site_config
        self.name = site_config.get('name', 'Unknown')
        self.selectors = site_config.get('selectors', {})
        self.conversion_config = site_config.get('conversion', {})
        self.preprocessing = site_config.get('preprocessing', {})
        self.dynamic_content = site_config.get('dynamic_content', {})
    
    async def extract_content(self, html_content: str, url: str) -> str:
        """提取網站特定內容"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 預處理：移除不需要的標籤
        if 'remove_tags' in self.preprocessing:
            for tag_name in self.preprocessing['remove_tags']:
                for tag in soup.find_all(tag_name):
                    tag.decompose()
        
        # 提取主要內容
        main_selector = self.selectors.get('main_content')
        if main_selector:
            content_element = soup.select_one(main_selector)
            if content_element:
                return str(content_element)
        
        # 回退到整個 body
        return str(soup.body) if soup.body else html_content
    
    def get_conversion_config(self) -> ConversionConfig:
        """獲取轉換配置"""
        engine_name = self.conversion_config.get('engine', 'markdownify')
        engine = ConversionEngine(engine_name)
        
        return ConversionConfig(
            engine=engine,
            include_images=self.conversion_config.get('include_images', True),
            include_links=self.conversion_config.get('include_links', True),
            include_tables=self.conversion_config.get('include_tables', True),
            include_title=self.conversion_config.get('include_title', True),
            enable_llm_processing=self.conversion_config.get('enable_llm_processing', False)
        )
    
    def requires_dynamic_rendering(self) -> bool:
        """是否需要動態渲染"""
        return self.dynamic_content.get('enabled', False)

class SiteAdapterManager:
    """網站適配器管理器"""
    
    def __init__(self, config_path: str = "config/site_adapters.yaml"):
        self.config_path = Path(config_path)
        self.adapters: Dict[str, SiteAdapter] = {}
        self.load_adapters()
    
    def load_adapters(self):
        """載入適配器配置"""
        if not self.config_path.exists():
            logger.warning(f"適配器配置文件不存在: {self.config_path}")
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        for site_key, site_config in config.get('site_adapters', {}).items():
            self.adapters[site_key] = SiteAdapter(site_config)
        
        logger.info(f"載入了 {len(self.adapters)} 個網站適配器")
    
    def get_adapter(self, url: str) -> SiteAdapter:
        """根據 URL 獲取適配器"""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower()
        
        # 精確匹配
        if domain in self.adapters:
            return self.adapters[domain]
        
        # 部分匹配
        for site_key, adapter in self.adapters.items():
            if site_key in domain:
                return adapter
        
        # 返回默認適配器
        return self.adapters.get('default', SiteAdapter({
            'name': 'Default',
            'conversion': {'engine': 'markdownify'}
        }))
```

### 3.3 ETL 流程整合

#### 3.3.1 ETL 整合介面

```python
class HTMLToMarkdownETLProcessor:
    """HTML to Markdown ETL 處理器"""
    
    def __init__(self):
        self.adapter_manager = SiteAdapterManager()
        self.converters = self._initialize_converters()
        self.cache = {}  # 可以整合 Redis
    
    def _initialize_converters(self) -> Dict[ConversionEngine, HTMLToMarkdownConverter]:
        """初始化轉換器"""
        return {
            ConversionEngine.MARKDOWNIFY: MarkdownifyConverter,
            ConversionEngine.TRAFILATURA: TrafilaturaConverter,
            # 可以添加更多轉換器
        }
    
    async def process_html_to_markdown(
        self, 
        html_content: str, 
        url: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """處理 HTML 轉 Markdown 的完整 ETL 流程"""
        
        try:
            # 1. Extract: 獲取網站適配器
            adapter = self.adapter_manager.get_adapter(url)
            logger.info(f"使用適配器: {adapter.name} for {url}")
            
            # 2. Transform: 提取和轉換內容
            # 2.1 提取網站特定內容
            extracted_html = await adapter.extract_content(html_content, url)
            
            # 2.2 獲取轉換配置
            conversion_config = adapter.get_conversion_config()
            
            # 2.3 選擇轉換器
            converter_class = self.converters[conversion_config.engine]
            converter = converter_class(conversion_config)
            
            # 2.4 執行轉換
            markdown_content = await converter.convert(extracted_html, url)
            
            # 3. Load: 準備輸出數據
            result = {
                'success': True,
                'url': url,
                'adapter_used': adapter.name,
                'conversion_engine': conversion_config.engine.value,
                'markdown_content': markdown_content,
                'content_length': len(markdown_content),
                'processing_timestamp': datetime.utcnow().isoformat(),
                'metadata': {
                    'original_html_size': len(html_content),
                    'extracted_html_size': len(extracted_html),
                    'compression_ratio': len(markdown_content) / len(html_content)
                }
            }
            
            # 快取結果
            cache_key = f"html2md:{hash(url + html_content)}"
            self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"HTML to Markdown 處理失敗 {url}: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'processing_timestamp': datetime.utcnow().isoformat()
            }
    
    async def batch_process(
        self, 
        html_url_pairs: List[tuple],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """批次處理多個 HTML 內容"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(html_content: str, url: str):
            async with semaphore:
                return await self.process_html_to_markdown(html_content, url)
        
        tasks = [
            process_single(html, url) 
            for html, url in html_url_pairs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'url': html_url_pairs[i][1],
                    'error': str(result),
                    'processing_timestamp': datetime.utcnow().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results
```

## 4. 操作流程說明

### 4.1 基本使用流程

```python
# 使用示例
async def main():
    # 1. 初始化處理器
    processor = HTMLToMarkdownETLProcessor()
    
    # 2. 處理單個網頁
    html_content = "<html>...</html>"
    url = "https://www.sslproxies.org"
    
    result = await processor.process_html_to_markdown(html_content, url)
    
    if result['success']:
        print(f"轉換成功，Markdown 長度: {result['content_length']}")
        print(f"使用適配器: {result['adapter_used']}")
        print(f"轉換引擎: {result['conversion_engine']}")
        
        # 保存結果
        with open(f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", 'w', encoding='utf-8') as f:
            f.write(result['markdown_content'])
    else:
        print(f"轉換失敗: {result['error']}")
    
    # 3. 批次處理
    html_url_pairs = [
        (html1, url1),
        (html2, url2),
        # ...
    ]
    
    batch_results = await processor.batch_process(html_url_pairs)
    
    success_count = sum(1 for r in batch_results if r['success'])
    print(f"批次處理完成: {success_count}/{len(batch_results)} 成功")

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.2 與現有 ETL 流程整合

```python
# 在現有的 ETL 流程中整合
class ProxyETLPipeline:
    def __init__(self):
        self.html_processor = HTMLToMarkdownETLProcessor()
    
    async def extract_phase(self, url: str) -> str:
        """Extract 階段：獲取 HTML 內容"""
        # 現有的 HTML 獲取邏輯
        html_content = await self.fetch_html(url)
        return html_content
    
    async def transform_phase(self, html_content: str, url: str) -> Dict[str, Any]:
        """Transform 階段：包含 HTML to Markdown 轉換"""
        # 1. HTML to Markdown 轉換
        markdown_result = await self.html_processor.process_html_to_markdown(
            html_content, url
        )
        
        if not markdown_result['success']:
            raise ValueError(f"HTML to Markdown 轉換失敗: {markdown_result['error']}")
        
        # 2. 從 Markdown 中提取代理數據
        proxy_data = await self.extract_proxy_from_markdown(
            markdown_result['markdown_content']
        )
        
        # 3. 數據清理和驗證
        cleaned_data = await self.clean_proxy_data(proxy_data)
        
        return {
            'markdown_content': markdown_result['markdown_content'],
            'proxy_data': cleaned_data,
            'metadata': markdown_result['metadata']
        }
    
    async def extract_proxy_from_markdown(self, markdown: str) -> List[Dict]:
        """從 Markdown 中提取代理數據"""
        # 使用正則表達式或 LLM 解析 Markdown 表格
        # 提取 IP、端口、協議等信息
        pass
```

## 5. 擴展性設計

### 5.1 添加新網站支援

1. **配置文件擴展**：在 `site_adapters.yaml` 中添加新網站配置
2. **自定義選擇器**：定義網站特定的 CSS 選擇器
3. **轉換規則**：配置適合該網站的轉換參數
4. **測試驗證**：編寫測試用例確保轉換品質

### 5.2 新轉換引擎整合

```python
class CustomConverter(HTMLToMarkdownConverter):
    """自定義轉換器示例"""
    
    async def convert(self, html_content: str, url: str = "") -> str:
        # 實現自定義轉換邏輯
        pass
    
    def validate_html(self, html_content: str) -> bool:
        # 實現驗證邏輯
        pass

# 註冊新轉換器
ConversionEngine.CUSTOM_NEW = "custom_new"
processor.converters[ConversionEngine.CUSTOM_NEW] = CustomConverter
```

## 6. 監控與維護

### 6.1 性能監控

```python
class PerformanceMonitor:
    """性能監控"""
    
    def __init__(self):
        self.metrics = {
            'conversion_times': [],
            'success_rates': {},
            'error_counts': {},
            'content_sizes': []
        }
    
    def record_conversion(self, result: Dict[str, Any], duration: float):
        """記錄轉換結果"""
        self.metrics['conversion_times'].append(duration)
        
        adapter = result.get('adapter_used', 'unknown')
        if adapter not in self.metrics['success_rates']:
            self.metrics['success_rates'][adapter] = {'success': 0, 'total': 0}
        
        self.metrics['success_rates'][adapter]['total'] += 1
        if result['success']:
            self.metrics['success_rates'][adapter]['success'] += 1
        
        if 'content_length' in result:
            self.metrics['content_sizes'].append(result['content_length'])
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        return {
            'avg_conversion_time': sum(self.metrics['conversion_times']) / len(self.metrics['conversion_times']),
            'success_rates': {
                adapter: data['success'] / data['total']
                for adapter, data in self.metrics['success_rates'].items()
            },
            'avg_content_size': sum(self.metrics['content_sizes']) / len(self.metrics['content_sizes'])
        }
```

### 6.2 錯誤處理與恢復

```python
class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self):
        self.retry_strategies = {
            'network_error': {'max_retries': 3, 'backoff': 2},
            'parsing_error': {'max_retries': 1, 'fallback_engine': True},
            'conversion_error': {'max_retries': 2, 'simplify_content': True}
        }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理錯誤並嘗試恢復"""
        error_type = self.classify_error(error)
        strategy = self.retry_strategies.get(error_type, {})
        
        if strategy.get('fallback_engine'):
            # 嘗試使用備用轉換引擎
            return await self.try_fallback_conversion(context)
        
        if strategy.get('simplify_content'):
            # 簡化內容後重試
            return await self.try_simplified_conversion(context)
        
        # 記錄錯誤並返回失敗結果
        logger.error(f"無法恢復的錯誤: {error}")
        return {'success': False, 'error': str(error)}
```

## 7. 總結

本實現方案提供了一個完整的、可擴展的 HTML to Markdown 轉換系統，具有以下特點：

1. **模組化設計**：核心轉換引擎、網站適配器、ETL 整合分離
2. **多引擎支援**：支援多種轉換引擎，可根據需求選擇
3. **網站特定優化**：通過配置文件支援不同網站的特殊需求
4. **異步處理**：支援高併發處理，提升性能
5. **ETL 整合**：無縫整合到現有的代理爬蟲 ETL 流程
6. **可擴展性**：易於添加新網站支援和新轉換引擎
7. **監控與維護**：內建性能監控和錯誤處理機制

這個系統將大大提升代理爬蟲系統處理複雜網頁內容的能力，並為未來的 LLM 整合奠定基礎。