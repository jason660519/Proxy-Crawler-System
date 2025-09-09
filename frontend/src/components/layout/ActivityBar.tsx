/**
 * Activity Bar 組件
 * 左側活動欄，提供主要導航功能
 */

import React, { useState, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled, { css } from 'styled-components';
import { useHealthStatus, useTaskQueue } from '../../hooks';
import { spacing, borderRadius, zIndex } from '../../styles';
import type { SystemMetrics, HealthStatus } from '../../types';
import { TaskStatus } from '../../types';
import { ROUTE_ITEMS } from '../../router';

// ============= 類型定義 =============

export interface ActivityBarProps {
  /** 是否摺疊 */
  collapsed?: boolean;
  /** 系統指標 */
  systemMetrics?: SystemMetrics;
  /** 主要健康狀態 */
  mainHealth?: HealthStatus;
}

interface ActivityItem {
  id: string;
  icon: React.ReactNode;
  label: string;
  badge?: number | string;
  badgeType?: 'info' | 'warning' | 'error' | 'success';
  disabled?: boolean;
}

// ============= 樣式定義 =============

const ActivityBarContainer = styled.div<{ collapsed: boolean }>`
  display: flex;
  flex-direction: column;
  width: ${props => props.collapsed ? '60px' : '240px'};
  height: 100%;
  background-color: var(--color-background-secondary);
  border-right: 1px solid var(--color-border-primary);
  transition: width 0.3s ease;
  position: relative;
  z-index: ${zIndex.sidebar};
`;

const ActivityList = styled.div`
  display: flex;
  flex-direction: column;
  padding: ${spacing[2]} 0;
  flex: 1;
  overflow-y: auto;
`;

const ActivityItemContainer = styled(Link)<{ 
  $active: boolean; 
  $collapsed: boolean;
  $disabled?: boolean;
}>`
  display: flex;
  align-items: center;
  gap: ${spacing[3]};
  padding: ${spacing[3]} ${spacing[4]};
  margin: ${spacing[1]} ${spacing[2]};
  border: none;
  background-color: transparent;
  border-radius: ${borderRadius.md};
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--color-text-secondary);
  text-align: left;
  position: relative;
  min-height: 44px;
  
  ${props => props.$collapsed && css`
    justify-content: center;
    padding: ${spacing[3]};
  `}
  
  ${props => props.$active && css`
    background-color: var(--color-interactive-primary);
    color: var(--color-text-inverse);
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 20px;
      background-color: var(--color-text-inverse);
      border-radius: 0 2px 2px 0;
    }
  `}
  
  ${props => !props.$active && css`
    &:hover {
      background-color: var(--color-background-tertiary);
      color: var(--color-text-primary);
    }
  `}
  
  ${props => props.$disabled && css`
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      background-color: transparent;
      color: var(--color-text-secondary);
    }
  `}
`;

const ActivityIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  position: relative;
`;

const ActivityLabel = styled.span<{ $collapsed: boolean }>`
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  
  ${props => props.$collapsed && css`
    display: none;
  `}
`;

const ActivityBadge = styled.div<{ 
  $type: 'info' | 'warning' | 'error' | 'success';
  $collapsed: boolean;
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 ${spacing[1]};
  border-radius: ${borderRadius.full};
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1;
  margin-left: auto;
  
  ${props => {
    switch (props.$type) {
      case 'error':
        return css`
          background-color: var(--color-status-error);
          color: white;
        `;
      case 'warning':
        return css`
          background-color: var(--color-status-warning);
          color: white;
        `;
      case 'success':
        return css`
          background-color: var(--color-status-success);
          color: white;
        `;
      case 'info':
      default:
        return css`
          background-color: var(--color-interactive-primary);
          color: white;
        `;
    }
  }}
  
  ${props => props.$collapsed && css`
    position: absolute;
    top: -2px;
    right: -2px;
    min-width: 16px;
    height: 16px;
    font-size: 0.625rem;
  `}
`;

const ConnectionStatus = styled.div<{ $collapsed: boolean }>`
  display: flex;
  align-items: center;
  gap: ${spacing[2]};
  padding: ${spacing[3]} ${spacing[4]};
  margin: ${spacing[2]};
  border-top: 1px solid var(--color-border-primary);
  
  ${props => props.$collapsed && css`
    justify-content: center;
    padding: ${spacing[3]};
  `}
`;

