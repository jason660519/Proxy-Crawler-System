"""代理模型定義

定義代理相關的數據模型和枚舉類型。
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class ProxyStatus(str, Enum):
    """代理狀態枚舉"""
    ACTIVE = "active"        # 活躍
    INACTIVE = "inactive"    # 非活躍
    FAILED = "failed"        # 失敗
    TESTING = "testing"      # 測試中
    BANNED = "banned"        # 被封禁


class ProxyType(str, Enum):
    """代理類型枚舉"""
    HTTP = "http"            # HTTP 代理
    HTTPS = "https"          # HTTPS 代理
    SOCKS4 = "socks4"        # SOCKS4 代理
    SOCKS5 = "socks5"        # SOCKS5 代理


@dataclass
class Proxy:
    """代理數據模型"""
    id: str
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    status: ProxyStatus = ProxyStatus.INACTIVE
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    provider: Optional[str] = None
    response_time: Optional[float] = None  # 響應時間（毫秒）
    success_rate: float = 0.0  # 成功率（0-1）
    last_used: Optional[datetime] = None
    last_tested: Optional[datetime] = None
    failure_count: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def url(self) -> str:
        """獲取代理 URL"""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"
    
    @property
    def is_available(self) -> bool:
        """檢查代理是否可用"""
        return self.status == ProxyStatus.ACTIVE
    
    def update_success_rate(self):
        """更新成功率"""
        if self.total_requests > 0:
            self.success_rate = self.successful_requests / self.total_requests
        else:
            self.success_rate = 0.0


# 為了向後兼容，創建別名
ProxyModel = Proxy