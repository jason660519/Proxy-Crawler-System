"""HTML to Markdown 轉換工具類

提供 HTML 清理、內容提取、品質評估等輔助功能。
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from bs4 import BeautifulSoup, Comment
from loguru import logger


@dataclass
class ContentQuality:
    """內容品質評估結果"""
    score: float  # 0-1 之間的品質分數
    word_count: int
    paragraph_count: int
    link_count: int
    image_count: int
    has_title: bool
    has_headings: bool
    text_to_html_ratio: float
    readability_score: float
    issues: List[str]
    
    @property
    def is_high_quality(self) -> bool:
        """是否為高品質內容"""
        return self.score >= 0.7
    
    @property
    def is_acceptable(self) -> bool:
        """是否為可接受品質"""
        return self.score >= 0.5


class HTMLCleaner:
    """HTML 清理器
    
    移除不必要的標籤、屬性和內容，
    為轉換做準備。
    """
    
    # 需要移除的標籤
    REMOVE_TAGS = {
        'script', 'style', 'noscript', 'iframe', 'embed', 'object',
        'applet', 'form', 'input', 'button', 'select', 'textarea',
        'meta', 'link', 'base', 'title', 'head'
    }
    
    # 需要移除的屬性
    REMOVE_ATTRIBUTES = {
        'style', 'onclick', 'onload', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'class', 'id'
    }
    
    # 廣告相關的 class 和 id 模式
    AD_PATTERNS = [
        r'ad[s]?[-_]',
        r'advertisement',
        r'banner',
        r'popup',
        r'sponsor',
        r'promo',
        r'sidebar',
        r'widget',
        r'social[-_]share',
        r'comment[s]?[-_]',
        r'footer',
        r'header',
        r'nav',
        r'menu'
    ]
    
    def __init__(self, aggressive: bool = False):
        self.aggressive = aggressive
        self.logger = logger.bind(component='HTMLCleaner')
        
        # 編譯正則表達式
        self.ad_regex = re.compile('|'.join(self.AD_PATTERNS), re.IGNORECASE)
    
    def clean(self, html_content: str) -> str:
        """清理 HTML 內容"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 移除註釋
            self._remove_comments(soup)
            
            # 移除不需要的標籤
            self._remove_unwanted_tags(soup)
            
            # 移除廣告相關元素
            self._remove_ads(soup)
            
            # 清理屬性
            self._clean_attributes(soup)
            
            # 移除空元素
            self._remove_empty_elements(soup)
            
            # 標準化空白字符
            self._normalize_whitespace(soup)
            
            return str(soup)
            
        except Exception as e:
            self.logger.error(f"HTML 清理失敗: {e}")
            return html_content
    
    def _remove_comments(self, soup: BeautifulSoup):
        """移除 HTML 註釋"""
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
    
    def _remove_unwanted_tags(self, soup: BeautifulSoup):
        """移除不需要的標籤"""
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
    
    def _remove_ads(self, soup: BeautifulSoup):
        """移除廣告相關元素"""
        # 根據 class 和 id 移除
        for attr in ['class', 'id']:
            for element in soup.find_all(attrs={attr: self.ad_regex}):
                element.decompose()
        
        # 移除常見的廣告容器
        ad_selectors = [
            '[class*="ad"]',
            '[id*="ad"]',
            '[class*="banner"]',
            '[class*="popup"]',
            '[class*="sponsor"]'
        ]
        
        for selector in ad_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                continue
    
    def _clean_attributes(self, soup: BeautifulSoup):
        """清理元素屬性"""
        for element in soup.find_all():
            # 移除不需要的屬性
            attrs_to_remove = []
            for attr in element.attrs:
                if attr in self.REMOVE_ATTRIBUTES:
                    attrs_to_remove.append(attr)
                elif self.aggressive and attr not in ['href', 'src', 'alt', 'title']:
                    attrs_to_remove.append(attr)
            
            for attr in attrs_to_remove:
                del element.attrs[attr]
    
    def _remove_empty_elements(self, soup: BeautifulSoup):
        """移除空元素"""
        # 可以為空的標籤
        void_tags = {'br', 'hr', 'img', 'input', 'meta', 'link'}
        
        changed = True
        while changed:
            changed = False
            for element in soup.find_all():
                if element.name in void_tags:
                    continue
                
                # 檢查是否為空元素
                if not element.get_text(strip=True) and not element.find_all():
                    element.decompose()
                    changed = True
    
    def _normalize_whitespace(self, soup: BeautifulSoup):
        """標準化空白字符"""
        for element in soup.find_all(string=True):
            if element.parent.name not in ['pre', 'code']:
                # 標準化空白字符
                normalized = re.sub(r'\s+', ' ', element.string)
                element.replace_with(normalized)


