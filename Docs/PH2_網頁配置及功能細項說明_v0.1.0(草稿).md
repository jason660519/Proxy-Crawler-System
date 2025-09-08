# PH2\_網頁配置及功能細項說明\_v0.1.0(草稿)

## 1. 文檔資訊

- 版本：v0.1.0 (草稿)
- 日期：2025-01-07
- 階段：PH2 開發與驗證
- 來源整合：
  - 《第三階段前端改善細部計畫報告\_第一集》
  - 《軟體專案全生命週期文檔命名規則》
  - 《代理伺服器管理系統 - 網頁配置及功能明細說明》

## 2. 目標與範圍

- 目標：統一 VS Code 風格前端的佈局、功能項、API 串接與驗收標準，形成可實作的 PH2 級規格。
- 範圍：首頁 Dashboard 與全域框架（Header/Activity Bar/Side Panel/Main/Status Bar）。不含帳號系統與深層管理頁之完整業務流程（另案）。

## 3. 命名與版本規範（摘要）

- 檔名結構：`[階段]_[主題]_[子領域(選)]_[版本/日期][(狀態)].md`
- 本文件命名：`PH2_網頁配置及功能細項說明_v0.1.0(草稿).md`
- 語言：繁中；英文化另存 `-en` 後綴。

## 4. 技術與環境配置

- 前端：React 18 + TypeScript + Vite、Tailwind/Headless UI、Zustand + React Query、React Router v6。
- 設計：VS Code 風格主題與 Codicons 圖標。
- 服務層：
  - `src/services/http.ts`：統一 axios 實例，讀 `VITE_API_BASE_URL`（預設 `http://localhost:8000`）。
  - `src/services/api.ts`：集中 API 封裝，完整型別。
- 啟動：
  - 前端：`npm ci && npm run dev -- --host`
  - 後端（Docker）：`docker compose -f JasonSpider/docker-compose.yml up -d --build`
- .env：`VITE_API_BASE_URL=http://localhost:8000`

## 5. 整體佈局（VS Code 風格）

- 固定區域：Title Bar、Menu Bar、Activity Bar、Side Panel、Main（Editor Group）、Panel（可選）、Status Bar。
- 尺寸（桌面）：
  - Activity Bar 48px（固定，圖標）
  - Side Panel 280px（可調 200–400px，可收合）
  - Status Bar 22px（固定）
- 佈局控制：快捷鍵（Ctrl+B、Ctrl+J）、拖拽分隔線、佈局記憶、全螢幕模式。

## 6. 首頁 Dashboard 功能清單與驗收

### 6.1 Header（搜尋與快捷）

- 搜尋列：代理/IP/國家/任務（先觸發查詢事件，mock）。
- 快速動作：新增任務、批次驗證、同步來源（Modal 占位）。
- 通知：錯誤/告警聚合，主題/語言切換。
- 驗收：可輸入查詢事件、動作按鈕與 Modal 顯示、通知徽章顯示。

### 6.2 Activity Bar（導航與狀態）

- 圖標：Dashboard / Proxies / ETL / Monitoring / Settings。
- 連線狀態點：API/Redis/Postgres 匯總，與 `/health`、`/etl/health` 同步。
- 驗收：圖標高亮與路由同步；狀態點依健康端點變化。

### 6.3 Side Panel（快速篩選與視圖）

- 快速篩選器：協議、國家、匿名等級、速度區間、狀態。
- Saved Views：保存/套用查詢（localStorage）。
- 最近任務/最近變更列表。
- 驗收：篩選事件影響主表格參數（先本地過濾，預留 API 參數）。

### 6.4 Main Content（四大區塊）

- 健康狀態卡片：主 API / ETL / Redis / Postgres。
- 趨勢圖：成功率、驗證量、平均延遲（先假資料）。
- 任務佇列板：排隊/執行/完成/失敗；重試/取消按鈕占位。
- 即時日誌：10s 輪詢，暫停/繼續、關鍵字高亮。
- 驗收：健康卡片反映 `/health`、`/etl/health`；三張趨勢圖渲染；任務板分組；日誌輪詢可控。

