/**
 * 卡片組件 - VS Code 風格的資訊展示卡片
 * 用於顯示代理節點、ETL任務、系統監控等資訊
 */

import React from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, shadows, transitions } from '../../styles/GlobalStyles';

// 卡片容器
const CardContainer = styled.div<{ 
  theme: 'light' | 'dark';
  variant?: 'default' | 'elevated' | 'outlined';
  clickable?: boolean;
  status?: 'success' | 'warning' | 'error' | 'info';
}>`
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  border-radius: ${borderRadius.md};
  padding: ${spacing.lg};
  transition: all ${transitions.normal} ease;
  position: relative;
  overflow: hidden;
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    switch (props.variant) {
      case 'elevated':
        return `
          box-shadow: ${shadows.medium};
          border: 1px solid ${colors.border.secondary};
        `;
      case 'outlined':
        return `
          border: 1px solid ${colors.border.primary};
          box-shadow: none;
        `;
      default:
        return `
          border: 1px solid ${colors.border.secondary};
          box-shadow: ${shadows.small};
        `;
    }
  }}
  
  ${props => props.clickable && `
    cursor: pointer;
    
    &:hover {
      background-color: ${getThemeColors(props.theme).interactive.hover};
      box-shadow: ${shadows.large};
      transform: translateY(-1px);
    }
    
    &:active {
      transform: translateY(0);
      box-shadow: ${shadows.small};
    }
  `}
  
  ${props => props.status && `
    border-left: 4px solid ${getThemeColors(props.theme).status[props.status]};
  `}
`;

// 卡片標題
const CardHeader = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.md};
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: ${props => getThemeColors(props.theme).text.primary};
    line-height: 1.4;
  }
`;

// 卡片內容
const CardContent = styled.div<{ theme: 'light' | 'dark' }>`
  color: ${props => getThemeColors(props.theme).text.secondary};
  line-height: 1.6;
  
  p {
    margin: 0 0 ${spacing.sm} 0;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
`;

// 卡片底部操作區
const CardFooter = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: ${spacing.lg};
  padding-top: ${spacing.md};
  border-top: 1px solid ${props => getThemeColors(props.theme).border.secondary};
`;

// 狀態指示器
const StatusIndicator = styled.div<{ 
  theme: 'light' | 'dark';
  status: 'success' | 'warning' | 'error' | 'info' | 'inactive';
  size?: 'small' | 'medium' | 'large';
}>`
  display: inline-flex;
  align-items: center;
  gap: ${spacing.xs};
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '11px';
      case 'large': return '14px';
      default: return '12px';
    }
  }};
  font-weight: 500;
  
  &::before {
    content: '';
    width: ${props => {
      switch (props.size) {
        case 'small': return '6px';
        case 'large': return '10px';
        default: return '8px';
      }
    }};
    height: ${props => {
      switch (props.size) {
        case 'small': return '6px';
        case 'large': return '10px';
        default: return '8px';
      }
    }};
    border-radius: 50%;
    background-color: ${props => {
      const colors = getThemeColors(props.theme);
      switch (props.status) {
        case 'success': return colors.status.success;
        case 'warning': return colors.status.warning;
        case 'error': return colors.status.error;
        case 'info': return colors.status.info;
        default: return colors.text.disabled;
      }
    }};
  }
  
  color: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'success': return colors.status.success;
      case 'warning': return colors.status.warning;
      case 'error': return colors.status.error;
      case 'info': return colors.status.info;
      default: return colors.text.disabled;
    }
  }};
`;

// 卡片動作按鈕
const CardAction = styled.button<{ theme: 'light' | 'dark'; variant?: 'primary' | 'secondary' }>`
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: ${borderRadius.sm};
  font-size: 12px;
  font-weight: 500;
  transition: all ${transitions.fast} ease;
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    if (props.variant === 'primary') {
      return `
        background-color: ${colors.interactive.primary};
        color: ${colors.interactive.primaryForeground};
        
        &:hover {
          background-color: ${colors.interactive.primaryHover};
        }
      `;
    }
    
    return `
      background-color: transparent;
      color: ${colors.text.secondary};
      border: 1px solid ${colors.border.primary};
      
      &:hover {
        background-color: ${colors.interactive.hover};
        color: ${colors.text.primary};
      }
    `;
  }}
  
  &:focus {
    outline: 1px solid ${props => getThemeColors(props.theme).border.focus};
    outline-offset: 1px;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      background-color: transparent;
    }
  }
`;

// 卡片圖標
const CardIcon = styled.div<{ theme: 'light' | 'dark'; size?: 'small' | 'medium' | 'large' }>`
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${props => getThemeColors(props.theme).text.secondary};
  
  svg, i {
    width: ${props => {
      switch (props.size) {
        case 'small': return '16px';
        case 'large': return '32px';
        default: return '24px';
      }
    }};
    height: ${props => {
      switch (props.size) {
        case 'small': return '16px';
        case 'large': return '32px';
        default: return '24px';
      }
    }};
  }
`;

// 卡片統計數據
const CardStats = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  gap: ${spacing.lg};
  margin-top: ${spacing.md};
`;

const StatItem = styled.div<{ theme: 'light' | 'dark' }>`
  text-align: center;
  
  .stat-value {
    display: block;
    font-size: 20px;
    font-weight: 700;
    color: ${props => getThemeColors(props.theme).text.primary};
    line-height: 1.2;
  }
  
  .stat-label {
    display: block;
    font-size: 11px;
    color: ${props => getThemeColors(props.theme).text.secondary};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: ${spacing.xs};
  }
`;

// 卡片組件介面
export interface CardProps {
  theme: 'light' | 'dark';
  title?: string;
  variant?: 'default' | 'elevated' | 'outlined';
  status?: 'success' | 'warning' | 'error' | 'info';
  clickable?: boolean;
  icon?: React.ReactNode;
  headerActions?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
}

/**
 * 卡片組件
 * 提供統一的資訊展示容器
 */
export const Card: React.FC<CardProps> = ({
  theme,
  title,
  variant = 'default',
  status,
  clickable = false,
  icon,
  headerActions,
  footer,
  className,
  children,
  onClick
}) => {
  return (
    <CardContainer
      theme={theme}
      variant={variant}
      status={status}
      clickable={clickable}
      className={className}
      onClick={clickable ? onClick : undefined}
    >
      {(title || icon || headerActions) && (
        <CardHeader theme={theme}>
          <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
            {icon && (
              <CardIcon theme={theme} size="medium">
                {icon}
              </CardIcon>
            )}
            {title && <h3>{title}</h3>}
          </div>
          {headerActions && (
            <div>{headerActions}</div>
          )}
        </CardHeader>
      )}
      
      <CardContent theme={theme}>
        {children}
      </CardContent>
      
      {footer && (
        <CardFooter theme={theme}>
          {footer}
        </CardFooter>
      )}
    </CardContainer>
  );
};

// 導出相關組件
export { StatusIndicator, CardAction, CardIcon, CardStats, StatItem };
export default Card;