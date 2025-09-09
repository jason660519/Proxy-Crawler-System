#!/usr/bin/env python3
"""
直接測試pipeline重定向處理
"""

import asyncio
from src.url2parquet.core.pipeline import Url2ParquetPipeline
from src.url2parquet.config import PipelineOptions

async def test_pipeline_redirect():
    """測試pipeline重定向處理"""
    print("🚀 開始測試pipeline重定向處理...")
    
    # 測試重定向URL
    test_url = "https://www.sslproxies.org/"
    
    options = PipelineOptions(
        urls=[test_url],
        engine="smart",
        output_formats=["md", "json", "parquet"],
        obey_robots_txt=True,
        timeout_seconds=30,
        max_concurrency=4,
        work_dir="data/url2parquet",
    )
    
    pipeline = Url2ParquetPipeline(options)
    
    try:
        result = await pipeline.process_single(test_url)
        print("✅ Pipeline處理成功!")
        print(f"結果: {result}")
    except Exception as e:
        print(f"❌ Pipeline處理失敗: {e}")
        print(f"錯誤類型: {type(e)}")
        print(f"錯誤詳情: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_pipeline_redirect())
