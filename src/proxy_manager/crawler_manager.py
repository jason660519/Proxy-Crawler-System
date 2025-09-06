"""爬蟲管理器模組

此模組提供統一的代理爬蟲管理功能，包括：
- 多源代理爬取調度
- 代理驗證和過濾
- 數據輸出和存儲
- 統計信息收集
- 配置管理

支援的代理源：
- SSLProxies.org
- Geonode.com
- Free-Proxy-List.net
- 其他自定義爬蟲
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Type
from dataclasses import asdict

from loguru import logger

from .crawlers.base_crawler import BaseCrawler, ProxyNode
from .crawlers.sslproxies_org__proxy_crawler__ import SSLProxiesCrawler
from .crawlers.geonode_com__proxy_crawler__ import GeonodeCrawler
from .crawlers.free_proxy_list_net__proxy_crawler__ import FreeProxyListCrawler
from .validators.proxy_validator import ProxyValidator, ValidationResult, ProxyStatus, AnonymityLevel


class CrawlerManager:
    """爬蟲管理器
    
    統一管理多個代理爬蟲，提供代理收集、驗證、過濾和輸出功能
    """
    
    def __init__(self, 
                 output_dir: Optional[Path] = None,
                 enable_validation: bool = True,
                 validation_timeout: float = 10.0,
                 max_concurrent_validation: int = 50,
                 enable_deduplication: bool = True,
                 etl_mode: bool = False):
        """初始化爬蟲管理器
        
        Args:
            output_dir: 輸出目錄路徑（僅在非ETL模式下使用）
            enable_validation: 是否啟用代理驗證
            validation_timeout: 驗證超時時間
            max_concurrent_validation: 最大並發驗證數
            enable_deduplication: 是否啟用去重
            etl_mode: 是否啟用ETL模式，按照ETL規範存放檔案
        """
        self.etl_mode = etl_mode
        
        if etl_mode:
            # ETL模式：按照ETL流程規範創建目錄結構
            self.base_dir = Path("data")
            self.raw_dir = self.base_dir / "raw"
            self.processed_dir = self.base_dir / "processed" 
            self.validated_dir = self.base_dir / "validated"
            self.reports_dir = self.base_dir / "reports"
            
            # 創建所有必要的目錄
            for directory in [self.raw_dir, self.processed_dir, self.validated_dir, self.reports_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                
            self.output_dir = self.processed_dir  # 預設輸出到processed目錄
        else:
            # 傳統模式：使用指定的輸出目錄
            self.output_dir = output_dir or Path("data/proxy_manager")
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_validation = enable_validation
        self.enable_deduplication = enable_deduplication
        
        # 初始化驗證器
        if enable_validation:
            self.validator = ProxyValidator(
                timeout=validation_timeout,
                max_concurrent=max_concurrent_validation
            )
        else:
            self.validator = None
        
        # 註冊可用的爬蟲
        self.available_crawlers: Dict[str, Type[BaseCrawler]] = {
            'sslproxies': SSLProxiesCrawler,
            'geonode': GeonodeCrawler,
            'free_proxy_list': FreeProxyListCrawler,
        }
        
        # 統計信息
        self.stats = {
            'total_crawled': 0,
            'total_unique': 0,
            'total_validated': 0,
            'total_working': 0,
            'by_source': {},
            'by_protocol': {},
            'by_country': {},
            'by_anonymity': {},
            'crawl_duration': 0.0,
            'validation_duration': 0.0,
            'start_time': None,
            'end_time': None
        }
    
    async def crawl_all_sources(self, 
                              sources: Optional[List[str]] = None,
                              validate_proxies: Optional[bool] = None,
                              output_formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """從所有或指定源爬取代理
        
        Args:
            sources: 要爬取的源列表，None表示所有源
            validate_proxies: 是否驗證代理，None使用默認設置
            output_formats: 輸出格式列表 ['json', 'markdown', 'csv']
            
        Returns:
            包含爬取結果和統計信息的字典
        """
        self.stats['start_time'] = time.time()
        
        # 確定要使用的源
        if sources is None:
            sources = list(self.available_crawlers.keys())
        
        # 確定是否驗證
        if validate_proxies is None:
            validate_proxies = self.enable_validation
        
        # 確定輸出格式
        if output_formats is None:
            output_formats = ['json', 'markdown']
        
        logger.info(f"開始從 {len(sources)} 個源爬取代理: {', '.join(sources)}")
        
        # 爬取階段
        crawl_start = time.time()
        all_proxies = await self._crawl_from_sources(sources)
        self.stats['crawl_duration'] = time.time() - crawl_start
        
        logger.info(f"爬取完成，共獲得 {len(all_proxies)} 個代理")
        
        # 去重階段
        if self.enable_deduplication:
            unique_proxies = self._deduplicate_proxies(all_proxies)
            logger.info(f"去重後剩餘 {len(unique_proxies)} 個唯一代理")
        else:
            unique_proxies = all_proxies
        
        self.stats['total_crawled'] = len(all_proxies)
        self.stats['total_unique'] = len(unique_proxies)
        
        # 驗證階段
        validation_results = []
        working_proxies = unique_proxies
        
        if validate_proxies and self.validator and unique_proxies:
            logger.info(f"開始驗證 {len(unique_proxies)} 個代理")
            validation_start = time.time()
            
            validation_results = await self.validator.validate_proxies(
                unique_proxies, 
                test_anonymity=True, 
                test_geo=False
            )
            
            working_proxies = self.validator.get_working_proxies(validation_results)
            
            self.stats['validation_duration'] = time.time() - validation_start
            self.stats['total_validated'] = len(validation_results)
            self.stats['total_working'] = len(working_proxies)
            
            logger.info(f"驗證完成，{len(working_proxies)} 個代理可用")
        
        # 更新統計信息
        self._update_detailed_stats(unique_proxies, validation_results)
        
        # 生成輸出
        output_files = await self._generate_outputs(
            working_proxies, 
            validation_results, 
            output_formats
        )
        
        self.stats['end_time'] = time.time()
        
        # 返回結果
        result = {
            'proxies': working_proxies,
            'validation_results': validation_results,
            'stats': self.stats.copy(),
            'output_files': output_files
        }
        
        logger.info(f"代理收集完成，總耗時 {self.stats['end_time'] - self.stats['start_time']:.2f}s")
        
        return result
    
    async def _crawl_from_sources(self, sources: List[str]) -> List[ProxyNode]:
        """從指定源爬取代理
        
        Args:
            sources: 源名稱列表
            
        Returns:
            所有爬取到的代理列表
        """
        all_proxies = []
        
        # 並發爬取所有源
        tasks = []
        for source_name in sources:
            if source_name in self.available_crawlers:
                crawler_class = self.available_crawlers[source_name]
                task = self._crawl_single_source(source_name, crawler_class)
                tasks.append(task)
            else:
                logger.warning(f"未知的代理源: {source_name}")
        
        # 等待所有爬取任務完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        for i, result in enumerate(results):
            source_name = sources[i] if i < len(sources) else f"source_{i}"
            
            if isinstance(result, Exception):
                logger.error(f"爬取源 {source_name} 時發生異常: {str(result)}")
                self.stats['by_source'][source_name] = {'count': 0, 'error': str(result)}
            elif isinstance(result, list):
                all_proxies.extend(result)
                self.stats['by_source'][source_name] = {'count': len(result)}
                logger.info(f"從 {source_name} 獲得 {len(result)} 個代理")
            else:
                logger.warning(f"源 {source_name} 返回了意外的結果類型: {type(result)}")
                self.stats['by_source'][source_name] = {'count': 0, 'error': 'Unexpected result type'}
        
        return all_proxies
    
    async def _crawl_single_source(self, source_name: str, crawler_class: Type[BaseCrawler]) -> List[ProxyNode]:
        """爬取單個源
        
        Args:
            source_name: 源名稱
            crawler_class: 爬蟲類
            
        Returns:
            代理列表
        """
        try:
            async with crawler_class() as crawler:
                proxies = await crawler.crawl()
                return proxies
        except Exception as e:
            logger.error(f"爬取 {source_name} 時發生錯誤: {str(e)}")
            raise
    
    def _deduplicate_proxies(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """去除重複的代理
        
        Args:
            proxies: 代理列表
            
        Returns:
            去重後的代理列表
        """
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            # 使用 IP:Port 作為唯一標識
            key = f"{proxy.ip}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    def _update_detailed_stats(self, proxies: List[ProxyNode], validation_results: List[ValidationResult]):
        """更新詳細統計信息
        
        Args:
            proxies: 代理列表
            validation_results: 驗證結果列表
        """
        # 按協議統計
        for proxy in proxies:
            protocol = proxy.protocol
            self.stats['by_protocol'][protocol] = self.stats['by_protocol'].get(protocol, 0) + 1
            
            country = proxy.country
            self.stats['by_country'][country] = self.stats['by_country'].get(country, 0) + 1
        
        # 按匿名等級統計（如果有驗證結果）
        for result in validation_results:
            if result.status == ProxyStatus.WORKING:
                anonymity = result.anonymity_level.value
                self.stats['by_anonymity'][anonymity] = self.stats['by_anonymity'].get(anonymity, 0) + 1
    
    async def _generate_outputs(self, 
                              proxies: List[ProxyNode], 
                              validation_results: List[ValidationResult],
                              formats: List[str]) -> Dict[str, str]:
        """生成輸出文件
        
        Args:
            proxies: 代理列表
            validation_results: 驗證結果列表
            formats: 輸出格式列表
            
        Returns:
            輸出文件路徑字典
        """
        output_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.etl_mode:
            # ETL模式：按照ETL流程規範生成多階段檔案
            await self._generate_etl_outputs(proxies, validation_results, formats, timestamp, output_files)
        else:
            # 傳統模式：生成到單一目錄
            await self._generate_traditional_outputs(proxies, validation_results, formats, timestamp, output_files)
        
        return output_files
    
    async def _generate_etl_outputs(self, 
                                  proxies: List[ProxyNode], 
                                  validation_results: List[ValidationResult],
                                  formats: List[str],
                                  timestamp: str,
                                  output_files: Dict[str, str]):
        """按照ETL規範生成輸出檔案
        
        Args:
            proxies: 代理列表
            validation_results: 驗證結果列表
            formats: 輸出格式列表
            timestamp: 時間戳
            output_files: 輸出檔案字典
        """
        # 1. Raw階段：原始爬取數據
        raw_data = {
            'metadata': {
                'timestamp': timestamp,
                'total_proxies': len(proxies),
                'extraction_stats': {
                    'by_source': self.stats['by_source'],
                    'crawl_duration': self.stats['crawl_duration']
                }
            },
            'raw_proxies': [asdict(proxy) for proxy in proxies]
        }
        
        raw_file = self.raw_dir / f"proxies_raw_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        output_files['raw'] = str(raw_file)
        logger.info(f"已生成原始數據檔案: {raw_file}")
        
        # 2. Processed階段：處理後的數據（去重、清洗）
        processed_data = {
            'metadata': {
                'timestamp': timestamp,
                'total_unique_proxies': len(proxies),
                'processing_stats': self.stats
            },
            'processed_proxies': [asdict(proxy) for proxy in proxies]
        }
        
        processed_file = self.processed_dir / f"proxies_processed_{timestamp}.json"
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        output_files['processed'] = str(processed_file)
        logger.info(f"已生成處理數據檔案: {processed_file}")
        
        # 3. Validated階段：驗證後的數據（僅在有驗證結果時）
        if validation_results:
            working_proxies = [result for result in validation_results if result.status == ProxyStatus.WORKING]
            validated_data = {
                'metadata': {
                    'timestamp': timestamp,
                    'total_validated': len(validation_results),
                    'working_proxies': len(working_proxies),
                    'validation_stats': {
                        'success_rate': len(working_proxies) / len(validation_results) if validation_results else 0,
                        'validation_duration': self.stats['validation_duration']
                    }
                },
                'validated_proxies': [result.to_dict() for result in working_proxies]
            }
            
            validated_file = self.validated_dir / f"proxies_validated_{timestamp}.json"
            with open(validated_file, 'w', encoding='utf-8') as f:
                json.dump(validated_data, f, indent=2, ensure_ascii=False)
            output_files['validated'] = str(validated_file)
            logger.info(f"已生成驗證數據檔案: {validated_file}")
        
        # 4. Reports階段：生成報告檔案
        if 'markdown' in formats:
            report_file = await self._generate_etl_markdown_report(proxies, validation_results, timestamp)
            output_files['report'] = str(report_file)
        
        if 'csv' in formats and validation_results:
            csv_file = await self._generate_etl_csv_output(validation_results, timestamp)
            output_files['csv'] = str(csv_file)
    
    async def _generate_etl_markdown_report(self, 
                                          proxies: List[ProxyNode], 
                                          validation_results: List[ValidationResult],
                                          timestamp: str) -> Path:
        """生成ETL模式的Markdown報告
        
        Args:
            proxies: 代理列表
            validation_results: 驗證結果列表
            timestamp: 時間戳
            
        Returns:
            報告檔案路徑
        """
        report_file = self.reports_dir / f"proxy_crawl_report_{timestamp}.md"
        
        # 統計資訊
        total_proxies = len(proxies)
        working_proxies = len([r for r in validation_results if r.status == ProxyStatus.WORKING]) if validation_results else 0
        success_rate = (working_proxies / len(validation_results)) * 100 if validation_results else 0
        
        # 生成報告內容
        content = f"""# 代理爬蟲執行報告

