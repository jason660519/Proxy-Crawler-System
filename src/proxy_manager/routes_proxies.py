"""Proxy-related routes extracted from monolithic api.py.

Provides endpoints:
- GET /api/proxy
- GET /api/proxies
- POST /api/proxies/filter
- POST /api/fetch (manual fetch trigger)

Future: batch validate, export, etc. will move here or dedicated modules.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from time import perf_counter

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends

from .api_shared import (
    ProxyResponse,
    ProxyNodeResponse,
    ProxyFilterRequest,
    get_proxy_manager,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    rate_limit_dependency,
)
from .pools import PoolType
from .models import ProxyProtocol, ProxyAnonymity, ProxyFilter

router = APIRouter()


@router.get("/api/proxy", response_model=ProxyResponse, summary="獲取單個代理", dependencies=[Depends(rate_limit_dependency)])
async def get_proxy(
    protocol: Optional[str] = Query(None),
    anonymity: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=1),
    max_response_time: Optional[int] = Query(None, gt=0),
    pool_preference: Optional[str] = Query("hot,warm,cold"),
    manager=Depends(get_proxy_manager),
):
    start = perf_counter()
    status_code = "200"
    try:
        filter_criteria = None
        if any([protocol, anonymity, country, min_score, max_response_time]):
            protocols = [ProxyProtocol(protocol)] if protocol else None
            anonymity_levels = [ProxyAnonymity(anonymity)] if anonymity else None
            countries = [country] if country else None
            filter_criteria = ProxyFilter(
                protocols=protocols,
                anonymity_levels=anonymity_levels,
                countries=countries,
                min_score=min_score,
                max_response_time=max_response_time,
            )
        pool_types = []
        if pool_preference:
            for name in pool_preference.split(','):
                n = name.strip().lower()
                if n == 'hot':
                    pool_types.append(PoolType.HOT)
                elif n == 'warm':
                    pool_types.append(PoolType.WARM)
                elif n == 'cold':
                    pool_types.append(PoolType.COLD)
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        proxy = await manager.get_proxy(filter_criteria, pool_types)
        if not proxy:
            raise HTTPException(status_code=404, detail="沒有找到符合條件的代理")
        return ProxyResponse.ok("成功獲取代理", ProxyNodeResponse.from_proxy_node(proxy).model_dump())
    except ValueError as e:
        status_code = "400"
        raise HTTPException(status_code=400, detail=f"參數錯誤: {e}")
    except Exception as e:  # noqa: BLE001
        status_code = "500"
        raise HTTPException(status_code=500, detail="內部服務器錯誤") from e
    finally:
        try:
            REQUEST_COUNT.labels(endpoint="/api/proxy", method="GET", status=status_code).inc()
            REQUEST_LATENCY.labels(endpoint="/api/proxy", method="GET", status=status_code).observe(perf_counter() - start)
        except Exception:  # noqa: BLE001
            pass


@router.get("/api/proxies", response_model=List[ProxyResponse], summary="批量獲取代理", dependencies=[Depends(rate_limit_dependency)])
async def get_proxies(
    count: int = Query(10, ge=1, le=100),
    protocol: Optional[str] = Query(None),
    anonymity: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=1),
    max_response_time: Optional[int] = Query(None, gt=0),
    pool_preference: Optional[str] = Query("hot,warm,cold"),
    manager=Depends(get_proxy_manager),
):
    try:
        filter_criteria = None
        if any([protocol, anonymity, country, min_score, max_response_time]):
            protocols = [ProxyProtocol(protocol)] if protocol else None
            anonymity_levels = [ProxyAnonymity(anonymity)] if anonymity else None
            countries = [country] if country else None
            filter_criteria = ProxyFilter(
                protocols=protocols,
                anonymity_levels=anonymity_levels,
                countries=countries,
                min_score=min_score,
                max_response_time=max_response_time,
            )
        pool_types = []
        if pool_preference:
            for name in pool_preference.split(','):
                n = name.strip().lower()
                if n == 'hot':
                    pool_types.append(PoolType.HOT)
                elif n == 'warm':
                    pool_types.append(PoolType.WARM)
                elif n == 'cold':
                    pool_types.append(PoolType.COLD)
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        proxies = await manager.get_proxies(count, filter_criteria, pool_types)
        return [
            ProxyResponse.ok("OK", ProxyNodeResponse.from_proxy_node(p).model_dump())
            for p in proxies
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"參數錯誤: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="內部服務器錯誤") from e


@router.post("/api/proxies/filter", response_model=List[ProxyResponse], summary="使用複雜條件篩選代理", dependencies=[Depends(rate_limit_dependency)])
async def filter_proxies(
    filter_request: ProxyFilterRequest,
    count: int = Query(10, ge=1, le=100),
    pool_preference: Optional[str] = Query("hot,warm,cold"),
    manager=Depends(get_proxy_manager),
):
    try:
        filter_criteria = filter_request.to_proxy_filter()
        pool_types = []
        if pool_preference:
            for name in pool_preference.split(','):
                n = name.strip().lower()
                if n == 'hot':
                    pool_types.append(PoolType.HOT)
                elif n == 'warm':
                    pool_types.append(PoolType.WARM)
                elif n == 'cold':
                    pool_types.append(PoolType.COLD)
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        proxies = await manager.get_proxies(count, filter_criteria, pool_types)
        return [
            ProxyResponse.ok("OK", ProxyNodeResponse.from_proxy_node(p).model_dump())
            for p in proxies
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"參數錯誤: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="內部服務器錯誤") from e


@router.post("/api/fetch", summary="手動獲取代理")
async def fetch_proxies(
    fetch_request: dict,  # 使用 dict 保持與舊行為兼容
    background_tasks: BackgroundTasks,
    manager=Depends(get_proxy_manager),
):
    try:
        sources = fetch_request.get("sources") if isinstance(fetch_request, dict) else None
        background_tasks.add_task(manager.fetch_proxies, sources)
        return {
            "message": "代理獲取任務已啟動",
            "sources": sources,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"獲取任務啟動失敗: {e}") from e
