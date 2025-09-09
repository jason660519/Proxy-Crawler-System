# **Python 軟體包封裝大法**

本文以 `URL_2_parquet_ETL` 項目為例，闡述將任意脚本封裝為可重用、可維護、可交付的專業軟體包的核心心法與實戰步驟。  
最後更新於：2025-09-08

## **核心心法 (The Philosophy)**

封裝之目的，在於「隱複雜之實現，露簡潔之接口」。 一流的封裝，應使调用者無需知曉其內部之波瀾壯闊，僅通過一紙文書（文檔），即可驅使其完成使命。務必追求：高內聚，低耦合。

---

## **第一重境界：Python 套件 (The Python Package)**

此法乃根基，適用於 Python 生態內之重用，為後續諸般變化之基礎。

### **步驟一：構建項目骨架**

創建標準目錄結構，此乃專業之始。

`text`

`url_to_parquet_etl/       # 項目根目錄`  
`├── src/                  # 源碼目錄（推薦結構）`  
`│   └── url_to_parquet/   # 我們的套件名`  
`│       ├── __init__.py   # 將此目錄變為一個Python模組，乃封裝之關鍵`  
`│       ├── core.py       # 核心邏輯`  
`│       ├── cli.py        # 命令列接口`  
`│       ├── exceptions.py # 自定義異常`  
`│       └── utils.py      # 輔助函數`  
`├── tests/                # 單元測試`  
`├── docs/                 # 文檔`  
`├── scripts/              # 輔助腳本`  
`├── pyproject.toml        # 現代依賴與構建配置（替代 setup.py）`

`└── README.md             # 項目門面`

### **步驟二：定義核心接口**

於 `src/url_to_quet/__init__.py` 中暴露主要功能，此乃用户所見之第一面。

`python`

`"""`  
`URL to Parquet ETL 工具庫。`  
`主要功能：將URL轉換為多種結構化數據格式。`  
`"""`

`from .core import UrlProcessor, ProcessingResult, OutputFormat`  
`from .exceptions import UrlProcessingError, ValidationError`

*`# 顯式導出，方便用户導入`*

`__all__ = ['UrlProcessor', 'ProcessingResult', 'OutputFormat', 'UrlProcessingError']`

於 `src/url_to_parquet/core.py` 中實現核心類。

`python`

`from dataclasses import dataclass`  
`from enum import Enum`  
`from pathlib import Path`  
`from typing import List, Optional`  
`import logging`

`logger = logging.getLogger(__name__)`

`class OutputFormat(Enum):`  
    `"""支持的輸出格式"""`  
    `PARQUET = "parquet"`  
    `CSV = "csv"`  
    `JSON = "json"`  
    `MARKDOWN = "md"`

`@dataclass`  
`class ProcessingResult:`  
    `"""處理結果數據類"""`  
    `success: bool`  
    `job_id: Optional[str] = None`  
    `output_path: Optional[Path] = None`  
    `error_message: Optional[str] = None`  
    `format: Optional[OutputFormat] = None`

