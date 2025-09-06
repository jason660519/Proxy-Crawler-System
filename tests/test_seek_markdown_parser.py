#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seek Markdown 解析程式測試模組

此模組用於測試 SeekMarkdownParser 的功能，驗證對三個示範檔案的解析效果。

作者: JasonSpider 專案
日期: 2024
"""

import unittest
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import patch, mock_open

# 添加 src 目錄到 Python 路徑
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from seek_markdown_parser import SeekMarkdownParser, JobListing


class TestSeekMarkdownParser(unittest.TestCase):
    """
    SeekMarkdownParser 測試類別
    """
    
    def setUp(self):
        """測試前的設定"""
        self.parser = SeekMarkdownParser()
        self.sample_dir = Path(r"C:\Users\a0922\OneDrive\Desktop\Jason_Spyder\JasonSpider\Docs\seek markdown sample")
        
        # 測試用的 Markdown 內容
        self.sample_markdown = """
# AI Jobs (with Salaries) - SEEK

Listed two days ago

This is a Full time job

$180,000

Work with bleeding edge Gen & Agentic AI, Azure & Databricks to build scalable ML infrastructure and shape next-gen technology.

subClassification: Engineering - SoftwareEngineering - Software

classification: Information & Communication Technology(Information & Communication Technology)

2d ago

Listed twenty four days ago