const StatusIndicator = styled.div<{ status: 'connected' | 'disconnected' | 'connecting' }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  
  ${props => {
    switch (props.status) {
      case 'connected':
        return css`
          background-color: var(--color-status-success);
        `;
      case 'disconnected':
        return css`
          background-color: var(--color-status-error);
        `;
      case 'connecting':
        return css`
          background-color: var(--color-status-warning);
          animation: pulse 2s infinite;
          
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `;
      default:
        return css`
          background-color: var(--color-text-tertiary);
        `;
    }
  }}
`;

const StatusText = styled.span<{ $collapsed: boolean }>`
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  
  ${props => props.$collapsed && css`
    display: none;
  `}
`;

const CollapseButton = styled.button`
  position: absolute;
  top: ${spacing[4]};
  right: -12px;
  width: 24px;
  height: 24px;
  border: 1px solid var(--color-border-primary);
  background-color: var(--color-background-primary);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
  z-index: 1;
  
  &:hover {
    background-color: var(--color-background-secondary);
    color: var(--color-text-primary);
  }
`;

// ============= 組件實作 =============

export const ActivityBar: React.FC<ActivityBarProps> = ({
  collapsed: controlledCollapsed,
  systemMetrics,
  mainHealth: propMainHealth,
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const collapsed = controlledCollapsed ?? internalCollapsed;
  const location = useLocation();
  
  const { mainHealth: hookMainHealth, etlHealth } = useHealthStatus();
  const mainHealth = propMainHealth || hookMainHealth;
  const { tasks } = useTaskQueue();
  
  // 計算任務統計
  const runningTasks = tasks.filter(task => task.status === TaskStatus.RUNNING).length;
  const failedTasks = tasks.filter(task => task.status === TaskStatus.FAILED).length;
  
  // 計算連線狀態
  const connectionStatus = (() => {
    if (mainHealth?.status === 'healthy' && etlHealth?.status === 'healthy') {
      return 'connected';
    } else if (mainHealth?.status === 'unhealthy' || etlHealth?.status === 'unhealthy') {
      return 'disconnected';
    } else {
      return 'connecting';
    }
  })();
  
  // 使用路由配置中的項目，並添加動態徽章
  const activityItems = ROUTE_ITEMS.map(item => {
    let badge: number | string | undefined;
    let badgeType: 'info' | 'warning' | 'error' | 'success' = 'info';
    
    // 根據項目 ID 添加動態徽章
    switch (item.id) {
      case 'proxies':
        badge = systemMetrics?.totalProxies || 0;
        badgeType = 'info';
        break;
      case 'tasks':
        badge = runningTasks > 0 ? runningTasks : undefined;
        badgeType = failedTasks > 0 ? 'error' : 'success';
        break;
      default:
        badge = undefined;
    }
    
    return {
      ...item,
      badge,
      badgeType
    };
  });
  
  // 判斷當前活動項目
  const getActiveItem = useCallback(() => {
    const currentPath = location.pathname;
    const activeItem = ROUTE_ITEMS.find(item => item.path === currentPath);
    return activeItem?.id || 'dashboard';
  }, [location.pathname]);
  
  const handleCollapseToggle = useCallback(() => {
    if (controlledCollapsed === undefined) {
      setInternalCollapsed(!collapsed);
    }
  }, [collapsed, controlledCollapsed]);
  
  return (
    <ActivityBarContainer collapsed={collapsed}>
      <CollapseButton onClick={handleCollapseToggle}>
        <svg 
          width="12" 
          height="12" 
          viewBox="0 0 24 24" 
          fill="currentColor"
          style={{ transform: collapsed ? 'rotate(180deg)' : 'none' }}
        >
          <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
        </svg>
      </CollapseButton>
      
      <ActivityList>
        {activityItems.map((item) => (
          <ActivityItemContainer
            key={item.id}
            to={item.path}
            $active={getActiveItem() === item.id}
            $collapsed={collapsed}
            title={collapsed ? item.label : undefined}
          >
            <ActivityIcon>
              {item.icon}
              {item.badge && (
                <ActivityBadge $type={item.badgeType || 'info'} $collapsed={collapsed}>
                  {item.badge}
                </ActivityBadge>
              )}
            </ActivityIcon>
            <ActivityLabel $collapsed={collapsed}>
              {item.label}
            </ActivityLabel>
          </ActivityItemContainer>
        ))}
      </ActivityList>
      
      <ConnectionStatus $collapsed={collapsed}>
        <StatusIndicator status={connectionStatus} />
        <StatusText $collapsed={collapsed}>
          {connectionStatus === 'connected' && '已連線'}
          {connectionStatus === 'disconnected' && '連線中斷'}
          {connectionStatus === 'connecting' && '連線中...'}
        </StatusText>
      </ConnectionStatus>
    </ActivityBarContainer>
  );
};

export default ActivityBar;