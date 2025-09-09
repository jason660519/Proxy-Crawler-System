# URL2Parquet 整合工作細部計畫（Integrated Work Plan）

文件版本：v1.0  
最後更新：2025-09-09  
狀態：執行計畫（可立即開工）

---

## 1. 目標與範圍（Goals & Scope）

- 將「URL → HTML → 內容提取 → Markdown/JSON → CSV/Parquet」建置為統一、可觀測的管線。
- 前端提供四步驟 Wizard 體驗，後端提供任務化 API（提交/狀態/日誌/下載）。
- 維持與現有 `html_to_markdown` 服務的相容層，逐步替換並最終收斂為 `url2parquet`。

非目標：爬蟲代理管理、JS 重渲染通用解決方案（可由 Playwright 作為兜底策略按需啟用）。

---

## 2. 來源文件整合結論（Valid vs. Adjusted）

- 有效（保留/採納）

  - 前端四步 Wizard（URL 輸入 → 高級選項 → 進度/日誌 → 預覽/下載）。
  - 後端任務化 API（`/api/url2parquet/jobs*`）、SSE/WebSocket 進度事件。
  - 模組化核心：`fetch`、`extract`、`transform`、`output`、`core(pipeline/cache/events)`。
  - 緩存策略：`sha256(url + canonicalized_options)`，檔案系統為主、可選對象儲存同步。
  - Parquet 為主輸出；統一 JSON schema；配置參數（提取模式/壓縮/並行度等）。

- 調整（簡化/落地）
  - 模組粒度：保留清晰分層，但避免過度拆分；以「可測試、可替換」為界。
  - 兼容層：以 Adapter 包裝既有 `html_to_markdown`，避免雙軌維護。
  - API 命名：統一掛載於 `Main API` 下（例如 `/api/url2parquet/...`），不另開服務優先。

---

## 3. 目錄與檔案結構（Proposed Layout）

```
src/
  url2parquet/
    __init__.py
    config.py              # PipelineOptions/環境參數
    types.py               # Result/事件/錯誤型別
    errors.py
    checksum.py
    fetch/http_client.py
    extract/base.py
    extract/trafilatura_engine.py
    extract/fallback_engine.py
    transform/markdown_converter.py
    transform/cleaners.py
    transform/normalizer.py
    output/parquet.py
    output/csv.py
    output/json.py
    output/markdown.py
    core/engine_selector.py
    core/pipeline.py       # 任務流程、事件派發、緩存/重試/統計
    core/cache.py          # FS cache +（可選）索引
    core/events.py         # SSE/WebSocket 事件模型
    api/router.py          # FastAPI Router（/api/url2parquet/...）
```

前端：

```
frontend/src/
  pages/UrlToParquetWizard.tsx
  api/url2parquetApi.ts          # jobs/status/logs/download 封裝
  hooks/useUrl2Parquet.ts        # 任務狀態、SSE 訂閱
  components/url2parquet/
    AdvancedOptionsPanel.tsx
    JobProgressPanel.tsx
    ResultPreview.tsx
```

---

## 4. 後端實作計畫（API、Pipeline、Schema、Cache）

### 4.1 API 端點

- POST `/api/url2parquet/jobs`：建立任務（單/多 URL；可接受文字檔上傳）。
- GET `/api/url2parquet/jobs/{job_id}`：查詢任務狀態（`queued|processing|completed|failed|canceled`）。
- GET `/api/url2parquet/jobs/{job_id}/logs`：SSE 串流日誌/事件（`phase_update/progress/log`）。
- GET `/api/url2parquet/jobs/{job_id}/download?format=parquet|csv|json|md`：下載產出。

設計要點：

- 任務 ID 採用 `job_{epoch_ms}_{rand}`，避免碰撞，便於追蹤。
- 請求體包含 `PipelineOptions`（輸出格式、提取模式、壓縮、並行度、work_dir 等）。
- 回應中返回 `job_id` 與初始狀態；長任務用 SSE，短任務可輪詢。

### 4.2 Pipeline 邏輯

步驟：`validate_input → cache_lookup → fetch → extract → transform → output → index_result`

- Validate：URL 格式、重複去重；robots.txt 選項（預設遵循）。
- Cache：以 checksum 為目錄鍵；命中直接回應並登記命中統計。
- Fetch：`httpx`（逾時/重試/UA/代理可選）；對同 host 節流並行度。
- Extract：引擎選擇器（`smart|trafilatura|full_html`）；失敗時降級回退。
- Transform：HTML→Markdown（`markdownify` 預設）、清洗廣告/導航、正規化欄位。
- Output：依需求輸出 Parquet/CSV/JSON/MD；產出索引寫入 `result.json`。
- Events：各階段派發事件（進度/分位數延遲/錯誤碼），供 SSE 與 Prometheus 收集。

### 4.3 資料結構（核心 Schema）

