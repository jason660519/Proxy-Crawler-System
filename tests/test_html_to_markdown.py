#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 轉換系統測試套件

這個模組包含了 HTML to Markdown 轉換系統的完整測試，
包括單元測試、整合測試和端到端測試。

Author: JasonSpider Team
Date: 2024
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# 導入要測試的模組
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from html_to_markdown.core import (
    HTMLToMarkdownConverter, ConversionConfig, ConversionResult,
    ConversionEngine, ContentScope, OutputFormat
)
from html_to_markdown.converters import (
    MarkdownifyConverter, TrafilaturaConverter, 
    HTML2TextConverter, ReadabilityConverter
)
from html_to_markdown.adapters import (
    WebsiteAdapter, AdapterManager, GenericAdapter,
    MediumAdapter, GitHubAdapter
)
from html_to_markdown.etl_processor import (
    HTMLToMarkdownETLProcessor, ETLConfig, ETLResult
)
from html_to_markdown.utils import (
    HTMLCleaner, ContentExtractor, QualityAssessment,
    URLProcessor, TextProcessor
)
from html_to_markdown import quick_convert, batch_convert_directory


class TestHTMLCleaner:
    """HTML 清理器測試類"""
    
    def setup_method(self):
        """設置測試環境"""
        self.cleaner = HTMLCleaner()
    
    def test_remove_scripts_and_styles(self):
        """測試移除腳本和樣式"""
        html = """
        <html>
            <head>
                <script>alert('test');</script>
                <style>body { color: red; }</style>
            </head>
            <body>
                <p>Content</p>
                <script>console.log('test');</script>
            </body>
        </html>
        """
        
        cleaned = self.cleaner.remove_scripts_and_styles(html)
        
        assert '<script>' not in cleaned
        assert '<style>' not in cleaned
        assert 'Content' in cleaned
    
    def test_remove_unwanted_elements(self):
        """測試移除不需要的元素"""
        html = """
        <div>
            <nav>Navigation</nav>
            <header>Header</header>
            <main>Main content</main>
            <footer>Footer</footer>
            <aside>Sidebar</aside>
        </div>
        """
        
        cleaned = self.cleaner.remove_unwanted_elements(html)
        
        assert 'Navigation' not in cleaned
        assert 'Header' not in cleaned
        assert 'Footer' not in cleaned
        assert 'Sidebar' not in cleaned
        assert 'Main content' in cleaned
    
    def test_clean_html_complete(self):
        """測試完整的 HTML 清理流程"""
        html = """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Test Page</title>
                <script>alert('test');</script>
            </head>
            <body>
                <nav>Navigation</nav>
                <main>
                    <h1>Title</h1>
                    <p>Content paragraph</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """
        
        cleaned = self.cleaner.clean_html(html)
        
        assert '<script>' not in cleaned
        assert 'Navigation' not in cleaned
        assert 'Footer' not in cleaned
        assert 'Title' in cleaned
        assert 'Content paragraph' in cleaned


