# ETL Pipeline (Brief)

This brief points to the authoritative English overview and highlights the current integration.

- Main reference: `Docs/ETL_Pipeline_Overview.md`
- Services:
  - Main API (8000): exposes `/api/*`, health `/api/health`, metrics `/metrics`
  - HTML→Markdown (8001): exposes `/health`, `/convert`, `/convert/batch`, `/upload`
- Data directories (via Docker Compose): `data/raw`, `data/processed`, `data/transformed`, `data/validated`, `data/reports`
- Migrations: Alembic runs on container start
- Monitoring: Prometheus scrapes `proxy_crawler:8000/metrics` and `html_to_markdown:8001/metrics`; Grafana on host `3001`

For full diagrams, storage paths and operational notes, see `ETL_Pipeline_Overview.md`.

## **2\. ETL 流程圖**

```mermaid
graph TB
    subgraph "Extract (數據提取)"
        E1[發起HTTP請求] --> E2[獲取HTML內容]
        E2 --> E3{內容類型?}
        E3 -->|靜態HTML| E4[BeautifulSoup解析]
        E3 -->|動態JS| E5[Playwright/Selenium渲染]
        E4 --> E6[提取數據表格]
        E5 --> E6
    end

    subgraph "Transform (數據轉換)"
        T1[原始代理數據] --> T1A[HTML to Markdown轉換]
        T1A --> T1B[LLM內容解析與結構化]
        T1B --> T2[IP地址驗證]
        T2 --> T3[端口號格式化]
        T3 --> T4[協議類型標準化]
        T4 --> T5[國家代碼轉換]
        T5 --> T6[匿名性分類]
        T6 --> T7[速度單位統一]
        T7 --> T8[數據質量評分]
    end

    subgraph "Validate (數據驗證)"
        V1[異步驗證隊列] --> V2[連接性測試]
        V2 --> V3[速度測試]
        V3 --> V4[匿名性測試]
        V4 --> V5[地理位置驗證]
        V5 --> V6[綜合評分計算]
    end

    subgraph "Load (數據加載)"
        L1[有效數據] --> L2[寫入PostgreSQL]
        L1 --> L3[更新Redis緩存]
        L2 --> L4[生成Markdown報告]
        L3 --> L5[API服務就緒]
    end

    E6 --> T1
    T8 --> V1
    V6 --> L1
```

---

## **3\. 各階段說明與檔案存儲**

### **3.1 Extract (數據提取)**

- **目標**：從目標網站獲取原始數據
- **存放位置**：

  - `data/raw/{source}_{timestamp}.json`
  - 保存原始 HTML 表格解析後的資料

---

### **3.2 Transform (數據轉換)**

- **目標**：清洗與標準化數據（IP、Port、Protocol、Country、Anonymity、Speed 等）
- **新增模組**：
  - **HTML to Markdown 轉換**：將原始 HTML 內容轉換為結構化的 Markdown 格式
  - **LLM 內容解析與結構化**：利用大型語言模型解析 Markdown 內容，提取並結構化代理伺服器資訊
- **存放位置**：

  - `data/processed/{source}_{timestamp}.json`
  - 存儲轉換後、已加上質量分數的數據
  - `data/processed/{source}_{timestamp}.md`
  - 存儲 HTML to Markdown 轉換後的中間格式，便於 LLM 處理

---

### **3.3 Validate (數據驗證)**

- **目標**：驗證代理伺服器可用性（連接性、速度、匿名性、地理位置）並計算綜合評分
- **存放位置**：

  - `data/validated/{source}_{timestamp}.json`
  - 保存驗證結果，包含每個代理的成功率、平均延遲、是否有效

---

### **3.4 Load (數據加載)**

- **目標**：將有效數據存入資料庫與快取，並生成報告
- **存放位置**：

  - **PostgreSQL**：長期保存代理伺服器資訊
  - **Redis**：即時快取，有效代理供 API 使用
  - `data/reports/{source}_{timestamp}_proxies.md`

    - Markdown 格式報告，方便人工檢視

---

## **4\. 監控與日誌**

- **監控指標**：抓取成功率、驗證通過率、數據質量分數
- **日誌存放**：`logs/{date}.log`
- **錯誤處理**：各階段具備重試機制，確保數據完整性
