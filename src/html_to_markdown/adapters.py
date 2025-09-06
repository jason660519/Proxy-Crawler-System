"""網站特定適配器系統

為不同網站提供特定的內容提取和轉換邏輯，
支援自定義選擇器、內容清理規則和轉換參數。
"""

import re
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse
from loguru import logger

from .core import ConversionConfig, ConversionResult


@dataclass
class SiteConfig:
    """網站特定配置"""
    domain: str
    name: str
    content_selectors: List[str]  # 主要內容選擇器
    title_selectors: List[str]    # 標題選擇器
    remove_selectors: List[str]   # 需要移除的元素選擇器
    author_selectors: List[str] = None
    date_selectors: List[str] = None
    image_selectors: List[str] = None
    custom_rules: Dict[str, Any] = None
    priority: int = 0  # 優先級，數字越大優先級越高


class SiteAdapter(ABC):
    """網站適配器抽象基類"""
    
    def __init__(self, config: SiteConfig):
        self.config = config
        self.logger = logger.bind(adapter=self.config.name)
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """檢查是否可以處理指定 URL"""
        pass
    
    @abstractmethod
    async def extract_content(self, html_content: str, url: str) -> Tuple[str, Dict[str, Any]]:
        """提取主要內容和元數據
        
        Returns:
            Tuple[str, Dict[str, Any]]: (清理後的HTML內容, 元數據字典)
        """
        pass
    
    def preprocess_html(self, html_content: str) -> str:
        """預處理 HTML 內容"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 移除指定的元素
            for selector in self.config.remove_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # 清理空白和格式
            for tag in soup.find_all(text=True):
                if tag.parent.name in ['script', 'style', 'meta', 'link']:
                    tag.extract()
            
            return str(soup)
            
        except Exception as e:
            self.logger.warning(f"HTML 預處理失敗: {e}")
            return html_content
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        for selector in self.config.title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                return title_element.get_text(strip=True)
        
        # 回退到 <title> 標籤
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return ""
    
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取元數據"""
        metadata = {}
        
        # 提取作者
        if self.config.author_selectors:
            for selector in self.config.author_selectors:
                author_element = soup.select_one(selector)
                if author_element:
                    metadata['author'] = author_element.get_text(strip=True)
                    break
        
        # 提取日期
        if self.config.date_selectors:
            for selector in self.config.date_selectors:
                date_element = soup.select_one(selector)
                if date_element:
                    # 嘗試從 datetime 屬性或文本中提取日期
                    date_text = date_element.get('datetime') or date_element.get_text(strip=True)
                    metadata['date'] = date_text
                    break
        
        # 提取描述
        description_meta = soup.find('meta', attrs={'name': 'description'}) or \
                          soup.find('meta', attrs={'property': 'og:description'})
        if description_meta:
            metadata['description'] = description_meta.get('content', '')
        
        # 提取關鍵詞
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            metadata['keywords'] = keywords_meta.get('content', '')
        
        return metadata


