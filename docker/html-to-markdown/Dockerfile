# HTML to Markdown 轉換服務 Docker 映像
# 基於 Python 3.11 的輕量級映像

FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=docker
ENV INPUT_DIR=/app/input
ENV PROCESSING_DIR=/app/processing
ENV OUTPUT_DIR=/app/output

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv 包管理器
RUN pip install uv

# 複製依賴文件
    COPY requirements_html_to_markdown.txt .
    
    # 安裝 Python 依賴
    RUN pip install -r requirements_html_to_markdown.txt

# 複製源代碼和配置
COPY src/ ./src/
COPY examples/ ./examples/
COPY tests/ ./tests/
COPY database_config.py .

# 創建 ETL 流程目錄
RUN mkdir -p /app/input /app/processing /app/output /app/logs /app/cache

# 設置權限
RUN chmod +x src/html_to_markdown/cli.py

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import html_to_markdown; print('OK')" || exit 1

# 暴露端口（API 服務）
EXPOSE 8001

# 創建非 root 用戶
RUN useradd -m -u 1000 converter && \
    chown -R converter:converter /app

USER converter

# 默認命令（啟動 API 服務）
CMD ["python", "-m", "src.html_to_markdown.api_server"]