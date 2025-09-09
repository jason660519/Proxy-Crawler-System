# 每日工作報告 - 2025-09-10

## 1. 【已完成】

- 拆分資料庫代理端點：從 `api.py` 抽離 `/api/database/proxies` 至 `routes_database.py`，並移除舊內嵌實作以消除耦合。
- API 聚合重構：`api.py` 精簡為路由聚合器，統一掛載 `routes_proxies / routes_stats / routes_maintenance / routes_health_etl / routes_database`，刪除遺留重複端點與背景任務樣板碼。
- 批量驗證功能實作：於 `routes_maintenance.py` 完成 `/api/batch/validate` 真實邏輯（收集池代理→批次驗證→統計 latency / status / anonymity / geo）。
- 新增精細化驗證指標：在 `api_shared.py` 加入 `VALIDATION_LATENCY`, `VALIDATION_STATUS_COUNT`, `VALIDATION_ANONYMITY_COUNT`, `VALIDATION_GEO_DETECT_COUNT`；於 `ProxyValidator.validate_proxy` 注入指標觀測。
- 主應用生命週期升級：`main.py` 由 deprecated `@app.on_event` 遷移至 `lifespan` context，集中啟停 `ProxyManager`，確保未來 FastAPI 版本相容性。
- 路由完整性測試：新增 `tests/test_route_integrity.py` 檢測 (method,path) 重複與核心端點煙囪測試骨架。
- 移除重複/過時：批量驗證、統計、ETL、metrics trends 等 legacy 端點自 `api.py` 清除，避免路由陰影與行為混淆。
- 增補驗證器錯誤處理：`ProxyValidator` 新增 metrics 發送 best-effort 區段，確保異常不影響主流程。

## 2. 【進行中】

- 路由掛載一致性修復（進度 60%）：`/api/health` 在整合後的 `TestClient(app)` 測試中回傳 404；研判為主應用合併路由時機與 `lifespan` 初始化/模組 import 順序導致（尚未在測試階段觸發聚合或循環 import 導致多 app 實例）。需：
  - 追蹤 `src.proxy_manager.api` 匯入後 `app.routes` 是否含 `'/api/health'`。
  - 規劃改為 `app.mount('/api', proxy_sub_app)` 或統一於 `create_proxy_app()` 工廠函式回傳，避免副作用式合併。
- ETL 同步實作（進度 20%）：目前 `/api/etl/sync` 仍回傳排程占位；尚未建立背景任務與 job registry（in-memory state + 查詢端點）。需定義資料匯出格式（JSON snapshot / streaming）。
- 驗證指標測試（進度 30%）：新增 metrics 後尚無對應單元/整合測試驗證計數與 bucket 觀察；需要 fixture 模擬 2~3 種驗證結果。
- 其餘子服務 lifespan 遷移（進度 10%）：`html_to_markdown.api_server` 仍使用 `@app.on_event` 觸發 deprecation warning。
- 文件同步（進度 40%）：README / API_CONFIGURATION.md 尚未更新新增批量驗證與 metrics 指標說明；TECH_DEBT_TODO 未標記已完成項目。

## 3. 【待辦事項】（優先序）

1. 修復 `/api/health` 測試 404 問題（今日內，優先 A）。
2. 設計並實作 ETL 同步背景任務 + job 狀態查詢 (`/api/etl/jobs` + `/api/etl/status`)（明日上午）。
3. 撰寫驗證指標測試：模擬 working / failed / timeout / geo 成功案例（明日下午）。
4. 將剩餘模組（`html_to_markdown.api_server` 等）改為 lifespan（本週內）。
5. 補齊文件：更新 README、技術文件、生成指標對照表 & 批量驗證使用說明（本週內）。
6. 增加 `/api/database/proxies` 測試覆蓋（本週內）。
7. 增加路由快照檔（JSON dump）供後續差異比對（本週內）。
8. 評估將 batch 驗證分流為背景任務 + job id（下週）。
9. 增加 Prometheus export 詳細標籤（來源 fetcher 與 validator error taxonomy）（下週）。

## 4. 【驗收準則 / 完成定義】

- 路由掛載修復：
  - a) `tests/test_route_integrity.py` 經調整後綠燈。
  - b) `/api/health`、`/api/stats`、`/api/batch/validate` 皆 200/授權保護可控。
  - c) 無重複 (method,path)；自動測試中 `duplicates` 為空。
- ETL 同步：
  - a) 提供 `/api/etl/sync` 觸發 → 回傳 job_id。
  - b) `/api/etl/jobs/{job_id}` 可查狀態（pending/running/success/failed）。
  - c) Snapshot 檔（或記憶結構）含池別、代理數、生成時間戳。
  - d) 失敗路徑記錄 error message。
- 驗證指標測試：
  - a) 單測驗證至少 1 個 working、1 個 failed、1 個 timeout 聚合後 counter > 0。
  - b) `VALIDATION_LATENCY` 至少觀測 1 筆樣本。
  - c) 匿名度與 geo outcome counter 正確遞增。
- Lifespan 遷移（其餘服務）：
  - a) 相關模組不再出現 `on_event` Deprecation warning。
  - b) 啟停流程中資源（session / 背景任務）正常釋放（測試觀察無 dangling task）。
- 文件更新：
  - a) README 新增批量驗證與指標對照區段。
  - b) TECH_DEBT_TODO 標記已完成項並新增新債務條列。
  - c) API 配置文件列出新路由與授權需求。
- `/api/database/proxies` 測試：
  - a) 成功回傳 pagination 結構。
  - b) 支援最少 3 種過濾參數組合。
  - c) 錯誤參數（非法排序欄位）返回 400。
- 路由快照：
  - a) 生成 `data/route_snapshot.json`，含 method, path, summary。
  - b) 後續測試比對新增/刪除異動可被檢出。
- Batch 驗證背景化（下階段）：
  - a) 非同步任務回傳 job_id；查詢端點提供進度百分比。
  - b) 允許取消（可選）。
- Prometheus 進階標籤：
  - a) Validation error taxonomy（network/dns/timeout/protocol）至少 4 分類。
  - b) 來源 fetcher 成功/錯誤百分比於 dashboard 可視化。

---
（如需補充或調整優先順序，請回覆註記。）