class ContentExtractor:
    """內容提取器
    
    從 HTML 中提取主要內容區域。
    """
    
    # 主要內容的選擇器
    CONTENT_SELECTORS = [
        'article',
        '[role="main"]',
        '.content',
        '.main-content',
        '.post-content',
        '.entry-content',
        '.article-content',
        '#content',
        '#main',
        '.container .content'
    ]
    
    # 需要排除的選擇器
    EXCLUDE_SELECTORS = [
        'nav',
        'header',
        'footer',
        '.sidebar',
        '.navigation',
        '.menu',
        '.ads',
        '.advertisement',
        '.social-share',
        '.comments',
        '.related-posts'
    ]
    
    def __init__(self):
        self.logger = logger.bind(component='ContentExtractor')
    
    def extract_main_content(self, html_content: str) -> str:
        """提取主要內容"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 首先嘗試使用內容選擇器
            main_content = self._find_by_selectors(soup)
            
            if main_content:
                return str(main_content)
            
            # 如果沒找到，使用啟發式方法
            main_content = self._heuristic_extraction(soup)
            
            return str(main_content) if main_content else html_content
            
        except Exception as e:
            self.logger.error(f"內容提取失敗: {e}")
            return html_content
    
    def _find_by_selectors(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """使用選擇器查找主要內容"""
        for selector in self.CONTENT_SELECTORS:
            try:
                elements = soup.select(selector)
                if elements:
                    # 選擇最大的元素
                    largest = max(elements, key=lambda x: len(x.get_text()))
                    if len(largest.get_text(strip=True)) > 100:
                        return largest
            except Exception:
                continue
        
        return None
    
    def _heuristic_extraction(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """啟發式內容提取"""
        # 移除不需要的元素
        for selector in self.EXCLUDE_SELECTORS:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                continue
        
        # 查找包含最多文本的元素
        candidates = []
        
        for element in soup.find_all(['div', 'section', 'main', 'article']):
            text_length = len(element.get_text(strip=True))
            if text_length > 200:  # 最少 200 字符
                # 計算文本密度
                html_length = len(str(element))
                density = text_length / html_length if html_length > 0 else 0
                
                candidates.append((element, text_length, density))
        
        if candidates:
            # 選擇文本最多且密度合理的元素
            candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
            return candidates[0][0]
        
        return None
    
    def extract_metadata(self, html_content: str) -> Dict[str, str]:
        """提取頁面元數據"""
        metadata = {}
        
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 標題
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text(strip=True)
            
            # Meta 標籤
            meta_tags = {
                'description': ['name', 'description'],
                'keywords': ['name', 'keywords'],
                'author': ['name', 'author'],
                'og:title': ['property', 'og:title'],
                'og:description': ['property', 'og:description'],
                'og:image': ['property', 'og:image'],
                'twitter:title': ['name', 'twitter:title'],
                'twitter:description': ['name', 'twitter:description']
            }
            
            for key, (attr, value) in meta_tags.items():
                meta_tag = soup.find('meta', {attr: value})
                if meta_tag and meta_tag.get('content'):
                    metadata[key] = meta_tag['content']
            
            # 語言
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                metadata['language'] = html_tag['lang']
            
            # 發布日期
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="date"]',
                'time[datetime]',
                '.published',
                '.date'
            ]
            
            for selector in date_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        date_value = element.get('content') or element.get('datetime') or element.get_text(strip=True)
                        if date_value:
                            metadata['published_date'] = date_value
                            break
                except Exception:
                    continue
            
        except Exception as e:
            self.logger.error(f"元數據提取失敗: {e}")
        
        return metadata


class QualityAssessor:
    """內容品質評估器
    
    評估轉換後內容的品質。
    """
    
    def __init__(self):
        self.logger = logger.bind(component='QualityAssessor')
    
    def assess_html_quality(self, html_content: str) -> ContentQuality:
        """評估 HTML 內容品質"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 基本統計
            text = soup.get_text()
            word_count = len(text.split())
            paragraph_count = len(soup.find_all('p'))
            link_count = len(soup.find_all('a'))
            image_count = len(soup.find_all('img'))
            
            # 結構檢查
            has_title = bool(soup.find('title') or soup.find('h1'))
            has_headings = bool(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            
            # 文本與 HTML 比例
            html_length = len(html_content)
            text_length = len(text)
            text_to_html_ratio = text_length / html_length if html_length > 0 else 0
            
            # 可讀性評估
            readability_score = self._calculate_readability(text)
            
            # 問題檢測
            issues = self._detect_issues(soup, text)
            
            # 計算總體品質分數
            score = self._calculate_quality_score(
                word_count, paragraph_count, has_title, has_headings,
                text_to_html_ratio, readability_score, len(issues)
            )
            
            return ContentQuality(
                score=score,
                word_count=word_count,
                paragraph_count=paragraph_count,
                link_count=link_count,
                image_count=image_count,
                has_title=has_title,
                has_headings=has_headings,
                text_to_html_ratio=text_to_html_ratio,
                readability_score=readability_score,
                issues=issues
            )
            
        except Exception as e:
            self.logger.error(f"品質評估失敗: {e}")
            return ContentQuality(
                score=0.0,
                word_count=0,
                paragraph_count=0,
                link_count=0,
                image_count=0,
                has_title=False,
                has_headings=False,
                text_to_html_ratio=0.0,
                readability_score=0.0,
                issues=["評估失敗"]
            )
    
    def assess_markdown_quality(self, markdown_content: str) -> ContentQuality:
        """評估 Markdown 內容品質"""
        try:
            lines = markdown_content.split('\n')
            
            # 基本統計
            text = re.sub(r'[#*`\[\]()_~]', '', markdown_content)
            word_count = len(text.split())
            
            # 段落計數（空行分隔）
            paragraphs = [p.strip() for p in markdown_content.split('\n\n') if p.strip()]
            paragraph_count = len(paragraphs)
            
            # 連結計數
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            link_count = len(re.findall(link_pattern, markdown_content))
            
            # 圖片計數
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            image_count = len(re.findall(image_pattern, markdown_content))
            
            # 結構檢查
            has_title = any(line.startswith('#') for line in lines)
            has_headings = any(line.startswith('#') for line in lines)
            
            # 文本比例（Markdown 語法相對較少）
            markdown_length = len(markdown_content)
            text_length = len(text)
            text_to_html_ratio = text_length / markdown_length if markdown_length > 0 else 0
            
            # 可讀性評估
            readability_score = self._calculate_readability(text)
            
            # 問題檢測
            issues = self._detect_markdown_issues(markdown_content)
            
            # 計算總體品質分數
            score = self._calculate_quality_score(
                word_count, paragraph_count, has_title, has_headings,
                text_to_html_ratio, readability_score, len(issues)
            )
            
            return ContentQuality(
                score=score,
                word_count=word_count,
                paragraph_count=paragraph_count,
                link_count=link_count,
                image_count=image_count,
                has_title=has_title,
                has_headings=has_headings,
                text_to_html_ratio=text_to_html_ratio,
                readability_score=readability_score,
                issues=issues
            )
            
        except Exception as e:
            self.logger.error(f"Markdown 品質評估失敗: {e}")
            return ContentQuality(
                score=0.0,
                word_count=0,
                paragraph_count=0,
                link_count=0,
                image_count=0,
                has_title=False,
                has_headings=False,
                text_to_html_ratio=0.0,
                readability_score=0.0,
                issues=["評估失敗"]
            )
    
    def _calculate_readability(self, text: str) -> float:
        """計算可讀性分數（簡化版）"""
        if not text.strip():
            return 0.0
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        words = text.split()
        
        # 平均句子長度
        avg_sentence_length = len(words) / len(sentences)
        
        # 長詞比例（超過 6 個字符）
        long_words = [w for w in words if len(w) > 6]
        long_word_ratio = len(long_words) / len(words) if words else 0
        
        # 簡化的可讀性分數（0-1）
        # 理想的句子長度是 15-20 詞
        sentence_score = max(0, 1 - abs(avg_sentence_length - 17.5) / 17.5)
        
        # 長詞不應該太多
        word_score = max(0, 1 - long_word_ratio)
        
        return (sentence_score + word_score) / 2
    
    def _detect_issues(self, soup: BeautifulSoup, text: str) -> List[str]:
        """檢測 HTML 內容問題"""
        issues = []
        
        # 內容長度檢查
        if len(text.split()) < 50:
            issues.append("內容過短")
        
        # 結構檢查
        if not soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            issues.append("缺少標題結構")
        
        if not soup.find_all('p'):
            issues.append("缺少段落結構")
        
        # 連結檢查
        broken_links = 0
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('#') or href == '' or href == 'javascript:void(0)':
                broken_links += 1
        
        if broken_links > 0:
            issues.append(f"發現 {broken_links} 個無效連結")
        
        # 圖片檢查
        images_without_alt = len(soup.find_all('img', alt=False))
        if images_without_alt > 0:
            issues.append(f"{images_without_alt} 張圖片缺少 alt 屬性")
        
        return issues
    
    def _detect_markdown_issues(self, markdown_content: str) -> List[str]:
        """檢測 Markdown 內容問題"""
        issues = []
        
        lines = markdown_content.split('\n')
        
        # 內容長度檢查
        text = re.sub(r'[#*`\[\]()_~]', '', markdown_content)
        if len(text.split()) < 50:
            issues.append("內容過短")
        
        # 標題檢查
        if not any(line.startswith('#') for line in lines):
            issues.append("缺少標題")
        
        # 連結檢查
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, markdown_content)
        
        broken_links = 0
        for text, url in links:
            if not url or url.startswith('#') or url == 'javascript:void(0)':
                broken_links += 1
        
        if broken_links > 0:
            issues.append(f"發現 {broken_links} 個無效連結")
        
        # 圖片檢查
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = re.findall(image_pattern, markdown_content)
        
        images_without_alt = sum(1 for alt, url in images if not alt.strip())
        if images_without_alt > 0:
            issues.append(f"{images_without_alt} 張圖片缺少描述")
        
        return issues
    
    def _calculate_quality_score(self, word_count: int, paragraph_count: int, 
                               has_title: bool, has_headings: bool,
                               text_ratio: float, readability: float, 
                               issue_count: int) -> float:
        """計算總體品質分數"""
        score = 0.0
        
        # 內容長度分數 (0-0.3)
        if word_count >= 500:
            score += 0.3
        elif word_count >= 200:
            score += 0.2
        elif word_count >= 100:
            score += 0.1
        
        # 結構分數 (0-0.3)
        if has_title:
            score += 0.1
        if has_headings:
            score += 0.1
        if paragraph_count >= 3:
            score += 0.1
        
        # 文本比例分數 (0-0.2)
        if text_ratio >= 0.3:
            score += 0.2
        elif text_ratio >= 0.2:
            score += 0.1
        
        # 可讀性分數 (0-0.2)
        score += readability * 0.2
        
        # 問題懲罰
        penalty = min(issue_count * 0.05, 0.2)
        score -= penalty
        
        return max(0.0, min(1.0, score))


