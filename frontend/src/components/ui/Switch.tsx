/**
 * Switch 開關組件
 * 
 * 提供開關切換功能，支援：
 * - 受控和非受控模式
 * - 不同尺寸和狀態
 * - 自定義標籤和描述
 * - 禁用狀態
 */

import React, { useState, useCallback } from 'react';
import styled from 'styled-components';

// ============= 類型定義 =============

export interface SwitchProps {
  /** 是否選中 */
  checked?: boolean;
  /** 預設選中狀態 */
  defaultChecked?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 載入狀態 */
  loading?: boolean;
  /** 選中時的文字 */
  checkedChildren?: React.ReactNode;
  /** 未選中時的文字 */
  unCheckedChildren?: React.ReactNode;
  /** 變更回調 */
  onChange?: (checked: boolean, event: React.MouseEvent<HTMLButtonElement>) => void;
  /** 點擊回調 */
  onClick?: (checked: boolean, event: React.MouseEvent<HTMLButtonElement>) => void;
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

// ============= 樣式定義 =============

const SwitchContainer = styled.button<{
  $checked: boolean;
  $disabled: boolean;
  $size: 'small' | 'medium' | 'large';
  $loading: boolean;
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: ${props => props.$checked ? 'flex-end' : 'flex-start'};
  width: ${props => {
    switch (props.$size) {
      case 'small': return '32px';
      case 'large': return '56px';
      default: return '44px';
    }
  }};
  height: ${props => {
    switch (props.$size) {
      case 'small': return '18px';
      case 'large': return '28px';
      default: return '22px';
    }
  }};
  padding: 2px;
  border: none;
  border-radius: ${props => {
    switch (props.$size) {
      case 'small': return '9px';
      case 'large': return '14px';
      default: return '11px';
    }
  }};
  background: ${props => {
    if (props.$disabled) return '#f5f5f5';
    return props.$checked ? '#1890ff' : '#d9d9d9';
  }};
  cursor: ${props => props.$disabled ? 'not-allowed' : 'pointer'};
  transition: all 0.2s ease;
  outline: none;
  
  &:hover:not(:disabled) {
    background: ${props => {
      if (props.$disabled) return '#f5f5f5';
      return props.$checked ? '#40a9ff' : '#bfbfbf';
    }};
  }
  
  &:focus {
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }
  
  &:active:not(:disabled) {
    background: ${props => {
      if (props.$disabled) return '#f5f5f5';
      return props.$checked ? '#096dd9' : '#8c8c8c';
    }};
  }
`;

const SwitchHandle = styled.div<{
  $checked: boolean;
  $size: 'small' | 'medium' | 'large';
  $loading: boolean;
}>`
  position: relative;
  width: ${props => {
    switch (props.$size) {
      case 'small': return '14px';
      case 'large': return '24px';
      default: return '18px';
    }
  }};
  height: ${props => {
    switch (props.$size) {
      case 'small': return '14px';
      case 'large': return '24px';
      default: return '18px';
    }
  }};
  background: #ffffff;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  
  ${props => props.$loading && `
    &::after {
      content: '';
      width: 8px;
      height: 8px;
      border: 1px solid #1890ff;
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }
  `}
`;

const SwitchInner = styled.div<{
  $checked: boolean;
  $size: 'small' | 'medium' | 'large';
}>`
  position: absolute;
  left: ${props => {
    if (props.$checked) {
      switch (props.$size) {
        case 'small': return '4px';
        case 'large': return '6px';
        default: return '5px';
      }
    }
    return 'auto';
  }};
  right: ${props => {
    if (!props.$checked) {
      switch (props.$size) {
        case 'small': return '4px';
        case 'large': return '6px';
        default: return '5px';
      }
    }
    return 'auto';
  }};
  top: 50%;
  transform: translateY(-50%);
  color: #ffffff;
  font-size: ${props => {
    switch (props.$size) {
      case 'small': return '10px';
      case 'large': return '14px';
      default: return '12px';
    }
  }};
  line-height: 1;
  white-space: nowrap;
  pointer-events: none;
  user-select: none;
`;

// ============= 組件實現 =============

export const Switch: React.FC<SwitchProps> = ({
  checked,
  defaultChecked = false,
  disabled = false,
  size = 'medium',
  loading = false,
  checkedChildren,
  unCheckedChildren,
  onChange,
  onClick,
  className,
  style
}) => {
  const [internalChecked, setInternalChecked] = useState(checked ?? defaultChecked);
  
  // 使用受控或非受控模式
  const isChecked = checked !== undefined ? checked : internalChecked;
  
  // 處理點擊事件
  const handleClick = useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) {
      return;
    }
    
    const newChecked = !isChecked;
    
    // 非受控模式下更新內部狀態
    if (checked === undefined) {
      setInternalChecked(newChecked);
    }
    
    // 觸發回調
    onChange?.(newChecked, event);
    onClick?.(newChecked, event);
  }, [checked, isChecked, disabled, loading, onChange, onClick]);
  
  return (
    <SwitchContainer
      type="button"
      role="switch"
      aria-checked={isChecked}
      disabled={disabled}
      $checked={isChecked}
      $disabled={disabled}
      $size={size}
      $loading={loading}
      onClick={handleClick}
      className={className}
      style={style}
    >
      {/* 內部文字 */}
      {(checkedChildren || unCheckedChildren) && (
        <SwitchInner $checked={isChecked} $size={size}>
          {isChecked ? checkedChildren : unCheckedChildren}
        </SwitchInner>
      )}
      
      {/* 開關手柄 */}
      <SwitchHandle
        $checked={isChecked}
        $size={size}
        $loading={loading}
      />
    </SwitchContainer>
  );
};

export default Switch;