## 執行摘要
- **執行時間**: {timestamp}
- **總爬取代理數**: {total_proxies}
- **驗證代理數**: {len(validation_results) if validation_results else 0}
- **可用代理數**: {working_proxies}
- **成功率**: {success_rate:.2f}%

## 數據來源統計
"""
        
        # 按來源統計
        if 'by_source' in self.stats:
            content += "\n| 來源 | 代理數量 |\n|------|----------|\n"
            for source, count in self.stats['by_source'].items():
                content += f"| {source} | {count} |\n"
        
        # 按協議統計
        if 'by_protocol' in self.stats:
            content += "\n## 協議分佈\n\n| 協議 | 數量 |\n|------|------|\n"
            for protocol, count in self.stats['by_protocol'].items():
                content += f"| {protocol.upper()} | {count} |\n"
        
        # 按國家統計（如果有地理位置資訊）
        if 'by_country' in self.stats:
            content += "\n## 地理分佈\n\n| 國家 | 數量 |\n|------|------|\n"
            for country, count in self.stats['by_country'].items():
                content += f"| {country} | {count} |\n"
        
        # 效能統計
        content += f"\n## 效能統計\n\n"
        if 'crawl_duration' in self.stats:
            content += f"- **爬取耗時**: {self.stats['crawl_duration']:.2f} 秒\n"
        if 'validation_duration' in self.stats:
            content += f"- **驗證耗時**: {self.stats['validation_duration']:.2f} 秒\n"
        
        # 檔案位置資訊
        content += f"\n## 生成檔案\n\n"
        content += f"- **原始數據**: `data/raw/proxies_raw_{timestamp}.json`\n"
        content += f"- **處理數據**: `data/processed/proxies_processed_{timestamp}.json`\n"
        if validation_results:
            content += f"- **驗證數據**: `data/validated/proxies_validated_{timestamp}.json`\n"
        content += f"- **本報告**: `data/reports/proxy_crawl_report_{timestamp}.md`\n"
        
        # 寫入檔案
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"已生成ETL報告檔案: {report_file}")
        return report_file
    
    async def _generate_etl_csv_output(self, 
                                     validation_results: List[ValidationResult],
                                     timestamp: str) -> Path:
        """生成ETL模式的CSV輸出
        
        Args:
            validation_results: 驗證結果列表
            timestamp: 時間戳
            
        Returns:
            CSV檔案路徑
        """
        import csv
        
        csv_file = self.reports_dir / f"validated_proxies_{timestamp}.csv"
        
        # 只輸出可用的代理
        working_proxies = [result for result in validation_results if result.status == ProxyStatus.WORKING]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 寫入標題行
            writer.writerow([
                'IP', 'Port', 'Protocol', 'Country', 'Anonymity', 
                'Response_Time', 'Last_Checked', 'Source'
            ])
            
            # 寫入數據行
            for result in working_proxies:
                proxy = result.proxy
                writer.writerow([
                    proxy.ip,
                    proxy.port,
                    proxy.protocol,
                    proxy.country or 'Unknown',
                    proxy.anonymity or 'Unknown',
                    f"{result.response_time:.3f}" if result.response_time else 'N/A',
                    result.checked_at.isoformat() if result.checked_at else 'N/A',
                    proxy.source or 'Unknown'
                ])
        
        logger.info(f"已生成ETL CSV檔案: {csv_file}")
        return csv_file
    
    async def _generate_traditional_outputs(self, 
                                          proxies: List[ProxyNode], 
                                          validation_results: List[ValidationResult],
                                          formats: List[str],
                                          timestamp: str,
                                          output_files: Dict[str, str]):
        """傳統模式輸出檔案生成
        
        Args:
            proxies: 代理列表
            validation_results: 驗證結果列表
            formats: 輸出格式列表
            timestamp: 時間戳
            output_files: 輸出檔案字典
        """
        for format_type in formats:
            try:
                if format_type == 'json':
                    file_path = await self._generate_json_output(proxies, validation_results, timestamp)
                elif format_type == 'markdown':
                    file_path = await self._generate_markdown_output(proxies, validation_results, timestamp)
                elif format_type == 'csv':
                    file_path = await self._generate_csv_output(proxies, validation_results, timestamp)
                else:
                    logger.warning(f"不支援的輸出格式: {format_type}")
                    continue
                
                output_files[format_type] = str(file_path)
                logger.info(f"已生成 {format_type.upper()} 輸出: {file_path}")
                
            except Exception as e:
                logger.error(f"生成 {format_type} 輸出時發生錯誤: {str(e)}")
    
    async def _generate_json_output(self, 
                                  proxies: List[ProxyNode], 
                                  validation_results: List[ValidationResult],
                                  timestamp: str) -> Path:
        """生成JSON格式輸出"""
        output_data = {
            'metadata': {
                'timestamp': timestamp,
                'total_proxies': len(proxies),
                'stats': self.stats
            },
            'proxies': [asdict(proxy) for proxy in proxies]
        }
        
        if validation_results:
            output_data['validation_results'] = [
                result.to_dict() for result in validation_results 
                if result.status == ProxyStatus.WORKING
            ]
        
        file_path = self.output_dir / f"proxies_{timestamp}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    async def _generate_markdown_output(self, 
                                      proxies: List[ProxyNode], 
                                      validation_results: List[ValidationResult],
                                      timestamp: str) -> Path:
        """生成Markdown格式輸出"""
        lines = []
        lines.append(f"# 代理列表報告")
        lines.append(f"")
        lines.append(f"**生成時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**代理總數:** {len(proxies)}")
        lines.append(f"")
        
        # 統計信息
        lines.append("## 統計信息")
        lines.append("")
        lines.append(f"- 爬取耗時: {self.stats['crawl_duration']:.2f}s")
        if self.stats['validation_duration'] > 0:
            lines.append(f"- 驗證耗時: {self.stats['validation_duration']:.2f}s")
        lines.append(f"- 總耗時: {self.stats.get('end_time', time.time()) - self.stats.get('start_time', time.time()):.2f}s")
        lines.append("")
        
        # 按源統計
        if self.stats['by_source']:
            lines.append("### 按來源統計")
            lines.append("")
            for source, info in self.stats['by_source'].items():
                if 'error' in info:
                    lines.append(f"- {source}: 錯誤 - {info['error']}")
                else:
                    lines.append(f"- {source}: {info['count']} 個代理")
            lines.append("")
        
        # 按協議統計
        if self.stats['by_protocol']:
            lines.append("### 按協議統計")
            lines.append("")
            for protocol, count in sorted(self.stats['by_protocol'].items()):
                lines.append(f"- {protocol}: {count} 個")
            lines.append("")
        
        # 代理列表表格
        lines.append("## 代理列表")
        lines.append("")
        
        if validation_results:
            # 包含驗證信息的表格
            lines.append("| IP地址 | 端口 | 協議 | 國家 | 匿名等級 | 響應時間 | 狀態 |")
            lines.append("|--------|------|------|------|----------|----------|------|")
            
            for result in validation_results:
                if result.status == ProxyStatus.WORKING:
                    proxy = result.proxy
                    response_time = f"{result.response_time:.2f}s" if result.response_time else "N/A"
                    lines.append(
                        f"| {proxy.ip} | {proxy.port} | {proxy.protocol} | {proxy.country} | "
                        f"{result.anonymity_level.value} | {response_time} | ✅ |"
                    )
        else:
            # 簡單代理列表
            lines.append("| IP地址 | 端口 | 協議 | 國家 | 來源 |")
            lines.append("|--------|------|------|------|------|")
            
            for proxy in proxies:
                lines.append(
                    f"| {proxy.ip} | {proxy.port} | {proxy.protocol} | {proxy.country} | {proxy.source} |"
                )
        
        lines.append("")
        lines.append(f"---")
        lines.append(f"*報告生成於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        file_path = self.output_dir / f"proxies_{timestamp}.md"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return file_path
    
    async def _generate_csv_output(self, 
                                 proxies: List[ProxyNode], 
                                 validation_results: List[ValidationResult],
                                 timestamp: str) -> Path:
        """生成CSV格式輸出"""
        import csv
        
        file_path = self.output_dir / f"proxies_{timestamp}.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if validation_results:
                # 包含驗證信息的CSV
                fieldnames = ['ip', 'port', 'protocol', 'country', 'source', 'anonymity_level', 
                            'response_time', 'status', 'supports_https']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in validation_results:
                    if result.status == ProxyStatus.WORKING:
                        proxy = result.proxy
                        writer.writerow({
                            'ip': proxy.ip,
                            'port': proxy.port,
                            'protocol': proxy.protocol,
                            'country': proxy.country,
                            'source': proxy.source,
                            'anonymity_level': result.anonymity_level.value,
                            'response_time': result.response_time,
                            'status': result.status.value,
                            'supports_https': result.supports_https
                        })
            else:
                # 簡單代理CSV
                fieldnames = ['ip', 'port', 'protocol', 'country', 'source', 'anonymity']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for proxy in proxies:
                    writer.writerow({
                        'ip': proxy.ip,
                        'port': proxy.port,
                        'protocol': proxy.protocol,
                        'country': proxy.country,
                        'source': proxy.source,
                        'anonymity': proxy.anonymity
                    })
        
        return file_path
    
    async def _generate_etl_markdown_report(self, 
                                          proxies: List[ProxyNode], 
                                          validation_results: List[ValidationResult],
                                          timestamp: str) -> Path:
        """生成ETL模式的Markdown報告
        
        Args:
            proxies: 代理列表
            validation_results: 驗證結果列表
            timestamp: 時間戳
            
        Returns:
            Markdown報告文件路徑
        """
        report_file = self.reports_dir / f"proxy_etl_report_{timestamp}.md"
        
        # 計算統計數據
        working_proxies = [r for r in validation_results if r.status == ProxyStatus.WORKING] if validation_results else []
        success_rate = len(working_proxies) / len(validation_results) if validation_results else 0
        
        content = f"""# 代理爬蟲 ETL 流程報告