class GenericSiteAdapter(SiteAdapter):
    """通用網站適配器
    
    使用配置文件中的選擇器進行內容提取。
    """
    
    def can_handle(self, url: str) -> bool:
        """檢查域名是否匹配"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # 支援精確匹配和子域名匹配
            config_domain = self.config.domain.lower()
            return domain == config_domain or domain.endswith(f'.{config_domain}')
            
        except Exception:
            return False
    
    async def extract_content(self, html_content: str, url: str) -> Tuple[str, Dict[str, Any]]:
        """使用選擇器提取內容"""
        try:
            # 預處理 HTML
            processed_html = self.preprocess_html(html_content)
            soup = BeautifulSoup(processed_html, 'lxml')
            
            # 提取主要內容
            content_elements = []
            for selector in self.config.content_selectors:
                elements = soup.select(selector)
                content_elements.extend(elements)
            
            if not content_elements:
                # 如果沒有找到內容，嘗試使用通用選擇器
                fallback_selectors = [
                    'article', 'main', '.content', '#content',
                    '.post-content', '.entry-content', '.article-content'
                ]
                for selector in fallback_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content_elements = elements
                        break
            
            # 構建清理後的 HTML
            if content_elements:
                # 創建新的 soup 只包含主要內容
                new_soup = BeautifulSoup('<div></div>', 'lxml')
                container = new_soup.find('div')
                
                for element in content_elements:
                    if isinstance(element, Tag):
                        container.append(element.extract())
                
                clean_html = str(container)
            else:
                # 如果沒有找到特定內容，返回整個 body
                body = soup.find('body')
                clean_html = str(body) if body else processed_html
            
            # 提取元數據
            metadata = self.extract_metadata(soup)
            metadata['adapter'] = self.config.name
            metadata['selectors_used'] = self.config.content_selectors
            
            return clean_html, metadata
            
        except Exception as e:
            self.logger.error(f"內容提取失敗 {url}: {e}")
            return html_content, {'error': str(e), 'adapter': self.config.name}


class MediumAdapter(SiteAdapter):
    """Medium 網站適配器
    
    專門處理 Medium 文章的特殊結構。
    """
    
    def __init__(self):
        config = SiteConfig(
            domain='medium.com',
            name='Medium',
            content_selectors=[
                'article section',
                '.postArticle-content',
                '[data-testid="storyContent"]'
            ],
            title_selectors=[
                'h1[data-testid="storyTitle"]',
                '.graf--title',
                'h1.p-name'
            ],
            remove_selectors=[
                '.highlighter',
                '.js-postMetaLockup',
                '.postActions',
                '.u-marginTop20',
                'footer',
                'nav',
                '.sidebar'
            ],
            author_selectors=[
                '[data-testid="authorName"]',
                '.postMetaInline-authorLockup a'
            ],
            date_selectors=[
                '[data-testid="storyPublishDate"]',
                'time'
            ]
        )
        super().__init__(config)
    
    def can_handle(self, url: str) -> bool:
        """檢查是否為 Medium URL"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            return 'medium.com' in domain or domain.endswith('.medium.com')
        except Exception:
            return False
    
    async def extract_content(self, html_content: str, url: str) -> Tuple[str, Dict[str, Any]]:
        """提取 Medium 文章內容"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Medium 特殊處理：移除不需要的元素
            for selector in [
                '.js-postMetaLockup',
                '.postActions',
                '.highlighter',
                'footer',
                'nav'
            ]:
                for element in soup.select(selector):
                    element.decompose()
            
            # 提取文章內容
            content_element = None
            for selector in self.config.content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                # 回退策略
                content_element = soup.find('article') or soup.find('main')
            
            if content_element:
                # 清理 Medium 特有的樣式類
                for element in content_element.find_all(True):
                    if element.get('class'):
                        # 保留語義化的類，移除樣式類
                        semantic_classes = [cls for cls in element['class'] 
                                          if not re.match(r'^[a-z]+-[a-f0-9]+$', cls)]
                        if semantic_classes:
                            element['class'] = semantic_classes
                        else:
                            del element['class']
                
                clean_html = str(content_element)
            else:
                clean_html = html_content
            
            # 提取元數據
            metadata = self.extract_metadata(soup)
            metadata['adapter'] = 'Medium'
            metadata['platform'] = 'Medium'
            
            return clean_html, metadata
            
        except Exception as e:
            self.logger.error(f"Medium 內容提取失敗 {url}: {e}")
            return html_content, {'error': str(e), 'adapter': 'Medium'}


class GitHubAdapter(SiteAdapter):
    """GitHub 適配器
    
    專門處理 GitHub README 和文檔頁面。
    """
    
    def __init__(self):
        config = SiteConfig(
            domain='github.com',
            name='GitHub',
            content_selectors=[
                '#readme article',
                '.markdown-body',
                '.repository-content'
            ],
            title_selectors=[
                'h1.public strong a',
                '.js-repo-nav-item',
                'h1'
            ],
            remove_selectors=[
                '.Header',
                '.footer',
                '.js-navigation-container',
                '.file-navigation',
                '.breadcrumb'
            ]
        )
        super().__init__(config)
    
    def can_handle(self, url: str) -> bool:
        """檢查是否為 GitHub URL"""
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc.lower() == 'github.com'
        except Exception:
            return False
    
    async def extract_content(self, html_content: str, url: str) -> Tuple[str, Dict[str, Any]]:
        """提取 GitHub 內容"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 移除 GitHub 特有的導航和頁腳
            for selector in self.config.remove_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # 提取主要內容
            content_element = None
            for selector in self.config.content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if content_element:
                # GitHub 的 Markdown 內容通常已經很乾淨
                clean_html = str(content_element)
            else:
                # 回退到整個頁面
                clean_html = html_content
            
            # 提取倉庫信息
            metadata = self.extract_metadata(soup)
            
            # 嘗試提取倉庫名稱
            repo_name_element = soup.select_one('h1.public strong a')
            if repo_name_element:
                metadata['repository'] = repo_name_element.get_text(strip=True)
            
            metadata['adapter'] = 'GitHub'
            metadata['platform'] = 'GitHub'
            
            return clean_html, metadata
            
        except Exception as e:
            self.logger.error(f"GitHub 內容提取失敗 {url}: {e}")
            return html_content, {'error': str(e), 'adapter': 'GitHub'}


