#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown 資料流程展示腳本

這個腳本展示了完整的 HTML to Markdown ETL 流程，
包括原始資料處理、結構化解析和最終的 JSON 轉換。
"""

import asyncio
from pathlib import Path
from loguru import logger

from src.html_to_markdown.data_pipeline import HTMLToMarkdownPipeline, DataPipelineConfig


async def demo_complete_pipeline():
    """展示完整的資料流程"""
    print("\n🚀 HTML to Markdown 資料流程展示")
    print("=" * 60)
    
    # 配置資料流程
    config = DataPipelineConfig(
        base_data_dir=Path("data"),
        source_name="html-to-markdown"
    )
    
    pipeline = HTMLToMarkdownPipeline(config)
    
    # 示範用的 HTML 內容
    demo_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>企業級 HTML to Markdown 轉換解決方案</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <header>
            <h1>HTML to Markdown 轉換系統</h1>
            <p class="subtitle">企業級文檔處理解決方案</p>
        </header>
        
        <main>
            <section id="overview">
                <h2>系統概述</h2>
                <p>本系統提供高效、可靠的 HTML 內容轉換為 Markdown 格式的完整解決方案。
                採用先進的解析技術和多層次驗證機制，確保轉換結果的準確性和一致性。</p>
                
                <h3>核心優勢</h3>
                <ul>
                    <li><strong>智能解析</strong>：採用多引擎解析策略，自動選擇最佳轉換方案</li>
                    <li><strong>品質保證</strong>：內建品質評分系統，確保輸出品質</li>
                    <li><strong>批量處理</strong>：支援大規模文檔批量轉換</li>
                    <li><strong>API 整合</strong>：提供完整的 RESTful API 介面</li>
                </ul>
            </section>
            
            <section id="features">
                <h2>技術特點</h2>
                <table border="1">
                    <thead>
                        <tr>
                            <th>功能模組</th>
                            <th>技術實現</th>
                            <th>效能指標</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>HTML 解析</td>
                            <td>Beautiful Soup + lxml</td>
                            <td>&gt; 1000 docs/min</td>
                        </tr>
                        <tr>
                            <td>Markdown 轉換</td>
                            <td>Markdownify + 自定義規則</td>
                            <td>99.5% 準確率</td>
                        </tr>
                        <tr>
                            <td>品質評估</td>
                            <td>多維度評分算法</td>
                            <td>實時監控</td>
                        </tr>
                    </tbody>
                </table>
            </section>
            
            <section id="workflow">
                <h2>工作流程</h2>
                <blockquote>
                    <p><em>"我們的三階段 ETL 流程確保了資料處理的完整性和可追溯性："</em></p>
                    <ol>
                        <li><strong>Extract（提取）</strong>：從 HTML 源文件中提取結構化內容</li>
                        <li><strong>Transform（轉換）</strong>：將 HTML 內容轉換為高品質的 Markdown 格式</li>
                        <li><strong>Load（載入）</strong>：將處理結果存儲為結構化的 JSON 格式</li>
                    </ol>
                </blockquote>
            </section>
            
            <section id="code-example">
                <h2>使用範例</h2>
                <pre><code class="python">
# 基本使用方式
from html_to_markdown import HTMLToMarkdownPipeline

# 初始化流程
pipeline = HTMLToMarkdownPipeline(config)

# 執行完整的 ETL 流程
result = await pipeline.run_complete_pipeline(
    html_content=html_content,
    source_url="https://example.com",
    metadata={"category": "documentation"}
)

print(f"處理完成：{result.success}")
print(f"輸出檔案：{result.output_files}")
                </code></pre>
            </section>
        </main>
        
        <footer>
            <p><small>© 2024 HTML to Markdown 轉換系統 | 企業級文檔處理解決方案</small></p>
        </footer>
    </body>
    </html>
    """
    
    try:
        print("\n📝 開始處理示範 HTML 內容...")
        
        # 執行完整的 ETL 流程
        result = await pipeline.run_complete_pipeline(
            html_content=demo_html,
            source_url="https://demo.html-to-markdown.com",
            metadata={
                "category": "demo",
                "type": "enterprise_solution",
                "version": "1.0"
            }
        )
        
        # 顯示處理結果
        print("\n📊 處理結果摘要：")
        print(f"   ✅ 處理狀態：{'成功' if result.success else '失敗'}")
        print(f"   📁 總檔案數：{result.total_files}")
        print(f"   ✅ 成功轉換：{result.successful_conversions}")
        print(f"   ❌ 失敗轉換：{result.failed_conversions}")
        print(f"   📈 成功率：{result.success_rate:.1%}")
        print(f"   ⏱️  處理時間：{result.processing_time:.3f} 秒")
        
        if result.output_files:
            print("\n📂 產生的檔案：")
            for file_path in result.output_files:
                print(f"   📄 {file_path}")
        
        if result.errors:
            print("\n⚠️  錯誤訊息：")
            for error in result.errors:
                print(f"   ❌ {error}")
        
        # 顯示品質指標
        if result.conversion_results:
            conversion_result = result.conversion_results[0]
            print("\n🎯 品質指標：")
            print(f"   📏 原始長度：{conversion_result.original_length} 字符")
            print(f"   📏 轉換長度：{conversion_result.converted_length} 字符")
            print(f"   ⚡ 處理速度：{conversion_result.original_length / conversion_result.processing_time:.0f} 字符/秒")
            print(f"   🎨 使用引擎：{conversion_result.engine_used.value}")
        
        print("\n🎉 展示完成！")
        print("\n💡 提示：")
        print("   - 查看 data/raw/html-to-markdown/ 目錄中的原始 .md 檔案")
        print("   - 查看 data/processed/html-to-markdown/ 目錄中的結構化 .csv 檔案")
        print("   - 查看 data/transformed/html-to-markdown/ 目錄中的最終 .json 檔案")
        
    except Exception as e:
        logger.error(f"展示過程中發生錯誤：{e}")
        print(f"\n❌ 展示失敗：{e}")


