# Proxies 管理測試頁面設計報告書

**專案名稱：** Proxy-Crawler-System  
**頁面功能：** IP 導入、健康檢查與統計分析  
**頁面路徑：** http://localhost:5174/proxies  
**文件版本：** 1.0  
**建立日期：** 2025-01-27  
**參考文檔：** Proxy_IP_驗證模組比較報告書_2025-09-08.md  

---

## 一、頁面概覽與功能定位

### 1.1 核心功能
本頁面專門設計為 **IP 導入與健康檢查測試平台**，主要服務於以下使用場景：

- **📁 檔案導入**：支援 JSON/CSV 格式的 IP 清單批量導入
- **🔍 健康檢查**：對導入的 IP 進行全面的連通性和功能驗證
- **📊 統計分析**：即時顯示 IP 健康指數、成功率和詳細統計資料
- **📈 視覺化報告**：提供直觀的圖表和儀表板展示檢測結果

### 1.2 目標使用者
- **測試工程師**：驗證代理 IP 清單的可用性
- **運維人員**：監控代理池的健康狀態
- **開發人員**：測試和調試代理相關功能
- **業務分析師**：分析代理 IP 的品質和分佈

### 1.3 設計理念
基於 **Proxy_IP_驗證模組比較報告書** 的分析結果，本頁面採用以下設計原則：

- **模組化架構**：清晰的功能分層，易於維護和擴展
- **即時反饋**：提供即時的檢測進度和結果回饋
- **數據驅動**：基於 Prometheus 指標的完整監控體系
- **使用者友善**：直觀的操作流程和豐富的視覺化元素

---

## 二、技術架構設計

