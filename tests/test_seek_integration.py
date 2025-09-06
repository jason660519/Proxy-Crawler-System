"""Seek 適配器整合測試

測試 Seek 適配器與 html_to_markdown 模組的整合功能。
"""

import unittest
import asyncio
import sys
from pathlib import Path
from typing import List

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

# 導入 html_to_markdown 模組中的 Seek 適配器
from src.html_to_markdown import SeekMarkdownAdapter, JobListing


class TestSeekIntegration(unittest.TestCase):
    """Seek 適配器整合測試類"""
    
    def setUp(self):
        """測試前置設定"""
        self.adapter = SeekMarkdownAdapter()
        self.sample_dir = Path("C:/Users/a0922/OneDrive/Desktop/Jason_Spyder/JasonSpider/Docs/seek markdown sample")
        self.output_dir = Path("C:/Users/a0922/OneDrive/Desktop/Jason_Spyder/JasonSpider/data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def test_adapter_initialization(self):
        """測試適配器初始化"""
        self.assertIsInstance(self.adapter, SeekMarkdownAdapter)
        self.assertEqual(self.adapter.name, "seek_markdown_adapter")
        self.assertEqual(len(self.adapter.jobs), 0)
    
    def test_job_listing_creation(self):
        """測試 JobListing 數據類"""
        job = JobListing(
            title="Software Engineer",
            company="Tech Corp",
            salary="$80,000",
            job_type="Full time",
            description="Great opportunity for a software engineer"
        )
        
        self.assertTrue(job.is_valid())
        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.company, "Tech Corp")
        
        job_dict = job.to_dict()
        self.assertIsInstance(job_dict, dict)
        self.assertEqual(job_dict['title'], "Software Engineer")
    
    def test_empty_job_listing(self):
        """測試空的 JobListing"""
        empty_job = JobListing()
        self.assertFalse(empty_job.is_valid())
    
    def test_sample_file_processing(self):
        """測試處理示範檔案"""
        if not self.sample_dir.exists():
            self.skipTest("示範檔案目錄不存在")
        
        markdown_files = list(self.sample_dir.glob("*.md"))
        self.assertGreater(len(markdown_files), 0, "未找到 Markdown 檔案")
        
        # 測試處理第一個檔案
        test_file = markdown_files[0]
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用 asyncio 運行異步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.adapter.convert(content, str(test_file))
            )
            
            self.assertTrue(result.success)
            self.assertGreater(len(self.adapter.jobs), 0)
            self.assertIn('total_jobs', result.metadata)
            self.assertEqual(result.metadata['total_jobs'], len(self.adapter.jobs))
            
        finally:
            loop.close()
    
    def test_export_functionality(self):
        """測試匯出功能"""
        # 創建測試數據
        test_jobs = [
            JobListing(
                title="Test Engineer 1",
                company="Test Company 1",
                salary="$70,000",
                job_type="Full time",
                description="Test description 1"
            ),
            JobListing(
                title="Test Engineer 2",
                company="Test Company 2",
                salary="$80,000",
                job_type="Part time",
                description="Test description 2"
            )
        ]
        
        # 手動設置職位數據
        self.adapter.jobs = test_jobs
        
        # 測試 CSV 匯出
        csv_path = self.output_dir / "test_seek_export.csv"
        csv_success = self.adapter.export_to_csv(csv_path)
        self.assertTrue(csv_success)
        self.assertTrue(csv_path.exists())
        
        # 測試 JSON 匯出
        json_path = self.output_dir / "test_seek_export.json"
        json_success = self.adapter.export_to_json(json_path)
        self.assertTrue(json_success)
        self.assertTrue(json_path.exists())
        
        # 清理測試檔案
        if csv_path.exists():
            csv_path.unlink()
        if json_path.exists():
            json_path.unlink()
    
    def test_quality_assessment(self):
        """測試品質評估功能"""
        # 高品質職位
        high_quality_job = JobListing(
            title="Senior Software Engineer - AI/ML",
            company="Tech Innovation Corp",
            salary="$120,000 - $150,000",
            job_type="Full time",
            classification="Engineering - Software",
            description="Exciting opportunity to work with cutting-edge AI and machine learning technologies in a fast-paced startup environment.",
            posted_date="2 days ago"
        )
        
        # 低品質職位
        low_quality_job = JobListing(
            title="Job",
            description="Work"
        )
        
        self.adapter.jobs = [high_quality_job, low_quality_job]
        quality_score = self.adapter._assess_quality()
        
        self.assertGreater(quality_score, 0.0)
        self.assertLessEqual(quality_score, 1.0)
    
    def test_pattern_compilation(self):
        """測試正則表達式模式編譯"""
        self.assertIn('job_block', self.adapter.patterns)
        self.assertIn('salary', self.adapter.patterns)
        self.assertIn('job_type', self.adapter.patterns)
        self.assertIn('posted_date', self.adapter.patterns)
        self.assertIn('classification', self.adapter.patterns)
        self.assertIn('logo_url', self.adapter.patterns)
        self.assertIn('company_url', self.adapter.patterns)
    
    def test_extraction_methods(self):
        """測試各種提取方法"""
        test_text = """
        Senior Software Engineer - AI/ML
        Tech Innovation Corp
        $120,000 - $150,000 per annum
        Full time position
        Posted 3 days ago
        Engineering - Software Development
        https://bx-branding-gateway.cloud.seek.com.au/logo.png
        https://www.seek.com.au/companies/tech-innovation-corp-123456
        Benefits: Flexible working hours, Health insurance, Professional development
        Sydney, NSW
        """
        
        # 測試薪資提取
        salary = self.adapter._extract_salary(test_text)
        self.assertIn("$120,000", salary)
        
        # 測試工作類型提取
        job_type = self.adapter._extract_job_type(test_text)
        self.assertEqual(job_type.lower(), "full time")
        
        # 測試發布日期提取
        posted_date = self.adapter._extract_posted_date(test_text)
        self.assertIn("3 days ago", posted_date)
        
        # 測試分類提取
        classification = self.adapter._extract_classification(test_text)
        self.assertIn("Engineering", classification)
        
        # 測試 Logo URL 提取
        logo_url = self.adapter._extract_logo_url(test_text)
        self.assertTrue(logo_url.startswith("https://"))
        
        # 測試公司 URL 提取
        company_url = self.adapter._extract_company_url(test_text)
        self.assertIn("seek.com.au/companies", company_url)
    
    def test_content_preprocessing(self):
        """測試內容預處理"""
        raw_content = """
        
        
        Test content with multiple newlines
        
        
        
        And some more content
        <!-- HTML comment -->
        Final content
        """
        
        processed = self.adapter._preprocess_content(raw_content)
        
        # 檢查多餘空行是否被移除
        self.assertNotIn("\n\n\n", processed)
        
        # 檢查 HTML 註釋是否被移除
        self.assertNotIn("<!--", processed)
        self.assertNotIn("-->", processed)
    
    def test_job_block_splitting(self):
        """測試職位區塊分割"""
        content = """
        Software Engineer Position
        Great company looking for talented engineers
        
        Data Analyst Role
        Exciting opportunity in data science
        
        Product Manager Job
        Lead product development initiatives
        """
        
        blocks = self.adapter._split_job_blocks(content)
        self.assertGreater(len(blocks), 0)
        
        # 檢查是否正確分割
        for block in blocks:
            self.assertGreater(len(block.strip()), 50)  # 確保區塊不會太短


