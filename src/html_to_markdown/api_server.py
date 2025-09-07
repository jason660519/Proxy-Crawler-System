#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown API 服務器

提供 RESTful API 介面來處理 HTML to Markdown 轉換任務。
支援單一轉換和批量處理功能。
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger

from .data_pipeline import HTMLToMarkdownPipeline, DataPipelineConfig
from .core import ConversionConfig, ConversionEngine, ContentScope, OutputFormat


# === Pydantic 模型定義 ===

class ConversionRequest(BaseModel):
    """轉換請求模型"""
    html_content: str = Field(..., description="要轉換的 HTML 內容")
    source_url: Optional[str] = Field(None, description="來源 URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="額外的元數據")
    engine: Optional[str] = Field("markdownify", description="轉換引擎")
    scope: Optional[str] = Field("full", description="內容範圍")
    output_format: Optional[str] = Field("github", description="輸出格式")


class BatchConversionRequest(BaseModel):
    """批量轉換請求模型"""
    items: List[ConversionRequest] = Field(..., description="轉換項目列表")
    batch_size: Optional[int] = Field(10, description="批次大小")


class ConversionResponse(BaseModel):
    """轉換回應模型"""
    success: bool = Field(..., description="轉換是否成功")
    markdown_content: Optional[str] = Field(None, description="轉換後的 Markdown 內容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="轉換元數據")
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    processing_time: Optional[float] = Field(None, description="處理時間（秒）")
    quality_score: Optional[float] = Field(None, description="品質評分")


class BatchConversionResponse(BaseModel):
    """批量轉換回應模型"""
    total_items: int = Field(..., description="總項目數")
    successful_conversions: int = Field(..., description="成功轉換數")
    failed_conversions: int = Field(..., description="失敗轉換數")
    success_rate: float = Field(..., description="成功率")
    results: List[ConversionResponse] = Field(..., description="轉換結果列表")
    processing_time: float = Field(..., description="總處理時間（秒）")


class PipelineStatusResponse(BaseModel):
    """流程狀態回應模型"""
    status: str = Field(..., description="流程狀態")
    message: str = Field(..., description="狀態訊息")
    timestamp: datetime = Field(..., description="時間戳")
    data_directories: Dict[str, str] = Field(..., description="資料目錄路徑")


# === FastAPI 應用程式初始化 ===

app = FastAPI(
    title="HTML to Markdown API",
    description="企業級 HTML to Markdown 轉換服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全域變數
pipeline: Optional[HTMLToMarkdownPipeline] = None


@app.on_event("startup")
async def startup_event():
    """應用程式啟動事件"""
    global pipeline
    
    logger.info("正在啟動 HTML to Markdown API 服務...")
    
    # 初始化資料流程
    config = DataPipelineConfig(
        base_data_dir=Path(os.getenv("OUTPUT_DIR", "/app/output")).parent,
        source_name="html-to-markdown"
    )
    
    pipeline = HTMLToMarkdownPipeline(config)
    
    logger.info(f"API 服務已啟動，資料目錄：{config.base_data_dir}")


@app.on_event("shutdown")
async def shutdown_event():
    """應用程式關閉事件"""
    logger.info("HTML to Markdown API 服務正在關閉...")


# === API 端點定義 ===

@app.get("/", response_model=Dict[str, str])
async def root():
    """根端點"""
    return {
        "service": "HTML to Markdown API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "html-to-markdown"
    }


@app.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """取得流程狀態"""
    if not pipeline:
        raise HTTPException(status_code=500, detail="流程尚未初始化")
    
    return PipelineStatusResponse(
        status="ready",
        message="流程已就緒，可以處理轉換請求",
        timestamp=datetime.now(),
        data_directories={
            "raw": str(pipeline.config.raw_dir),
            "processed": str(pipeline.config.processed_dir),
            "transformed": str(pipeline.config.transformed_dir)
        }
    )


@app.post("/convert", response_model=ConversionResponse)
async def convert_html(request: ConversionRequest):
    """單一 HTML 轉換端點"""
    if not pipeline:
        raise HTTPException(status_code=500, detail="流程尚未初始化")
    
    try:
        start_time = datetime.now()
        
        # 執行轉換
        result = await pipeline.run_full_pipeline(
            html_content=request.html_content,
            source_url=request.source_url or "api://single-conversion",
            metadata=request.metadata or {}
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result.success and result.conversion_results:
            conversion_result = result.conversion_results[0]
            return ConversionResponse(
                success=True,
                markdown_content=conversion_result.content,
                metadata={
                    "original_length": conversion_result.original_length,
                    "converted_length": conversion_result.converted_length,
                    "engine_used": conversion_result.engine_used.value,
                    "output_files": [str(f) for f in result.output_files]
                },
                processing_time=processing_time,
                quality_score=getattr(conversion_result, 'quality_score', None)
            )
        else:
            return ConversionResponse(
                success=False,
                error_message=result.errors[0] if result.errors else "轉換失敗",
                processing_time=processing_time
            )
    
    except Exception as e:
        logger.error(f"轉換過程中發生錯誤：{e}")
        return ConversionResponse(
            success=False,
            error_message=str(e),
            processing_time=0
        )


@app.post("/convert/batch", response_model=BatchConversionResponse)
async def convert_html_batch(request: BatchConversionRequest, background_tasks: BackgroundTasks):
    """批量 HTML 轉換端點"""
    if not pipeline:
        raise HTTPException(status_code=500, detail="流程尚未初始化")
    
    start_time = datetime.now()
    results = []
    successful_count = 0
    
    try:
        for item in request.items:
            try:
                # 執行單一轉換
                result = await pipeline.run_full_pipeline(
                    html_content=item.html_content,
                    source_url=item.source_url or f"api://batch-conversion-{len(results)}",
                    metadata=item.metadata or {}
                )
                
                if result.success and result.conversion_results:
                    conversion_result = result.conversion_results[0]
                    results.append(ConversionResponse(
                        success=True,
                        markdown_content=conversion_result.content,
                        metadata={
                            "original_length": conversion_result.original_length,
                            "converted_length": conversion_result.converted_length,
                            "engine_used": conversion_result.engine_used.value
                        },
                        quality_score=getattr(conversion_result, 'quality_score', None)
                    ))
                    successful_count += 1
                else:
                    results.append(ConversionResponse(
                        success=False,
                        error_message=result.errors[0] if result.errors else "轉換失敗"
                    ))
            
            except Exception as e:
                logger.error(f"批量轉換項目失敗：{e}")
                results.append(ConversionResponse(
                    success=False,
                    error_message=str(e)
                ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        total_items = len(request.items)
        failed_count = total_items - successful_count
        
        return BatchConversionResponse(
            total_items=total_items,
            successful_conversions=successful_count,
            failed_conversions=failed_count,
            success_rate=successful_count / total_items if total_items > 0 else 0,
            results=results,
            processing_time=processing_time
        )
    
    except Exception as e:
        logger.error(f"批量轉換過程中發生錯誤：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_html_file(file: UploadFile = File(...)):
    """上傳 HTML 檔案進行轉換"""
    if not pipeline:
        raise HTTPException(status_code=500, detail="流程尚未初始化")
    
    if not file.filename.endswith(('.html', '.htm')):
        raise HTTPException(status_code=400, detail="只支援 HTML 檔案")
    
    try:
        # 讀取檔案內容
        content = await file.read()
        html_content = content.decode('utf-8')
        
        # 執行轉換
        result = await pipeline.run_full_pipeline(
            html_content=html_content,
            source_url=f"upload://{file.filename}",
            metadata={"filename": file.filename, "file_size": len(content)}
        )
        
        if result.success and result.conversion_results:
            conversion_result = result.conversion_results[0]
            return ConversionResponse(
                success=True,
                markdown_content=conversion_result.content,
                metadata={
                    "filename": file.filename,
                    "original_length": conversion_result.original_length,
                    "converted_length": conversion_result.converted_length,
                    "engine_used": conversion_result.engine_used.value,
                    "output_files": [str(f) for f in result.output_files]
                },
                quality_score=getattr(conversion_result, 'quality_score', None)
            )
        else:
            return ConversionResponse(
                success=False,
                error_message=result.errors[0] if result.errors else "轉換失敗"
            )
    
    except Exception as e:
        logger.error(f"檔案上傳轉換失敗：{e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """主要執行函數"""
    # 配置日誌
    logger.remove()
    logger.add(
        "/app/logs/api_server_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # 啟動服務器
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"正在啟動 HTML to Markdown API 服務器於 {host}:{port}")
    
    uvicorn.run(
        "src.html_to_markdown.api_server:app",
        host=host,
        port=port,
        reload=False,
        workers=1
    )


if __name__ == "__main__":
    main()