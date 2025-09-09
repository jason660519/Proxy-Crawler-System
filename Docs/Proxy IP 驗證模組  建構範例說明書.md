# Proxy IP 驗證模組建構範例說明書

模組名稱：Proxy Pool Manager (PPM) 之 Proxy IP 驗證模組  
核心目標：打造一個高可用、高性能、全自動化的代理 IP 質量管理與分發系統。  
技術棧：Python 3.11+, Asyncio, aiohttp, Redis, FastAPI, Prometheus, Grafana, Docker  
最後更新：2025-09-08  
版本：v1.0

---

## 一、核心架構與設計哲學

### 1.1 設計原則

1. 高併發：採用異步IO模型，萬級IP驗證分鐘內完成。  
2. 高可用：無單點故障，組件可水平擴展。  
3. 數據驅動：所有決策（評分、淘汰、調度）基於指標數據，而非人工猜測。  
4. 透明可觀測：系統所有狀態和性能指標均被採集、可視化、可告警。  
5. 低耦合：模組通過清晰API對外提供服務，可輕鬆集成至任何爬蟲項目。

### 1.2 系統架構圖

以下圖表展示了 Proxy Pool Manager (PPM) 的整體架構及其核心工作流程：

```mermaid
flowchart TD
  subgraph A [數據採集層]
    A1[免費源爬取器]
    A2[付費API適配器]
    A3[手動上傳接口]
  end

  subgraph B [調度與協調層]
    B1[調度器\nScheduler]
    B2[[任務隊列\nRedis List]]
  end

    `subgraph C [核心驗證層]`  
        `C1[驗證器 Worker]`  
        `C2[驗證器 Worker]`  
        `C3[驗證器 Worker]`  
        `C4[目標網站<br>httpbin/真實站點]`  
    `end`

    `subgraph D [數據存儲層]`  
        `D1[(狀態存儲<br>Redis)]`  
        `D2[(指標時序數據庫<br>Prometheus)]`  
    `end`

    `subgraph E [服務與控制層]`  
        `E1[管理API<br>FastAPI]`  
        `E2[對外RESTful API]`  
        `E3[指標看板<br>Grafana]`  
    `end`

    `subgraph F [消費端]`  
        `F1[爬蟲應用]`  
        `F2[數據採集任務]`  
        `F3[管理員]`  
    `end`

    `A -- 原始IP --> B1`  
    `B1 -- 調度驗證任務 --> B2`  
    `B2 -- 分配任務 --> C`  
    `C -- 驗證結果 --> D1`  
    `C -- 性能指標 --> D2`  
      
    `D1 -- 提供可用IP --> E2`  
    `E2 -- 獲取/反饋IP --> F1 & F2`  
      
    `E1 -- 管理與配置 --> F3`  
    `D2 -- 數據可視化 --> E3`

    `E3 -- 監控與告警 --> F3`

---

## 二、模組詳細說明

### 2.1 數據採集層 (Fetcher)

職責：從多樣化來源獲取原始代理IP。

`python`

*`# src/fetcher/abstract_fetcher.py`*  
`from abc import ABC, abstractmethod`  
`from typing import List`  
`from dataclasses import dataclass`

`@dataclass`  
`class ProxyItem:`  
    `ip: str`  
    `port: int`  
    `protocol: str = 'http'  # http, https, socks4, socks5`  
    `source: str = 'unknown'`

`class AbstractFetcher(ABC):`  
    `@abstractmethod`  
    `async def fetch(self) -> List[ProxyItem]:`  
        `pass`

*`# 示例：免費網站抓取`*  
*`# src/fetcher/free_proxy_list_fetcher.py`*  
`class FreeProxyListFetcher(AbstractFetcher):`  
    `async def fetch(self) -> List[ProxyItem]:`  
        `# 使用 aiohttp 抓取 https://free-proxy-list.net/`  
        `# 使用 lxml 或 beautifulsoup4 解析 HTML`  
        `# 返回 List[ProxyItem]`

        `pass`

