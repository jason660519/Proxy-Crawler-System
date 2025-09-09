"""Health, pools info, ETL integration, metrics summary routes."""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from .api_shared import (
    get_proxy_manager,
    HealthResponse,
    ProxyResponse,
)
from .manager import ProxyManager

router = APIRouter()

ETL_AVAILABLE = True  # 最後可動態檢查

@router.get('/api/health', response_model=HealthResponse, summary='健康檢查')
async def health_check(manager: ProxyManager = Depends(get_proxy_manager)):
    stats = manager.get_stats()
    uptime = None
    if stats['manager_stats']['start_time']:
        start_time = stats['manager_stats']['start_time']
        from datetime import datetime as dt
        uptime = (dt.now() - start_time).total_seconds()
    # TODO: 加入真正 DB / Redis 檢查呼叫
    overall = 'healthy' if stats['status']['running'] else 'degraded'
    return HealthResponse(
        status=overall,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        total_proxies=stats['pool_summary']['total_proxies'],
        active_proxies=stats['pool_summary']['total_active_proxies']
    )

@router.get('/api/pools', summary='獲取池詳細信息')
async def get_pools(manager=Depends(get_proxy_manager)):
    stats = manager.get_stats()
    return {
        'success': True,
        'data': {'pools': stats['pool_details'], 'summary': stats['pool_summary']},
        'timestamp': datetime.utcnow().isoformat()
    }

@router.post('/api/etl/sync', summary='同步代理數據到 ETL 系統')
async def sync_to_etl(pool_types: str = Query('hot,warm,cold'), manager=Depends(get_proxy_manager)):
    if not ETL_AVAILABLE:
        raise HTTPException(status_code=503, detail='ETL 系統不可用')
    parsed = [p for p in pool_types.split(',') if p in ['hot', 'warm', 'cold']]
    return {
        'message': '數據同步任務已排程（尚未實作）',
        'pool_types': parsed,
        'timestamp': datetime.utcnow().isoformat()
    }

@router.get('/api/etl/status', summary='獲取 ETL 系統狀態')
async def get_etl_status():
    if not ETL_AVAILABLE:
        return {'available': False, 'message': 'ETL 系統不可用', 'timestamp': datetime.utcnow().isoformat()}
    return {
        'available': True,
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'mock': True
    }

@router.get('/api/metrics/summary', summary='獲取系統指標摘要')
async def metrics_summary(manager=Depends(get_proxy_manager)):
    stats = manager.get_stats()
    pool_summary = stats['pool_summary']
    mgr = stats['manager_stats']
    total_requests = mgr.get('total_requests', 0)
    successful_requests = mgr.get('successful_requests', 0)
    success_rate = (successful_requests / total_requests * 100) if total_requests else 0
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'system_health': {
            'status': 'healthy' if stats['status']['running'] else 'stopped',
            'uptime_seconds': mgr.get('uptime_seconds', 0),
        },
        'proxy_metrics': {
            'total_proxies': pool_summary['total_proxies'],
            'active_proxies': pool_summary['total_active_proxies'],
        },
        'performance_metrics': {
            'success_rate': round(success_rate, 2),
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': total_requests - successful_requests,
        },
        'mock': True
    }
