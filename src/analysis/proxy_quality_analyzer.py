#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理品質分析器

提供代理品質評估、性能分析和預測功能
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from statistics import mean, median, stdev
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

from ..proxy_manager.models import ProxyNode, ProxyStatus, ProxyAnonymity, ProxyProtocol

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """代理品質指標"""
    response_time: float  # 響應時間 (ms)
    success_rate: float   # 成功率 (0-1)
    uptime: float         # 運行時間 (0-1)
    anonymity_level: int  # 匿名等級 (1-4)
    location_score: float # 地理位置評分 (0-1)
    protocol_score: float # 協議支援評分 (0-1)
    stability: float      # 穩定性評分 (0-1)
    security: float       # 安全性評分 (0-1)


@dataclass
class QualityScore:
    """代理品質評分"""
    proxy_id: str
    overall_score: float      # 總體評分 (0-100)
    performance_score: float  # 性能評分 (0-100)
    reliability_score: float  # 可靠性評分 (0-100)
    security_score: float     # 安全性評分 (0-100)
    location_score: float     # 地理位置評分 (0-100)
    metrics: QualityMetrics
    timestamp: datetime
    recommendations: List[str]  # 改進建議


@dataclass
class AnalysisReport:
    """分析報告"""
    total_proxies: int
    analyzed_proxies: int
    average_score: float
    score_distribution: Dict[str, int]  # 評分分布
    top_proxies: List[QualityScore]
    worst_proxies: List[QualityScore]
    recommendations: List[str]
    generated_at: datetime


