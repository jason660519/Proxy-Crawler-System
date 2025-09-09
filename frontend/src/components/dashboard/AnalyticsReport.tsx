/**
 * 數據分析報告組件
 * 提供詳細的統計分析、趨勢分析和報告生成功能
 */

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Card } from '../ui/Card';
import { spacing, borderRadius } from '../../styles';

// ============= 類型定義 =============

interface AnalyticsReportProps {
  className?: string;
  data?: ReportData;
  timeRange?: TimeRange;
  onExport?: (format: ExportFormat) => void;
}

interface ReportData {
  metrics: MetricSummary[];
  trends: TrendAnalysis[];
  insights: Insight[];
  performance: PerformanceMetrics;
  timestamp: string;
}

interface MetricSummary {
  name: string;
  current: number;
  previous: number;
  change: number;
  changePercent: number;
  trend: 'up' | 'down' | 'stable';
  unit?: string;
}

interface TrendAnalysis {
  metric: string;
  direction: 'increasing' | 'decreasing' | 'stable';
  strength: 'strong' | 'moderate' | 'weak';
  confidence: number;
  description: string;
}

interface Insight {
  type: 'positive' | 'negative' | 'neutral' | 'warning';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  recommendation?: string;
}

interface PerformanceMetrics {
  uptime: number;
  responseTime: number;
  errorRate: number;
  throughput: number;
  efficiency: number;
}

type TimeRange = '1h' | '24h' | '7d' | '30d' | '90d';
type ExportFormat = 'pdf' | 'excel' | 'csv' | 'json';

// ============= 樣式定義 =============

const ReportContainer = styled(Card)`
  padding: ${spacing[6]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.lg};
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[6]};
  padding-bottom: ${spacing[4]};
  border-bottom: 1px solid var(--color-border-light);
`;

const Title = styled.h2`
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
`;

const Subtitle = styled.p`
  margin: ${spacing[1]} 0 0 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const Controls = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[3]};
`;

const TimeRangeSelector = styled.div`
  display: flex;
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.md};
  overflow: hidden;
`;

const TimeRangeButton = styled.button<{ active?: boolean }>`
  padding: ${spacing[2]} ${spacing[3]};
  border: none;
  background: ${({ active }) => active ? 'var(--color-primary-500)' : 'var(--color-background-card)'};
  color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-text-secondary)'};
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ active }) => active ? 'var(--color-primary-600)' : 'var(--color-background-hover)'};
  }

  &:not(:last-child) {
    border-right: 1px solid var(--color-border-default);
  }
`;

const ExportButton = styled.button`
  display: flex;
  align-items: center;
  gap: ${spacing[1]};
  padding: ${spacing[2]} ${spacing[4]};
  border: 1px solid var(--color-primary-500);
  border-radius: ${borderRadius.md};
  background: var(--color-primary-500);
  color: var(--color-white);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: var(--color-primary-600);
    border-color: var(--color-primary-600);
  }
`;

const Section = styled.div`
  margin-bottom: ${spacing[6]};

  &:last-child {
    margin-bottom: 0;
  }
`;

const SectionTitle = styled.h3`
  margin: 0 0 ${spacing[4]} 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${spacing[4]};
`;

const MetricCard = styled(Card)`
  padding: ${spacing[4]};
  background: var(--color-background-subtle);
  border: 1px solid var(--color-border-light);
  border-radius: ${borderRadius.md};
`;

const MetricName = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-bottom: ${spacing[1]};
`;

const MetricValue = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: ${spacing[2]};
`;

const MetricChange = styled.div<{ trend: 'up' | 'down' | 'stable' }>`
  display: flex;
  align-items: center;
  gap: ${spacing[1]};
  font-size: 0.75rem;
  font-weight: 500;
  color: ${({ trend }) => {
    switch (trend) {
      case 'up': return 'var(--color-success-600)';
      case 'down': return 'var(--color-error-600)';
      default: return 'var(--color-text-secondary)';
    }
  }};
`;

const TrendIcon = styled.span<{ trend: 'up' | 'down' | 'stable' }>`
  font-size: 0.875rem;
  
  &::before {
    content: ${({ trend }) => {
      switch (trend) {
        case 'up': return '"↗"';
        case 'down': return '"↘"';
        default: return '"→"';
      }
    }};
  }
`;

const TrendsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing[3]};
`;

const TrendItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing[3]};
  background: var(--color-background-subtle);
  border: 1px solid var(--color-border-light);
  border-radius: ${borderRadius.md};
`;

const TrendInfo = styled.div`
  flex: 1;
`;

const TrendMetric = styled.div`
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: ${spacing[1]};
`;

const TrendDescription = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const TrendBadge = styled.div<{ direction: string; strength: string }>`
  display: flex;
  align-items: center;
  gap: ${spacing[1]};
  padding: ${spacing[1]} ${spacing[2]};
  border-radius: ${borderRadius.sm};
  font-size: 0.75rem;
  font-weight: 500;
  background: ${({ direction, strength }) => {
    if (direction === 'increasing') {
      return strength === 'strong' ? 'var(--color-success-100)' : 'var(--color-success-50)';
    } else if (direction === 'decreasing') {
      return strength === 'strong' ? 'var(--color-error-100)' : 'var(--color-error-50)';
    }
    return 'var(--color-background-muted)';
  }};
  color: ${({ direction, strength }) => {
    if (direction === 'increasing') {
      return strength === 'strong' ? 'var(--color-success-700)' : 'var(--color-success-600)';
    } else if (direction === 'decreasing') {
      return strength === 'strong' ? 'var(--color-error-700)' : 'var(--color-error-600)';
    }
    return 'var(--color-text-secondary)';
  }};
`;

const InsightsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing[3]};
`;

const InsightItem = styled.div<{ type: string; impact: string }>`
  padding: ${spacing[4]};
  border-left: 4px solid ${({ type }) => {
    switch (type) {
      case 'positive': return 'var(--color-success-500)';
      case 'negative': return 'var(--color-error-500)';
      case 'warning': return 'var(--color-warning-500)';
      default: return 'var(--color-info-500)';
    }
  }};
  background: ${({ type }) => {
    switch (type) {
      case 'positive': return 'var(--color-success-50)';
      case 'negative': return 'var(--color-error-50)';
      case 'warning': return 'var(--color-warning-50)';
      default: return 'var(--color-info-50)';
    }
  }};
  border-radius: ${borderRadius.md};
`;

const InsightHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[2]};
`;

const InsightTitle = styled.div`
  font-weight: 600;
  color: var(--color-text-primary);
`;

const ImpactBadge = styled.div<{ impact: string }>`
  padding: ${spacing[1]} ${spacing[2]};
  border-radius: ${borderRadius.sm};
  font-size: 0.75rem;
  font-weight: 500;
  background: ${({ impact }) => {
    switch (impact) {
      case 'high': return 'var(--color-error-100)';
      case 'medium': return 'var(--color-warning-100)';
      default: return 'var(--color-info-100)';
    }
  }};
  color: ${({ impact }) => {
    switch (impact) {
      case 'high': return 'var(--color-error-700)';
      case 'medium': return 'var(--color-warning-700)';
      default: return 'var(--color-info-700)';
    }
  }};
`;

const InsightDescription = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-bottom: ${spacing[2]};
`;

const InsightRecommendation = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-primary);
  font-weight: 500;
  padding: ${spacing[2]};
  background: var(--color-background-card);
  border-radius: ${borderRadius.sm};
  border: 1px solid var(--color-border-light);
`;

const PerformanceGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: ${spacing[4]};
`;

const PerformanceCard = styled(Card)`
  padding: ${spacing[4]};
  text-align: center;
  background: var(--color-background-subtle);
  border: 1px solid var(--color-border-light);
  border-radius: ${borderRadius.md};
`;

const PerformanceValue = styled.div<{ score: number }>`
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: ${spacing[1]};
  color: ${({ score }) => {
    if (score >= 90) return 'var(--color-success-600)';
    if (score >= 70) return 'var(--color-warning-600)';
    return 'var(--color-error-600)';
  }};
`;

const PerformanceLabel = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const LoadingState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-secondary);
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-secondary);
  text-align: center;
  
  .empty-icon {
    font-size: 2rem;
    margin-bottom: ${spacing[2]};
  }
  
  .empty-message {
    font-size: 0.875rem;
  }
`;

// ============= 工具函數 =============

/**
 * 格式化數值
 */
const formatValue = (value: number, unit?: string): string => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M${unit || ''}`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K${unit || ''}`;
  }
  return `${value.toFixed(1)}${unit || ''}`;
};