`class UrlProcessor:`  
    `"""核心處理器類"""`

    `def __init__(self, output_dir: str = "./output", enable_playwright: bool = True):`  
        `self.output_dir = Path(output_dir)`  
        `self.output_dir.mkdir(parents=True, exist_ok=True)`  
        `self.enable_playwright = enable_playwright`

    `def process(`  
        `self,`  
        `urls: List[str],`  
        `output_format: OutputFormat = OutputFormat.PARQUET,`  
        `**kwargs`  
    `) -> ProcessingResult:`  
        `"""`  
        `處理一個或多個URLs的核心方法`  
          
        `Args:`  
            `urls: 要處理的URL列表`  
            `output_format: 輸出格式，默認為Parquet`  
            `**kwargs: 其他高級選項（如清洗配置）`

        `Returns:`  
            `ProcessingResult: 處理結果對象`  
        `"""`  
        `# 1. 參數驗證`  
        `# 2. 生成唯一 job_id`  
        `job_id = self._generate_job_id()`  
        `logger.info(f"Starting job {job_id} for {len(urls)} URL(s)")`

        `try:`  
            `# 3. 執行五步轉換流程 (Extract -> Transform -> Load)`  
            `#    此處調用你原有的模組，但將其抽象化`  
            `final_output_path = self._run_etl_pipeline(urls, output_format, job_id, kwargs)`

            `return ProcessingResult(`  
                `success=True,`  
                `job_id=job_id,`  
                `output_path=final_output_path,`  
                `format=output_format`  
            `)`

        `except Exception as e:`  
            `logger.exception(f"Job {job_id} failed with error: {e}")`  
            `return ProcessingResult(success=False, job_id=job_id, error_message=str(e))`

    `def _run_etl_pipeline(self, urls, output_format, job_id, options):`  
        `"""封裝原有的五步流程"""`  
        `# 這裡實現或調用你的 HTML -> MD -> JSON -> CSV -> Parquet 邏輯`  
        `# 此為封裝之核心，對调用者隱藏`

        `pass`

### **步驟三：配置項目依賴與元數據**

使用現代 `pyproject.toml` 替代傳統 `setup.py`。

`toml`

`[build-system]`  
`requires = ["setuptools>=64.0.0", "wheel"]`  
`build-backend = "setuptools.build_meta"`

`[project]`  
`name = "url-to-parquet-etl"`  
`version = "0.1.0"`  
`description = "將URL轉換為Parquet/CSV/JSON/Markdown的ETL管道"`  
`readme = "README.md"`  
`requires-python = ">=3.8"`  
`keywords = ["etl", "parquet", "web-scraping", "data-processing"]`  
`authors = [`  
    `{ name = "Your Name", email = "your.email@example.com" }`  
`]`  
`dependencies = [`  
    `"aiohttp>=3.8.0",`  
    `"parsel>=1.8.0",`  
    `"pandas>=2.0.0",`  
    `"pyarrow>=12.0.0",`  
    `"fastapi>=0.100.0",   # 為將來升級為API做準備`  
    `"playwright>=1.36.0", # 用於JS渲染兜底`  
    `"python-dotenv>=1.0.0",`  
`]`

`[project.optional-dependencies]`  
`dev = ["pytest", "black", "ruff", "mkdocs"] # 開發依賴`

`[project.scripts] # 定義命令列工具入口點`  
`url2parquet = "url_to_parquet.cli:main"`

`[tool.setuptools.packages.find]`

`where = ["src"]`

### **步驟四：編寫命令列接口 (CLI)**

於 `src/url_to_parquet/cli.py` 中創建。

`python`

`import argparse`  
`import asyncio`  
`from pathlib import Path`  
`from .core import UrlProcessor, OutputFormat`  
`from . import __version__`

`def main():`  
    `"""命令列主入口函數"""`  
    `parser = argparse.ArgumentParser(description="將URL轉換為多種數據格式")`  
    `parser.add_argument("urls", nargs="*", help="要處理的一個或多個URL")`  
    `parser.add_argument("-i", "--input-file", type=Path, help包含URL的文本文件")`  
    `parser.add_argument("-f", "--format", default="parquet", choices=["parquet", "csv", "json", "md"], help="輸出格式")`  
    `parser.add_argument("-o", "--output-dir", default="./output", help="輸出目錄")`  
    `parser.add_argument("--no-playwright", action="store_true", help="禁用Playwright渲染")`  
    `parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")`

    `args = parser.parse_args()`  
    `asyncio.run(run_processor(args))`

