# Proxies 頁面細部設計規劃書

**專案名稱：** Proxy-Crawler-System  
**頁面路徑：** http://localhost:5174/proxies  
**文件版本：** 1.0  
**建立日期：** 2025-01-27  
**負責模組：** ProxyManagement.tsx  

---

## 1. 頁面概覽 (Page Overview)

### 1.1 功能定位
Proxies 頁面是代理爬蟲管理系統的核心功能模組，負責代理伺服器的完整生命週期管理，包括新增、編輯、測試、監控和批量操作等功能。

### 1.2 主要職責
- **代理節點管理**：提供代理的 CRUD 操作
- **狀態監控**：即時顯示代理的健康狀態和性能指標
- **批量操作**：支援多選代理進行批量測試、刪除等操作
- **篩選與搜尋**：提供多維度的代理篩選和搜尋功能
- **數據視覺化**：以表格和統計卡片形式展示代理資訊

### 1.3 使用者角色
- **系統管理員**：完整的代理管理權限
- **運維人員**：代理監控和基本操作權限
- **開發人員**：代理測試和查看權限

---

## 2. 技術架構 (Technical Architecture)

### 2.1 組件層次結構
```
ProxyManagement (主容器)
├── 統計卡片區域
│   ├── StatCard (總數統計)
│   ├── StatCard (活躍代理)
│   ├── StatCard (健康分數)
│   └── StatCard (平均響應時間)
├── 操作工具列
│   ├── SearchBox (搜尋框)
│   ├── FilterDropdown (篩選器)
│   ├── ActionButtons (操作按鈕)
│   └── ViewToggle (視圖切換)
├── 代理列表區域
│   ├── ProxyTable (主要表格)
│   ├── Pagination (分頁控制)
│   └── BulkActions (批量操作)
└── 模態視窗
    ├── ProxyFormModal (新增/編輯)
    ├── TestResultModal (測試結果)
    └── ConfirmModal (確認對話框)
```

### 2.2 狀態管理架構
```typescript
interface ProxyManagementState {
  // 數據狀態
  proxies: ProxyNode[];
  selectedProxies: string[];
  total: number;
  totalCount: number;
  
  // UI 狀態
  loading: boolean;
  error?: string;
  
  // 篩選與分頁
  filters: ProxyFilters;
  pagination: PaginationState;
  
  // 模態視窗狀態
  showAddModal: boolean;
  showEditModal: boolean;
  editingProxy?: ProxyNode;
}
```

### 2.3 API 整合
- **基礎 API**：`/api/proxies`
- **統計 API**：`/api/proxies/statistics`
- **測試 API**：`/api/proxies/{id}/test`
- **批量操作 API**：`/api/proxies/bulk`
- **匯入/匯出 API**：`/api/proxies/import`, `/api/proxies/export`

---

## 3. 使用者介面設計 (UI Design)

### 3.1 頁面佈局

#### 3.1.1 頂部統計區域 (Statistics Section)
```
┌─────────────────────────────────────────────────────────────┐
│  📊 總代理數    🟢 活躍代理    ❤️ 健康分數    ⚡ 平均響應   │
│     1,234         856          85.2%         245ms      │
└─────────────────────────────────────────────────────────────┘
```

#### 3.1.2 操作工具列 (Toolbar Section)
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 [搜尋框]  📋 [篩選] 📥 [匯入] 📤 [匯出] ➕ [新增代理]   │
└─────────────────────────────────────────────────────────────┘
```

#### 3.1.3 主要表格區域 (Table Section)
```
┌─────────────────────────────────────────────────────────────┐
│ ☑️ │ 狀態 │ IP地址:端口 │ 協議 │ 國家 │ 健康分數 │ 響應時間 │ 操作 │
├─────────────────────────────────────────────────────────────┤
│ ☑️ │ 🟢   │ 1.2.3.4:8080│ HTTP │ 美國 │   92%   │  156ms │ ⚙️  │
│ ☑️ │ 🔴   │ 5.6.7.8:3128│HTTPS │ 日本 │   45%   │  892ms │ ⚙️  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 互動元素設計

