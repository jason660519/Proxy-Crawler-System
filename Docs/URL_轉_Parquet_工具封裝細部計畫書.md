# URL 轉 Parquet 工具封裝細部計畫書

**文件版本**：v0.1 (草案)  
**專案代號**：`url2parquet`  
**最後更新**：2025-09-09 (Australia/Sydney)  
**狀態**：設計審閱中（可供 PoC 實作）

---

## 1. 摘要（Executive Summary）
`url2parquet` 是一個以 **Python** 為主的模組化工具包與服務，將 **URL → HTML → 主要內容抽取 → Markdown/結構化資料 → Parquet/CSV/JSON** 的流程**標準化、可觀測、可擴展**。它提供：
- **CLI**（單一/批次）
- **Python API**（函式呼叫）
- **FastAPI**（網路服務/任務化）

核心能力：
- 跨站適配的**內容提取引擎**（預設輕量、可切換 trafilatura）
- **緩存機制**（URL×Options 指紋；去重省資源）
- **并行處理**與可觀測性（統計、日誌、事件）
- **多格式輸出**（Parquet/CSV/JSON/Markdown），其中 **Parquet** 為數據倉儲/分析優先格式。

**與現有系統整合**：預計逐步替換既有 `html_to_markdown` 服務（port 8001），在過渡期提供 API 相容層，最終納入 Proxy Crawler 的 ETL 主幹。

---

## 2. 服務與組件（Components & Services）

### 2.1 組件清單
- **CLI**：`url2parquet` 指令；支援單一 URL、批次（檔案/STDIN）、并行度控制。
- **Python API**：
  - `convert_url(url: str, options: PipelineOptions) -> Result`
  - `batch_convert(urls: List[str], options: PipelineOptions, parallel: int) -> List[Result]`
- **FastAPI 服務**：
  - 任務管理端點：建立/查詢/取消/下載
  - 健康檢查與統計
- **核心模組**：
  - `fetch`（HTTP 客戶端/重試/逾時/UA）
  - `extract`（多引擎策略 + 後備）
  - `transform`（清洗/標準化/HTML→MD）
  - `output`（Parquet/CSV/JSON/MD 寫出）
  - `core`（管線/緩存/事件/錯誤）
- **支援模組**：
  - `checksum`（URL+Options 指紋）
  - `config`（環境/檔案化設定）
  - `utils`（IO/HTML/Text 工具）

### 2.2 邏輯架構（Mermaid）
```mermaid
flowchart TB
  subgraph IN[輸入層]
    IN1[單一 URL]
    IN2[URL 列表檔]
    IN3[REST API 請求]
  end

  subgraph CORE[核心處理引擎]
    C1[URL 解析/驗證]
    C2[HTTP 抓取/重試]
    C3[內容提取引擎
(smart / full_html / trafilatura)]
    C4[內容轉換
(清洗/標準化/HTML→Markdown)]
    C5[輸出格式器
(Parquet/CSV/JSON/MD)]
  end

  subgraph OUT[輸出層]
    O1[Parquet]
    O2[CSV]
    O3[JSON]
    O4[Markdown]
  end

  subgraph SUP[支援組件]
    S1[緩存管理
(URL×Options 指紋)]
    S2[并行/任務調度]
    S3[錯誤處理]
    S4[日誌/指標]
  end

  IN1-->C1; IN2-->C1; IN3-->C1
  C1-->C2-->C3-->C4-->C5
  C5-->O1; C5-->O2; C5-->O3; C5-->O4
  S1---C2; S2---C3; S3---C4; S4---C5
```

---

## 3. 數據流程（Pipeline）
1. **輸入驗證**：URL 格式與協定、阻擋空白/重複；遵循 robots.txt（可設定是否遵循）。
2. **緩存查詢**：以 `hash(url + options)` 為鍵，命中則直接回傳（可設 TTL/手動失效）。
3. **抓取**：`httpx/requests`，逾時、重試（指數退避）、連線池；自訂 UA、Headers、代理（可選）。
4. **提取**：
   - `smart`：Heuristic/Readability 類策略（輕量）
   - `trafilatura`：高精度抽取（可選依賴）
   - `full_html`：保留整頁（用於差異化場景）
