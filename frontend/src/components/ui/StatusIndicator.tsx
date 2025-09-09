/**
 * StatusIndicator 組件
 * 統一的狀態指示器組件，用於顯示各種狀態信息
 */

import React from 'react';
import styled from 'styled-components';
import { spacing, borderRadius } from '../../styles';
import type { BaseComponentProps } from '../../types';

// ============= 類型定義 =============

export type StatusType = 
  | 'success' 
  | 'warning' 
  | 'error' 
  | 'info' 
  | 'pending' 
  | 'disabled'
  | 'active'
  | 'inactive';

export type StatusSize = 'small' | 'medium' | 'large';

export type StatusVariant = 'dot' | 'badge' | 'pill' | 'outline';

export interface StatusIndicatorProps extends BaseComponentProps {
  /** 狀態類型 */
  status: StatusType;
  /** 狀態文字 */
  text?: string;
  /** 組件大小 */
  size?: StatusSize;
  /** 顯示變體 */
  variant?: StatusVariant;
  /** 是否顯示動畫 */
  animated?: boolean;
  /** 自訂顏色 */
  color?: string;
  /** 點擊事件 */
  onClick?: () => void;
  /** 工具提示 */
  tooltip?: string;
}

// ============= 狀態配置 =============

const statusConfig = {
  success: {
    color: 'var(--color-status-success)',
    backgroundColor: 'var(--color-status-success-background)',
    borderColor: 'var(--color-status-success)',
    label: '成功'
  },
  warning: {
    color: 'var(--color-status-warning)',
    backgroundColor: 'var(--color-status-warning-background)',
    borderColor: 'var(--color-status-warning)',
    label: '警告'
  },
  error: {
    color: 'var(--color-status-error)',
    backgroundColor: 'var(--color-status-error-background)',
    borderColor: 'var(--color-status-error)',
    label: '錯誤'
  },
  info: {
    color: 'var(--color-status-info)',
    backgroundColor: 'var(--color-status-info-background)',
    borderColor: 'var(--color-status-info)',
    label: '信息'
  },
  pending: {
    color: 'var(--color-text-secondary)',
    backgroundColor: 'var(--color-background-secondary)',
    borderColor: 'var(--color-border-primary)',
    label: '等待中'
  },
  disabled: {
    color: 'var(--color-text-disabled)',
    backgroundColor: 'var(--color-background-disabled)',
    borderColor: 'var(--color-border-disabled)',
    label: '已禁用'
  },
  active: {
    color: 'var(--color-interactive-primary)',
    backgroundColor: 'var(--color-interactive-primary-background)',
    borderColor: 'var(--color-interactive-primary)',
    label: '活躍'
  },
  inactive: {
    color: 'var(--color-text-tertiary)',
    backgroundColor: 'var(--color-background-tertiary)',
    borderColor: 'var(--color-border-secondary)',
    label: '非活躍'
  }
};

const sizeConfig = {
  small: {
    dotSize: '6px',
    fontSize: '0.75rem',
    padding: `${spacing[1]} ${spacing[2]}`,
    height: '20px'
  },
  medium: {
    dotSize: '8px',
    fontSize: '0.8125rem',
    padding: `${spacing[2]} ${spacing[3]}`,
    height: '24px'
  },
  large: {
    dotSize: '10px',
    fontSize: '0.875rem',
    padding: `${spacing[2]} ${spacing[4]}`,
    height: '28px'
  }
};

// ============= 樣式定義 =============

