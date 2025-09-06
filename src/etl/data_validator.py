#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據驗證層

實現代理數據的品質控制和一致性驗證，包括：
1. 數據格式驗證
2. 業務邏輯驗證
3. 重複數據檢測
4. 數據品質評分
5. 異常數據標記

作者: JasonSpider 專案
日期: 2024
"""

import re
import ipaddress
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

import aiohttp
from loguru import logger

# 導入現有模型
from ..proxy_manager.models import (
    ProxyNode, ProxyProtocol, ProxyAnonymity, ProxySpeed, ProxyStatus
)


class ValidationLevel(Enum):
    """驗證級別"""
    BASIC = "basic"          # 基本格式驗證
    STANDARD = "standard"    # 標準驗證（包含連通性測試）
    STRICT = "strict"        # 嚴格驗證（包含匿名性檢測）
    COMPREHENSIVE = "comprehensive"  # 全面驗證（包含性能測試）


class ValidationResult(Enum):
    """驗證結果"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    SUSPICIOUS = "suspicious"


@dataclass
class ValidationIssue:
    """驗證問題"""
    field: str
    issue_type: str
    severity: str  # error, warning, info
    message: str
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'issue_type': self.issue_type,
            'severity': self.severity,
            'message': self.message,
            'suggested_fix': self.suggested_fix
        }


@dataclass
class ValidationReport:
    """驗證報告"""
    proxy_id: str
    validation_level: ValidationLevel
    overall_result: ValidationResult
    quality_score: float  # 0.0 - 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_valid(self) -> bool:
        """是否通過驗證"""
        return self.overall_result in [ValidationResult.VALID, ValidationResult.WARNING]
    
    @property
    def has_errors(self) -> bool:
        """是否有錯誤"""
        return any(issue.severity == 'error' for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return any(issue.severity == 'warning' for issue in self.issues)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proxy_id': self.proxy_id,
            'validation_level': self.validation_level.value,
            'overall_result': self.overall_result.value,
            'quality_score': self.quality_score,
            'is_valid': self.is_valid,
            'has_errors': self.has_errors,
            'has_warnings': self.has_warnings,
            'issues': [issue.to_dict() for issue in self.issues],
            'metadata': self.metadata,
            'validation_timestamp': self.validation_timestamp.isoformat()
        }


@dataclass
class ValidationConfig:
    """驗證配置"""
    # 驗證級別
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    
    # 連通性測試
    connection_timeout: int = 10
    test_urls: List[str] = field(default_factory=lambda: [
        'http://httpbin.org/ip',
        'https://api.ipify.org?format=json',
        'http://icanhazip.com'
    ])
    
    # 重複檢測
    enable_duplicate_detection: bool = True
    duplicate_threshold_hours: int = 24
    
    # 品質評分權重
    quality_weights: Dict[str, float] = field(default_factory=lambda: {
        'format_validity': 0.2,
        'connectivity': 0.3,
        'response_time': 0.2,
        'anonymity': 0.15,
        'stability': 0.15
    })
    
    # 閾值設定
    min_quality_score: float = 0.6
    max_response_time_ms: int = 5000
    min_success_rate: float = 0.7
    
    # 地理位置驗證
    enable_geo_validation: bool = True
    allowed_countries: Optional[Set[str]] = None
    blocked_countries: Optional[Set[str]] = None
    
    # 安全檢查
    enable_security_checks: bool = True
    check_malicious_ips: bool = True
    
    def __post_init__(self):
        if self.blocked_countries is None:
            self.blocked_countries = {'CN', 'RU', 'KP'}  # 預設封鎖清單


