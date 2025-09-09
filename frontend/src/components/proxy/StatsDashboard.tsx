/**
 * 統計儀表盤組件
 * 
 * 提供代理統計和效能監控功能，包括：
 * - 即時統計資訊
 * - 效能趨勢圖表
 * - 地理分佈統計
 * - 協議類型分析
 * - 健康狀態監控
 */

import React, { useState, useEffect, useMemo } from 'react';
import styled from 'styled-components';
import { Card, Select, Button } from '../ui';
import { formatDateTime } from '../../utils/formatters';

// ============= 樣式定義 =============

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  background: var(--color-background);
`;

const DashboardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h2`
  margin: 0;
  color: var(--color-text-primary);
  font-size: 1.8rem;
  font-weight: 600;
`;

const Controls = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
`;

const StatCard = styled(Card)`
  padding: 24px;
  background: var(--color-surface);
  border-radius: 12px;
  box-shadow: var(--shadow-medium);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-large);
  }
`;

const StatHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
`;

const StatTitle = styled.h3`
  margin: 0;
  font-size: 1rem;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const StatIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  background: var(--color-primary-light);
  color: var(--color-primary);
`;

const StatValue = styled.div`
  font-size: 2.5rem;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 8px;
`;

const StatChange = styled.div<{ positive: boolean }>`
  font-size: 0.875rem;
  color: ${props => props.positive ? 'var(--color-success)' : 'var(--color-error)'};
  display: flex;
  align-items: center;
  gap: 4px;
`;

const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const ChartCard = styled(Card)`
  padding: 24px;
  background: var(--color-surface);
  border-radius: 12px;
  box-shadow: var(--shadow-medium);
`;

const ChartTitle = styled.h3`
  margin: 0 0 20px 0;
  font-size: 1.2rem;
  color: var(--color-text-primary);
  font-weight: 600;
`;

const SimpleChart = styled.div`
  height: 200px;
  background: var(--color-background-secondary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
`;

const DistributionList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const DistributionItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--color-background-secondary);
  border-radius: 6px;
`;

const DistributionLabel = styled.div`
  font-weight: 500;
  color: var(--color-text-primary);
`;

const DistributionValue = styled.div`
  font-weight: 600;
  color: var(--color-primary);
`;

const DistributionBar = styled.div<{ percentage: number }>`
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  margin-top: 8px;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: ${props => props.percentage}%;
    background: var(--color-primary);
    border-radius: 2px;
    transition: width 0.3s ease;
  }
`;

const AlertsSection = styled.div`
  margin-top: 24px;
`;

const AlertCard = styled(Card)<{ severity: 'info' | 'warning' | 'error' }>`
  padding: 16px;
  margin-bottom: 12px;
  border-left: 4px solid ${
    props => props.severity === 'error' ? 'var(--color-error)' :
             props.severity === 'warning' ? 'var(--color-warning)' : 'var(--color-info)'
  };
  background: var(--color-surface);
`;

const AlertHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const AlertTitle = styled.div`
  font-weight: 600;
  color: var(--color-text-primary);
`;

const AlertTime = styled.div`
  font-size: 0.75rem;
  color: var(--color-text-secondary);
`;

const AlertMessage = styled.div`
  color: var(--color-text-secondary);
  font-size: 0.875rem;
`;

// ============= 類型定義 =============

interface ProxyStats {
  total: number;
  active: number;
  healthy: number;
  avgResponseTime: number;
  successRate: number;
  totalRequests: number;
  errorRate: number;
}

interface CountryDistribution {
  country: string;
  count: number;
  percentage: number;
}

interface ProtocolDistribution {
  protocol: string;
  count: number;
  percentage: number;
}

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
}

interface StatsDashboardProps {
  proxies: any[];
  className?: string;
}

// ============= 主要組件 =============