#### 3.2.1 狀態指示器
- **🟢 Active (活躍)**：綠色圓點，代理正常運作
- **🔴 Error (錯誤)**：紅色圓點，代理無法連接
- **🟡 Testing (測試中)**：黃色圓點，正在進行連接測試
- **⚪ Inactive (非活躍)**：灰色圓點，代理已停用

#### 3.2.2 操作按鈕
- **主要操作**：新增代理 (Primary Button)
- **次要操作**：匯入、匯出 (Secondary Button)
- **行內操作**：編輯、測試、刪除 (Icon Button)
- **批量操作**：測試選中、刪除選中 (Batch Action Button)

#### 3.2.3 篩選器設計
```typescript
interface FilterOptions {
  status: ProxyStatus[];     // 狀態篩選
  protocol: ProxyProtocol[]; // 協議篩選
  country: string[];         // 國家篩選
  anonymity: AnonymityLevel[]; // 匿名等級篩選
  speedRange: [number, number]; // 響應時間範圍
  healthScore: { min: number; max: number }; // 健康分數範圍
}
```

---

## 4. 功能規格 (Functional Specifications)

### 4.1 核心功能

#### 4.1.1 代理列表顯示
- **分頁載入**：支援伺服器端分頁，預設每頁 20 筆
- **排序功能**：支援按狀態、響應時間、健康分數等欄位排序
- **即時更新**：每 30 秒自動刷新代理狀態
- **響應式設計**：適配不同螢幕尺寸

#### 4.1.2 代理管理操作

**新增代理**
```typescript
interface ProxyFormData {
  ip: string;                    // IP 地址 (必填)
  port: number;                  // 端口號 (必填)
  protocol: ProxyProtocol;       // 協議類型 (必填)
  username?: string;             // 用戶名 (選填)
  password?: string;             // 密碼 (選填)
  country?: string;              // 國家 (選填)
  city?: string;                 // 城市 (選填)
  anonymity?: AnonymityLevel;    // 匿名等級 (選填)
  tags?: string[];               // 標籤 (選填)
}
```

**編輯代理**
- 支援修改代理的基本資訊和配置
- 即時驗證輸入格式
- 支援批量編輯標籤

**刪除代理**
- 單個刪除：確認對話框
- 批量刪除：支援多選刪除
- 軟刪除：標記為已刪除，保留歷史記錄

#### 4.1.3 代理測試功能

**單個測試**
```typescript
interface ProxyTestConfig {
  testUrl: string;      // 測試 URL
  timeout: number;      // 超時時間 (秒)
  retries: number;      // 重試次數
}
```

**批量測試**
- 支援同時測試多個代理
- 顯示測試進度條
- 即時更新測試結果

**測試結果顯示**
```typescript
interface TestResult {
  proxyId: string;
  success: boolean;
  responseTime?: number;
  error?: string;
  testedAt: string;
}
```

### 4.2 進階功能

#### 4.2.1 智慧篩選
- **快速篩選**：預設篩選條件 (活躍代理、高速代理等)
- **自訂篩選**：支援多條件組合篩選
- **儲存篩選**：常用篩選條件可儲存為預設

#### 4.2.2 數據匯入匯出
- **匯入格式**：支援 CSV、JSON 格式
- **匯出格式**：支援 CSV、JSON、Excel 格式
- **批量匯入**：支援大量代理資料匯入
- **匯出篩選**：可匯出篩選後的代理列表

#### 4.2.3 監控與告警
- **健康監控**：定期檢查代理健康狀態
- **性能監控**：追蹤響應時間趨勢
- **告警通知**：代理失效時發送通知

---

## 5. 數據模型 (Data Models)

### 5.1 核心數據結構