const StatusContainer = styled.div<{
  variant: StatusVariant;
  size: StatusSize;
  clickable: boolean;
  status: StatusType;
  customColor?: string;
}>`
  display: inline-flex;
  align-items: center;
  gap: ${spacing[2]};
  font-size: ${props => sizeConfig[props.size].fontSize};
  font-weight: 500;
  line-height: 1;
  
  ${props => props.clickable && `
    cursor: pointer;
    transition: opacity 0.2s ease;
    
    &:hover {
      opacity: 0.8;
    }
  `}
  
  ${props => {
    const config = statusConfig[props.status];
    const customColor = props.customColor;
    
    switch (props.variant) {
      case 'badge':
        return `
          background-color: ${customColor || config.backgroundColor};
          color: ${customColor || config.color};
          padding: ${sizeConfig[props.size].padding};
          border-radius: ${borderRadius.md};
          border: 1px solid ${customColor || config.borderColor};
        `;
      case 'pill':
        return `
          background-color: ${customColor || config.backgroundColor};
          color: ${customColor || config.color};
          padding: ${sizeConfig[props.size].padding};
          border-radius: ${sizeConfig[props.size].height};
          border: 1px solid ${customColor || config.borderColor};
        `;
      case 'outline':
        return `
          background-color: transparent;
          color: ${customColor || config.color};
          padding: ${sizeConfig[props.size].padding};
          border-radius: ${borderRadius.md};
          border: 1px solid ${customColor || config.borderColor};
        `;
      default: // dot
        return `
          color: var(--color-text-primary);
        `;
    }
  }}
`;

const StatusDot = styled.div<{
  status: StatusType;
  size: StatusSize;
  animated: boolean;
  customColor?: string;
}>`
  width: ${props => sizeConfig[props.size].dotSize};
  height: ${props => sizeConfig[props.size].dotSize};
  border-radius: 50%;
  background-color: ${props => props.customColor || statusConfig[props.status].color};
  flex-shrink: 0;
  
  ${props => props.animated && `
    animation: pulse 2s infinite;
    
    @keyframes pulse {
      0% {
        opacity: 1;
        transform: scale(1);
      }
      50% {
        opacity: 0.7;
        transform: scale(1.1);
      }
      100% {
        opacity: 1;
        transform: scale(1);
      }
    }
  `}
`;

const StatusText = styled.span`
  white-space: nowrap;
`;

const TooltipContainer = styled.div`
  position: relative;
  display: inline-flex;
  
  &:hover .tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateY(-2px);
  }
`;

const Tooltip = styled.div`
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-4px);
  background-color: var(--color-background-tooltip);
  color: var(--color-text-tooltip);
  padding: ${spacing[2]} ${spacing[3]};
  border-radius: ${borderRadius.sm};
  font-size: 0.75rem;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  
  &::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: var(--color-background-tooltip);
  }
`;

// ============= 組件實現 =============

/**
 * StatusIndicator 組件
 * 提供統一的狀態指示功能，支援多種顯示樣式和動畫效果
 * 
 * @param props - StatusIndicator 屬性
 * @returns React 組件
 */
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  text,
  size = 'medium',
  variant = 'dot',
  animated = false,
  color,
  onClick,
  tooltip,
  className,
  ...rest
}) => {
  const config = statusConfig[status];
  const displayText = text || config.label;
  
  const statusElement = (
    <StatusContainer
      variant={variant}
      size={size}
      clickable={!!onClick}
      status={status}
      customColor={color}
      onClick={onClick}
      className={className}
      {...rest}
    >
      {variant === 'dot' && (
        <StatusDot
          status={status}
          size={size}
          animated={animated}
          customColor={color}
        />
      )}
      {displayText && (
        <StatusText>
          {displayText}
        </StatusText>
      )}
    </StatusContainer>
  );
  
  if (tooltip) {
    return (
      <TooltipContainer>
        {statusElement}
        <Tooltip className="tooltip">
          {tooltip}
        </Tooltip>
      </TooltipContainer>
    );
  }
  
  return statusElement;
};

// ============= 預設狀態組件 =============

/**
 * 成功狀態指示器
 */
export const SuccessStatus: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="success" {...props} />
);

/**
 * 警告狀態指示器
 */
export const WarningStatus: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="warning" {...props} />
);

/**
 * 錯誤狀態指示器
 */
export const ErrorStatus: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="error" {...props} />
);

/**
 * 信息狀態指示器
 */
export const InfoStatus: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="info" {...props} />
);

/**
 * 等待狀態指示器
 */
export const PendingStatus: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="pending" animated {...props} />
);

/**
 * 活躍狀態指示器
 */
export const ActiveStatus: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="active" animated {...props} />
);

export default StatusIndicator;