/**
 * 格式化百分比
 */
const formatPercent = (value: number): string => {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
};

/**
 * 生成模擬數據
 */
const generateMockData = (): ReportData => {
  return {
    metrics: [
      {
        name: '總請求數',
        current: 125430,
        previous: 118200,
        change: 7230,
        changePercent: 6.1,
        trend: 'up',
        unit: ''
      },
      {
        name: '成功率',
        current: 98.5,
        previous: 97.8,
        change: 0.7,
        changePercent: 0.7,
        trend: 'up',
        unit: '%'
      },
      {
        name: '平均響應時間',
        current: 245,
        previous: 280,
        change: -35,
        changePercent: -12.5,
        trend: 'down',
        unit: 'ms'
      },
      {
        name: '活躍代理數',
        current: 1250,
        previous: 1180,
        change: 70,
        changePercent: 5.9,
        trend: 'up',
        unit: ''
      }
    ],
    trends: [
      {
        metric: '請求量',
        direction: 'increasing',
        strength: 'strong',
        confidence: 95,
        description: '過去7天請求量持續增長，增長率達到15%'
      },
      {
        metric: '錯誤率',
        direction: 'decreasing',
        strength: 'moderate',
        confidence: 78,
        description: '錯誤率呈下降趨勢，系統穩定性有所改善'
      },
      {
        metric: '響應時間',
        direction: 'stable',
        strength: 'weak',
        confidence: 65,
        description: '響應時間保持相對穩定，波動較小'
      }
    ],
    insights: [
      {
        type: 'positive',
        title: '系統性能優化成效顯著',
        description: '通過最近的優化措施，系統響應時間降低了12.5%，用戶體驗得到明顯改善。',
        impact: 'high',
        recommendation: '建議繼續監控性能指標，並考慮將優化策略應用到其他模組。'
      },
      {
        type: 'warning',
        title: '代理池使用率接近上限',
        description: '當前代理池使用率已達到85%，可能影響系統的擴展能力。',
        impact: 'medium',
        recommendation: '建議增加代理資源或優化代理分配策略。'
      },
      {
        type: 'neutral',
        title: '用戶活躍度保持穩定',
        description: '用戶活躍度在過去30天內保持穩定，沒有明顯的增長或下降趨勢。',
        impact: 'low'
      }
    ],
    performance: {
      uptime: 99.8,
      responseTime: 85,
      errorRate: 98.5,
      throughput: 92,
      efficiency: 88
    },
    timestamp: new Date().toISOString()
  };
};

// ============= 組件實作 =============

/**
 * 數據分析報告組件
 */
