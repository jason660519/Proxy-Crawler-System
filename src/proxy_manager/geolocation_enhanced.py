"""增強地理位置檢測模組

提供精確的代理地理位置檢測功能：
- 多數據源地理位置查詢
- IP 地址歸屬分析
- 地理位置智能路由
- 延遲和距離計算
"""

import asyncio
import aiohttp
import json
import math
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sqlite3
try:
    import geoip2.database
    import geoip2.errors
    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

from .models import ProxyNode, ProxyStatus
from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class GeolocationInfo:
    """地理位置信息"""
    ip: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    organization: Optional[str] = None
    asn: Optional[str] = None
    asn_name: Optional[str] = None
    accuracy_radius: Optional[int] = None
    confidence: float = 0.0
    source: str = "unknown"
    query_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "ip": self.ip,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "isp": self.isp,
            "organization": self.organization,
            "asn": self.asn,
            "asn_name": self.asn_name,
            "accuracy_radius": self.accuracy_radius,
            "confidence": self.confidence,
            "source": self.source,
            "query_time": self.query_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeolocationInfo':
        """從字典創建"""
        data = data.copy()
        if 'query_time' in data and isinstance(data['query_time'], str):
            data['query_time'] = datetime.fromisoformat(data['query_time'])
        return cls(**data)


@dataclass
class ProximityInfo:
    """距離信息"""
    target_location: Tuple[float, float]  # (lat, lon)
    proxy_location: Tuple[float, float]   # (lat, lon)
    distance_km: float
    estimated_latency_ms: float
    routing_score: float  # 0-100, 越高越好


