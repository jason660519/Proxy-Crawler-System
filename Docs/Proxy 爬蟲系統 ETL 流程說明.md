# ETL Pipeline（URL2Parquet 中心設計）

本文說明本專案在第三階段的合理 ETL 設計，重心移轉至 URL2Parquet 管線，並保留代理驗證（Proxy Validation）流程。完整英文版參考 `Docs/ETL_Pipeline_Overview.md`。

- 主要服務：
  - 主後端（8000）: `/api/*`，健康檢查 `/health`，URL2Parquet 路由 `/api/url2parquet/*`
  - HTML→Markdown：標記為過渡相容層（將被 URL2Parquet 取代）
- 資料目錄（本地/容器掛載）：`data/url2parquet/{cache,jobs,outputs}`, `data/proxy_manager/*`, `logs/*`
- 監控：Prometheus/Grafana（延伸指標與面板），應新增 URL2Parquet 指標

---

## 1. URL2Parquet 管線（Extract → Transform → Output → Index）

```mermaid
graph TB
    A[Validate Input] --> B{Cache Hit?}
    B -- Yes --> H[Load result.json]
    B -- No --> C[Fetch HTML via httpx]
    C --> D[Extract/Engine Select]
    D --> E[Transform -> Markdown]
    E --> F[Output md/json | (parquet/csv 後續)]
    F --> G[Write result.json]
    H --> I[Return Job Result]
    G --> I
```

- Validate：URL 合法性、去重、選項標準化。
- Cache：以 `sha256(url + options)` 作為鍵；命中直接回應、並更新統計。
- Fetch：`httpx` + UA/逾時；必要時可引入 Playwright 作兜底（僅在需要）。
- Extract/Transform：以「smart」為預設，現階段產出 Markdown；將逐步擴充至 Parquet/CSV。
- Output/Index：寫出檔案與 `result.json` 摘要索引，回傳檔案清單。

### 1.1 API 端點（MVP）

- POST `/api/url2parquet/jobs`
  - Body: `{ "urls": ["https://..."], "output_formats": ["md","json"], ... }`
  - 回傳：`{ job_id, status }`
- GET `/api/url2parquet/jobs/{job_id}`
  - 回傳：`JobResult`（狀態、checksum、files 等）
- GET `/api/url2parquet/jobs/{job_id}/download`
  - 回傳：`{ files: [...] }`（檔案路徑清單）

PowerShell 範例：

```powershell
$body = '{"urls":["https://example.com"],"output_formats":["md","json"],"timeout_seconds":10}'
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/url2parquet/jobs' -ContentType 'application/json' -Body $body
```

### 1.2 儲存佈局（URL2Parquet）

```
data/
  url2parquet/
    cache/{checksum}/
      result.json
      content.parquet | content.json | content.md  # 依格式產出
    jobs/{job_id}/                 # 後續：任務歸檔
      results.json
      outputs/{timestamp}_{checksum8}.{ext}
    outputs/{checksum8}_content.{ext}  # MVP 直接輸出位置
```

`result.json`（示例）：

```json
{
  "url": "https://example.com",
  "files": [
    {
      "format": "md",
      "path": "data/url2parquet/outputs/abcd1234_content.md",
      "size": 1234
    },
    {
      "format": "json",
      "path": "data/url2parquet/outputs/abcd1234_content.json",
      "size": 567
    }
  ],
  "checksum": "sha256:...",
  "engine": "smart",
  "processing_time_ms": 2500
}
```

### 1.3 快取與鍵計算

- 鍵：`sha256(url + canonicalized_options)`，options 僅取影響內容的關鍵欄位（engine、formats、robots 等）。
- 命中策略：讀取 `cache/{checksum}/result.json` 並直接回應；記錄命中次數（待補指標）。

---

## 2. 代理驗證（Proxy Validation）流程（保留）

此流程維持原先架構：

```mermaid
graph TB
  P1[來源抓取] --> P2[標準化]
  P2 --> P3[掃描/驗證(連通/速度/匿名/地理)]
  P3 --> P4[評分/分類(熱/溫/冷/黑)]
  P4 --> P5[Load -> DB/Redis]
  P5 --> P6[報表/可視化]
```

- Extract：從多來源獲取代理（ProxyScrape、GitHub、Shodan、Censys 等）。
- Transform：欄位標準化（IP、Port、Protocol、Country、Anonymity、Speed）。
- Validate：`scanner` + `validator`，輸出狀態與分數。
- Load：寫入 DB/Redis，供 API 與前端即時使用；產出報表。

目錄與產出（既有）：

- 驗證結果：`data/validated/{source}_{timestamp}.json`
- 報表：`data/reports/{source}_{timestamp}_proxies.md`

---

## 3. 監控與日誌

- URL2Parquet 指標（建議）：QPS、P50/P95、成功/失敗、重試、快取命中率、引擎用量。
- Proxy 驗證指標：掃描量、活躍率、國別分布、匿名性分布、成功率曲線。
- 日誌：結構化 JSON，包含 `job_id/url/phase/duration/status`；存放 `logs/{date}.log`。
- 錯誤處理：Fetch/Transform/Output 各階段具重試與降級策略（例如引擎回退）。

---

## 4. 後續里程碑

- URL2Parquet：
  - 增加 Parquet/CSV 實輸出（PyArrow/Pandas），與 `jobs/{job_id}` 歸檔。
  - 任務化/SSE 進度事件、批次處理與並行度控制。
  - 指標上報與 Grafana 面板。
- Proxy 驗證：
  - 掃描器性能優化與智能目標發現；質量評估報表強化。
