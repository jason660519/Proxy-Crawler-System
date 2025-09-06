# HTML to Markdown 轉換系統 - 部署與使用指南

## 專案概述

本專案基於 LLMFeeder 瀏覽器擴展的經驗，開發了一個通用的 HTML to Markdown 轉換系統，能夠處理多個指定網站的內容轉換，並整合到 ETL 流程中。

### 核心特性

- **多引擎支援**：支援 Markdownify、Trafilatura、HTML2Text、Readability 等轉換引擎
- **網站特定適配器**：針對 Medium、GitHub 等網站的專門優化
- **智能內容提取**：自動識別主要內容區域，過濾廣告和導航元素
- **品質評估**：自動評估轉換結果的品質
- **ETL 整合**：完整的 Extract-Transform-Load 流程支援
- **容器化部署**：支援 Docker 容器化部署
- **命令行工具**：提供便捷的 CLI 介面

## 系統架構

```
HTML to Markdown 轉換系統
├── 核心轉換引擎 (Core)
│   ├── HTMLToMarkdownConverter (抽象基類)
│   ├── ConversionConfig (配置管理)
│   └── ConversionResult (結果封裝)
├── 轉換器實現 (Converters)
│   ├── MarkdownifyConverter
│   ├── TrafilaturaConverter
│   ├── HTML2TextConverter
│   └── ReadabilityConverter
├── 網站適配器 (Adapters)
│   ├── GenericAdapter (通用適配器)
│   ├── MediumAdapter (Medium 專用)
│   ├── GitHubAdapter (GitHub 專用)
│   └── AdapterManager (適配器管理)
├── ETL 處理器 (ETL Processor)
│   ├── HTMLToMarkdownETLProcessor
│   ├── ETLConfig
│   └── ETLResult
├── 工具類 (Utils)
│   ├── HTMLCleaner (HTML 清理)
│   ├── ContentExtractor (內容提取)
│   ├── QualityAssessment (品質評估)
│   └── URLProcessor (URL 處理)
└── 命令行工具 (CLI)
    └── 完整的命令行介面
```

## 安裝與設置

### 1. 環境要求

- Python 3.11+
- Windows 10/11 或 Linux
- 8GB+ RAM（推薦）
- 2GB+ 可用磁碟空間

### 2. 安裝依賴

#### 使用 uv（推薦）

```bash
# 創建虛擬環境
uv venv

# 啟動虛擬環境
uv shell

# 安裝依賴
uv pip install -r requirements_html_to_markdown.txt
```

#### 使用 pip

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境（Windows）
venv\Scripts\activate

# 啟動虛擬環境（Linux/Mac）
source venv/bin/activate

# 安裝依賴
pip install -r requirements_html_to_markdown.txt
```

### 3. 驗證安裝

```bash
# 測試基本功能
python -c "import html_to_markdown; print('安裝成功！')"

# 運行測試套件
pytest tests/test_html_to_markdown.py -v
```

## 使用方式

### 1. 基本使用

#### Python API

```python
import asyncio
from html_to_markdown import quick_convert

async def main():
    html = """
    <html>
        <body>
            <h1>測試標題</h1>
            <p>這是一段測試內容。</p>
        </body>
    </html>
    """
    
    result = await quick_convert(html)
    
    if result.success:
        print("轉換成功！")
        print(result.markdown_content)
    else:
        print(f"轉換失敗：{result.error_message}")

asyncio.run(main())
```

#### 命令行工具

```bash
# 轉換單個文件
python src/html_to_markdown/cli.py convert input.html -o output.md

# 批次轉換目錄
python src/html_to_markdown/cli.py batch-convert ./html_files/ -o ./markdown_files/

# 從 URL 獲取並轉換
python src/html_to_markdown/cli.py convert-url https://medium.com/@author/article -o article.md

# 分析 HTML 文件品質
python src/html_to_markdown/cli.py analyze input.html

# 列出可用的轉換引擎
python src/html_to_markdown/cli.py list-engines
```

### 2. 進階使用

#### 自定義配置

```python
from html_to_markdown.core import ConversionConfig, ConversionEngine, ContentScope
from html_to_markdown.etl_processor import HTMLToMarkdownETLProcessor, ETLConfig

# 創建自定義配置
conversion_config = ConversionConfig(
    engine=ConversionEngine.TRAFILATURA,
    content_scope=ContentScope.MAIN_CONTENT,
    remove_images=False,
    preserve_links=True,
    custom_selectors={
        'content': 'article, .post-content, .entry-content',
        'title': 'h1, .title, .post-title'
    }
)

