#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 轉換系統測試腳本
"""

import sys
import asyncio
from pathlib import Path

# 添加 src 目錄到 Python 路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("HTML to Markdown 轉換系統測試")
print("=" * 50)

try:
    from html_to_markdown import (
        MarkdownifyConverter,
        ConversionConfig,
        ConversionEngine,
        ContentScope
    )
    print("✓ 模組導入成功")
except Exception as e:
    print(f"✗ 模組導入失敗: {e}")
    sys.exit(1)

async def test_conversion():
    """測試轉換功能"""
    try:
        # 創建配置
        config = ConversionConfig(
            engine=ConversionEngine.MARKDOWNIFY,
            content_scope=ContentScope.FULL_PAGE
        )
        print("✓ 配置創建成功")
        
        # 創建轉換器
        converter = MarkdownifyConverter(config)
        print("✓ 轉換器創建成功")
        
        # 測試 HTML
        test_html = "<h1>測試標題</h1><p>這是一個測試段落。</p>"
        
        # 執行轉換
        result = await converter.convert(test_html)
        print("✓ 轉換執行成功")
        
        print(f"\n轉換結果:")
        print(f"原始 HTML: {test_html}")
        print(f"轉換後 Markdown: {result.markdown.strip()}")
        print(f"處理時間: {result.processing_time:.3f} 秒")
        
        return True
        
    except Exception as e:
        print(f"✗ 轉換測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_conversion())
    
    if success:
        print("\n=== 測試完成 ===")
        print("✓ HTML to Markdown 轉換系統運行正常！")
    else:
        print("\n=== 測試失敗 ===")
        print("✗ 請檢查系統配置和依賴。")
        sys.exit(1)