Result（摘要）：

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "language": "en",
  "files": [
    {
      "format": "parquet",
      "path": "/.../content.parquet",
      "size": 12345,
      "rows": 1
    }
  ],
  "checksum": "sha256:...",
  "engine": "smart",
  "processing_time_ms": 2500
}
```

Parquet（PyArrow）：`url,title,language,markdown,content_length,fetched_at,engine,checksum,warnings[],extra{author,publish_date,keywords[]}`。

### 4.4 緩存與儲存（Storage Layout）

```
work_dir/
  cache/{checksum}/
    result.json
    content.parquet | content.json | content.md
  jobs/{job_id}/
    results.json
    outputs/{timestamp}_{checksum8}.{format}
  reports/{date}/summary_{timestamp}.json
```

策略：

- 先本地檔案系統；必要時增加索引檔（最近 N 次、大小、行數）。
- 提供工具將 `cache/` 與 `jobs/` 同步至 S3/GCS（選配）。

### 4.5 相容層（與 `html_to_markdown`）

- 建立 Adapter：`HtmlToMarkdownAdapter` 封裝現有 API 與模型，作為 transform 的一種引擎。
- 在 `url2parquet` 完整穩定前，同時支援原路徑端點（低風險漸進遷移）。

---

## 5. 前端實作計畫（Wizard、元件、路由、預覽）

### 5.1 路由與導覽

- 在 `ActivityBar` 新增入口：`URL 轉換`（路由：`/url2parquet`）。
- 新頁面 `UrlToParquetWizard` 四步：輸入 → 高級選項 → 進度 → 結果。

### 5.2 關鍵元件

- `AdvancedOptionsPanel`：輸出格式、提取模式、清洗、Parquet 壓縮與分區。
- `JobProgressPanel`：總體進度條、事件時間線、日誌（SSE 訂閱）。
- `ResultPreview`：
  - 表格（CSV/Parquet 摘要，虛擬清單 + 分頁）。
  - JSON、Markdown 預覽（可折疊/複製）。
  - 下載按鈕（依格式顯示）。

### 5.3 前端 API 與 Hook

- `frontend/src/api/url2parquetApi.ts`：封裝 `createJob/getStatus/getLogs/download`。
- `useUrl2Parquet`：管理任務生命週期、SSE 訂閱、自動重試與取消。

可及性與國際化：保留 aria-label、鍵盤可達；沿用現有 i18n 機制（如有）。

---

## 6. 可觀測性與營運（Observability & Ops）

- 指標：QPS、P50/P95 延遲、成功/失敗率、重試次數、緩存命中率、引擎使用比。
- 日誌：結構化（JSON），包含 job_id/phase/url/耗時/錯誤碼；前端可串流查看。
- 事件：`queued/started/phase_update/progress/log/completed/failed`。
- 儀表板：沿用現有 Prometheus/Grafana 佈署；新增 url2parquet 面板。

---

## 7. 測試計畫（Testing）

- 單元測試：fetch/extract/transform/output/core/cache/errors。
- 整合測試：單 URL 與批次；命中/未命中緩存；各引擎回退；大檔案。
- 相容測試：`html_to_markdown` 舊輸出對比；API 參數相容驗證。
- 性能測試：并行度掃描、冷/熱緩存、長時穩定性；磁碟 I/O 壓力。
- Windows 本地驗證：PowerShell 指令與路徑相容性。

---

## 8. 部署與本地操作（Windows/PowerShell 友善）

- 依賴：`httpx|requests, markdownify, pyarrow, pydantic, (opt) trafilatura, bs4, lxml, pandas`。
- 本地（PowerShell 示例）：

```powershell
# 建議在專案根目錄執行
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 啟動後端（包含 url2parquet 路由）
python run_server.py

# 前端開發伺服器
cd frontend
npm run dev
```

- Docker Compose：沿用既有架構，追加 url2parquet 組件或僅增路由；資料目錄掛載 `./data:/app/data`。

---

## 9. 里程碑與時程（Milestones）

1. 週 1：核心管線 MVP（單 URL、Parquet/JSON、FS 緩存、CLI/API 雛形）。
2. 週 2：批次處理與并行、CSV/Markdown、trafilatura 可選；前端 Wizard 基礎。
3. 週 3：任務化 API 完整（SSE/下載）；前端預覽/下載；相容層落地。
4. 週 4：測試覆蓋、性能優化、Grafana 面板、文件與示例。

---

## 10. 風險與緩解（Risks & Mitigations）

- 提取品質波動：多引擎回退、站點規則、人工標註回饋。
- 高并發瓶頸：host 節流、連線池/逾時優化、批次拆分、降級策略。
- 儲存成本：TTL、壓縮、冷/熱分層；外部物件存儲同步（選配）。
- JS 強依賴頁面：以 Playwright 作兜底，僅在必要時啟用。

---

## 11. 驗收標準（Acceptance Criteria）

- 單 URL 2 秒內完成（熱緩存）；冷路徑 P95 < 5 秒（一般頁面）。
- 前端可視化流程完整可用；下載四種格式可用；SSE 事件正常。
- 兼容層路徑穩定，既有使用者不需改動即可過渡。

---

## 12. 交付物（Deliverables）

- 後端：`src/url2parquet/*`、FastAPI Router、整合到主 API、Prom 指標、文件。
- 前端：Wizard/Options/Progress/Preview 元件與 API 封裝、路由與導覽。
- 運維：Grafana 面板、部署說明、PowerShell 指令手冊。