`async def run_processor(args):`  
    `"""運行處理器"""`  
    `# 合併從參數和文件中的URL`  
    `urls = args.urls`  
    `if args.input_file:`  
        `urls.extend(args.input_file.read_text().splitlines())`

    `if not urls:`  
        `print("錯誤：未提供任何URL。使用 -h 查看幫助。")`  
        `return`

    `processor = UrlProcessor(output_dir=args.output_dir, enable_playwright=not args.no_playwright)`  
    `result = processor.process(urls=urls, output_format=OutputFormat(args.format))`

    `if result.success:`  
        `print(f"成功！輸出文件：{result.output_path}")`  
    `else:`  
        `print(f"處理失敗：{result.error_message}")`  
        `exit(1)`

`if __name__ == "__main__":`

    `main()`

至此，第一重境界已成。 用户可通過 `pip install .` 安裝你的包，並在Python中 `from url_to_parquet import UrlProcessor` 使用，或在終端中直接使用 `url2parquet https://example.com` 命令。

---

## **第二重境界：RESTful API 服務 (The Microservice)**

欲使此功服務於天下萬般語言，需以HTTP協議包裹之，是為微服務。

### **步驟一：使用 FastAPI 創建 Web 層**

創建 `src/url_to_parquet/api.py`。

`python`

`from fastapi import FastAPI, BackgroundTasks, HTTPException`  
`from fastapi.responses import FileResponse`  
`from pydantic import BaseModel, Field`  
`from typing import List, Optional`  
`import uuid`

`from .core import UrlProcessor, OutputFormat, ProcessingResult, UrlProcessingError`

`app = FastAPI(title="URL to Parquet API", version="0.1.0")`

*`# 內存中存儲任務結果（生產環境請改用Redis或數據庫）`*  
`_job_results = {}`

`class ProcessingRequest(BaseModel):`  
    `"""API請求體模型"""`  
    `urls: List[str] = Field(..., description="要處理的URL列表")`  
    `output_format: OutputFormat = Field(default=OutputFormat.PARQUET, description="輸出格式")`  
    `options: Optional[dict] = Field(default_factory=dict, description="高級選項")`

`class JobStatusResponse(BaseModel):`  
    `"""任務狀態響應模型"""`  
    `job_id: str`  
    `status: str # 'pending', 'processing', 'completed', 'failed'`  
    `result: Optional[ProcessingResult] = None`  
    `download_url: Optional[str] = None`

`@app.post("/jobs", response_model=JobStatusResponse, status_code=202)`  
`async def create_job(request: ProcessingRequest, background_tasks: BackgroundTasks):`  
    `"""提交一個新的處理任務"""`  
    `job_id = str(uuid.uuid4())`  
    `processor = UrlProcessor()`

    `# 將任務加入後台`  
    `background_tasks.add_task(run_processing_task, processor, job_id, request)`

    `_job_results[job_id] = {'status': 'pending', 'request': request}`

    `return JobStatusResponse(job_id=job_id, status='pending')`

`async def run_processing_task(processor: UrlProcessor, job_id: str, request: ProcessingRequest):`  
    `"""後台異步執行任務"""`  
    `try:`  
        `_job_results[job_id]['status'] = 'processing'`  
        `result = processor.process(urls=request.urls, output_format=request.output_format, **request.options)`

        `_job_results[job_id].update({`  
            `'status': 'completed' if result.success else 'failed',`  
            `'result': result,`  
            `'download_url': f"/jobs/{job_id}/download" if result.success else None`  
        `})`  
    `except Exception as e:`  
        `_job_results[job_id] = {'status': 'failed', 'error': str(e)}`

`@app.get("/jobs/{job_id}", response_model=JobStatusResponse)`  
`async def get_job_status(job_id: str):`  
    `"""查詢任務狀態"""`  
    `if job_id not in _job_results:`  
        `raise HTTPException(status_code=404, detail="Job not found")`  
    `return {**{'job_id': job_id}, **_job_results[job_id]}`

`@app.get("/jobs/{job_id}/download")`  
`async def download_result(job_id: str):`  
    `"""下載處理結果文件"""`  
    `job = _job_results.get(job_id)`  
    `if not job or job['status'] != 'completed':`  
        `raise HTTPException(status_code=404, detail="File not ready or not found")`

    `result = job['result']`

    `return FileResponse(path=result.output_path, filename=result.output_path.name)`

