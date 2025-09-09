"""代理管理 API 模組

提供代理節點的完整管理功能，包括：
- 代理列表查詢與篩選
- 代理狀態管理
- 批量操作
- 代理測試與驗證
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
from ..core.proxy_manager import ProxyManager
from ..models.proxy import ProxyNode, ProxyStatus, ProxyProtocol, AnonymityLevel
from ..utils.pagination import PaginationParams, PaginatedResponse
from ..utils.validation import validate_proxy_format
from ..utils.logging import get_logger

# ============= 路由器設定 =============

router = APIRouter(prefix="/api/proxy-management", tags=["代理管理"])
logger = get_logger(__name__)

# ============= 請求模型 =============

class ProxyFilters(BaseModel):
    """代理篩選參數"""
    status: Optional[List[ProxyStatus]] = Field(None, description="狀態篩選")
    protocol: Optional[List[ProxyProtocol]] = Field(None, description="協議篩選")
    country: Optional[List[str]] = Field(None, description="國家篩選")
    anonymity: Optional[List[AnonymityLevel]] = Field(None, description="匿名等級篩選")
    search: Optional[str] = Field(None, description="搜尋關鍵字")
    min_speed: Optional[float] = Field(None, ge=0, description="最小響應速度 (ms)")
    max_speed: Optional[float] = Field(None, ge=0, description="最大響應速度 (ms)")
    min_uptime: Optional[float] = Field(None, ge=0, le=100, description="最小正常運行時間 (%)")
    last_checked_hours: Optional[int] = Field(None, ge=1, description="最近檢查時間 (小時內)")

class ProxyCreateRequest(BaseModel):
    """新增代理請求"""
    ip: str = Field(..., description="IP 地址")
    port: int = Field(..., ge=1, le=65535, description="端口號")
    protocol: ProxyProtocol = Field(..., description="協議類型")
    username: Optional[str] = Field(None, description="用戶名")
    password: Optional[str] = Field(None, description="密碼")
    country: Optional[str] = Field(None, description="國家")
    city: Optional[str] = Field(None, description="城市")
    anonymity: Optional[AnonymityLevel] = Field(AnonymityLevel.UNKNOWN, description="匿名等級")
    source: Optional[str] = Field(None, description="來源")
    tags: Optional[List[str]] = Field(default_factory=list, description="標籤")

class ProxyUpdateRequest(BaseModel):
    """更新代理請求"""
    status: Optional[ProxyStatus] = Field(None, description="狀態")
    country: Optional[str] = Field(None, description="國家")
    city: Optional[str] = Field(None, description="城市")
    anonymity: Optional[AnonymityLevel] = Field(None, description="匿名等級")
    tags: Optional[List[str]] = Field(None, description="標籤")
    notes: Optional[str] = Field(None, description="備註")

class ProxyBatchOperation(BaseModel):
    """批量操作請求"""
    operation: str = Field(..., description="操作類型: test, delete, export, tag, enable, disable")
    proxy_ids: List[str] = Field(..., min_items=1, description="代理 ID 列表")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作選項")

class ProxyTestRequest(BaseModel):
    """代理測試請求"""
    proxy_ids: List[str] = Field(..., min_items=1, description="要測試的代理 ID 列表")
    test_url: Optional[str] = Field("http://httpbin.org/ip", description="測試 URL")
    timeout: Optional[int] = Field(10, ge=1, le=60, description="超時時間 (秒)")
    concurrent: Optional[int] = Field(5, ge=1, le=20, description="並發數量")

# ============= 回應模型 =============

class ProxyResponse(BaseModel):
    """代理回應模型"""
    id: str
    ip: str
    port: int
    protocol: ProxyProtocol
    country: Optional[str]
    country_code: Optional[str]
    city: Optional[str]
    anonymity: AnonymityLevel
    status: ProxyStatus
    response_time: Optional[float]
    last_checked: Optional[datetime]
    uptime: Optional[float]
    success_rate: Optional[float]
    total_requests: Optional[int]
    failed_requests: Optional[int]
    source: Optional[str]
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class ProxyTestResult(BaseModel):
    """代理測試結果"""
    proxy_id: str
    success: bool
    response_time: Optional[float]
    error: Optional[str]
    test_url: str
    tested_at: datetime

class BatchOperationResult(BaseModel):
    """批量操作結果"""
    success: bool
    total: int
    processed: int
    failed: int
    errors: List[str]
    results: Optional[List[Dict[str, Any]]]
    message: str

class ProxyStatistics(BaseModel):
    """代理統計信息"""
    total: int
    active: int
    inactive: int
    testing: int
    error: int
    by_protocol: Dict[str, int]
    by_country: Dict[str, int]
    by_anonymity: Dict[str, int]
    average_response_time: Optional[float]
    average_uptime: Optional[float]
    last_updated: datetime

# ============= 依賴注入 =============

async def get_proxy_manager() -> ProxyManager:
    """獲取代理管理器實例"""
    # 這裡應該從應用程式上下文中獲取代理管理器
    # 暫時返回一個模擬實例
    return ProxyManager()

# ============= API 端點 =============

@router.get("/proxies", response_model=PaginatedResponse[ProxyResponse])
async def get_proxies(
    pagination: PaginationParams = Depends(),
    filters: ProxyFilters = Depends(),
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """獲取代理列表
    
    支援分頁、排序和多種篩選條件
    """
    try:
        logger.info(f"獲取代理列表，分頁: {pagination}, 篩選: {filters}")
        
        # 構建查詢條件
        query_params = {
            "status": filters.status,
            "protocol": filters.protocol,
            "country": filters.country,
            "anonymity": filters.anonymity,
            "search": filters.search,
            "min_speed": filters.min_speed,
            "max_speed": filters.max_speed,
            "min_uptime": filters.min_uptime,
            "last_checked_hours": filters.last_checked_hours
        }
        
        # 移除 None 值
        query_params = {k: v for k, v in query_params.items() if v is not None}
        
        # 執行查詢
        result = await proxy_manager.get_proxies_paginated(
            page=pagination.page,
            size=pagination.size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            **query_params
        )
        
        return PaginatedResponse(
            data=[ProxyResponse.from_orm(proxy) for proxy in result.data],
            pagination=result.pagination,
            success=True,
            message="代理列表獲取成功"
        )
        
    except Exception as e:
        logger.error(f"獲取代理列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取代理列表失敗: {str(e)}")

@router.get("/proxies/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: str,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """獲取單個代理詳情"""
    try:
        proxy = await proxy_manager.get_proxy_by_id(proxy_id)
        if not proxy:
            raise HTTPException(status_code=404, detail="代理不存在")
        
        return ProxyResponse.from_orm(proxy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取代理詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取代理詳情失敗: {str(e)}")

@router.post("/proxies", response_model=ProxyResponse)
async def create_proxy(
    request: ProxyCreateRequest,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """新增代理"""
    try:
        # 驗證代理格式
        if not validate_proxy_format(request.ip, request.port):
            raise HTTPException(status_code=400, detail="無效的代理格式")
        
        # 檢查是否已存在
        existing = await proxy_manager.get_proxy_by_address(request.ip, request.port)
        if existing:
            raise HTTPException(status_code=409, detail="代理已存在")
        
        # 建立代理
        proxy_data = request.dict()
        proxy = await proxy_manager.create_proxy(proxy_data)
        
        logger.info(f"新增代理成功: {request.ip}:{request.port}")
        return ProxyResponse.from_orm(proxy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"新增代理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"新增代理失敗: {str(e)}")

@router.put("/proxies/{proxy_id}", response_model=ProxyResponse)
async def update_proxy(
    proxy_id: str,
    request: ProxyUpdateRequest,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """更新代理信息"""
    try:
        # 檢查代理是否存在
        existing = await proxy_manager.get_proxy_by_id(proxy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="代理不存在")
        
        # 更新代理
        update_data = request.dict(exclude_unset=True)
        proxy = await proxy_manager.update_proxy(proxy_id, update_data)
        
        logger.info(f"更新代理成功: {proxy_id}")
        return ProxyResponse.from_orm(proxy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新代理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新代理失敗: {str(e)}")

@router.delete("/proxies/{proxy_id}")
async def delete_proxy(
    proxy_id: str,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """刪除代理"""
    try:
        # 檢查代理是否存在
        existing = await proxy_manager.get_proxy_by_id(proxy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="代理不存在")
        
        # 刪除代理
        await proxy_manager.delete_proxy(proxy_id)
        
        logger.info(f"刪除代理成功: {proxy_id}")
        return {"success": True, "message": "代理刪除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除代理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刪除代理失敗: {str(e)}")

@router.post("/proxies/test", response_model=List[ProxyTestResult])
async def test_proxies(
    request: ProxyTestRequest,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """測試代理連通性"""
    try:
        logger.info(f"開始測試 {len(request.proxy_ids)} 個代理")
        
        # 執行代理測試
        results = await proxy_manager.test_proxies(
            proxy_ids=request.proxy_ids,
            test_url=request.test_url,
            timeout=request.timeout,
            concurrent=request.concurrent
        )
        
        # 轉換結果格式
        test_results = [
            ProxyTestResult(
                proxy_id=result["proxy_id"],
                success=result["success"],
                response_time=result.get("response_time"),
                error=result.get("error"),
                test_url=request.test_url,
                tested_at=datetime.now()
            )
            for result in results
        ]
        
        logger.info(f"代理測試完成，成功: {sum(1 for r in test_results if r.success)}")
        return test_results
        
    except Exception as e:
        logger.error(f"代理測試失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"代理測試失敗: {str(e)}")

@router.post("/proxies/batch", response_model=BatchOperationResult)
async def batch_operation(
    request: ProxyBatchOperation,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """批量操作代理"""
    try:
        logger.info(f"執行批量操作: {request.operation}，影響 {len(request.proxy_ids)} 個代理")
        
        # 執行批量操作
        result = await proxy_manager.batch_operation(
            operation=request.operation,
            proxy_ids=request.proxy_ids,
            options=request.options
        )
        
        return BatchOperationResult(
            success=result["success"],
            total=len(request.proxy_ids),
            processed=result["processed"],
            failed=result["failed"],
            errors=result.get("errors", []),
            results=result.get("results"),
            message=result["message"]
        )
        
    except Exception as e:
        logger.error(f"批量操作失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量操作失敗: {str(e)}")

@router.get("/statistics", response_model=ProxyStatistics)
async def get_proxy_statistics(
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """獲取代理統計信息"""
    try:
        stats = await proxy_manager.get_statistics()
        
        return ProxyStatistics(
            total=stats["total"],
            active=stats["active"],
            inactive=stats["inactive"],
            testing=stats["testing"],
            error=stats["error"],
            by_protocol=stats["by_protocol"],
            by_country=stats["by_country"],
            by_anonymity=stats["by_anonymity"],
            average_response_time=stats.get("average_response_time"),
            average_uptime=stats.get("average_uptime"),
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"獲取代理統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取代理統計失敗: {str(e)}")

@router.get("/countries")
async def get_available_countries(
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """獲取可用國家列表"""
    try:
        countries = await proxy_manager.get_available_countries()
        return {"countries": countries}
        
    except Exception as e:
        logger.error(f"獲取國家列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取國家列表失敗: {str(e)}")

@router.post("/import")
async def import_proxies(
    file_content: str,
    file_format: str = Query("txt", description="文件格式: txt, csv, json"),
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """批量導入代理"""
    try:
        logger.info(f"開始導入代理，格式: {file_format}")
        
        # 解析代理數據
        result = await proxy_manager.import_proxies(file_content, file_format)
        
        return {
            "success": True,
            "imported": result["imported"],
            "failed": result["failed"],
            "errors": result.get("errors", []),
            "message": f"成功導入 {result['imported']} 個代理"
        }
        
    except Exception as e:
        logger.error(f"導入代理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"導入代理失敗: {str(e)}")

@router.get("/export")
async def export_proxies(
    format: str = Query("txt", description="導出格式: txt, csv, json"),
    filters: ProxyFilters = Depends(),
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
):
    """導出代理列表"""
    try:
        logger.info(f"導出代理列表，格式: {format}")
        
        # 獲取符合條件的代理
        query_params = {k: v for k, v in filters.dict().items() if v is not None}
        proxies = await proxy_manager.get_proxies_for_export(**query_params)
        
        # 導出數據
        export_data = await proxy_manager.export_proxies(proxies, format)
        
        return {
            "success": True,
            "data": export_data,
            "count": len(proxies),
            "format": format
        }
        
    except Exception as e:
        logger.error(f"導出代理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"導出代理失敗: {str(e)}")