class TestContentExtractor:
    """內容提取器測試類"""
    
    def setup_method(self):
        """設置測試環境"""
        self.extractor = ContentExtractor()
    
    def test_extract_main_content(self):
        """測試主要內容提取"""
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <main>
                    <h1>Main Title</h1>
                    <p>Main content paragraph</p>
                </main>
                <aside>Sidebar content</aside>
            </body>
        </html>
        """
        
        main_content = self.extractor.extract_main_content(html)
        
        assert 'Main Title' in main_content
        assert 'Main content paragraph' in main_content
        assert 'Navigation' not in main_content
        assert 'Sidebar content' not in main_content
    
    def test_extract_page_metadata(self):
        """測試頁面元數據提取"""
        html = """
        <html>
            <head>
                <title>Test Page Title</title>
                <meta name="description" content="Test page description">
                <meta name="author" content="Test Author">
                <meta name="keywords" content="test, html, metadata">
                <meta property="og:title" content="OG Title">
            </head>
            <body>
                <h1>Page Content</h1>
            </body>
        </html>
        """
        
        metadata = self.extractor.extract_page_metadata(html)
        
        assert metadata['title'] == 'Test Page Title'
        assert metadata['description'] == 'Test page description'
        assert metadata['author'] == 'Test Author'
        assert metadata['keywords'] == 'test, html, metadata'
        assert metadata['og_title'] == 'OG Title'


class TestQualityAssessment:
    """品質評估測試類"""
    
    def setup_method(self):
        """設置測試環境"""
        self.assessor = QualityAssessment()
    
    def test_assess_content_quality_high(self):
        """測試高品質內容評估"""
        content = """
        # 這是一篇高品質的文章
        
        這是一段很長的內容，包含了豐富的資訊和詳細的描述。
        文章結構清晰，段落分明，內容充實。
        
        ## 子標題
        
        更多詳細的內容說明，包含了具體的例子和解釋。
        這樣的內容對讀者來說是有價值的。
        """
        
        score = self.assessor.assess_content_quality(content)
        
        assert score > 0.7  # 高品質內容應該有較高評分
    
    def test_assess_content_quality_low(self):
        """測試低品質內容評估"""
        content = "短內容"
        
        score = self.assessor.assess_content_quality(content)
        
        assert score < 0.5  # 低品質內容應該有較低評分
    
    def test_calculate_readability_score(self):
        """測試可讀性評分計算"""
        text = "這是一個測試句子。它包含了一些基本的內容。"
        
        score = self.assessor.calculate_readability_score(text)
        
        assert 0 <= score <= 1  # 評分應該在 0-1 之間


class TestWebsiteAdapters:
    """網站適配器測試類"""
    
    def test_medium_adapter_detection(self):
        """測試 Medium 適配器檢測"""
        adapter = MediumAdapter()
        
        # 測試 URL 檢測
        assert adapter.detect_website('https://medium.com/article', '')
        assert adapter.detect_website('https://user.medium.com/post', '')
        
        # 測試 HTML 檢測
        html_with_medium = '<div data-testid="storyContent">Content</div>'
        assert adapter.detect_website('', html_with_medium)
        
        # 測試非 Medium 內容
        assert not adapter.detect_website('https://github.com/repo', '')
    
    def test_github_adapter_detection(self):
        """測試 GitHub 適配器檢測"""
        adapter = GitHubAdapter()
        
        # 測試 URL 檢測
        assert adapter.detect_website('https://github.com/user/repo', '')
        
        # 測試 HTML 檢測
        html_with_github = '<div class="markdown-body">Content</div>'
        assert adapter.detect_website('', html_with_github)
        
        # 測試非 GitHub 內容
        assert not adapter.detect_website('https://medium.com/article', '')
    
    def test_adapter_manager(self):
        """測試適配器管理器"""
        manager = AdapterManager()
        
        # 測試 Medium 適配器選擇
        adapter = manager.get_adapter('https://medium.com/article', '')
        assert isinstance(adapter, MediumAdapter)
        
        # 測試 GitHub 適配器選擇
        adapter = manager.get_adapter('https://github.com/user/repo', '')
        assert isinstance(adapter, GitHubAdapter)
        
        # 測試通用適配器選擇
        adapter = manager.get_adapter('https://example.com', '')
        assert isinstance(adapter, GenericAdapter)


class TestConverters:
    """轉換器測試類"""
    
    @pytest.fixture
    def sample_html(self):
        """測試用的 HTML 樣本"""
        return """
        <html>
            <body>
                <h1>Test Title</h1>
                <p>This is a test paragraph with <strong>bold</strong> text.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
                <a href="https://example.com">Link</a>
            </body>
        </html>
        """
    
    @pytest.mark.asyncio
    async def test_markdownify_converter(self, sample_html):
        """測試 Markdownify 轉換器"""
        converter = MarkdownifyConverter()
        config = ConversionConfig(engine=ConversionEngine.MARKDOWNIFY)
        
        result = await converter.convert(sample_html, config)
        
        assert result.success
        assert '# Test Title' in result.markdown
        assert '**bold**' in result.markdown
        assert '[Link](https://example.com)' in result.markdown
    
    @pytest.mark.asyncio
    async def test_html2text_converter(self, sample_html):
        """測試 HTML2Text 轉換器"""
        converter = HTML2TextConverter()
        config = ConversionConfig(engine=ConversionEngine.HTML2TEXT)
        
        result = await converter.convert(sample_html, config)
        
        assert result.success
        assert 'Test Title' in result.markdown
        assert 'bold' in result.markdown
    
    def test_converter_validation(self):
        """測試轉換器驗證功能"""
        converter = MarkdownifyConverter()
        
        # 測試有效 HTML
        assert converter.validate_html('<p>Valid HTML</p>')
        
        # 測試無效 HTML
        assert not converter.validate_html('')
        assert not converter.validate_html('   ')


class TestETLProcessor:
    """ETL 處理器測試類"""
    
    def setup_method(self):
        """設置測試環境"""
        self.config = ETLConfig(
            output_directory='./test_output',
            save_results=False,  # 測試時不保存檔案
            enable_quality_assessment=True
        )
        self.processor = HTMLToMarkdownETLProcessor(self.config)
    
    @pytest.mark.asyncio
    async def test_process_html_content(self):
        """測試 HTML 內容處理"""
        html = """
        <html>
            <body>
                <h1>Test Article</h1>
                <p>This is test content for ETL processing.</p>
            </body>
        </html>
        """
        
        result = await self.processor.process_html_content(html)
        
        assert isinstance(result, ETLResult)
        assert result.success
        assert 'Test Article' in result.markdown_content
        assert result.quality_score > 0
    
    @pytest.mark.asyncio
    async def test_process_with_url(self):
        """測試帶 URL 的處理"""
        html = '<div data-testid="storyContent"><h1>Medium Article</h1></div>'
        url = 'https://medium.com/test-article'
        
        result = await self.processor.process_html_content(html, url)
        
        assert result.success
        assert result.structured_data.get('website') == 'Medium'
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """測試錯誤處理"""
        # 測試無效 HTML
        result = await self.processor.process_html_content('')
        
        assert not result.success
        assert result.error_message


class TestQuickConvert:
    """快速轉換功能測試類"""
    
    @pytest.mark.asyncio
    async def test_quick_convert_basic(self):
        """測試基本快速轉換"""
        html = '<h1>Quick Test</h1><p>Quick conversion test.</p>'
        
        result = await quick_convert(html)
        
        assert result.success
        assert 'Quick Test' in result.markdown_content
    
    @pytest.mark.asyncio
    async def test_quick_convert_with_url(self):
        """測試帶 URL 的快速轉換"""
        html = '<div class="markdown-body"><h1>GitHub README</h1></div>'
        url = 'https://github.com/user/repo'
        
        result = await quick_convert(html, url=url)
        
        assert result.success
        assert result.structured_data.get('website') == 'GitHub'
    
    @pytest.mark.asyncio
    async def test_quick_convert_engine_selection(self):
        """測試轉換引擎選擇"""
        html = '<h1>Engine Test</h1><p>Testing engine selection.</p>'
        
        # 測試指定引擎
        result = await quick_convert(html, engine=ConversionEngine.MARKDOWNIFY)
        
        assert result.success
        assert result.metadata.get('engine') == 'MARKDOWNIFY'


class TestIntegration:
    """整合測試類"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_medium_article(self):
        """測試端到端 Medium 文章處理"""
        html = """
        <html>
            <head>
                <title>Test Medium Article</title>
            </head>
            <body>
                <article>
                    <div data-testid="storyContent">
                        <h1 data-testid="storyTitle">Amazing Article Title</h1>
                        <div data-testid="authorName">John Doe</div>
                        <time datetime="2024-01-01">January 1, 2024</time>
                        <p class="pw-post-body-paragraph">This is the article content.</p>
                        <p class="pw-post-body-paragraph">More content here.</p>
                    </div>
                </article>
            </body>
        </html>
        """
        
        url = 'https://medium.com/@author/amazing-article'
        
        # 使用 ETL 處理器進行完整處理
        config = ETLConfig(save_results=False)
        processor = HTMLToMarkdownETLProcessor(config)
        
        result = await processor.process_html_content(html, url)
        
        # 驗證結果
        assert result.success
        assert 'Amazing Article Title' in result.markdown_content
        assert result.structured_data['title'] == 'Amazing Article Title'
        assert result.structured_data['author'] == 'John Doe'
        assert result.structured_data['website'] == 'Medium'
        assert result.quality_score > 0.5
    
    @pytest.mark.asyncio
    async def test_end_to_end_github_readme(self):
        """測試端到端 GitHub README 處理"""
        html = """
        <html>
            <body>
                <div class="markdown-body">
                    <h1>Project Title</h1>
                    <p>Project description</p>
                    <h2>Installation</h2>
                    <pre><code>pip install package</code></pre>
                    <h2>Usage</h2>
                    <p>Usage instructions</p>
                </div>
            </body>
        </html>
        """
        
        url = 'https://github.com/user/project'
        
        result = await quick_convert(html, url=url)
        
        # 驗證結果
        assert result.success
        assert '# Project Title' in result.markdown_content
        assert '## Installation' in result.markdown_content
        assert '```' in result.markdown_content  # 代碼塊
        assert result.structured_data['website'] == 'GitHub'


