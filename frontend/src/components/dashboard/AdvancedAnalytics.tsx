/**
 * 高級數據分析組件
 * 提供多維度數據分析、自定義圖表、報告生成等功能
 */

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Card } from '../ui/Card';
import { spacing, borderRadius } from '../../styles';

// ============= 類型定義 =============

interface AdvancedAnalyticsProps {
  className?: string;
}

interface SystemOverview {
  totalProxies: number;
  activeProxies: number;
  totalTasks: number;
  activeTasks: number;
  systemUptime: number;
  memoryUsage: number;
  cpuUsage: number;
  proxySuccessRate: number;
  averageResponseTime: number;
  taskSuccessRate: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  diskUsage: number;
  networkIn: number;
  networkOut: number;
  lastUpdated: string;
}

interface AnalyticsData {
  overview: SystemOverview;
  metrics: Record<string, any[]>;
  trends: Record<string, number>;
  alerts: Array<{
    id: string;
    type: 'warning' | 'error' | 'info';
    message: string;
    timestamp: string;
  }>;
}

// ============= 樣式定義 =============

const AnalyticsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing[6]};
  padding: ${spacing[6]};
  background: var(--color-background-primary);
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[4]};
`;

const Title = styled.h2`
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-secondary-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const Controls = styled.div`
  display: flex;
  gap: ${spacing[3]};
  align-items: center;
`;

const FilterButton = styled.button<{ active?: boolean }>`
  padding: ${spacing[2]} ${spacing[4]};
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.md};
  background: ${({ active }) => active ? 'var(--color-primary-500)' : 'var(--color-background-card)'};
  color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-text-secondary)'};
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-primary-500);
    color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-primary-500)'};
  }
`;

const ExportButton = styled.button`
  padding: ${spacing[2]} ${spacing[4]};
  background: var(--color-success-500);
  color: var(--color-white);
  border: none;
  border-radius: ${borderRadius.md};
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: var(--color-success-600);
    transform: translateY(-1px);
  }
`;

const GridLayout = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: ${spacing[6]};
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const FullWidthSection = styled.div`
  grid-column: 1 / -1;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${spacing[4]};
  margin-bottom: ${spacing[6]};
`;

const MetricCard = styled(Card)`
  padding: ${spacing[4]};
  text-align: center;
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-primary-500);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px var(--color-shadow-light);
  }
`;

const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-primary-600);
  margin-bottom: ${spacing[1]};
`;

const MetricLabel = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const MetricTrend = styled.div<{ trend: 'up' | 'down' | 'stable' }>`
  font-size: 0.75rem;
  margin-top: ${spacing[1]};
  color: ${({ trend }) => {
    switch (trend) {
      case 'up': return 'var(--color-success-500)';
      case 'down': return 'var(--color-error-500)';
      default: return 'var(--color-text-secondary)';
    }
  }};
`;

const ChartContainer = styled(Card)`
  padding: ${spacing[6]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.lg};
`;

const ChartHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[4]};
`;

const ChartTitle = styled.h3`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const ChartControls = styled.div`
  display: flex;
  gap: ${spacing[2]};
`;

const ChartTypeButton = styled.button<{ active?: boolean }>`
  padding: ${spacing[1]} ${spacing[2]};
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.sm};
  background: ${({ active }) => active ? 'var(--color-primary-500)' : 'var(--color-background-card)'};
  color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-text-secondary)'};
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-primary-500);
  }
