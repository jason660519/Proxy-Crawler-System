/**
 * 按鈕組件 - VS Code 風格的互動按鈕
 * 提供多種樣式變體和狀態
 */

import React from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 按鈕基礎樣式
const BaseButton = styled.button<{
  theme: 'light' | 'dark';
  variant: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  loading?: boolean;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.xs};
  border: none;
  border-radius: ${borderRadius.sm};
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all ${transitions.fast} ease;
  position: relative;
  overflow: hidden;
  white-space: nowrap;
  
  ${props => props.fullWidth && 'width: 100%;'}
  
  /* 尺寸樣式 */
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          padding: ${spacing.xs} ${spacing.sm};
          font-size: 11px;
          min-height: 24px;
        `;
      case 'large':
        return `
          padding: ${spacing.md} ${spacing.lg};
          font-size: 14px;
          min-height: 40px;
        `;
      default:
        return `
          padding: ${spacing.sm} ${spacing.md};
          font-size: 12px;
          min-height: 32px;
        `;
    }
  }}
  
  /* 變體樣式 */
  ${props => {
    const colors = getThemeColors(props.theme);
    
    switch (props.variant) {
      case 'primary':
        return `
          background-color: ${colors.interactive.primary};
          color: ${colors.interactive.primaryForeground};
          
          &:hover:not(:disabled) {
            background-color: ${colors.interactive.primaryHover};
          }
          
          &:active:not(:disabled) {
            background-color: ${colors.interactive.primaryActive};
          }
        `;
        
      case 'secondary':
        return `
          background-color: ${colors.background.tertiary};
          color: ${colors.text.primary};
          border: 1px solid ${colors.border.primary};
          
          &:hover:not(:disabled) {
            background-color: ${colors.interactive.hover};
          }
          
          &:active:not(:disabled) {
            background-color: ${colors.interactive.selected};
          }
        `;
        
      case 'outline':
        return `
          background-color: transparent;
          color: ${colors.interactive.primary};
          border: 1px solid ${colors.interactive.primary};
          
          &:hover:not(:disabled) {
            background-color: ${colors.interactive.primary};
            color: ${colors.interactive.primaryForeground};
          }
          
          &:active:not(:disabled) {
            background-color: ${colors.interactive.primaryActive};
          }
        `;
        
      case 'ghost':
        return `
          background-color: transparent;
          color: ${colors.text.secondary};
          
          &:hover:not(:disabled) {
            background-color: ${colors.interactive.hover};
            color: ${colors.text.primary};
          }
          
          &:active:not(:disabled) {
            background-color: ${colors.interactive.selected};
          }
        `;
        
      case 'danger':
        return `
          background-color: ${colors.status.error};
          color: ${colors.interactive.primaryForeground};
          
          &:hover:not(:disabled) {
            background-color: ${colors.status.errorHover || colors.status.error};
            filter: brightness(0.9);
          }
          
          &:active:not(:disabled) {
            filter: brightness(0.8);
          }
        `;
        
      default:
        return '';
    }
  }}
  
  /* 焦點樣式 */
  &:focus-visible {
    outline: 2px solid ${props => getThemeColors(props.theme).border.focus};
    outline-offset: 2px;
  }
  
  /* 禁用狀態 */
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      transform: none;
    }
  }
  
  /* 載入狀態 */
  ${props => props.loading && `
    pointer-events: none;
    
    &::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 16px;
      height: 16px;
      margin: -8px 0 0 -8px;
      border: 2px solid transparent;
      border-top: 2px solid currentColor;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `}
`;

// 按鈕圖標
const ButtonIcon = styled.span<{ position: 'left' | 'right' }>`
  display: inline-flex;
  align-items: center;
  
  svg, i {
    width: 14px;
    height: 14px;
  }
  
  ${props => props.position === 'right' && 'order: 1;'}
`;

// 按鈕文字（載入時隱藏）
const ButtonText = styled.span<{ loading?: boolean }>`
  ${props => props.loading && 'opacity: 0;'}
`;

