#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理IP驗證測試腳本
測試 UTF-8onlyip11.csv 中的IP地址
"""

import asyncio
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# 導入我們的代理驗證模組
from src.proxy_manager.validators.proxy_validator import ProxyValidator, ValidationResult, ProxyStatus, AnonymityLevel
from src.proxy_manager.models import ProxyNode, ProxyProtocol, ProxyAnonymity, ProxyStatus as ModelProxyStatus

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('proxy_validation_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def load_ips_from_csv(csv_file_path: str) -> List[str]:
    """從CSV文件加載IP地址"""
    ips = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row and row[0].strip():  # 確保第一列有IP地址
                    ip = row[0].strip()
                    if ip:  # 確保不是空字符串
                        ips.append(ip)
        logger.info(f"✅ 從 {csv_file_path} 加載了 {len(ips)} 個IP地址")
    except Exception as e:
        logger.error(f"❌ 加載CSV文件失敗: {e}")
    return ips

def create_proxy_nodes(ips: List[str], default_port: int = 8080) -> List[ProxyNode]:
    """將IP地址轉換為ProxyNode對象"""
    proxy_nodes = []
    for ip in ips:
        # 創建HTTP代理節點（默認端口8080）
        proxy_http = ProxyNode(
            host=ip,
            port=default_port,
            protocol=ProxyProtocol.HTTP,
            anonymity=ProxyAnonymity.UNKNOWN,
            country="Unknown",
            source="CSV測試"
        )
        proxy_nodes.append(proxy_http)
        
        # 也測試常見的代理端口
        for port in [3128, 8888, 1080]:
            proxy_alt = ProxyNode(
                host=ip,
                port=port,
                protocol=ProxyProtocol.HTTP,
                anonymity=ProxyAnonymity.UNKNOWN,
                country="Unknown",
                source="CSV測試"
            )
            proxy_nodes.append(proxy_alt)
    
    logger.info(f"✅ 創建了 {len(proxy_nodes)} 個代理節點進行測試")
    return proxy_nodes

async def test_proxy_validation():
    """測試代理驗證功能"""
    logger.info("🚀 開始代理IP驗證測試...")
    
    # 1. 加載CSV文件中的IP地址
    csv_file = "test_input_csv_exel files/UTF-8onlyip11.csv"
    ips = load_ips_from_csv(csv_file)
    
    if not ips:
        logger.error("❌ 沒有找到有效的IP地址")
        return
    
    # 只測試前10個IP以節省時間
    test_ips = ips[:10]
    logger.info(f"📋 將測試前 {len(test_ips)} 個IP地址")
    
    # 2. 創建代理節點
    proxy_nodes = create_proxy_nodes(test_ips)
    
    # 3. 配置驗證器（使用默認配置）
    # 4. 創建驗證器並測試
    validator = ProxyValidator(
        timeout=10.0,
        max_concurrent=5,
        real_ip=None
    )
    
    try:
        logger.info("✅ 代理驗證器準備就緒")
        
        # 執行驗證
        results = await validator.validate_proxies(proxy_nodes)
        
        # 5. 分析結果
        working_proxies = [r for r in results if r.status == ProxyStatus.WORKING]
        failed_proxies = [r for r in results if r.status != ProxyStatus.WORKING]
        
        logger.info(f"\n📊 驗證結果統計:")
        logger.info(f"   總測試數量: {len(results)}")
        logger.info(f"   ✅ 可用代理: {len(working_proxies)}")
        logger.info(f"   ❌ 不可用代理: {len(failed_proxies)}")
        logger.info(f"   📈 成功率: {len(working_proxies)/len(results)*100:.1f}%")
            
        # 6. 詳細結果報告
        print("\n" + "="*80)
        print("📋 詳細驗證結果報告")
        print("="*80)
        
        if working_proxies:
            print(f"\n✅ 可用代理 ({len(working_proxies)} 個):")
            for result in working_proxies:
                proxy = result.proxy
                print(f"   🟢 {proxy.host}:{proxy.port} ({proxy.protocol})")
                print(f"      響應時間: {result.response_time:.2f}s" if result.response_time else "      響應時間: N/A")
                print(f"      匿名度: {result.anonymity_level.value if result.anonymity_level else 'Unknown'}")
                if result.detected_country:
                    print(f"      地理位置: {result.detected_country}")
                if hasattr(result, 'error_message') and result.error_message:
                    print(f"      備註: {result.error_message}")
                print()
        
        if failed_proxies:
            print(f"\n❌ 不可用代理 ({len(failed_proxies)} 個):")
            for result in failed_proxies[:10]:  # 只顯示前10個失敗的
                proxy = result.proxy
                print(f"   🔴 {proxy.host}:{proxy.port} ({proxy.protocol})")
                print(f"      錯誤: {result.error_message if result.error_message else 'Unknown error'}")
                print()
        
        # 7. 保存結果到JSON文件
        results_data = {
            'test_time': datetime.now().isoformat(),
            'total_tested': len(results),
            'working_count': len(working_proxies),
            'failed_count': len(failed_proxies),
            'success_rate': len(working_proxies)/len(results)*100,
            'working_proxies': [
                {
                     'host': r.proxy.host,
                     'port': r.proxy.port,
                     'protocol': r.proxy.protocol.value if hasattr(r.proxy.protocol, 'value') else str(r.proxy.protocol),
                     'response_time': r.response_time,
                     'anonymity': r.anonymity_level.value if r.anonymity_level else None,
                     'country': r.detected_country,
                     'status': r.status.value
                 } for r in working_proxies
            ],
            'failed_proxies': [
                {
                     'host': r.proxy.host,
                     'port': r.proxy.port,
                     'protocol': r.proxy.protocol.value if hasattr(r.proxy.protocol, 'value') else str(r.proxy.protocol),
                     'error': r.error_message,
                     'status': r.status.value
                 } for r in failed_proxies
            ]
        }
        
        with open('proxy_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        logger.info("💾 結果已保存到 proxy_validation_results.json")
        
    except Exception as e:
        logger.error(f"❌ 驗證過程中發生錯誤: {e}")

def main():
    """主函數"""
    print("🔍 代理IP驗證模組測試")
    print("=" * 50)
    print(f"測試文件: UTF-8onlyip11.csv")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 運行異步測試
    asyncio.run(test_proxy_validation())
    
    print("\n✅ 測試完成！")
    print("📄 詳細日誌請查看: proxy_validation_test.log")
    print("📊 結果數據請查看: proxy_validation_results.json")

if __name__ == "__main__":
    main()