配置化來源：所有來源應在 `config/sources.yaml` 中配置，便於動態增刪。

`yaml`

`sources:`  
  `- name: "free-proxy-list"`  
    `enabled: true`  
    `type: "web"`  
    `url: "https://free-proxy-list.net/"`  
    `schedule: "*/30 * * * *"  # 每30分鐘抓取一次`  
  `- name: "premium-proxy-provider"`  
    `enabled: true`  
    `type: "api"`  
    `url: "https://api.provider.com/getproxies"`  
    `api_key: "${API_KEY}"     # 從環境變數讀取`

    `schedule: "0 */1 * * *"   # 每小時抓取一次`

### 2.2 驗證器 (Worker)

職責：執行單個代理IP的全面質量驗證。

核心驗證邏輯：

`python`

*`# src/validator/core_validator.py`*  
`import asyncio`  
`import aiohttp`  
`from datetime import datetime`

`class CoreValidator:`  
    `def __init__(self, session: aiohttp.ClientSession):`  
        `self.session = session`  
        `self.timeout = aiohttp.ClientTimeout(total=15)`  
        `self.test_urls = [`  
            `"http://httpbin.org/ip",          # 基礎測試`  
            `"https://httpbin.org/ip",         # HTTPS支持測試`  
            `"http://httpbin.org/headers",     # 匿名度測試`  
            `"https://www.target-site.com/"    # 真實業務目標測試（配置化）`  
        `]`

    `async def validate_proxy(self, proxy_item: ProxyItem) -> ValidationResult:`  
        `result = ValidationResult(proxy_item=proxy_item)`  
        `proxy_url = f"{proxy_item.protocol}://{proxy_item.ip}:{proxy_item.port}"`

        `for test_url in self.test_urls:`  
            `start_time = datetime.now()`  
            `try:`  
                `async with self.session.get(test_url, proxy=proxy_url, timeout=self.timeout, ssl=False) as response:`  
                    `end_time = datetime.now()`  
                    `response_time = (end_time - start_time).total_seconds() * 1000  # ms`

                    `result.response_times[test_url] = response_time`  
                    `result.is_online = True`

                    `# 分析匿名度`  
                    `if "headers" in test_url:`  
                        `anonymity = self._check_anonymity(await response.text())`  
                        `result.anonymity = anonymity`

                    `# 驗證地理位置 (可選)`  
                    `if "ip" in test_url:`  
                        `result.geo_info = await self._parse_geo_info(await response.json())`

            `except (aiohttp.ClientError, asyncio.TimeoutError) as e:`  
                `result.errors[test_url] = str(e)`  
                `result.is_online = False`  
                `break  # 一個請求失敗即可認為代理不可用，節省時間`

        `return result`

### 2.3 數據模型 (Data Models)

使用 Pydantic 清晰定義所有數據結構：

`python`

*`# src/models.py`*  
`from pydantic import BaseModel, Field`  
`from enum import Enum`  
`from typing import Dict, Optional`

`class AnonymityLevel(str, Enum):`  
    `TRANSPARENT = "transparent"`  
    `ANONYMOUS = "anonymous"`  
    `ELITE = "elite"`

`class ProxyStatus(str, Enum):`  
    `PENDING = "pending"`  
    `ONLINE = "online"`  
    `OFFLINE = "offline"`

`class ProxyItem(BaseModel):`  
    `ip: str`  
    `port: int`  
    `protocol: str`  
    `source: str`

`class ValidationResult(BaseModel):`  
    `proxy_item: ProxyItem`  
    `is_online: bool = False`  
    `anonymity: AnonymityLevel = AnonymityLevel.TRANSPARENT`  
    `response_times: Dict[str, float] = Field(default_factory=dict)  # url -> ms`  
    `geo_info: Optional[Dict] = None`  
    `errors: Dict[str, str] = Field(default_factory=dict)`  
    `validated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())`