class ProxyDataValidator:
    """代理數據驗證器
    
    實現多層次的代理數據驗證，確保數據品質和一致性
    """
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.logger = logger.bind(component='DataValidator')
        
        # HTTP 客戶端
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # 快取
        self._validation_cache: Dict[str, ValidationReport] = {}
        self._duplicate_cache: Set[str] = set()
        
        # 統計
        self.validation_stats = {
            'total_validated': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'warning_count': 0,
            'duplicate_count': 0
        }
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """初始化驗證器"""
        timeout = aiohttp.ClientTimeout(total=self.config.connection_timeout)
        self.http_session = aiohttp.ClientSession(timeout=timeout)
        self.logger.info("數據驗證器初始化完成")
    
    async def cleanup(self) -> None:
        """清理資源"""
        if self.http_session:
            await self.http_session.close()
        self.logger.info("數據驗證器資源清理完成")
    
    def generate_proxy_id(self, proxy: ProxyNode) -> str:
        """生成代理唯一標識"""
        identifier = f"{proxy.host}:{proxy.port}:{proxy.protocol.value}"
        return hashlib.md5(identifier.encode()).hexdigest()
    
    async def validate_proxy(self, proxy: ProxyNode) -> ValidationReport:
        """驗證單個代理
        
        Args:
            proxy: 要驗證的代理節點
            
        Returns:
            ValidationReport: 驗證報告
        """
        proxy_id = self.generate_proxy_id(proxy)
        
        # 檢查快取
        if proxy_id in self._validation_cache:
            cached_report = self._validation_cache[proxy_id]
            if (datetime.now() - cached_report.validation_timestamp).total_seconds() < 3600:
                return cached_report
        
        self.logger.debug(f"開始驗證代理: {proxy.url}")
        
        report = ValidationReport(
            proxy_id=proxy_id,
            validation_level=self.config.validation_level,
            overall_result=ValidationResult.VALID,
            quality_score=1.0
        )
        
        try:
            # 1. 基本格式驗證
            await self._validate_format(proxy, report)
            
            # 2. 重複檢測
            if self.config.enable_duplicate_detection:
                await self._check_duplicates(proxy, report)
            
            # 3. 連通性測試（如果需要）
            if self.config.validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE]:
                await self._validate_connectivity(proxy, report)
            
            # 4. 匿名性檢測（如果需要）
            if self.config.validation_level in [ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE]:
                await self._validate_anonymity(proxy, report)
            
            # 5. 性能測試（如果需要）
            if self.config.validation_level == ValidationLevel.COMPREHENSIVE:
                await self._validate_performance(proxy, report)
            
            # 6. 地理位置驗證
            if self.config.enable_geo_validation:
                await self._validate_geography(proxy, report)
            
            # 7. 安全檢查
            if self.config.enable_security_checks:
                await self._validate_security(proxy, report)
            
            # 8. 計算品質評分
            self._calculate_quality_score(proxy, report)
            
            # 9. 確定最終結果
            self._determine_final_result(report)
            
        except Exception as e:
            self.logger.error(f"驗證代理時發生錯誤 {proxy.url}: {e}")
            report.issues.append(ValidationIssue(
                field='general',
                issue_type='validation_error',
                severity='error',
                message=f'驗證過程中發生錯誤: {str(e)}'
            ))
            report.overall_result = ValidationResult.INVALID
            report.quality_score = 0.0
        
        # 更新統計
        self._update_stats(report)
        
        # 快取結果
        self._validation_cache[proxy_id] = report
        
        self.logger.debug(
            f"代理驗證完成: {proxy.url}, "
            f"結果: {report.overall_result.value}, "
            f"品質評分: {report.quality_score:.2f}"
        )
        
        return report
    
    async def validate_batch(self, proxies: List[ProxyNode], max_concurrent: int = 50) -> List[ValidationReport]:
        """批量驗證代理
        
        Args:
            proxies: 代理列表
            max_concurrent: 最大並發數
            
        Returns:
            List[ValidationReport]: 驗證報告列表
        """
        self.logger.info(f"開始批量驗證 {len(proxies)} 個代理")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_with_semaphore(proxy: ProxyNode) -> ValidationReport:
            async with semaphore:
                return await self.validate_proxy(proxy)
        
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        reports = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常
        valid_reports = []
        for i, result in enumerate(reports):
            if isinstance(result, Exception):
                self.logger.error(f"驗證代理失敗 {proxies[i].url}: {result}")
                # 創建錯誤報告
                error_report = ValidationReport(
                    proxy_id=self.generate_proxy_id(proxies[i]),
                    validation_level=self.config.validation_level,
                    overall_result=ValidationResult.INVALID,
                    quality_score=0.0
                )
                error_report.issues.append(ValidationIssue(
                    field='general',
                    issue_type='validation_exception',
                    severity='error',
                    message=f'驗證異常: {str(result)}'
                ))
                valid_reports.append(error_report)
            else:
                valid_reports.append(result)
        
        self.logger.info(
            f"批量驗證完成: {len(valid_reports)} 個報告, "
            f"有效: {sum(1 for r in valid_reports if r.is_valid)}, "
            f"無效: {sum(1 for r in valid_reports if not r.is_valid)}"
        )
        
        return valid_reports
    
    async def _validate_format(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """驗證基本格式"""
        # 驗證 IP 地址格式
        try:
            ipaddress.ip_address(proxy.host)
        except ValueError:
            # 可能是域名，檢查域名格式
            if not self._is_valid_hostname(proxy.host):
                report.issues.append(ValidationIssue(
                    field='host',
                    issue_type='invalid_format',
                    severity='error',
                    message=f'無效的主機地址: {proxy.host}',
                    suggested_fix='請提供有效的 IP 地址或域名'
                ))
        
        # 驗證端口範圍
        if not (1 <= proxy.port <= 65535):
            report.issues.append(ValidationIssue(
                field='port',
                issue_type='invalid_range',
                severity='error',
                message=f'端口超出有效範圍: {proxy.port}',
                suggested_fix='端口應在 1-65535 範圍內'
            ))
        
        # 檢查常見代理端口
        common_ports = {80, 443, 1080, 3128, 8080, 8888, 9050}
        if proxy.port not in common_ports:
            report.issues.append(ValidationIssue(
                field='port',
                issue_type='uncommon_port',
                severity='warning',
                message=f'使用非常見代理端口: {proxy.port}'
            ))
        
        # 驗證協議和端口的匹配
        if proxy.protocol == ProxyProtocol.HTTP and proxy.port == 443:
            report.issues.append(ValidationIssue(
                field='protocol',
                issue_type='protocol_port_mismatch',
                severity='warning',
                message='HTTP 協議使用 443 端口（通常用於 HTTPS）'
            ))
        
        # 檢查必要字段
        if not proxy.source:
            report.issues.append(ValidationIssue(
                field='source',
                issue_type='missing_required_field',
                severity='warning',
                message='缺少代理來源資訊'
            ))
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """檢查是否為有效的主機名"""
        if len(hostname) > 255:
            return False
        
        # 移除尾隨點
        if hostname.endswith('.'):
            hostname = hostname[:-1]
        
        # 檢查每個標籤
        allowed = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')
        return all(allowed.match(label) for label in hostname.split('.'))
    
    async def _check_duplicates(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """檢查重複代理"""
        proxy_signature = f"{proxy.host}:{proxy.port}"
        
        if proxy_signature in self._duplicate_cache:
            report.issues.append(ValidationIssue(
                field='general',
                issue_type='duplicate_proxy',
                severity='warning',
                message=f'檢測到重複代理: {proxy_signature}'
            ))
            self.validation_stats['duplicate_count'] += 1
        else:
            self._duplicate_cache.add(proxy_signature)
    
    async def _validate_connectivity(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """驗證連通性"""
        if not self.http_session:
            return
        
        proxy_url = proxy.url
        successful_tests = 0
        total_response_time = 0
        
        for test_url in self.config.test_urls:
            try:
                start_time = asyncio.get_event_loop().time()
                
                async with self.http_session.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.config.connection_timeout)
                ) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time = int((end_time - start_time) * 1000)
                    
                    if response.status == 200:
                        successful_tests += 1
                        total_response_time += response_time
                        
                        # 記錄響應時間
                        report.metadata[f'response_time_{test_url}'] = response_time
                    else:
                        report.issues.append(ValidationIssue(
                            field='connectivity',
                            issue_type='http_error',
                            severity='warning',
                            message=f'測試 URL {test_url} 返回狀態碼: {response.status}'
                        ))
                        
            except asyncio.TimeoutError:
                report.issues.append(ValidationIssue(
                    field='connectivity',
                    issue_type='timeout',
                    severity='error',
                    message=f'連接 {test_url} 超時'
                ))
            except Exception as e:
                report.issues.append(ValidationIssue(
                    field='connectivity',
                    issue_type='connection_error',
                    severity='error',
                    message=f'連接 {test_url} 失敗: {str(e)}'
                ))
        
        # 計算成功率
        success_rate = successful_tests / len(self.config.test_urls)
        report.metadata['connectivity_success_rate'] = success_rate
        
        if successful_tests > 0:
            avg_response_time = total_response_time / successful_tests
            report.metadata['avg_response_time'] = avg_response_time
            
            # 檢查響應時間
            if avg_response_time > self.config.max_response_time_ms:
                report.issues.append(ValidationIssue(
                    field='performance',
                    issue_type='slow_response',
                    severity='warning',
                    message=f'平均響應時間過慢: {avg_response_time:.0f}ms'
                ))
        
        # 檢查成功率
        if success_rate < self.config.min_success_rate:
            report.issues.append(ValidationIssue(
                field='connectivity',
                issue_type='low_success_rate',
                severity='error',
                message=f'連通性測試成功率過低: {success_rate:.1%}'
            ))
    
    async def _validate_anonymity(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """驗證匿名性"""
        if not self.http_session:
            return
        
        try:
            # 獲取真實 IP
            async with self.http_session.get('http://httpbin.org/ip') as response:
                if response.status == 200:
                    real_ip_data = await response.json()
                    real_ip = real_ip_data.get('origin', '').split(',')[0].strip()
                    
                    # 通過代理獲取 IP
                    async with self.http_session.get(
                        'http://httpbin.org/ip',
                        proxy=proxy.url
                    ) as proxy_response:
                        if proxy_response.status == 200:
                            proxy_ip_data = await proxy_response.json()
                            proxy_ip = proxy_ip_data.get('origin', '').split(',')[0].strip()
                            
                            # 檢查 IP 是否被隱藏
                            if real_ip == proxy_ip:
                                report.issues.append(ValidationIssue(
                                    field='anonymity',
                                    issue_type='ip_leak',
                                    severity='error',
                                    message='代理未能隱藏真實 IP 地址'
                                ))
                            else:
                                report.metadata['proxy_detected_ip'] = proxy_ip
                                report.metadata['anonymity_verified'] = True
                                
                                # 檢查是否為透明代理
                                headers = proxy_response.headers
                                forwarded_headers = [
                                    'X-Forwarded-For', 'X-Real-IP', 'Via', 'X-Proxy-ID'
                                ]
                                
                                for header in forwarded_headers:
                                    if header in headers:
                                        report.issues.append(ValidationIssue(
                                            field='anonymity',
                                            issue_type='transparent_proxy',
                                            severity='warning',
                                            message=f'檢測到透明代理標頭: {header}'
                                        ))
                                        break
                        
        except Exception as e:
            report.issues.append(ValidationIssue(
                field='anonymity',
                issue_type='anonymity_test_failed',
                severity='warning',
                message=f'匿名性測試失敗: {str(e)}'
            ))
    
    async def _validate_performance(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """驗證性能"""
        # 執行多次測試以獲得更準確的性能數據
        test_count = 3
        response_times = []
        
        for i in range(test_count):
            try:
                start_time = asyncio.get_event_loop().time()
                
                async with self.http_session.get(
                    'http://httpbin.org/get',
                    proxy=proxy.url,
                    timeout=aiohttp.ClientTimeout(total=self.config.connection_timeout)
                ) as response:
                    end_time = asyncio.get_event_loop().time()
                    
                    if response.status == 200:
                        response_time = (end_time - start_time) * 1000
                        response_times.append(response_time)
                        
            except Exception:
                continue
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            report.metadata.update({
                'performance_avg_response_time': avg_response_time,
                'performance_min_response_time': min_response_time,
                'performance_max_response_time': max_response_time,
                'performance_test_count': len(response_times),
                'performance_stability': 1.0 - (max_response_time - min_response_time) / avg_response_time
            })
            
            # 性能評估
            if avg_response_time < 1000:
                report.metadata['performance_rating'] = 'excellent'
            elif avg_response_time < 3000:
                report.metadata['performance_rating'] = 'good'
            elif avg_response_time < 5000:
                report.metadata['performance_rating'] = 'fair'
            else:
                report.metadata['performance_rating'] = 'poor'
                report.issues.append(ValidationIssue(
                    field='performance',
                    issue_type='poor_performance',
                    severity='warning',
                    message=f'性能較差，平均響應時間: {avg_response_time:.0f}ms'
                ))
    
    async def _validate_geography(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """驗證地理位置"""
        # 檢查國家限制
        if proxy.country:
            country_code = proxy.country.upper()
            
            if self.config.blocked_countries and country_code in self.config.blocked_countries:
                report.issues.append(ValidationIssue(
                    field='geography',
                    issue_type='blocked_country',
                    severity='error',
                    message=f'代理來自被封鎖的國家: {proxy.country}'
                ))
            
            if self.config.allowed_countries and country_code not in self.config.allowed_countries:
                report.issues.append(ValidationIssue(
                    field='geography',
                    issue_type='country_not_allowed',
                    severity='warning',
                    message=f'代理來自非允許的國家: {proxy.country}'
                ))
    
    async def _validate_security(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """驗證安全性"""
        # 檢查惡意 IP（簡化實現）
        if self.config.check_malicious_ips:
            # 這裡可以整合第三方威脅情報 API
            # 暫時檢查一些已知的惡意 IP 範圍
            malicious_ranges = [
                '127.0.0.0/8',    # 本地回環
                '10.0.0.0/8',     # 私有網路
                '172.16.0.0/12',  # 私有網路
                '192.168.0.0/16'  # 私有網路
            ]
            
            try:
                proxy_ip = ipaddress.ip_address(proxy.host)
                for malicious_range in malicious_ranges:
                    if proxy_ip in ipaddress.ip_network(malicious_range):
                        report.issues.append(ValidationIssue(
                            field='security',
                            issue_type='private_ip_range',
                            severity='error',
                            message=f'代理 IP 位於私有網路範圍: {malicious_range}'
                        ))
                        break
            except ValueError:
                # 不是 IP 地址，跳過檢查
                pass
    
    def _calculate_quality_score(self, proxy: ProxyNode, report: ValidationReport) -> None:
        """計算品質評分"""
        scores = {}
        weights = self.config.quality_weights
        
        # 1. 格式有效性評分
        format_errors = sum(1 for issue in report.issues 
                          if issue.field in ['host', 'port', 'protocol'] and issue.severity == 'error')
        scores['format_validity'] = max(0.0, 1.0 - format_errors * 0.5)
        
        # 2. 連通性評分
        connectivity_success_rate = report.metadata.get('connectivity_success_rate', 0.0)
        scores['connectivity'] = connectivity_success_rate
        
        # 3. 響應時間評分
        avg_response_time = report.metadata.get('avg_response_time', float('inf'))
        if avg_response_time == float('inf'):
            scores['response_time'] = 0.0
        else:
            # 響應時間越短評分越高
            scores['response_time'] = max(0.0, 1.0 - avg_response_time / self.config.max_response_time_ms)
        
        # 4. 匿名性評分
        if report.metadata.get('anonymity_verified', False):
            anonymity_issues = sum(1 for issue in report.issues 
                                 if issue.field == 'anonymity' and issue.severity == 'error')
            scores['anonymity'] = max(0.0, 1.0 - anonymity_issues * 0.3)
        else:
            scores['anonymity'] = 0.5  # 未測試時給予中等評分
        
        # 5. 穩定性評分
        stability = report.metadata.get('performance_stability', 0.5)
        scores['stability'] = stability
        
        # 計算加權總分
        total_score = sum(scores[key] * weights[key] for key in scores)
        
        # 扣除嚴重錯誤的分數
        error_penalty = sum(0.1 for issue in report.issues if issue.severity == 'error')
        total_score = max(0.0, total_score - error_penalty)
        
        report.quality_score = min(1.0, total_score)
        report.metadata['quality_breakdown'] = scores
    
    def _determine_final_result(self, report: ValidationReport) -> None:
        """確定最終驗證結果"""
        if report.has_errors:
            report.overall_result = ValidationResult.INVALID
        elif report.quality_score < self.config.min_quality_score:
            report.overall_result = ValidationResult.SUSPICIOUS
        elif report.has_warnings:
            report.overall_result = ValidationResult.WARNING
        else:
            report.overall_result = ValidationResult.VALID
    
    def _update_stats(self, report: ValidationReport) -> None:
        """更新統計資訊"""
        self.validation_stats['total_validated'] += 1
        
        if report.overall_result == ValidationResult.VALID:
            self.validation_stats['valid_count'] += 1
        elif report.overall_result == ValidationResult.WARNING:
            self.validation_stats['warning_count'] += 1
        else:
            self.validation_stats['invalid_count'] += 1
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計資訊"""
        stats = self.validation_stats.copy()
        
        if stats['total_validated'] > 0:
            stats['valid_rate'] = stats['valid_count'] / stats['total_validated']
            stats['invalid_rate'] = stats['invalid_count'] / stats['total_validated']
            stats['warning_rate'] = stats['warning_count'] / stats['total_validated']
            stats['duplicate_rate'] = stats['duplicate_count'] / stats['total_validated']
        else:
            stats.update({
                'valid_rate': 0.0,
                'invalid_rate': 0.0,
                'warning_rate': 0.0,
                'duplicate_rate': 0.0
            })
        
        return stats
    
    def clear_cache(self) -> None:
        """清除快取"""
        self._validation_cache.clear()
        self._duplicate_cache.clear()
        self.logger.info("驗證快取已清除")


# 便利函數
async def validate_proxy_data(
    proxies: List[ProxyNode],
    config: Optional[ValidationConfig] = None,
    max_concurrent: int = 50
) -> List[ValidationReport]:
    """驗證代理數據的便利函數
    
    Args:
        proxies: 代理列表
        config: 驗證配置
        max_concurrent: 最大並發數
        
    Returns:
        List[ValidationReport]: 驗證報告列表
    """
    if config is None:
        config = ValidationConfig()
    
    async with ProxyDataValidator(config) as validator:
        return await validator.validate_batch(proxies, max_concurrent)


if __name__ == "__main__":
    # 測試用例
    async def main():
        from ..proxy_manager.models import ProxyNode, ProxyProtocol
        
        # 創建測試代理
        test_proxies = [
            ProxyNode(
                host="8.8.8.8",
                port=80,
                protocol=ProxyProtocol.HTTP,
                source="test"
            ),
            ProxyNode(
                host="invalid-host",
                port=99999,
                protocol=ProxyProtocol.HTTP,
                source="test"
            )
        ]
        
        # 配置驗證器
        config = ValidationConfig(
            validation_level=ValidationLevel.STANDARD,
            connection_timeout=5
        )
        
        # 執行驗證
        reports = await validate_proxy_data(test_proxies, config)
        
        # 輸出結果
        for report in reports:
            print(f"代理: {report.proxy_id}")
            print(f"結果: {report.overall_result.value}")
            print(f"品質評分: {report.quality_score:.2f}")
            print(f"問題數量: {len(report.issues)}")
            print("---")
    
    asyncio.run(main())