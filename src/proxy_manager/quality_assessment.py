"""代理質量評估模組

提供綜合的代理質量評分和排序功能：
- 多維度質量評估
- 動態權重調整
- 歷史性能追蹤
- 智能排序算法
- 質量預測模型
"""

import asyncio
import json
import time
import statistics
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import math

from .models import ProxyNode, ProxyProtocol, ProxyStatus
from .intelligent_detection import DetectionResult, BenchmarkResult, AnonymityLevel, ProxyType
from .config import get_config

logger = logging.getLogger(__name__)


class QualityGrade(Enum):
    """質量等級"""
    EXCELLENT = "excellent"    # 優秀 (90-100)
    GOOD = "good"              # 良好 (70-89)
    AVERAGE = "average"        # 一般 (50-69)
    POOR = "poor"              # 較差 (30-49)
    TERRIBLE = "terrible"      # 極差 (0-29)


@dataclass
class QualityMetrics:
    """質量指標"""
    # 基礎指標
    connectivity_score: float = 0.0      # 連接性評分 (0-100)
    speed_score: float = 0.0             # 速度評分 (0-100)
    stability_score: float = 0.0         # 穩定性評分 (0-100)
    anonymity_score: float = 0.0         # 匿名性評分 (0-100)
    security_score: float = 0.0          # 安全性評分 (0-100)
    
    # 高級指標
    reliability_score: float = 0.0       # 可靠性評分 (0-100)
    performance_score: float = 0.0       # 性能評分 (0-100)
    compatibility_score: float = 0.0     # 兼容性評分 (0-100)
    geographic_score: float = 0.0        # 地理位置評分 (0-100)
    cost_effectiveness: float = 0.0      # 成本效益評分 (0-100)
    
    # 綜合評分
    overall_score: float = 0.0           # 總體評分 (0-100)
    quality_grade: QualityGrade = QualityGrade.TERRIBLE
    
    # 元數據
    evaluation_time: datetime = field(default_factory=datetime.now)
    sample_size: int = 0                 # 評估樣本數量
    confidence_level: float = 0.0        # 置信度 (0-1)


@dataclass
class HistoricalPerformance:
    """歷史性能記錄"""
    proxy: ProxyNode
    timestamps: List[datetime] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    success_rates: List[float] = field(default_factory=list)
    quality_scores: List[float] = field(default_factory=list)
    error_counts: List[int] = field(default_factory=list)
    
    # 統計指標
    avg_response_time: float = 0.0
    avg_success_rate: float = 0.0
    avg_quality_score: float = 0.0
    uptime_percentage: float = 0.0
    trend_direction: str = "stable"      # "improving", "declining", "stable"
    
    def add_record(self, response_time: float, success_rate: float, 
                  quality_score: float, error_count: int = 0):
        """添加性能記錄"""
        now = datetime.now()
        
        self.timestamps.append(now)
        self.response_times.append(response_time)
        self.success_rates.append(success_rate)
        self.quality_scores.append(quality_score)
        self.error_counts.append(error_count)
        
        # 保持最近 100 條記錄
        if len(self.timestamps) > 100:
            self.timestamps = self.timestamps[-100:]
            self.response_times = self.response_times[-100:]
            self.success_rates = self.success_rates[-100:]
            self.quality_scores = self.quality_scores[-100:]
            self.error_counts = self.error_counts[-100:]
        
        self._update_statistics()
    
    def _update_statistics(self):
        """更新統計指標"""
        if not self.response_times:
            return
        
        self.avg_response_time = statistics.mean(self.response_times)
        self.avg_success_rate = statistics.mean(self.success_rates)
        self.avg_quality_score = statistics.mean(self.quality_scores)
        
        # 計算正常運行時間百分比
        working_count = sum(1 for rate in self.success_rates if rate > 0.5)
        self.uptime_percentage = working_count / len(self.success_rates) * 100
        
        # 分析趨勢
        self._analyze_trend()
    
    def _analyze_trend(self):
        """分析性能趨勢"""
        if len(self.quality_scores) < 5:
            self.trend_direction = "stable"
            return
        
        # 使用最近 10 個數據點分析趨勢
        recent_scores = self.quality_scores[-10:]
        
        # 計算線性回歸斜率
        n = len(recent_scores)
        x_values = list(range(n))
        
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(recent_scores)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, recent_scores))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator != 0:
            slope = numerator / denominator
            
            if slope > 1:
                self.trend_direction = "improving"
            elif slope < -1:
                self.trend_direction = "declining"
            else:
                self.trend_direction = "stable"
        else:
            self.trend_direction = "stable"


