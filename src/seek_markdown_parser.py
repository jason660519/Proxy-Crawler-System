#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek Markdown 解析程式

此模組用於解析從 Seek 平台透過 LLMFeeder 擴充功能抓取的 Markdown 檔案，
提取職位資訊並轉換為結構化資料格式（CSV）。

作者: JasonSpider 專案
日期: 2024
"""

import re
import csv
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JobListing:
    """
    職位資訊資料模型
    
    Attributes:
        title: 職位標題
        company: 公司名稱
        salary: 薪資資訊
        job_type: 工作類型（Full time, Part time, Contract等）
        location: 工作地點
        posted_date: 發布日期
        sub_classification: 子分類
        classification: 主分類
        benefits: 福利資訊列表
        description: 職位描述
        logo_url: 公司Logo URL
        company_url: 公司頁面URL
    """
    title: str = ""
    company: str = ""
    salary: str = ""
    job_type: str = ""
    location: str = ""
    posted_date: str = ""
    sub_classification: str = ""
    classification: str = ""
    benefits: List[str] = None
    description: str = ""
    logo_url: str = ""
    company_url: str = ""
    
    def __post_init__(self):
        """初始化後處理，確保 benefits 是列表"""
        if self.benefits is None:
            self.benefits = []


class SeekMarkdownParser:
    """
    Seek Markdown 解析器
    
    用於解析 Seek 平台的 Markdown 檔案，提取職位資訊。
    """
    
    def __init__(self):
        """初始化解析器"""
        self.job_listings: List[JobListing] = []
        
        # 編譯正則表達式模式以提高效能
        self.patterns = {
            'posted_date': re.compile(r'Listed\s+(.*?)\s+ago|^(\d+d?)\s+ago$', re.MULTILINE),
            'job_type': re.compile(r'This is a\s+(.*?)\s+job'),
            'salary': re.compile(r'\$([\d,]+(?:\.\d{2})?(?:\s*-\s*\$[\d,]+(?:\.\d{2})?)?(?:\s+per\s+\w+)?(?:\s*/\s*\$[\d,]+(?:\.\d{2})?\s+per\s+\w+)?)'),
            'classification': re.compile(r'classification:\s*([^(]+)\(([^)]+)\)'),
            'sub_classification': re.compile(r'subClassification:\s*([^\n]+)'),
            'logo_url': re.compile(r'!\[SerpLogo\]\(([^)]+)\)'),
            'company_url': re.compile(r'\]\((https://www\.seek\.com\.au/companies/[^)]+)\)'),
            'benefits': re.compile(r'^-\s+(.+)$', re.MULTILINE)
        }
    
    def parse_file(self, file_path: Union[str, Path]) -> List[JobListing]:
        """
        解析單個 Markdown 檔案
        
        Args:
            file_path: Markdown 檔案路徑
            
        Returns:
            解析出的職位資訊列表
            
        Raises:
            FileNotFoundError: 檔案不存在
            UnicodeDecodeError: 檔案編碼錯誤
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"檔案不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 嘗試其他編碼
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        
        logger.info(f"開始解析檔案: {file_path.name}")
        
        # 分割職位區塊
        job_blocks = self._split_job_blocks(content)
        
        parsed_jobs = []
        for i, block in enumerate(job_blocks):
            try:
                job = self._parse_job_block(block)
                if job.title or job.description:  # 只保留有效的職位資訊
                    parsed_jobs.append(job)
                    logger.debug(f"成功解析職位 {i+1}: {job.title[:50]}...")
            except Exception as e:
                logger.warning(f"解析職位區塊 {i+1} 時發生錯誤: {e}")
                continue
        
        logger.info(f"檔案 {file_path.name} 解析完成，共找到 {len(parsed_jobs)} 個職位")
        return parsed_jobs
    
    def _split_job_blocks(self, content: str) -> List[str]:
        """
        將 Markdown 內容分割為個別的職位區塊
        
        Args:
            content: Markdown 檔案內容
            
        Returns:
            職位區塊列表
        """
        # 使用 "Listed" 關鍵字作為分割點
        blocks = re.split(r'(?=Listed\s+)', content)
        
        # 過濾掉太短的區塊（可能是標題或其他非職位內容）
        valid_blocks = [block.strip() for block in blocks if len(block.strip()) > 50]
        
        return valid_blocks
    
    def _parse_job_block(self, block: str) -> JobListing:
        """
        解析單個職位區塊
        
        Args:
            block: 職位區塊文字
            
        Returns:
            JobListing 物件
        """
        job = JobListing()
        
        # 解析發布日期
        posted_match = self.patterns['posted_date'].search(block)
        if posted_match:
            job.posted_date = posted_match.group(1) or posted_match.group(2) or ""
        
        # 解析工作類型
        job_type_match = self.patterns['job_type'].search(block)
        if job_type_match:
            job.job_type = job_type_match.group(1).strip()
        
        # 解析薪資
        salary_match = self.patterns['salary'].search(block)
        if salary_match:
            job.salary = f"${salary_match.group(1)}"
        
        # 解析分類資訊
        classification_match = self.patterns['classification'].search(block)
        if classification_match:
            job.classification = classification_match.group(1).strip()
        
        sub_classification_match = self.patterns['sub_classification'].search(block)
        if sub_classification_match:
            job.sub_classification = sub_classification_match.group(1).strip()
        
        # 解析公司 Logo URL
        logo_match = self.patterns['logo_url'].search(block)
        if logo_match:
            job.logo_url = logo_match.group(1)
        
        # 解析公司頁面 URL
        company_url_match = self.patterns['company_url'].search(block)
        if company_url_match:
            job.company_url = company_url_match.group(1)
        
        # 解析福利資訊
        benefits_matches = self.patterns['benefits'].findall(block)
        if benefits_matches:
            job.benefits = [benefit.strip() for benefit in benefits_matches]
        
        # 解析職位描述（取最長的文字段落作為描述）
        lines = block.split('\n')
        description_candidates = []
        
        for line in lines:
            line = line.strip()
            # 跳過特定格式的行
            if (line and 
                not line.startswith('Listed') and 
                not line.startswith('This is a') and 
                not line.startswith('subClassification:') and 
                not line.startswith('classification:') and 
                not line.startswith('![') and 
                not line.startswith('-') and 
                not re.match(r'^\d+d?\s+ago$', line) and 
                not line.startswith('$') and 
                len(line) > 20):
                description_candidates.append(line)
        
        if description_candidates:
            # 選擇最長的描述
            job.description = max(description_candidates, key=len)
            # 如果描述太長，取前100個字符作為標題
            if not job.title and len(job.description) > 30:
                job.title = job.description[:100] + "..." if len(job.description) > 100 else job.description
        
        return job
    
    def parse_multiple_files(self, directory_path: Union[str, Path]) -> List[JobListing]:
        """
        解析目錄中的所有 Markdown 檔案
        
        Args:
            directory_path: 包含 Markdown 檔案的目錄路徑
            
        Returns:
            所有檔案解析出的職位資訊列表
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"目錄不存在或不是有效目錄: {directory_path}")
        
        all_jobs = []
        markdown_files = list(directory_path.glob('*.md'))
        
        logger.info(f"找到 {len(markdown_files)} 個 Markdown 檔案")
        
        for file_path in markdown_files:
            try:
                jobs = self.parse_file(file_path)
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"解析檔案 {file_path.name} 時發生錯誤: {e}")
                continue
        
        logger.info(f"總共解析出 {len(all_jobs)} 個職位")
        return all_jobs
    
    def export_to_csv(self, jobs: List[JobListing], output_path: Union[str, Path]) -> None:
        """
        將職位資訊匯出為 CSV 檔案
        
        Args:
            jobs: 職位資訊列表
            output_path: 輸出 CSV 檔案路徑
        """
        output_path = Path(output_path)
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'title', 'company', 'salary', 'job_type', 'location', 
            'posted_date', 'sub_classification', 'classification', 
            'benefits', 'description', 'logo_url', 'company_url'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in jobs:
                job_dict = asdict(job)
                # 將 benefits 列表轉換為字串
                job_dict['benefits'] = '; '.join(job.benefits) if job.benefits else ''
                writer.writerow(job_dict)
        
        logger.info(f"成功匯出 {len(jobs)} 個職位到 {output_path}")
    
    def export_to_json(self, jobs: List[JobListing], output_path: Union[str, Path]) -> None:
        """
        將職位資訊匯出為 JSON 檔案
        
        Args:
            jobs: 職位資訊列表
            output_path: 輸出 JSON 檔案路徑
        """
        output_path = Path(output_path)
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        jobs_data = [asdict(job) for job in jobs]
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(jobs_data, jsonfile, ensure_ascii=False, indent=2)
        
        logger.info(f"成功匯出 {len(jobs)} 個職位到 {output_path}")


def main():
    """
    主函數，示範如何使用 SeekMarkdownParser
    """
    # 設定路徑
    sample_dir = Path(r"C:\Users\a0922\OneDrive\Desktop\Jason_Spyder\JasonSpider\Docs\seek markdown sample")
    output_dir = Path(r"C:\Users\a0922\OneDrive\Desktop\Jason_Spyder\JasonSpider\data\processed")
    
    # 創建解析器
    parser = SeekMarkdownParser()
    
    try:
        # 解析所有 Markdown 檔案
        jobs = parser.parse_multiple_files(sample_dir)
        
        if jobs:
            # 生成時間戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 匯出為 CSV
            csv_path = output_dir / f"seek_jobs_{timestamp}.csv"
            parser.export_to_csv(jobs, csv_path)
            
            # 匯出為 JSON
            json_path = output_dir / f"seek_jobs_{timestamp}.json"
            parser.export_to_json(jobs, json_path)
            
            print(f"解析完成！")
            print(f"總共找到 {len(jobs)} 個職位")
            print(f"CSV 檔案: {csv_path}")
            print(f"JSON 檔案: {json_path}")
        else:
            print("未找到任何職位資訊")
            
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}")
        raise


if __name__ == "__main__":
    main()