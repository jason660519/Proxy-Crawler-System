"""Seek 網站專用 Markdown 解析適配器

提供針對 Seek 平台職位資訊的專門解析功能，
整合到 HTML to Markdown 轉換系統中。
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger

from .core import HTMLToMarkdownConverter, ConversionResult, ConversionConfig, ConversionEngine
from .utils import ContentExtractor


@dataclass
class JobListing:
    """職位資訊數據類
    
    用於存儲從 Seek Markdown 中解析出的職位資訊。
    """
    title: str = ""
    company: str = ""
    salary: str = ""
    job_type: str = ""
    location: str = ""
    posted_date: str = ""
    sub_classification: str = ""
    classification: str = ""
    benefits: str = ""
    description: str = ""
    logo_url: str = ""
    company_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """檢查職位資訊是否有效"""
        return bool(self.title.strip() or self.description.strip())


class SeekMarkdownAdapter(HTMLToMarkdownConverter):
    """Seek 平台 Markdown 解析適配器
    
    專門用於解析從 Seek 平台抓取的 Markdown 格式職位資訊，
    提取結構化的職位數據並支援多種輸出格式。
    """
    
    @property
    def name(self) -> str:
        """適配器名稱"""
        return "seek_markdown_adapter"
    
    def __init__(self, config: Optional[ConversionConfig] = None):
        """初始化 Seek 適配器
        
        Args:
            config: 轉換配置，如果為 None 則使用預設配置
        """
        super().__init__(config or ConversionConfig())
        self.jobs: List[JobListing] = []
        
        # 編譯正則表達式以提高效能
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """編譯常用的正則表達式模式"""
        self.patterns = {
            'job_block': re.compile(r'(?:\*\*[^*]+\*\*|^[A-Z][^\n]*(?:jobs?|engineer|developer|analyst|manager|specialist))', re.MULTILINE | re.IGNORECASE),
            'salary': re.compile(r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:per|/)?\s*(?:hour|day|week|month|year|annum))?', re.IGNORECASE),
            'job_type': re.compile(r'\b(?:Full time|Part time|Contract|Casual|Temporary|Permanent|Internship|Graduate|Vacation|Remote|Hybrid|On-site)\b', re.IGNORECASE),
            'posted_date': re.compile(r'\b(?:today|yesterday|\d+\s+(?:day|week|month)s?\s+ago|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b', re.IGNORECASE),
            'classification': re.compile(r'(?:Engineering|Information|Technology|Science|Healthcare|Finance|Marketing|Sales|Education|Legal|Government|Manufacturing|Retail|Hospitality|Construction|Transport|Agriculture|Mining|Energy|Utilities|Real Estate|Media|Entertainment|Sports|Non-profit|Consulting|Other)(?:\s*-\s*[^\n]+)?', re.IGNORECASE),
            'logo_url': re.compile(r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|svg|webp)', re.IGNORECASE),
            'company_url': re.compile(r'https://www\.seek\.com\.au/companies/[^\s)]+', re.IGNORECASE)
        }
    
    async def convert(self, content: str, url: Optional[str] = None) -> ConversionResult:
        """轉換 Seek Markdown 內容為結構化職位資訊
        
        Args:
            content: Markdown 格式的內容
            url: 來源 URL（可選）
            
        Returns:
            ConversionResult: 包含解析結果的轉換結果物件
        """
        start_time = datetime.now()
        
        try:
            # 清理和預處理內容
            cleaned_content = self._preprocess_content(content)
            
            # 分割職位區塊
            job_blocks = self._split_job_blocks(cleaned_content)
            
            # 解析每個職位區塊
            self.jobs = []
            for block in job_blocks:
                job = self._parse_job_block(block)
                if job and job.is_valid():
                    self.jobs.append(job)
            
            # 計算處理時間
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 生成結果
            result_content = self._generate_result_content()
            
            # 品質評估
            quality_score = self._assess_quality()
            
            return ConversionResult(
                success=True,
                content=result_content,
                original_length=len(content),
                converted_length=len(result_content),
                processing_time=processing_time,
                engine_used=ConversionEngine.CUSTOM,
                url=url,
                title=f"Seek Jobs Analysis - {len(self.jobs)} positions found",
                metadata={
                    'total_jobs': len(self.jobs),
                    'processing_time': processing_time,
                    'source_url': url,
                    'adapter': self.name,
                    'quality_score': quality_score,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Seek Markdown 解析失敗: {e}")
            return ConversionResult(
                success=False,
                content="",
                original_length=len(content),
                converted_length=0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                engine_used=ConversionEngine.CUSTOM,
                url=url,
                error_message=str(e),
                metadata={'error': str(e), 'adapter': self.name}
            )
    
    def _preprocess_content(self, content: str) -> str:
        """預處理 Markdown 內容
        
        Args:
            content: 原始 Markdown 內容
            
        Returns:
            str: 清理後的內容
        """
        # 移除多餘的空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 統一換行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除 HTML 註釋
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        return content.strip()
    
    def _split_job_blocks(self, content: str) -> List[str]:
        """將內容分割為職位區塊
        
        Args:
            content: 預處理後的內容
            
        Returns:
            List[str]: 職位區塊列表
        """
        # 使用多種分割策略
        blocks = []
        
        # 策略1: 根據職位標題模式分割
        potential_splits = list(self.patterns['job_block'].finditer(content))
        
        if potential_splits:
            for i, match in enumerate(potential_splits):
                start = match.start()
                end = potential_splits[i + 1].start() if i + 1 < len(potential_splits) else len(content)
                block = content[start:end].strip()
                if len(block) > 50:  # 過濾太短的區塊
                    blocks.append(block)
        else:
            # 策略2: 根據段落分割
            paragraphs = content.split('\n\n')
            current_block = ""
            
            for paragraph in paragraphs:
                if self._is_job_start(paragraph):
                    if current_block.strip():
                        blocks.append(current_block.strip())
                    current_block = paragraph
                else:
                    current_block += "\n\n" + paragraph
            
            if current_block.strip():
                blocks.append(current_block.strip())
        
        return blocks
    
    def _is_job_start(self, text: str) -> bool:
        """判斷文本是否為職位開始
        
        Args:
            text: 要檢查的文本
            
        Returns:
            bool: 是否為職位開始
        """
        # 檢查是否包含職位相關關鍵詞
        job_keywords = [
            'engineer', 'developer', 'analyst', 'manager', 'specialist',
            'coordinator', 'assistant', 'director', 'lead', 'senior',
            'junior', 'intern', 'graduate', 'consultant', 'advisor'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in job_keywords)
    
    def _parse_job_block(self, block: str) -> Optional[JobListing]:
        """解析單個職位區塊
        
        Args:
            block: 職位區塊文本
            
        Returns:
            Optional[JobListing]: 解析出的職位資訊，如果解析失敗則返回 None
        """
        try:
            job = JobListing()
            lines = block.split('\n')
            
            # 提取標題（通常是第一行或包含粗體的行）
            job.title = self._extract_title(lines)
            
            # 提取其他資訊
            job.salary = self._extract_salary(block)
            job.job_type = self._extract_job_type(block)
            job.posted_date = self._extract_posted_date(block)
            job.classification = self._extract_classification(block)
            job.logo_url = self._extract_logo_url(block)
            job.company_url = self._extract_company_url(block)
            job.benefits = self._extract_benefits(block)
            job.description = self._extract_description(block)
            job.company = self._extract_company(block)
            job.location = self._extract_location(block)
            
            return job
            
        except Exception as e:
            logger.warning(f"解析職位區塊失敗: {e}")
            return None
    
    def _extract_title(self, lines: List[str]) -> str:
        """提取職位標題"""
        for line in lines[:5]:  # 只檢查前5行
            line = line.strip()
            if line and not line.startswith(('http', 'www', '$')):
                # 移除 Markdown 格式
                title = re.sub(r'[*_#]+', '', line).strip()
                if len(title) > 10 and len(title) < 200:
                    return title
        return ""
    
    def _extract_salary(self, text: str) -> str:
        """提取薪資資訊"""
        match = self.patterns['salary'].search(text)
        return match.group(0) if match else ""
    
    def _extract_job_type(self, text: str) -> str:
        """提取工作類型"""
        match = self.patterns['job_type'].search(text)
        return match.group(0) if match else ""
    
    def _extract_posted_date(self, text: str) -> str:
        """提取發布日期"""
        match = self.patterns['posted_date'].search(text)
        return match.group(0) if match else ""
    
    def _extract_classification(self, text: str) -> str:
        """提取職位分類"""
        match = self.patterns['classification'].search(text)
        return match.group(0) if match else ""
    
    def _extract_logo_url(self, text: str) -> str:
        """提取公司 Logo URL"""
        match = self.patterns['logo_url'].search(text)
        return match.group(0) if match else ""
    
    def _extract_company_url(self, text: str) -> str:
        """提取公司 URL"""
        match = self.patterns['company_url'].search(text)
        return match.group(0) if match else ""
    
    def _extract_benefits(self, text: str) -> str:
        """提取福利資訊"""
        # 尋找包含福利關鍵詞的行
        benefit_keywords = ['benefit', 'perk', 'bonus', 'insurance', 'leave', 'flexible', 'remote', 'hybrid']
        lines = text.split('\n')
        benefits = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in benefit_keywords):
                clean_line = re.sub(r'[*_#]+', '', line).strip()
                if clean_line and len(clean_line) < 200:
                    benefits.append(clean_line)
        
        return '; '.join(benefits[:5])  # 限制福利數量
    
    def _extract_description(self, text: str) -> str:
        """提取職位描述"""
        # 移除 URL 和 Markdown 格式
        description = re.sub(r'https?://[^\s]+', '', text)
        description = re.sub(r'[*_#]+', '', description)
        
        # 取前200個字符作為描述
        lines = [line.strip() for line in description.split('\n') if line.strip()]
        description_text = ' '.join(lines)
        
        return description_text[:200] + '...' if len(description_text) > 200 else description_text
    
    def _extract_company(self, text: str) -> str:
        """提取公司名稱"""
        # 從公司 URL 中提取
        company_url = self._extract_company_url(text)
        if company_url:
            # 從 URL 中提取公司名稱
            match = re.search(r'/companies/([^-]+)', company_url)
            if match:
                return match.group(1).replace('-', ' ').title()
        
        return ""
    
    def _extract_location(self, text: str) -> str:
        """提取工作地點"""
        # 尋找地點模式
        location_patterns = [
            r'\b(?:Sydney|Melbourne|Brisbane|Perth|Adelaide|Canberra|Darwin|Hobart)\b',
            r'\b(?:NSW|VIC|QLD|WA|SA|ACT|NT|TAS)\b',
            r'\b(?:Remote|Work from home|WFH)\b'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _generate_result_content(self) -> str:
        """生成結果內容"""
        if not self.jobs:
            return "未找到有效的職位資訊"
        
        result = f"# Seek 職位解析結果\n\n"
        result += f"總共找到 {len(self.jobs)} 個職位\n\n"
        
        for i, job in enumerate(self.jobs[:5], 1):  # 只顯示前5個職位的詳細資訊
            result += f"## 職位 {i}: {job.title}\n\n"
            if job.company:
                result += f"**公司:** {job.company}\n\n"
            if job.salary:
                result += f"**薪資:** {job.salary}\n\n"
            if job.job_type:
                result += f"**類型:** {job.job_type}\n\n"
            if job.description:
                result += f"**描述:** {job.description}\n\n"
            result += "---\n\n"
        
        return result
    
    def _assess_quality(self) -> float:
        """評估提取的職位資訊品質
        
        Returns:
            float: 品質分數 (0-1)
        """
        if not self.jobs:
            return 0.0
        
        total_score = 0.0
        for job in self.jobs:
            score = 0.0
            
            # 基本資訊完整性 (40%)
            if job.title and len(job.title.strip()) > 5:
                score += 0.15
            if job.company and len(job.company.strip()) > 2:
                score += 0.10
            if job.description and len(job.description.strip()) > 20:
                score += 0.15
            
            # 薪資資訊 (20%)
            if job.salary and any(char.isdigit() for char in job.salary):
                score += 0.20
            
            # 分類和類型資訊 (20%)
            if job.classification:
                score += 0.10
            if job.job_type:
                score += 0.10
            
            # 時效性 (10%)
            if job.posted_date:
                score += 0.10
            
            # 額外資訊 (10%)
            if job.benefits:
                score += 0.05
            if job.location:
                score += 0.05
            
            total_score += score
        
        return total_score / len(self.jobs)
    
    def validate_html(self, html_content: str) -> bool:
        """驗證 HTML 內容有效性
        
        Args:
            html_content: HTML 內容
            
        Returns:
            bool: 是否有效
        """
        if not html_content or not html_content.strip():
            return False
        
        # 對於 Markdown 內容，我們檢查是否包含基本的職位資訊模式
        content = html_content.lower()
        
        # 檢查是否包含職位相關的關鍵字
        job_keywords = ['job', 'position', 'role', 'career', 'employment', 'work']
        has_job_keywords = any(keyword in content for keyword in job_keywords)
        
        # 檢查是否包含薪資相關的關鍵字
        salary_keywords = ['salary', 'pay', 'wage', '$', 'aud', 'per annum']
        has_salary_keywords = any(keyword in content for keyword in salary_keywords)
        
        # 檢查是否包含公司相關的關鍵字
        company_keywords = ['company', 'employer', 'organisation', 'business']
        has_company_keywords = any(keyword in content for keyword in company_keywords)
        
        # 至少要包含職位和薪資或公司相關的關鍵字
        return has_job_keywords and (has_salary_keywords or has_company_keywords)
    
    def export_to_csv(self, output_path: Path) -> bool:
        """匯出為 CSV 格式
        
        Args:
            output_path: 輸出檔案路徑
            
        Returns:
            bool: 是否成功匯出
        """
        try:
            import csv
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if not self.jobs:
                    return False
                
                fieldnames = list(self.jobs[0].to_dict().keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for job in self.jobs:
                    writer.writerow(job.to_dict())
            
            logger.info(f"成功匯出 {len(self.jobs)} 個職位到 {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"CSV 匯出失敗: {e}")
            return False
    
    def export_to_json(self, output_path: Path) -> bool:
        """匯出為 JSON 格式
        
        Args:
            output_path: 輸出檔案路徑
            
        Returns:
            bool: 是否成功匯出
        """
        try:
            data = {
                'metadata': {
                    'total_jobs': len(self.jobs),
                    'export_time': datetime.now().isoformat(),
                    'adapter': self.name
                },
                'jobs': [job.to_dict() for job in self.jobs]
            }
            
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, ensure_ascii=False, indent=2)
            
            logger.info(f"成功匯出 {len(self.jobs)} 個職位到 {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"JSON 匯出失敗: {e}")
            return False
    
    def get_jobs(self) -> List[JobListing]:
        """獲取解析出的職位列表
        
        Returns:
            List[JobListing]: 職位列表
        """
        return self.jobs.copy()
    
    def get_job_count(self) -> int:
        """獲取職位數量
        
        Returns:
            int: 職位數量
        """
        return len(self.jobs)