export const AnalyticsReport: React.FC<AnalyticsReportProps> = ({
  className,
  data,
  timeRange: initialTimeRange = '24h',
  onExport
}) => {
  const [timeRange, setTimeRange] = useState<TimeRange>(initialTimeRange);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  
  // 模擬數據加載
  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      setReportData(data || generateMockData());
      setLoading(false);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [data, timeRange]);
  
  // 時間範圍選項
  const timeRangeOptions: { value: TimeRange; label: string }[] = [
    { value: '1h', label: '1小時' },
    { value: '24h', label: '24小時' },
    { value: '7d', label: '7天' },
    { value: '30d', label: '30天' },
    { value: '90d', label: '90天' }
  ];
  
  // 處理導出
  const handleExport = () => {
    if (onExport) {
      onExport('pdf');
    } else {
      // 模擬導出
      console.log('導出報告:', reportData);
      alert('報告導出功能開發中...');
    }
  };
  
  if (loading) {
    return (
      <ReportContainer className={className}>
        <LoadingState>
          <div>正在生成報告...</div>
        </LoadingState>
      </ReportContainer>
    );
  }
  
  if (!reportData) {
    return (
      <ReportContainer className={className}>
        <EmptyState>
          <div className="empty-icon">📊</div>
          <div className="empty-message">暫無報告數據</div>
        </EmptyState>
      </ReportContainer>
    );
  }
  
  return (
    <ReportContainer className={className}>
      <Header>
        <div>
          <Title>數據分析報告</Title>
          <Subtitle>
            生成時間: {new Date(reportData.timestamp).toLocaleString('zh-TW')}
          </Subtitle>
        </div>
        <Controls>
          <TimeRangeSelector>
            {timeRangeOptions.map(({ value, label }) => (
              <TimeRangeButton
                key={value}
                active={timeRange === value}
                onClick={() => setTimeRange(value)}
              >
                {label}
              </TimeRangeButton>
            ))}
          </TimeRangeSelector>
          <ExportButton onClick={handleExport}>
            <span>📄</span>
            導出報告
          </ExportButton>
        </Controls>
      </Header>
      
      {/* 關鍵指標 */}
      <Section>
        <SectionTitle>關鍵指標</SectionTitle>
        <MetricsGrid>
          {reportData.metrics.map((metric, index) => (
            <MetricCard key={index}>
              <MetricName>{metric.name}</MetricName>
              <MetricValue>
                {formatValue(metric.current, metric.unit)}
              </MetricValue>
              <MetricChange trend={metric.trend}>
                <TrendIcon trend={metric.trend} />
                {formatPercent(metric.changePercent)}
                <span>({formatValue(Math.abs(metric.change), metric.unit)})</span>
              </MetricChange>
            </MetricCard>
          ))}
        </MetricsGrid>
      </Section>
      
      {/* 趨勢分析 */}
      <Section>
        <SectionTitle>趨勢分析</SectionTitle>
        <TrendsList>
          {reportData.trends.map((trend, index) => (
            <TrendItem key={index}>
              <TrendInfo>
                <TrendMetric>{trend.metric}</TrendMetric>
                <TrendDescription>{trend.description}</TrendDescription>
              </TrendInfo>
              <TrendBadge direction={trend.direction} strength={trend.strength}>
                {trend.direction === 'increasing' ? '📈' : trend.direction === 'decreasing' ? '📉' : '➡️'}
                {trend.strength === 'strong' ? '強' : trend.strength === 'moderate' ? '中' : '弱'}
                ({trend.confidence}%)
              </TrendBadge>
            </TrendItem>
          ))}
        </TrendsList>
      </Section>
      
      {/* 洞察分析 */}
      <Section>
        <SectionTitle>洞察分析</SectionTitle>
        <InsightsList>
          {reportData.insights.map((insight, index) => (
            <InsightItem key={index} type={insight.type} impact={insight.impact}>
              <InsightHeader>
                <InsightTitle>{insight.title}</InsightTitle>
                <ImpactBadge impact={insight.impact}>
                  {insight.impact === 'high' ? '高影響' : insight.impact === 'medium' ? '中影響' : '低影響'}
                </ImpactBadge>
              </InsightHeader>
              <InsightDescription>{insight.description}</InsightDescription>
              {insight.recommendation && (
                <InsightRecommendation>
                  💡 建議: {insight.recommendation}
                </InsightRecommendation>
              )}
            </InsightItem>
          ))}
        </InsightsList>
      </Section>
      
      {/* 性能評分 */}
      <Section>
        <SectionTitle>性能評分</SectionTitle>
        <PerformanceGrid>
          <PerformanceCard>
            <PerformanceValue score={reportData.performance.uptime}>
              {reportData.performance.uptime}%
            </PerformanceValue>
            <PerformanceLabel>系統可用性</PerformanceLabel>
          </PerformanceCard>
          <PerformanceCard>
            <PerformanceValue score={reportData.performance.responseTime}>
              {reportData.performance.responseTime}
            </PerformanceValue>
            <PerformanceLabel>響應時間評分</PerformanceLabel>
          </PerformanceCard>
          <PerformanceCard>
            <PerformanceValue score={reportData.performance.errorRate}>
              {reportData.performance.errorRate}%
            </PerformanceValue>
            <PerformanceLabel>成功率</PerformanceLabel>
          </PerformanceCard>
          <PerformanceCard>
            <PerformanceValue score={reportData.performance.throughput}>
              {reportData.performance.throughput}
            </PerformanceValue>
            <PerformanceLabel>吞吐量評分</PerformanceLabel>
          </PerformanceCard>
          <PerformanceCard>
            <PerformanceValue score={reportData.performance.efficiency}>
              {reportData.performance.efficiency}
            </PerformanceValue>
            <PerformanceLabel>效率評分</PerformanceLabel>
          </PerformanceCard>
        </PerformanceGrid>
      </Section>
    </ReportContainer>
  );
};

export default AnalyticsReport;