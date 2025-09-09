"""Maintenance & administrative routes: validate, cleanup, export, download, batch validate."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, BackgroundTasks, Query, HTTPException

from .api_shared import (
    get_proxy_manager,
    require_api_key,
    ProxyResponse,
)
from .pools import PoolType

router = APIRouter(dependencies=[Depends(require_api_key)])

@router.post('/api/validate', summary='手動驗證代理池')
async def validate_pools(background_tasks: BackgroundTasks, manager=Depends(get_proxy_manager)):
    try:
        background_tasks.add_task(manager.validate_pools)
        return {'message': '代理池驗證任務已啟動', 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'啟動驗證任務失敗: {e}') from e

@router.post('/api/cleanup', summary='手動清理代理池')
async def cleanup_pools(background_tasks: BackgroundTasks, manager=Depends(get_proxy_manager)):
    try:
        background_tasks.add_task(manager.cleanup_pools)
        return {'message': '代理池清理任務已啟動', 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'啟動清理任務失敗: {e}') from e

@router.post('/api/export', summary='導出代理')
async def export_proxies(export_request: dict, manager=Depends(get_proxy_manager)):
    try:
        pool_types = []
        req_types = export_request.get('pool_types') if isinstance(export_request, dict) else None
        if req_types:
            for name in req_types:
                n = name.strip().lower()
                if n == 'hot':
                    pool_types.append(PoolType.HOT)
                elif n == 'warm':
                    pool_types.append(PoolType.WARM)
                elif n == 'cold':
                    pool_types.append(PoolType.COLD)
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        fmt = (export_request.get('format_type') if isinstance(export_request, dict) else 'json') or 'json'
        filename = export_request.get('filename') if isinstance(export_request, dict) else None
        if not filename:
            filename = f"proxies_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        file_path = Path('data/exports') / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        count = await manager.export_proxies(file_path, fmt, pool_types)
        return {
            'message': '代理導出成功',
            'filename': filename,
            'format': fmt,
            'count': count,
            'download_url': f'/api/download/{filename}',
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'導出失敗: {e}') from e

@router.get('/api/download/{filename}', summary='下載導出文件')
async def download_file(filename: str):
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    if any(part in filename for part in ['..', '//', '\\']):
        raise HTTPException(status_code=400, detail='非法文件名')
    base_dir = Path('data/exports').resolve()
    file_path = (base_dir / filename).resolve()
    if not str(file_path).startswith(str(base_dir)):
        raise HTTPException(status_code=400, detail='路徑越界')
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='文件不存在')
    return FileResponse(path=str(file_path), filename=file_path.name, media_type='application/octet-stream')

@router.post('/api/batch/validate', summary='批量驗證代理')
async def batch_validate(
    pool_types: str = Query('hot,warm,cold'),
    batch_size: int = Query(100, ge=10, le=1000),
    manager=Depends(get_proxy_manager)
):
    """Execute a batch validation over selected pools returning aggregated stats."""
    try:
        selected = [p for p in (pool_types.split(',') if pool_types else []) if p in ['hot', 'warm', 'cold']]
        if not selected:
            selected = ['hot', 'warm', 'cold']
        pool_enum_map = { 'hot': PoolType.HOT, 'warm': PoolType.WARM, 'cold': PoolType.COLD }
        # Collect proxies from pools
        proxies = []
        for name in selected:
            pool = manager.pool_manager.pools.get(pool_enum_map[name])
            if not pool:
                continue
            for p in pool.proxies.values():  # include inactive for re-check
                proxies.append(p)
        if not proxies:
            return {
                'message': '選定池沒有代理',
                'pool_types': selected,
                'batch_size': batch_size,
                'totals': {'proxies': 0},
                'timestamp': datetime.utcnow().isoformat()
            }
        # Trim to batch_size if requested smaller than available
        target = proxies[:batch_size] if batch_size < len(proxies) else proxies
        results = []
        if manager.batch_validator is not None:
            results = await manager.batch_validator.validate_large_batch(target)
        else:
            # Fallback to single validator
            if manager.validator is None:
                from .validators.proxy_validator import ProxyValidator  # lazy
                manager.validator = ProxyValidator()
            results = await manager.validator.validate_proxies(target)
        total = len(results)
        status_counts = {}
        avg_latency = 0.0
        latencies = []
        anonymity_counts = {}
        geo_success = 0
        for r in results:
            status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1
            if r.response_time:
                latencies.append(r.response_time)
            if getattr(r, 'anonymity_level', None):
                anonymity_counts[r.anonymity_level.value] = anonymity_counts.get(r.anonymity_level.value, 0) + 1
            if getattr(r, 'detected_country', None):
                geo_success += 1
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
        working = status_counts.get('working', 0)
        success_rate = (working / total * 100) if total else 0
        return {
            'message': '批量驗證完成',
            'pool_types': selected,
            'batch_size': batch_size,
            'totals': {
                'proxies': len(target),
                'validated': total,
                'working': working,
                'failed': status_counts.get('failed', 0),
                'timeout': status_counts.get('timeout', 0),
                'unknown': status_counts.get('unknown', 0),
                'success_rate': round(success_rate, 2)
            },
            'metrics': {
                'avg_latency_seconds': round(avg_latency, 4),
                'anonymity_distribution': anonymity_counts,
                'geo_detection_success': geo_success,
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'批量驗證失敗: {e}') from e
