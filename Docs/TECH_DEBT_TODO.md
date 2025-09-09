# 技術債與後續重構計畫

## 第一批（已修復或部分完成）

- 修復 `manager.py` 重複 `_cleanup_old_backups` 語法錯誤
- 為 `persistence_service` / `fetch_service` / `validation_service` 缺失情況加入防護
- 修正 `ProxyResponse` 使用錯誤，統一以 `ProxyNodeResponse` 包裝
- CORS origins 改用 `settings.allowed_origins`
- `/metrics` 回傳正確 `CONTENT_TYPE_LATEST`
- 下載端點加入路徑穿越防護
- `/status` 敏感資訊脫敏
- 新增基本測試 `tests/test_proxy_api_basic.py`

## 第二批（優先）

1. 拆分 `src/proxy_manager/api.py` → `routes/` 子模組 (proxies.py / stats.py / maintenance.py / metrics.py / etl.py)
2. 新增 fetch source 級別 metrics（labels: source, outcome）
3. 為自動任務加入取消協調與健康檢測（心跳）
4. 實作背景任務 `_batch_validate_proxies` 與 `_sync_data_to_etl`
5. Pool 取得代理時加入租借/歸還機制避免短時間重複

## 第三批（強化）

- 引入 OpenTelemetry（trace + metrics + logs）
- Rate Limiting (依 IP + API key) middleware
- 將 ProxyManager 拆出 service 層（FetchOrchestrator / ValidationCoordinator 等）
- 增加黑名單原因統計與輸出
- 增加版本資訊與 Git commit hash 注入 (/health)

## 測試規劃補充

- 單元：fetch_pipeline, validation fallback, export/import edge cases
- 整合：auto loops, graceful shutdown snapshot, metrics 收集增量
- 壓力：池內 5k+ 代理輪詢性能

(此檔案自動生成初稿，可持續更新)
