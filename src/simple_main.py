#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版主應用程式
整合所有功能到單一應用中，包含：
- 代理管理 API
- HTML 轉 Markdown 轉換
- 系統監控
- Web 界面
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 導入項目模組
from src.proxy_manager.api import router as proxy_router
from src.api.unified_api import router as api_router
from src.core.logger import setup_logger
from src.core.config import get_settings
from src.html_to_markdown.core import HTMLToMarkdownConverter
from src.html_to_markdown.api_server import create_html_converter_router

# 設置日誌
logger = setup_logger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Proxy Crawler System - 簡化版",
    description="整合代理爬蟲、HTML 轉換和管理功能的統一應用",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態文件和模板
static_dir = project_root / "static"
templates_dir = project_root / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
else:
    templates = None

# 全局變數
settings = get_settings()
html_converter: Optional[HTMLToMarkdownConverter] = None


@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    global html_converter
    
    logger.info("正在啟動簡化版 Proxy Crawler System...")
    
    try:
        # 初始化 HTML 轉換器
        html_converter = HTMLToMarkdownConverter()
        logger.info("HTML 轉換器初始化完成")
        
        # 創建必要的目錄
        directories = [
            project_root / "logs",
            project_root / "data",
            project_root / "data" / "raw",
            project_root / "data" / "processed",
            project_root / "data" / "transformed"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("應用啟動完成")
        
    except Exception as e:
        logger.error(f"應用啟動失敗: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時的清理"""
    logger.info("正在關閉應用...")


# 健康檢查端點
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "proxy-crawler-simple",
        "version": "1.0.0",
        "features": {
            "proxy_management": True,
            "html_conversion": html_converter is not None,
            "web_interface": templates is not None
        }
    }


# 根路徑 - 簡單的歡迎頁面
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路徑 - 顯示歡迎頁面"""
    if templates:
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "title": "Proxy Crawler System"}
        )
    else:
        # 簡單的 HTML 響應
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Proxy Crawler System</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .feature { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .api-link { color: #007bff; text-decoration: none; }
                .api-link:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Proxy Crawler System - 簡化版</h1>
                <p>歡迎使用整合式代理爬蟲管理系統</p>
                
                <div class="feature">
                    <h3>📡 代理管理 API</h3>
                    <p>管理和驗證代理伺服器</p>
                    <a href="/api/proxies" class="api-link">查看代理列表</a>
                </div>
                
                <div class="feature">
                    <h3>🔄 HTML 轉 Markdown</h3>
                    <p>將 HTML 內容轉換為 Markdown 格式</p>
                    <a href="/convert/docs" class="api-link">轉換 API 文檔</a>
                </div>
                
                <div class="feature">
                    <h3>📊 系統狀態</h3>
                    <p>查看系統健康狀態和統計資訊</p>
                    <a href="/health" class="api-link">健康檢查</a> | 
                    <a href="/docs" class="api-link">API 文檔</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)


# HTML 轉 Markdown API
@app.post("/convert/html-to-markdown")
async def convert_html_to_markdown(request: Dict[str, Any]) -> Dict[str, Any]:
    """將 HTML 轉換為 Markdown"""
    if not html_converter:
        raise HTTPException(status_code=503, detail="HTML 轉換器未初始化")
    
    try:
        html_content = request.get("html", "")
        if not html_content:
            raise HTTPException(status_code=400, detail="缺少 HTML 內容")
        
        # 執行轉換
        markdown_result = await html_converter.convert_async(html_content)
        
        return {
            "success": True,
            "markdown": markdown_result,
            "original_length": len(html_content),
            "converted_length": len(markdown_result)
        }
        
    except Exception as e:
        logger.error(f"HTML 轉換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"轉換失敗: {str(e)}")


# 系統資訊端點
@app.get("/info")
async def system_info() -> Dict[str, Any]:
    """獲取系統資訊"""
    return {
        "application": "Proxy Crawler System - Simple",
        "version": "1.0.0",
        "python_version": sys.version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "proxy_management": True,
            "html_conversion": True,
            "web_interface": True,
            "api_documentation": True
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "proxy_api": "/api/proxies",
            "html_convert": "/convert/html-to-markdown",
            "system_info": "/info"
        }
    }


# 註冊路由
app.include_router(proxy_router, prefix="/api", tags=["代理管理"])
app.include_router(api_router, prefix="/api", tags=["統一 API"])

# 如果 HTML 轉換器可用，註冊轉換路由
if html_converter:
    try:
        convert_router = create_html_converter_router()
        app.include_router(convert_router, prefix="/convert", tags=["HTML 轉換"])
    except Exception as e:
        logger.warning(f"無法註冊 HTML 轉換路由: {e}")


def main():
    """主函數 - 啟動應用"""
    # 從環境變數獲取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"正在啟動服務於 {host}:{port}")
    
    # 啟動 Uvicorn 服務器
    uvicorn.run(
        "simple_main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=os.getenv("ENVIRONMENT") == "development",
        access_log=True
    )


if __name__ == "__main__":
    main()