async def demo_individual_stages():
    """展示各個階段的獨立功能"""
    print("\n🔧 各階段功能展示")
    print("=" * 60)
    
    config = DataPipelineConfig(
        base_data_dir=Path("data"),
        source_name="html-to-markdown"
    )
    
    pipeline = HTMLToMarkdownPipeline(config)
    
    # 簡化的測試內容
    test_html = """
    <article>
        <h1>階段測試文檔</h1>
        <p>這是用於測試各個處理階段的示範內容。每個階段都會對資料進行特定的處理和轉換。</p>
        <h2>處理階段說明</h2>
        <ul>
            <li>階段1：HTML 轉換為 Markdown 格式</li>
            <li>階段2：解析 Markdown 並提取結構化資料</li>
            <li>階段3：轉換為 JSON 格式並計算品質指標</li>
        </ul>
        <p>透過這個三階段的處理流程，我們能夠確保資料的完整性和一致性。</p>
    </article>
    """
    
    try:
        # 階段1：HTML -> Markdown
        print("\n🔄 階段1：HTML -> Markdown")
        raw_path = await pipeline.stage1_save_raw_markdown(
            html_content=test_html,
            source_url="https://demo.test/stages",
            metadata={"stage": "demo"}
        )
        print(f"   ✅ 完成：{raw_path}")
        
        # 階段2：Markdown -> CSV
        print("\n🔄 階段2：Markdown -> CSV")
        csv_path = pipeline.stage2_parse_to_csv(raw_path)
        print(f"   ✅ 完成：{csv_path}")
        
        # 階段3：CSV -> JSON
        print("\n🔄 階段3：CSV -> JSON")
        json_path = pipeline.stage3_transform_to_json(csv_path)
        print(f"   ✅ 完成：{json_path}")
        
        print("\n🎯 所有階段測試完成！")
        
    except Exception as e:
        logger.error(f"階段測試中發生錯誤：{e}")
        print(f"\n❌ 階段測試失敗：{e}")


async def main():
    """主要展示函數"""
    print("🌟 歡迎使用 HTML to Markdown 資料流程展示系統")
    print("\n選擇展示模式：")
    print("1. 完整流程展示（推薦）")
    print("2. 各階段獨立展示")
    print("3. 兩者都執行")
    
    try:
        choice = input("\n請輸入選擇 (1/2/3，預設為1)：").strip() or "1"
        
        if choice in ["1", "3"]:
            await demo_complete_pipeline()
        
        if choice in ["2", "3"]:
            await demo_individual_stages()
        
        print("\n✨ 展示結束，感謝使用！")
        
    except KeyboardInterrupt:
        print("\n\n👋 使用者中斷，展示結束。")
    except Exception as e:
        logger.error(f"展示過程中發生未預期的錯誤：{e}")
        print(f"\n❌ 發生錯誤：{e}")


if __name__ == "__main__":
    # 配置日誌
    logger.remove()
    logger.add(
        "logs/demo_pipeline_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # 執行展示
    asyncio.run(main())