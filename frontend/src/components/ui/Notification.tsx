/**
 * 通知組件 - VS Code 風格的通知系統
 * 提供多種類型的通知消息和自動消失功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import styled, { keyframes } from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 通知動畫
const slideInRight = keyframes`
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`;

const slideOutRight = keyframes`
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
`;

const slideInTop = keyframes`
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
`;

const slideOutTop = keyframes`
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(-100%);
    opacity: 0;
  }
`;

// 通知容器
const NotificationContainer = styled.div<{
  placement: 'topRight' | 'topLeft' | 'bottomRight' | 'bottomLeft' | 'top' | 'bottom';
}>`
  position: fixed;
  z-index: 10000;
  pointer-events: none;
  
  ${props => {
    switch (props.placement) {
      case 'topRight':
        return `
          top: ${spacing.lg};
          right: ${spacing.lg};
        `;
      case 'topLeft':
        return `
          top: ${spacing.lg};
          left: ${spacing.lg};
        `;
      case 'bottomRight':
        return `
          bottom: ${spacing.lg};
          right: ${spacing.lg};
        `;
      case 'bottomLeft':
        return `
          bottom: ${spacing.lg};
          left: ${spacing.lg};
        `;
      case 'top':
        return `
          top: ${spacing.lg};
          left: 50%;
          transform: translateX(-50%);
        `;
      case 'bottom':
        return `
          bottom: ${spacing.lg};
          left: 50%;
          transform: translateX(-50%);
        `;
      default:
        return `
          top: ${spacing.lg};
          right: ${spacing.lg};
        `;
    }
  }}
`;

// 通知項目
const NotificationItem = styled.div<{
  theme: 'light' | 'dark';
  type: 'info' | 'success' | 'warning' | 'error';
  placement: 'topRight' | 'topLeft' | 'bottomRight' | 'bottomLeft' | 'top' | 'bottom';
  closing?: boolean;
}>`
  display: flex;
  align-items: flex-start;
  gap: ${spacing.sm};
  min-width: 320px;
  max-width: 480px;
  margin-bottom: ${spacing.sm};
  padding: ${spacing.md};
  background-color: ${props => getThemeColors(props.theme).background.primary};
  border: 1px solid ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.type) {
      case 'success': return colors.status.success;
      case 'warning': return colors.status.warning;
      case 'error': return colors.status.error;
      default: return colors.accent.primary;
    }
  }};
  border-left: 4px solid ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.type) {
      case 'success': return colors.status.success;
      case 'warning': return colors.status.warning;
      case 'error': return colors.status.error;
      default: return colors.accent.primary;
    }
  }};
  border-radius: ${borderRadius.md};
  box-shadow: 0 4px 12px ${props => getThemeColors(props.theme).shadow.notification};
  pointer-events: auto;
  
  animation: ${props => {
    const isVertical = props.placement === 'top' || props.placement === 'bottom';
    if (props.closing) {
      return isVertical ? slideOutTop : slideOutRight;
    }
    return isVertical ? slideInTop : slideInRight;
  }} ${transitions.normal} ease;
`;

// 通知圖標
const NotificationIcon = styled.div<{
  theme: 'light' | 'dark';
  type: 'info' | 'success' | 'warning' | 'error';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  margin-top: 2px;
  
  color: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.type) {
      case 'success': return colors.status.success;
      case 'warning': return colors.status.warning;
      case 'error': return colors.status.error;
      default: return colors.accent.primary;
    }
  }};
  
  font-size: 16px;
  font-weight: 600;
`;

// 通知內容
const NotificationContent = styled.div`
  flex: 1;
  min-width: 0;
`;

// 通知標題
const NotificationTitle = styled.div<{ theme: 'light' | 'dark' }>`
  font-size: 14px;
  font-weight: 600;
  color: ${props => getThemeColors(props.theme).text.primary};
  margin-bottom: ${spacing.xs};
  line-height: 1.4;
`;

// 通知描述
const NotificationDescription = styled.div<{ theme: 'light' | 'dark' }>`
  font-size: 13px;
  color: ${props => getThemeColors(props.theme).text.secondary};
  line-height: 1.5;
  word-wrap: break-word;
`;

// 通知操作
const NotificationActions = styled.div`
  display: flex;
  gap: ${spacing.sm};
  margin-top: ${spacing.sm};
`;

// 通知按鈕
const NotificationButton = styled.button<{
  theme: 'light' | 'dark';
  variant: 'primary' | 'secondary';
}>`
  padding: ${spacing.xs} ${spacing.sm};
  border: none;
  border-radius: ${borderRadius.sm};
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all ${transitions.fast} ease;
  
  ${props => {
    const colors = getThemeColors(props.theme);
    if (props.variant === 'primary') {
      return `
        background-color: ${colors.accent.primary};
        color: ${colors.accent.foreground};
        
        &:hover {
          background-color: ${colors.accent.hover};
        }
      `;
    }
    return `
      background-color: transparent;
      color: ${colors.text.secondary};
      border: 1px solid ${colors.border.primary};
      
      &:hover {
        background-color: ${colors.background.hover};
        color: ${colors.text.primary};
      }
    `;
  }}
  
  &:focus-visible {
    outline: 2px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: 1px;
  }
`;

// 關閉按鈕
const CloseButton = styled.button<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: none;
  color: ${props => getThemeColors(props.theme).text.secondary};
  cursor: pointer;
  border-radius: ${borderRadius.xs};
  transition: all ${transitions.fast} ease;
  flex-shrink: 0;
  margin-top: 2px;
  
  &:hover {
    background-color: ${props => getThemeColors(props.theme).background.hover};
    color: ${props => getThemeColors(props.theme).text.primary};
  }
  
  &:focus-visible {
    outline: 1px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: 1px;
  }
`;

// 進度條
const ProgressBar = styled.div<{
  theme: 'light' | 'dark';
  duration: number;
  paused?: boolean;
}>`
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background-color: ${props => getThemeColors(props.theme).accent.primary};
  border-radius: 0 0 ${borderRadius.md} ${borderRadius.md};
  
  animation: ${props => `progressAnimation ${props.duration}ms linear`};
  animation-play-state: ${props => props.paused ? 'paused' : 'running'};
  
  @keyframes progressAnimation {
    from {
      width: 100%;
    }
    to {
      width: 0%;
    }
  }
`;

// 通知項目介面
export interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: React.ReactNode;
  description?: React.ReactNode;
  duration?: number;
  closable?: boolean;
  showProgress?: boolean;
  actions?: Array<{
    label: React.ReactNode;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  }>;
  onClose?: () => void;
}

// 通知組件介面
export interface NotificationProps {
  theme: 'light' | 'dark';
  item: NotificationItem;
  placement?: 'topRight' | 'topLeft' | 'bottomRight' | 'bottomLeft' | 'top' | 'bottom';
  onClose: (id: string) => void;
}

/**
 * 單個通知組件
 */