class URLUtils:
    """URL 處理工具"""
    
    @staticmethod
    def normalize_url(url: str, base_url: str = "") -> str:
        """標準化 URL"""
        if not url:
            return ""
        
        # 處理相對 URL
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        # 移除片段
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{parsed.params}{parsed.query}"
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """提取域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""
    
    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """檢查是否為同一域名"""
        return URLUtils.extract_domain(url1) == URLUtils.extract_domain(url2)


class TextUtils:
    """文本處理工具"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 標準化空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除多餘的換行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # 清理開頭和結尾
        text = text.strip()
        
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """截斷文本"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_sentences(text: str, max_sentences: int = 3) -> List[str]:
        """提取句子"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences[:max_sentences]
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """計算文本相似度（簡化版）"""
        if not text1 or not text2:
            return 0.0
        
        # 轉換為小寫並分詞
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 計算 Jaccard 相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0


class HashUtils:
    """雜湊工具"""
    
    @staticmethod
    def content_hash(content: str) -> str:
        """計算內容雜湊"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def url_hash(url: str) -> str:
        """計算 URL 雜湊"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def combined_hash(content: str, url: str) -> str:
        """計算組合雜湊"""
        combined = f"{content}|{url}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


# 便利函數
def quick_clean_html(html_content: str, aggressive: bool = False) -> str:
    """快速清理 HTML"""
    cleaner = HTMLCleaner(aggressive=aggressive)
    return cleaner.clean(html_content)


def extract_main_content(html_content: str) -> str:
    """提取主要內容"""
    extractor = ContentExtractor()
    return extractor.extract_main_content(html_content)


def assess_content_quality(content: str, is_markdown: bool = False) -> ContentQuality:
    """評估內容品質"""
    assessor = QualityAssessor()
    if is_markdown:
        return assessor.assess_markdown_quality(content)
    else:
        return assessor.assess_html_quality(content)


def extract_page_metadata(html_content: str) -> Dict[str, str]:
    """提取頁面元數據"""
    extractor = ContentExtractor()
    return extractor.extract_metadata(html_content)