class GeolocationCache:
    """地理位置緩存"""
    
    def __init__(self, cache_file: str = "geolocation_cache.db"):
        self.cache_file = Path(cache_file)
        self.cache_duration = timedelta(days=30)  # 緩存30天
        self._init_cache()
    
    def _init_cache(self):
        """初始化緩存數據庫"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.cache_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS geolocation_cache (
                    ip TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_geolocation_updated_at 
                ON geolocation_cache(updated_at)
            """)
    
    async def get(self, ip: str) -> Optional[GeolocationInfo]:
        """從緩存獲取地理位置信息"""
        try:
            with sqlite3.connect(self.cache_file) as conn:
                cursor = conn.execute(
                    "SELECT data, updated_at FROM geolocation_cache WHERE ip = ?",
                    (ip,)
                )
                row = cursor.fetchone()
                
                if row:
                    data_json, updated_at = row
                    updated_time = datetime.fromisoformat(updated_at)
                    
                    # 檢查是否過期
                    if datetime.now() - updated_time < self.cache_duration:
                        data = json.loads(data_json)
                        return GeolocationInfo.from_dict(data)
                    else:
                        # 刪除過期記錄
                        conn.execute("DELETE FROM geolocation_cache WHERE ip = ?", (ip,))
                        
        except Exception as e:
            logger.error(f"緩存讀取失敗: {e}")
        
        return None
    
    async def set(self, ip: str, info: GeolocationInfo):
        """設置緩存"""
        try:
            with sqlite3.connect(self.cache_file) as conn:
                data_json = json.dumps(info.to_dict())
                conn.execute("""
                    INSERT OR REPLACE INTO geolocation_cache (ip, data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (ip, data_json))
                
        except Exception as e:
            logger.error(f"緩存寫入失敗: {e}")
    
    async def cleanup_expired(self):
        """清理過期緩存"""
        try:
            cutoff_time = datetime.now() - self.cache_duration
            with sqlite3.connect(self.cache_file) as conn:
                cursor = conn.execute(
                    "DELETE FROM geolocation_cache WHERE updated_at < ?",
                    (cutoff_time.isoformat(),)
                )
                deleted_count = cursor.rowcount
                logger.info(f"清理了 {deleted_count} 條過期緩存記錄")
                
        except Exception as e:
            logger.error(f"緩存清理失敗: {e}")


class EnhancedGeolocationDetector:
    """增強地理位置檢測器
    
    支援多種數據源的地理位置檢測
    """
    
    def __init__(self):
        self.config = get_config()
        self.cache = GeolocationCache()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # GeoIP 數據庫路徑
        self.geoip_db_path = Path("data/GeoLite2-City.mmdb")
        self.geoip_asn_db_path = Path("data/GeoLite2-ASN.mmdb")
        
        # API 限制
        self.api_limits = {
            "ipapi": {"requests_per_minute": 1000, "last_request": 0, "request_count": 0},
            "ipinfo": {"requests_per_minute": 1000, "last_request": 0, "request_count": 0},
            "ipgeolocation": {"requests_per_minute": 1000, "last_request": 0, "request_count": 0}
        }
        
        # 地理編碼器
        self.geocoder = Nominatim(user_agent="proxy-manager")
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "ProxyManager/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def detect_location(self, ip: str, use_cache: bool = True) -> Optional[GeolocationInfo]:
        """檢測 IP 地址的地理位置
        
        Args:
            ip: IP 地址
            use_cache: 是否使用緩存
            
        Returns:
            地理位置信息
        """
        # 檢查緩存
        if use_cache:
            cached_info = await self.cache.get(ip)
            if cached_info:
                logger.debug(f"從緩存獲取 {ip} 的地理位置信息")
                return cached_info
        
        # 嘗試多種檢測方法
        detection_methods = [
            self._detect_with_geoip,
            self._detect_with_ipapi,
            self._detect_with_ipinfo,
            self._detect_with_ipgeolocation
        ]
        
        best_info = None
        best_confidence = 0.0
        
        for method in detection_methods:
            try:
                info = await method(ip)
                if info and info.confidence > best_confidence:
                    best_info = info
                    best_confidence = info.confidence
                    
                    # 如果置信度足夠高，直接使用
                    if best_confidence >= 0.8:
                        break
                        
            except Exception as e:
                logger.debug(f"地理位置檢測方法失敗: {method.__name__} - {e}")
                continue
        
        # 緩存結果
        if best_info and use_cache:
            await self.cache.set(ip, best_info)
        
        return best_info
    
    async def _detect_with_geoip(self, ip: str) -> Optional[GeolocationInfo]:
        """使用 GeoIP 數據庫檢測"""
        if not self.geoip_db_path.exists():
            logger.debug("GeoIP 數據庫不存在")
            return None
        
        if not GEOIP2_AVAILABLE:
            logger.warning("⚠️ GeoIP2 不可用，跳過地理位置檢測")
            return None
            
        try:
            with geoip2.database.Reader(str(self.geoip_db_path)) as reader:
                response = reader.city(ip)
                
                # 獲取 ASN 信息
                asn = None
                asn_name = None
                if self.geoip_asn_db_path.exists():
                    if GEOIP2_AVAILABLE:
                        try:
                            with geoip2.database.Reader(str(self.geoip_asn_db_path)) as asn_reader:
                                asn_response = asn_reader.asn(ip)
                                asn = f"AS{asn_response.autonomous_system_number}"
                                asn_name = asn_response.autonomous_system_organization
                        except geoip2.errors.AddressNotFoundError:
                            pass
                
                return GeolocationInfo(
                    ip=ip,
                    country=response.country.name,
                    country_code=response.country.iso_code,
                    region=response.subdivisions.most_specific.name,
                    city=response.city.name,
                    latitude=float(response.location.latitude) if response.location.latitude else None,
                    longitude=float(response.location.longitude) if response.location.longitude else None,
                    timezone=response.location.time_zone,
                    accuracy_radius=response.location.accuracy_radius,
                    asn=asn,
                    asn_name=asn_name,
                    confidence=0.7,  # GeoIP 數據庫置信度中等
                    source="geoip"
                )
                
        except Exception as e:
            if GEOIP2_AVAILABLE and hasattr(e, '__class__') and 'AddressNotFoundError' in str(e.__class__):
                logger.debug(f"GeoIP 數據庫中未找到 {ip}")
            else:
                logger.error(f"GeoIP 檢測失敗: {e}")
        
        return None
    
    async def _detect_with_ipapi(self, ip: str) -> Optional[GeolocationInfo]:
        """使用 ip-api.com 檢測"""
        if not await self._check_rate_limit("ipapi"):
            return None
        
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,query"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "success":
                        # 解析 ASN
                        as_info = data.get("as", "")
                        asn = None
                        asn_name = None
                        if as_info:
                            parts = as_info.split(" ", 1)
                            if len(parts) >= 1:
                                asn = parts[0]
                            if len(parts) >= 2:
                                asn_name = parts[1]
                        
                        return GeolocationInfo(
                            ip=ip,
                            country=data.get("country"),
                            country_code=data.get("countryCode"),
                            region=data.get("regionName"),
                            city=data.get("city"),
                            latitude=data.get("lat"),
                            longitude=data.get("lon"),
                            timezone=data.get("timezone"),
                            isp=data.get("isp"),
                            organization=data.get("org"),
                            asn=asn,
                            asn_name=asn_name,
                            confidence=0.8,  # ip-api 置信度較高
                            source="ipapi"
                        )
                    else:
                        logger.debug(f"ip-api 查詢失敗: {data.get('message')}")
                        
        except Exception as e:
            logger.error(f"ip-api 檢測失敗: {e}")
        
        return None
    
    async def _detect_with_ipinfo(self, ip: str) -> Optional[GeolocationInfo]:
        """使用 ipinfo.io 檢測"""
        if not await self._check_rate_limit("ipinfo"):
            return None
        
        try:
            # 使用 API 金鑰（如果有）
            url = f"https://ipinfo.io/{ip}/json"
            headers = {}
            if self.config.api.ipinfo_api_key:
                headers["Authorization"] = f"Bearer {self.config.api.ipinfo_api_key}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析位置
                    loc = data.get("loc", "")
                    latitude = None
                    longitude = None
                    if loc and "," in loc:
                        try:
                            lat_str, lon_str = loc.split(",")
                            latitude = float(lat_str)
                            longitude = float(lon_str)
                        except ValueError:
                            pass
                    
                    # 解析地區
                    region_parts = data.get("region", "").split(",")
                    region = region_parts[0] if region_parts else None
                    
                    return GeolocationInfo(
                        ip=ip,
                        country=data.get("country"),
                        city=data.get("city"),
                        region=region,
                        latitude=latitude,
                        longitude=longitude,
                        timezone=data.get("timezone"),
                        organization=data.get("org"),
                        confidence=0.75,  # ipinfo 置信度中上
                        source="ipinfo"
                    )
                    
        except Exception as e:
            logger.error(f"ipinfo 檢測失敗: {e}")
        
        return None
    
    async def _detect_with_ipgeolocation(self, ip: str) -> Optional[GeolocationInfo]:
        """使用 ipgeolocation.io 檢測"""
        if not self.config.api.ipgeolocation_api_key:
            return None
        
        if not await self._check_rate_limit("ipgeolocation"):
            return None
        
        try:
            url = f"https://api.ipgeolocation.io/ipgeo"
            params = {
                "apiKey": self.config.api.ipgeolocation_api_key,
                "ip": ip,
                "fields": "country_name,country_code2,state_prov,city,latitude,longitude,timezone,isp,organization,asn"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return GeolocationInfo(
                        ip=ip,
                        country=data.get("country_name"),
                        country_code=data.get("country_code2"),
                        region=data.get("state_prov"),
                        city=data.get("city"),
                        latitude=float(data["latitude"]) if data.get("latitude") else None,
                        longitude=float(data["longitude"]) if data.get("longitude") else None,
                        timezone=data.get("timezone"),
                        isp=data.get("isp"),
                        organization=data.get("organization"),
                        asn=data.get("asn"),
                        confidence=0.85,  # ipgeolocation 置信度高
                        source="ipgeolocation"
                    )
                    
        except Exception as e:
            logger.error(f"ipgeolocation 檢測失敗: {e}")
        
        return None
    
    async def _check_rate_limit(self, service: str) -> bool:
        """檢查 API 速率限制"""
        current_time = time.time()
        limit_info = self.api_limits[service]
        
        # 重置計數器（每分鐘）
        if current_time - limit_info["last_request"] > 60:
            limit_info["request_count"] = 0
            limit_info["last_request"] = current_time
        
        # 檢查是否超過限制
        if limit_info["request_count"] >= limit_info["requests_per_minute"]:
            logger.warning(f"{service} API 達到速率限制")
            return False
        
        limit_info["request_count"] += 1
        return True
    
    async def batch_detect_locations(self, ips: List[str], 
                                   max_concurrent: int = 10) -> Dict[str, GeolocationInfo]:
        """批量檢測地理位置
        
        Args:
            ips: IP 地址列表
            max_concurrent: 最大並發數
            
        Returns:
            IP 到地理位置信息的映射
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def detect_single(ip: str):
            async with semaphore:
                try:
                    info = await self.detect_location(ip)
                    if info:
                        results[ip] = info
                except Exception as e:
                    logger.error(f"檢測 {ip} 地理位置失敗: {e}")
        
        # 執行批量檢測
        tasks = [detect_single(ip) for ip in ips]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"批量檢測完成: {len(results)}/{len(ips)} 成功")
        return results
    
    def calculate_proximity(self, 
                          proxy_location: Tuple[float, float],
                          target_location: Tuple[float, float]) -> ProximityInfo:
        """計算代理與目標的距離信息
        
        Args:
            proxy_location: 代理位置 (緯度, 經度)
            target_location: 目標位置 (緯度, 經度)
            
        Returns:
            距離信息
        """
        # 計算地理距離
        distance = geodesic(proxy_location, target_location).kilometers
        
        # 估算延遲（簡化模型：距離 * 0.02ms/km + 基礎延遲）
        estimated_latency = distance * 0.02 + 10
        
        # 計算路由評分（距離越近評分越高）
        max_distance = 20000  # 地球周長的一半
        routing_score = max(0, 100 - (distance / max_distance * 100))
        
        return ProximityInfo(
            target_location=target_location,
            proxy_location=proxy_location,
            distance_km=distance,
            estimated_latency_ms=estimated_latency,
            routing_score=routing_score
        )
    
    async def enhance_proxy_with_location(self, proxy: ProxyNode) -> ProxyNode:
        """為代理節點添加地理位置信息
        
        Args:
            proxy: 代理節點
            
        Returns:
            增強後的代理節點
        """
        try:
            location_info = await self.detect_location(proxy.host)
            
            if location_info:
                # 更新代理元數據
                proxy.metadata.update({
                    "country": location_info.country,
                    "country_code": location_info.country_code,
                    "region": location_info.region,
                    "city": location_info.city,
                    "latitude": location_info.latitude,
                    "longitude": location_info.longitude,
                    "timezone": location_info.timezone,
                    "isp": location_info.isp,
                    "organization": location_info.organization,
                    "asn": location_info.asn,
                    "asn_name": location_info.asn_name,
                    "geolocation_confidence": location_info.confidence,
                    "geolocation_source": location_info.source,
                    "geolocation_updated": location_info.query_time.isoformat()
                })
                
                # 添加地理位置標籤
                if location_info.country_code:
                    proxy.tags.append(f"country:{location_info.country_code.lower()}")
                if location_info.region:
                    proxy.tags.append(f"region:{location_info.region.lower().replace(' ', '-')}")
                if location_info.city:
                    proxy.tags.append(f"city:{location_info.city.lower().replace(' ', '-')}")
                if location_info.isp:
                    proxy.tags.append(f"isp:{location_info.isp.lower().replace(' ', '-')}")
                
                logger.debug(f"為代理 {proxy.host}:{proxy.port} 添加地理位置信息: {location_info.country}, {location_info.city}")
            
        except Exception as e:
            logger.error(f"為代理 {proxy.host}:{proxy.port} 添加地理位置信息失敗: {e}")
        
        return proxy
    
    async def find_optimal_proxies_by_location(self, 
                                             proxies: List[ProxyNode],
                                             target_location: Tuple[float, float],
                                             max_distance_km: float = 1000) -> List[Tuple[ProxyNode, ProximityInfo]]:
        """根據地理位置尋找最佳代理
        
        Args:
            proxies: 代理列表
            target_location: 目標位置 (緯度, 經度)
            max_distance_km: 最大距離限制
            
        Returns:
            按距離排序的代理和距離信息列表
        """
        optimal_proxies = []
        
        for proxy in proxies:
            # 檢查代理是否有地理位置信息
            lat = proxy.metadata.get("latitude")
            lon = proxy.metadata.get("longitude")
            
            if lat is not None and lon is not None:
                proxy_location = (float(lat), float(lon))
                proximity = self.calculate_proximity(proxy_location, target_location)
                
                # 檢查距離限制
                if proximity.distance_km <= max_distance_km:
                    optimal_proxies.append((proxy, proximity))
        
        # 按距離排序
        optimal_proxies.sort(key=lambda x: x[1].distance_km)
        
        logger.info(f"找到 {len(optimal_proxies)} 個符合距離要求的代理")
        return optimal_proxies
    
    async def get_location_statistics(self, proxies: List[ProxyNode]) -> Dict[str, Any]:
        """獲取代理地理位置統計信息
        
        Args:
            proxies: 代理列表
            
        Returns:
            統計信息
        """
        stats = {
            "total_proxies": len(proxies),
            "with_location": 0,
            "countries": {},
            "regions": {},
            "cities": {},
            "isps": {},
            "asns": {}
        }
        
        for proxy in proxies:
            # 檢查是否有地理位置信息
            if proxy.metadata.get("latitude") and proxy.metadata.get("longitude"):
                stats["with_location"] += 1
                
                # 統計國家
                country = proxy.metadata.get("country")
                if country:
                    stats["countries"][country] = stats["countries"].get(country, 0) + 1
                
                # 統計地區
                region = proxy.metadata.get("region")
                if region:
                    stats["regions"][region] = stats["regions"].get(region, 0) + 1
                
                # 統計城市
                city = proxy.metadata.get("city")
                if city:
                    stats["cities"][city] = stats["cities"].get(city, 0) + 1
                
                # 統計 ISP
                isp = proxy.metadata.get("isp")
                if isp:
                    stats["isps"][isp] = stats["isps"].get(isp, 0) + 1
                
                # 統計 ASN
                asn = proxy.metadata.get("asn")
                if asn:
                    stats["asns"][asn] = stats["asns"].get(asn, 0) + 1
        
        # 計算覆蓋率
        stats["location_coverage"] = (stats["with_location"] / stats["total_proxies"] * 100) if stats["total_proxies"] > 0 else 0
        
        # 排序統計結果
        for key in ["countries", "regions", "cities", "isps", "asns"]:
            stats[key] = dict(sorted(stats[key].items(), key=lambda x: x[1], reverse=True))
        
        return stats
    
    async def cleanup_cache(self):
        """清理過期緩存"""
        await self.cache.cleanup_expired()
    
    async def close(self):
        """關閉地理位置檢測器"""
        if self.session:
            await self.session.close()
        logger.info("✅ 地理位置檢測器已關閉")


