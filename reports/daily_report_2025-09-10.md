# 每日開發進度報告（2025-09-10）

## 1. 【已完成】

| 類型 | 任務描述 | 備註 / 影響 |
| ---- | -------- | ------------ |
| 啟動修復 | 修正主 API 啟動錯誤（缺少 `get_proxy_manager` 匯入、未初始化 `ProxyManager`） | 新增 FastAPI lifespan 初始化，啟動穩定性恢復 |
| 路由優化 | 新增主 API 根路由 `/` 與 `/health` redirect | 避免使用者初次造訪 404，提高可探索性 |
| ETL API | 新增 ETL API 根路由 `/` 與 `/health` redirect（對應 `/api/etl/health`） | 介面一致性提升 |
| Bug 修復 | 移除對 `ETLConfig` 不存在參數（`validation_level`, `enable_monitoring`）的傳入 | 修正 500 啟動錯誤，ETL API 可正常啟動 |
| Metrics | 使用既有 `FETCH_SOURCE_COUNT` 指標，為各 fetch source 加入 outcome 標籤（success / empty / error） | 觀測代理來源成效，可供後續告警基礎 |
| 資源管理 | 代理池加入「租借 / 歸還」機制（短期避免重複使用同一 proxy） | 降低瞬間重用，改善分散度；可擴充 TTL & 使用次數策略 |
| 系統資訊 | 讀取 git short commit，注入主 API `/` 與 `/api/health` 回傳 | 便於定位部署版本 |
| 任務監控 | 新增心跳迴圈與 `/api/system/tasks` 端點（回傳 heartbeat + 背景任務狀態） | 為後續自動任務可觀測化奠基 |
| 背景任務骨架 | 新增 `background_sync_to_etl` 與 `schedule_etl_sync`（目前為資料收集 mock） | 後續可掛接實際 ETL 推送 |
| 健康擴充 | `/api/health` 回傳 version / commit（ETL 健康尚未同步增加 commit） | 統一版本可追溯性 |
| 安全/穩定 | Persistence snapshot 目錄建立防護（由使用者補 patch，流程已驗證） | 避免 FileNotFound / 初次啟動失敗 |

## 2. 【進行中】

| 任務 | 進度 | 現況 / 阻礙 | 需要協助 |
| ---- | ---- | ----------- | ---------- |
| 背景 ETL 同步實作（將代理池摘要推送至 ETL API 或中介儲存層） | 30% | 骨架存在：收集數量；尚未定義傳輸協議 / 目標 API | 需確認 ETL 期望 payload schema（字段、頻率、可靠性要求） |
| 租借機制完善（TTL 策略 & metrics） | 40% | 目前僅 default 30s TTL + 單純清理；尚未支持：最大並行租借、重入策略、Prometheus gauge | 確認實際使用場景：是否需要「以請求標識」追蹤歸還 |
| Batch 驗證任務自動化排程 | 20% | 僅手動端點；尚未有定時 scheduling / 指標增量比較 | 池大小期望頻率（分鐘/小時） & 是否分 pool 並行策略 |
| Rate Limiting Middleware（IP + API Key + Bucket） | 10% | 目前只有簡單 dependency 限流；尚未 middleware 化、無滑動視窗 | 明確配額策略：global vs per-endpoint 配置 |
| OpenTelemetry 整合 | 0%（設計中） | 尚未選擇 exporter (OTLP / Prometheus Bridge / Jaeger) | 決定目標觀測平台與必要 span 命名標準 |
| ETL `/api/etl/health` 擴充 version/commit | 50% | Root 已有資訊；health 未帶 commit | 是否同步加上資源（DB 連線/Redis）檢測 |
| 任務狀態細節（新增：最近錯誤、重啟次數、平均執行時間） | 10% | 現在僅最小心跳 + done 狀態 | 確認是否需持久化到檔案 / DB |
| 自動 fetch/cleanup/save 任務觀測（指標化 active loops） | 15% | 尚未在 metrics 中暴露 loop 週期與耗時 | 確認哪些 loop 需優先做 SLA / 告警 |

