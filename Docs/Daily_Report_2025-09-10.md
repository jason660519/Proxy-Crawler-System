### 【已完成】

- 完成前端啟動卡住問題修復：新增 `/api/health` 別名端點，解除首頁「JasonSpider 正在啟動…」gating（修改 `src/main.py`）
- 修復前端輪詢 404：新增相容的 `/api/tasks` 別名端點回傳空分頁，避免 dashboard 輪詢失敗（修改 `src/main.py`）
- 後端 Parquet/CSV 產出邏輯：在 `Url2ParquetPipeline` 中加入 CSV/Parquet 輸出（`src/url2parquet/core/pipeline.py`）
- 依賴環境就緒：以 `.venv` 安裝並可匯入 `pandas`、`pyarrow`；後端已使用 `.venv` Python 啟動（Windows PowerShell）

### 【進行中】

- 打通前端 Wizard 與 API（約 70%，`wizard-api-e2e`）
  - 現況：可建立任務、處理重定向確認、看到 MD/JSON 檔。正在驗證 CSV/Parquet 是否穩定出現在 files 清單並可下載
  - 風險/阻礙：
    - 需確認前端有把 `output_formats`（含 csv/parquet）確實傳到後端
    - 需確認快取策略：同一 URL 若命中舊快取可能不會重產 Parquet（需繞過或納入 `output_formats` 至 cache key）
    - 需確認目前執行中的後端進程皆使用 `.venv`（避免不同環境導致行為不一致）
  - 需要協助：若有前端 UI 的格式選擇（CSV/Parquet）請確認有傳遞至 `/api/url2parquet/jobs`；或同意我們在後端預設包含 csv/parquet

### 【待辦事項】（高 → 低）

1. 優化輪詢或加上 SSE（`polling-or-sse`，明日上午）
2. 前端 API 包裝重構與型別補齊（`frontend/src/api/url2parquetApi.ts`，明日下午）
3. 放置範例 Markdown 並驗證 `/api/url2parquet/local-md*`（`local-md-sample-verify`，後天上午）
4. 增補測試：redirect、cache、API 基本流（`tests-add`，本週內）
5. 文件更新：啟動指令、Vite 代理、路由與使用指南（`docs-update`，本週內）

### 【驗收準則 / 完成定義】

- 打通前端 Wizard 與 API（wizard-api-e2e）
  - 提交多個 URL 可穩定建立 job
  - 遇到重定向能提示並繼續處理
  - 輪詢可看到最終 files 列表，且包含 `.csv`、`.parquet`
  - 前端可成功下載檔案並開啟驗證格式正確
- 優化輪詢或 SSE
  - 輪詢退避與錯誤處理完善，或 SSE 可即時推送進度
  - 無多餘 404/500 訊息，資源使用可控
- 前端 API 包裝與型別
  - `url2parquetApi.ts` 具明確函式、回傳型別，UI 僅呼叫封裝層
  - 錯誤/重試邏輯集中實作並覆蓋主要流程
- Local MD 驗證
  - `data/url2parquet/outputs` 放置樣本後，`/local-md`、`/local-md/content` 皆能正確讀取與呈現
- 測試
  - 單元/整合測試覆蓋 redirect 流程、cache 命中/繞過、基本 API happy path
  - CI 綠燈
- 文件
  - README/Docs 更新啟動、代理設定、端點與使用示例
  - 新人依文件可在 10 分鐘內跑起並走完整流程
