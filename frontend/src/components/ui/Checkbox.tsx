/**
 * Checkbox 組件
 * 
 * 提供複選框功能，支援：
 * - 基本選中/未選中狀態
 * - 不確定狀態（indeterminate）
 * - 禁用狀態
 * - 自定義樣式
 */

import React from 'react';
import styled from 'styled-components';

// ============= 類型定義 =============

export interface CheckboxProps {
  /** 是否選中 */
  checked?: boolean;
  /** 不確定狀態（用於全選時部分選中的情況） */
  indeterminate?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 標籤文字 */
  children?: React.ReactNode;
  /** 變更事件處理 */
  onChange?: (checked: boolean) => void;
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

// ============= 樣式定義 =============

const CheckboxContainer = styled.label<{ disabled?: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.disabled ? 0.6 : 1};
  user-select: none;
  font-size: 14px;
  line-height: 1.5;
`;

const CheckboxInput = styled.input`
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
`;

const CheckboxBox = styled.div<{ checked?: boolean; indeterminate?: boolean; disabled?: boolean }>`
  width: 16px;
  height: 16px;
  border: 2px solid ${props => {
    if (props.disabled) return 'var(--color-border-disabled)';
    if (props.checked || props.indeterminate) return 'var(--color-primary)';
    return 'var(--color-border)';
  }};
  border-radius: 3px;
  background: ${props => {
    if (props.checked || props.indeterminate) return 'var(--color-primary)';
    return 'var(--color-background)';
  }};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  position: relative;
  
  &:hover {
    border-color: ${props => props.disabled ? 'var(--color-border-disabled)' : 'var(--color-primary)'};
  }
  
  &::after {
    content: '';
    display: ${props => (props.checked || props.indeterminate) ? 'block' : 'none'};
    width: ${props => props.indeterminate ? '8px' : '4px'};
    height: ${props => props.indeterminate ? '2px' : '8px'};
    border: ${props => props.indeterminate ? 'none' : '2px solid white'};
    border-top: ${props => props.indeterminate ? '2px solid white' : 'none'};
    border-left: ${props => props.indeterminate ? 'none' : 'none'};
    border-right: ${props => props.indeterminate ? 'none' : '2px solid white'};
    border-bottom: ${props => props.indeterminate ? 'none' : '2px solid white'};
    background: ${props => props.indeterminate ? 'white' : 'transparent'};
    transform: ${props => props.indeterminate ? 'none' : 'rotate(45deg) translate(-1px, -2px)'};
  }
`;

const CheckboxLabel = styled.span`
  color: var(--color-text-primary);
  font-weight: 400;
`;

// ============= 組件實現 =============

export const Checkbox: React.FC<CheckboxProps> = ({
  checked = false,
  indeterminate = false,
  disabled = false,
  children,
  onChange,
  className,
  style
}) => {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    onChange?.(event.target.checked);
  };

  return (
    <CheckboxContainer 
      disabled={disabled}
      className={className}
      style={style}
    >
      <CheckboxInput
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={handleChange}
      />
      <CheckboxBox 
        checked={checked}
        indeterminate={indeterminate}
        disabled={disabled}
      />
      {children && (
        <CheckboxLabel>{children}</CheckboxLabel>
      )}
    </CheckboxContainer>
  );
};

export default Checkbox;