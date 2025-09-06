#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 資料流程管理器
實現統一的 ETL 流程：原始資料(.md) -> 結構化資料(.csv) -> 轉換資料(.json)
"""

import asyncio
import json
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
from loguru import logger

from .core import ConversionConfig, ConversionResult
from .converters import MarkdownifyConverter


@dataclass
class DataPipelineConfig:
    """資料流程配置"""
    base_data_dir: Path = Path("data")
    source_name: str = "html-to-markdown"
    enable_llm_processing: bool = False
    llm_model: str = "gpt-3.5-turbo"
    batch_size: int = 100
    max_workers: int = 4


@dataclass
class ProcessedRecord:
    """處理後的記錄結構"""
    id: str
    source_url: Optional[str]
    title: str
    content: str
    content_length: int
    processing_time: float
    timestamp: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class TransformedRecord:
    """轉換後的記錄結構（用於資料庫）"""
    id: str
    source_url: Optional[str]
    title: str
    content_preview: str  # 前 200 字符
    full_content: str
    word_count: int
    processing_time: float
    quality_score: float
    tags: List[str]
    created_at: str
    updated_at: str


class HTMLToMarkdownPipeline:
    """HTML to Markdown 資料流程管理器"""
    
    def __init__(self, config: DataPipelineConfig):
        """
        初始化資料流程管理器
        
        Args:
            config: 資料流程配置
        """
        self.config = config
        self.base_dir = config.base_data_dir
        self.source_name = config.source_name
        
        # 設定目錄路徑
        self.raw_dir = self.base_dir / "raw" / self.source_name
        self.processed_dir = self.base_dir / "processed" / self.source_name
        self.transformed_dir = self.base_dir / "transformed" / self.source_name
        
        # 確保目錄存在
        self._ensure_directories()
        
        # 初始化轉換器
        conversion_config = ConversionConfig(engine="markdownify")
        self.converter = MarkdownifyConverter(conversion_config)
        
        logger.info(f"資料流程管理器已初始化，來源：{self.source_name}")
    
    def _ensure_directories(self) -> None:
        """確保所有必要的目錄存在"""
        for directory in [self.raw_dir, self.processed_dir, self.transformed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"目錄已確保存在：{directory}")
    
    def _generate_filename(self, stage: str, extension: str) -> str:
        """生成檔案名稱"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.source_name}_{stage}_{timestamp}.{extension}"
    
    async def stage1_save_raw_markdown(self, 
                                     html_content: str, 
                                     source_url: Optional[str] = None,
                                     metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        階段1：將 HTML 轉換為 Markdown 並保存為原始資料
        
        Args:
            html_content: HTML 內容
            source_url: 來源 URL
            metadata: 額外的元資料
            
        Returns:
            保存的檔案路徑
        """
        logger.info("開始階段1：HTML 轉換為 Markdown")
        
        try:
            # 轉換 HTML 為 Markdown
            result = await self.converter.convert(html_content)
            
            if not result.success:
                raise ValueError(f"HTML 轉換失敗：{result.error_message}")
            
            # 準備檔案內容
            file_content = self._prepare_raw_content(result, source_url, metadata)
            
            # 保存檔案
            filename = self._generate_filename("raw", "md")
            file_path = self.raw_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            logger.success(f"原始 Markdown 已保存：{file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"階段1處理失敗：{e}")
            raise
    
    def _prepare_raw_content(self, 
                           result: ConversionResult, 
                           source_url: Optional[str],
                           metadata: Optional[Dict[str, Any]]) -> str:
        """準備原始檔案內容"""
        header = []
        header.append("---")
        header.append(f"source_url: {source_url or 'N/A'}")
        header.append(f"processing_time: {result.processing_time}")
        header.append(f"original_length: {result.original_length}")
        header.append(f"timestamp: {datetime.now().isoformat()}")
        
        if metadata:
            for key, value in metadata.items():
                header.append(f"{key}: {value}")
        
        header.append("---")
        header.append("")
        
        return "\n".join(header) + result.content
    
    def stage2_parse_to_csv(self, raw_file_path: Path) -> Path:
        """
        階段2：解析 Markdown 檔案並轉換為結構化的 CSV 格式
        
        Args:
            raw_file_path: 原始 Markdown 檔案路徑
            
        Returns:
            CSV 檔案路徑
        """
        logger.info(f"開始階段2：解析 Markdown 為 CSV - {raw_file_path.name}")
        
        try:
            # 讀取原始檔案
            with open(raw_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析檔案
            metadata, markdown_content = self._parse_raw_file(content)
            
            # 創建處理記錄
            record = ProcessedRecord(
                id=raw_file_path.stem,
                source_url=metadata.get('source_url'),
                title=self._extract_title(markdown_content),
                content=markdown_content,
                content_length=len(markdown_content),
                processing_time=float(metadata.get('processing_time', 0)),
                timestamp=metadata.get('timestamp', datetime.now().isoformat()),
                success=True
            )
            
            # 保存為 CSV
            filename = self._generate_filename("processed", "csv")
            csv_path = self.processed_dir / filename
            
            self._save_to_csv([record], csv_path)
            
            logger.success(f"CSV 檔案已保存：{csv_path}")
            return csv_path
            
        except Exception as e:
            logger.error(f"階段2處理失敗：{e}")
            raise
    
    def _parse_raw_file(self, content: str) -> tuple[Dict[str, str], str]:
        """解析原始檔案的元資料和內容"""
        lines = content.split('\n')
        
        if not lines[0].strip() == '---':
            return {}, content
        
        metadata = {}
        content_start = 0
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                content_start = i + 1
                break
            
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        markdown_content = '\n'.join(lines[content_start:]).strip()
        return metadata, markdown_content
    
    def _extract_title(self, markdown_content: str) -> str:
        """從 Markdown 內容中提取標題"""
        lines = markdown_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        
        # 如果沒有找到標題，使用第一行非空內容
        for line in lines:
            line = line.strip()
            if line:
                return line[:50] + ('...' if len(line) > 50 else '')
        
        return "無標題"
    
    def _save_to_csv(self, records: List[ProcessedRecord], file_path: Path) -> None:
        """保存記錄到 CSV 檔案"""
        df = pd.DataFrame([asdict(record) for record in records])
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    def stage3_transform_to_json(self, csv_file_path: Path) -> Path:
        """
        階段3：將 CSV 資料轉換為可直接導入資料庫的 JSON 格式
        
        Args:
            csv_file_path: CSV 檔案路徑
            
        Returns:
            JSON 檔案路徑
        """
        logger.info(f"開始階段3：轉換 CSV 為 JSON - {csv_file_path.name}")
        
        try:
            # 讀取 CSV 檔案
            df = pd.read_csv(csv_file_path)
            
            # 轉換為資料庫格式
            transformed_records = []
            
            for _, row in df.iterrows():
                record = TransformedRecord(
                    id=row['id'],
                    source_url=row['source_url'] if pd.notna(row['source_url']) else None,
                    title=row['title'],
                    content_preview=row['content'][:200],
                    full_content=row['content'],
                    word_count=len(row['content'].split()),
                    processing_time=row['processing_time'],
                    quality_score=self._calculate_quality_score(row),
                    tags=self._extract_tags(row['content']),
                    created_at=row['timestamp'],
                    updated_at=datetime.now().isoformat()
                )
                
                transformed_records.append(asdict(record))
            
            # 保存為 JSON
            filename = self._generate_filename("transformed", "json")
            json_path = self.transformed_dir / filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(transformed_records, f, ensure_ascii=False, indent=2)
            
            logger.success(f"JSON 檔案已保存：{json_path}")
            return json_path
            
        except Exception as e:
            logger.error(f"階段3處理失敗：{e}")
            raise
    
    def _calculate_quality_score(self, row: pd.Series) -> float:
        """計算內容品質分數"""
        score = 0.0
        
        # 基於內容長度
        content_length = row['content_length']
        if content_length > 1000:
            score += 0.4
        elif content_length > 500:
            score += 0.3
        elif content_length > 100:
            score += 0.2
        
        # 基於標題品質
        title = row['title']
        if title and title != "無標題" and len(title) > 5:
            score += 0.3
        
        # 基於處理時間（越快越好）
        processing_time = row['processing_time']
        if processing_time < 0.01:
            score += 0.3
        elif processing_time < 0.1:
            score += 0.2
        elif processing_time < 1.0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_tags(self, content: str) -> List[str]:
        """從內容中提取標籤"""
        tags = []
        
        # 基於內容特徵添加標籤
        if '```' in content:
            tags.append('code')
        if '|' in content and '---' in content:
            tags.append('table')
        if content.count('#') > 3:
            tags.append('structured')
        if len(content) > 2000:
            tags.append('long-form')
        if len(content.split()) > 500:
            tags.append('detailed')
        
        return tags
    
    async def run_full_pipeline(self, 
                              html_content: str, 
                              source_url: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
        """
        執行完整的資料流程
        
        Args:
            html_content: HTML 內容
            source_url: 來源 URL
            metadata: 額外的元資料
            
        Returns:
            各階段產生的檔案路徑
        """
        logger.info("開始執行完整的 HTML to Markdown 資料流程")
        
        try:
            # 階段1：HTML -> Markdown (raw)
            raw_path = await self.stage1_save_raw_markdown(html_content, source_url, metadata)
            
            # 階段2：Markdown -> CSV (processed)
            csv_path = self.stage2_parse_to_csv(raw_path)
            
            # 階段3：CSV -> JSON (transformed)
            json_path = self.stage3_transform_to_json(csv_path)
            
            result = {
                'raw': raw_path,
                'processed': csv_path,
                'transformed': json_path
            }
            
            logger.success("完整資料流程執行成功")
            return result
            
        except Exception as e:
            logger.error(f"資料流程執行失敗：{e}")
            raise
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """獲取資料流程狀態"""
        status = {
            'raw_files': len(list(self.raw_dir.glob('*.md'))),
            'processed_files': len(list(self.processed_dir.glob('*.csv'))),
            'transformed_files': len(list(self.transformed_dir.glob('*.json'))),
            'directories': {
                'raw': str(self.raw_dir),
                'processed': str(self.processed_dir),
                'transformed': str(self.transformed_dir)
            }
        }
        
        return status


# 使用範例
if __name__ == "__main__":
    async def demo():
        """示範完整的資料流程"""
        # 配置
        config = DataPipelineConfig(
            base_data_dir=Path("data"),
            source_name="html-to-markdown"
        )
        
        # 初始化流程管理器
        pipeline = HTMLToMarkdownPipeline(config)
        
        # 示範 HTML 內容
        html_content = """
        <div>
            <h1>測試文章</h1>
            <p>這是一個測試的 HTML 內容，用於示範完整的資料流程。</p>
            <ul>
                <li>項目 1</li>
                <li>項目 2</li>
            </ul>
            <table>
                <tr><th>欄位1</th><th>欄位2</th></tr>
                <tr><td>資料1</td><td>資料2</td></tr>
            </table>
        </div>
        """
        
        # 執行完整流程
        result = await pipeline.run_full_pipeline(
            html_content=html_content,
            source_url="https://example.com/test",
            metadata={"author": "測試作者", "category": "demo"}
        )
        
        print("資料流程完成！")
        print(f"原始檔案：{result['raw']}")
        print(f"處理檔案：{result['processed']}")
        print(f"轉換檔案：{result['transformed']}")
        
        # 顯示狀態
        status = pipeline.get_pipeline_status()
        print(f"\n流程狀態：{status}")
    
    asyncio.run(demo())