### **步驟二：使用容器封裝 (Dockerfile)**

創建 `Dockerfile` 以實現環境一致性。

`dockerfile`

`FROM python:3.11-slim-bookworm`

`# 安裝 Playwright 的系統依賴及中文字體`  
`RUN apt-get update && \`  
    `apt-get install -y --no-install-recommends \`  
    `fonts-wqy-microhei \`  
    `&& rm -rf /var/lib/apt/lists/*`

`WORKDIR /app`

`# 複製依賴定義並安裝`  
`COPY pyproject.toml ./`  
`RUN pip install --no-cache-dir .[dev]  # 根據pyproject.toml安裝依賴`

`# 複製源碼`  
`COPY src/ ./src/`  
`COPY tests/ ./tests/`

`# 安裝當前套件`  
`RUN pip install -e .`

`# 安裝Playwright瀏覽器`  
`RUN playwright install --with-deps chromium`

`# 暴露端口`  
`EXPOSE 8000`

`# 啟動應用`

`CMD ["uvicorn", "url_to_parquet.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]`

至此，第二重境界已成。 你可通過 `docker build -t url2parquet-api .` 構建映像，並通過 `docker run -p 8000:8000 url2parquet-api` 運行一個獨立的API服務。任何語言均可通過HTTP調用之。

---

## **第三重境界：持續交付與文檔 (The Finishing Touch)**

### **文檔為先 (Documentation)**

於 `docs/` 下使用 MkDocs 創建精美文檔，並在 `README.md` 中提供快速開始指南。

`markdown`

`# URL to Parquet ETL`

`[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)]((https://www.python.org/))`  
`[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](((https://opensource.org/licenses/MIT)))`

`一個強大的工具，可將任意URL轉換為結構化的Parquet、CSV、JSON或Markdown文件。`

`## 快速開始`

`### 作為Python庫使用`

```` ```python ````  
`from url_to_parquet import UrlProcessor, OutputFormat`

`processor = UrlProcessor()`  
`result = processor.process(["https://example.com"], OutputFormat.PARQUET)`

`if result.success:`  
    `print(f"文件已保存至: {result.output_path}")`

```` ``` ````

### **持續集成 (CI/CD)**

創建 `.github/workflows/test.yml`，實現自動化測試與發布。

`yaml`

`name: Test and Release`

`on: [push, pull_request]`

`jobs:`  
  `test:`  
    `runs-on: ubuntu-latest`  
    `steps:`  
      `- uses: actions/checkout@v4`  
      `- name: Set up Python`  
        `uses: actions/setup-python@v4`  
        `with:`  
          `python-version: "3.11"`  
      `- name: Install dependencies`  
        `run: pip install .[dev]`  
      `- name: Run tests`  
        `run: pytest -v --cov=src/url_to_parquet tests/`

  `publish:`  
    `needs: test`  
    `runs-on: ubuntu-latest`  
    `if: startsWith(github.ref, 'refs/tags/')`  
    `steps:`  
      `- uses: actions/checkout@v4`  
      `- name: Build and publish to PyPI`  
        `uses: JRubics/poetry-publish@v2.0`  
        `with:`

          `pypi_token: ${{ secrets.PYPI_TOKEN }}`

---

## **總結：封裝之道**

1. 始於接口：首先思考你希望用户如何调用你的代碼，設計出簡潔明了的類與函數。  
2. 忠於實現：將複雜的實現細節隱藏在優雅的接口之後，保證核心邏輯健壯。  
3. 多態出口：提供多種使用方式（庫、CLI、API），以適應不同場景。  
4. 成於交付：通過標準化的打包、容器化和文檔，讓你的成果能被任何人輕鬆獲取和使用。

遵循此大法，你的代碼將從一介脚本，脫胎換骨，成為一件可流傳、可協作、可自豪的藝術品。  