etl_config = ETLConfig(
    output_directory='./output',
    save_results=True,
    enable_quality_assessment=True,
    min_quality_score=0.6
)

# 創建 ETL 處理器
processor = HTMLToMarkdownETLProcessor(etl_config)

# 處理 HTML 內容
result = await processor.process_html_content(
    html_content,
    url='https://example.com/article',
    conversion_config=conversion_config
)
```

#### 網站特定處理

```python
from html_to_markdown.adapters import AdapterManager

# 自動選擇適配器
manager = AdapterManager()
adapter = manager.get_adapter(url, html_content)

# 使用適配器預處理
processed_html = adapter.preprocess_html(html_content)
config = adapter.get_conversion_config()

# 轉換
result = await processor.process_html_content(
    processed_html,
    url=url,
    conversion_config=config
)
```

### 3. 批次處理

```python
from html_to_markdown import batch_convert_directory

# 批次轉換目錄中的所有 HTML 文件
results = await batch_convert_directory(
    input_directory='./html_files',
    output_directory='./markdown_files',
    engine=ConversionEngine.MARKDOWNIFY
)

# 處理結果
for result in results:
    if result.success:
        print(f"✓ {result.source_file} -> {result.output_file}")
    else:
        print(f"✗ {result.source_file}: {result.error_message}")
```

## Docker 部署

### 1. 構建映像

```bash
# 進入專案根目錄
cd JasonSpider

# 構建 Docker 映像
docker build -f docker/html-to-markdown/Dockerfile -t html-to-markdown:latest .
```

### 2. 使用 Docker Compose

```bash
# 進入 Docker 目錄
cd docker/html-to-markdown

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f html-to-markdown

# 停止服務
docker-compose down
```

### 3. 容器使用

```bash
# 運行單次轉換
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output \
    html-to-markdown:latest \
    python src/html_to_markdown/cli.py convert /app/input/file.html -o /app/output/file.md

# 批次處理
docker run --rm -v $(pwd)/html_files:/app/input -v $(pwd)/markdown_files:/app/output \
    html-to-markdown:latest \
    python src/html_to_markdown/cli.py batch-convert /app/input -o /app/output
```

## 與 ETL 流程整合

### 1. 在爬蟲系統中整合

```python
from html_to_markdown.etl_processor import HTMLToMarkdownETLProcessor
from your_crawler import WebCrawler

class EnhancedWebCrawler(WebCrawler):
    def __init__(self):
        super().__init__()
        self.html_processor = HTMLToMarkdownETLProcessor()
    
    async def process_page(self, url: str, html: str):
        # 原有的爬蟲處理邏輯
        raw_data = await super().process_page(url, html)
        
        # HTML to Markdown 轉換
        markdown_result = await self.html_processor.process_html_content(
            html, url
        )
        
        # 整合結果
        if markdown_result.success:
            raw_data['markdown_content'] = markdown_result.markdown_content
            raw_data['structured_data'] = markdown_result.structured_data
            raw_data['quality_score'] = markdown_result.quality_score
        
        return raw_data
```

### 2. 與 LLM 上下文管理整合

```python
from html_to_markdown import quick_convert

class LLMContextManager:
    async def prepare_context_from_url(self, url: str) -> str:
        # 獲取網頁內容
        html = await self.fetch_html(url)
        
        # 轉換為 Markdown
        result = await quick_convert(html, url=url)
        
        if result.success:
            # 格式化為 LLM 上下文
            context = f"""
            # 來源：{url}
            # 標題：{result.structured_data.get('title', '未知')}
            # 作者：{result.structured_data.get('author', '未知')}
            # 品質評分：{result.quality_score:.2f}
            
            ## 內容
            
            {result.markdown_content}
            """
            return context
        else:
            raise Exception(f"轉換失敗：{result.error_message}")
```

## 擴展性設計

### 1. 新增網站適配器

```python
from html_to_markdown.adapters import WebsiteAdapter
from html_to_markdown.core import ConversionConfig