class ProxyQualityAnalyzer:
    """代理品質分析器"""
    
    def __init__(self, data_dir: str = "data/analysis"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 機器學習模型
        self.performance_model = None
        self.reliability_model = None
        self.model_file = self.data_dir / "quality_models.joblib"
        
        # 分析配置
        self.weights = {
            'response_time': 0.25,
            'success_rate': 0.30,
            'uptime': 0.20,
            'anonymity_level': 0.15,
            'location_score': 0.10
        }
        
        # 載入或初始化模型
        self._load_models()
    
    def _load_models(self):
        """載入機器學習模型"""
        try:
            if self.model_file.exists():
                models = joblib.load(self.model_file)
                self.performance_model = models.get('performance')
                self.reliability_model = models.get('reliability')
                logger.info("✅ 機器學習模型載入成功")
            else:
                logger.info("📊 初始化新的機器學習模型")
        except Exception as e:
            logger.error(f"❌ 模型載入失敗: {e}")
    
    def _save_models(self):
        """保存機器學習模型"""
        try:
            models = {
                'performance': self.performance_model,
                'reliability': self.reliability_model
            }
            joblib.dump(models, self.model_file)
            logger.info("✅ 機器學習模型保存成功")
        except Exception as e:
            logger.error(f"❌ 模型保存失敗: {e}")
    
    def calculate_quality_metrics(self, proxy: ProxyNode, 
                                response_times: List[float],
                                success_count: int,
                                total_requests: int) -> QualityMetrics:
        """計算代理品質指標"""
        
        # 響應時間指標
        avg_response_time = mean(response_times) if response_times else 1000
        response_time_score = max(0, 1 - (avg_response_time / 5000))  # 5秒為最差
        
        # 成功率
        success_rate = success_count / total_requests if total_requests > 0 else 0
        
        # 運行時間 (基於歷史數據)
        uptime = min(1.0, success_rate * 1.2)  # 簡化計算
        
        # 匿名等級評分
        anonymity_scores = {
            ProxyAnonymity.TRANSPARENT: 0.2,
            ProxyAnonymity.ANONYMOUS: 0.6,
            ProxyAnonymity.ELITE: 1.0
        }
        anonymity_score = anonymity_scores.get(proxy.anonymity, 0.4)
        
        # 地理位置評分 (基於國家)
        location_scores = {
            'United States': 0.9, 'Canada': 0.8, 'United Kingdom': 0.8, 'Germany': 0.8, 'France': 0.7,
            'Japan': 0.7, 'Australia': 0.7, 'Netherlands': 0.8, 'Singapore': 0.6, 'Hong Kong': 0.6
        }
        location_score = location_scores.get(proxy.country, 0.5)
        
        # 協議支援評分
        protocol_scores = {
            ProxyProtocol.HTTP: 0.6,
            ProxyProtocol.HTTPS: 0.8,
            ProxyProtocol.SOCKS4: 0.7,
            ProxyProtocol.SOCKS5: 0.9
        }
        protocol_score = protocol_scores.get(proxy.protocol, 0.5)
        
        # 穩定性評分 (基於響應時間變異)
        stability = 1.0 - (stdev(response_times) / mean(response_times)) if len(response_times) > 1 else 0.5
        stability = max(0, min(1, stability))
        
        # 安全性評分 (基於匿名等級和協議)
        security = (anonymity_score + protocol_score) / 2
        
        return QualityMetrics(
            response_time=avg_response_time,
            success_rate=success_rate,
            uptime=uptime,
            anonymity_level=proxy.anonymity.value if hasattr(proxy.anonymity, 'value') else 1,
            location_score=location_score,
            protocol_score=protocol_score,
            stability=stability,
            security=security
        )
    
    def calculate_quality_score(self, proxy: ProxyNode, metrics: QualityMetrics) -> QualityScore:
        """計算代理品質評分"""
        
        # 性能評分 (響應時間 + 成功率)
        performance_score = (
            (1 - metrics.response_time / 5000) * 0.6 +  # 響應時間權重
            metrics.success_rate * 0.4  # 成功率權重
        ) * 100
        
        # 可靠性評分 (穩定性 + 運行時間)
        reliability_score = (
            metrics.stability * 0.6 +
            metrics.uptime * 0.4
        ) * 100
        
        # 安全性評分 (匿名等級 + 協議支援)
        security_score = (
            metrics.security * 0.7 +
            metrics.protocol_score * 0.3
        ) * 100
        
        # 地理位置評分
        location_score = metrics.location_score * 100
        
        # 總體評分 (加權平均)
        overall_score = (
            performance_score * self.weights['response_time'] +
            reliability_score * self.weights['success_rate'] +
            security_score * self.weights['anonymity_level'] +
            location_score * self.weights['location_score']
        )
        
        # 生成改進建議
        recommendations = self._generate_recommendations(metrics, overall_score)
        
        return QualityScore(
            proxy_id=f"{proxy.host}:{proxy.port}",
            overall_score=round(overall_score, 2),
            performance_score=round(performance_score, 2),
            reliability_score=round(reliability_score, 2),
            security_score=round(security_score, 2),
            location_score=round(location_score, 2),
            metrics=metrics,
            timestamp=datetime.now(),
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, metrics: QualityMetrics, overall_score: float) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if metrics.response_time > 3000:
            recommendations.append("響應時間過慢，建議檢查網路連接")
        
        if metrics.success_rate < 0.7:
            recommendations.append("成功率較低，建議更換代理或檢查配置")
        
        if metrics.stability < 0.5:
            recommendations.append("穩定性不足，建議使用更穩定的代理")
        
        if metrics.security < 0.6:
            recommendations.append("安全性較低，建議使用高匿名代理")
        
        if overall_score < 60:
            recommendations.append("整體評分較低，建議考慮更換代理")
        
        return recommendations
    
    async def analyze_proxies(self, proxies: List[ProxyNode], 
                            historical_data: Optional[Dict[str, Any]] = None) -> AnalysisReport:
        """分析代理列表"""
        logger.info(f"🔍 開始分析 {len(proxies)} 個代理的品質")
        
        quality_scores = []
        
        for proxy in proxies:
            try:
                # 獲取歷史數據
                proxy_data = historical_data.get(f"{proxy.host}:{proxy.port}", {}) if historical_data else {}
                
                # 模擬測試數據 (實際應用中應該從數據庫獲取)
                response_times = proxy_data.get('response_times', [1000, 1200, 1100])
                success_count = proxy_data.get('success_count', 8)
                total_requests = proxy_data.get('total_requests', 10)
                
                # 計算品質指標
                metrics = self.calculate_quality_metrics(proxy, response_times, success_count, total_requests)
                
                # 計算品質評分
                score = self.calculate_quality_score(proxy, metrics)
                quality_scores.append(score)
                
            except Exception as e:
                logger.error(f"❌ 分析代理 {proxy.host}:{proxy.port} 失敗: {e}")
                continue
        
        # 生成分析報告
        report = self._generate_analysis_report(quality_scores)
        
        # 保存分析結果
        await self._save_analysis_results(report)
        
        logger.info(f"✅ 代理品質分析完成，平均評分: {report.average_score:.2f}")
        return report
    
    def _generate_analysis_report(self, quality_scores: List[QualityScore]) -> AnalysisReport:
        """生成分析報告"""
        if not quality_scores:
            return AnalysisReport(
                total_proxies=0,
                analyzed_proxies=0,
                average_score=0,
                score_distribution={},
                top_proxies=[],
                worst_proxies=[],
                recommendations=[],
                generated_at=datetime.now()
            )
        
        # 計算統計數據
        scores = [score.overall_score for score in quality_scores]
        average_score = mean(scores)
        
        # 評分分布
        score_distribution = {
            "優秀 (90-100)": len([s for s in scores if s >= 90]),
            "良好 (80-89)": len([s for s in scores if 80 <= s < 90]),
            "一般 (70-79)": len([s for s in scores if 70 <= s < 80]),
            "較差 (60-69)": len([s for s in scores if 60 <= s < 70]),
            "很差 (0-59)": len([s for s in scores if s < 60])
        }
        
        # 排序
        sorted_scores = sorted(quality_scores, key=lambda x: x.overall_score, reverse=True)
        
        # 最佳和最差代理
        top_proxies = sorted_scores[:5]
        worst_proxies = sorted_scores[-5:]
        
        # 生成建議
        recommendations = self._generate_global_recommendations(quality_scores, average_score)
        
        return AnalysisReport(
            total_proxies=len(quality_scores),
            analyzed_proxies=len(quality_scores),
            average_score=round(average_score, 2),
            score_distribution=score_distribution,
            top_proxies=top_proxies,
            worst_proxies=worst_proxies,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
    
    def _generate_global_recommendations(self, quality_scores: List[QualityScore], 
                                       average_score: float) -> List[str]:
        """生成全局建議"""
        recommendations = []
        
        if average_score < 70:
            recommendations.append("整體代理品質較低，建議更新代理池")
        
        # 分析各項指標
        performance_scores = [s.performance_score for s in quality_scores]
        reliability_scores = [s.reliability_score for s in quality_scores]
        security_scores = [s.security_score for s in quality_scores]
        
        if mean(performance_scores) < 70:
            recommendations.append("代理性能普遍較差，建議優化網路配置")
        
        if mean(reliability_scores) < 70:
            recommendations.append("代理可靠性不足，建議增加穩定性檢查")
        
        if mean(security_scores) < 70:
            recommendations.append("代理安全性較低，建議使用高匿名代理")
        
        return recommendations
    
    async def _save_analysis_results(self, report: AnalysisReport):
        """保存分析結果"""
        try:
            # 保存詳細報告
            report_file = self.data_dir / f"quality_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report_data = {
                'report': asdict(report),
                'generated_at': report.generated_at.isoformat()
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            # 保存最新報告
            latest_file = self.data_dir / "latest_quality_analysis.json"
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 分析結果已保存到 {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存分析結果失敗: {e}")
    
    def get_quality_trends(self, days: int = 7) -> Dict[str, Any]:
        """獲取品質趨勢數據"""
        try:
            # 讀取歷史分析結果
            trend_data = []
            for file_path in self.data_dir.glob("quality_analysis_*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    trend_data.append({
                        'date': data['generated_at'][:10],
                        'average_score': data['report']['average_score'],
                        'total_proxies': data['report']['total_proxies']
                    })
            
            # 按日期排序
            trend_data.sort(key=lambda x: x['date'])
            
            return {
                'trends': trend_data[-days:],
                'period_days': days,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取品質趨勢失敗: {e}")
            return {'trends': [], 'period_days': days, 'generated_at': datetime.now().isoformat()}
    
    def predict_proxy_performance(self, proxy: ProxyNode) -> Dict[str, float]:
        """預測代理性能"""
        if not self.performance_model:
            return {'predicted_score': 0, 'confidence': 0}
        
        try:
            # 準備特徵數據
            features = np.array([[
                proxy.port,  # 端口
                1 if proxy.protocol == ProxyProtocol.HTTPS else 0,  # 是否HTTPS
                1 if proxy.protocol == ProxyProtocol.SOCKS5 else 0,  # 是否SOCKS5
                proxy.anonymity.value if hasattr(proxy.anonymity, 'value') else 1,  # 匿名等級
            ]])
            
            # 預測
            predicted_score = self.performance_model.predict(features)[0]
            confidence = 0.8  # 簡化的置信度計算
            
            return {
                'predicted_score': round(predicted_score, 2),
                'confidence': round(confidence, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ 預測代理性能失敗: {e}")
            return {'predicted_score': 0, 'confidence': 0}