`;

const ChartCanvas = styled.div`
  height: 300px;
  position: relative;
  background: var(--color-background-subtle);
  border-radius: ${borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
`;

const AlertsSection = styled.div`
  margin-top: ${spacing[6]};
`;

const AlertItem = styled.div<{ type: 'warning' | 'error' | 'info' }>`
  display: flex;
  align-items: center;
  gap: ${spacing[3]};
  padding: ${spacing[3]};
  margin-bottom: ${spacing[2]};
  border-radius: ${borderRadius.md};
  background: ${({ type }) => {
    switch (type) {
      case 'error': return 'var(--color-error-50)';
      case 'warning': return 'var(--color-warning-50)';
      default: return 'var(--color-info-50)';
    }
  }};
  border-left: 4px solid ${({ type }) => {
    switch (type) {
      case 'error': return 'var(--color-error-500)';
      case 'warning': return 'var(--color-warning-500)';
      default: return 'var(--color-info-500)';
    }
  }};
`;

const AlertIcon = styled.div<{ type: 'warning' | 'error' | 'info' }>`
  font-size: 1.2rem;
  color: ${({ type }) => {
    switch (type) {
      case 'error': return 'var(--color-error-500)';
      case 'warning': return 'var(--color-warning-500)';
      default: return 'var(--color-info-500)';
    }
  }};
`;

const AlertContent = styled.div`
  flex: 1;
`;

const AlertMessage = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-primary);
  margin-bottom: ${spacing[1]};
`;

const AlertTime = styled.div`
  font-size: 0.75rem;
  color: var(--color-text-secondary);
`;

// ============= 組件實作 =============

/**
 * 高級數據分析組件
 */
export const AdvancedAnalytics: React.FC<AdvancedAnalyticsProps> = ({ className }) => {
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d' | '30d'>('24h');
  // const [selectedCharts] = useState<string[]>(['performance', 'usage']);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  // 模擬數據載入
  useEffect(() => {
    const loadAnalyticsData = async () => {
      setLoading(true);
      try {
        // 模擬 API 調用
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const mockData: AnalyticsData = {
          overview: {
            totalProxies: 1250,
            activeProxies: 1180,
            totalTasks: 45,
            activeTasks: 12,
            systemUptime: 99.8,
            memoryUsage: 68.5,
            cpuUsage: 42.3,
            proxySuccessRate: 91.2,
            averageResponseTime: 245,
            taskSuccessRate: 87.5,
            runningTasks: 12,
            completedTasks: 28,
            failedTasks: 5,
            diskUsage: 45.2,
            networkIn: 1250,
            networkOut: 980,
            lastUpdated: new Date().toISOString()
          },
          metrics: {},
          trends: {
            proxySuccessRate: 2.3,
            averageResponseTime: -5.1,
            taskSuccessRate: 1.8,
            systemLoad: -0.7
          },
          alerts: [
            {
              id: '1',
              type: 'warning',
              message: '代理節點 proxy-server-03 響應時間異常',
              timestamp: new Date(Date.now() - 300000).toISOString()
            },
            {
              id: '2',
              type: 'info',
              message: '系統已自動清理過期任務 25 個',
              timestamp: new Date(Date.now() - 600000).toISOString()
            }
          ]
        };
        
        setAnalyticsData(mockData);
      } catch (error) {
        console.error('載入分析數據失敗:', error);
      } finally {
        setLoading(false);
      }
    };

    loadAnalyticsData();
  }, [timeRange]);

  // 格式化數值
  const formatValue = (value: number, unit?: string) => {
    if (unit === '%') {
      return `${value.toFixed(1)}%`;
    }
    if (unit === 'ms') {
      return `${value.toFixed(0)}ms`;
    }
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  // 獲取趨勢指示器
  const getTrendIndicator = (value: number) => {
    if (value > 1) return { trend: 'up' as const, text: `↗ +${value.toFixed(1)}%` };
    if (value < -1) return { trend: 'down' as const, text: `↘ ${value.toFixed(1)}%` };
    return { trend: 'stable' as const, text: '→ 穩定' };
  };

  // 導出報告
  const handleExportReport = () => {
    // TODO: 實現報告導出功能
    console.log('導出分析報告');
  };

  if (loading) {
    return (
      <AnalyticsContainer className={className}>
        <div style={{ textAlign: 'center', padding: spacing[8], color: 'var(--color-text-secondary)' }}>
          載入高級分析數據中...
        </div>
      </AnalyticsContainer>
    );
  }

  if (!analyticsData) {
    return (
      <AnalyticsContainer className={className}>
        <div style={{ textAlign: 'center', padding: spacing[8], color: 'var(--color-error-500)' }}>
          無法載入分析數據
        </div>
      </AnalyticsContainer>
    );
  }

  return (
    <AnalyticsContainer className={className}>
      <Header>
        <Title>高級數據分析</Title>
        <Controls>
          {(['1h', '6h', '24h', '7d', '30d'] as const).map((range) => (
            <FilterButton
              key={range}
              active={timeRange === range}
              onClick={() => setTimeRange(range)}
            >
              {range}
            </FilterButton>
          ))}
          <ExportButton onClick={handleExportReport}>
            📊 導出報告
          </ExportButton>
        </Controls>
      </Header>

      {/* 關鍵指標概覽 */}
      <MetricsGrid>
        <MetricCard>
          <MetricValue>{analyticsData.overview.activeProxies}</MetricValue>
          <MetricLabel>活躍代理</MetricLabel>
          <MetricTrend trend={getTrendIndicator(analyticsData.trends.proxySuccessRate || 0).trend}>
            {getTrendIndicator(analyticsData.trends.proxySuccessRate || 0).text}
          </MetricTrend>
        </MetricCard>
        
        <MetricCard>
          <MetricValue>{formatValue(analyticsData.overview.proxySuccessRate, '%')}</MetricValue>
          <MetricLabel>代理成功率</MetricLabel>
          <MetricTrend trend={getTrendIndicator(analyticsData.trends.proxySuccessRate || 0).trend}>
            {getTrendIndicator(analyticsData.trends.proxySuccessRate || 0).text}
          </MetricTrend>
        </MetricCard>
        
        <MetricCard>
          <MetricValue>{formatValue(analyticsData.overview.averageResponseTime, 'ms')}</MetricValue>
          <MetricLabel>平均響應時間</MetricLabel>
          <MetricTrend trend={getTrendIndicator(analyticsData.trends.averageResponseTime || 0).trend}>
            {getTrendIndicator(analyticsData.trends.averageResponseTime || 0).text}
          </MetricTrend>
        </MetricCard>
        
        <MetricCard>
          <MetricValue>{formatValue(analyticsData.overview.taskSuccessRate, '%')}</MetricValue>
          <MetricLabel>任務成功率</MetricLabel>
          <MetricTrend trend={getTrendIndicator(analyticsData.trends.taskSuccessRate || 0).trend}>
            {getTrendIndicator(analyticsData.trends.taskSuccessRate || 0).text}
          </MetricTrend>
        </MetricCard>
      </MetricsGrid>

      {/* 圖表區域 */}
      <GridLayout>
        <ChartContainer>
          <ChartHeader>
            <ChartTitle>性能趨勢分析</ChartTitle>
            <ChartControls>
              {(['line', 'area', 'bar'] as const).map((type) => (
                <ChartTypeButton key={type} active={type === 'line'}>
                  {type === 'line' ? '📈' : type === 'area' ? '📊' : '📊'}
                </ChartTypeButton>
              ))}
            </ChartControls>
          </ChartHeader>
          <ChartCanvas>
            性能趨勢圖表 (待實現)
          </ChartCanvas>
        </ChartContainer>

        <ChartContainer>
          <ChartHeader>
            <ChartTitle>資源使用分析</ChartTitle>
            <ChartControls>
              {(['pie', 'bar'] as const).map((type) => (
                <ChartTypeButton key={type} active={type === 'pie'}>
                  {type === 'pie' ? '🥧' : '📊'}
                </ChartTypeButton>
              ))}
            </ChartControls>
          </ChartHeader>
          <ChartCanvas>
            資源使用圖表 (待實現)
          </ChartCanvas>
        </ChartContainer>
      </GridLayout>

      {/* 全寬度圖表 */}
      <FullWidthSection>
        <ChartContainer>
          <ChartHeader>
            <ChartTitle>任務執行時間線</ChartTitle>
            <ChartControls>
              <ChartTypeButton active>
                📅 時間線
              </ChartTypeButton>
            </ChartControls>
          </ChartHeader>
          <ChartCanvas>
            任務執行時間線圖表 (待實現)
          </ChartCanvas>
        </ChartContainer>
      </FullWidthSection>

      {/* 警報和通知 */}
      {analyticsData.alerts.length > 0 && (
        <AlertsSection>
          <h3 style={{ margin: `0 0 ${spacing[4]} 0`, color: 'var(--color-text-primary)' }}>系統警報</h3>
          {analyticsData.alerts.map((alert) => (
            <AlertItem key={alert.id} type={alert.type}>
              <AlertIcon type={alert.type}>
                {alert.type === 'error' ? '❌' : alert.type === 'warning' ? '⚠️' : 'ℹ️'}
              </AlertIcon>
              <AlertContent>
                <AlertMessage>{alert.message}</AlertMessage>
                <AlertTime>{new Date(alert.timestamp).toLocaleString('zh-TW')}</AlertTime>
              </AlertContent>
            </AlertItem>
          ))}
        </AlertsSection>
      )}
    </AnalyticsContainer>
  );
};

export default AdvancedAnalytics;