class TestPerformance:
    """性能測試類"""
    
    @pytest.mark.asyncio
    async def test_conversion_performance(self):
        """測試轉換性能"""
        import time
        
        # 生成較大的 HTML 內容
        html_parts = ['<html><body>']
        for i in range(100):
            html_parts.append(f'<h2>Section {i}</h2>')
            html_parts.append(f'<p>Content for section {i} with some text.</p>')
        html_parts.append('</body></html>')
        
        large_html = ''.join(html_parts)
        
        start_time = time.time()
        result = await quick_convert(large_html)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert result.success
        assert processing_time < 5.0  # 應該在 5 秒內完成
    
    @pytest.mark.asyncio
    async def test_concurrent_conversions(self):
        """測試並發轉換"""
        html_samples = [
            '<h1>Article 1</h1><p>Content 1</p>',
            '<h1>Article 2</h1><p>Content 2</p>',
            '<h1>Article 3</h1><p>Content 3</p>',
            '<h1>Article 4</h1><p>Content 4</p>',
            '<h1>Article 5</h1><p>Content 5</p>'
        ]
        
        # 並發執行轉換
        tasks = [quick_convert(html) for html in html_samples]
        results = await asyncio.gather(*tasks)
        
        # 驗證所有轉換都成功
        assert len(results) == 5
        for i, result in enumerate(results, 1):
            assert result.success
            assert f'Article {i}' in result.markdown_content


class TestErrorHandling:
    """錯誤處理測試類"""
    
    @pytest.mark.asyncio
    async def test_empty_html_handling(self):
        """測試空 HTML 處理"""
        result = await quick_convert('')
        
        assert not result.success
        assert result.error_message
    
    @pytest.mark.asyncio
    async def test_malformed_html_handling(self):
        """測試格式錯誤的 HTML 處理"""
        malformed_html = '<html><body><h1>Title</h1><p>Unclosed paragraph</body></html>'
        
        result = await quick_convert(malformed_html)
        
        # 應該能夠處理格式錯誤的 HTML
        assert result.success or result.error_message
    
    @pytest.mark.asyncio
    async def test_network_timeout_simulation(self):
        """測試網路超時模擬"""
        # 這裡可以模擬網路請求超時的情況
        # 實際實現中可能需要 mock 網路請求
        pass


if __name__ == '__main__':
    # 運行測試
    pytest.main([__file__, '-v', '--tb=short'])