#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 資料流程測試
測試完整的 ETL 流程：HTML -> Markdown(.md) -> CSV(.csv) -> JSON(.json)
"""

import asyncio
import json
from pathlib import Path
from src.html_to_markdown.data_pipeline import HTMLToMarkdownPipeline, DataPipelineConfig

async def test_complete_pipeline():
    """測試完整的資料流程"""
    print("🚀 開始測試 HTML to Markdown 完整資料流程")
    print("=" * 60)
    
    # 配置資料流程
    config = DataPipelineConfig(
        base_data_dir=Path("data"),
        source_name="html-to-markdown",
        enable_llm_processing=False
    )
    
    # 初始化流程管理器
    pipeline = HTMLToMarkdownPipeline(config)
    
    # 測試用的複雜 HTML 內容
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HTML to Markdown 轉換系統測試頁面 - 完整功能展示</title>
    </head>
    <body>
        <div class="container">
            <h1>HTML to Markdown 轉換系統</h1>
            <p>本系統提供高效的 HTML 內容轉換為 Markdown 格式的完整解決方案，包含豐富的文字處理和結構化轉換功能。這個先進的轉換引擎能夠處理複雜的 HTML 結構，保持原始內容的語義和格式，同時提供高品質的 Markdown 輸出。系統採用多層次的解析策略，確保轉換過程的準確性和可靠性，並支援各種 HTML 元素的智能識別和轉換。</p>
            
            <h2>主要功能</h2>
            <ul>
                <li><strong>智能轉換</strong>：採用先進的 HTML 解析算法，能夠準確識別和轉換各種 HTML 元素為對應的 Markdown 語法</li>
                <li><strong>品質保證</strong>：內建多重驗證機制，確保轉換後的 Markdown 格式正確且語義完整</li>
                <li><strong>批量處理</strong>：支援大量 HTML 文件的批量轉換，提高工作效率和處理速度</li>
                <li><strong>自定義配置</strong>：提供豐富的配置選項，允許用戶根據需求調整轉換規則和輸出格式</li>
                <li><strong>API 整合</strong>：提供完整的 RESTful API 介面，方便與其他系統和應用程式整合</li>
                <li><strong>錯誤處理</strong>：完善的錯誤檢測和處理機制，確保轉換過程的穩定性和可靠性</li>
            </ul>
            
            <h2>技術架構</h2>
            <table border="1">
                <thead>
                    <tr>
                        <th>層級</th>
                        <th>技術棧</th>
                        <th>說明</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>前端</td>
                        <td>React + TypeScript</td>
                        <td>現代化的使用者介面</td>
                    </tr>
                    <tr>
                        <td>後端</td>
                        <td>Python + FastAPI</td>
                        <td>高性能的 API 服務</td>
                    </tr>
                    <tr>
                        <td>資料庫</td>
                        <td>PostgreSQL + Redis</td>
                        <td>持久化存儲和快取</td>
                    </tr>
                    <tr>
                        <td>轉換引擎</td>
                        <td>Beautiful Soup + Markdownify</td>
                        <td>高效的 HTML 解析和轉換</td>
                    </tr>
                </tbody>
            </table>
            
            <h2>轉換品質評估</h2>
            <blockquote>
                <p>我們的系統採用多維度品質評估機制，確保轉換結果的高品質，評估指標包括：</p>
                <ol>
                    <li>語法正確性：檢查 Markdown 語法的正確性和完整性</li>
                    <li>內容完整性：確保原始 HTML 內容在轉換過程中不會遺失</li>
                    <li>格式一致性：保持轉換後格式的統一性和可讀性</li>
                    <li>結構保持度：維持原始文檔的邏輯結構和層次關係</li>
                    <li>效能指標：監控轉換速度和系統資源使用情況</li>
                    <li>相容性測試：確保轉換結果在不同 Markdown 渲染器中的相容性</li>
                </ol>
            </blockquote>
            
            <h3>程式碼範例</h3>
            <pre><code class="python">
# 使用 HTML to Markdown 轉換器
from html_to_markdown import HTMLToMarkdownConverter

converter = HTMLToMarkdownConverter()
html_content = "<h1>標題</h1><p>這是一段文字內容。</p>"
markdown_result = await converter.convert(html_content)
print(f"轉換結果：{markdown_result}")

# 批量轉換範例
files = ["file1.html", "file2.html", "file3.html"]
results = await converter.batch_convert(files)
for file, result in results.items():
    print(f"{file} -> {result.output_path}")
            </code></pre>
            
            <h3>聯絡資訊</h3>
            <p>如有任何問題，請聯絡：<a href="mailto:admin@example.com">admin@example.com</a></p>
            
            <footer>
                <p><em>© 2024 HTML to Markdown 轉換系統. 版權所有. 本系統提供企業級的文檔轉換解決方案，支援多種輸入格式和自定義輸出選項，是現代文檔處理工作流程的理想選擇。</em></p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    try:
        # 執行完整的資料流程
        print("📝 開始執行完整資料流程...")
        
        result = await pipeline.run_full_pipeline(
            html_content=test_html,
            source_url="https://example.com/proxy-crawler-system",
            metadata={
                "author": "系統管理員",
                "category": "技術文檔",
                "version": "1.0",
                "language": "zh-TW"
            }
        )
        
        print("\n✅ 資料流程執行成功！")
        print("📁 產生的檔案：")
        print(f"   📄 原始檔案 (.md): {result['raw']}")
        print(f"   📊 處理檔案 (.csv): {result['processed']}")
        print(f"   🗃️ 轉換檔案 (.json): {result['transformed']}")
        
        # 顯示各階段檔案內容預覽
        await show_file_previews(result)
        
        # 顯示流程狀態
        status = pipeline.get_pipeline_status()
        print("\n📈 流程狀態統計：")
        print(f"   原始檔案數量: {status['raw_files']}")
        print(f"   處理檔案數量: {status['processed_files']}")
        print(f"   轉換檔案數量: {status['transformed_files']}")
        
        print("\n🎯 測試完成！所有階段都成功執行。")
        
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        raise

async def show_file_previews(result: dict):
    """顯示各階段檔案的內容預覽"""
    print("\n" + "=" * 60)
    print("📋 檔案內容預覽")
    print("=" * 60)
    
    # 預覽原始 Markdown 檔案
    print("\n📄 原始 Markdown 檔案 (.md) - 前 500 字符：")
    print("-" * 40)
    with open(result['raw'], 'r', encoding='utf-8') as f:
        content = f.read()
        print(content[:500] + ("..." if len(content) > 500 else ""))
    
    # 預覽 CSV 檔案
    print("\n📊 處理後 CSV 檔案 (.csv) - 標題行：")
    print("-" * 40)
    with open(result['processed'], 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            print(f"欄位：{lines[0].strip()}")
            if len(lines) > 1:
                print(f"第一筆資料（部分）：{lines[1][:100]}...")
    
    # 預覽 JSON 檔案
    print("\n🗃️ 轉換後 JSON 檔案 (.json) - 結構預覽：")
    print("-" * 40)
    with open(result['transformed'], 'r', encoding='utf-8') as f:
        data = json.load(f)
        if data:
            record = data[0]
            print(f"記錄數量：{len(data)}")
            print(f"第一筆記錄結構：")
            for key, value in record.items():
                if key == 'full_content':
                    print(f"  {key}: {str(value)[:50]}...")
                elif isinstance(value, str) and len(value) > 50:
                    print(f"  {key}: {value[:50]}...")
                else:
                    print(f"  {key}: {value}")

async def test_individual_stages():
    """測試各個階段的獨立功能"""
    print("\n🔧 測試各階段獨立功能")
    print("=" * 60)
    
    config = DataPipelineConfig(
        base_data_dir=Path("data"),
        source_name="html-to-markdown"
    )
    
    pipeline = HTMLToMarkdownPipeline(config)
    
    # 簡單的測試 HTML
    simple_html = """
    <div>
        <h1>HTML to Markdown 轉換系統測試</h1>
        <p>這是一個完整的測試內容，用於驗證 HTML to Markdown 轉換功能的正確性和穩定性。本測試涵蓋了基本的 HTML 元素轉換，包括標題、段落、列表等常見結構。</p>
        <h2>主要功能特點</h2>
        <ul>
            <li>支援多種 HTML 元素的智能轉換</li>
            <li>保持原始文檔的結構和格式</li>
            <li>提供高品質的 Markdown 輸出</li>
            <li>完整的錯誤處理和驗證機制</li>
        </ul>
        <p>系統採用先進的解析算法，能夠準確識別 HTML 結構並轉換為對應的 Markdown 語法，確保轉換結果的準確性和可讀性。</p>
    </div>
    """
    
    try:
        # 測試階段1
        print("\n🔄 測試階段1：HTML -> Markdown")
        raw_path = await pipeline.stage1_save_raw_markdown(
            html_content=simple_html,
            source_url="https://test.com/simple",
            metadata={"test": "stage1"}
        )
        print(f"✅ 階段1完成：{raw_path}")
        
        # 測試階段2
        print("\n🔄 測試階段2：Markdown -> CSV")
        csv_path = pipeline.stage2_parse_to_csv(raw_path)
        print(f"✅ 階段2完成：{csv_path}")
        
        # 測試階段3
        print("\n🔄 測試階段3：CSV -> JSON")
        json_path = pipeline.stage3_transform_to_json(csv_path)
        print(f"✅ 階段3完成：{json_path}")
        
        print("\n🎯 所有階段獨立測試通過！")
        
    except Exception as e:
        print(f"❌ 階段測試失敗：{e}")
        raise

if __name__ == "__main__":
    async def main():
        """主測試函數"""
        print("🧪 HTML to Markdown 資料流程測試套件")
        print("=" * 60)
        
        # 測試完整流程
        await test_complete_pipeline()
        
        # 測試各階段獨立功能
        await test_individual_stages()
        
        print("\n🏆 所有測試完成！")
        print("\n📁 檢查 data/ 目錄以查看產生的檔案：")
        print("   data/raw/html-to-markdown/        - 原始 .md 檔案")
        print("   data/processed/html-to-markdown/  - 處理後 .csv 檔案")
        print("   data/transformed/html-to-markdown/ - 轉換後 .json 檔案")
    
    asyncio.run(main())