class SiteAdapterManager:
    """網站適配器管理器
    
    負責管理和選擇合適的網站適配器。
    """
    
    def __init__(self):
        self.adapters: List[SiteAdapter] = []
        self.logger = logger.bind(component='SiteAdapterManager')
        
        # 註冊內建適配器
        self._register_builtin_adapters()
    
    def _register_builtin_adapters(self):
        """註冊內建適配器"""
        self.adapters.extend([
            MediumAdapter(),
            GitHubAdapter()
        ])
    
    def register_adapter(self, adapter: SiteAdapter):
        """註冊新的適配器"""
        self.adapters.append(adapter)
        # 按優先級排序
        self.adapters.sort(key=lambda x: x.config.priority, reverse=True)
        self.logger.info(f"已註冊適配器: {adapter.config.name}")
    
    def register_site_config(self, site_config: SiteConfig):
        """從配置註冊通用適配器"""
        adapter = GenericSiteAdapter(site_config)
        self.register_adapter(adapter)
    
    def get_adapter(self, url: str) -> Optional[SiteAdapter]:
        """獲取適合的適配器"""
        for adapter in self.adapters:
            if adapter.can_handle(url):
                self.logger.info(f"為 {url} 選擇適配器: {adapter.config.name}")
                return adapter
        
        self.logger.info(f"未找到專用適配器，使用通用處理: {url}")
        return None
    
    async def extract_content(self, html_content: str, url: str) -> Tuple[str, Dict[str, Any]]:
        """使用適當的適配器提取內容"""
        adapter = self.get_adapter(url)
        
        if adapter:
            return await adapter.extract_content(html_content, url)
        else:
            # 使用通用提取邏輯
            return await self._generic_extract(html_content, url)
    
    async def _generic_extract(self, html_content: str, url: str) -> Tuple[str, Dict[str, Any]]:
        """通用內容提取"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 移除常見的不需要元素
            for selector in [
                'script', 'style', 'nav', 'footer', 'header',
                '.sidebar', '.navigation', '.menu', '.ads',
                '.comments', '.social-share'
            ]:
                for element in soup.select(selector):
                    element.decompose()
            
            # 嘗試找到主要內容區域
            main_content = None
            for selector in [
                'main', 'article', '.content', '#content',
                '.main-content', '.post-content', '.entry-content'
            ]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                clean_html = str(main_content)
            else:
                # 如果找不到主要內容區域，使用 body
                body = soup.find('body')
                clean_html = str(body) if body else html_content
            
            # 基本元數據
            metadata = {
                'adapter': 'Generic',
                'title': soup.find('title').get_text(strip=True) if soup.find('title') else '',
                'url': url
            }
            
            return clean_html, metadata
            
        except Exception as e:
            self.logger.error(f"通用內容提取失敗 {url}: {e}")
            return html_content, {'error': str(e), 'adapter': 'Generic'}
    
    def load_site_configs(self, config_file: str):
        """從配置文件載入網站配置"""
        try:
            import yaml
            
            with open(config_file, 'r', encoding='utf-8') as f:
                configs = yaml.safe_load(f)
            
            for config_data in configs.get('sites', []):
                site_config = SiteConfig(**config_data)
                self.register_site_config(site_config)
            
            self.logger.info(f"已載入 {len(configs.get('sites', []))} 個網站配置")
            
        except Exception as e:
            self.logger.error(f"載入網站配置失敗: {e}")


# 全局適配器管理器實例
site_adapter_manager = SiteAdapterManager()