"""核心基礎類別和介面定義

這個模組定義了系統中使用的基礎類別、介面和共用功能。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseEntity(BaseModel):
    """基礎實體類別
    
    所有資料實體的基礎類別，提供共用的欄位和方法。
    """
    id: str = Field(..., description="唯一識別碼")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")
    
    class Config:
        """Pydantic 配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StatusEnum(str, Enum):
    """狀態列舉基礎類別"""
    pass


class TaskStatus(StatusEnum):
    """任務狀態列舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任務優先級列舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class LogLevel(str, Enum):
    """日誌等級列舉"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BaseResponse(BaseModel, Generic[T]):
    """API 回應基礎類別"""
    success: bool = Field(..., description="操作是否成功")
    message: Optional[str] = Field(None, description="回應訊息")
    timestamp: datetime = Field(default_factory=datetime.now, description="回應時間")
    data: Optional[T] = Field(None, description="回應資料")
    
    class Config:
        """Pydantic 配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(BaseResponse, Generic[T]):
    """分頁回應類別"""
    data: List[T] = Field(default_factory=list, description="資料列表")
    total: int = Field(0, description="總筆數")
    page: int = Field(1, description="當前頁數")
    page_size: int = Field(10, description="每頁筆數")
    total_pages: int = Field(0, description="總頁數")
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.total > 0 and self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size


class BaseFilter(BaseModel):
    """基礎篩選器類別"""
    page: int = Field(1, ge=1, description="頁數")
    page_size: int = Field(10, ge=1, le=100, description="每頁筆數")
    sort_by: Optional[str] = Field(None, description="排序欄位")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="排序方向")
    search: Optional[str] = Field(None, description="搜尋關鍵字")


class BaseService(ABC):
    """基礎服務類別
    
    所有服務類別的抽象基礎類別。
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服務"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理服務資源"""
        pass


class BaseRepository(ABC):
    """基礎資料存取類別
    
    所有資料存取類別的抽象基礎類別。
    """
    
    @abstractmethod
    async def create(self, entity: BaseEntity) -> BaseEntity:
        """建立實體"""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[BaseEntity]:
        """根據 ID 取得實體"""
        pass
    
    @abstractmethod
    async def update(self, entity: BaseEntity) -> BaseEntity:
        """更新實體"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """刪除實體"""
        pass
    
    @abstractmethod
    async def list(self, filters: BaseFilter) -> PaginatedResponse:
        """列出實體"""
        pass


class ConfigurationError(Exception):
    """配置錯誤異常"""
    pass


class ValidationError(Exception):
    """驗證錯誤異常"""
    pass


class ServiceError(Exception):
    """服務錯誤異常"""
    pass


class DatabaseError(Exception):
    """資料庫錯誤異常"""
    pass