```typescript
// 代理節點模型
interface ProxyNode {
  id: string;                    // 唯一識別碼
  ip: string;                    // IP 地址
  port: number;                  // 端口號
  protocol: ProxyProtocol;       // 協議類型
  country?: string;              // 國家
  countryCode?: string;          // 國家代碼
  city?: string;                 // 城市
  anonymity: AnonymityLevel;     // 匿名等級
  status: ProxyStatus;           // 當前狀態
  responseTime?: number;         // 響應時間 (毫秒)
  lastChecked?: string;          // 最後檢查時間
  uptime?: number;               // 正常運行時間百分比
  source?: string;               // 來源網站
  maxConcurrent?: number;        // 最大併發數
  timeout?: number;              // 超時時間
  enabled?: boolean;             // 是否啟用
  username?: string;             // 用戶名
  password?: string;             // 密碼
  url?: string;                  // 完整代理 URL
  healthScore?: number;          // 健康分數 (0-100)
  tags?: string[];               // 標籤
  createdAt: string;             // 建立時間
  updatedAt: string;             // 更新時間
}

// 代理狀態枚舉
enum ProxyStatus {
  ACTIVE = 'active',       // 活躍
  INACTIVE = 'inactive',   // 非活躍
  TESTING = 'testing',     // 測試中
  ERROR = 'error',         // 錯誤
  UNKNOWN = 'unknown'      // 未知
}

// 代理協議枚舉
enum ProxyProtocol {
  HTTP = 'http',
  HTTPS = 'https',
  SOCKS4 = 'socks4',
  SOCKS5 = 'socks5'
}

// 匿名等級枚舉
enum AnonymityLevel {
  TRANSPARENT = 'transparent',  // 透明
  ANONYMOUS = 'anonymous',      // 匿名
  ELITE = 'elite'              // 精英
}
```

### 5.2 統計數據模型

```typescript
interface ProxyStatistics {
  total: number;                    // 總代理數
  active: number;                   // 活躍代理數
  inactive: number;                 // 非活躍代理數
  error: number;                    // 錯誤代理數
  averageResponseTime: number;      // 平均響應時間
  averageHealthScore: number;       // 平均健康分數
  byProtocol: Record<string, number>; // 按協議分組統計
  byCountry: Record<string, number>;  // 按國家分組統計
  byAnonymity: Record<string, number>; // 按匿名等級分組統計
}
```

---

## 6. API 介面規格 (API Specifications)

### 6.1 RESTful API 端點

#### 6.1.1 代理列表查詢
```http
GET /api/proxies
Query Parameters:
  - page: number (頁碼，預設 1)
  - limit: number (每頁筆數，預設 20)
  - sortBy: string (排序欄位)
  - sortOrder: 'asc' | 'desc' (排序方向)
  - status: ProxyStatus[] (狀態篩選)
  - protocol: ProxyProtocol[] (協議篩選)
  - country: string[] (國家篩選)
  - search: string (搜尋關鍵字)
  - minSpeed: number (最小響應速度)
  - maxSpeed: number (最大響應速度)

Response:
{
  "success": true,
  "data": ProxyNode[],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 1234,
    "totalPages": 62
  }
}
```

#### 6.1.2 代理詳情查詢
```http
GET /api/proxies/{id}

Response:
{
  "success": true,
  "data": ProxyNode
}
```

#### 6.1.3 新增代理
```http
POST /api/proxies
Content-Type: application/json

Body:
{
  "ip": "192.168.1.1",
  "port": 8080,
  "protocol": "http",
  "username": "user",
  "password": "pass",
  "country": "Taiwan",
  "tags": ["high-speed", "reliable"]
}

Response:
{
  "success": true,
  "data": ProxyNode,
  "message": "代理新增成功"
}
```

#### 6.1.4 更新代理
```http
PUT /api/proxies/{id}
Content-Type: application/json

Body: Partial<ProxyNode>

Response:
{
  "success": true,
  "data": ProxyNode,
  "message": "代理更新成功"
}
```

#### 6.1.5 刪除代理
```http
DELETE /api/proxies/{id}

Response:
{
  "success": true,
  "message": "代理刪除成功"
}
```

#### 6.1.6 代理測試
```http
POST /api/proxies/{id}/test
Content-Type: application/json

Body:
{
  "testUrl": "http://httpbin.org/ip",
  "timeout": 10
}

Response:
{
  "success": true,
  "data": {
    "proxyId": "proxy-123",
    "success": true,
    "responseTime": 245,
    "testedAt": "2025-01-27T10:30:00Z"
  }
}
```