## 3. 【待辦事項】（優先級高 → 低）

1. 實作 ETL 同步實際傳輸（定義 JSON schema；加重試 / 指標） — 預計：明日 上午
2. Rate limiting middleware（支援 X-Forwarded-For、Token 綁定、指標化） — 預計：明日 下午
3. Batch 驗證自動排程 + 任務統計（成功率、耗時直方圖） — 預計：後日 上午
4. 租借機制增強：Prometheus gauges（leased_total, lease_expired_total, lease_reuse_attempts）與 TTL 配置化 — 預計：後日 下午
5. OpenTelemetry 初始整合（trace 基礎：/api/*、validator、fetch flows） — 本週內
6. ETL `/api/etl/health` 增加 version/commit + 依賴檢查（DB / Redis mock） — 本週內
7. 系統任務狀態擴充（平均耗時/失敗次數/最後錯誤摘要） — 本週內
8. Fetch source metrics 補充：新增耗時直方圖 + 失敗原因分類(label=error_type) — 本週內
9. Pool / Lease 策略配置化（透過 config/ YAML 或環境變數） — 視前面進展排期
10. 編寫針對新增功能的單元測試（metrics 暴露、租借行為、系統任務 API） — 本週內收尾

## 4. 【驗收準則 / 完成定義】

### 背景 ETL 同步（Complete Definition）

- 可透過 `schedule_etl_sync` 週期性觸發。
- 向 ETL API（或暫存檔案）送出包含 pools summary + timestamp + version 的 JSON。
- 失敗自動重試（指數回退，最多 3 次）並在 metrics 中累積錯誤計數。
- `/api/system/tasks` 可看到最近一次同步狀態與耗時。

### Rate Limiting Middleware

- 可針對 IP / API Key / Endpoint 精細限制（Token > IP 優先）。
- 超限回傳 429 並帶剩餘重置秒數 header（如 `X-RateLimit-Reset`）。
- Prometheus 指標：`rate_limit_requests_total{result="allowed|blocked"}`。
- 支援白名單列表與全域開關。

### Batch 驗證自動排程

- 可配置間隔（最小 5 分鐘）與每輪最大驗證數量。
- 驗證完成後更新統計並輸出 latency/成功率指標增量。
- 手動 API 仍可即時觸發且不互相衝突（具互斥鎖防重入）。

### 租借機制增強

- 指標：當前租借中數量、租借命中率、提前歸還次數、過期數量。
- TTL 可透過設定調整，並支援不同池自訂（HOT < WARM < COLD）。
- 高併發壓測不會出現大量重複同一 proxy（重複率 < 5%）。

### OpenTelemetry 初始整合

- 主要端點 /fetch /validate /export 產生 trace（包含 request id）。
- 至少 1 個自訂 span capturing validation pipeline。
- 可匯出至本地 OTLP Collector 或 Jaeger（文件化啟動步驟）。

### ETL `/api/etl/health` 擴充

- 回傳欄位：`status, timestamp, version, commit, db_connected, redis_connected`。
- 異常（任一依賴失敗）時 `status != healthy` 並標記 `issues[]`。

### 任務狀態擴充

- `/api/system/tasks` 每項任務包含：`created_at, started_at, ended_at, duration_seconds, last_error(optional)`。
- 失敗任務計數與最近錯誤摘要指標化。

### Fetch Source Metrics 深化

- 新增 `proxy_fetch_duration_seconds` Histogram。
- 新增失敗類型 label：`error_type`（timeout / parse / network / unknown）。
- Dashboard 能展示各來源成功率 / 平均耗時 / 錯誤拓樸。

### 測試覆蓋新增功能

- 單元測試：租借 TTL 邏輯、ETL 同步調度、Rate limit decision function。
- 整合測試：/api/system/tasks 正確顯示任務與心跳。
- Metrics 測試：使用 test client 抓取 /metrics，驗證新增 counter/histogram 存在且遞增。

---

若需我立即著手其中某個「待辦」請指派（例如：#1 ETL 同步實體化 或 #2 Rate Limit）。可再附帶期望資料格式或外部系統規格，我會直接實作。
