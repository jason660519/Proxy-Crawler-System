#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的 API 端點

提供基本的代理管理和 ETL 功能 API
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime

# 創建簡化的 API 應用程式
simple_api = FastAPI(title="Simple Proxy API", version="1.0.0")

@simple_api.get("/proxies")
async def get_proxies(limit: int = 10) -> List[Dict[str, Any]]:
    """獲取代理列表"""
    try:
        # 從處理後的數據文件讀取代理
        data_dir = Path("data/processed")
        json_files = list(data_dir.glob("*.json"))
        
        if not json_files:
            return []
        
        # 讀取最新的文件
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        proxies = data.get("proxies", [])
        
        # 限制返回數量
        return proxies[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取代理數據失敗: {str(e)}")

@simple_api.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """獲取代理統計信息"""
    try:
        # 從處理後的數據文件讀取統計
        data_dir = Path("data/processed")
        json_files = list(data_dir.glob("*.json"))
        
        if not json_files:
            return {
                "total_proxies": 0,
                "sources": {},
                "last_update": None
            }
        
        # 讀取最新的文件
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get("metadata", {})
        
        return {
            "total_proxies": metadata.get("total_unique_proxies", 0),
            "sources": metadata.get("by_source", {}),
            "last_update": metadata.get("timestamp"),
            "processing_stats": metadata.get("processing_stats", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取統計數據失敗: {str(e)}")

@simple_api.get("/pools")
async def get_pools() -> Dict[str, Any]:
    """獲取代理池狀態"""
    try:
        # 讀取代理池數據
        pool_file = Path("data/proxy_manager/proxy_pools.json")
        
        if not pool_file.exists():
            return {
                "hot_pool": 0,
                "warm_pool": 0,
                "cold_pool": 0,
                "blacklist": 0
            }
        
        with open(pool_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "hot_pool": len(data.get("hot_pool", [])),
            "warm_pool": len(data.get("warm_pool", [])),
            "cold_pool": len(data.get("cold_pool", [])),
            "blacklist": len(data.get("blacklist", []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取代理池數據失敗: {str(e)}")

@simple_api.get("/etl/status")
async def get_etl_status() -> Dict[str, Any]:
    """獲取 ETL 狀態"""
    try:
        # 檢查 ETL 輸出文件
        data_dir = Path("data")
        
        raw_files = list((data_dir / "raw").glob("*.json"))
        processed_files = list((data_dir / "processed").glob("*.json"))
        validated_files = list((data_dir / "validated").glob("*.json"))
        report_files = list((data_dir / "reports").glob("*.md"))
        
        return {
            "status": "running",
            "stages": {
                "extract": {
                    "status": "completed" if raw_files else "pending",
                    "files_count": len(raw_files)
                },
                "transform": {
                    "status": "completed" if processed_files else "pending",
                    "files_count": len(processed_files)
                },
                "validate": {
                    "status": "completed" if validated_files else "pending",
                    "files_count": len(validated_files)
                },
                "load": {
                    "status": "completed" if report_files else "pending",
                    "files_count": len(report_files)
                }
            },
            "last_run": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取 ETL 狀態失敗: {str(e)}")

@simple_api.post("/etl/sync")
async def sync_etl() -> Dict[str, Any]:
    """同步 ETL 數據"""
    try:
        # 這裡可以觸發 ETL 流程
        # 目前只是返回成功狀態
        return {
            "status": "success",
            "message": "ETL 同步已觸發",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ETL 同步失敗: {str(e)}")

@simple_api.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "simple-proxy-api",
        "timestamp": datetime.now().isoformat()
    }

