/**
 * Input 組件
 * 提供多種樣式和功能的輸入欄位元件
 */

import React from 'react';
import styled, { css } from 'styled-components';
import { spacing, borderRadius, typography, animations } from '../../styles';

// ============= 類型定義 =============

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** 輸入欄位尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否有錯誤狀態 */
  error?: boolean;
  /** 錯誤訊息 */
  errorMessage?: string;
  /** 標籤文字 */
  label?: string;
  /** 提示文字 */
  helperText?: string;
  /** 左側圖標 */
  leftIcon?: React.ReactNode;
  /** 右側圖標 */
  rightIcon?: React.ReactNode;
  /** 是否為全寬度 */
  fullWidth?: boolean;
  /** 容器的額外樣式類名 */
  containerClassName?: string;
}

// ============= 樣式定義 =============

const getSizeStyles = (size: InputProps['size']) => {
  switch (size) {
    case 'sm':
      return css`
        padding: ${spacing[2]} ${spacing[3]};
        font-size: ${typography.fontSize.sm};
        min-height: 32px;
      `;
    
    case 'lg':
      return css`
        padding: ${spacing[3]} ${spacing[4]};
        font-size: ${typography.fontSize.lg};
        min-height: 48px;
      `;
    
    case 'md':
    default:
      return css`
        padding: ${spacing[2]} ${spacing[3]};
        font-size: ${typography.fontSize.base};
        min-height: 40px;
      `;
  }
};

const InputContainer = styled.div<{ fullWidth?: boolean }>`
  display: flex;
  flex-direction: column;
  gap: ${spacing[1]};
  
  ${props => props.fullWidth && css`
    width: 100%;
  `}
`;

const Label = styled.label`
  font-size: ${typography.fontSize.sm};
  font-weight: ${typography.fontWeight.medium};
  color: var(--color-text-primary);
  line-height: ${typography.lineHeight.tight};
`;

const InputWrapper = styled.div<{ hasLeftIcon?: boolean; hasRightIcon?: boolean; error?: boolean }>`
  position: relative;
  display: flex;
  align-items: center;
  
  ${props => props.hasLeftIcon && css`
    padding-left: ${spacing[10]};
  `}
  
  ${props => props.hasRightIcon && css`
    padding-right: ${spacing[10]};
  `}
`;

const StyledInput = styled.input<InputProps>`
  width: 100%;
  font-family: ${typography.fontFamily.sans.join(', ')};
  font-weight: ${typography.fontWeight.normal};
  line-height: ${typography.lineHeight.normal};
  color: var(--color-text-primary);
  background-color: var(--color-background-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: ${borderRadius.md};
  transition: all ${animations.duration.fast} ${animations.easing.easeInOut};
  
  ${props => getSizeStyles(props.size)}
  
  &::placeholder {
    color: var(--color-text-tertiary);
  }
  
  &:hover:not(:disabled) {
    border-color: var(--color-border-secondary);
  }
  
  &:focus {
    outline: none;
    border-color: var(--color-border-focus);
    box-shadow: 0 0 0 3px var(--color-border-focus-shadow);
  }
  
  &:disabled {
    background-color: var(--color-background-disabled);
    color: var(--color-text-disabled);
    cursor: not-allowed;
    
    &::placeholder {
      color: var(--color-text-disabled);
    }
  }
  
  ${props => props.error && css`
    border-color: var(--color-status-error);
    
    &:focus {
      border-color: var(--color-status-error);
      box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
    }
  `}
`;

const IconWrapper = styled.div<{ position: 'left' | 'right' }>`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  pointer-events: none;
  z-index: 1;
  
  ${props => props.position === 'left' && css`
    left: ${spacing[3]};
  `}
  
  ${props => props.position === 'right' && css`
    right: ${spacing[3]};
  `}
`;

const HelperText = styled.div<{ error?: boolean }>`
  font-size: ${typography.fontSize.sm};
  line-height: ${typography.lineHeight.tight};
  color: var(--color-text-secondary);
  
  ${props => props.error && css`
    color: var(--color-status-error);
  `}
`;

// ============= 組件實作 =============

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      size = 'md',
      error = false,
      errorMessage,
      label,
      helperText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      containerClassName,
      ...props
    },
    ref
  ) => {
    const hasLeftIcon = Boolean(leftIcon);
    const hasRightIcon = Boolean(rightIcon);
    const displayHelperText = error ? errorMessage : helperText;

    return (
      <InputContainer fullWidth={fullWidth} className={containerClassName}>
        {label && <Label>{label}</Label>}
        
        <InputWrapper
          hasLeftIcon={hasLeftIcon}
          hasRightIcon={hasRightIcon}
          error={error}
        >
          {leftIcon && (
            <IconWrapper position="left">
              {leftIcon}
            </IconWrapper>
          )}
          
          <StyledInput
            ref={ref}
            size={size}
            error={error}
            style={{
              paddingLeft: hasLeftIcon ? spacing[10] : undefined,
              paddingRight: hasRightIcon ? spacing[10] : undefined,
            }}
            {...props}
          />
          
          {rightIcon && (
            <IconWrapper position="right">
              {rightIcon}
            </IconWrapper>
          )}
        </InputWrapper>
        
        {displayHelperText && (
          <HelperText error={error}>
            {displayHelperText}
          </HelperText>
        )}
      </InputContainer>
    );
  }
);

Input.displayName = 'Input';

export default Input;