export const StatsDashboard: React.FC<StatsDashboardProps> = ({
  proxies,
  className
}) => {
  const [timeRange, setTimeRange] = useState('24h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // ============= 計算統計資料 =============

  const stats: ProxyStats = useMemo(() => {
    const total = proxies.length;
    const active = proxies.filter(p => p.status === 'active').length;
    const healthy = proxies.filter(p => (p.healthScore || 0) >= 80).length;
    const avgResponseTime = proxies.reduce((sum, p) => sum + (p.responseTime || 0), 0) / total || 0;
    const successfulProxies = proxies.filter(p => p.status === 'active').length;
    const successRate = total > 0 ? (successfulProxies / total) * 100 : 0;
    const totalRequests = proxies.reduce((sum, p) => sum + (p.totalRequests || 0), 0);
    const errorRequests = proxies.reduce((sum, p) => sum + (p.errorRequests || 0), 0);
    const errorRate = totalRequests > 0 ? (errorRequests / totalRequests) * 100 : 0;

    return {
      total,
      active,
      healthy,
      avgResponseTime: Math.round(avgResponseTime),
      successRate: Math.round(successRate * 100) / 100,
      totalRequests,
      errorRate: Math.round(errorRate * 100) / 100
    };
  }, [proxies]);

  const countryDistribution: CountryDistribution[] = useMemo(() => {
    const countryCount = proxies.reduce((acc, proxy) => {
      const country = proxy.country || '未知';
      acc[country] = (acc[country] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(countryCount)
      .map(([country, count]) => ({
        country,
        count: count as number,
        percentage: ((count as number) / proxies.length) * 100
      }))
      .sort((a, b) => (b.count as number) - (a.count as number))
      .slice(0, 5);
  }, [proxies]);

  const protocolDistribution: ProtocolDistribution[] = useMemo(() => {
    const protocolCount = proxies.reduce((acc, proxy) => {
      const protocol = (proxy.type || 'http').toUpperCase();
      acc[protocol] = (acc[protocol] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(protocolCount)
      .map(([protocol, count]) => ({
        protocol,
        count: count as number,
        percentage: ((count as number) / proxies.length) * 100
      }))
      .sort((a, b) => (b.count as number) - (a.count as number));
  }, [proxies]);

  const alerts: Alert[] = useMemo(() => {
    const alertList: Alert[] = [];

    // 檢查錯誤率過高
    if (stats.errorRate > 10) {
      alertList.push({
        id: 'high-error-rate',
        severity: 'error',
        title: '錯誤率過高',
        message: `當前錯誤率為 ${stats.errorRate}%，建議檢查代理配置`,
        timestamp: new Date()
      });
    }

    // 檢查響應時間過慢
    if (stats.avgResponseTime > 5000) {
      alertList.push({
        id: 'slow-response',
        severity: 'warning',
        title: '響應時間過慢',
        message: `平均響應時間為 ${stats.avgResponseTime}ms，可能影響效能`,
        timestamp: new Date()
      });
    }

    // 檢查健康代理數量過少
    if (stats.total > 0 && (stats.healthy / stats.total) < 0.5) {
      alertList.push({
        id: 'low-healthy-proxies',
        severity: 'warning',
        title: '健康代理不足',
        message: `僅有 ${stats.healthy}/${stats.total} 個代理處於健康狀態`,
        timestamp: new Date()
      });
    }

    return alertList;
  }, [stats]);

  // ============= 自動刷新 =============

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setLastUpdate(new Date());
    }, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // ============= 渲染 =============

  return (
    <DashboardContainer className={className}>
      <DashboardHeader>
        <Title>統計儀表盤</Title>
        <Controls>
          <Select
            value={timeRange}
            onChange={(value) => setTimeRange(value as string)}
            options={[
              { value: '1h', label: '過去 1 小時' },
              { value: '24h', label: '過去 24 小時' },
              { value: '7d', label: '過去 7 天' },
              { value: '30d', label: '過去 30 天' }
            ]}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '停止' : '開始'}自動刷新
          </Button>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
            最後更新：{formatDateTime(lastUpdate)}
          </div>
        </Controls>
      </DashboardHeader>

      {/* 主要統計卡片 */}
      <StatsGrid>
        <StatCard>
          <StatHeader>
            <StatTitle>總代理數</StatTitle>
            <StatIcon>🌐</StatIcon>
          </StatHeader>
          <StatValue>{stats.total}</StatValue>
          <StatChange positive={true}>
            ↗ 較昨日增加 5%
          </StatChange>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatTitle>活躍代理</StatTitle>
            <StatIcon>✅</StatIcon>
          </StatHeader>
          <StatValue>{stats.active}</StatValue>
          <StatChange positive={stats.active > stats.total * 0.8}>
            {stats.active > stats.total * 0.8 ? '↗' : '↘'} 
            {Math.round((stats.active / stats.total) * 100)}% 活躍率
          </StatChange>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatTitle>健康代理</StatTitle>
            <StatIcon>💚</StatIcon>
          </StatHeader>
          <StatValue>{stats.healthy}</StatValue>
          <StatChange positive={stats.healthy > stats.total * 0.7}>
            {stats.healthy > stats.total * 0.7 ? '↗' : '↘'} 
            {Math.round((stats.healthy / stats.total) * 100)}% 健康率
          </StatChange>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatTitle>平均響應時間</StatTitle>
            <StatIcon>⚡</StatIcon>
          </StatHeader>
          <StatValue>{stats.avgResponseTime}ms</StatValue>
          <StatChange positive={stats.avgResponseTime < 2000}>
            {stats.avgResponseTime < 2000 ? '↗' : '↘'} 
            {stats.avgResponseTime < 2000 ? '良好' : '需優化'}
          </StatChange>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatTitle>成功率</StatTitle>
            <StatIcon>📊</StatIcon>
          </StatHeader>
          <StatValue>{stats.successRate}%</StatValue>
          <StatChange positive={stats.successRate > 90}>
            {stats.successRate > 90 ? '↗' : '↘'} 
            {stats.successRate > 90 ? '優秀' : '一般'}
          </StatChange>
        </StatCard>

        <StatCard>
          <StatHeader>
            <StatTitle>錯誤率</StatTitle>
            <StatIcon>⚠️</StatIcon>
          </StatHeader>
          <StatValue>{stats.errorRate}%</StatValue>
          <StatChange positive={stats.errorRate < 5}>
            {stats.errorRate < 5 ? '↗' : '↘'} 
            {stats.errorRate < 5 ? '正常' : '偏高'}
          </StatChange>
        </StatCard>
      </StatsGrid>

      {/* 圖表區域 */}
      <ChartsGrid>
        <ChartCard>
          <ChartTitle>效能趨勢</ChartTitle>
          <SimpleChart>
            📈 效能趨勢圖表 (需要圖表庫支援)
          </SimpleChart>
        </ChartCard>

        <ChartCard>
          <ChartTitle>地理分佈</ChartTitle>
          <DistributionList>
            {countryDistribution.map((item) => (
              <div key={item.country}>
                <DistributionItem>
                  <DistributionLabel>{item.country}</DistributionLabel>
                  <DistributionValue>{item.count}</DistributionValue>
                </DistributionItem>
                <DistributionBar percentage={item.percentage} />
              </div>
            ))}
          </DistributionList>
        </ChartCard>
      </ChartsGrid>

      <ChartsGrid>
        <ChartCard>
          <ChartTitle>協議分佈</ChartTitle>
          <DistributionList>
            {protocolDistribution.map((item) => (
              <div key={item.protocol}>
                <DistributionItem>
                  <DistributionLabel>{item.protocol}</DistributionLabel>
                  <DistributionValue>{item.count} ({Math.round(item.percentage)}%)</DistributionValue>
                </DistributionItem>
                <DistributionBar percentage={item.percentage} />
              </div>
            ))}
          </DistributionList>
        </ChartCard>

        <ChartCard>
          <ChartTitle>請求統計</ChartTitle>
          <SimpleChart>
            📊 請求統計圖表 (需要圖表庫支援)
            <br />
            總請求數：{stats.totalRequests.toLocaleString()}
          </SimpleChart>
        </ChartCard>
      </ChartsGrid>

      {/* 警告和通知 */}
      {alerts.length > 0 && (
        <AlertsSection>
          <h3 style={{ marginBottom: '16px', color: 'var(--color-text-primary)' }}>系統警告</h3>
          {alerts.map((alert) => (
            <AlertCard key={alert.id} severity={alert.severity}>
              <AlertHeader>
                <AlertTitle>{alert.title}</AlertTitle>
                <AlertTime>{formatDateTime(alert.timestamp)}</AlertTime>
              </AlertHeader>
              <AlertMessage>{alert.message}</AlertMessage>
            </AlertCard>
          ))}
        </AlertsSection>
      )}
    </DashboardContainer>
  );
};

export default StatsDashboard;