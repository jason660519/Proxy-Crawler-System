# 🌐 代理管理器 (Proxy Manager)

一個現代化的智能代理獲取、驗證和管理系統，專為高效的網路爬蟲和數據採集而設計。

## ✨ 主要特性

### 🚀 智能代理獲取
- **多源整合**: 支援 JSON 文件、網頁爬取等多種代理來源
- **自動去重**: 智能識別和過濾重複代理
- **批量獲取**: 支持大批量代理獲取和管理

### 🔍 全面驗證系統
- **多維度檢測**: 可用性、速度、匿名度、地理位置全方位驗證
- **並發驗證**: 高效的異步並發驗證機制
- **智能評分**: 基於多項指標的代理質量評分系統

### 🏊 分級代理池
- **熱池 (Hot Pool)**: 高質量、低延遲的優質代理
- **溫池 (Warm Pool)**: 中等質量的穩定代理
- **冷池 (Cold Pool)**: 備用代理資源
- **黑名單池**: 自動隔離失效代理

### 🌐 Web 管理界面
- **實時監控**: 代理池狀態、統計數據實時更新
- **可視化操作**: 直觀的 Web 界面進行代理管理
- **批量操作**: 支持批量驗證、導出等操作

### 🔌 RESTful API
- **標準接口**: 完整的 REST API 支持
- **自動文檔**: Swagger/OpenAPI 自動生成文檔
- **靈活篩選**: 支援多種篩選條件和排序方式

## 🛠️ 快速開始

### 1. 安裝依賴

```bash
# 使用 uv (推薦)
uv add -r requirements-proxy-manager.txt

# 或使用 pip
pip install -r requirements-proxy-manager.txt
```

### 2. 啟動服務

```bash
# 開發模式 (自動重載)
python src/proxy_manager/server.py

# 生產模式
python src/proxy_manager/server.py --mode production

# 自定義配置
python src/proxy_manager/server.py --host 0.0.0.0 --port 8080

# 調試模式
python src/proxy_manager/server.py --debug
```

### 3. 訪問服務

- **Web 管理界面**: http://localhost:8000/
- **API 文檔**: http://localhost:8000/api/docs
- **健康檢查**: http://localhost:8000/api/health

## 📖 使用指南

### 基本使用

```python
from src.proxy_manager import ProxyManager, ProxyManagerConfig

# 創建配置
config = ProxyManagerConfig(
    fetcher_enabled=["free_proxy", "json_file"],
    validation_timeout=10,
    hot_pool_size=50
)

# 初始化管理器
manager = ProxyManager(config)

# 啟動服務
await manager.start()

# 獲取代理
proxy = await manager.get_proxy()
print(f"獲取到代理: {proxy.url}")

# 獲取統計信息
stats = await manager.get_stats()
print(f"熱池代理數量: {stats.hot_pool_size}")
```

### API 使用示例

```python
import httpx

# 獲取代理
response = httpx.get("http://localhost:8000/api/proxies")
proxies = response.json()

# 獲取統計信息
response = httpx.get("http://localhost:8000/api/stats")
stats = response.json()

# 手動獲取新代理
response = httpx.post("http://localhost:8000/api/fetch", json={"count": 50})
result = response.json()
```

### 配置文件

系統支持 YAML 配置文件，位於 `src/proxy_manager/config.yaml`：

```yaml
# 基本設置
basic:
  service_name: "代理管理器服務"
  debug: false
  log_level: "INFO"

# 代理獲取設置
fetcher:
  enabled_fetchers:
    - "free_proxy"
    - "json_file"
  free_proxy:
    count: 100
    timeout: 10

# 代理池設置
pool:
  hot_pool:
    max_size: 50
    min_success_rate: 0.9
```

## 🏗️ 架構設計

### 核心模塊

```
src/proxy_manager/
├── __init__.py          # 模塊入口
├── models.py            # 數據模型定義
├── fetchers.py          # 代理獲取器
├── validators.py        # 代理驗證器
├── pools.py             # 代理池管理
├── manager.py           # 核心管理器
├── api.py               # FastAPI 接口
├── server.py            # 服務啟動腳本
├── config.yaml          # 配置文件
├── templates/           # Web 模板
│   └── index.html       # 管理界面
└── README.md            # 說明文檔
```

