"""代理管理器資料模型

定義代理節點的資料結構、枚舉類型和相關的資料模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import json
import time


class ProxyProtocol(Enum):
    """代理協議類型"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyAnonymity(Enum):
    """代理匿名度等級"""
    ELITE = "elite"          # 高匿名
    ANONYMOUS = "anonymous"  # 匿名
    TRANSPARENT = "transparent"  # 透明
    UNKNOWN = "unknown"      # 未知


class ProxySpeed(Enum):
    """代理速度等級"""
    FAST = "fast"        # < 1000ms
    MEDIUM = "medium"    # 1000-3000ms
    SLOW = "slow"        # > 3000ms
    UNKNOWN = "unknown"  # 未測試


class ProxyStatus(Enum):
    """代理狀態"""
    ACTIVE = "active"        # 活躍可用
    INACTIVE = "inactive"    # 不可用
    TESTING = "testing"      # 測試中
    BLACKLISTED = "blacklisted"  # 黑名單


class ScanProtocol(Enum):
    """掃描協議枚舉"""
    HTTP = "http"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    HTTPS = "https"


class ScanStatus(Enum):
    """掃描狀態枚舉"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CONNECTION_REFUSED = "connection_refused"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ProxyMetrics:
    """代理性能指標"""
    response_time_ms: Optional[int] = None
    success_rate: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    
    def update_success(self, response_time_ms: int) -> None:
        """更新成功統計"""
        self.total_requests += 1
        self.successful_requests += 1
        self.response_time_ms = response_time_ms
        self.last_success_time = datetime.now()
        self.consecutive_failures = 0
        self._calculate_success_rate()
    
    def update_failure(self) -> None:
        """更新失敗統計"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure_time = datetime.now()
        self.consecutive_failures += 1
        self._calculate_success_rate()
    
    def _calculate_success_rate(self) -> None:
        """計算成功率"""
        if self.total_requests > 0:
            self.success_rate = self.successful_requests / self.total_requests