`class ScoredProxyItem(ProxyItem):`  
    `score: float = 0.0`  
    `success_rate: float = 0.0`  
    `last_checked: str`  
    `status: ProxyStatus = ProxyStatus.PENDING`  
    `total_checks: int = 0`

    `success_checks: int = 0`

### 2.4 存儲管理器 (Storage Manager)

職責：封裝所有與Redis的交互邏輯，提供高效的数据讀寫接口。

`python`

*`# src/storage/redis_manager.py`*  
`import redis.asyncio as redis`  
`from src.models import ScoredProxyItem`

`class RedisStorageManager:`  
    `def __init__(self, redis_conn: redis.Redis):`  
        `self.conn = redis_conn`

    `async def upsert_proxy(self, scored_item: ScoredProxyItem):`  
        `# 使用 Pipeline 提高性能`  
        `pipe = self.conn.pipeline()`  
        `proxy_key = f"proxy:{scored_item.ip}:{scored_item.port}"`

        `# 將代理數據存為 Hash`  
        `pipe.hset(proxy_key, mapping=scored_item.dict())`  
        `# 將代理加入按分數排序的集合`  
        `pipe.zadd("proxies:sorted_by_score", {proxy_key: scored_item.score})`  
        `# 將代理加入按響應速度排序的集合`  
        `pipe.zadd("proxies:sorted_by_speed", {proxy_key: scored_item.response_time})`  
        `await pipe.execute()`

    `async def get_best_proxies(self, limit: int = 10, protocol: str = None) -> List[ScoredProxyItem]:`  
        `# 從分數最高的集合中取出Top N`  
        `proxy_keys = await self.conn.zrevrange("proxies:sorted_by_score", 0, limit - 1)`  
        `proxies = []`  
        `for key in proxy_keys:`  
            `proxy_data = await self.conn.hgetall(key)`  
            `proxies.append(ScoredProxyItem(**proxy_data))`

        `return proxies`

---

## 三、核心工作流程

1. 採集階段：調度器根據配置定時觸發各個Fetcher，將抓取到的原始 `ProxyItem` 放入「待驗證隊列」（Redis List）。  
2. 驗證階段：  
   * 多個Worker異步地從隊列中獲取任務。  
   * 每個Worker對一個IP執行完整的驗證鏈（基礎連通性 \-\> HTTPS \-\> 匿名度 \-\> 真實目標）。  
   * 生成帶有詳細指標的 `ValidationResult`。  
3. 評分與存儲階段：  
   * `ResultProcessor` 根據驗證結果計算綜合評分。  
     `score = (success_rate * 100) + (1 / avg_response_time * 1000) + (anonymity_weight)`  
   * 將帶分數的 `ScoredProxyItem` 持久化到Redis，並更新排序集合。  
4. 生命周期管理：  
   * 調度器定時觸發對已有代理的重驗證，防止IP失效。  
   * 根據評分和最後驗證時間，定期清理低質量、陳舊的代理。

---

## 四、質量指標與觀測體系

### 4.1 核心指標 (Metrics)

使用Prometheus客戶端暴露指標：

`python`

*`# src/metrics.py`*  
`from prometheus_client import Counter, Gauge, Histogram`

*`# 定義指標`*  
`VALIDATION_ATTEMPTS = Counter('proxy_validation_attempts_total', 'Total validation attempts', ['source', 'result'])`  
`VALIDATION_DURATION = Histogram('proxy_validation_duration_seconds', 'Time spent validating a proxy')`  
`PROXY_POOL_GAUGE = Gauge('proxy_pool_total', 'Current total proxies in pool', ['status', 'anonymity'])`  
`RESPONSE_TIME_HISTOGRAM = Histogram('proxy_response_time_ms', 'Proxy response time in ms', ['test_url'])`

*`# 在驗證器中記錄指標`*  
`@VALIDATION_DURATION.time()`  
`async def validate_proxy(proxy_item):`  
    `VALIDATION_ATTEMPTS.labels(source=proxy_item.source).inc()`  
    `start_time = time.time()`  
    `# ... 驗證邏輯 ...`

    `RESPONSE_TIME_HISTOGRAM.labels(test_url=test_url).observe(response_time)`

