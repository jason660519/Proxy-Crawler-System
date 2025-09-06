"""HTML to Markdown 轉換系統使用範例

展示如何使用 HTML to Markdown 轉換系統的各種功能，
包括單檔案轉換、批次處理、ETL 流程等。
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# 添加專案根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.html_to_markdown import (
    # 核心類
    ConversionConfig, ConversionEngine, ContentScope, OutputFormat,
    
    # 轉換器
    MarkdownifyConverter, TrafilaturaConverter, HTML2TextConverter,
    
    # 適配器
    SiteAdapterManager, MediumAdapter, GitHubAdapter,
    
    # ETL 處理器
    HTMLToMarkdownETLProcessor, ETLConfig,
    
    # 工具函數
    quick_convert, batch_convert_directory,
    quick_clean_html, extract_main_content, assess_content_quality
)
from loguru import logger


# 範例 HTML 內容
SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>範例文章 - HTML to Markdown 轉換測試</title>
    <meta name="description" content="這是一個用於測試 HTML to Markdown 轉換功能的範例文章。">
    <meta name="author" content="測試作者">
    <style>
        .sidebar { display: none; }
        .ads { background: yellow; }
    </style>
</head>
<body>
    <header>
        <nav>
            <ul>
                <li><a href="#home">首頁</a></li>
                <li><a href="#about">關於</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <article>
            <h1>HTML to Markdown 轉換系統介紹</h1>
            
            <p>這是一個功能強大的 <strong>HTML to Markdown</strong> 轉換系統，支援多種轉換引擎和網站適配器。</p>
            
            <h2>主要功能</h2>
            
            <ul>
                <li>支援多種轉換引擎（Trafilatura、Markdownify、HTML2Text 等）</li>
                <li>網站特定適配器（Medium、GitHub 等）</li>
                <li>完整的 ETL 流程支援</li>
                <li>內容品質評估</li>
                <li>批次處理功能</li>
            </ul>
            
            <h3>技術特色</h3>
            
            <p>系統採用 <em>異步處理</em> 架構，能夠高效處理大量檔案。同時提供豐富的配置選項，滿足不同場景的需求。</p>
            
            <blockquote>
                <p>「好的工具應該讓複雜的任務變得簡單。」</p>
            </blockquote>
            
            <h3>程式碼範例</h3>
            
            <pre><code class="language-python">
# 快速轉換範例
result = await quick_convert(html_content, url="https://example.com")
print(result.content)
            </code></pre>
            
            <p>更多資訊請參考 <a href="https://github.com/example/html-to-markdown">專案文檔</a>。</p>
            
            <p><img src="https://example.com/image.jpg" alt="範例圖片" title="這是一張範例圖片"></p>
        </article>
    </main>
    
    <aside class="sidebar">
        <div class="ads">
            <p>廣告內容</p>
        </div>
    </aside>
    
    <footer>
        <p>&copy; 2024 HTML to Markdown 轉換系統</p>
    </footer>
    
    <script>
        console.log("這段 JavaScript 應該被移除");
    </script>
</body>
</html>
"""


async def example_basic_conversion():
    """基本轉換範例"""
    print("\n=== 基本轉換範例 ===")
    
    # 使用預設配置進行快速轉換
    result = await quick_convert(SAMPLE_HTML, url="https://example.com")
    
    print(f"轉換成功: {result.success}")
    print(f"使用引擎: {result.engine_used.value}")
    print(f"原始長度: {result.original_length}")
    print(f"轉換長度: {result.converted_length}")
    print(f"處理時間: {result.processing_time:.3f}s")
    print(f"標題: {result.title}")
    
    print("\n轉換結果:")
    print("-" * 50)
    print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
    print("-" * 50)


