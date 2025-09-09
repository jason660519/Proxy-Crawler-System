"""系統日誌 API 模組

提供系統日誌相關的 API 端點，包括日誌查詢、篩選、搜尋和匯出等功能。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import io

from ..core.base import BaseResponse, PaginatedResponse
from ..core.logs import (
    LogEntry, LogFilter, LogSearchRequest, LogExportRequest,
    LogStatistics, LogSource, LogAlert, LogStreamConfig, LogService
)

# 創建路由器
router = APIRouter(prefix="/api/v1/logs", tags=["系統日誌"])

# 模擬日誌服務實例
class MockLogService(LogService):
    """模擬日誌服務實作"""
    
    def __init__(self):
        self._logs: List[LogEntry] = []
        self._log_counter = 0
        self._generate_sample_logs()
    
    async def initialize(self) -> None:
        """初始化服務"""
        pass
    
    async def cleanup(self) -> None:
        """清理服務資源"""
        pass
    
    def _generate_sample_logs(self):
        """生成範例日誌資料"""
        import random
        
        levels = ["debug", "info", "warning", "error", "critical"]
        sources = ["proxy_manager", "task_queue", "web_scraper", "api_server", "database"]
        messages = [
            "代理連線成功",
            "任務執行完成",
            "資料庫連線逾時",
            "API 請求處理中",
            "系統記憶體使用率過高",
            "爬蟲任務啟動",
            "代理驗證失敗",
            "資料儲存成功"
        ]
        
        base_time = datetime.now() - timedelta(days=7)
        
        for i in range(100):
            self._log_counter += 1
            log_time = base_time + timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            log_entry = LogEntry(
                id=f"log_{self._log_counter:06d}",
                timestamp=log_time,
                level=random.choice(levels),
                source=random.choice(sources),
                message=random.choice(messages),
                details={"request_id": f"req_{random.randint(1000, 9999)}"},
                tags=["system", random.choice(["production", "development"])],
                created_at=log_time
            )
            
            self._logs.append(log_entry)
        
        # 按時間排序（最新的在前）
        self._logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    async def search_logs(self, request: LogSearchRequest) -> List[LogEntry]:
        """搜尋日誌"""
        logs = self._logs.copy()
        
        # 篩選邏輯
        if request.filters:
            filters = request.filters
            
            if filters.levels:
                logs = [log for log in logs if log.level in filters.levels]
            
            if filters.sources:
                logs = [log for log in logs if log.source in filters.sources]
            
            if filters.start_time:
                logs = [log for log in logs if log.timestamp >= filters.start_time]
            
            if filters.end_time:
                logs = [log for log in logs if log.timestamp <= filters.end_time]
            
            if filters.search_query:
                query = filters.search_query.lower()
                logs = [log for log in logs if query in log.message.lower()]
        
        # 分頁
        start_idx = request.skip or 0
        end_idx = start_idx + (request.limit or 50)
        
        return logs[start_idx:end_idx]
    
    async def get_log(self, log_id: str) -> Optional[LogEntry]:
        """取得單一日誌"""
        for log in self._logs:
            if log.id == log_id:
                return log
        return None
    
    async def get_statistics(self, filters: Optional[LogFilter] = None) -> LogStatistics:
        """取得日誌統計"""
        logs = self._logs
        
        if filters:
            if filters.start_time:
                logs = [log for log in logs if log.timestamp >= filters.start_time]
            if filters.end_time:
                logs = [log for log in logs if log.timestamp <= filters.end_time]
        
        level_counts = {}
        source_counts = {}
        
        for log in logs:
            level_counts[log.level] = level_counts.get(log.level, 0) + 1
            source_counts[log.source] = source_counts.get(log.source, 0) + 1
        
        return LogStatistics(
            total_logs=len(logs),
            error_count=level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0),
            warning_count=level_counts.get("WARNING", 0),
            info_count=level_counts.get("INFO", 0),
            debug_count=level_counts.get("DEBUG", 0),
            level_distribution=level_counts,
            source_distribution=source_counts,
            last_updated=datetime.now()
        )
    
    async def export_logs(self, request: LogExportRequest) -> bytes:
        """匯出日誌"""
        # 搜尋日誌
        search_request = LogSearchRequest(
            filters=request.filters,
            skip=0,
            limit=request.limit or 10000
        )
        
        logs = await self.search_logs(search_request)
        
        if request.format == "json":
            data = [log.dict() for log in logs]
            return json.dumps(data, ensure_ascii=False, indent=2, default=str).encode('utf-8')
        
        elif request.format == "csv":
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 寫入標題
            writer.writerow(["ID", "時間戳", "等級", "來源", "訊息", "標籤"])
            
            # 寫入資料
            for log in logs:
                writer.writerow([
                    log.id,
                    log.timestamp.isoformat(),
                    log.level,
                    log.source,
                    log.message,
                    ",".join(log.tags)
                ])
            
            return output.getvalue().encode('utf-8')
        
        else:
            raise ValueError(f"不支援的匯出格式: {request.format}")
    
    async def get_sources(self) -> List[LogSource]:
        """取得日誌來源列表"""
        sources = set(log.source for log in self._logs)
        return [
            LogSource(
                name=source,
                display_name=source.replace("_", " ").title(),
                description=f"{source} 模組的日誌",
                enabled=True
            )
            for source in sources
        ]


# 全域日誌服務實例
log_service = MockLogService()


def get_log_service() -> LogService:
    """取得日誌服務實例"""
    return log_service


@router.get("/", response_model=PaginatedResponse[LogEntry])
async def search_logs(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(50, ge=1, le=1000, description="每頁數量"),
    level: Optional[List[str]] = Query(None, description="日誌等級篩選"),
    source: Optional[List[str]] = Query(None, description="日誌來源篩選"),
    start_time: Optional[datetime] = Query(None, description="開始時間"),
    end_time: Optional[datetime] = Query(None, description="結束時間"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    service: LogService = Depends(get_log_service)
):
    """搜尋系統日誌
    
    支援多種篩選條件和分頁功能。
    """
    try:
        # 建立篩選器
        filters = LogFilter(
            levels=level,
            sources=source,
            start_time=start_time,
            end_time=end_time,
            search_query=search
        )
        
        # 建立搜尋請求
        search_request = LogSearchRequest(
            filters=filters,
            skip=(page - 1) * page_size,
            limit=page_size
        )
        
        # 執行搜尋
        logs = await service.search_logs(search_request)
        
        # 取得總數（簡化實作）
        total = len(logs) + search_request.skip
        
        return PaginatedResponse(
            items=logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜尋日誌失敗: {str(e)}")


@router.get("/statistics", response_model=LogStatistics)
async def get_log_statistics(
    start_time: Optional[datetime] = Query(None, description="開始時間"),
    end_time: Optional[datetime] = Query(None, description="結束時間"),
    service: LogService = Depends(get_log_service)
):
    """取得日誌統計資訊"""
    try:
        filters = LogFilter(
            start_time=start_time,
            end_time=end_time
        )
        
        statistics = await service.get_statistics(filters)
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得日誌統計失敗: {str(e)}")


@router.get("/sources", response_model=BaseResponse[List[LogSource]])
async def get_log_sources(
    service: LogService = Depends(get_log_service)
):
    """取得日誌來源列表"""
    try:
        sources = await service.get_sources()
        
        return BaseResponse(
            success=True,
            message="取得日誌來源成功",
            data=sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得日誌來源失敗: {str(e)}")


@router.get("/{log_id}", response_model=BaseResponse[LogEntry])
async def get_log(
    log_id: str,
    service: LogService = Depends(get_log_service)
):
    """取得單一日誌詳情"""
    try:
        log = await service.get_log(log_id)
        
        if not log:
            raise HTTPException(status_code=404, detail="日誌不存在")
        
        return BaseResponse(
            success=True,
            message="取得日誌成功",
            data=log
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得日誌失敗: {str(e)}")


@router.post("/export")
async def export_logs(
    request: LogExportRequest,
    service: LogService = Depends(get_log_service)
):
    """匯出日誌
    
    支援 JSON 和 CSV 格式匯出。
    """
    try:
        # 匯出日誌
        data = await service.export_logs(request)
        
        # 設定檔案名稱和 MIME 類型
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if request.format == "json":
            filename = f"logs_{timestamp}.json"
            media_type = "application/json"
        elif request.format == "csv":
            filename = f"logs_{timestamp}.csv"
            media_type = "text/csv"
        else:
            raise HTTPException(status_code=400, detail="不支援的匯出格式")
        
        # 建立串流回應
        def generate():
            yield data
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出日誌失敗: {str(e)}")


@router.post("/search", response_model=PaginatedResponse[LogEntry])
async def advanced_search(
    request: LogSearchRequest,
    service: LogService = Depends(get_log_service)
):
    """進階日誌搜尋
    
    支援複雜的篩選條件和搜尋邏輯。
    """
    try:
        logs = await service.search_logs(request)
        
        # 計算分頁資訊
        page_size = request.limit or 50
        page = (request.skip or 0) // page_size + 1
        total = len(logs) + (request.skip or 0)
        
        return PaginatedResponse(
            items=logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"進階搜尋失敗: {str(e)}")


@router.get("/levels/distribution", response_model=BaseResponse[Dict[str, int]])
async def get_level_distribution(
    start_time: Optional[datetime] = Query(None, description="開始時間"),
    end_time: Optional[datetime] = Query(None, description="結束時間"),
    service: LogService = Depends(get_log_service)
):
    """取得日誌等級分佈"""
    try:
        filters = LogFilter(
            start_time=start_time,
            end_time=end_time
        )
        
        statistics = await service.get_statistics(filters)
        
        return BaseResponse(
            success=True,
            message="取得日誌等級分佈成功",
            data=statistics.level_distribution
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得日誌等級分佈失敗: {str(e)}")


@router.get("/sources/distribution", response_model=BaseResponse[Dict[str, int]])
async def get_source_distribution(
    start_time: Optional[datetime] = Query(None, description="開始時間"),
    end_time: Optional[datetime] = Query(None, description="結束時間"),
    service: LogService = Depends(get_log_service)
):
    """取得日誌來源分佈"""
    try:
        filters = LogFilter(
            start_time=start_time,
            end_time=end_time
        )
        
        statistics = await service.get_statistics(filters)
        
        return BaseResponse(
            success=True,
            message="取得日誌來源分佈成功",
            data=statistics.source_distribution
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得日誌來源分佈失敗: {str(e)}")


@router.get("/recent", response_model=BaseResponse[List[LogEntry]])
async def get_recent_logs(
    limit: int = Query(10, ge=1, le=100, description="數量限制"),
    level: Optional[str] = Query(None, description="日誌等級篩選"),
    service: LogService = Depends(get_log_service)
):
    """取得最近的日誌"""
    try:
        filters = LogFilter(levels=[level] if level else None)
        
        search_request = LogSearchRequest(
            filters=filters,
            skip=0,
            limit=limit
        )
        
        logs = await service.search_logs(search_request)
        
        return BaseResponse(
            success=True,
            message="取得最近日誌成功",
            data=logs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得最近日誌失敗: {str(e)}")