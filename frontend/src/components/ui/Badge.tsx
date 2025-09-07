/**
 * 徽章組件 - VS Code 風格的狀態標籤
 * 提供多種樣式和用途的徽章組件，用於顯示狀態、計數等信息
 */

import React from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 徽章容器
const BadgeContainer = styled.span<{
  theme: 'light' | 'dark';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
  size: 'small' | 'medium' | 'large';
  outline?: boolean;
  dot?: boolean;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  vertical-align: baseline;
  
  border-radius: ${props => props.dot ? '50%' : borderRadius.full};
  transition: ${transitions.fast};
  
  ${props => {
    // 尺寸設置
    switch (props.size) {
      case 'small':
        return `
          min-width: ${props.dot ? '6px' : '16px'};
          height: ${props.dot ? '6px' : '16px'};
          padding: ${props.dot ? '0' : `0 ${spacing.xs}`};
          font-size: 10px;
        `;
      case 'large':
        return `
          min-width: ${props.dot ? '10px' : '24px'};
          height: ${props.dot ? '10px' : '24px'};
          padding: ${props.dot ? '0' : `0 ${spacing.sm}`};
          font-size: 14px;
        `;
      default:
        return `
          min-width: ${props.dot ? '8px' : '20px'};
          height: ${props.dot ? '8px' : '20px'};
          padding: ${props.dot ? '0' : `0 ${spacing.xs}`};
          font-size: 12px;
        `;
    }
  }}
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    // 顏色變體
    const getVariantColors = () => {
      switch (props.variant) {
        case 'primary':
          return {
            bg: colors.accent.primary,
            text: colors.text.inverse,
            border: colors.accent.primary
          };
        case 'success':
          return {
            bg: colors.status.success,
            text: colors.text.inverse,
            border: colors.status.success
          };
        case 'warning':
          return {
            bg: colors.status.warning,
            text: colors.text.primary,
            border: colors.status.warning
          };
        case 'error':
          return {
            bg: colors.status.error,
            text: colors.text.inverse,
            border: colors.status.error
          };
        case 'info':
          return {
            bg: colors.status.info,
            text: colors.text.inverse,
            border: colors.status.info
          };
        default:
          return {
            bg: colors.background.secondary,
            text: colors.text.secondary,
            border: colors.border.primary
          };
      }
    };
    
    const variantColors = getVariantColors();
    
    if (props.outline) {
      return `
        background-color: transparent;
        color: ${variantColors.bg};
        border: 1px solid ${variantColors.border};
      `;
    }
    
    return `
      background-color: ${variantColors.bg};
      color: ${variantColors.text};
      border: 1px solid transparent;
    `;
  }}
`;

// 徽章文字
const BadgeText = styled.span`
  display: inline-block;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