async def example_custom_config():
    """自訂配置轉換範例"""
    print("\n=== 自訂配置轉換範例 ===")
    
    # 建立自訂配置
    config = ConversionConfig(
        engine=ConversionEngine.MARKDOWNIFY,
        content_scope=ContentScope.MAIN_CONTENT,
        output_format=OutputFormat.MARKDOWN,
        include_links=True,
        include_images=True,
        strip_tags=['script', 'style', 'nav', 'footer'],
        custom_options={
            'heading_style': 'ATX',
            'bullet_style': '-'
        }
    )
    
    # 建立轉換器
    try:
        converter = MarkdownifyConverter(config)
        result = await converter.convert(SAMPLE_HTML, "https://example.com")
        
        print(f"轉換成功: {result.success}")
        print(f"使用引擎: {result.engine_used.value}")
        
        if result.success:
            print("\n自訂配置轉換結果:")
            print("-" * 50)
            print(result.content[:300] + "..." if len(result.content) > 300 else result.content)
            print("-" * 50)
        else:
            print(f"轉換失敗: {result.error_message}")
            
    except ImportError:
        print("Markdownify 未安裝，跳過此範例")


async def example_multiple_engines():
    """多引擎比較範例"""
    print("\n=== 多引擎比較範例 ===")
    
    engines = [
        ConversionEngine.TRAFILATURA,
        ConversionEngine.MARKDOWNIFY,
        ConversionEngine.HTML2TEXT
    ]
    
    results = {}
    
    for engine in engines:
        try:
            config = ConversionConfig(engine=engine)
            
            if engine == ConversionEngine.TRAFILATURA:
                converter = TrafilaturaConverter(config)
            elif engine == ConversionEngine.MARKDOWNIFY:
                converter = MarkdownifyConverter(config)
            elif engine == ConversionEngine.HTML2TEXT:
                converter = HTML2TextConverter(config)
            else:
                continue
            
            result = await converter.convert(SAMPLE_HTML, "https://example.com")
            results[engine.value] = result
            
            print(f"\n{engine.value}:")
            print(f"  成功: {result.success}")
            print(f"  長度: {result.converted_length}")
            print(f"  時間: {result.processing_time:.3f}s")
            
        except ImportError:
            print(f"\n{engine.value}: 未安裝，跳過")
        except Exception as e:
            print(f"\n{engine.value}: 錯誤 - {e}")
    
    # 比較結果
    if results:
        print("\n引擎比較:")
        for engine_name, result in results.items():
            if result.success:
                quality = assess_content_quality(result.content, is_markdown=True)
                print(f"  {engine_name}: 品質分數 {quality.score:.2f}, 字數 {quality.word_count}")


async def example_site_adapters():
    """網站適配器範例"""
    print("\n=== 網站適配器範例 ===")
    
    # Medium 風格的 HTML
    medium_html = """
    <article>
        <div class="meteredContent">
            <h1>Medium 文章標題</h1>
            <div class="subtitle">這是副標題</div>
            <div class="author-info">
                <span class="author-name">作者名稱</span>
                <span class="publish-date">2024-01-15</span>
            </div>
            <div class="article-content">
                <p>這是 Medium 文章的內容...</p>
                <p>支援 <strong>粗體</strong> 和 <em>斜體</em> 文字。</p>
            </div>
        </div>
    </article>
    """
    
    # 使用 Medium 適配器
    adapter_manager = SiteAdapterManager()
    adapter_manager.register_adapter("medium.com", MediumAdapter())
    
    try:
        processed_html, metadata = await adapter_manager.extract_content(
            medium_html, "https://medium.com/@author/article"
        )
        
        print("Medium 適配器處理結果:")
        print(f"  提取的元數據: {metadata}")
        print(f"  處理後 HTML 長度: {len(processed_html)}")
        
        # 轉換為 Markdown
        result = await quick_convert(processed_html, "https://medium.com/@author/article")
        if result.success:
            print("\n轉換結果:")
            print("-" * 30)
            print(result.content[:200] + "..." if len(result.content) > 200 else result.content)
            print("-" * 30)
            
    except Exception as e:
        print(f"適配器處理失敗: {e}")


