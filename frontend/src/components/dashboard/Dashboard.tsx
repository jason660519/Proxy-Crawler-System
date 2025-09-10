/**
 * 主要儀表板組件
 * 整合健康狀態、趨勢圖、任務佇列和即時日誌等功能
 */

import React, { useState } from 'react';
import styled from 'styled-components';
import HealthCard from './HealthCard';
import TrendChart from './TrendChart';
import TaskBoard from './TaskBoard';
import LogViewer from './LogViewer';
import { spacing } from '../../styles';
// ============= 類型定義 =============

interface DashboardProps {
  className?: string;
}

interface GridItemProps {
  gridArea: string;
  minHeight?: string;
}

// ============= 樣式定義 =============

const DashboardContainer = styled.div`
  padding: ${spacing[6]};
  background: var(--color-background-primary);
  min-height: 100vh;
  overflow-y: auto;
`;

const DashboardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[8]};
`;

const Title = styled.h1`
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-400));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const Subtitle = styled.p`
  margin: ${spacing[1]} 0 0 0;
  font-size: 1rem;
  color: var(--color-text-secondary);
`;

const HeaderActions = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[4]};
`;

const RefreshButton = styled.button`
  display: flex;
  align-items: center;
  gap: ${spacing[1]};
  padding: ${spacing[2]} ${spacing[4]};
  background: var(--color-primary-500);
  color: var(--color-white);
  border: none;
  border-radius: var(--border-radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: var(--color-primary-600);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    background: var(--color-neutral-400);
    cursor: not-allowed;
    transform: none;
  }
`;



const DashboardGrid = styled.div`
  display: grid;
  gap: ${spacing[6]};
  grid-template-columns: 1fr 1fr;
  grid-template-areas:
    "health trends"
    "tasks logs";
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
    grid-template-areas:
      "health"
      "trends"
      "tasks"
      "logs";
  }
`;

const GridItem = styled.div<GridItemProps>`
  grid-area: ${({ gridArea }) => gridArea};
  min-height: ${({ minHeight }) => minHeight || 'auto'};
  display: flex;
  flex-direction: column;
`;

const StatsOverview = styled.div`
  display: flex;
  gap: ${spacing[4]};
  margin-bottom: ${spacing[6]};
  
  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const StatCard = styled.div`
  flex: 1;
  padding: ${spacing[4]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  border-radius: var(--border-radius-lg);
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-primary-600);
  margin-bottom: ${spacing[1]};
`;

const StatLabel = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const LoadingOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-background-primary-80);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
`;

const LoadingSpinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-neutral-300);
  border-top: 3px solid var(--color-primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// ============= 組件實作 =============

/**
 * 主要儀表板組件
 */
export const Dashboard: React.FC<DashboardProps> = ({ 
  className
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // 重新整理所有資料
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // 這裡應該調用各個組件的重新整理方法
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模擬 API 調用
      setLastRefresh(new Date());
    } catch (error) {
      console.error('重新整理失敗:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // 格式化最後更新時間
  const formatLastRefresh = (date: Date) => {
    return date.toLocaleTimeString('zh-TW', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <DashboardContainer className={className}>
      {isRefreshing && (
        <LoadingOverlay>
          <LoadingSpinner />
        </LoadingOverlay>
      )}
      
      <DashboardHeader>
        <div>
          <Title>Proxy 管理儀表板</Title>
          <Subtitle>即時監控系統狀態與代理節點效能</Subtitle>
        </div>
        
        <HeaderActions>
          <RefreshButton
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <>
                <LoadingSpinner style={{ width: '16px', height: '16px', border: '2px solid currentColor', borderTop: '2px solid transparent' }} />
                重新整理中...
              </>
            ) : (
              <>
                🔄 重新整理
              </>
            )}
          </RefreshButton>
        </HeaderActions>
      </DashboardHeader>

      <StatsOverview>
        <StatCard>
          <StatValue>156</StatValue>
          <StatLabel>活躍代理</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>98.5%</StatValue>
          <StatLabel>成功率</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>245ms</StatValue>
          <StatLabel>平均響應時間</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>12</StatValue>
          <StatLabel>待處理任務</StatLabel>
        </StatCard>
      </StatsOverview>

      <DashboardGrid>
        <GridItem gridArea="health" minHeight="300px">
          <HealthCard />
        </GridItem>
        
        <GridItem gridArea="trends" minHeight="400px">
          <TrendChart />
        </GridItem>
        
        <GridItem gridArea="tasks" minHeight="500px">
          <TaskBoard />
        </GridItem>
        
        <GridItem gridArea="logs" minHeight="400px">
          <LogViewer maxItems={50} autoScroll={true} />
        </GridItem>
      </DashboardGrid>
      
      <div style={{ 
        marginTop: spacing[8], 
        textAlign: 'center', 
        color: 'var(--color-text-secondary)',
        fontSize: '0.875rem'
      }}>
        最後更新: {formatLastRefresh(lastRefresh)}
      </div>
    </DashboardContainer>
  );
};

export default Dashboard;