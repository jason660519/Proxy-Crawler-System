#!/usr/bin/env python3
"""
服務器啟動腳本
解決模組導入問題
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 導入並啟動應用
if __name__ == "__main__":
    import uvicorn
    from src.main import app
    
    print("🚀 啟動 JasonSpider 服務器...")
    print(f"📁 專案目錄: {project_root}")
    print(f"🌐 服務地址: http://localhost:8000")
    print(f"📚 API 文檔: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