### 數據流程

```
代理來源 → 獲取器 → 驗證器 → 代理池 → API/Web界面
    ↓         ↓        ↓        ↓         ↓
多種來源   去重處理   質量評分   分級管理   用戶接口
```

## 🔧 高級功能

### 自定義代理獲取器

```python
from src.proxy_manager.fetchers import ProxyFetcher

class CustomFetcher(ProxyFetcher):
    async def fetch_proxies(self, count: int) -> List[ProxyNode]:
        # 實現自定義獲取邏輯
        proxies = []
        # ... 獲取代理邏輯
        return proxies

# 註冊自定義獲取器
manager.fetcher_manager.register_fetcher("custom", CustomFetcher())
```

### 自定義驗證規則

```python
from src.proxy_manager.validators import ValidationConfig

# 自定義驗證配置
config = ValidationConfig(
    timeout=15,
    test_urls=["https://httpbin.org/ip", "https://icanhazip.com"],
    check_anonymity=True,
    check_location=True
)

validator = ProxyValidator(config)
```

### 批量操作

```python
# 批量驗證
results = await manager.batch_validate(proxy_list)

# 批量導入
await manager.import_proxies("proxy_list.json")

# 批量導出
await manager.export_proxies("output.json", format="json")
```

## 📊 監控和統計

### 實時統計

系統提供豐富的統計信息：

- **代理池狀態**: 各池代理數量、質量分佈
- **性能指標**: 平均響應時間、成功率
- **獲取統計**: 獲取速度、來源分佈
- **驗證統計**: 驗證速度、通過率

### Web 監控界面

訪問 http://localhost:8000/ 查看：

- 📊 實時統計卡片
- 📈 代理池狀態圖表
- 📋 代理列表和詳細信息
- 🔄 手動操作按鈕
- 📝 系統日誌顯示

## 🚀 性能優化

### 並發設置

```yaml
# 配置文件中調整並發數
validator:
  max_concurrent: 100  # 增加並發驗證數
  timeout: 5           # 減少超時時間

pool:
  hot_pool:
    validation_interval: 3  # 更頻繁的驗證
```

### 緩存優化

```python
# 啟用 Redis 緩存 (可選)
config = ProxyManagerConfig(
    cache_enabled=True,
    cache_url="redis://localhost:6379"
)
```

## 🔒 安全考慮

### API 安全

```yaml
# 啟用 API 密鑰驗證
security:
  api_key:
    enabled: true
    key: "your-secret-key"
    header_name: "X-API-Key"
```

### IP 白名單

```yaml
# 限制訪問 IP
security:
  ip_whitelist:
    enabled: true
    allowed_ips:
      - "192.168.1.0/24"
      - "10.0.0.0/8"
```

## 🐛 故障排除

### 常見問題

1. **代理獲取失敗**
   ```bash
   # 檢查網路連接
   python -c "import requests; print(requests.get('https://httpbin.org/ip').text)"
   ```

2. **驗證速度慢**
   ```yaml
   # 調整並發數和超時
   validator:
     max_concurrent: 200
     timeout: 5
   ```

3. **內存使用過高**
   ```yaml
   # 減少池大小
   pool:
     cold_pool:
       max_size: 200
   ```

### 日誌分析

```bash
# 查看詳細日誌
python server.py --debug

# 查看特定模塊日誌
grep "validator" logs/proxy_manager.log
```

## 🤝 貢獻指南

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 許可證

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 🙏 致謝

- [FastAPI](https://fastapi.tiangolo.com/) - 現代 Web 框架
- [aiohttp](https://aiohttp.readthedocs.io/) - 異步 HTTP 客戶端
- [loguru](https://loguru.readthedocs.io/) - 優雅的日誌記錄

---

**🌟 如果這個項目對您有幫助，請給我們一個 Star！**