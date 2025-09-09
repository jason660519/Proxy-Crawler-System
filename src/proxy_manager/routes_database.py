"""Database-related proxy routes extracted from api.py."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from .api_shared import ProxyResponse, ProxyNodeResponse
from .models import ProxyProtocol, ProxyAnonymity, ProxyFilter
from .database_service import get_database_service

router = APIRouter()

@router.post('/api/database/proxies', response_model=ProxyResponse, summary='從數據庫獲取代理')
async def get_database_proxies(
    page: int = Query(1, ge=1, description='頁碼'),
    page_size: int = Query(20, ge=1, le=100, description='每頁數量'),
    protocol: Optional[str] = Query(None, description='協議類型'),
    anonymity: Optional[str] = Query(None, description='匿名度'),
    country: Optional[str] = Query(None, description='國家代碼'),
    min_score: Optional[float] = Query(None, ge=0, le=1, description='最低分數'),
    max_response_time: Optional[int] = Query(None, gt=0, description='最大響應時間(毫秒)'),
    order_by: str = Query('score', description='排序字段'),
    order_desc: bool = Query(True, description='是否降序排列')
):
    try:
        db_service = await get_database_service()
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
                max_response_time=max_response_time
            )
        result = await db_service.get_proxies(
            filter_criteria=filter_criteria,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc
        )
        return ProxyResponse(
            success=True,
            message=f'成功獲取 {len(result.proxies)} 個代理',
            data={
                'proxies': [ProxyNodeResponse.from_proxy_node(p).dict() for p in result.proxies],
                'pagination': {
                    'page': result.page,
                    'page_size': result.page_size,
                    'total_count': result.total_count,
                    'has_next': result.has_next,
                    'has_prev': result.has_prev
                }
            }
        )
    except ValueError as e:  # noqa: BLE001
        return ProxyResponse(success=False, message=f'參數錯誤: {e}', data=None)
    except Exception as e:  # noqa: BLE001
        return ProxyResponse(success=False, message=f'從數據庫獲取代理失敗: {e}', data=None)