class IntelligentProxyRouter:
    """智能代理路由器
    
    根據地理位置和網路條件智能選擇代理
    """
    
    def __init__(self, geolocation_detector: EnhancedGeolocationDetector):
        self.geo_detector = geolocation_detector
        self.routing_history: List[Dict[str, Any]] = []
    
    async def select_optimal_proxy(self, 
                                 proxies: List[ProxyNode],
                                 target_url: str,
                                 preferences: Dict[str, Any] = None) -> Optional[ProxyNode]:
        """選擇最佳代理
        
        Args:
            proxies: 可用代理列表
            target_url: 目標 URL
            preferences: 偏好設置
            
        Returns:
            最佳代理
        """
        if not proxies:
            return None
        
        if preferences is None:
            preferences = {}
        
        # 解析目標域名的地理位置
        target_location = await self._get_target_location(target_url)
        
        # 評分所有代理
        scored_proxies = []
        
        for proxy in proxies:
            score = await self._calculate_proxy_score(
                proxy, target_location, preferences
            )
            scored_proxies.append((proxy, score))
        
        # 按評分排序
        scored_proxies.sort(key=lambda x: x[1], reverse=True)
        
        # 記錄路由決策
        if scored_proxies:
            best_proxy, best_score = scored_proxies[0]
            self.routing_history.append({
                "timestamp": datetime.now().isoformat(),
                "target_url": target_url,
                "selected_proxy": f"{best_proxy.host}:{best_proxy.port}",
                "score": best_score,
                "total_candidates": len(proxies)
            })
            
            logger.info(f"選擇代理 {best_proxy.host}:{best_proxy.port} (評分: {best_score:.2f})")
            return best_proxy
        
        return None
    
    async def _get_target_location(self, target_url: str) -> Optional[Tuple[float, float]]:
        """獲取目標 URL 的地理位置"""
        try:
            from urllib.parse import urlparse
            import socket
            
            # 解析域名
            parsed = urlparse(target_url)
            hostname = parsed.hostname or parsed.netloc
            
            if not hostname:
                return None
            
            # 解析 IP 地址
            ip = socket.gethostbyname(hostname)
            
            # 獲取地理位置
            location_info = await self.geo_detector.detect_location(ip)
            
            if location_info and location_info.latitude and location_info.longitude:
                return (location_info.latitude, location_info.longitude)
                
        except Exception as e:
            logger.debug(f"獲取目標位置失敗: {e}")
        
        return None
    
    async def _calculate_proxy_score(self, 
                                   proxy: ProxyNode,
                                   target_location: Optional[Tuple[float, float]],
                                   preferences: Dict[str, Any]) -> float:
        """計算代理評分
        
        Args:
            proxy: 代理節點
            target_location: 目標位置
            preferences: 偏好設置
            
        Returns:
            代理評分 (0-100)
        """
        score = 0.0
        
        # 基礎評分（根據代理狀態）
        if proxy.status == ProxyStatus.ACTIVE:
            score += 30
        elif proxy.status == ProxyStatus.INACTIVE:
            score += 10
        
        # 響應時間評分
        if proxy.response_time:
            if proxy.response_time < 1.0:
                score += 25
            elif proxy.response_time < 3.0:
                score += 15
            elif proxy.response_time < 5.0:
                score += 5
        
        # 成功率評分
        if proxy.success_rate:
            score += proxy.success_rate * 20  # 最高20分
        
        # 地理位置評分
        if target_location:
            proxy_lat = proxy.metadata.get("latitude")
            proxy_lon = proxy.metadata.get("longitude")
            
            if proxy_lat and proxy_lon:
                proxy_location = (float(proxy_lat), float(proxy_lon))
                proximity = self.geo_detector.calculate_proximity(
                    proxy_location, target_location
                )
                score += proximity.routing_score * 0.25  # 最高25分
        
        # 偏好評分
        preferred_countries = preferences.get("preferred_countries", [])
        if preferred_countries:
            proxy_country = proxy.metadata.get("country_code", "").upper()
            if proxy_country in [c.upper() for c in preferred_countries]:
                score += 10
        
        # 避免的國家
        avoided_countries = preferences.get("avoided_countries", [])
        if avoided_countries:
            proxy_country = proxy.metadata.get("country_code", "").upper()
            if proxy_country in [c.upper() for c in avoided_countries]:
                score -= 20
        
        # 協議偏好
        preferred_protocols = preferences.get("preferred_protocols", [])
        if preferred_protocols and proxy.protocol.value in preferred_protocols:
            score += 5
        
        return max(0, min(100, score))  # 限制在 0-100 範圍內
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """獲取路由統計信息"""
        if not self.routing_history:
            return {"total_routes": 0}
        
        total_routes = len(self.routing_history)
        avg_score = sum(r["score"] for r in self.routing_history) / total_routes
        avg_candidates = sum(r["total_candidates"] for r in self.routing_history) / total_routes
        
        # 統計最常用的代理
        proxy_usage = {}
        for record in self.routing_history:
            proxy = record["selected_proxy"]
            proxy_usage[proxy] = proxy_usage.get(proxy, 0) + 1
        
        most_used_proxy = max(proxy_usage.items(), key=lambda x: x[1]) if proxy_usage else None
        
        return {
            "total_routes": total_routes,
            "average_score": avg_score,
            "average_candidates": avg_candidates,
            "most_used_proxy": most_used_proxy[0] if most_used_proxy else None,
            "most_used_count": most_used_proxy[1] if most_used_proxy else 0,
            "unique_proxies_used": len(proxy_usage)
        }