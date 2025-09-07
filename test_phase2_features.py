#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二階段功能測試

測試代理品質分析、系統監控和進階功能
"""

import asyncio
import requests
import json
from datetime import datetime
from typing import Dict, Any
import time

def test_api_endpoint(url: str, description: str) -> Dict[str, Any]:
    """測試 API 端點"""
    print(f"🔍 測試: {description}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功 - 狀態碼: {response.status_code}")
            return {"success": True, "data": data, "status_code": response.status_code}
        else:
            print(f"   ❌ 失敗 - 狀態碼: {response.status_code}")
            return {"success": False, "status_code": response.status_code, "error": response.text}
    except Exception as e:
        print(f"   ❌ 錯誤: {str(e)}")
        return {"success": False, "error": str(e)}

def test_analysis_features():
    """測試分析功能"""
    print("\n" + "="*60)
    print("🔬 測試代理品質分析功能")
    print("="*60)
    
    # 測試分析 API 健康檢查
    result = test_api_endpoint(
        "http://localhost:8000/analysis/health",
        "分析 API 健康檢查"
    )
    
    if not result["success"]:
        print("⚠️ 分析 API 不可用，跳過分析功能測試")
        return
    
    # 測試代理品質分析
    result = test_api_endpoint(
        "http://localhost:8000/analysis/quality/analyze?limit=10",
        "代理品質分析"
    )
    
    if result["success"]:
        data = result["data"]
        print(f"   📊 分析結果:")
        print(f"   - 總代理數: {data.get('analysis_report', {}).get('total_proxies', 0)}")
        print(f"   - 平均評分: {data.get('analysis_report', {}).get('average_score', 0)}")
        print(f"   - 最佳代理數: {len(data.get('top_proxies', []))}")
    
    # 測試品質統計
    result = test_api_endpoint(
        "http://localhost:8000/analysis/quality/statistics",
        "品質統計數據"
    )
    
    if result["success"]:
        data = result["data"]
        stats = data.get("statistics", {})
        print(f"   📈 統計數據:")
        print(f"   - 總分析數: {stats.get('total_analyzed', 0)}")
        print(f"   - 平均評分: {stats.get('average_score', 0)}")
        print(f"   - 評分分布: {stats.get('score_distribution', {})}")

def test_monitoring_features():
    """測試監控功能"""
    print("\n" + "="*60)
    print("📊 測試系統監控功能")
    print("="*60)
    
    # 測試監控 API 健康檢查
    result = test_api_endpoint(
        "http://localhost:8000/monitoring/health",
        "監控 API 健康檢查"
    )
    
    if not result["success"]:
        print("⚠️ 監控 API 不可用，跳過監控功能測試")
        return
    
    # 測試當前指標
    result = test_api_endpoint(
        "http://localhost:8000/monitoring/metrics/current",
        "當前系統指標"
    )
    
    if result["success"]:
        data = result["data"]
        metrics = data.get("metrics", {})
        print(f"   💻 系統指標:")
        print(f"   - CPU 使用率: {metrics.get('cpu_percent', 0):.1f}%")
        print(f"   - 記憶體使用率: {metrics.get('memory_percent', 0):.1f}%")
        print(f"   - 磁碟使用率: {metrics.get('disk_percent', 0):.1f}%")
        print(f"   - 代理數量: {metrics.get('proxy_count', 0)}")
        print(f"   - 活躍連接: {metrics.get('active_connections', 0)}")
    
    # 測試系統健康狀態
    result = test_api_endpoint(
        "http://localhost:8000/monitoring/health/status",
        "系統健康狀態"
    )
    
    if result["success"]:
        data = result["data"]
        health = data.get("health", {})
        print(f"   🏥 健康狀態:")
        print(f"   - 狀態: {health.get('status', 'unknown')}")
        print(f"   - 健康評分: {health.get('health_score', 0)}")
        print(f"   - 活躍告警: {health.get('active_alerts', 0)}")
        if health.get('issues'):
            print(f"   - 問題: {', '.join(health.get('issues', []))}")
    
    # 測試監控儀表板
    result = test_api_endpoint(
        "http://localhost:8000/monitoring/dashboard",
        "監控儀表板"
    )
    
    if result["success"]:
        data = result["data"]
        dashboard = data.get("dashboard", {})
        print(f"   📊 儀表板數據:")
        print(f"   - 當前 CPU: {dashboard.get('current_metrics', {}).get('cpu_percent', 0):.1f}%")
        print(f"   - 24小時平均 CPU: {dashboard.get('averages_24h', {}).get('cpu_percent', 0):.1f}%")
        print(f"   - 活躍告警: {dashboard.get('alerts', {}).get('active_count', 0)}")

def test_basic_apis():
    """測試基本 API"""
    print("\n" + "="*60)
    print("🔧 測試基本 API 功能")
    print("="*60)
    
    # 測試主服務健康檢查
    result = test_api_endpoint(
        "http://localhost:8000/health",
        "主服務健康檢查"
    )
    
    # 測試代理管理 API
    result = test_api_endpoint(
        "http://localhost:8000/api/proxies",
        "代理列表 API"
    )
    
    if result["success"]:
        data = result["data"]
        print(f"   📋 代理列表: {len(data)} 個代理")
    
    # 測試 ETL 狀態
    result = test_api_endpoint(
        "http://localhost:8000/etl/status",
        "ETL 狀態 API"
    )
    
    if result["success"]:
        data = result["data"]
        stages = data.get("stages", {})
        print(f"   🔄 ETL 狀態:")
        for stage, info in stages.items():
            print(f"   - {stage}: {info.get('status', 'unknown')} ({info.get('files_count', 0)} 文件)")

def main():
    """主測試函數"""
    print("🚀 第二階段功能測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 等待服務啟動
    print("\n⏳ 等待服務啟動...")
    time.sleep(5)
    
    # 測試基本 API
    test_basic_apis()
    
    # 測試分析功能
    test_analysis_features()
    
    # 測試監控功能
    test_monitoring_features()
    
    print("\n" + "="*60)
    print("✅ 第二階段功能測試完成")
    print("="*60)

if __name__ == "__main__":
    main()
