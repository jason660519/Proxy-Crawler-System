# URL2Parquet Wizard 頁面狀況分析報告

最後更新：2025-09-09  
頁面路由：`/url2parquet`（Vite 開發伺服器預設 `http://localhost:5173/url2parquet` 或你提供的 `http://172.20.16.1:5173/url2parquet`）

---

## 一、概要結論

- 前端頁面 `frontend/src/pages/UrlToParquetWizard.tsx` 已提供基本「多 URL 輸入 → 呼叫後端建立任務 → 取得檔案 → 下載」流程，並具備「偵測重定向並確認」的互動。
- 後端路由 `src/url2parquet/api/router.py` 已掛載到主 API（`/api/url2parquet`），具備建立作業、查詢作業、讀檔與下載檔案、重定向確認等端點；檔案型別涵蓋 `md/json/parquet/csv`。
- 與《URL2Parquet\_工作細部計畫.md》相比，Wizard 頁面目前是「單頁簡化版」，尚未分拆成「四步驟 Wizard + 進階選項 + 進度/日誌（SSE）」等模組化元件與體驗。

---

## 二、現況細節（依實作）

### 2.1 前端 `UrlToParquetWizard.tsx`

- 主要流程：

  - 使用者可新增/移除多個 URL 輸入框。
  - 送出時呼叫 `POST /api/url2parquet/jobs`，payload 範例：
    ```json
    { "urls": [...], "output_formats": ["md","json","parquet"], "timeout_seconds": 60 }
    ```
  - 若後端回覆 `status: redirected`，會彈出重定向確認卡片，點選確認後再呼叫 `POST /api/url2parquet/jobs/{job_id}/confirm-redirect`（以重定向後 URL 重新處理）。
  - 作業完成後，前端會：
    - 顯示任務資訊與檔案清單。
    - 以 `GET /api/url2parquet/jobs/{job_id}/files/md` 嘗試抓取 Markdown 內容，並解析代理表格，生成可視化表格與三種導出（CSV/JSON/TXT）。
    - 支援各檔案逐一下載：`GET /api/url2parquet/jobs/{job_id}/files/{format}/download`（含 parquet 二進位）。

- 顯示與匯出：

  - 代理清單表格：IP、Port、Country(Code/Name)、Anonymity、Google/HTTPS 支援、最後檢查時間、來源。
  - 導出功能：CSV、JSON、TXT（`ip:port` 列表）。

- 尚未實作/待強化：
  - 四步 Wizard（輸入 → 高級選項 → 進度/日誌 → 結果）。
  - SSE/WebSocket 進度與日誌呈現。
  - `AdvancedOptionsPanel` 等模組化元件、hook（`useUrl2Parquet` 等）。
  - 結果預覽（Parquet/CSV 分頁表、JSON/Markdown 摘要等）。

### 2.2 後端 `src/url2parquet/api/router.py`

- 已提供端點：

  - `POST /api/url2parquet/jobs`：建立任務；支援新舊參數格式（`urls[]` 或 `url + options`）。
  - `GET /api/url2parquet/jobs/{job_id}`：查詢任務狀態。
  - `GET /api/url2parquet/jobs/{job_id}/download`：回傳檔案清單（中繼資訊）。
  - `GET /api/url2parquet/jobs/{job_id}/files/{format}`：讀取檔案內容（目前以文字方式回傳，適用 md/json/csv/txt）。
  - `GET /api/url2parquet/jobs/{job_id}/files/{format}/download`：串流下載檔案（含 parquet 二進位）。
  - `POST /api/url2parquet/jobs/{job_id}/confirm-redirect`：重定向確認後重新處理（支援快取命中）。

- 核心行為：

  - 以 `FileCache` + `compute_checksum(url, options)` 實現工作目錄 (`data/url2parquet`) 快取。
  - `Url2ParquetPipeline` 處理單一 URL；多 URL 逐一處理並彙整結果；對 `httpx` 重定向回應與例外有對應處理。

- 尚未實作/待強化：
  - SSE/WebSocket 事件派發與狀態流（目前為同步立即回應設計）。
  - 多 URL 的批次結果彙整（目前前端只用第一筆成功結果）。
  - 進一步的可觀測性（Prometheus 指標、結構化日誌映射）。

