# 每日工作報告 (2025-09-10)

## 1. 【已完成】

| 類型 | 任務 | 說明 / 備註 |
|------|------|-------------|
| 環境治理 | 虛擬環境統一 | 移除重複 `venv/`，保留 `.venv` 並於 README 更新標準流程 |
| 啟動修復 | 修正縮排 / 結構錯誤 | `pools.py`、`manager.py`、`fetchers.py` 多處錯誤導致啟動失敗，全部修復 |
| 匯入循環 | 消除 circular import | 調整 `api.py`、`api_shared.py`、`__init__.py`，使用延遲匯入與 TYPE_CHECKING |
| 資源釋放 | Validator 關閉流程 | 統一 async `close()` + `close_sync()`，避免關閉時例外 |
| API 功能 | 新增 `/api/system/health` | 回傳版本、時間戳、ProxyManager 初始化狀態與基本統計 |
| 資料模型 | Pydantic 衝突修正 | `FetchRequest.validate` → `perform_validation`，移除警告 |
| 文件 | README 重構 | 新增徽章、目錄、健康檢查、Troubleshooting、Tech Stack、uv 工作流說明 |
| 観測性 | 健康端點補充 | `/health` 導向、`/api/health`、`/metrics` 說明整理 |
| 架構圖 | Mermaid 占位提交 | 新增 `Docs/diagrams/architecture.mmd` 與 `proxy_manager_sequence.mmd` |
| 提交 | 變更推送 | Commit: `feat(docs+api): add system health endpoint, restructure README, validator shutdown fixes` |

## 2. 【進行中】

| 任務 | 進度 | 阻礙 / 需要協助 | 備註 |
|------|------|----------------|------|
| CI Workflow 設計 | 30% | 是否納入整合測試需 API 金鑰 (Shodan/Censys)？需決策 mock vs 真實 | 規劃 ruff + pytest + uv sync --frozen |
| Mermaid 自動轉圖 | 20% | 需決定使用容器 (`mermaid-cli`) 或 Node 安裝 | 後續生成 PNG 放入 `Docs/images/` |
| Playwright E2E 測試導入 | 15% | Python 版或 Node 版選型待定；前端尚未穩定 | 目標先做 `/docs` 與 `/api/system/health` 煙囪測試 |
| 指標擴充 | 25% | 欄位清單尚未定稿（池大小 / 驗證耗時 / 來源成功率） | 之後 Grafana 模板化 |
| 英文 README | 10% | 是否保持功能等量或簡化？需產品定位方向 | 產出 README_EN.md |
| ETL API 文檔一致化 | 40% | 尚缺 OpenAPI 標籤與 README 連結 | 健康端點已列出 |
| ProxyManager 詳細狀態輸出 | 20% | 需統一定義 `last_fetch_at` 與來源失敗策略 | health 擴充欄位 |
| 依賴安全審視 | 50% | 是否鎖定特定套件版本策略（安全公告） | 透過 uv.lock 基礎完成 |
| Docker 編排增強 | 30% | 是否內建 Prometheus+Grafana 預設啟動 | 目前只含核心服務 |

## 3. 【待辦事項】 (優先級高→低)

1. 建立 CI `ci.yml`（明日上午）
2. 建立 Mermaid 轉 PNG workflow（明日下午）
3. Playwright e2e 煙囪測試 (`tests/e2e/`)（明日完成基本）
4. 擴充 `/api/system/health`：加入 `last_fetch_at`、來源成功/失敗統計（後日）
5. 新增自定 Prometheus metrics（fetch_success_total 等）（後日）
6. README_EN.md 草稿（本週內）
7. 部署指南補強（Docker 監控堆疊部分）（本週內）
8. 安全章節：金鑰管理與未來 RBAC 規劃（本週內）
9. 覆蓋率工具整合（pytest-cov + Codecov）（下週初）
10. Locust 壓力測試腳本占位（下週）
11. 設定模組 config 說明文檔（下週）
12. 結構化日誌策略（JSON logger 選型）（下週）

## 4. 【驗收準則 / 完成定義】

### CI / 工作流程

- ci.yml：push/PR 觸發；步驟 = uv sync --frozen → ruff → pytest；失敗阻擋 merge
- Mermaid workflow：提交 .mmd 自動產生對應 .png 並附加至 PR / push

### 測試 / 品質

- Playwright：最少 2 個煙囪測試 (docs 頁、system health JSON)
- Coverage：主分支 ≥ 70%（初期），上傳並顯示徽章

### 指標 / 監控

- `/metrics` 新增：pool_hot、pool_warm、pool_cold（gauge）；fetch_success_total / fetch_failure_total（counter）；validation_latency_seconds（histogram）
- Health 擴充：`last_fetch_at`、`sources: {name: {success, failure}}`

### 文件

- README_EN.md：章節對應中文版；指令英文化
- 部署指南：本地 / Docker / CI 差異、環境變數表
- 圖片：`Docs/images/architecture.png` 由 workflow 產出並引用於 README

### 安全 / 設定

- `.env.example` 與 README 配置一致
- grep 無敏感金鑰硬編碼

### 代理核心

- 抓取失敗不阻塞啟動，health 反映來源狀態
- Validator 關閉無例外，重啟穩定

---

> 若需調整優先順序或插入緊急任務，請回覆標註項目與新優先級。