![SerpLogo](https://bx-branding-gateway.cloud.seek.com.au/82326e63-b922-439d-a070-f7423f91fe91.1/serpLogo)

Expiring soon

This is a Full time job

+ stock options, 401(k) and health coverages

-   Work from NYC or Santa Clara (California)
-   Build a cutting-edge BCI to enhance quality of life
-   Collaborate with a world-class team of neuroscientists and engineers

Live in NYC or San Francisco: Open call for ML Engineers and Scientists with a passion for neurotechnology and human-centered AI.

subClassification: Modelling & SimulationModelling & Simulation

classification: Science & Technology(Science & Technology)

24d ago
        """
    
    def test_job_listing_dataclass(self):
        """測試 JobListing 資料類別"""
        job = JobListing(
            title="AI Engineer",
            company="Test Company",
            salary="$100,000",
            job_type="Full time"
        )
        
        self.assertEqual(job.title, "AI Engineer")
        self.assertEqual(job.company, "Test Company")
        self.assertEqual(job.salary, "$100,000")
        self.assertEqual(job.job_type, "Full time")
        self.assertIsInstance(job.benefits, list)
    
    def test_split_job_blocks(self):
        """測試職位區塊分割功能"""
        blocks = self.parser._split_job_blocks(self.sample_markdown)
        
        # 應該至少分割出兩個職位區塊
        self.assertGreaterEqual(len(blocks), 2)
        
        # 每個區塊都應該包含 "Listed" 關鍵字
        for block in blocks:
            self.assertIn("Listed", block)
    
    def test_parse_job_block(self):
        """測試單個職位區塊解析"""
        job_block = """
Listed two days ago

This is a Full time job

$180,000

Work with bleeding edge Gen & Agentic AI, Azure & Databricks to build scalable ML infrastructure and shape next-gen technology.

subClassification: Engineering - SoftwareEngineering - Software

classification: Information & Communication Technology(Information & Communication Technology)

2d ago
        """
        
        job = self.parser._parse_job_block(job_block)
        
        # 驗證解析結果
        self.assertEqual(job.posted_date, "two days")
        self.assertEqual(job.job_type, "Full time")
        self.assertEqual(job.salary, "$180,000")
        self.assertIn("AI", job.description)
        self.assertEqual(job.sub_classification, "Engineering - SoftwareEngineering - Software")
        self.assertEqual(job.classification, "Information & Communication Technology")
    
    def test_parse_job_block_with_benefits(self):
        """測試包含福利資訊的職位區塊解析"""
        job_block = """
Listed twenty four days ago

This is a Full time job

+ stock options, 401(k) and health coverages

-   Work from NYC or Santa Clara (California)
-   Build a cutting-edge BCI to enhance quality of life
-   Collaborate with a world-class team of neuroscientists and engineers

Live in NYC or San Francisco: Open call for ML Engineers and Scientists.

subClassification: Modelling & SimulationModelling & Simulation

classification: Science & Technology(Science & Technology)
        """
        
        job = self.parser._parse_job_block(job_block)
        
        # 驗證福利資訊解析
        self.assertGreaterEqual(len(job.benefits), 3)
        self.assertIn("Work from NYC or Santa Clara (California)", job.benefits)
        self.assertIn("Build a cutting-edge BCI to enhance quality of life", job.benefits)
        
        # 驗證其他欄位
        self.assertEqual(job.posted_date, "twenty four days")
        self.assertEqual(job.job_type, "Full time")
        self.assertEqual(job.sub_classification, "Modelling & SimulationModelling & Simulation")
        self.assertEqual(job.classification, "Science & Technology")
    
    @patch('builtins.open', new_callable=mock_open)
    def test_parse_file_mock(self, mock_file):
        """測試檔案解析功能（使用 mock）"""
        mock_file.return_value.read.return_value = self.sample_markdown
        
        with patch('pathlib.Path.exists', return_value=True):
            jobs = self.parser.parse_file("fake_file.md")
        
        # 應該解析出至少一個職位
        self.assertGreater(len(jobs), 0)
        
        # 驗證第一個職位的基本資訊
        first_job = jobs[0]
        self.assertIsInstance(first_job, JobListing)
        self.assertTrue(first_job.salary or first_job.description)
    
    def test_export_to_csv(self):
        """測試 CSV 匯出功能"""
        # 創建測試資料
        test_jobs = [
            JobListing(
                title="AI Engineer",
                company="Test Company",
                salary="$100,000",
                job_type="Full time",
                benefits=["Health insurance", "Stock options"]
            ),
            JobListing(
                title="Data Scientist",
                company="Another Company",
                salary="$120,000",
                job_type="Contract"
            )
        ]
        
        # 使用臨時檔案測試
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # 匯出到 CSV
            self.parser.export_to_csv(test_jobs, temp_path)
            
            # 驗證檔案內容
            with open(temp_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['title'], "AI Engineer")
            self.assertEqual(rows[0]['salary'], "$100,000")
            self.assertEqual(rows[0]['benefits'], "Health insurance; Stock options")
            
        finally:
            # 清理臨時檔案
            if temp_path.exists():
                temp_path.unlink()
    
    def test_export_to_json(self):
        """測試 JSON 匯出功能"""
        # 創建測試資料
        test_jobs = [
            JobListing(
                title="AI Engineer",
                company="Test Company",
                salary="$100,000",
                job_type="Full time",
                benefits=["Health insurance", "Stock options"]
            )
        ]
        
        # 使用臨時檔案測試
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # 匯出到 JSON
            self.parser.export_to_json(test_jobs, temp_path)
            
            # 驗證檔案內容
            with open(temp_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['title'], "AI Engineer")
            self.assertEqual(data[0]['salary'], "$100,000")
            self.assertIsInstance(data[0]['benefits'], list)
            
        finally:
            # 清理臨時檔案
            if temp_path.exists():
                temp_path.unlink()
    
    @unittest.skipUnless(
        Path(r"C:\Users\a0922\OneDrive\Desktop\Jason_Spyder\JasonSpider\Docs\seek markdown sample").exists(),
        "示範檔案目錄不存在"
    )
    def test_parse_real_files(self):
        """測試解析真實的示範檔案"""
        if not self.sample_dir.exists():
            self.skipTest("示範檔案目錄不存在")
        
        # 檢查是否有 Markdown 檔案
        markdown_files = list(self.sample_dir.glob('*.md'))
        if not markdown_files:
            self.skipTest("示範目錄中沒有 Markdown 檔案")
        
        # 解析所有檔案
        jobs = self.parser.parse_multiple_files(self.sample_dir)
        
        # 基本驗證
        self.assertIsInstance(jobs, list)
        
        if jobs:
            # 驗證至少有一些有效的職位資訊
            valid_jobs = [job for job in jobs if job.title or job.description]
            self.assertGreater(len(valid_jobs), 0)
            
            # 驗證資料結構
            for job in valid_jobs[:5]:  # 檢查前5個職位
                self.assertIsInstance(job, JobListing)
                self.assertIsInstance(job.benefits, list)
        
        print(f"\n成功解析 {len(jobs)} 個職位")
        if jobs:
            print(f"第一個職位範例:")
            print(f"  標題: {jobs[0].title[:100]}...")
            print(f"  薪資: {jobs[0].salary}")
            print(f"  類型: {jobs[0].job_type}")
            print(f"  分類: {jobs[0].classification}")


class TestIntegration(unittest.TestCase):
    """整合測試類別"""
    
    def setUp(self):
        """測試前的設定"""
        self.parser = SeekMarkdownParser()
        self.sample_dir = Path(r"C:\Users\a0922\OneDrive\Desktop\Jason_Spyder\JasonSpider\Docs\seek markdown sample")
        self.output_dir = Path(r"C:\Users\a0922\OneDrive\Desktop\Jason_Spyder\JasonSpider\data\processed")
    
    @unittest.skipUnless(
        Path(r"C:\Users\a0922\OneDrive\Desktop\Jason_Spyder\JasonSpider\Docs\seek markdown sample").exists(),
        "示範檔案目錄不存在"
    )
    def test_full_workflow(self):
        """測試完整的工作流程"""
        if not self.sample_dir.exists():
            self.skipTest("示範檔案目錄不存在")
        
        # 確保輸出目錄存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. 解析檔案
            jobs = self.parser.parse_multiple_files(self.sample_dir)
            
            if not jobs:
                self.skipTest("沒有解析到任何職位資訊")
            
            # 2. 匯出為 CSV
            csv_path = self.output_dir / "test_seek_jobs.csv"
            self.parser.export_to_csv(jobs, csv_path)
            self.assertTrue(csv_path.exists())
            
            # 3. 匯出為 JSON
            json_path = self.output_dir / "test_seek_jobs.json"
            self.parser.export_to_json(jobs, json_path)
            self.assertTrue(json_path.exists())
            
            # 4. 驗證匯出的檔案
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                csv_rows = list(csv_reader)
            
            with open(json_path, 'r', encoding='utf-8') as jsonfile:
                json_data = json.load(jsonfile)
            
            # 驗證資料一致性
            self.assertEqual(len(csv_rows), len(json_data))
            self.assertEqual(len(csv_rows), len(jobs))
            
            print(f"\n完整工作流程測試成功:")
            print(f"  解析職位數量: {len(jobs)}")
            print(f"  CSV 檔案: {csv_path}")
            print(f"  JSON 檔案: {json_path}")
            
        finally:
            # 清理測試檔案
            for file_path in [self.output_dir / "test_seek_jobs.csv", self.output_dir / "test_seek_jobs.json"]:
                if file_path.exists():
                    file_path.unlink()


def run_tests():
    """執行所有測試"""
    # 創建測試套件
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # 添加測試類別
    test_suite.addTest(loader.loadTestsFromTestCase(TestSeekMarkdownParser))
    test_suite.addTest(loader.loadTestsFromTestCase(TestIntegration))
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("開始執行 Seek Markdown 解析程式測試...")
    success = run_tests()
    
    if success:
        print("\n所有測試通過！")
    else:
        print("\n部分測試失敗，請檢查錯誤訊息。")
        sys.exit(1)