---

## 三、與《URL2Parquet\_工作細部計畫》差距

- Wizard 分步：目前為單頁集中 UI，未拆分 `AdvancedOptionsPanel`、`JobProgressPanel`、`ResultPreview`。
- 進度/日誌：計畫要求 SSE/WebSocket，現行為同步請求，無即時進度與事件時間線。
- 前端 API 封裝與 Hook：未見 `frontend/src/api/url2parquetApi.ts` 與 `hooks/useUrl2Parquet.ts`；現況直接用通用 `apiClient/http`。
- 結果預覽：未提供 Parquet/CSV 的表格虛擬化預覽、JSON/Markdown 折疊等。
- 批次作業與並行：UI 上未暴露並行/節流/引擎選擇等「高級選項」。

---

## 四、已知風險與注意事項

- 網頁實測端口：Vite 預設 5173；請確認你的開發機 IP `172.20.16.1` 是否能被瀏覽器訪問（同網段/防火牆）。
- CORS/代理：前端以 `/api` 為 baseURL；需由 Vite dev server 代理至後端或同源部署，否則會遇到 CORS 問題。
- 大檔案下載：Parquet 以二進位串流傳輸，建議檢查 Nginx/反代的回應緩衝與超時設定。
- 重定向流程：當後端回覆 `redirected` 時，前端以 `confirm-redirect` 重新提交，這對多 URL 場景仍需更多 UX 引導（例如逐條確認）。

---

## 五、快速驗證步驟（Windows/PowerShell）

```powershell
# 啟動後端（含 URL2Parquet 路由）
python run_server.py

# 啟動前端（Vite）
cd frontend
npm run dev

# 瀏覽器開啟
# http://localhost:5173/url2parquet 或 http://172.20.16.1:5173/url2parquet
```

測試流程：

- 在「代理網站 URL 列表」輸入 1~N 個 URL（例如 `https://free-proxy-list.net/`）。
- 按「開始轉換」，預期顯示任務結果、生成檔案清單，並可下載 `md/json/parquet`。
- 成功擷取 Markdown 後，應顯示解析出的代理表格，並可匯出 CSV/JSON/TXT。
- 若出現重定向提示卡片，點「是，繼續測試重定向的 URL」。

---

## 六、下一步建議（落地優先級）

1. 分步 Wizard 與 UI 拆分（高）

- 新增 `components/url2parquet/*` 與 `api/url2parquetApi.ts`、`hooks/useUrl2Parquet.ts`。
- Step 1 輸入、Step 2 高級選項、Step 3 進度與日誌、Step 4 結果與下載。

2. 進度與日誌（高）

- 後端新增 SSE 事件（`queued/started/phase_update/progress/log/completed/failed`）。
- 前端 `JobProgressPanel` 訂閱 SSE，提供進度條與時間線。

3. 結果預覽與多格式支持（中）

- Parquet/CSV 預覽（虛擬清單 + 分頁），JSON/Markdown 折疊與拷貝。
- 支援多 URL 的結果彙整與切換檢視。

4. 高級選項（中）

- 暴露 `engine/output_formats/timeout/max_concurrency/work_dir/robots` 等。

5. 可觀測性與穩定性（中）

- Prometheus 指標、結構化日誌；錯誤碼與例外分類；下載穩定性與超時重試策略。

---

## 七、對照檔案與路徑

- 前端頁面：`frontend/src/pages/UrlToParquetWizard.tsx`
- 前端 HTTP 客戶端：`frontend/src/services/http.ts`
- 後端路由：`src/url2parquet/api/router.py`
- 主 API 掛載：`src/proxy_manager/api.py`、`src/main.py`

---

## 八、總結

目前頁面已能串接後端完成基本任務與檔案下載，且提供 Markdown → 代理表解析與匯出，功能可用但仍屬 MVP。建議依計畫文件補齊 Wizard 體驗、SSE 進度/日誌、API 封裝與預覽能力，以達成完整的「URL → Parquet」可觀測與可操作流程。
