"""HTML to Markdown 轉換器具體實現

提供多種轉換引擎的具體實現，包括 Markdownify、Trafilatura、HTML2Text 等。
"""

import time
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger

from .core import HTMLToMarkdownConverter, ConversionResult, ConversionConfig, ConversionEngine


class MarkdownifyConverter(HTMLToMarkdownConverter):
    """基於 markdownify 的轉換器
    
    適用於大多數標準 HTML 內容的轉換，支援豐富的自定義選項。
    """
    
    def __init__(self, config: ConversionConfig):
        super().__init__(config)
        try:
            import markdownify
            self.markdownify = markdownify
        except ImportError:
            raise ImportError("請安裝 markdownify: pip install markdownify")
    
    async def convert(self, html_content: str, url: str = "") -> ConversionResult:
        """使用 markdownify 進行轉換"""
        start_time = time.time()
        
        try:
            # 驗證 HTML
            if not self.validate_html(html_content):
                return ConversionResult(
                    success=False,
                    content="",
                    original_length=len(html_content),
                    converted_length=0,
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.MARKDOWNIFY,
                    url=url,
                    error_message="無效的 HTML 內容"
                )
            
            # 預處理 HTML
            processed_html = await self.preprocess_html(html_content)
            
            # 提取標題
            title = await self.extract_title(processed_html) if self.config.include_title else ""
            
            # 配置轉換選項
            convert_tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'del', 'code', 'pre']
            
            if self.config.include_links:
                convert_tags.append('a')
            
            if self.config.include_images:
                convert_tags.append('img')
            
            if self.config.include_tables:
                convert_tags.extend(['table', 'thead', 'tbody', 'tr', 'th', 'td'])
            
            # 添加標題標籤
            convert_tags.extend(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            # 添加列表標籤
            convert_tags.extend(['ul', 'ol', 'li'])
            
            # 添加引用和分隔線
            convert_tags.extend(['blockquote', 'hr'])
            
            # 配置 markdownify 選項
            options = {
                'heading_style': 'ATX' if self.config.heading_style == 'ATX' else 'SETEXT',
                'bullets': self.config.bullet_style,
                'convert': convert_tags,
                'escape_asterisks': False,
                'escape_underscores': False
            }
            
            # 如果有需要移除的標籤，使用 strip 參數（不能與 convert 同時使用）
            if self.config.strip_tags:
                # 當指定 strip_tags 時，不使用 convert 參數
                options = {
                    'heading_style': 'ATX' if self.config.heading_style == 'ATX' else 'SETEXT',
                    'bullets': self.config.bullet_style,
                    'strip': self.config.strip_tags,
                    'escape_asterisks': False,
                    'escape_underscores': False
                }
            
            # 執行轉換
            markdown = self.markdownify.markdownify(
                processed_html,
                **options
            )
            
            # 後處理
            markdown = await self.postprocess_markdown(markdown)
            
            # 添加標題 (如果需要)
            if title and self.config.include_title:
                markdown = f"# {title}\n\n{markdown}"
            
            # LLM 處理 (如果啟用)
            if self.config.enable_llm_processing:
                markdown = await self.llm_enhance_content(markdown, url)
            
            # 檢查內容長度
            if len(markdown.strip()) < self.config.min_content_length:
                return ConversionResult(
                    success=False,
                    content=markdown,
                    original_length=len(html_content),
                    converted_length=len(markdown),
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.MARKDOWNIFY,
                    url=url,
                    title=title,
                    error_message=f"轉換後內容過短 ({len(markdown)} < {self.config.min_content_length})"
                )
            
            return ConversionResult(
                success=True,
                content=markdown,
                original_length=len(html_content),
                converted_length=len(markdown),
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.MARKDOWNIFY,
                url=url,
                title=title,
                metadata={
                    'conversion_options': options,
                    'processed_html_length': len(processed_html)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Markdownify 轉換失敗 {url}: {e}")
            return ConversionResult(
                success=False,
                content="",
                original_length=len(html_content),
                converted_length=0,
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.MARKDOWNIFY,
                url=url,
                error_message=str(e)
            )
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容"""
        try:
            if not html_content or len(html_content.strip()) == 0:
                return False
            
            soup = BeautifulSoup(html_content, 'lxml')
            text_content = soup.get_text(strip=True)
            
            return len(text_content) > 0
            
        except Exception as e:
            self.logger.warning(f"HTML 驗證失敗: {e}")
            return False
    
    async def llm_enhance_content(self, markdown: str, url: str) -> str:
        """使用 LLM 增強內容結構"""
        try:
            # 這裡可以整合 OpenAI 或其他 LLM API
            # 進行內容結構化、摘要生成、關鍵詞提取等
            
            if not self.config.llm_prompt_template:
                # 使用預設提示模板
                prompt = f"""
                請幫我優化以下 Markdown 內容的結構和格式：
                
                1. 確保標題層級合理
                2. 改善段落結構
                3. 修正格式問題
                4. 保持原始內容的完整性
                
                原始內容：
                {markdown}
                
                請返回優化後的 Markdown 內容：
                """
            else:
                prompt = self.config.llm_prompt_template.format(
                    content=markdown,
                    url=url
                )
            
            # 這裡應該調用實際的 LLM API
            # enhanced_content = await call_llm_api(prompt, self.config.llm_model)
            
            # 暫時返回原始內容
            self.logger.info(f"LLM 處理已啟用但未實現，返回原始內容: {url}")
            return markdown
            
        except Exception as e:
            self.logger.warning(f"LLM 內容增強失敗，返回原始內容: {e}")
            return markdown


class TrafilaturaConverter(HTMLToMarkdownConverter):
    """基於 trafilatura 的轉換器
    
    專業的內容提取工具，特別適合新聞文章和部落格內容。
    能夠智能識別主要內容區域，過濾廣告和導航元素。
    """
    
    def __init__(self, config: ConversionConfig):
        super().__init__(config)
        try:
            import trafilatura
            self.trafilatura = trafilatura
        except ImportError:
            raise ImportError("請安裝 trafilatura: pip install trafilatura")
    
    async def convert(self, html_content: str, url: str = "") -> ConversionResult:
        """使用 trafilatura 進行轉換"""
        start_time = time.time()
        
        try:
            # 驗證 HTML
            if not self.validate_html(html_content):
                return ConversionResult(
                    success=False,
                    content="",
                    original_length=len(html_content),
                    converted_length=0,
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.TRAFILATURA,
                    url=url,
                    error_message="無效的 HTML 內容"
                )
            
            # 使用 trafilatura 提取主要內容
            extraction_options = {
                'output_format': 'markdown',
                'include_images': self.config.include_images,
                'include_links': self.config.include_links,
                'include_tables': self.config.include_tables,
                'include_formatting': True,
                'deduplicate': True,
                'favor_precision': True,
                'url': url if url else None
            }
            
            extracted = self.trafilatura.extract(
                html_content,
                **extraction_options
            )
            
            if not extracted:
                # 嘗試更寬鬆的提取
                extracted = self.trafilatura.extract(
                    html_content,
                    output_format='markdown',
                    favor_precision=False,
                    include_comments=False
                )
            
            if not extracted:
                return ConversionResult(
                    success=False,
                    content="",
                    original_length=len(html_content),
                    converted_length=0,
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.TRAFILATURA,
                    url=url,
                    error_message="無法提取內容"
                )
            
            # 提取標題和元數據
            title = ""
            metadata = {}
            
            if self.config.include_title or self.config.include_metadata:
                metadata_result = self.trafilatura.extract_metadata(html_content)
                if metadata_result:
                    title = metadata_result.title or ""
                    metadata = {
                        'author': metadata_result.author,
                        'date': metadata_result.date,
                        'description': metadata_result.description,
                        'sitename': metadata_result.sitename,
                        'tags': metadata_result.tags
                    }
            
            # 後處理
            markdown = await self.postprocess_markdown(extracted)
            
            # 添加標題 (如果需要)
            if title and self.config.include_title:
                markdown = f"# {title}\n\n{markdown}"
            
            # 檢查內容長度
            if len(markdown.strip()) < self.config.min_content_length:
                return ConversionResult(
                    success=False,
                    content=markdown,
                    original_length=len(html_content),
                    converted_length=len(markdown),
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.TRAFILATURA,
                    url=url,
                    title=title,
                    error_message=f"轉換後內容過短 ({len(markdown)} < {self.config.min_content_length})"
                )
            
            return ConversionResult(
                success=True,
                content=markdown,
                original_length=len(html_content),
                converted_length=len(markdown),
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.TRAFILATURA,
                url=url,
                title=title,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Trafilatura 轉換失敗 {url}: {e}")
            return ConversionResult(
                success=False,
                content="",
                original_length=len(html_content),
                converted_length=0,
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.TRAFILATURA,
                url=url,
                error_message=str(e)
            )
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容"""
        try:
            if not html_content or len(html_content.strip()) == 0:
                return False
            
            # 使用 trafilatura 嘗試提取內容來驗證
            extracted = self.trafilatura.extract(html_content, output_format='txt')
            return extracted is not None and len(extracted.strip()) > 0
            
        except Exception as e:
            self.logger.warning(f"HTML 驗證失敗: {e}")
            return False


class HTML2TextConverter(HTMLToMarkdownConverter):
    """基於 html2text 的轉換器
    
    經典的 HTML to Markdown 轉換工具，提供高度可配置的轉換選項。
    特別適合需要精確控制輸出格式的場景。
    """
    
    def __init__(self, config: ConversionConfig):
        super().__init__(config)
        try:
            import html2text
            self.html2text = html2text
        except ImportError:
            raise ImportError("請安裝 html2text: pip install html2text")
    
    async def convert(self, html_content: str, url: str = "") -> ConversionResult:
        """使用 html2text 進行轉換"""
        start_time = time.time()
        
        try:
            # 驗證 HTML
            if not self.validate_html(html_content):
                return ConversionResult(
                    success=False,
                    content="",
                    original_length=len(html_content),
                    converted_length=0,
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.HTML2TEXT,
                    url=url,
                    error_message="無效的 HTML 內容"
                )
            
            # 預處理 HTML
            processed_html = await self.preprocess_html(html_content)
            
            # 提取標題
            title = await self.extract_title(processed_html) if self.config.include_title else ""
            
            # 配置 html2text
            h = self.html2text.HTML2Text()
            
            # 基本設置
            h.ignore_links = not self.config.include_links
            h.ignore_images = not self.config.include_images
            h.ignore_tables = not self.config.include_tables
            h.body_width = 0  # 不限制行寬
            h.unicode_snob = True  # 使用 Unicode
            h.escape_snob = True  # 轉義特殊字符
            
            # 標題設置
            if self.config.heading_style == 'ATX':
                h.use_automatic_links = False
            
            # 列表設置
            h.ul_item_mark = self.config.bullet_style
            
            # 其他設置
            h.emphasis_mark = '*'
            h.strong_mark = '**'
            h.single_line_break = False
            h.wrap_links = False
            h.wrap_list_items = False
            
            # 執行轉換
            markdown = h.handle(processed_html)
            
            # 後處理
            markdown = await self.postprocess_markdown(markdown)
            
            # 添加標題 (如果需要)
            if title and self.config.include_title:
                markdown = f"# {title}\n\n{markdown}"
            
            # 檢查內容長度
            if len(markdown.strip()) < self.config.min_content_length:
                return ConversionResult(
                    success=False,
                    content=markdown,
                    original_length=len(html_content),
                    converted_length=len(markdown),
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.HTML2TEXT,
                    url=url,
                    title=title,
                    error_message=f"轉換後內容過短 ({len(markdown)} < {self.config.min_content_length})"
                )
            
            return ConversionResult(
                success=True,
                content=markdown,
                original_length=len(html_content),
                converted_length=len(markdown),
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.HTML2TEXT,
                url=url,
                title=title,
                metadata={
                    'processed_html_length': len(processed_html),
                    'html2text_config': {
                        'ignore_links': h.ignore_links,
                        'ignore_images': h.ignore_images,
                        'ignore_tables': h.ignore_tables
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"HTML2Text 轉換失敗 {url}: {e}")
            return ConversionResult(
                success=False,
                content="",
                original_length=len(html_content),
                converted_length=0,
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.HTML2TEXT,
                url=url,
                error_message=str(e)
            )
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容"""
        try:
            if not html_content or len(html_content.strip()) == 0:
                return False
            
            # 嘗試使用 html2text 轉換來驗證
            h = self.html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            result = h.handle(html_content)
            
            return len(result.strip()) > 0
            
        except Exception as e:
            self.logger.warning(f"HTML 驗證失敗: {e}")
            return False


class ReadabilityConverter(HTMLToMarkdownConverter):
    """基於 readability 的轉換器
    
    使用 Mozilla 的 Readability 算法提取主要內容，
    然後轉換為 Markdown 格式。適合處理複雜的網頁結構。
    """
    
    def __init__(self, config: ConversionConfig):
        super().__init__(config)
        try:
            from readability import Document
            self.Document = Document
            import markdownify
            self.markdownify = markdownify
        except ImportError:
            raise ImportError("請安裝 readability-lxml 和 markdownify: pip install readability-lxml markdownify")
    
    async def convert(self, html_content: str, url: str = "") -> ConversionResult:
        """使用 readability + markdownify 進行轉換"""
        start_time = time.time()
        
        try:
            # 驗證 HTML
            if not self.validate_html(html_content):
                return ConversionResult(
                    success=False,
                    content="",
                    original_length=len(html_content),
                    converted_length=0,
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.READABILITY,
                    url=url,
                    error_message="無效的 HTML 內容"
                )
            
            # 使用 Readability 提取主要內容
            doc = self.Document(html_content)
            
            # 獲取標題和內容
            title = doc.title() if self.config.include_title else ""
            clean_html = doc.summary()
            
            if not clean_html:
                return ConversionResult(
                    success=False,
                    content="",
                    original_length=len(html_content),
                    converted_length=0,
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.READABILITY,
                    url=url,
                    error_message="Readability 無法提取內容"
                )
            
            # 使用 markdownify 轉換清理後的 HTML
            convert_tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'del', 'code', 'pre']
            convert_tags.extend(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            convert_tags.extend(['ul', 'ol', 'li'])
            convert_tags.extend(['blockquote', 'hr'])
            
            if self.config.include_links:
                convert_tags.append('a')
            if self.config.include_images:
                convert_tags.append('img')
            if self.config.include_tables:
                convert_tags.extend(['table', 'thead', 'tbody', 'tr', 'th', 'td'])
            
            markdown = self.markdownify.markdownify(
                clean_html,
                heading_style='ATX',
                bullets=self.config.bullet_style,
                convert=convert_tags
            )
            
            # 後處理
            markdown = await self.postprocess_markdown(markdown)
            
            # 添加標題 (如果需要)
            if title and self.config.include_title:
                markdown = f"# {title}\n\n{markdown}"
            
            # 檢查內容長度
            if len(markdown.strip()) < self.config.min_content_length:
                return ConversionResult(
                    success=False,
                    content=markdown,
                    original_length=len(html_content),
                    converted_length=len(markdown),
                    processing_time=time.time() - start_time,
                    engine_used=ConversionEngine.READABILITY,
                    url=url,
                    title=title,
                    error_message=f"轉換後內容過短 ({len(markdown)} < {self.config.min_content_length})"
                )
            
            return ConversionResult(
                success=True,
                content=markdown,
                original_length=len(html_content),
                converted_length=len(markdown),
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.READABILITY,
                url=url,
                title=title,
                metadata={
                    'readability_score': doc.summary(),
                    'clean_html_length': len(clean_html)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Readability 轉換失敗 {url}: {e}")
            return ConversionResult(
                success=False,
                content="",
                original_length=len(html_content),
                converted_length=0,
                processing_time=time.time() - start_time,
                engine_used=ConversionEngine.READABILITY,
                url=url,
                error_message=str(e)
            )
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容"""
        try:
            if not html_content or len(html_content.strip()) == 0:
                return False
            
            doc = self.Document(html_content)
            summary = doc.summary()
            
            return summary is not None and len(summary.strip()) > 0
            
        except Exception as e:
            self.logger.warning(f"HTML 驗證失敗: {e}")
            return False