"""數據分析 API 模組

提供數據分析相關的 API 端點，包括指標查詢、儀表板管理、報告生成等功能。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import random

from ..core.base import BaseResponse, PaginatedResponse
from ..core.analytics import (
    Metric, MetricDataPoint, SystemOverview, AnalyticsFilter,
    MetricRequest, AnalyticsResponse, Dashboard, Report, Alert,
    MetricType, TimeRange, AggregationType, AnalyticsService
)

# 創建路由器
router = APIRouter(prefix="/api/v1/analytics", tags=["數據分析"])

# 模擬分析服務實例
class MockAnalyticsService(AnalyticsService):
    """模擬分析服務實作"""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._dashboards: Dict[str, Dashboard] = {}
        self._reports: Dict[str, Report] = {}
        self._alerts: Dict[str, Alert] = {}
        self._metric_counter = 0
        self._dashboard_counter = 0
        self._report_counter = 0
        self._alert_counter = 0
        self._initialize_sample_data()
    
    async def initialize(self) -> None:
        """初始化服務"""
        pass
    
    async def cleanup(self) -> None:
        """清理服務資源"""
        pass
    
    def _initialize_sample_data(self):
        """初始化範例資料"""
        # 建立範例指標
        metrics_data = [
            ("proxy_success_rate", "代理成功率", MetricType.GAUGE, "%"),
            ("task_completion_rate", "任務完成率", MetricType.GAUGE, "%"),
            ("response_time", "回應時間", MetricType.HISTOGRAM, "ms"),
            ("active_connections", "活躍連線數", MetricType.GAUGE, "count"),
            ("error_count", "錯誤計數", MetricType.COUNTER, "count"),
            ("cpu_usage", "CPU 使用率", MetricType.GAUGE, "%"),
            ("memory_usage", "記憶體使用率", MetricType.GAUGE, "%"),
            ("disk_usage", "磁碟使用率", MetricType.GAUGE, "%")
        ]
        
        for name, display_name, metric_type, unit in metrics_data:
            self._metric_counter += 1
            metric_id = f"metric_{self._metric_counter:03d}"
            
            # 生成範例資料點
            data_points = self._generate_sample_data_points(metric_type)
            
            metric = Metric(
                id=metric_id,
                name=name,
                display_name=display_name,
                description=f"{display_name}的監控指標",
                metric_type=metric_type,
                unit=unit,
                data_points=data_points,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self._metrics[metric_id] = metric
    
    def _generate_sample_data_points(self, metric_type: MetricType, count: int = 100) -> List[MetricDataPoint]:
        """生成範例資料點"""
        data_points = []
        base_time = datetime.now() - timedelta(hours=24)
        
        for i in range(count):
            timestamp = base_time + timedelta(minutes=i * 15)  # 每15分鐘一個點
            
            if metric_type == MetricType.GAUGE:
                value = random.uniform(0, 100)
            elif metric_type == MetricType.COUNTER:
                value = random.randint(0, 1000)
            elif metric_type == MetricType.HISTOGRAM:
                value = random.uniform(10, 500)
            else:
                value = random.uniform(0, 1)
            
            data_point = MetricDataPoint(
                timestamp=timestamp,
                value=round(value, 2),
                labels={"instance": "server-01", "environment": "production"}
            )
            
            data_points.append(data_point)
        
        return data_points
    
    async def get_system_overview(self) -> SystemOverview:
        """取得系統概覽"""
        return SystemOverview(
            total_proxies=150,
            active_proxies=128,
            proxy_success_rate=85.3,
            average_response_time=245.7,
            total_tasks=1250,
            running_tasks=23,
            completed_tasks=1180,
            failed_tasks=47,
            task_success_rate=94.4,
            system_uptime=86400 * 15,  # 15天
            cpu_usage=45.2,
            memory_usage=67.8,
            disk_usage=34.1,
            network_in=1024 * 1024 * 500,  # 500MB
            network_out=1024 * 1024 * 300,  # 300MB
            last_updated=datetime.now()
        )
    
    async def get_metric_data(self, request: MetricRequest) -> AnalyticsResponse:
        """取得指標資料"""
        # 尋找指標
        metric = None
        for m in self._metrics.values():
            if m.name == request.metric_name:
                metric = m
                break
        
        if not metric:
            raise ValueError(f"指標 {request.metric_name} 不存在")
        
        # 篩選資料點
        data_points = metric.data_points.copy()
        
        if request.filters:
            if request.filters.start_time:
                data_points = [dp for dp in data_points if dp.timestamp >= request.filters.start_time]
            if request.filters.end_time:
                data_points = [dp for dp in data_points if dp.timestamp <= request.filters.end_time]
        
        # 限制結果數量
        if request.limit:
            data_points = data_points[-request.limit:]
        
        # 計算摘要統計
        values = [dp.value for dp in data_points]
        summary = {}
        if values:
            summary = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values)
            }
        
        return AnalyticsResponse(
            metric_name=request.metric_name,
            data_points=data_points,
            summary=summary,
            metadata={"metric_type": metric.metric_type, "unit": metric.unit}
        )
    
    async def list_metrics(self, filters: Optional[AnalyticsFilter] = None) -> List[Metric]:
        """列出指標"""
        metrics = list(self._metrics.values())
        
        if filters:
            if filters.metric_names:
                metrics = [m for m in metrics if m.name in filters.metric_names]
            if filters.metric_types:
                metrics = [m for m in metrics if m.metric_type in filters.metric_types]
        
        return metrics
    
    async def create_metric(self, metric: Metric) -> Metric:
        """建立指標"""
        self._metric_counter += 1
        metric.id = f"metric_{self._metric_counter:03d}"
        metric.created_at = datetime.now()
        metric.updated_at = datetime.now()
        
        self._metrics[metric.id] = metric
        return metric
    
    async def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> Metric:
        """更新指標"""
        if metric_id not in self._metrics:
            raise ValueError(f"指標 {metric_id} 不存在")
        
        metric = self._metrics[metric_id]
        for key, value in updates.items():
            if hasattr(metric, key):
                setattr(metric, key, value)
        
        metric.updated_at = datetime.now()
        return metric
    
    async def delete_metric(self, metric_id: str) -> bool:
        """刪除指標"""
        if metric_id in self._metrics:
            del self._metrics[metric_id]
            return True
        return False
    
    async def record_metric(self, metric_name: str, value: Union[int, float], 
                          labels: Optional[Dict[str, str]] = None) -> bool:
        """記錄指標資料"""
        # 尋找指標
        metric = None
        for m in self._metrics.values():
            if m.name == metric_name:
                metric = m
                break
        
        if not metric:
            return False
        
        # 新增資料點
        data_point = MetricDataPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        
        metric.data_points.append(data_point)
        metric.last_updated = datetime.now()
        
        return True
    
    async def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        """建立儀表板"""
        self._dashboard_counter += 1
        dashboard.id = f"dashboard_{self._dashboard_counter:03d}"
        dashboard.created_at = datetime.now()
        dashboard.updated_at = datetime.now()
        
        self._dashboards[dashboard.id] = dashboard
        return dashboard
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """取得儀表板"""
        return self._dashboards.get(dashboard_id)
    
    async def list_dashboards(self) -> List[Dashboard]:
        """列出儀表板"""
        return list(self._dashboards.values())
    
    async def update_dashboard(self, dashboard_id: str, updates: Dict[str, Any]) -> Dashboard:
        """更新儀表板"""
        if dashboard_id not in self._dashboards:
            raise ValueError(f"儀表板 {dashboard_id} 不存在")
        
        dashboard = self._dashboards[dashboard_id]
        for key, value in updates.items():
            if hasattr(dashboard, key):
                setattr(dashboard, key, value)
        
        dashboard.updated_at = datetime.now()
        return dashboard
    
    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """刪除儀表板"""
        if dashboard_id in self._dashboards:
            del self._dashboards[dashboard_id]
            return True
        return False
    
    async def generate_report(self, report_id: str) -> Dict[str, Any]:
        """生成報告"""
        if report_id not in self._reports:
            raise ValueError(f"報告 {report_id} 不存在")
        
        report = self._reports[report_id]
        
        # 模擬報告生成
        report_data = {
            "report_id": report_id,
            "name": report.name,
            "generated_at": datetime.now().isoformat(),
            "data": {
                "summary": {
                    "total_metrics": len(self._metrics),
                    "total_dashboards": len(self._dashboards),
                    "system_health": "良好"
                },
                "metrics": [m.dict() for m in list(self._metrics.values())[:5]]
            }
        }
        
        return report_data
    
    async def create_report(self, report: Report) -> Report:
        """建立報告"""
        self._report_counter += 1
        report.id = f"report_{self._report_counter:03d}"
        report.created_at = datetime.now()
        report.updated_at = datetime.now()
        
        self._reports[report.id] = report
        return report
    
    async def list_reports(self) -> List[Report]:
        """列出報告"""
        return list(self._reports.values())
    
    async def create_alert(self, alert: Alert) -> Alert:
        """建立警報"""
        self._alert_counter += 1
        alert.id = f"alert_{self._alert_counter:03d}"
        alert.created_at = datetime.now()
        alert.updated_at = datetime.now()
        
        self._alerts[alert.id] = alert
        return alert
    
    async def list_alerts(self) -> List[Alert]:
        """列出警報"""
        return list(self._alerts.values())
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """檢查警報"""
        triggered_alerts = []
        
        for alert in self._alerts.values():
            if not alert.enabled:
                continue
            
            # 模擬警報檢查邏輯
            if random.random() < 0.1:  # 10% 機率觸發
                triggered_alerts.append({
                    "alert_id": alert.id,
                    "name": alert.name,
                    "severity": alert.severity,
                    "message": f"警報 {alert.name} 已觸發",
                    "triggered_at": datetime.now().isoformat()
                })
        
        return triggered_alerts


# 全域分析服務實例
analytics_service = MockAnalyticsService()


def get_analytics_service() -> AnalyticsService:
    """取得分析服務實例"""
    return analytics_service


@router.get("/overview", response_model=SystemOverview)
async def get_system_overview(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """取得系統概覽"""
    try:
        overview = await service.get_system_overview()
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得系統概覽失敗: {str(e)}")


@router.get("/metrics", response_model=BaseResponse[List[Metric]])
async def list_metrics(
    metric_type: Optional[List[MetricType]] = Query(None, description="指標類型篩選"),
    metric_name: Optional[List[str]] = Query(None, description="指標名稱篩選"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """列出所有指標"""
    try:
        filters = AnalyticsFilter(
            metric_types=metric_type,
            metric_names=metric_name
        )
        
        metrics = await service.list_metrics(filters)
        
        return BaseResponse(
            success=True,
            message="取得指標列表成功",
            data=metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得指標列表失敗: {str(e)}")


@router.post("/metrics/query", response_model=AnalyticsResponse)
async def query_metric_data(
    request: MetricRequest,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """查詢指標資料"""
    try:
        response = await service.get_metric_data(request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢指標資料失敗: {str(e)}")


@router.post("/metrics", response_model=BaseResponse[Metric])
async def create_metric(
    metric: Metric,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """建立新指標"""
    try:
        created_metric = await service.create_metric(metric)
        
        return BaseResponse(
            success=True,
            message="指標建立成功",
            data=created_metric
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立指標失敗: {str(e)}")


@router.post("/metrics/{metric_name}/record", response_model=BaseResponse[bool])
async def record_metric_data(
    metric_name: str,
    value: Union[int, float],
    labels: Optional[Dict[str, str]] = None,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """記錄指標資料"""
    try:
        success = await service.record_metric(metric_name, value, labels)
        
        return BaseResponse(
            success=success,
            message="指標資料記錄成功" if success else "指標不存在",
            data=success
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"記錄指標資料失敗: {str(e)}")


@router.get("/dashboards", response_model=BaseResponse[List[Dashboard]])
async def list_dashboards(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """列出所有儀表板"""
    try:
        dashboards = await service.list_dashboards()
        
        return BaseResponse(
            success=True,
            message="取得儀表板列表成功",
            data=dashboards
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得儀表板列表失敗: {str(e)}")


@router.post("/dashboards", response_model=BaseResponse[Dashboard])
async def create_dashboard(
    dashboard: Dashboard,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """建立新儀表板"""
    try:
        created_dashboard = await service.create_dashboard(dashboard)
        
        return BaseResponse(
            success=True,
            message="儀表板建立成功",
            data=created_dashboard
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立儀表板失敗: {str(e)}")


@router.get("/dashboards/{dashboard_id}", response_model=BaseResponse[Dashboard])
async def get_dashboard(
    dashboard_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """取得儀表板詳情"""
    try:
        dashboard = await service.get_dashboard(dashboard_id)
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="儀表板不存在")
        
        return BaseResponse(
            success=True,
            message="取得儀表板成功",
            data=dashboard
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得儀表板失敗: {str(e)}")


@router.get("/reports", response_model=BaseResponse[List[Report]])
async def list_reports(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """列出所有報告"""
    try:
        reports = await service.list_reports()
        
        return BaseResponse(
            success=True,
            message="取得報告列表成功",
            data=reports
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得報告列表失敗: {str(e)}")


@router.post("/reports", response_model=BaseResponse[Report])
async def create_report(
    report: Report,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """建立新報告"""
    try:
        created_report = await service.create_report(report)
        
        return BaseResponse(
            success=True,
            message="報告建立成功",
            data=created_report
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立報告失敗: {str(e)}")


@router.post("/reports/{report_id}/generate")
async def generate_report(
    report_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """生成報告"""
    try:
        report_data = await service.generate_report(report_id)
        
        return JSONResponse(
            content=report_data,
            headers={"Content-Type": "application/json"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成報告失敗: {str(e)}")


@router.get("/alerts", response_model=BaseResponse[List[Alert]])
async def list_alerts(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """列出所有警報"""
    try:
        alerts = await service.list_alerts()
        
        return BaseResponse(
            success=True,
            message="取得警報列表成功",
            data=alerts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得警報列表失敗: {str(e)}")


@router.post("/alerts", response_model=BaseResponse[Alert])
async def create_alert(
    alert: Alert,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """建立新警報"""
    try:
        created_alert = await service.create_alert(alert)
        
        return BaseResponse(
            success=True,
            message="警報建立成功",
            data=created_alert
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立警報失敗: {str(e)}")


@router.get("/alerts/check", response_model=BaseResponse[List[Dict[str, Any]]])
async def check_alerts(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """檢查警報狀態"""
    try:
        triggered_alerts = await service.check_alerts()
        
        return BaseResponse(
            success=True,
            message="警報檢查完成",
            data=triggered_alerts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢查警報失敗: {str(e)}")