export const Notification: React.FC<NotificationProps> = ({
  theme,
  item,
  placement = 'topRight',
  onClose
}) => {
  const [closing, setClosing] = useState(false);
  const [paused, setPaused] = useState(false);
  
  // 獲取圖標
  const getIcon = () => {
    switch (item.type) {
      case 'success': return '✓';
      case 'warning': return '⚠';
      case 'error': return '✕';
      default: return 'ℹ';
    }
  };
  
  // 處理關閉
  const handleClose = useCallback(() => {
    setClosing(true);
    setTimeout(() => {
      onClose(item.id);
      item.onClose?.();
    }, 300); // 動畫持續時間
  }, [item.id, item.onClose, onClose]);
  
  // 自動關閉
  useEffect(() => {
    if (item.duration && item.duration > 0 && !paused) {
      const timer = setTimeout(handleClose, item.duration);
      return () => clearTimeout(timer);
    }
  }, [item.duration, paused, handleClose]);
  
  return (
    <NotificationItem
      theme={theme}
      type={item.type}
      placement={placement}
      closing={closing}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <NotificationIcon theme={theme} type={item.type}>
        {getIcon()}
      </NotificationIcon>
      
      <NotificationContent>
        <NotificationTitle theme={theme}>
          {item.title}
        </NotificationTitle>
        
        {item.description && (
          <NotificationDescription theme={theme}>
            {item.description}
          </NotificationDescription>
        )}
        
        {item.actions && item.actions.length > 0 && (
          <NotificationActions>
            {item.actions.map((action, index) => (
              <NotificationButton
                key={index}
                theme={theme}
                variant={action.variant || 'secondary'}
                onClick={action.onClick}
              >
                {action.label}
              </NotificationButton>
            ))}
          </NotificationActions>
        )}
      </NotificationContent>
      
      {item.closable !== false && (
        <CloseButton theme={theme} onClick={handleClose}>
          ×
        </CloseButton>
      )}
      
      {item.showProgress && item.duration && item.duration > 0 && (
        <ProgressBar
          theme={theme}
          duration={item.duration}
          paused={paused}
        />
      )}
    </NotificationItem>
  );
};

// 通知管理器介面
export interface NotificationManagerProps {
  theme: 'light' | 'dark';
  notifications: NotificationItem[];
  placement?: 'topRight' | 'topLeft' | 'bottomRight' | 'bottomLeft' | 'top' | 'bottom';
  maxCount?: number;
  onClose: (id: string) => void;
}

/**
 * 通知管理器組件
 */
export const NotificationManager: React.FC<NotificationManagerProps> = ({
  theme,
  notifications,
  placement = 'topRight',
  maxCount = 5,
  onClose
}) => {
  // 限制顯示數量
  const visibleNotifications = notifications.slice(0, maxCount);
  
  if (visibleNotifications.length === 0) {
    return null;
  }
  
  return createPortal(
    <NotificationContainer placement={placement}>
      {visibleNotifications.map(notification => (
        <Notification
          key={notification.id}
          theme={theme}
          item={notification}
          placement={placement}
          onClose={onClose}
        />
      ))}
    </NotificationContainer>,
    document.body
  );
};

// 通知 Hook
export const useNotification = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  
  const addNotification = useCallback((notification: Omit<NotificationItem, 'id'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: NotificationItem = {
      ...notification,
      id,
      duration: notification.duration ?? 4000,
      closable: notification.closable ?? true,
      showProgress: notification.showProgress ?? false
    };
    
    setNotifications(prev => [newNotification, ...prev]);
    return id;
  }, []);
  
  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);
  
  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);
  
  // 便捷方法
  const info = useCallback((title: React.ReactNode, description?: React.ReactNode, options?: Partial<NotificationItem>) => {
    return addNotification({ ...options, type: 'info', title, description });
  }, [addNotification]);
  
  const success = useCallback((title: React.ReactNode, description?: React.ReactNode, options?: Partial<NotificationItem>) => {
    return addNotification({ ...options, type: 'success', title, description });
  }, [addNotification]);
  
  const warning = useCallback((title: React.ReactNode, description?: React.ReactNode, options?: Partial<NotificationItem>) => {
    return addNotification({ ...options, type: 'warning', title, description });
  }, [addNotification]);
  
  const error = useCallback((title: React.ReactNode, description?: React.ReactNode, options?: Partial<NotificationItem>) => {
    return addNotification({ ...options, type: 'error', title, description });
  }, [addNotification]);
  
  return {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    info,
    success,
    warning,
    error
  };
};

export default Notification;