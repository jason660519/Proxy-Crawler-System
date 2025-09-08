/**
 * 健康狀態卡片組件
 * 顯示系統健康狀態、連線數量、成功率等關鍵指標
 */

import React from 'react';
import styled from 'styled-components';
import { Card } from '../ui/Card';
import { useHealthStatus } from '../../hooks';
import { spacing, borderRadius } from '../../styles';

// ============= 類型定義 =============

interface HealthCardProps {
  className?: string;
}

// 健康指標類型
interface HealthMetric {
  label: string;
  value: string | number;
  status?: 'healthy' | 'warning' | 'error';
}

interface StatusIndicatorProps {
  status: 'healthy' | 'warning' | 'error' | 'unknown';
}

// ============= 樣式定義 =============

const HealthCardContainer = styled(Card)`
  padding: ${spacing[6]};
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-primary);
  border-radius: ${borderRadius.lg};
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-border-focus);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[4]};
`;

const Title = styled.h3`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const StatusIndicator = styled.div<StatusIndicatorProps>`
  display: flex;
  align-items: center;
  gap: ${spacing[1]};
  padding: ${spacing[1]} ${spacing[2]};
  border-radius: ${borderRadius.full};
  font-size: 0.875rem;
  font-weight: 500;
  
  ${({ status }) => {
    switch (status) {
      case 'healthy':
        return `
          background: var(--color-status-success-bg);
          color: var(--color-status-success);
        `;
      case 'warning':
        return `
          background: var(--color-status-warning-bg);
          color: var(--color-status-warning);
        `;
      case 'error':
        return `
          background: var(--color-status-error-bg);
          color: var(--color-status-error);
        `;
      default:
        return `
          background: var(--color-background-secondary);
          color: var(--color-text-secondary);
        `;
    }
  }}

  &::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
  }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: ${spacing[4]};
  margin-top: ${spacing[4]};
`;

const MetricItem = styled.div`
  text-align: center;
`;

const MetricValue = styled.div`
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: ${spacing[1]};
`;

const MetricLabel = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const LoadingState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${spacing[8]};
  color: var(--color-text-secondary);
`;

const ErrorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: ${spacing[8]};
  color: var(--color-status-error);
  text-align: center;
  
  .error-message {
    margin-top: ${spacing[2]};
    font-size: 0.875rem;
  }
`;

// ============= 組件實作 =============

/**
 * 健康狀態卡片組件
 */
export const HealthCard: React.FC<HealthCardProps> = ({ className }) => {
  const { mainHealth, loading, error } = useHealthStatus();

  // 載入狀態
  if (loading) {
    return (
      <HealthCardContainer className={className}>
        <LoadingState>
          載入健康狀態中...
        </LoadingState>
      </HealthCardContainer>
    );
  }

  // 錯誤狀態
  if (error) {
    return (
      <HealthCardContainer className={className}>
        <ErrorState>
          <div>⚠️</div>
          <div className="error-message">
            無法載入健康狀態：{error.message}
          </div>
        </ErrorState>
      </HealthCardContainer>
    );
  }

  // 正常狀態
  if (!mainHealth) {
    return (
      <HealthCardContainer className={className}>
        <ErrorState>
          <div>📊</div>
          <div className="error-message">
            暫無健康狀態資料
          </div>
        </ErrorState>
      </HealthCardContainer>
    );
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return '健康';
      case 'warning': return '警告';
      case 'error': return '錯誤';
      default: return '未知';
    }
  };

  return (
    <HealthCardContainer className={className}>
      <Header>
        <Title>系統健康狀態</Title>
        <StatusIndicator status={mainHealth.status as any}>
          {getStatusText(mainHealth.status)}
        </StatusIndicator>
      </Header>

      <MetricsGrid>
        <MetricItem>
          <MetricValue>{mainHealth?.details?.activeConnections || 0}</MetricValue>
          <MetricLabel>活躍連線</MetricLabel>
        </MetricItem>
        
        <MetricItem>
          <MetricValue>{mainHealth?.details?.totalProxies || 0}</MetricValue>
          <MetricLabel>代理節點</MetricLabel>
        </MetricItem>
        
        <MetricItem>
          <MetricValue>
            {mainHealth?.details?.successRate ? `${(mainHealth.details.successRate * 100).toFixed(1)}%` : '0%'}
          </MetricValue>
          <MetricLabel>成功率</MetricLabel>
        </MetricItem>
        
        <MetricItem>
          <MetricValue>
            {mainHealth?.responseTime ? `${mainHealth.responseTime.toFixed(0)}ms` : '0ms'}
          </MetricValue>
          <MetricLabel>平均響應</MetricLabel>
        </MetricItem>
      </MetricsGrid>
    </HealthCardContainer>
  );
};

// 導出類型
export type { HealthCardProps, HealthMetric };

export default HealthCard;