#### 6.1.7 批量操作
```http
POST /api/proxies/bulk
Content-Type: application/json

Body:
{
  "operation": "test",
  "proxyIds": ["proxy-1", "proxy-2"],
  "options": {
    "testUrl": "http://httpbin.org/ip",
    "timeout": 10
  }
}

Response:
{
  "success": true,
  "data": {
    "total": 2,
    "processed": 2,
    "failed": 0,
    "results": [TestResult[]]
  }
}
```

#### 6.1.8 統計資料
```http
GET /api/proxies/statistics

Response:
{
  "success": true,
  "data": ProxyStatistics
}
```

### 6.2 WebSocket 即時更新

```typescript
// WebSocket 連接
const ws = new WebSocket('ws://localhost:8000/ws/proxies');

// 訊息格式
interface WSMessage {
  type: 'proxy_update' | 'proxy_test_result' | 'statistics_update';
  data: any;
  timestamp: string;
}

// 代理狀態更新
{
  "type": "proxy_update",
  "data": {
    "proxyId": "proxy-123",
    "status": "active",
    "responseTime": 156,
    "healthScore": 92
  },
  "timestamp": "2025-01-27T10:30:00Z"
}
```

---

## 7. 使用者體驗設計 (UX Design)

### 7.1 互動流程

#### 7.1.1 新增代理流程
1. 點擊「新增代理」按鈕
2. 開啟代理表單模態視窗
3. 填寫必要資訊 (IP、端口、協議)
4. 選填其他資訊 (用戶名、密碼、標籤等)
5. 點擊「測試連接」驗證代理可用性
6. 確認無誤後點擊「儲存」
7. 關閉模態視窗，刷新代理列表

#### 7.1.2 批量測試流程
1. 勾選要測試的代理
2. 點擊「批量測試」按鈕
3. 顯示測試進度條
4. 即時更新測試結果
5. 完成後顯示測試摘要

#### 7.1.3 篩選操作流程
1. 點擊篩選按鈕
2. 選擇篩選條件
3. 即時更新列表內容
4. 可儲存常用篩選條件

### 7.2 錯誤處理

#### 7.2.1 網路錯誤
- 顯示友善的錯誤訊息
- 提供重試按鈕
- 自動重連機制

#### 7.2.2 驗證錯誤
- 即時表單驗證
- 清楚的錯誤提示
- 高亮錯誤欄位

#### 7.2.3 操作失敗
- Toast 通知顯示錯誤
- 詳細錯誤資訊
- 建議解決方案

### 7.3 載入狀態

#### 7.3.1 頁面載入
- 骨架屏 (Skeleton) 顯示
- 載入進度指示
- 分段載入優化

#### 7.3.2 操作載入
- 按鈕載入狀態
- 禁用重複操作
- 載入動畫效果

---

## 8. 性能優化 (Performance Optimization)

### 8.1 前端優化

#### 8.1.1 虛擬滾動
- 大量數據時使用虛擬滾動
- 減少 DOM 節點數量
- 提升滾動性能

#### 8.1.2 分頁載入
- 伺服器端分頁
- 預載入下一頁
- 無限滾動選項

#### 8.1.3 快取策略
- 代理列表快取
- 統計資料快取
- 智慧快取失效

### 8.2 後端優化

#### 8.2.1 資料庫索引
- IP 地址索引
- 狀態索引
- 複合索引優化

#### 8.2.2 查詢優化
- 分頁查詢優化
- 篩選條件優化
- 統計查詢快取

#### 8.2.3 併發處理
- 批量操作併發控制
- 代理測試併發限制
- 資源池管理

---

## 9. 安全性考量 (Security Considerations)

### 9.1 資料安全

#### 9.1.1 敏感資料保護
- 代理密碼加密儲存
- 傳輸過程 HTTPS 加密
- 敏感資料脫敏顯示

#### 9.1.2 存取控制
- 基於角色的權限控制
- API 端點權限驗證
- 操作日誌記錄

### 9.2 輸入驗證

#### 9.2.1 前端驗證
- IP 地址格式驗證
- 端口範圍驗證
- XSS 防護

#### 9.2.2 後端驗證
- 參數類型驗證
- SQL 注入防護
- 請求頻率限制