class ProxyQualityAssessor:
    """代理質量評估器
    
    提供全面的代理質量評估和排序功能
    """
    
    def __init__(self):
        self.config = get_config()
        
        # 評估權重配置
        self.weights = {
            "connectivity": 0.25,      # 連接性權重
            "speed": 0.20,             # 速度權重
            "stability": 0.15,         # 穩定性權重
            "anonymity": 0.15,         # 匿名性權重
            "security": 0.10,          # 安全性權重
            "reliability": 0.10,       # 可靠性權重
            "performance": 0.05        # 性能權重
        }
        
        # 歷史性能記錄
        self.performance_history: Dict[str, HistoricalPerformance] = {}
        
        # 評估統計
        self.assessment_stats = {
            "total_assessed": 0,
            "excellent_count": 0,
            "good_count": 0,
            "average_count": 0,
            "poor_count": 0,
            "terrible_count": 0
        }
    
    def assess_proxy_quality(self, 
                           proxy: ProxyNode,
                           detection_result: Optional[DetectionResult] = None,
                           benchmark_result: Optional[BenchmarkResult] = None,
                           custom_weights: Optional[Dict[str, float]] = None) -> QualityMetrics:
        """評估代理質量
        
        Args:
            proxy: 代理節點
            detection_result: 檢測結果
            benchmark_result: 基準測試結果
            custom_weights: 自定義權重
            
        Returns:
            質量指標
        """
        metrics = QualityMetrics()
        weights = custom_weights or self.weights
        
        try:
            # 基礎指標評估
            if detection_result:
                metrics.connectivity_score = self._evaluate_connectivity(detection_result)
                metrics.anonymity_score = self._evaluate_anonymity(detection_result)
                metrics.security_score = self._evaluate_security(detection_result)
                metrics.compatibility_score = self._evaluate_compatibility(detection_result)
            
            if benchmark_result:
                metrics.speed_score = self._evaluate_speed(benchmark_result)
                metrics.performance_score = self._evaluate_performance(benchmark_result)
            
            # 穩定性和可靠性評估（基於歷史數據）
            proxy_key = f"{proxy.host}:{proxy.port}"
            if proxy_key in self.performance_history:
                history = self.performance_history[proxy_key]
                metrics.stability_score = self._evaluate_stability(history)
                metrics.reliability_score = self._evaluate_reliability(history)
            else:
                # 新代理的預設評分
                metrics.stability_score = 50.0
                metrics.reliability_score = 50.0
            
            # 地理位置評分
            metrics.geographic_score = self._evaluate_geographic_location(proxy)
            
            # 成本效益評分
            metrics.cost_effectiveness = self._evaluate_cost_effectiveness(proxy, metrics)
            
            # 計算綜合評分
            metrics.overall_score = self._calculate_overall_score(metrics, weights)
            metrics.quality_grade = self._determine_quality_grade(metrics.overall_score)
            
            # 計算置信度
            metrics.confidence_level = self._calculate_confidence_level(proxy, detection_result, benchmark_result)
            
            # 更新歷史記錄
            self._update_performance_history(proxy, metrics, detection_result, benchmark_result)
            
            # 更新統計
            self._update_assessment_stats(metrics.quality_grade)
            
            logger.info(f"代理質量評估完成: {proxy.host}:{proxy.port} - 評分: {metrics.overall_score:.1f}, 等級: {metrics.quality_grade.value}")
            
        except Exception as e:
            logger.error(f"代理質量評估失敗 {proxy.host}:{proxy.port}: {e}")
            metrics.overall_score = 0.0
            metrics.quality_grade = QualityGrade.TERRIBLE
        
        return metrics
    
    def _evaluate_connectivity(self, detection_result: DetectionResult) -> float:
        """評估連接性"""
        score = 0.0
        
        # 基礎連接
        if detection_result.is_working:
            score += 40.0
        
        # 響應時間
        if detection_result.response_time > 0:
            if detection_result.response_time < 1000:  # < 1秒
                score += 30.0
            elif detection_result.response_time < 3000:  # < 3秒
                score += 20.0
            elif detection_result.response_time < 5000:  # < 5秒
                score += 10.0
        
        # 成功率
        if detection_result.success_rate > 0:
            score += detection_result.success_rate * 30.0
        
        return min(score, 100.0)
    
    def _evaluate_speed(self, benchmark_result: BenchmarkResult) -> float:
        """評估速度"""
        score = 0.0
        
        # 下載速度評分
        if benchmark_result.download_speed > 0:
            if benchmark_result.download_speed >= 10:  # >= 10 MB/s
                score += 40.0
            elif benchmark_result.download_speed >= 5:  # >= 5 MB/s
                score += 30.0
            elif benchmark_result.download_speed >= 1:  # >= 1 MB/s
                score += 20.0
            else:
                score += benchmark_result.download_speed * 10  # 線性評分
        
        # 延遲評分
        if benchmark_result.latency > 0:
            if benchmark_result.latency <= 100:  # <= 100ms
                score += 30.0
            elif benchmark_result.latency <= 300:  # <= 300ms
                score += 20.0
            elif benchmark_result.latency <= 500:  # <= 500ms
                score += 10.0
            else:
                score += max(0, 10 - (benchmark_result.latency - 500) / 100)
        
        # 抖動評分
        if benchmark_result.jitter >= 0:
            if benchmark_result.jitter <= 10:  # <= 10ms
                score += 20.0
            elif benchmark_result.jitter <= 50:  # <= 50ms
                score += 10.0
            else:
                score += max(0, 10 - (benchmark_result.jitter - 50) / 10)
        
        # 上傳速度評分
        if benchmark_result.upload_speed > 0:
            score += min(benchmark_result.upload_speed * 2, 10.0)
        
        return min(score, 100.0)
    
    def _evaluate_stability(self, history: HistoricalPerformance) -> float:
        """評估穩定性"""
        if not history.response_times:
            return 50.0
        
        score = 0.0
        
        # 正常運行時間
        score += history.uptime_percentage * 0.4
        
        # 響應時間穩定性
        if len(history.response_times) > 1:
            cv = statistics.stdev(history.response_times) / statistics.mean(history.response_times)
            stability_score = max(0, 100 - cv * 100)
            score += stability_score * 0.3
        
        # 成功率穩定性
        if len(history.success_rates) > 1:
            success_stability = 100 - (statistics.stdev(history.success_rates) * 100)
            score += max(0, success_stability) * 0.3
        
        return min(score, 100.0)
    
    def _evaluate_anonymity(self, detection_result: DetectionResult) -> float:
        """評估匿名性"""
        score = 0.0
        
        # 匿名性等級
        if detection_result.anonymity_level == AnonymityLevel.ELITE:
            score += 50.0
        elif detection_result.anonymity_level == AnonymityLevel.ANONYMOUS:
            score += 35.0
        elif detection_result.anonymity_level == AnonymityLevel.TRANSPARENT:
            score += 10.0
        
        # IP 洩漏檢測
        if not detection_result.real_ip_leaked:
            score += 15.0
        
        # DNS 洩漏檢測
        if not detection_result.dns_leak:
            score += 10.0
        
        # WebRTC 洩漏檢測
        if not detection_result.webrtc_leak:
            score += 10.0
        
        # 時區洩漏檢測
        if not detection_result.timezone_leak:
            score += 5.0
        
        # 語言洩漏檢測
        if not detection_result.language_leak:
            score += 5.0
        
        # 用戶代理一致性
        if detection_result.user_agent_consistency:
            score += 5.0
        
        return min(score, 100.0)
    
    def _evaluate_security(self, detection_result: DetectionResult) -> float:
        """評估安全性"""
        score = 0.0
        
        # HTTPS 支援
        if detection_result.supports_https:
            score += 30.0
        
        # CONNECT 方法支援
        if detection_result.supports_connect:
            score += 20.0
        
        # 指紋抗性
        score += detection_result.fingerprint_resistance * 30.0
        
        # 代理類型安全性
        if hasattr(detection_result, 'proxy_type'):
            if detection_result.proxy_type == ProxyType.RESIDENTIAL:
                score += 15.0
            elif detection_result.proxy_type == ProxyType.MOBILE:
                score += 10.0
            elif detection_result.proxy_type == ProxyType.DATACENTER:
                score += 5.0
        
        # 錯誤數量（越少越好）
        error_penalty = min(len(detection_result.errors) * 5, 20)
        score = max(0, score - error_penalty)
        
        return min(score, 100.0)
    
    def _evaluate_performance(self, benchmark_result: BenchmarkResult) -> float:
        """評估性能"""
        score = 0.0
        
        # 並發連接數
        if benchmark_result.concurrent_connections > 0:
            score += min(benchmark_result.concurrent_connections * 10, 40.0)
        
        # 頻寬穩定性
        score += benchmark_result.bandwidth_stability * 30.0
        
        # 封包丟失率（越低越好）
        if benchmark_result.packet_loss >= 0:
            packet_loss_score = max(0, 100 - benchmark_result.packet_loss * 10)
            score += packet_loss_score * 0.3
        
        return min(score, 100.0)
    
    def _evaluate_reliability(self, history: HistoricalPerformance) -> float:
        """評估可靠性"""
        if not history.quality_scores:
            return 50.0
        
        score = 0.0
        
        # 平均質量評分
        score += history.avg_quality_score * 0.4
        
        # 趨勢方向
        if history.trend_direction == "improving":
            score += 30.0
        elif history.trend_direction == "stable":
            score += 20.0
        elif history.trend_direction == "declining":
            score += 10.0
        
        # 數據樣本數量（更多樣本更可靠）
        sample_bonus = min(len(history.quality_scores) * 2, 30.0)
        score += sample_bonus
        
        return min(score, 100.0)
    
    def _evaluate_compatibility(self, detection_result: DetectionResult) -> float:
        """評估兼容性"""
        score = 50.0  # 基礎分
        
        # 協議支援
        if detection_result.supports_https:
            score += 25.0
        
        if detection_result.supports_connect:
            score += 25.0
        
        return min(score, 100.0)
    
    def _evaluate_geographic_location(self, proxy: ProxyNode) -> float:
        """評估地理位置"""
        # 這裡可以根據具體需求實現地理位置評分
        # 例如：距離目標地區的遠近、地區穩定性等
        
        # 暫時返回預設評分
        return 75.0
    
    def _evaluate_cost_effectiveness(self, proxy: ProxyNode, metrics: QualityMetrics) -> float:
        """評估成本效益"""
        # 免費代理的成本效益評分基於其質量
        base_score = (metrics.connectivity_score + metrics.speed_score + metrics.anonymity_score) / 3
        
        # 免費代理額外獎勵
        return min(base_score + 20.0, 100.0)
    
    def _calculate_overall_score(self, metrics: QualityMetrics, weights: Dict[str, float]) -> float:
        """計算綜合評分"""
        score = 0.0
        
        score += metrics.connectivity_score * weights.get("connectivity", 0.25)
        score += metrics.speed_score * weights.get("speed", 0.20)
        score += metrics.stability_score * weights.get("stability", 0.15)
        score += metrics.anonymity_score * weights.get("anonymity", 0.15)
        score += metrics.security_score * weights.get("security", 0.10)
        score += metrics.reliability_score * weights.get("reliability", 0.10)
        score += metrics.performance_score * weights.get("performance", 0.05)
        
        return min(score, 100.0)
    
    def _determine_quality_grade(self, overall_score: float) -> QualityGrade:
        """確定質量等級"""
        if overall_score >= 90:
            return QualityGrade.EXCELLENT
        elif overall_score >= 70:
            return QualityGrade.GOOD
        elif overall_score >= 50:
            return QualityGrade.AVERAGE
        elif overall_score >= 30:
            return QualityGrade.POOR
        else:
            return QualityGrade.TERRIBLE
    
    def _calculate_confidence_level(self, 
                                  proxy: ProxyNode,
                                  detection_result: Optional[DetectionResult],
                                  benchmark_result: Optional[BenchmarkResult]) -> float:
        """計算置信度"""
        confidence = 0.0
        
        # 檢測結果置信度
        if detection_result:
            confidence += 0.4
            if detection_result.success_rate > 0:
                confidence += 0.2
        
        # 基準測試置信度
        if benchmark_result:
            confidence += 0.3
        
        # 歷史數據置信度
        proxy_key = f"{proxy.host}:{proxy.port}"
        if proxy_key in self.performance_history:
            history = self.performance_history[proxy_key]
            sample_confidence = min(len(history.quality_scores) / 10, 0.1)
            confidence += sample_confidence
        
        return min(confidence, 1.0)
    
    def _update_performance_history(self, 
                                  proxy: ProxyNode,
                                  metrics: QualityMetrics,
                                  detection_result: Optional[DetectionResult],
                                  benchmark_result: Optional[BenchmarkResult]):
        """更新性能歷史記錄"""
        proxy_key = f"{proxy.host}:{proxy.port}"
        
        if proxy_key not in self.performance_history:
            self.performance_history[proxy_key] = HistoricalPerformance(proxy=proxy)
        
        history = self.performance_history[proxy_key]
        
        # 提取性能數據
        response_time = detection_result.response_time if detection_result else 0.0
        success_rate = detection_result.success_rate if detection_result else 0.0
        error_count = len(detection_result.errors) if detection_result else 0
        
        # 添加記錄
        history.add_record(response_time, success_rate, metrics.overall_score, error_count)
    
    def _update_assessment_stats(self, grade: QualityGrade):
        """更新評估統計"""
        self.assessment_stats["total_assessed"] += 1
        
        if grade == QualityGrade.EXCELLENT:
            self.assessment_stats["excellent_count"] += 1
        elif grade == QualityGrade.GOOD:
            self.assessment_stats["good_count"] += 1
        elif grade == QualityGrade.AVERAGE:
            self.assessment_stats["average_count"] += 1
        elif grade == QualityGrade.POOR:
            self.assessment_stats["poor_count"] += 1
        else:
            self.assessment_stats["terrible_count"] += 1
    
    def batch_assess_quality(self, 
                           proxies_with_results: List[Tuple[ProxyNode, Optional[DetectionResult], Optional[BenchmarkResult]]],
                           custom_weights: Optional[Dict[str, float]] = None) -> List[QualityMetrics]:
        """批量評估代理質量
        
        Args:
            proxies_with_results: 代理和檢測結果的元組列表
            custom_weights: 自定義權重
            
        Returns:
            質量指標列表
        """
        results = []
        
        for proxy, detection_result, benchmark_result in proxies_with_results:
            try:
                metrics = self.assess_proxy_quality(proxy, detection_result, benchmark_result, custom_weights)
                results.append(metrics)
            except Exception as e:
                logger.error(f"批量質量評估失敗 {proxy.host}:{proxy.port}: {e}")
                # 創建失敗的評估結果
                failed_metrics = QualityMetrics()
                failed_metrics.overall_score = 0.0
                failed_metrics.quality_grade = QualityGrade.TERRIBLE
                results.append(failed_metrics)
        
        logger.info(f"批量質量評估完成: {len(results)} 個代理")
        return results
    
    def rank_proxies(self, 
                    quality_metrics: List[QualityMetrics],
                    sort_by: str = "overall_score",
                    ascending: bool = False,
                    filter_grade: Optional[QualityGrade] = None) -> List[QualityMetrics]:
        """代理排序
        
        Args:
            quality_metrics: 質量指標列表
            sort_by: 排序依據
            ascending: 是否升序
            filter_grade: 過濾等級
            
        Returns:
            排序後的質量指標列表
        """
        # 過濾
        filtered_metrics = quality_metrics
        if filter_grade:
            filtered_metrics = [m for m in quality_metrics if m.quality_grade == filter_grade]
        
        # 排序
        try:
            if sort_by == "overall_score":
                sorted_metrics = sorted(filtered_metrics, key=lambda x: x.overall_score, reverse=not ascending)
            elif sort_by == "connectivity":
                sorted_metrics = sorted(filtered_metrics, key=lambda x: x.connectivity_score, reverse=not ascending)
            elif sort_by == "speed":
                sorted_metrics = sorted(filtered_metrics, key=lambda x: x.speed_score, reverse=not ascending)
            elif sort_by == "anonymity":
                sorted_metrics = sorted(filtered_metrics, key=lambda x: x.anonymity_score, reverse=not ascending)
            elif sort_by == "stability":
                sorted_metrics = sorted(filtered_metrics, key=lambda x: x.stability_score, reverse=not ascending)
            else:
                sorted_metrics = sorted(filtered_metrics, key=lambda x: x.overall_score, reverse=not ascending)
            
            return sorted_metrics
            
        except Exception as e:
            logger.error(f"代理排序失敗: {e}")
            return filtered_metrics
    
    def get_top_proxies(self, 
                       quality_metrics: List[QualityMetrics],
                       count: int = 10,
                       min_grade: QualityGrade = QualityGrade.AVERAGE) -> List[QualityMetrics]:
        """獲取頂級代理
        
        Args:
            quality_metrics: 質量指標列表
            count: 返回數量
            min_grade: 最低等級要求
            
        Returns:
            頂級代理列表
        """
        # 過濾最低等級
        grade_values = {
            QualityGrade.EXCELLENT: 5,
            QualityGrade.GOOD: 4,
            QualityGrade.AVERAGE: 3,
            QualityGrade.POOR: 2,
            QualityGrade.TERRIBLE: 1
        }
        
        min_grade_value = grade_values[min_grade]
        qualified_metrics = [
            m for m in quality_metrics 
            if grade_values[m.quality_grade] >= min_grade_value
        ]
        
        # 按綜合評分排序
        sorted_metrics = self.rank_proxies(qualified_metrics, "overall_score")
        
        return sorted_metrics[:count]
    
    def predict_proxy_quality(self, proxy: ProxyNode) -> Tuple[float, float]:
        """預測代理質量
        
        Args:
            proxy: 代理節點
            
        Returns:
            預測評分和置信度的元組
        """
        proxy_key = f"{proxy.host}:{proxy.port}"
        
        if proxy_key not in self.performance_history:
            return 50.0, 0.1  # 新代理的預設預測
        
        history = self.performance_history[proxy_key]
        
        if not history.quality_scores:
            return 50.0, 0.1
        
        # 簡單的趨勢預測
        recent_scores = history.quality_scores[-5:]  # 最近 5 次評分
        
        if len(recent_scores) < 2:
            return recent_scores[0], 0.3
        
        # 線性趨勢預測
        x_values = list(range(len(recent_scores)))
        y_values = recent_scores
        
        # 計算線性回歸
        n = len(recent_scores)
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator != 0:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            # 預測下一個時間點的評分
            predicted_score = slope * n + intercept
            predicted_score = max(0, min(100, predicted_score))  # 限制在 0-100 範圍
            
            # 計算置信度（基於歷史數據的一致性）
            variance = statistics.variance(recent_scores) if len(recent_scores) > 1 else 0
            confidence = max(0.1, 1.0 - variance / 1000)  # 變異越小，置信度越高
            
            return predicted_score, confidence
        else:
            return statistics.mean(recent_scores), 0.5
    
    def get_assessment_statistics(self) -> Dict[str, Any]:
        """獲取評估統計信息"""
        stats = self.assessment_stats.copy()
        
        if stats["total_assessed"] > 0:
            stats["excellent_rate"] = stats["excellent_count"] / stats["total_assessed"] * 100
            stats["good_rate"] = stats["good_count"] / stats["total_assessed"] * 100
            stats["average_rate"] = stats["average_count"] / stats["total_assessed"] * 100
            stats["poor_rate"] = stats["poor_count"] / stats["total_assessed"] * 100
            stats["terrible_rate"] = stats["terrible_count"] / stats["total_assessed"] * 100
            
            # 質量分佈
            stats["quality_distribution"] = {
                "excellent": stats["excellent_rate"],
                "good": stats["good_rate"],
                "average": stats["average_rate"],
                "poor": stats["poor_rate"],
                "terrible": stats["terrible_rate"]
            }
        
        # 歷史記錄統計
        stats["total_tracked_proxies"] = len(self.performance_history)
        
        if self.performance_history:
            avg_uptime = statistics.mean([h.uptime_percentage for h in self.performance_history.values()])
            stats["average_uptime"] = avg_uptime
            
            improving_count = sum(1 for h in self.performance_history.values() if h.trend_direction == "improving")
            stats["improving_proxies"] = improving_count
            stats["improving_rate"] = improving_count / len(self.performance_history) * 100
        
        return stats
    
    def export_quality_report(self, quality_metrics: List[QualityMetrics], 
                            filename: Optional[str] = None) -> str:
        """導出質量報告
        
        Args:
            quality_metrics: 質量指標列表
            filename: 文件名
            
        Returns:
            報告文件路徑
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"proxy_quality_report_{timestamp}.json"
        
        report_data = {
            "report_time": datetime.now().isoformat(),
            "total_proxies": len(quality_metrics),
            "statistics": self.get_assessment_statistics(),
            "proxies": []
        }
        
        for metrics in quality_metrics:
            proxy_data = {
                "proxy": {
                    "host": metrics.proxy.host if hasattr(metrics, 'proxy') else "unknown",
                    "port": metrics.proxy.port if hasattr(metrics, 'proxy') else 0,
                    "protocol": metrics.proxy.protocol.value if hasattr(metrics, 'proxy') else "unknown"
                },
                "quality_metrics": {
                    "overall_score": metrics.overall_score,
                    "quality_grade": metrics.quality_grade.value,
                    "connectivity_score": metrics.connectivity_score,
                    "speed_score": metrics.speed_score,
                    "stability_score": metrics.stability_score,
                    "anonymity_score": metrics.anonymity_score,
                    "security_score": metrics.security_score,
                    "reliability_score": metrics.reliability_score,
                    "performance_score": metrics.performance_score,
                    "compatibility_score": metrics.compatibility_score,
                    "geographic_score": metrics.geographic_score,
                    "cost_effectiveness": metrics.cost_effectiveness,
                    "confidence_level": metrics.confidence_level,
                    "evaluation_time": metrics.evaluation_time.isoformat()
                }
            }
            report_data["proxies"].append(proxy_data)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"質量報告已導出: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"導出質量報告失敗: {e}")
            raise
    
    def set_custom_weights(self, weights: Dict[str, float]):
        """設置自定義權重
        
        Args:
            weights: 權重字典
        """
        # 驗證權重總和
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"權重總和不等於 1.0: {total_weight}")
            # 正規化權重
            weights = {k: v / total_weight for k, v in weights.items()}
        
        self.weights.update(weights)
        logger.info(f"自定義權重已設置: {weights}")