## 基本資訊
- **執行時間**: {timestamp}
- **總爬取代理數**: {len(proxies)}
- **驗證代理數**: {len(validation_results) if validation_results else 0}
- **可用代理數**: {len(working_proxies)}
- **成功率**: {success_rate:.2%}

## ETL 流程階段

### 1. Extract (提取階段)
- **原始數據檔案**: `data/raw/proxies_raw_{timestamp}.json`
- **提取來源統計**:
{self._format_source_stats()}

### 2. Transform (轉換階段)
- **處理數據檔案**: `data/processed/proxies_processed_{timestamp}.json`
- **去重處理**: 已移除重複代理
- **數據清洗**: 已標準化格式

### 3. Load (載入階段)
- **驗證數據檔案**: `data/validated/proxies_validated_{timestamp}.json`
- **驗證統計**:
{self._format_validation_stats(validation_results) if validation_results else '  - 未執行驗證'}

## 詳細統計

### 按協議分類
{self._format_protocol_stats()}

### 按國家分類
{self._format_country_stats()}

### 按匿名等級分類
{self._format_anonymity_stats()}

## 檔案位置
- **原始數據**: `data/raw/proxies_raw_{timestamp}.json`
- **處理數據**: `data/processed/proxies_processed_{timestamp}.json`
- **驗證數據**: `data/validated/proxies_validated_{timestamp}.json`
- **此報告**: `data/reports/proxy_etl_report_{timestamp}.md`

