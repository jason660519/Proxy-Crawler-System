/**
 * Button 組件
 * 提供多種樣式和尺寸的按鈕元件
 */

import React from 'react';
import styled, { css } from 'styled-components';
import { spacing, borderRadius, typography, animations } from '../../styles';

// ============= 類型定義 =============

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** 按鈕變體 */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  /** 按鈕尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否為載入狀態 */
  loading?: boolean;
  /** 是否為全寬度 */
  fullWidth?: boolean;
  /** 左側圖標 */
  leftIcon?: React.ReactNode;
  /** 右側圖標 */
  rightIcon?: React.ReactNode;
  /** 子元素 */
  children?: React.ReactNode;
}

// ============= 樣式定義 =============

const getVariantStyles = (variant: ButtonProps['variant']) => {
  switch (variant) {
    case 'primary':
      return css`
        background-color: var(--color-interactive-primary);
        color: var(--color-text-inverse);
        border: 1px solid var(--color-interactive-primary);
        
        &:hover:not(:disabled) {
          background-color: var(--color-interactive-primaryHover);
          border-color: var(--color-interactive-primaryHover);
        }
        
        &:active:not(:disabled) {
          background-color: var(--color-interactive-primaryActive);
          border-color: var(--color-interactive-primaryActive);
        }
      `;
    
    case 'secondary':
      return css`
        background-color: var(--color-interactive-secondary);
        color: var(--color-text-primary);
        border: 1px solid var(--color-border-primary);
        
        &:hover:not(:disabled) {
          background-color: var(--color-interactive-secondaryHover);
          border-color: var(--color-border-primary);
        }
        
        &:active:not(:disabled) {
          background-color: var(--color-interactive-secondaryActive);
        }
      `;
    
    case 'outline':
      return css`
        background-color: transparent;
        color: var(--color-interactive-primary);
        border: 1px solid var(--color-interactive-primary);
        
        &:hover:not(:disabled) {
          background-color: var(--color-interactive-primary);
          color: var(--color-text-inverse);
        }
        
        &:active:not(:disabled) {
          background-color: var(--color-interactive-primaryActive);
          border-color: var(--color-interactive-primaryActive);
        }
      `;
    
    case 'ghost':
      return css`
        background-color: transparent;
        color: var(--color-text-primary);
        border: 1px solid transparent;
        
        &:hover:not(:disabled) {
          background-color: var(--color-interactive-secondary);
        }
        
        &:active:not(:disabled) {
          background-color: var(--color-interactive-secondaryHover);
        }
      `;
    
    case 'danger':
      return css`
        background-color: var(--color-status-error);
        color: var(--color-text-inverse);
        border: 1px solid var(--color-status-error);
        
        &:hover:not(:disabled) {
          background-color: #dc2626;
          border-color: #dc2626;
        }
        
        &:active:not(:disabled) {
          background-color: #b91c1c;
          border-color: #b91c1c;
        }
      `;
    
    default:
      return css``;
  }
};

const getSizeStyles = (size: ButtonProps['size']) => {
  switch (size) {
    case 'sm':
      return css`
        padding: ${spacing[2]} ${spacing[3]};
        font-size: ${typography.fontSize.sm};
        min-height: 32px;
      `;
    
    case 'lg':
      return css`
        padding: ${spacing[3]} ${spacing[6]};
        font-size: ${typography.fontSize.lg};
        min-height: 48px;
      `;
    
    case 'md':
    default:
      return css`
        padding: ${spacing[2]} ${spacing[4]};
        font-size: ${typography.fontSize.base};
        min-height: 40px;
      `;
  }
};

const StyledButton = styled.button<ButtonProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing[2]};
  font-family: ${typography.fontFamily.sans.join(', ')};
  font-weight: ${typography.fontWeight.medium};
  line-height: ${typography.lineHeight.none};
  border-radius: ${borderRadius.md};
  cursor: pointer;
  transition: all ${animations.duration.fast} ${animations.easing.easeInOut};
  white-space: nowrap;
  user-select: none;
  
  ${props => getVariantStyles(props.variant)}
  ${props => getSizeStyles(props.size)}
  
  ${props => props.fullWidth && css`
    width: 100%;
  `}
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &:focus {
    outline: 2px solid var(--color-border-focus);
    outline-offset: 2px;
  }
`;

const LoadingSpinner = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const IconWrapper = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`;

// ============= 組件實作 =============

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      fullWidth = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <StyledButton
        ref={ref}
        variant={variant}
        size={size}
        fullWidth={fullWidth}
        disabled={isDisabled}
        {...props}
      >
        {loading && <LoadingSpinner />}
        {!loading && leftIcon && <IconWrapper>{leftIcon}</IconWrapper>}
        {children}
        {!loading && rightIcon && <IconWrapper>{rightIcon}</IconWrapper>}
      </StyledButton>
    );
  }
);

Button.displayName = 'Button';

export default Button;