async def example_content_quality():
    """內容品質評估範例"""
    print("\n=== 內容品質評估範例 ===")
    
    # 評估原始 HTML
    html_quality = assess_content_quality(SAMPLE_HTML, is_markdown=False)
    print("原始 HTML 品質:")
    print(f"  品質分數: {html_quality.score:.2f}")
    print(f"  字數: {html_quality.word_count}")
    print(f"  段落數: {html_quality.paragraph_count}")
    print(f"  有標題: {html_quality.has_title}")
    print(f"  文字比例: {html_quality.text_to_html_ratio:.2f}")
    print(f"  可讀性: {html_quality.readability_score:.2f}")
    if html_quality.issues:
        print(f"  問題: {', '.join(html_quality.issues)}")
    
    # 轉換並評估 Markdown
    result = await quick_convert(SAMPLE_HTML)
    if result.success:
        markdown_quality = assess_content_quality(result.content, is_markdown=True)
        print("\n轉換後 Markdown 品質:")
        print(f"  品質分數: {markdown_quality.score:.2f}")
        print(f"  字數: {markdown_quality.word_count}")
        print(f"  段落數: {markdown_quality.paragraph_count}")
        print(f"  有標題: {markdown_quality.has_title}")
        print(f"  可讀性: {markdown_quality.readability_score:.2f}")
        if markdown_quality.issues:
            print(f"  問題: {', '.join(markdown_quality.issues)}")


async def example_etl_processing():
    """ETL 處理範例"""
    print("\n=== ETL 處理範例 ===")
    
    # 建立測試檔案
    test_dir = Path("temp_test_html")
    test_dir.mkdir(exist_ok=True)
    
    # 建立多個測試 HTML 檔案
    test_files = []
    for i in range(3):
        test_file = test_dir / f"test_{i+1}.html"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_HTML.replace("範例文章", f"範例文章 {i+1}"))
        test_files.append(str(test_file))
    
    try:
        # 建立 ETL 配置
        etl_config = ETLConfig(
            input_directory=str(test_dir),
            output_directory="temp_test_output",
            primary_engine=ConversionEngine.TRAFILATURA,
            batch_size=2,
            max_concurrent=2,
            enable_caching=True
        )
        
        # 建立 ETL 處理器
        processor = HTMLToMarkdownETLProcessor(etl_config)
        
        # 處理目錄
        etl_result = await processor.process_directory()
        
        print(f"ETL 處理結果:")
        print(f"  總檔案數: {etl_result.total_files}")
        print(f"  成功轉換: {etl_result.successful_conversions}")
        print(f"  失敗轉換: {etl_result.failed_conversions}")
        print(f"  成功率: {etl_result.success_rate:.2%}")
        print(f"  處理時間: {etl_result.processing_time:.2f}s")
        print(f"  輸出檔案: {len(etl_result.output_files)}")
        
        if etl_result.output_files:
            print("\n輸出檔案:")
            for output_file in etl_result.output_files:
                print(f"  - {output_file}")
        
        if etl_result.errors:
            print("\n錯誤:")
            for error in etl_result.errors:
                print(f"  - {error}")
        
        # 生成報告
        report_path = await processor.save_report(etl_result)
        print(f"\n處理報告已儲存: {report_path}")
        
    finally:
        # 清理測試檔案
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
        output_dir = Path("temp_test_output")
        if output_dir.exists():
            shutil.rmtree(output_dir)


async def example_utility_functions():
    """工具函數範例"""
    print("\n=== 工具函數範例 ===")
    
    # HTML 清理
    cleaned_html = quick_clean_html(SAMPLE_HTML, aggressive=True)
    print(f"原始 HTML 長度: {len(SAMPLE_HTML)}")
    print(f"清理後長度: {len(cleaned_html)}")
    
    # 主要內容提取
    main_content = extract_main_content(SAMPLE_HTML)
    print(f"主要內容長度: {len(main_content)}")
    
    # 顯示清理後的內容片段
    print("\n清理後的 HTML 片段:")
    print("-" * 30)
    print(cleaned_html[:300] + "..." if len(cleaned_html) > 300 else cleaned_html)
    print("-" * 30)


async def main():
    """主函數"""
    print("HTML to Markdown 轉換系統範例")
    print("=" * 50)
    
    try:
        # 執行各種範例
        await example_basic_conversion()
        await example_custom_config()
        await example_multiple_engines()
        await example_site_adapters()
        await example_content_quality()
        await example_etl_processing()
        await example_utility_functions()
        
        print("\n=== 所有範例執行完成 ===")
        
    except Exception as e:
        logger.error(f"範例執行失敗: {e}")
        raise


if __name__ == "__main__":
    # 配置日誌
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 執行範例
    asyncio.run(main())