// 按鈕群組
const ButtonGroup = styled.div<{ theme: 'light' | 'dark' }>`
  display: inline-flex;
  
  button {
    border-radius: 0;
    
    &:first-child {
      border-top-left-radius: ${borderRadius.sm};
      border-bottom-left-radius: ${borderRadius.sm};
    }
    
    &:last-child {
      border-top-right-radius: ${borderRadius.sm};
      border-bottom-right-radius: ${borderRadius.sm};
    }
    
    &:not(:first-child) {
      border-left: 1px solid ${props => getThemeColors(props.theme).border.secondary};
    }
  }
`;

// 圖標按鈕（正方形）
const IconButton = styled(BaseButton)<{
  theme: 'light' | 'dark';
  variant: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size: 'small' | 'medium' | 'large';
}>`
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 24px;
          height: 24px;
          padding: 0;
        `;
      case 'large':
        return `
          width: 40px;
          height: 40px;
          padding: 0;
        `;
      default:
        return `
          width: 32px;
          height: 32px;
          padding: 0;
        `;
    }
  }}
  
  svg, i {
    width: ${props => {
      switch (props.size) {
        case 'small': return '12px';
        case 'large': return '20px';
        default: return '16px';
      }
    }};
    height: ${props => {
      switch (props.size) {
        case 'small': return '12px';
        case 'large': return '20px';
        default: return '16px';
      }
    }};
  }
`;

// 按鈕組件介面
export interface ButtonProps {
  theme: 'light' | 'dark';
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  className?: string;
  children?: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseEnter?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseLeave?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  title?: string;
}

/**
 * 按鈕組件
 * 提供統一的互動按鈕樣式
 */
export const Button: React.FC<ButtonProps> = ({
  theme,
  variant = 'secondary',
  size = 'medium',
  fullWidth = false,
  loading = false,
  disabled = false,
  icon,
  iconPosition = 'left',
  className,
  children,
  onClick,
  onMouseEnter,
  onMouseLeave,
  type = 'button',
  title
}) => {
  return (
    <BaseButton
      theme={theme}
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      loading={loading}
      disabled={disabled || loading}
      className={className}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      type={type}
      title={title}
    >
      {icon && iconPosition === 'left' && (
        <ButtonIcon position="left">
          {icon}
        </ButtonIcon>
      )}
      
      {children && (
        <ButtonText loading={loading}>
          {children}
        </ButtonText>
      )}
      
      {icon && iconPosition === 'right' && (
        <ButtonIcon position="right">
          {icon}
        </ButtonIcon>
      )}
    </BaseButton>
  );
};

// 圖標按鈕組件介面
export interface IconButtonProps {
  theme: 'light' | 'dark';
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  icon: React.ReactNode;
  className?: string;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseEnter?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseLeave?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  title?: string;
}

/**
 * 圖標按鈕組件
 * 專門用於只顯示圖標的按鈕
 */
export const IconButtonComponent: React.FC<IconButtonProps> = ({
  theme,
  variant = 'ghost',
  size = 'medium',
  loading = false,
  disabled = false,
  icon,
  className,
  onClick,
  onMouseEnter,
  onMouseLeave,
  type = 'button',
  title
}) => {
  return (
    <IconButton
      theme={theme}
      variant={variant}
      size={size}
      loading={loading}
      disabled={disabled || loading}
      className={className}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      type={type}
      title={title}
    >
      {!loading && icon}
    </IconButton>
  );
};

// 按鈕群組組件介面
export interface ButtonGroupProps {
  theme: 'light' | 'dark';
  className?: string;
  children: React.ReactNode;
}

/**
 * 按鈕群組組件
 * 將多個按鈕組合在一起
 */
export const ButtonGroupComponent: React.FC<ButtonGroupProps> = ({
  theme,
  className,
  children
}) => {
  return (
    <ButtonGroup theme={theme} className={className}>
      {children}
    </ButtonGroup>
  );
};

// 導出組件
export { IconButtonComponent as IconButton, ButtonGroupComponent as ButtonGroup };
export default Button;