"""Shared API models, dependencies, metrics, and global state for proxy_manager API.

This module centralizes:
- Pydantic response/request models
- Dependency helpers (API key, proxy manager accessor)
- Prometheus metrics objects
- Global proxy_manager instance placeholder

Route modules should import from here to avoid circular imports.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Any, Dict, List
import asyncio
import logging

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram

from src.config.settings import settings
from .manager import ProxyManager
from .models import (
    ProxyNode,
    ProxyAnonymity,
    ProxyProtocol,
    ProxyFilter,
)
from .pools import PoolType

logger = logging.getLogger(__name__)

# ---------- Pydantic Models ----------
class ProxyResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

    @staticmethod
    def ok(message: str, data: Any = None) -> "ProxyResponse":
        return ProxyResponse(success=True, message=message, data=data)

    @staticmethod
    def fail(message: str) -> "ProxyResponse":
        return ProxyResponse(success=False, message=message, data=None)


class ProxyNodeResponse(BaseModel):
    host: str
    port: int
    protocol: str
    anonymity: str
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    score: float
    response_time_ms: Optional[int] = None
    last_checked: Optional[datetime] = None

    @classmethod
    def from_proxy_node(cls, proxy: ProxyNode) -> "ProxyNodeResponse":
        return cls(
            host=proxy.host,
            port=proxy.port,
            protocol=proxy.protocol.value,
            anonymity=proxy.anonymity.value,
            country=proxy.country,
            region=proxy.region,
            city=proxy.city,
            score=proxy.score,
            response_time_ms=proxy.metrics.response_time_ms,
            last_checked=proxy.last_checked,
        )


class ProxyFilterRequest(BaseModel):
    protocols: Optional[List[str]] = None
    anonymity_levels: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    min_score: Optional[float] = None
    max_response_time: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    order_by: str = Field(default="score")
    order_desc: bool = Field(default=True)

    @property
    def filter(self) -> ProxyFilter:
        protocols = None
        if self.protocols:
            protocols = [ProxyProtocol(p) for p in self.protocols if p in [e.value for e in ProxyProtocol]]
        anonymity_levels = None
        if self.anonymity_levels:
            anonymity_levels = [ProxyAnonymity(a) for a in self.anonymity_levels if a in [e.value for e in ProxyAnonymity]]
        return ProxyFilter(
            protocols=protocols,
            anonymity_levels=anonymity_levels,
            countries=self.countries,
            min_score=self.min_score,
            max_response_time=self.max_response_time,
        )

    def to_proxy_filter(self) -> ProxyFilter:  # backward compatibility
        return self.filter


class StatsResponse(BaseModel):
    total_proxies: int
    total_active_proxies: int
    pool_distribution: Dict[str, int]
    overall_success_rate: float
    last_updated: str
    manager_stats: Dict[str, Any]
    pool_details: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    uptime_seconds: Optional[float] = None
    total_proxies: int
    active_proxies: int
    version: str = "1.0.0"


class FetchRequest(BaseModel):
    sources: Optional[List[str]] = None
    validate: bool = True


class ExportRequest(BaseModel):
    format_type: str = Field(default="json", pattern="^(json|txt|csv)$")
    pool_types: Optional[List[str]] = None
    filename: Optional[str] = None


# ---------- Metrics ----------
REQUEST_COUNT = Counter("proxy_api_requests_total", "Total API requests", ["endpoint", "method", "status"])
POOL_ACTIVE = Gauge("proxy_pool_active", "Active proxies in pool")
POOL_TOTAL = Gauge("proxy_pool_total", "Total proxies in pool")
REQUEST_LATENCY = Histogram(
    "proxy_api_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint", "method", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
FETCH_SOURCE_COUNT = Counter(
    "proxy_fetch_source_total",
    "Fetch attempts per source and outcome",
    ["source", "outcome"],  # outcome: success|error|empty
)
VALIDATION_RESULT_COUNT = Counter(
    "proxy_validation_result_total",
    "Validation results (working vs failed)",
    ["outcome"],  # working|failed
)

# Fine-grained validation metrics (added for enhanced observability)
VALIDATION_LATENCY = Histogram(
    "proxy_validation_latency_seconds",
    "Latency of individual proxy validations",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
VALIDATION_STATUS_COUNT = Counter(
    "proxy_validation_status_total",
    "Validation status counts",
    ["status"],  # working|failed|timeout|unknown
)
VALIDATION_ANONYMITY_COUNT = Counter(
    "proxy_validation_anonymity_total",
    "Detected anonymity level counts",
    ["level"],  # elite|anonymous|transparent|unknown
)
VALIDATION_GEO_DETECT_COUNT = Counter(
    "proxy_validation_geo_detect_total",
    "Geolocation detection outcome",
    ["outcome"],  # success|failure
)

# ---------- Global State ----------
proxy_manager: Optional[ProxyManager] = None
ROLLUP_LOCK = asyncio.Lock()

# ---------- Dependencies ----------
async def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if not getattr(settings, "api_key_enabled", False):
        return
    valid_keys = getattr(settings, "api_keys", []) or []
    if not x_api_key or x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def get_proxy_manager() -> ProxyManager:
    if proxy_manager is None:
        raise HTTPException(status_code=503, detail="代理管理器未初始化")
    return proxy_manager


# ---------- Utility ----------
class RateLimiter:
    def __init__(self, max_requests: int = 300, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def hit(self, key: str):
        async with self._lock:
            from time import time
            now = int(time())
            bucket = self._buckets.get(key)
            if not bucket or now - bucket["start"] >= self.window_seconds:
                bucket = {"start": now, "count": 0}
                self._buckets[key] = bucket
            bucket["count"] += 1
            if bucket["count"] > self.max_requests:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

rate_limiter = RateLimiter()

async def rate_limit_dependency(request):  # FastAPI Request type hinted lazily
    client_ip = request.client.host if request.client else "unknown"
    await rate_limiter.hit(client_ip)

__all__ = [
    "ProxyResponse",
    "ProxyNodeResponse",
    "ProxyFilterRequest",
    "StatsResponse",
    "HealthResponse",
    "FetchRequest",
    "ExportRequest",
    "require_api_key",
    "get_proxy_manager",
    "proxy_manager",
    "REQUEST_COUNT",
    "POOL_ACTIVE",
    "POOL_TOTAL",
    "REQUEST_LATENCY",
    "FETCH_SOURCE_COUNT",
    "VALIDATION_RESULT_COUNT",
    "VALIDATION_LATENCY",
    "VALIDATION_STATUS_COUNT",
    "VALIDATION_ANONYMITY_COUNT",
    "VALIDATION_GEO_DETECT_COUNT",
    "rate_limit_dependency",
]