class TestSeekIntegrationAsync(unittest.IsolatedAsyncioTestCase):
    """Seek 適配器異步整合測試類"""
    
    async def asyncSetUp(self):
        """異步測試前置設定"""
        self.adapter = SeekMarkdownAdapter()
        self.sample_dir = Path("C:/Users/a0922/OneDrive/Desktop/Jason_Spyder/JasonSpider/Docs/seek markdown sample")
    
    async def test_async_conversion(self):
        """測試異步轉換功能"""
        test_content = """
        Senior Python Developer
        Amazing Tech Company
        $90,000 - $110,000
        Full time
        Posted yesterday
        
        We are looking for a talented Python developer to join our team.
        Great benefits and flexible working arrangements.
        """
        
        result = await self.adapter.convert(test_content, "test_url")
        
        self.assertTrue(result.success)
        self.assertGreater(len(self.adapter.jobs), 0)
        self.assertIn("Python Developer", result.content)
    
    async def test_multiple_file_processing(self):
        """測試多檔案處理"""
        if not self.sample_dir.exists():
            self.skipTest("示範檔案目錄不存在")
        
        markdown_files = list(self.sample_dir.glob("*.md"))
        if len(markdown_files) == 0:
            self.skipTest("未找到 Markdown 檔案")
        
        total_jobs = 0
        
        for file_path in markdown_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = await self.adapter.convert(content, str(file_path))
            
            self.assertTrue(result.success)
            total_jobs += len(self.adapter.jobs)
            
            # 重置適配器以處理下一個檔案
            self.adapter.jobs = []
        
        self.assertGreater(total_jobs, 0)


if __name__ == '__main__':
    # 運行測試
    unittest.main(verbosity=2)