5. **轉換**：
   - HTML→Markdown（`markdownify`）
   - 清理廣告/導航/腳註（可開關）
   - 絕對化連結、語言偵測、標準化欄位
6. **輸出**：寫出 **Parquet/CSV/JSON/MD**；回傳索引（檔案路徑/大小/行數）。
7. **觀測**：處理時間、緩存命中率、錯誤碼、引擎分佈；寫入統計端點與日誌。

---

## 4. 存儲佈局（Storage Layout & Naming）
```
work_dir/
  cache/
    {checksum}/
      result.json           # 所有欄位的彙整（含 files[] 列表）
      content.parquet       # 標準表結構
      content.json          # 結構化 JSON（與 Parquet 對齊）
      content.md            # 轉換後 Markdown
  jobs/
    {job_id}/
      results.json
      outputs/
        {timestamp}_{checksum8}.{format}
  reports/
    {date}/
      summary_{timestamp}.json
```
**命名規則**：
- 單一：`{timestamp}_{checksum[:8]}.{format}`
- 批次：`batch_{batch_id}_{timestamp}.{format}`

**遠端儲存（選配）**：支援將 `cache/` 與 `jobs/` 同步至 S3/GCS（以 `{prefix}/{checksum}/...` 佈局）。

---

## 5. 操作與範例（How to Use）

### 5.1 CLI
```bash
# 單一網址
url2parquet https://example.com --format parquet,json

# 批次處理（urls.txt 每行一個 URL）
url2parquet --file urls.txt --parallel 5 --format parquet --work-dir ./data

# 以 STDIN 輸入
cat urls.txt | url2parquet --parallel 8 --format parquet
```

### 5.2 Python API
```python
from url2parquet import convert_url, batch_convert, PipelineOptions

opts = PipelineOptions(output_formats=["parquet", "json"], extract_mode="smart")
result = convert_url("https://example.com", options=opts)

results = batch_convert(["url1", "url2", "url3"], options=opts, parallel=5)
```

### 5.3 FastAPI 整合
```python
from fastapi import FastAPI
from url2parquet.api.fastapi_router import get_router

app = FastAPI()
app.include_router(get_router(), prefix="/v1")
```

---

## 6. API 詳細說明（REST）

### 6.1 任務管理
- `POST /jobs`
  - 建立任務；Body：`{"url": str, "options": PipelineOptionsLike}`
  - 回應：`202 Accepted`：`{"job_id": str, "status": "processing"}`
- `GET /jobs/{job_id}`
  - 查詢任務狀態（`pending|processing|completed|failed|canceled`）
- `GET /jobs/{job_id}/result`
  - 成功回 `200` 與 Result 結構；失敗回 `4xx/5xx` 與錯誤碼
- `DELETE /jobs/{job_id}`
  - 取消未完成任務

### 6.2 下載
- `GET /download/{file_id}`：下載單檔（校驗 `file_id` 屬於該 job）
- `GET /batch/{batch_id}/download`：批次打包下載（zip 或清單）

### 6.3 管理
- `GET /health`：liveness/readiness
- `GET /stats`：QPS、P95 延遲、緩存命中率、引擎使用分佈
- `POST /cache/clear`：條件式清除（by checksum/prefix/TTL）

**範例：**
```http
POST /v1/jobs
Content-Type: application/json

{
  "url": "https://example.com",
  "options": {
    "output_formats": ["parquet", "json"],
    "extract_mode": "smart",
    "clean_ads": true
  }
}
```
```http
HTTP/1.1 200 OK
{
  "job_id": "job_123456",
  "status": "completed",
  "result": {
    "url": "https://example.com",
    "title": "Example Domain",
    "language": "en",
    "files": [
      {"format": "parquet", "path": "/data/cache/abc123/content.parquet", "size": 12345, "rows": 1}
    ],
    "processing_time": 2.5
  }
}
```

---

## 7. 資料結構與模式（Schemas）