### 6.5 Status Bar（環境與統計）

- 顯示：`environment`、版本/延遲、背景作業與錯誤數、當前視圖統計（顯示數/總數）。
- 驗收：顯示最近一次 `/health` 耗時與環境資訊。

## 7. API 串接與資料策略

- 一律由前端透過 API 層呼叫；禁止直連 DB。
- 分頁/排序/篩選由伺服端支援，避免全量抓取。
- 輪詢採指數回退與中止控制；中長期升級 WebSocket/SSE。
- 熱資料後端 Redis 快取（TTL 30–120s）。
- 大批量操作走背景任務，前端展示任務狀態。
- 寫入冪等：樂觀鎖或 `updated_at` 欄位。

建議端點（提案）：

- GET `/proxies?status=&protocol=&country=&page=&size=`
- GET `/metrics/summary`
- GET `/tasks?status=&page=&size=`
- GET `/logs?source=&since=&limit=`
- POST `/tasks/{id}/retry`
- POST `/tasks/{id}/cancel`

索引建議（DB）：

- `proxies(status, protocol, country, last_checked)`
- `tasks(status, created_at)`
- `logs(source, timestamp)`

## 8. 型別與目錄規劃

- 組件拆分：`components/dashboard/*`、`components/status/*`
- 型別：`types/metrics.ts`、`types/tasks.ts`、`types/proxies.ts`
- 狀態：本地 state + hooks；視需引入 store
- 錯誤/重試：全域攔截器 + 統一通知

## 9. 驗收清單（MVP 摘要）

- Header 搜尋與快捷動作（mock）可用。
- Activity Bar 狀態點依健康端點變化。
- Side Panel 篩選影響主列表（本地過濾先行）。
- Main Content 四區塊渲染與輪詢（mock + 健康端點）。
- Status Bar 顯示環境、延遲、統計。
- API 層與型別齊備，`.env` 可切換後端位址。

## 10. 里程碑與時程（2 週，約 3 人）

- W1：UI/骨架/假資料；API 層完成；健康端點接上。
- W2：列表/篩選/日誌/任務板；體驗優化與驗收。

## 11. 風險與緩解

- 後端缺端點 → 先 mock，協議先行；預留轉接層。
- 大量資料性能 → 分頁 + 虛擬滾動；逐步引入伺服端分頁。
- 輪詢過頻 → 回退/節流；升級 WebSocket/SSE。
- 權限/安全 → 先封裝，待帳號系統導入再分級。

## 12. 後續擴充（摘要）

- Analytics 進階：多維度分析、地圖與圖表聯動、報表中心。
- 任務系統：模板、排程、即時監控與日誌聚合。
- 商業化：訂閱版位、API 金鑰與用量、SLA 指標看板。

---

附錄 A：實作參考（節錄）

1. 狀態管理結構（Zustand）

```typescript
interface AppStore {
  ui: {
    theme: "light" | "dark" | "highContrast";
    sidebarCollapsed: boolean;
    activeView: string;
  };
  proxy: ProxyStore;
  crawler: CrawlerStore;
  analytics: AnalyticsStore;
  user: UserStore;
}
```

2. 路由級懶加載

```typescript
const Dashboard = lazy(() => import("./pages/Dashboard"));
const ProxyPool = lazy(() => import("./pages/ProxyPool"));
```

3. 大列表虛擬化

```typescript
import { FixedSizeList as List } from "react-window";

const ProxyList = ({ proxies }: { proxies: any[] }) => (
  <List
    height={600}
    itemCount={proxies.length}
    itemSize={50}
    itemData={proxies}
  >
    {ProxyItem}
  </List>
);
```

4. 基本安全與審計

```bash
npm audit
npm audit fix
```

---

備註：本文件聚焦於 PH2 落地細項；更完整的長期規劃、商業模式與分析功能，請參考《網頁配置及功能明細說明》原始文件之 Phase/Roadmap 章節。