### 2.1 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 React 應用層                        │
├─────────────────────────────────────────────────────────────┤
│  檔案上傳組件  │  檢測控制台  │  統計儀表板  │  結果展示區   │
├─────────────────────────────────────────────────────────────┤
│                    API 服務層 (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│  檔案解析器   │   驗證引擎   │   統計計算   │   結果匯出    │
├─────────────────────────────────────────────────────────────┤
│                    數據存儲層                               │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL    │     Redis      │  Prometheus  │  檔案系統  │
│  (持久化存儲)   │   (快取層)      │   (指標)     │  (檔案)    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心組件設計

#### 2.2.1 檔案導入模組
```typescript
interface FileImportModule {
  // 支援的檔案格式
  supportedFormats: ['json', 'csv', 'txt'];
  
  // 檔案驗證
  validateFile(file: File): ValidationResult;
  
  // 檔案解析
  parseFile(file: File): Promise<ProxyItem[]>;
  
  // 批量導入
  importProxies(proxies: ProxyItem[]): Promise<ImportResult>;
}
```

#### 2.2.2 健康檢查引擎
```typescript
interface HealthCheckEngine {
  // 檢查配置
  config: {
    timeout: number;           // 超時時間 (秒)
    retries: number;          // 重試次數
    concurrency: number;      // 併發數量
    testUrls: string[];       // 測試目標網站
  };
  
  // 單個 IP 檢查
  checkSingle(proxy: ProxyItem): Promise<HealthResult>;
  
  // 批量檢查
  checkBatch(proxies: ProxyItem[]): Promise<BatchResult>;
  
  // 即時進度回報
  onProgress: (progress: ProgressInfo) => void;
}
```

#### 2.2.3 統計分析模組
```typescript
interface StatisticsModule {
  // 健康指數計算
  calculateHealthScore(results: HealthResult[]): HealthScore;
  
  // 統計資料生成
  generateStatistics(results: HealthResult[]): StatisticsData;
  
  // 趨勢分析
  analyzeTrends(historical: HealthResult[]): TrendAnalysis;
}
```

### 2.3 數據模型定義

#### 2.3.1 代理項目模型
```typescript
interface ProxyItem {
  id?: string;                    // 唯一識別碼
  ip: string;                     // IP 地址
  port: number;                   // 端口號
  protocol: ProxyProtocol;        // 協議類型
  username?: string;              // 用戶名
  password?: string;              // 密碼
  country?: string;               // 國家
  city?: string;                  // 城市
  source: 'import' | 'crawl';     // 來源類型
  importedAt: string;             // 導入時間
  tags?: string[];                // 標籤
}

enum ProxyProtocol {
  HTTP = 'http',
  HTTPS = 'https',
  SOCKS4 = 'socks4',
  SOCKS5 = 'socks5'
}
```

#### 2.3.2 健康檢查結果模型
```typescript
interface HealthResult {
  proxyId: string;                // 代理 ID
  status: HealthStatus;           // 健康狀態
  responseTime?: number;          // 響應時間 (毫秒)
  successRate: number;            // 成功率 (0-1)
  anonymityLevel: AnonymityLevel; // 匿名等級
  geoLocation?: GeoInfo;          // 地理位置資訊
  testResults: TestResult[];      // 詳細測試結果
  healthScore: number;            // 健康分數 (0-100)
  checkedAt: string;              // 檢查時間
  error?: string;                 // 錯誤訊息
}

enum HealthStatus {
  HEALTHY = 'healthy',       // 健康
  UNHEALTHY = 'unhealthy',   // 不健康
  TESTING = 'testing',       // 測試中
  UNKNOWN = 'unknown'        // 未知
}

enum AnonymityLevel {
  TRANSPARENT = 'transparent',  // 透明
  ANONYMOUS = 'anonymous',      // 匿名
  ELITE = 'elite'              // 精英
}

interface TestResult {
  testType: 'connectivity' | 'https' | 'anonymity' | 'geo' | 'target';
  success: boolean;
  responseTime?: number;
  details?: any;
  error?: string;
}
```

#### 2.3.3 統計資料模型
```typescript
interface StatisticsData {
  summary: {
    total: number;              // 總數
    healthy: number;            // 健康數量
    unhealthy: number;          // 不健康數量
    testing: number;            // 測試中數量
    averageHealthScore: number; // 平均健康分數
    averageResponseTime: number; // 平均響應時間
  };
  
  distribution: {
    byProtocol: Record<string, number>;     // 按協議分佈
    byCountry: Record<string, number>;      // 按國家分佈
    byAnonymity: Record<string, number>;    // 按匿名等級分佈
    byHealthScore: HealthScoreRange[];      // 按健康分數分佈
  };
  
  trends: {
    healthScoreHistory: TimeSeriesData[];   // 健康分數趨勢
    responseTimeHistory: TimeSeriesData[];  // 響應時間趨勢
  };
}

interface HealthScoreRange {
  range: string;    // 例如: "90-100", "80-89"
  count: number;
  percentage: number;
}

interface TimeSeriesData {
  timestamp: string;
  value: number;
}
```

---

## 三、使用者介面設計

### 3.1 頁面佈局結構

```
┌─────────────────────────────────────────────────────────────┐
│                        頁面標題區                            │
│  📊 Proxies 管理測試平台  [設定] [說明] [匯出報告]           │
├─────────────────────────────────────────────────────────────┤
│                      檔案導入區域                            │
│  📁 拖拽上傳區域 或 [選擇檔案] [JSON/CSV/TXT]               │
│  📋 檔案預覽: 顯示前 10 筆資料                               │
├─────────────────────────────────────────────────────────────┤
│                      檢測控制區域                            │
│  ⚙️ [檢測設定] [開始檢測] [暫停] [停止] [清除結果]           │
│  📊 進度條: ████████░░ 80% (800/1000)                      │
├─────────────────────────────────────────────────────────────┤
│                      統計儀表板                              │
│  ┌─────────┬─────────┬─────────┬─────────┐                  │
│  │ 總數量   │ 健康IP  │ 失效IP  │ 健康指數 │                  │
│  │ 1,000   │  856   │  144   │  85.6%  │                  │
│  └─────────┴─────────┴─────────┴─────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                      結果展示區域                            │
│  📈 [圖表視圖] [列表視圖] [詳細視圖]                         │
│  🔍 [篩選] [搜尋] [排序] [匯出]                              │
│  📋 結果表格或圖表                                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 關鍵 UI 組件設計

#### 3.2.1 檔案上傳組件
```typescript
interface FileUploadComponent {
  // 拖拽上傳區域
  dragDropZone: {
    acceptedTypes: ['.json', '.csv', '.txt'];
    maxFileSize: '10MB';
    multipleFiles: false;
  };
  
  // 檔案預覽
  filePreview: {
    showFirstNRows: 10;
    validateFormat: boolean;
    showParsingErrors: boolean;
  };
  
  // 上傳進度
  uploadProgress: {
    showProgressBar: boolean;
    showFileInfo: boolean;
  };
}
```

#### 3.2.2 檢測控制台組件
```typescript
interface TestControlPanel {
  // 檢測設定
  settings: {
    timeout: number;        // 1-60 秒
    retries: number;        // 0-5 次
    concurrency: number;    // 1-50 併發
    testUrls: string[];     // 自訂測試網站
  };
  
  // 控制按鈕
  controls: {
    startTest: () => void;
    pauseTest: () => void;
    stopTest: () => void;
    clearResults: () => void;
  };
  
  // 進度顯示
  progress: {
    percentage: number;
    current: number;
    total: number;
    estimatedTime: string;
  };
}
```

#### 3.2.3 統計儀表板組件
```typescript
interface StatisticsDashboard {
  // 摘要卡片
  summaryCards: [
    { title: '總數量', value: number, icon: '📊' },
    { title: '健康 IP', value: number, icon: '✅', color: 'green' },
    { title: '失效 IP', value: number, icon: '❌', color: 'red' },
    { title: '健康指數', value: string, icon: '💚', unit: '%' }
  ];
  
  // 圖表組件
  charts: {
    healthDistribution: PieChart;      // 健康狀態分佈圓餅圖
    protocolDistribution: BarChart;    // 協議分佈長條圖
    responseTimeHistogram: Histogram;  // 響應時間分佈直方圖
    countryDistribution: WorldMap;     // 國家分佈世界地圖
  };
}
```

#### 3.2.4 結果展示組件
```typescript
interface ResultsDisplay {
  // 視圖模式
  viewModes: ['table', 'cards', 'charts'];
  
  // 篩選選項
  filters: {
    status: HealthStatus[];
    protocol: ProxyProtocol[];
    country: string[];
    healthScoreRange: [number, number];
    responseTimeRange: [number, number];
  };
  
  // 排序選項
  sorting: {
    field: 'healthScore' | 'responseTime' | 'checkedAt';
    order: 'asc' | 'desc';
  };
  
  // 分頁
  pagination: {
    page: number;
    size: number;
    total: number;
  };
}
```

### 3.3 互動流程設計

#### 3.3.1 檔案導入流程
```
1. 使用者拖拽或選擇檔案
   ↓
2. 系統驗證檔案格式和大小
   ↓
3. 解析檔案內容並顯示預覽
   ↓
4. 使用者確認導入
   ↓
5. 系統批量導入到資料庫
   ↓
6. 顯示導入結果摘要
```

#### 3.3.2 健康檢查流程
```
1. 使用者設定檢測參數
   ↓
2. 點擊「開始檢測」
   ↓
3. 系統開始併發檢測
   ↓
4. 即時更新進度和結果
   ↓
5. 檢測完成，生成統計報告
   ↓
6. 使用者查看結果和匯出報告
```

---

## 四、API 介面設計

### 4.1 檔案導入 API

#### 4.1.1 檔案上傳
```http
POST /api/proxies/import/upload
Content-Type: multipart/form-data

Body:
- file: File (JSON/CSV/TXT)
- options: {
    "skipDuplicates": true,
    "validateFormat": true,
    "tags": ["imported", "test"]
  }

Response:
{
  "success": true,
  "data": {
    "uploadId": "upload-123",
    "filename": "proxies.csv",
    "size": 1024000,
    "previewData": ProxyItem[],
    "totalCount": 1000,
    "validCount": 950,
    "invalidCount": 50,
    "errors": ["Line 15: Invalid IP format"]
  }
}
```

#### 4.1.2 確認導入
```http
POST /api/proxies/import/confirm
Content-Type: application/json

Body:
{
  "uploadId": "upload-123",
  "importOptions": {
    "skipInvalid": true,
    "overwriteExisting": false,
    "batchSize": 100
  }
}

Response:
{
  "success": true,
  "data": {
    "importId": "import-456",
    "status": "processing",
    "progress": {
      "current": 0,
      "total": 950
    }
  }
}
```

#### 4.1.3 導入進度查詢
```http
GET /api/proxies/import/{importId}/status

Response:
{
  "success": true,
  "data": {
    "importId": "import-456",
    "status": "completed",
    "progress": {
      "current": 950,
      "total": 950
    },
    "result": {
      "imported": 920,
      "skipped": 30,
      "failed": 0
    },
    "completedAt": "2025-01-27T10:30:00Z"
  }
}
```

### 4.2 健康檢查 API

#### 4.2.1 開始批量檢測
```http
POST /api/proxies/health-check/batch
Content-Type: application/json

Body:
{
  "proxyIds": ["proxy-1", "proxy-2", ...],
  "config": {
    "timeout": 10,
    "retries": 2,
    "concurrency": 20,
    "testUrls": [
      "http://httpbin.org/ip",
      "https://api.ipify.org"
    ],
    "tests": [
      "connectivity",
      "https_support",
      "anonymity",
      "geo_location"
    ]
  }
}

Response:
{
  "success": true,
  "data": {
    "checkId": "check-789",
    "status": "started",
    "totalProxies": 1000,
    "estimatedDuration": "5 minutes"
  }
}
```

#### 4.2.2 檢測進度查詢
```http
GET /api/proxies/health-check/{checkId}/progress

Response:
{
  "success": true,
  "data": {
    "checkId": "check-789",
    "status": "running",
    "progress": {
      "current": 650,
      "total": 1000,
      "percentage": 65
    },
    "statistics": {
      "healthy": 520,
      "unhealthy": 130,
      "averageResponseTime": 245
    },
    "estimatedTimeRemaining": "2 minutes"
  }
}
```

#### 4.2.3 檢測結果查詢
```http
GET /api/proxies/health-check/{checkId}/results
Query Parameters:
  - page: number
  - size: number
  - status: HealthStatus
  - sortBy: string
  - sortOrder: 'asc' | 'desc'

Response:
{
  "success": true,
  "data": {
    "results": HealthResult[],
    "pagination": {
      "page": 1,
      "size": 50,
      "total": 1000,
      "totalPages": 20
    },
    "statistics": StatisticsData
  }
}
```

### 4.3 統計分析 API

#### 4.3.1 即時統計
```http
GET /api/proxies/statistics/realtime
Query Parameters:
  - checkId: string (可選，特定檢測的統計)
  - timeRange: string (可選，時間範圍)

Response:
{
  "success": true,
  "data": StatisticsData
}
```

#### 4.3.2 歷史趨勢
```http
GET /api/proxies/statistics/trends
Query Parameters:
  - startDate: string
  - endDate: string
  - granularity: 'hour' | 'day' | 'week'

Response:
{
  "success": true,
  "data": {
    "healthScoreTrend": TimeSeriesData[],
    "responseTimeTrend": TimeSeriesData[],
    "availabilityTrend": TimeSeriesData[]
  }
}
```

### 4.4 WebSocket 即時更新

```typescript
// WebSocket 連接
const ws = new WebSocket('ws://localhost:8000/ws/health-check');

// 訊息格式
interface WSMessage {
  type: 'progress_update' | 'result_update' | 'statistics_update';
  data: any;
  timestamp: string;
}

// 進度更新
{
  "type": "progress_update",
  "data": {
    "checkId": "check-789",
    "current": 650,
    "total": 1000,
    "recentResults": HealthResult[]
  },
  "timestamp": "2025-01-27T10:30:00Z"
}

// 結果更新
{
  "type": "result_update",
  "data": {
    "proxyId": "proxy-123",
    "result": HealthResult
  },
  "timestamp": "2025-01-27T10:30:01Z"
}

// 統計更新
{
  "type": "statistics_update",
  "data": StatisticsData,
  "timestamp": "2025-01-27T10:30:02Z"
}
```

---

## 五、監控與指標設計

### 5.1 Prometheus 指標定義

基於 **Proxy_IP_驗證模組比較報告書** 的建議，設計以下監控指標：

```python
# 檔案導入相關指標
file_import_total = Counter(
    'proxy_file_import_total',
    'Total number of file imports',
    ['format', 'status']
)

file_import_duration = Histogram(
    'proxy_file_import_duration_seconds',
    'Time spent importing files',
    ['format']
)

file_import_records = Histogram(
    'proxy_file_import_records_total',
    'Number of records imported per file',
    ['format']
)

# 健康檢查相關指標
health_check_attempts = Counter(
    'proxy_health_check_attempts_total',
    'Total number of health check attempts',
    ['protocol', 'test_type']
)

health_check_duration = Histogram(
    'proxy_health_check_duration_seconds',
    'Time spent on health checks',
    ['protocol', 'test_type']
)

health_check_success_rate = Gauge(
    'proxy_health_check_success_rate',
    'Success rate of health checks',
    ['protocol', 'country']
)

proxy_response_time = Histogram(
    'proxy_response_time_milliseconds',
    'Proxy response time in milliseconds',
    ['protocol', 'country', 'anonymity']
)

proxy_health_score = Histogram(
    'proxy_health_score',
    'Proxy health score distribution',
    ['protocol', 'country']
)

# 系統性能指標
concurrent_checks = Gauge(
    'proxy_concurrent_checks_active',
    'Number of concurrent health checks running'
)

queue_size = Gauge(
    'proxy_check_queue_size',
    'Number of proxies waiting for health check'
)

memory_usage = Gauge(
    'proxy_system_memory_usage_bytes',
    'Memory usage of the proxy system'
)
```

### 5.2 Grafana 儀表板設計

#### 5.2.1 主要儀表板佈局
```
┌─────────────────────────────────────────────────────────────┐
│                    Proxies 管理測試儀表板                    │
├─────────────────────────────────────────────────────────────┤
│  📊 總覽統計                                                │
│  ┌─────────┬─────────┬─────────┬─────────┐                  │
│  │ 總檢測數 │ 成功率  │ 平均響應 │ 健康分數 │                  │
│  │ 10,000  │ 85.6%  │ 245ms  │ 82.3   │                  │
│  └─────────┴─────────┴─────────┴─────────┘                  │
├─────────────────────────────────────────────────────────────┤
│  📈 趨勢圖表                                                │
│  ┌─────────────────┬─────────────────────────────────────┐  │
│  │ 健康檢查成功率   │        響應時間分佈                  │  │
│  │ (時間序列)      │        (直方圖)                     │  │
│  └─────────────────┴─────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  🌍 地理分佈與協議分析                                       │
│  ┌─────────────────┬─────────────────────────────────────┐  │
│  │ 國家分佈圓餅圖   │        協議分佈長條圖                │  │
│  └─────────────────┴─────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ⚠️ 告警與異常                                              │
│  • 健康率低於 80% 的國家/協議                                │
│  • 響應時間超過 1000ms 的代理                               │
│  • 最近 1 小時失效的代理數量                                 │
└─────────────────────────────────────────────────────────────┘
```

#### 5.2.2 告警規則配置
```yaml
# 健康率告警
- alert: ProxyHealthRateLow
  expr: proxy_health_check_success_rate < 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "代理健康率過低"
    description: "{{ $labels.protocol }} 協議在 {{ $labels.country }} 的健康率為 {{ $value | humanizePercentage }}"

# 響應時間告警
- alert: ProxyResponseTimeSlow
  expr: histogram_quantile(0.95, proxy_response_time_milliseconds) > 2000
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "代理響應時間過慢"
    description: "95% 的代理響應時間超過 2 秒"

# 檢測失敗率告警
- alert: HealthCheckFailureRateHigh
  expr: rate(proxy_health_check_attempts_total{status="failed"}[5m]) / rate(proxy_health_check_attempts_total[5m]) > 0.2
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "健康檢查失敗率過高"
    description: "最近 5 分鐘的健康檢查失敗率為 {{ $value | humanizePercentage }}"

# 系統資源告警
- alert: SystemMemoryUsageHigh
  expr: proxy_system_memory_usage_bytes / (1024^3) > 8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "系統記憶體使用量過高"
    description: "系統記憶體使用量為 {{ $value | humanize }}GB"
```

---

## 六、安全性與性能考量

### 6.1 安全性設計

#### 6.1.1 檔案上傳安全
```typescript
interface FileUploadSecurity {
  // 檔案類型驗證
  allowedMimeTypes: ['application/json', 'text/csv', 'text/plain'];
  
  // 檔案大小限制
  maxFileSize: 10 * 1024 * 1024; // 10MB
  
  // 內容掃描
  scanForMaliciousContent: boolean;
  
  // 檔案隔離
  uploadDirectory: '/tmp/proxy-uploads';
  
  // 自動清理
  autoCleanupAfter: '24h';
}
```

#### 6.1.2 API 安全
```typescript
interface APISecurity {
  // 認證授權
  authentication: 'JWT' | 'API_KEY';
  
  // 請求頻率限制
  rateLimiting: {
    fileUpload: '5 requests/minute';
    healthCheck: '10 requests/minute';
    statistics: '60 requests/minute';
  };
  
  // 輸入驗證
  inputValidation: {
    sanitizeFileContent: boolean;
    validateProxyFormat: boolean;
    preventSQLInjection: boolean;
  };
  
  // 資料脫敏
  dataMasking: {
    hideProxyCredentials: boolean;
    logSanitization: boolean;
  };
}
```

### 6.2 性能優化策略

#### 6.2.1 併發控制
```python
class ConcurrencyManager:
    """併發控制管理器"""
    
    def __init__(self):
        self.max_concurrent_checks = 50
        self.semaphore = asyncio.Semaphore(self.max_concurrent_checks)
        self.rate_limiter = RateLimiter(requests_per_second=10)
    
    async def check_proxy_with_limit(self, proxy: ProxyItem) -> HealthResult:
        """帶限制的代理檢查"""
        async with self.semaphore:
            await self.rate_limiter.acquire()
            return await self.check_proxy(proxy)
```

#### 6.2.2 快取策略
```python
class CacheManager:
    """快取管理器"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = {
            'health_result': 3600,      # 1 小時
            'statistics': 300,          # 5 分鐘
            'geo_info': 86400,          # 24 小時
        }
    
    async def get_cached_result(self, proxy_id: str) -> Optional[HealthResult]:
        """獲取快取的檢測結果"""
        cached = await self.redis.get(f"health:{proxy_id}")
        if cached:
            return HealthResult.parse_raw(cached)
        return None
    
    async def cache_result(self, proxy_id: str, result: HealthResult):
        """快取檢測結果"""
        await self.redis.setex(
            f"health:{proxy_id}",
            self.cache_ttl['health_result'],
            result.json()
        )
```

#### 6.2.3 資料庫優化
```sql
-- 索引優化
CREATE INDEX CONCURRENTLY idx_proxy_items_status ON proxy_items(status);
CREATE INDEX CONCURRENTLY idx_proxy_items_protocol ON proxy_items(protocol);
CREATE INDEX CONCURRENTLY idx_proxy_items_country ON proxy_items(country);
CREATE INDEX CONCURRENTLY idx_health_results_checked_at ON health_results(checked_at);
CREATE INDEX CONCURRENTLY idx_health_results_health_score ON health_results(health_score);

-- 複合索引
CREATE INDEX CONCURRENTLY idx_proxy_items_status_protocol 
ON proxy_items(status, protocol);

CREATE INDEX CONCURRENTLY idx_health_results_proxy_status 
ON health_results(proxy_id, status, checked_at);
```

---

## 七、測試策略

### 7.1 單元測試

#### 7.1.1 檔案解析測試
```typescript
describe('FileParser', () => {
  it('should parse valid JSON file correctly', async () => {
    const jsonContent = JSON.stringify([
      { ip: '192.168.1.1', port: 8080, protocol: 'http' },
      { ip: '192.168.1.2', port: 3128, protocol: 'https' }
    ]);
    
    const result = await fileParser.parseJSON(jsonContent);
    
    expect(result.success).toBe(true);
    expect(result.data).toHaveLength(2);
    expect(result.data[0].ip).toBe('192.168.1.1');
  });
  
  it('should handle invalid CSV format gracefully', async () => {
    const csvContent = 'invalid,csv,format\nwithout,proper,headers';
    
    const result = await fileParser.parseCSV(csvContent);
    
    expect(result.success).toBe(false);
    expect(result.errors).toContain('Invalid CSV format');
  });
});
```

#### 7.1.2 健康檢查測試
```typescript
describe('HealthChecker', () => {
  it('should detect healthy proxy correctly', async () => {
    const proxy = {
      ip: '127.0.0.1',
      port: 8080,
      protocol: 'http'
    };
    
    // Mock successful response
    mockHttpClient.get.mockResolvedValue({
      status: 200,
      data: { origin: '127.0.0.1' },
      responseTime: 150
    });
    
    const result = await healthChecker.checkProxy(proxy);
    
    expect(result.status).toBe(HealthStatus.HEALTHY);
    expect(result.responseTime).toBe(150);
    expect(result.healthScore).toBeGreaterThan(80);
  });
  
  it('should handle timeout correctly', async () => {
    const proxy = {
      ip: '192.168.1.100',
      port: 8080,
      protocol: 'http'
    };
    
    // Mock timeout
    mockHttpClient.get.mockRejectedValue(new Error('TIMEOUT'));
    
    const result = await healthChecker.checkProxy(proxy);
    
    expect(result.status).toBe(HealthStatus.UNHEALTHY);
    expect(result.error).toContain('TIMEOUT');
  });
});
```

### 7.2 整合測試

#### 7.2.1 端到端測試
```typescript
describe('Proxies Management E2E', () => {
  it('should complete full import and health check workflow', async () => {
    // 1. 上傳檔案
    const uploadResponse = await request(app)
      .post('/api/proxies/import/upload')
      .attach('file', 'test-proxies.csv')
      .expect(200);
    
    const { uploadId } = uploadResponse.body.data;
    
    // 2. 確認導入
    const importResponse = await request(app)
      .post('/api/proxies/import/confirm')
      .send({ uploadId })
      .expect(200);
    
    const { importId } = importResponse.body.data;
    
    // 3. 等待導入完成
    await waitForImportCompletion(importId);
    
    // 4. 開始健康檢查
    const checkResponse = await request(app)
      .post('/api/proxies/health-check/batch')
      .send({
        proxyIds: ['all'],
        config: { timeout: 5, retries: 1, concurrency: 10 }
      })
      .expect(200);
    
    const { checkId } = checkResponse.body.data;
    
    // 5. 等待檢查完成
    await waitForHealthCheckCompletion(checkId);
    
    // 6. 驗證結果
    const resultsResponse = await request(app)
      .get(`/api/proxies/health-check/${checkId}/results`)
      .expect(200);
    
    expect(resultsResponse.body.data.results).toBeDefined();
    expect(resultsResponse.body.data.statistics.summary.total).toBeGreaterThan(0);
  });
});
```

### 7.3 性能測試

#### 7.3.1 負載測試
```javascript
// K6 負載測試腳本
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 },   // 逐漸增加到 10 個用戶
    { duration: '5m', target: 10 },   // 保持 10 個用戶 5 分鐘
    { duration: '2m', target: 50 },   // 增加到 50 個用戶
    { duration: '5m', target: 50 },   // 保持 50 個用戶 5 分鐘
    { duration: '2m', target: 0 },    // 逐漸減少到 0
  ],
};

export default function() {
  // 測試檔案上傳
  let uploadResponse = http.post('http://localhost:8000/api/proxies/import/upload', {
    file: http.file(open('test-proxies.csv', 'b'), 'test-proxies.csv', 'text/csv')
  });
  
  check(uploadResponse, {
    'upload status is 200': (r) => r.status === 200,
    'upload response time < 5s': (r) => r.timings.duration < 5000,
  });
  
  // 測試健康檢查
  let checkResponse = http.post('http://localhost:8000/api/proxies/health-check/batch', 
    JSON.stringify({
      proxyIds: ['proxy-1', 'proxy-2', 'proxy-3'],
      config: { timeout: 5, retries: 1, concurrency: 5 }
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(checkResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  sleep(1);
}
```

---

## 八、部署與維護

### 8.1 Docker 容器化

#### 8.1.1 前端 Dockerfile
```dockerfile
# 前端 Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 8.1.2 後端 Dockerfile
```dockerfile
# 後端 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 建立非 root 使用者
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 8.1.3 Docker Compose 配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5174:80"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE_URL=http://backend:8000

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/proxy_db
      - REDIS_URL=redis://redis:6379
      - PROMETHEUS_ENABLED=true
    volumes:
      - ./uploads:/app/uploads

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=proxy_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 8.2 CI/CD 管道

#### 8.2.1 GitHub Actions 工作流程
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run frontend tests
      run: |
        cd frontend
        npm run test
    
    - name: Build frontend
      run: |
        cd frontend
        npm run build
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        # 部署腳本
        echo "Deploying to production..."
```

### 8.3 監控與告警

#### 8.3.1 健康檢查端點
```python
@app.get("/health")
async def health_check():
    """系統健康檢查端點"""
    try:
        # 檢查資料庫連接
        await database.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    try:
        # 檢查 Redis 連接
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # 檢查系統資源
    memory_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent()
    
    status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status
        },
        "system": {
            "memory_usage_percent": memory_usage,
            "cpu_usage_percent": cpu_usage
        }
    }
```

#### 8.3.2 日誌配置
```python
# logging_config.py
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    """設定結構化日誌"""
    
    # JSON 格式化器
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    
    # 檔案處理器
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(json_formatter)
    
    # 根日誌器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 設定特定模組的日誌級別
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
```

---

## 九、結論與建議

### 9.1 設計總結

本設計報告書基於 **Proxy_IP_驗證模組比較報告書** 的深入分析，為 Proxies 管理測試頁面提供了完整的設計方案。主要特色包括：

#### 9.1.1 核心優勢
- **📁 靈活的檔案導入**：支援多種格式，智慧解析和驗證
- **🔍 全面的健康檢查**：多維度驗證，即時進度回饋
- **📊 豐富的統計分析**：視覺化儀表板，深度數據洞察
- **⚡ 高性能架構**：併發控制，快取優化，資源管理
- **🛡️ 安全可靠**：完整的安全防護，錯誤處理機制

#### 9.1.2 技術亮點
- **模組化設計**：清晰的分層架構，易於維護和擴展
- **即時監控**：基於 Prometheus + Grafana 的完整監控體系
- **容器化部署**：Docker + Docker Compose 一鍵部署
- **自動化測試**：完整的測試覆蓋，CI/CD 管道

### 9.2 實施建議

#### 9.2.1 開發優先級
1. **第一階段（2-3 週）**：
   - 實現基礎的檔案導入功能
   - 建立健康檢查核心引擎
   - 設計基本的統計儀表板

2. **第二階段（3-4 週）**：
   - 完善監控指標和告警系統
   - 優化性能和併發控制
   - 增加進階的統計分析功能

3. **第三階段（2-3 週）**：
   - 完善安全性和錯誤處理
   - 建立完整的測試覆蓋
   - 優化使用者體驗和介面設計

#### 9.2.2 技術選型建議
- **前端框架**：React + TypeScript + Vite
- **UI 組件庫**：Ant Design 或 Material-UI
- **圖表庫**：ECharts 或 Chart.js
- **狀態管理**：React Query + Zustand
- **後端框架**：FastAPI + SQLAlchemy + Alembic
- **資料庫**：PostgreSQL + Redis
- **監控**：Prometheus + Grafana
- **容器化**：Docker + Docker Compose

### 9.3 風險評估與緩解

#### 9.3.1 技術風險
- **併發性能瓶頸**：通過合理的併發控制和資源池管理緩解
- **大檔案處理**：實施分批處理和進度回饋機制
- **記憶體洩漏**：建立完善的資源清理和監控機制

#### 9.3.2 業務風險
- **檢測準確性**：建立多重驗證機制和品質評估標準
- **資料安全性**：實施完整的安全防護和存取控制
- **系統可用性**：建立健康檢查和自動恢復機制

### 9.4 未來擴展方向

#### 9.4.1 功能擴展
- **智慧推薦**：基於歷史數據的代理品質預測
- **自動化調度**：智慧的檢測任務調度和資源分配
- **多租戶支援**：支援多使用者和權限管理
- **API 整合**：提供 RESTful API 供第三方系統整合

#### 9.4.2 技術升級
- **微服務架構**：將單體應用拆分為微服務
- **雲原生部署**：支援 Kubernetes 和雲平台部署
- **機器學習**：引入 ML 模型進行代理品質預測
- **邊緣計算**：支援分散式檢測節點

---

**總結：** 本設計方案為 Proxies 管理測試頁面提供了完整、可行的實施藍圖。通過參考現有的驗證模組架構和最佳實踐，確保了系統的技術先進性和業務適用性。建議按照分階段的方式進行實施，優先實現核心功能，再逐步完善進階特性和優化性能。