### 7.1 Parquet Schema（PyArrow）
```python
ParquetSchema = pa.schema([
    ("url", pa.string()),
    ("title", pa.string()),
    ("language", pa.string()),
    ("markdown", pa.string()),
    ("content_length", pa.int64()),
    ("fetched_at", pa.timestamp("ms")),
    ("engine", pa.string()),
    ("checksum", pa.string()),
    ("warnings", pa.list_(pa.string())),
    ("extra", pa.struct([
        ("author", pa.string()),
        ("publish_date", pa.timestamp("ms")),
        ("keywords", pa.list_(pa.string())),
    ])),
])
```

### 7.2 Result JSON（回傳範例）
```json
{
  "url": "https://example.com",
  "title": "網頁標題",
  "language": "zh",
  "content_length": 1234,
  "files": [
    {"format": "parquet", "path": "/path/to/file.parquet"},
    {"format": "json", "path": "/path/to/file.json"}
  ],
  "processing_time": 190
}
```

---

## 8. 環境與配置（Env & Config）

### 8.1 依賴
**必要**：
- `httpx` 或 `requests`（抓取）
- `markdownify`（HTML→Markdown）
- `pyarrow`（Parquet 輸出）
- `pydantic`（設定/資料驗證）

**可選**：
- `trafilatura`（高精度內容抽取）
- `beautifulsoup4`, `lxml`（HTML 解析輔助）
- `pandas`（資料框轉換/匯出 CSV）

### 8.2 配置參數
| 參數 | 類型 | 預設值 | 說明 |
|---|---|---|---|
| `output_formats` | List[str] | `["parquet"]` | 輸出格式 |
| `work_dir` | Path | `./data` | 工作目錄 |
| `cache_enabled` | bool | `True` | 啟用磁碟/記憶體緩存 |
| `cache_ttl` | int | `86400` | 緩存存活（秒） |
| `max_concurrent` | int | `5` | 最大并行度 |
| `request_timeout` | int | `30` | 抓取逾時（秒） |
| `extract_mode` | str | `smart` | `smart/full_html/trafilatura` |
| `clean_ads` | bool | `True` | 移除廣告/導航 |
| `absolutize_links` | bool | `True` | 相對連結→絕對 |
| `detect_language` | bool | `True` | 語言偵測 |
| `parquet_compression` | str | `snappy` | Parquet 壓縮 |
| `user_agent` | str | `url2parquet/1.0` | HTTP UA |

### 8.3 Docker Compose（示例）
```yaml
services:
  url2parquet:
    image: url2parquet:latest
    ports:
      - "8002:8000"
    volumes:
      - ./data:/app/data
    environment:
      - WORK_DIR=/app/data
      - CACHE_ENABLED=true
      - MAX_CONCURRENT=10
```

### 8.4 Kubernetes（示例）
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: url2parquet
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: url2parquet
        image: url2parquet:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - mountPath: /app/data
          name: data-volume
        env:
        - name: WORK_DIR
          value: "/app/data"