### 4.2 Grafana 儀表板

創建至少三個看板：

1. 總體健康度：Pool總量、可用率、平均分數、平均速度。  
2. 來源質量：按來源統計的可用率、貢獻IP數量。  
3. 性能詳情：驗證耗時分佈、各目標網站的響應時間。

### 4.3 告警規則 (Alerting)

在Prometheus中配置：

`yaml`

`groups:`  
`- name: proxy-pool-alerts`  
  `rules:`  
  `- alert: ProxyPoolShrinkage`  
    `expr: avg_over_time(proxy_pool_total{status="online"}[1h]) < 100`  
    `for: 10m`  
    `labels:`  
      `severity: critical`  
    `annotations:`  
      `summary: "可用代理IP池急劇縮水，低於100個"`  
  `- alert: HighProxyFailureRate`  
    `expr: rate(proxy_validation_attempts_total{result="fail"}[5m]) / rate(proxy_validation_attempts_total[5m]) > 0.8`  
    `for: 5m`  
    `labels:`  
      `severity: warning`  
    `annotations:`

      `summary: "代理驗證失敗率過高"`

---

## 五、部署與擴展

### 5.1 Docker化

提供完整的 `docker-compose.yml` 來一鍵部署所有依賴：

`yaml`

`version: '3.8'`  
`services:`  
  `redis:`  
    `image: redis:7-alpine`  
    `ports:`  
      `- "6379:6379"`  
    `volumes:`  
      `- redis_data:/data`

  `prometheus:`  
    `image: prom/prometheus`  
    `ports:`  
      `- "9090:9090"`  
    `volumes:`  
      `- ./config/prometheus.yml:/etc/prometheus/prometheus.yml`

  `grafana:`  
    `image: grafana/grafana-enterprise`  
    `ports:`  
      `- "3000:3000"`  
    `environment:`  
      `- GF_SECURITY_ADMIN_PASSWORD=admin`  
    `depends_on:`  
      `- prometheus`

  `proxy-pool:`  
    `build: .`  
    `image: proxy-pool:latest`  
    `environment:`  
      `- REDIS_URL=redis://redis:6379/0`  
      `- PROMETHEUS_MULTIPROC_DIR=/tmp`  
    `depends_on:`  
      `- redis`  
    `deploy:`  
      `replicas: 3  # 可以輕鬆水平擴展Worker`

`volumes:`

  `redis_data:`

### 5.2 水平擴展方案

1. Worker無狀態：任何Worker實例都可以從Redis隊列中消費任務。  
2. 分片鍵：可根據代理IP的協議或來源進行分片，不同Worker組處理不同類型的任務。  
3. 動態擴縮容：結合Kubernetes HPA，根據隊列積壓任務數量自動調整Worker副本數。

---

## 六、使用方式

### 6.1 作為 Python 庫使用

`python`

`from proxy_pool_manager import ProxyPoolManager`

`async with ProxyPoolManager(redis_url="redis://localhost:6379/0") as ppm:`  
    `best_proxies = await ppm.get_best_proxies(limit=5, protocol='https')`  
    `for proxy in best_proxies:`

        `print(f"{proxy.ip}:{proxy.port} - Score: {proxy.score}")`

### 6.2 作為獨立服務使用

通過RESTful API調用：

`bash`

*`# 獲取一個最佳代理`*  
`curl -X GET "http://localhost:8000/api/v1/proxy?protocol=https"`

*`# 上報代理失效（眾包反饋）`*  
`curl -X POST "http://localhost:8000/api/v1/proxy/feedback" \`  
  `-H "Content-Type: application/json" \`

  `-d '{"ip": "192.168.1.1", "port": 8080, "success": false}'`

---

結語：此系統設計兼顧了性能、可靠性和可擴展性，是現代化數據採集基礎設施的核心組件。嚴格遵循此說明書構建，您的代理IP管理能力將達到業界專業水準，成為名副其實的技術傳家寶。  
