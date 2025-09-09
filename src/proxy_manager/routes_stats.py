"""Statistics and metrics oriented routes extracted from legacy api.py."""
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException

from .api_shared import get_proxy_manager, StatsResponse, ProxyResponse

router = APIRouter()

@router.get('/api/stats', response_model=StatsResponse, summary='獲取統計信息')
async def get_stats(manager=Depends(get_proxy_manager)):
    try:
        stats = manager.get_stats()
        return StatsResponse(
            total_proxies=stats['pool_summary']['total_proxies'],
            total_active_proxies=stats['pool_summary']['total_active_proxies'],
            pool_distribution=stats['pool_summary']['pool_distribution'],
            overall_success_rate=stats['pool_summary']['overall_success_rate'],
            last_updated=stats['pool_summary']['last_updated'],
            manager_stats=stats['manager_stats'],
            pool_details=stats['pool_details']
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail='獲取統計信息失敗') from e

@router.get('/api/stats/detailed', summary='獲取詳細統計信息')
async def get_detailed_stats(manager=Depends(get_proxy_manager)):
    try:
        stats = manager.get_stats()
        return {
            'success': True,
            'data': {
                'total_proxies': stats['pool_summary']['total_proxies'],
                'total_active_proxies': stats['pool_summary']['total_active_proxies'],
                'pool_distribution': stats['pool_summary']['pool_distribution'],
                'overall_success_rate': stats['pool_summary']['overall_success_rate'],
                'last_updated': stats['pool_summary']['last_updated'],
                'manager_stats': stats['manager_stats'],
                'pool_details': stats['pool_details']
            },
            'message': '統計信息獲取成功',
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail='內部服務器錯誤') from e

@router.get('/api/metrics/trends', summary='獲取系統指標趨勢')
async def get_metrics_trends(hours: int = Query(24, ge=1, le=168), manager=Depends(get_proxy_manager)):
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        # 模擬資料（保留 TODO 標記）
        data_points = []
        current = start_time
        while current <= end_time:
            factor = (current.hour % 24) / 24
            data_points.append({
                'timestamp': current.isoformat(),
                'total_proxies': 1000 + int(150 * factor),
                'active_proxies': 900 + int(120 * factor),
                'success_rate': 80 + int(15 * factor),
                'avg_response_time_ms': 600 - int(200 * factor),
                'requests_per_hour': 800 + int(400 * factor),
                'mock': True
            })
            current += timedelta(hours=1)
        return {
            'period': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'hours': hours
            },
            'data_points': data_points,
            'summary': {
                'avg_total_proxies': sum(d['total_proxies'] for d in data_points) // len(data_points),
                'avg_active_proxies': sum(d['active_proxies'] for d in data_points) // len(data_points),
                'avg_success_rate': sum(d['success_rate'] for d in data_points) / len(data_points),
                'avg_response_time_ms': sum(d['avg_response_time_ms'] for d in data_points) / len(data_points)
            }
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail='獲取指標趨勢失敗') from e