class CustomWebsiteAdapter(WebsiteAdapter):
    def detect_website(self, url: str, html: str) -> bool:
        """檢測是否為目標網站"""
        return 'custom-website.com' in url
    
    def preprocess_html(self, html: str) -> str:
        """預處理 HTML"""
        # 移除特定的廣告區塊
        # 清理特殊格式
        return processed_html
    
    def get_conversion_config(self) -> ConversionConfig:
        """獲取轉換配置"""
        return ConversionConfig(
            engine=ConversionEngine.TRAFILATURA,
            custom_selectors={
                'content': '.article-content',
                'title': '.article-title'
            }
        )
    
    def extract_metadata(self, html: str) -> Dict[str, Any]:
        """提取元數據"""
        return {
            'website': 'CustomWebsite',
            'title': self._extract_title(html),
            'author': self._extract_author(html)
        }

# 註冊適配器
from html_to_markdown.adapters import AdapterManager
AdapterManager.register_adapter(CustomWebsiteAdapter())
```

### 2. 新增轉換引擎

```python
from html_to_markdown.core import HTMLToMarkdownConverter

class CustomConverter(HTMLToMarkdownConverter):
    async def convert(self, html: str, config: ConversionConfig) -> ConversionResult:
        """實現自定義轉換邏輯"""
        try:
            # 自定義轉換實現
            markdown = self._custom_conversion_logic(html, config)
            
            return ConversionResult(
                success=True,
                markdown=markdown,
                metadata={'engine': 'custom'}
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=str(e)
            )
```

## 監控與維護

### 1. 日誌配置

```python
from loguru import logger

# 配置日誌
logger.add(
    "logs/html_to_markdown_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)
```

### 2. 性能監控

```python
import time
from prometheus_client import Counter, Histogram

# 定義監控指標
conversion_counter = Counter('html_conversions_total', 'Total conversions')
conversion_duration = Histogram('html_conversion_duration_seconds', 'Conversion duration')

class MonitoredETLProcessor(HTMLToMarkdownETLProcessor):
    async def process_html_content(self, html: str, url: str = None) -> ETLResult:
        start_time = time.time()
        
        try:
            result = await super().process_html_content(html, url)
            conversion_counter.inc()
            return result
        finally:
            conversion_duration.observe(time.time() - start_time)
```

### 3. 健康檢查

```python
class HealthChecker:
    async def check_system_health(self) -> Dict[str, Any]:
        """檢查系統健康狀態"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # 檢查轉換引擎
        try:
            test_html = '<h1>Test</h1>'
            result = await quick_convert(test_html)
            health_status['checks']['conversion'] = 'ok' if result.success else 'error'
        except Exception as e:
            health_status['checks']['conversion'] = f'error: {e}'
            health_status['status'] = 'unhealthy'
        
        return health_status
```

## 故障排除

### 常見問題

1. **轉換失敗**
   - 檢查 HTML 格式是否正確
   - 確認轉換引擎依賴是否安裝
   - 查看錯誤日誌獲取詳細信息

2. **品質評分過低**
   - 調整內容選擇器
   - 使用不同的轉換引擎
   - 檢查網站適配器是否正確

3. **性能問題**
   - 啟用緩存機制
   - 調整並發處理數量
   - 優化 HTML 預處理邏輯

### 調試技巧

```python
# 啟用詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 保存中間結果
config = ETLConfig(
    save_intermediate_results=True,
    debug_mode=True
)

# 分步驟調試
from html_to_markdown.utils import HTMLCleaner, ContentExtractor

cleaner = HTMLCleaner()
extractor = ContentExtractor()

# 1. 清理 HTML
cleaned_html = cleaner.clean_html(original_html)
print("清理後的 HTML:", cleaned_html[:500])

# 2. 提取主要內容
main_content = extractor.extract_main_content(cleaned_html)
print("主要內容:", main_content[:500])

# 3. 轉換為 Markdown
result = await quick_convert(main_content)
print("轉換結果:", result.markdown_content[:500])
```

## 總結

本 HTML to Markdown 轉換系統提供了完整的解決方案，從基本的 HTML 轉換到複雜的 ETL 流程整合。系統具有以下優勢：

1. **模組化設計**：易於擴展和維護
2. **多引擎支援**：適應不同的轉換需求
3. **網站特定優化**：針對主流網站的專門處理
4. **品質保證**：自動評估和優化轉換結果
5. **容器化部署**：支援現代化的部署方式
6. **完整的監控**：提供全面的運行狀態監控

通過本系統，您可以輕鬆地將任何網站的 HTML 內容轉換為高品質的 Markdown 格式，為 LLM 應用提供清潔、結構化的上下文資訊。