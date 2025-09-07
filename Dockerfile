# Proxy Crawler 主應用程式 Dockerfile
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv 包管理器
RUN pip install uv

# 複製依賴文件
COPY requirements.txt ./

# 安裝 Python 依賴
RUN pip install -r requirements.txt

# 複製源碼
COPY src/ ./src/
COPY *.py ./

# 創建必要的目錄
RUN mkdir -p /app/logs /app/data /app/output

# 設定環境變數
ENV PYTHONPATH=/app
ENV ENVIRONMENT=docker

# 健康檢查（對齊代理管理 API）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 暴露端口
EXPOSE 8000

# 創建非 root 用戶
RUN useradd -m -u 1000 crawler && \
    chown -R crawler:crawler /app

# 切換到非 root 用戶
USER crawler

# 啟動命令：代理管理 API
CMD ["python", "-m", "uvicorn", "src.proxy_manager.api:app", "--host", "0.0.0.0", "--port", "8000"]