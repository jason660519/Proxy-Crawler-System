/**
 * TextArea 多行文字輸入組件
 * 
 * 提供多行文字輸入功能，支援：
 * - 自動調整高度
 * - 字數統計
 * - 最大長度限制
 * - 不同狀態樣式
 */

import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';

// ============= 類型定義 =============

export interface TextAreaProps {
  /** 輸入值 */
  value?: string;
  /** 預設值 */
  defaultValue?: string;
  /** 佔位符文字 */
  placeholder?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否唯讀 */
  readOnly?: boolean;
  /** 最大長度 */
  maxLength?: number;
  /** 最小行數 */
  minRows?: number;
  /** 最大行數 */
  maxRows?: number;
  /** 是否自動調整高度 */
  autoResize?: boolean;
  /** 是否顯示字數統計 */
  showCount?: boolean;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 狀態 */
  status?: 'default' | 'error' | 'warning' | 'success';
  /** 變更回調 */
  onChange?: (value: string, event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  /** 焦點回調 */
  onFocus?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  /** 失焦回調 */
  onBlur?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  /** 按鍵回調 */
  onKeyDown?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

// ============= 樣式定義 =============

const TextAreaContainer = styled.div<{
  $disabled?: boolean;
  $size: 'small' | 'medium' | 'large';
}>`
  position: relative;
  width: 100%;
  
  ${props => props.$disabled && `
    opacity: 0.6;
    cursor: not-allowed;
  `}
`;

const StyledTextArea = styled.textarea<{
  $size: 'small' | 'medium' | 'large';
  $status: 'default' | 'error' | 'warning' | 'success';
  $focused: boolean;
  $showCount: boolean;
}>`
  width: 100%;
  padding: ${props => {
    switch (props.$size) {
      case 'small': return '6px 12px';
      case 'large': return '12px 16px';
      default: return '8px 12px';
    }
  }};
  padding-bottom: ${props => props.$showCount ? '32px' : undefined};
  border: 1px solid ${props => {
    if (props.$focused) return '#3b82f6';
    switch (props.$status) {
      case 'error': return '#ef4444';
      case 'warning': return '#f59e0b';
      case 'success': return '#10b981';
      default: return '#d1d5db';
    }
  }};
  border-radius: 6px;
  background: #ffffff;
  color: #1f2937;
  font-size: ${props => {
    switch (props.$size) {
      case 'small': return '12px';
      case 'large': return '16px';
      default: return '14px';
    }
  }};
  line-height: 1.5;
  resize: vertical;
  transition: all 0.2s ease;
  outline: none;
  
  &::placeholder {
    color: #6b7280;
  }
  
  &:hover:not(:disabled) {
    border-color: #3b82f6;
  }
  
  &:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  }
  
  &:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
  }
  
  &:read-only {
    background: #f9fafb;
  }
`;

const CountDisplay = styled.div<{
  $size: 'small' | 'medium' | 'large';
  $status: 'default' | 'error' | 'warning' | 'success';
  $exceeded: boolean;
}>`
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: ${props => {
    switch (props.$size) {
      case 'small': return '10px';
      case 'large': return '14px';
      default: return '12px';
    }
  }};
  color: ${props => {
    if (props.$exceeded) return '#ef4444';
    return '#6b7280';
  }};
  pointer-events: none;
  user-select: none;
`;

// ============= 組件實現 =============

export const TextArea: React.FC<TextAreaProps> = ({
  value,
  defaultValue,
  placeholder,
  disabled = false,
  readOnly = false,
  maxLength,
  minRows = 3,
  maxRows,
  autoResize = false,
  showCount = false,
  size = 'medium',
  status = 'default',
  onChange,
  onFocus,
  onBlur,
  onKeyDown,
  className,
  style
}) => {
  const [internalValue, setInternalValue] = useState(value || defaultValue || '');
  const [focused, setFocused] = useState(false);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  // 同步外部值
  useEffect(() => {
    if (value !== undefined) {
      setInternalValue(value);
    }
  }, [value]);

  // 自動調整高度
  useEffect(() => {
    if (autoResize && textAreaRef.current) {
      const textArea = textAreaRef.current;
      textArea.style.height = 'auto';
      
      const lineHeight = parseInt(getComputedStyle(textArea).lineHeight);
      const minHeight = lineHeight * minRows;
      const maxHeight = maxRows ? lineHeight * maxRows : Infinity;
      
      const scrollHeight = Math.max(minHeight, Math.min(textArea.scrollHeight, maxHeight));
      textArea.style.height = `${scrollHeight}px`;
    }
  }, [internalValue, autoResize, minRows, maxRows]);

  // 處理值變更
  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = event.target.value;
    
    // 檢查最大長度
    if (maxLength && newValue.length > maxLength) {
      return;
    }
    
    setInternalValue(newValue);
    onChange?.(newValue, event);
  };

  // 處理焦點
  const handleFocus = (event: React.FocusEvent<HTMLTextAreaElement>) => {
    setFocused(true);
    onFocus?.(event);
  };

  // 處理失焦
  const handleBlur = (event: React.FocusEvent<HTMLTextAreaElement>) => {
    setFocused(false);
    onBlur?.(event);
  };

  // 計算字數統計
  const currentLength = internalValue.length;
  const isExceeded = maxLength ? currentLength > maxLength : false;

  return (
    <TextAreaContainer
      $disabled={disabled}
      $size={size}
      className={className}
      style={style}
    >
      <StyledTextArea
        ref={textAreaRef}
        value={internalValue}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        maxLength={maxLength}
        rows={autoResize ? undefined : minRows}
        $size={size}
        $status={status}
        $focused={focused}
        $showCount={showCount}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onKeyDown={onKeyDown}
      />
      
      {showCount && (
        <CountDisplay
          $size={size}
          $status={status}
          $exceeded={isExceeded}
        >
          {maxLength ? `${currentLength}/${maxLength}` : currentLength}
        </CountDisplay>
      )}
    </TextAreaContainer>
  );
};

export default TextArea;