---

## 10. 測試策略 (Testing Strategy)

### 10.1 單元測試

#### 10.1.1 組件測試
```typescript
// ProxyManagement 組件測試
describe('ProxyManagement', () => {
  it('should render proxy list correctly', () => {
    // 測試代理列表渲染
  });
  
  it('should handle proxy creation', () => {
    // 測試代理新增功能
  });
  
  it('should handle bulk operations', () => {
    // 測試批量操作功能
  });
});
```

#### 10.1.2 API 測試
```typescript
// API 端點測試
describe('Proxy API', () => {
  it('should get proxies with pagination', async () => {
    // 測試分頁查詢
  });
  
  it('should create proxy successfully', async () => {
    // 測試代理新增
  });
  
  it('should test proxy connection', async () => {
    // 測試代理連接
  });
});
```

### 10.2 整合測試

#### 10.2.1 端到端測試
```typescript
// E2E 測試場景
describe('Proxy Management E2E', () => {
  it('should complete proxy management workflow', () => {
    // 完整的代理管理流程測試
    cy.visit('/proxies');
    cy.get('[data-testid="add-proxy-btn"]').click();
    cy.get('[data-testid="ip-input"]').type('192.168.1.1');
    cy.get('[data-testid="port-input"]').type('8080');
    cy.get('[data-testid="save-btn"]').click();
    cy.get('[data-testid="proxy-list"]').should('contain', '192.168.1.1');
  });
});
```

### 10.3 性能測試

#### 10.3.1 載入測試
- 大量代理數據載入測試
- 分頁性能測試
- 篩選響應時間測試

#### 10.3.2 壓力測試
- 併發用戶測試
- 批量操作壓力測試
- 記憶體使用測試

---

## 11. 部署與維護 (Deployment & Maintenance)

### 11.1 部署配置

#### 11.1.1 環境變數
```bash
# 前端環境變數
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENABLE_MOCK=false

# 後端環境變數
DATABASE_URL=postgresql://user:pass@localhost:5432/proxy_db
REDIS_URL=redis://localhost:6379
API_SECRET_KEY=your-secret-key
```

#### 11.1.2 Docker 配置
```dockerfile
# 前端 Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 5174
CMD ["npm", "run", "preview"]
```

### 11.2 監控與日誌

#### 11.2.1 應用監控
- 頁面載入時間監控
- API 響應時間監控
- 錯誤率監控

#### 11.2.2 業務監控
- 代理測試成功率
- 用戶操作統計
- 系統資源使用

---

## 12. 未來擴展 (Future Enhancements)

### 12.1 功能擴展

#### 12.1.1 智慧推薦
- 基於使用歷史推薦代理
- 智慧代理輪換
- 性能預測分析

#### 12.1.2 自動化管理
- 自動代理發現
- 智慧故障轉移
- 自動性能優化

### 12.2 技術升級

#### 12.2.1 架構優化
- 微服務架構遷移
- GraphQL API 支援
- 邊緣計算整合

#### 12.2.2 使用者體驗
- PWA 支援
- 離線功能
- 多語言支援

---

## 13. 結論 (Conclusion)

本設計規劃書詳細定義了 Proxies 頁面的完整實現方案，涵蓋了從技術架構到使用者體驗的各個層面。通過模組化的設計和完善的 API 整合，該頁面將為使用者提供強大而直觀的代理管理功能。

### 13.1 關鍵特色
- **完整的代理生命週期管理**
- **即時狀態監控和更新**
- **強大的篩選和搜尋功能**
- **批量操作支援**
- **響應式設計和優秀的使用者體驗**

### 13.2 技術亮點
- **TypeScript 強型別支援**
- **React Hooks 狀態管理**
- **RESTful API 設計**
- **WebSocket 即時通訊**
- **完善的錯誤處理和載入狀態**

### 13.3 品質保證
- **全面的測試覆蓋**
- **性能優化策略**
- **安全性考量**
- **可維護的代碼結構**

這個設計方案為 Proxy-Crawler-System 的核心功能提供了堅實的基礎，確保系統能夠滿足當前需求並具備良好的擴展性。