// 徽章圖標
const BadgeIcon = styled.span<{
  hasText: boolean;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  
  ${props => props.hasText ? `margin-right: ${spacing.xs};` : ''}
  
  svg {
    width: 1em;
    height: 1em;
  }
`;

// 徽章組件介面
export interface BadgeProps {
  theme: 'light' | 'dark';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'small' | 'medium' | 'large';
  children?: React.ReactNode;
  icon?: React.ReactNode;
  outline?: boolean;
  dot?: boolean;
  className?: string;
  onClick?: () => void;
}

/**
 * 徽章組件
 * 用於顯示狀態、計數和標籤信息
 */
export const Badge: React.FC<BadgeProps> = ({
  theme,
  variant = 'default',
  size = 'medium',
  children,
  icon,
  outline = false,
  dot = false,
  className,
  onClick
}) => {
  const hasText = children !== undefined && children !== null && children !== '';
  const hasIcon = icon !== undefined;
  
  // 如果是點狀徽章，不顯示文字和圖標
  if (dot) {
    return (
      <BadgeContainer
        theme={theme}
        variant={variant}
        size={size}
        outline={outline}
        dot={dot}
        className={className}
        onClick={onClick}
        style={{ cursor: onClick ? 'pointer' : 'default' }}
      />
    );
  }
  
  return (
    <BadgeContainer
      theme={theme}
      variant={variant}
      size={size}
      outline={outline}
      dot={dot}
      className={className}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {hasIcon && (
        <BadgeIcon hasText={hasText}>
          {icon}
        </BadgeIcon>
      )}
      
      {hasText && (
        <BadgeText>
          {children}
        </BadgeText>
      )}
    </BadgeContainer>
  );
};

// 數字徽章組件介面
export interface NumberBadgeProps {
  theme: 'light' | 'dark';
  count: number;
  max?: number;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'small' | 'medium' | 'large';
  outline?: boolean;
  showZero?: boolean;
  className?: string;
  onClick?: () => void;
}

/**
 * 數字徽章組件
 * 專門用於顯示數字計數
 */
export const NumberBadge: React.FC<NumberBadgeProps> = ({
  theme,
  count,
  max = 99,
  variant = 'primary',
  size = 'medium',
  outline = false,
  showZero = false,
  className,
  onClick
}) => {
  // 如果計數為0且不顯示零，則不渲染
  if (count === 0 && !showZero) {
    return null;
  }
  
  // 格式化計數顯示
  const formatCount = (num: number): string => {
    if (num <= max) {
      return num.toString();
    }
    return `${max}+`;
  };
  
  return (
    <Badge
      theme={theme}
      variant={variant}
      size={size}
      outline={outline}
      className={className}
      onClick={onClick}
    >
      {formatCount(count)}
    </Badge>
  );
};

// 狀態徽章組件介面
export interface StatusBadgeProps {
  theme: 'light' | 'dark';
  status: 'online' | 'offline' | 'busy' | 'away' | 'idle';
  size?: 'small' | 'medium' | 'large';
  showText?: boolean;
  className?: string;
}

/**
 * 狀態徽章組件
 * 用於顯示用戶或系統狀態
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  theme,
  status,
  size = 'medium',
  showText = false,
  className
}) => {
  // 狀態配置
  const statusConfig = {
    online: {
      variant: 'success' as const,
      text: '在線',
      icon: '●'
    },
    offline: {
      variant: 'default' as const,
      text: '離線',
      icon: '●'
    },
    busy: {
      variant: 'error' as const,
      text: '忙碌',
      icon: '●'
    },
    away: {
      variant: 'warning' as const,
      text: '離開',
      icon: '●'
    },
    idle: {
      variant: 'info' as const,
      text: '閒置',
      icon: '●'
    }
  };
  
  const config = statusConfig[status];
  
  if (!showText) {
    return (
      <Badge
        theme={theme}
        variant={config.variant}
        size={size}
        dot
        className={className}
      />
    );
  }
  
  return (
    <Badge
      theme={theme}
      variant={config.variant}
      size={size}
      className={className}
    >
      {config.text}
    </Badge>
  );
};

// 徽章組合容器
const BadgeGroupContainer = styled.div<{
  direction: 'horizontal' | 'vertical';
}>`
  display: flex;
  flex-direction: ${props => props.direction === 'vertical' ? 'column' : 'row'};
  gap: ${spacing.xs};
  align-items: ${props => props.direction === 'vertical' ? 'flex-start' : 'center'};
  flex-wrap: wrap;
`;

// 徽章組合組件介面
export interface BadgeGroupProps {
  direction?: 'horizontal' | 'vertical';
  children: React.ReactNode;
  className?: string;
}

/**
 * 徽章組合組件
 * 用於組織多個徽章的布局
 */
export const BadgeGroup: React.FC<BadgeGroupProps> = ({
  direction = 'horizontal',
  children,
  className
}) => {
  return (
    <BadgeGroupContainer
      direction={direction}
      className={className}
    >
      {children}
    </BadgeGroupContainer>
  );
};

export default Badge;