@dataclass
class ProxyNode:
    """代理節點資料模型"""
    host: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    anonymity: ProxyAnonymity = ProxyAnonymity.UNKNOWN
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    status: ProxyStatus = ProxyStatus.INACTIVE
    metrics: ProxyMetrics = field(default_factory=ProxyMetrics)
    source: Optional[str] = None  # 代理來源（json_file, manual等）
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_checked: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化後處理"""
        if not hasattr(self, 'proxy_id') or not self.proxy_id:
            self.proxy_id = f"{self.host}:{self.port}"
    
    @property
    def url(self) -> str:
        """獲取代理URL"""
        return f"{self.protocol.value}://{self.host}:{self.port}"
    
    @property
    def is_available(self) -> bool:
        """檢查代理是否可用"""
        return self.status == ProxyStatus.ACTIVE
    
    @property
    def speed_level(self) -> ProxySpeed:
        """獲取速度等級"""
        if self.metrics.response_time_ms is None:
            return ProxySpeed.UNKNOWN
        elif self.metrics.response_time_ms < 1000:
            return ProxySpeed.FAST
        elif self.metrics.response_time_ms < 3000:
            return ProxySpeed.MEDIUM
        else:
            return ProxySpeed.SLOW
    
    @property
    def score(self) -> float:
        """計算代理評分（0-100）"""
        if not self.is_available:
            return 0.0
        
        score = 0.0
        
        # 成功率權重 40%
        score += self.metrics.success_rate * 40
        
        # 速度權重 30%
        if self.metrics.response_time_ms is not None:
            if self.metrics.response_time_ms < 1000:
                score += 30
            elif self.metrics.response_time_ms < 3000:
                score += 20
            elif self.metrics.response_time_ms < 5000:
                score += 10
        
        # 匿名度權重 20%
        anonymity_scores = {
            ProxyAnonymity.ELITE: 20,
            ProxyAnonymity.ANONYMOUS: 15,
            ProxyAnonymity.TRANSPARENT: 5,
            ProxyAnonymity.UNKNOWN: 0
        }
        score += anonymity_scores.get(self.anonymity, 0)
        
        # 穩定性權重 10%（連續失敗次數的反向）
        if self.metrics.consecutive_failures == 0:
            score += 10
        elif self.metrics.consecutive_failures < 3:
            score += 5
        
        return min(score, 100.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol.value,
            "anonymity": self.anonymity.value,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "isp": self.isp,
            "status": self.status.value,
            "url": self.url,
            "score": self.score,
            "speed_level": self.speed_level.value,
            "metrics": {
                "response_time_ms": self.metrics.response_time_ms,
                "success_rate": self.metrics.success_rate,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "consecutive_failures": self.metrics.consecutive_failures
            },
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyNode':
        """從字典創建代理節點"""
        metrics = ProxyMetrics(
            response_time_ms=data.get("metrics", {}).get("response_time_ms"),
            success_rate=data.get("metrics", {}).get("success_rate", 0.0),
            total_requests=data.get("metrics", {}).get("total_requests", 0),
            successful_requests=data.get("metrics", {}).get("successful_requests", 0),
            failed_requests=data.get("metrics", {}).get("failed_requests", 0),
            consecutive_failures=data.get("metrics", {}).get("consecutive_failures", 0)
        )
        
        return cls(
            host=data["host"],
            port=data["port"],
            protocol=ProxyProtocol(data.get("protocol", "http")),
            anonymity=ProxyAnonymity(data.get("anonymity", "unknown")),
            country=data.get("country"),
            region=data.get("region"),
            city=data.get("city"),
            isp=data.get("isp"),
            status=ProxyStatus(data.get("status", "inactive")),
            metrics=metrics,
            source=data.get("source"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            last_checked=datetime.fromisoformat(data["last_checked"]) if data.get("last_checked") else None,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        return f"ProxyNode({self.url}, {self.status.value}, score={self.score:.1f})"
    
    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class ProxyFilter:
    """代理篩選條件"""
    protocols: Optional[List[ProxyProtocol]] = None
    anonymity_levels: Optional[List[ProxyAnonymity]] = None
    countries: Optional[List[str]] = None
    min_score: Optional[float] = None
    max_response_time: Optional[int] = None
    min_success_rate: Optional[float] = None
    status: Optional[List[ProxyStatus]] = None
    tags: Optional[List[str]] = None
    
    def matches(self, proxy: ProxyNode) -> bool:
        """檢查代理是否符合篩選條件"""
        if self.protocols and proxy.protocol not in self.protocols:
            return False
        
        if self.anonymity_levels and proxy.anonymity not in self.anonymity_levels:
            return False
        
        if self.countries and proxy.country not in self.countries:
            return False
        
        if self.min_score is not None and proxy.score < self.min_score:
            return False
        
        if (self.max_response_time is not None and 
            proxy.metrics.response_time_ms is not None and 
            proxy.metrics.response_time_ms > self.max_response_time):
            return False
        
        if (self.min_success_rate is not None and 
            proxy.metrics.success_rate < self.min_success_rate):
            return False
        
        if self.status and proxy.status not in self.status:
            return False
        
        if self.tags and not any(tag in proxy.tags for tag in self.tags):
            return False
        
        return True


@dataclass
class ScanTarget:
    """掃描目標"""
    host: str
    port: int
    protocols: List[ScanProtocol] = field(default_factory=lambda: [ScanProtocol.HTTP])
    priority: int = 1  # 1-10, 10為最高優先級


@dataclass
class ScanResult:
    """掃描結果"""
    target: ScanTarget
    protocol: ScanProtocol
    result: ScanStatus
    response_time: float = 0.0
    error_message: str = ""
    proxy_node: Optional[ProxyNode] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ScanConfig:
    """掃描配置"""
    # 並發控制
    max_concurrent_scans: int = 100
    max_concurrent_connections: int = 50
    
    # 超時設置
    connection_timeout: float = 5.0
    read_timeout: float = 10.0
    
    # 重試設置
    max_retries: int = 2
    retry_delay: float = 1.0
    
    # 掃描設置
    default_ports: List[int] = field(default_factory=lambda: [80, 8080, 3128, 1080])
    test_urls: List[str] = field(default_factory=lambda: [
        "http://httpbin.org/ip",
        "https://httpbin.org/ip"
    ])
    
    # 結果設置
    save_results: bool = True
    results_file: str = "scan_results.json"
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return getattr(self, key, default)