```

---

## 9. 變更日誌與相容性（Changelog & Compatibility）
- **v0.1.0**：基礎功能（單一 URL、Parquet/JSON、緩存、CLI）
- **v0.2.0**：進階功能（批次、并行優化、CSV/Markdown、trafilatura）
- **v0.3.0**：服務化（FastAPI、任務追蹤、下載端點）

**相容性策略**：
- 過渡期與 `html_to_markdown` 並行；提供相容端點（相同輸入/輸出結構）。
- 緩存資料遷移工具：將舊格式（MD-only）補齊結果 JSON 與 Parquet。

---

## 10. 與現有 ETL（Proxy Crawler）整合
- **替代點**：在 ETL 流程中的「HTML→Markdown + 結構化」節點以 `url2parquet` 取代。
- **整合模式**：
  1) **服務模式**：由爬蟲將 URL 投遞至 `/jobs`；完成後回調或輪詢取結果。
  2) **庫模式**：在現有 Python 任務中直接呼叫 `convert_url/batch_convert`。
  3) **隊列模式**：接入既有任務隊列（e.g., Celery/RQ/Kafka），以 Job 消費方式出入。
- **資料契約**：Parquet Schema 與 JSON 統一，便於下游（清洗/分析/搜尋索引）重用。

---

## 11. 性能與可靠性（Perf & Resilience）
- **緩存策略**：URL×Options 指紋；分層緩存（記憶體→磁碟→物件儲存）；TTL/最少最近使用（LRU）。
- **并行策略**：可調執行緒池；站點節流（host-based concurrency / rate-limit）。
- **重試策略**：針對 `5xx/逾時/連線重置` 之指數退避；尊重 `Retry-After`。
- **資源管理**：
  - 連線池：上限/存活時間
  - 文件句柄：開啟數監控與批次關閉
  - 記憶體：分頁寫出、流式轉換
- **SLA/指標**：P50/P95 延遲、吞吐、失敗率、緩存命中率、輸出大小、行數。

---

## 12. 安全與合規（Security & Compliance）
- **robots.txt** 與 **ToS**：預設遵循，可由管理者覆蓋（審批記錄）。
- **版權與隱私**：僅內部分析使用；若對外分發需脫敏/過濾。
- **審計**：記錄請求來源、抓取時間、UA/代理設定、錯誤碼。
- **速率限制**：全域/每來源/每網域；防止濫用。

---

## 13. 測試計畫（Testing）
- **單元測試**：提取、轉換、緩存、輸出器、錯誤處理。
- **整合測試**：端到端（URL→Parquet）；多站樣本/邊界案例。
- **相容測試**：舊 `html_to_markdown` 輸入輸出對比。
- **性能測試**：并行度掃描、冷/熱緩存、長時穩定性。

---

## 14. 風險評估與緩解
- **提取品質波動**：
  - *緩解*：多引擎回退、站點規則表、人工標註回饋迭代。
- **高并發性能瓶頸**：
  - *緩解*：節流/隔離、連線池調優、分散式部署。
- **儲存壓力/成本**：
  - *緩解*：TTL、壓縮、冷/熱分層、外部物件儲存。
- **法規/合規**：
  - *緩解*：風險分類、白名單、審批流程。

---

## 15. 路線圖（Roadmap）
- **Phase 1（2 週）**：核心管線、抓取、抽取、Parquet/JSON、文件緩存、CLI。
- **Phase 2（2 週）**：批次與并行、CSV/Markdown、trafilatura 整合。
- **Phase 3（2 週）**：FastAPI 任務化、下載端點、兼容層。
- **Phase 4（2 週）**：測試覆蓋、性能優化、部署與文件。

---

## 16. 參考實作骨架（Project Skeleton）
```
url2parquet/
├── __init__.py
├── config.py
├── types.py
├── errors.py
├── checksum.py
├── utils/
│   ├── html.py
│   ├── text.py
│   └── io.py
├── fetch/
│   └── http_client.py
├── extract/
│   ├── base.py
│   ├── trafilatura_engine.py
│   └── fallback_engine.py
├── transform/
│   ├── markdown_converter.py
│   ├── cleaners.py
│   └── normalizer.py
├── output/
│   ├── parquet.py
│   ├── csv.py
│   ├── json.py
│   └── markdown.py
├── core/
│   ├── engine_selector.py
│   ├── pipeline.py
│   ├── cache.py
│   └── events.py
├── api/
│   └── fastapi_router.py
└── cli/
    └── main.py
```

---

## 17. 決策紀錄（ADR 摘要）
- **輸出主格式選擇**：以 **Parquet** 為主（列式/壓縮/向量化分析友好），CSV/JSON/MD 為輔。
- **抽取引擎策略**：預設 `smart`，特定站點允許 `trafilatura` 或 `full_html` 回退；以 **準確性→穩定性→成本** 排序。
- **緩存鍵**：`sha256(url + canonicalized_options)`；避免因參數不同導致誤命中。
- **相容策略**：維持 `html_to_markdown` 的輸入/輸出接口直到 v0.3 完成遷移。
