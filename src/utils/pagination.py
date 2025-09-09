"""分頁工具模組

提供分頁相關的參數處理和響應格式化功能。
"""

from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel, Field
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """分頁參數
    
    用於處理分頁請求的參數，包括頁碼、每頁大小等。
    """
    
    page: int = Field(default=1, ge=1, description="頁碼，從1開始")
    page_size: int = Field(default=20, ge=1, le=100, description="每頁大小，最大100")
    
    @property
    def offset(self) -> int:
        """計算偏移量
        
        Returns:
            int: 偏移量
        """
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """獲取限制數量
        
        Returns:
            int: 限制數量
        """
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """分頁響應
    
    用於格式化分頁響應數據的通用類別。
    """
    
    items: List[T] = Field(description="當前頁的數據項目")
    total: int = Field(description="總數據量")
    page: int = Field(description="當前頁碼")
    page_size: int = Field(description="每頁大小")
    total_pages: int = Field(description="總頁數")
    has_next: bool = Field(description="是否有下一頁")
    has_prev: bool = Field(description="是否有上一頁")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        pagination: PaginationParams
    ) -> 'PaginatedResponse[T]':
        """創建分頁響應
        
        Args:
            items: 當前頁的數據項目
            total: 總數據量
            pagination: 分頁參數
            
        Returns:
            PaginatedResponse[T]: 分頁響應對象
        """
        total_pages = ceil(total / pagination.page_size) if total > 0 else 0
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的分頁響應
        """
        return {
            "items": [item.dict() if hasattr(item, 'dict') else item for item in self.items],
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev
            }
        }


def paginate_list(
    items: List[T],
    pagination: PaginationParams
) -> PaginatedResponse[T]:
    """對列表進行分頁處理
    
    Args:
        items: 要分頁的項目列表
        pagination: 分頁參數
        
    Returns:
        PaginatedResponse[T]: 分頁響應
    """
    total = len(items)
    start_idx = pagination.offset
    end_idx = start_idx + pagination.page_size
    
    paginated_items = items[start_idx:end_idx]
    
    return PaginatedResponse.create(
        items=paginated_items,
        total=total,
        pagination=pagination
    )


def calculate_pagination_info(
    total: int,
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """計算分頁資訊
    
    Args:
        total: 總數據量
        page: 當前頁碼
        page_size: 每頁大小
        
    Returns:
        Dict[str, Any]: 分頁資訊字典
    """
    total_pages = ceil(total / page_size) if total > 0 else 0
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "offset": (page - 1) * page_size,
        "limit": page_size
    }