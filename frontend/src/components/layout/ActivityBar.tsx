/**
 * Activity Bar 組件
 * 左側活動欄，提供主要導航功能
 */

import React, { useState, useCallback } from 'react';
import styled, { css } from 'styled-components';
import { useHealthStatus, useTaskQueue } from '../../hooks';
import { spacing, borderRadius, zIndex } from '../../styles';
import type { SystemMetrics, HealthStatus } from '../../types';
import { TaskStatus } from '../../types';

// ============= 類型定義 =============

export interface ActivityBarProps {
  /** 當前活動項目 */
  activeItem?: string;
  /** 活動項目變更回調 */
  onItemChange?: (itemId: string) => void;
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

const ActivityItemContainer = styled.button<{ 
  active: boolean; 
  collapsed: boolean;
  disabled?: boolean;
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
  
  ${props => props.collapsed && css`
    justify-content: center;
    padding: ${spacing[3]};
  `}
  
  ${props => props.active && css`
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
  
  ${props => !props.active && css`
    &:hover {
      background-color: var(--color-background-tertiary);
      color: var(--color-text-primary);
    }
  `}
  
  ${props => props.disabled && css`
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

const ActivityLabel = styled.span<{ collapsed: boolean }>`
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  
  ${props => props.collapsed && css`
    display: none;
  `}
`;

const ActivityBadge = styled.div<{ 
  type: 'info' | 'warning' | 'error' | 'success';
  collapsed: boolean;
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
    switch (props.type) {
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
  
  ${props => props.collapsed && css`
    position: absolute;
    top: -2px;
    right: -2px;
    min-width: 16px;
    height: 16px;
    font-size: 0.625rem;
  `}
`;

const ConnectionStatus = styled.div<{ collapsed: boolean }>`
  display: flex;
  align-items: center;
  gap: ${spacing[2]};
  padding: ${spacing[3]} ${spacing[4]};
  margin: ${spacing[2]};
  border-top: 1px solid var(--color-border-primary);
  
  ${props => props.collapsed && css`
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

const StatusText = styled.span<{ collapsed: boolean }>`
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  
  ${props => props.collapsed && css`
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
  activeItem = 'dashboard',
  onItemChange,
  collapsed: controlledCollapsed,
  systemMetrics,
  mainHealth: propMainHealth,
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const collapsed = controlledCollapsed ?? internalCollapsed;
  
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
  
  const activityItems: ActivityItem[] = [
    {
      id: 'dashboard',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
        </svg>
      ),
      label: '儀表板',
    },
    {
      id: 'proxies',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
        </svg>
      ),
      label: '代理管理',
      badge: systemMetrics?.totalProxies || 0,
      badgeType: 'info',
    },
    {
      id: 'tasks',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
        </svg>
      ),
      label: '任務佇列',
      badge: runningTasks > 0 ? runningTasks : undefined,
      badgeType: failedTasks > 0 ? 'error' : 'success',
    },
    {
      id: 'logs',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 2 2h8c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
        </svg>
      ),
      label: '系統日誌',
    },
    {
      id: 'analytics',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" />
        </svg>
      ),
      label: '數據分析',
    },
    {
      id: 'settings',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z" />
        </svg>
      ),
      label: '系統設定',
    },
  ];
  
  const handleItemClick = useCallback((itemId: string) => {
    onItemChange?.(itemId);
  }, [onItemChange]);
  
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
            active={activeItem === item.id}
            collapsed={collapsed}
            disabled={item.disabled}
            onClick={() => !item.disabled && handleItemClick(item.id)}
            title={collapsed ? item.label : undefined}
          >
            <ActivityIcon>
              {item.icon}
              {item.badge && (
                <ActivityBadge type={item.badgeType || 'info'} collapsed={collapsed}>
                  {item.badge}
                </ActivityBadge>
              )}
            </ActivityIcon>
            <ActivityLabel collapsed={collapsed}>
              {item.label}
            </ActivityLabel>
          </ActivityItemContainer>
        ))}
      </ActivityList>
      
      <ConnectionStatus collapsed={collapsed}>
        <StatusIndicator status={connectionStatus} />
        <StatusText collapsed={collapsed}>
          {connectionStatus === 'connected' && '已連線'}
          {connectionStatus === 'disconnected' && '連線中斷'}
          {connectionStatus === 'connecting' && '連線中...'}
        </StatusText>
      </ConnectionStatus>
    </ActivityBarContainer>
  );
};

export default ActivityBar;