---
*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"已生成ETL報告: {report_file}")
        return report_file
    
    async def _generate_etl_csv_output(self, 
                                     validation_results: List[ValidationResult],
                                     timestamp: str) -> Path:
        """生成ETL模式的CSV輸出
        
        Args:
            validation_results: 驗證結果列表
            timestamp: 時間戳
            
        Returns:
            CSV文件路徑
        """
        csv_file = self.reports_dir / f"validated_proxies_{timestamp}.csv"
        
        # 準備CSV數據（僅包含可用代理）
        csv_data = []
        working_proxies = [r for r in validation_results if r.status == ProxyStatus.WORKING]
        
        for result in working_proxies:
            proxy = result.proxy
            row = {
                'IP': proxy.ip,
                'Port': proxy.port,
                'Protocol': proxy.protocol,
                'Country': proxy.country or 'Unknown',
                'Anonymity': proxy.anonymity_level or 'Unknown',
                'Source': proxy.source,
                'Response_Time': f"{result.response_time:.2f}s" if result.response_time else 'N/A',
                'Checked_At': result.checked_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': result.status.value
            }
            csv_data.append(row)
        
        # 寫入CSV文件
        import csv
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if csv_data:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
        
        logger.info(f"已生成ETL CSV報告: {csv_file}")
        return csv_file
    
    def _format_source_stats(self) -> str:
        """格式化來源統計資訊"""
        if 'by_source' not in self.stats:
            return "  - 無統計資料"
        
        lines = []
        for source, info in self.stats['by_source'].items():
            if isinstance(info, dict) and 'count' in info:
                lines.append(f"  - {source}: {info['count']} 個代理")
            else:
                lines.append(f"  - {source}: {info} 個代理")
        return "\n".join(lines)
    
    def _format_validation_stats(self, validation_results: List[ValidationResult]) -> str:
        """格式化驗證統計資訊"""
        if not validation_results:
            return "  - 未執行驗證"
        
        status_counts = {}
        total_time = 0
        valid_times = 0
        
        for result in validation_results:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            if result.response_time:
                total_time += result.response_time
                valid_times += 1
        
        lines = []
        for status, count in status_counts.items():
            percentage = count / len(validation_results) * 100
            lines.append(f"  - {status}: {count} 個 ({percentage:.1f}%)")
        
        if valid_times > 0:
            avg_time = total_time / valid_times
            lines.append(f"  - 平均響應時間: {avg_time:.2f}秒")
        
        return "\n".join(lines)
    
    def _format_protocol_stats(self) -> str:
        """格式化協議統計資訊"""
        if 'by_protocol' not in self.stats:
            return "  - 無統計資料"
        
        lines = []
        for protocol, count in self.stats['by_protocol'].items():
            lines.append(f"  - {protocol}: {count} 個代理")
        return "\n".join(lines)
    
    def _format_country_stats(self) -> str:
        """格式化國家統計資訊"""
        if 'by_country' not in self.stats:
            return "  - 無統計資料"
        
        lines = []
        # 只顯示前10個國家
        sorted_countries = sorted(self.stats['by_country'].items(), key=lambda x: x[1], reverse=True)[:10]
        for country, count in sorted_countries:
            lines.append(f"  - {country or 'Unknown'}: {count} 個代理")
        
        if len(self.stats['by_country']) > 10:
            lines.append(f"  - ... 其他 {len(self.stats['by_country']) - 10} 個國家")
        
        return "\n".join(lines)
    
    def _format_anonymity_stats(self) -> str:
        """格式化匿名等級統計資訊"""
        if 'by_anonymity' not in self.stats:
            return "  - 無統計資料"
        
        lines = []
        for anonymity, count in self.stats['by_anonymity'].items():
            lines.append(f"  - {anonymity or 'Unknown'}: {count} 個代理")
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息
        
        Returns:
            統計信息字典
        """
        return self.stats.copy()
    
    def add_crawler(self, name: str, crawler_class: Type[BaseCrawler]):
        """添加自定義爬蟲
        
        Args:
            name: 爬蟲名稱
            crawler_class: 爬蟲類
        """
        self.available_crawlers[name] = crawler_class
        logger.info(f"已添加爬蟲: {name}")
    
    def list_available_crawlers(self) -> List[str]:
        """列出可用的爬蟲
        
        Returns:
            爬蟲名稱列表
        """
        return list(self.available_crawlers.keys())


async def main():
    """測試函數"""
    # 創建管理器
    manager = CrawlerManager(
        output_dir=Path("test_output"),
        enable_validation=True,
        validation_timeout=5.0,
        max_concurrent_validation=20
    )
    
    # 列出可用爬蟲
    logger.info(f"可用爬蟲: {manager.list_available_crawlers()}")
    
    # 爬取所有源
    logger.info("開始爬取所有代理源...")
    result = await manager.crawl_all_sources(
        sources=['sslproxies', 'geonode', 'free_proxy_list'],
        validate_proxies=True,
        output_formats=['json', 'markdown', 'csv']
    )
    
    # 顯示結果
    logger.info(f"爬取完成!")
    logger.info(f"總代理數: {len(result['proxies'])}")
    logger.info(f"統計信息: {result['stats']}")
    logger.info(f"輸出文件: {result['output_files']}")


if __name__ == "__main__":
    asyncio.run(main())