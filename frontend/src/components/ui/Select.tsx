/**
 * Select 選擇器組件
 * 
 * 提供下拉選擇功能，支援：
 * - 單選和多選
 * - 搜尋過濾
 * - 自定義選項渲染
 * - 禁用狀態
 */

import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';

// ============= 類型定義 =============

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  icon?: React.ReactNode;
}

export interface SelectProps {
  /** 選項列表 */
  options: SelectOption[];
  /** 當前值 */
  value?: string | number | (string | number)[];
  /** 預設值 */
  defaultValue?: string | number | (string | number)[];
  /** 佔位符文字 */
  placeholder?: string;
  /** 是否多選 */
  multiple?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否可搜尋 */
  searchable?: boolean;
  /** 是否可清除 */
  clearable?: boolean;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 狀態 */
  status?: 'default' | 'error' | 'warning' | 'success';
  /** 載入狀態 */
  loading?: boolean;
  /** 變更回調 */
  onChange?: (value: string | number | (string | number)[]) => void;
  /** 搜尋回調 */
  onSearch?: (searchText: string) => void;
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

// ============= 樣式定義 =============

const SelectContainer = styled.div<{
  $disabled?: boolean;
  $size: 'small' | 'medium' | 'large';
  $status: 'default' | 'error' | 'warning' | 'success';
}>`
  position: relative;
  display: inline-block;
  width: 100%;
  
  ${props => props.$disabled && `
    opacity: 0.6;
    cursor: not-allowed;
  `}
`;

const SelectTrigger = styled.div<{
  $size: 'small' | 'medium' | 'large';
  $status: 'default' | 'error' | 'warning' | 'success';
  $focused: boolean;
}>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${props => {
    switch (props.$size) {
      case 'small': return '6px 12px';
      case 'large': return '12px 16px';
      default: return '8px 12px';
    }
  }};
  border: 1px solid ${props => {
    if (props.$focused) return props.theme.colors.interactive.primary;
    switch (props.$status) {
      case 'error': return props.theme.colors.status.error;
      case 'warning': return props.theme.colors.status.warning;
      case 'success': return props.theme.colors.status.success;
      default: return props.theme.colors.border;
    }
  }};
  border-radius: 6px;
  background: ${props => props.theme.colors.background};
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: ${props => props.theme.colors.interactive.primary};
  }
`;

const SelectValue = styled.div`
  flex: 1;
  color: ${props => props.theme.colors.text};
  font-size: 14px;
  
  &.placeholder {
    color: ${props => props.theme.colors.text.secondary};
  }
`;

const SelectArrow = styled.div<{ $open: boolean }>`
  margin-left: 8px;
  transition: transform 0.2s ease;
  transform: ${props => props.$open ? 'rotate(180deg)' : 'rotate(0deg)'};
  color: ${props => props.theme.colors.text.secondary};
`;

const SelectDropdown = styled.div<{ $open: boolean }>`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
  margin-top: 4px;
  
  opacity: ${props => props.$open ? 1 : 0};
  visibility: ${props => props.$open ? 'visible' : 'hidden'};
  transform: ${props => props.$open ? 'translateY(0)' : 'translateY(-10px)'};
  transition: all 0.2s ease;
`;

const SelectOption = styled.div<{ $selected: boolean; $disabled?: boolean }>`
  padding: 8px 12px;
  cursor: ${props => props.$disabled ? 'not-allowed' : 'pointer'};
  background: ${props => {
    if (props.$disabled) return 'transparent';
    if (props.$selected) return props.theme.colors.background.secondary;
    return 'transparent';
  }};
  color: ${props => {
    if (props.$disabled) return props.theme.colors.text.disabled;
    if (props.$selected) return props.theme.colors.interactive.primary;
    return props.theme.colors.text;
  }};
  
  &:hover {
    background: ${props => {
      if (props.$disabled) return 'transparent';
      return props.theme.colors.interactive.primaryHover;
    }};
  }
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
  font-size: 14px;
  outline: none;
  
  &::placeholder {
    color: ${props => props.theme.colors.text.secondary};
  }
`;

// ============= 組件實現 =============

export const Select: React.FC<SelectProps> = ({
  options,
  value,
  defaultValue,
  placeholder = '請選擇',
  multiple = false,
  disabled = false,
  searchable = false,
  size = 'medium',
  status = 'default',
  onChange,
  onSearch,
  className,
  style
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [internalValue, setInternalValue] = useState(value || defaultValue || (multiple ? [] : ''));
  const [focused, setFocused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // 處理點擊外部關閉
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 同步外部值
  useEffect(() => {
    if (value !== undefined) {
      setInternalValue(value);
    }
  }, [value]);

  // 過濾選項
  const filteredOptions = searchable && searchText
    ? options.filter(option => 
        option.label.toLowerCase().includes(searchText.toLowerCase())
      )
    : options;

  // 獲取顯示值
  const getDisplayValue = () => {
    if (multiple) {
      const selectedOptions = options.filter(option => 
        (internalValue as (string | number)[]).includes(option.value)
      );
      return selectedOptions.length > 0 
        ? selectedOptions.map(option => option.label).join(', ')
        : placeholder;
    } else {
      const selectedOption = options.find(option => option.value === internalValue);
      return selectedOption ? selectedOption.label : placeholder;
    }
  };

  // 處理選項點擊
  const handleOptionClick = (optionValue: string | number) => {
    if (disabled) return;

    let newValue;
    if (multiple) {
      const currentValues = internalValue as (string | number)[];
      if (currentValues.includes(optionValue)) {
        newValue = currentValues.filter(v => v !== optionValue);
      } else {
        newValue = [...currentValues, optionValue];
      }
    } else {
      newValue = optionValue;
      setIsOpen(false);
      setFocused(false);
    }

    setInternalValue(newValue);
    onChange?.(newValue);
  };

  // 處理搜尋
  const handleSearch = (text: string) => {
    setSearchText(text);
    onSearch?.(text);
  };

  return (
    <SelectContainer
      ref={containerRef}
      $disabled={disabled}
      $size={size}
      $status={status}
      className={className}
      style={style}
    >
      <SelectTrigger
        $size={size}
        $status={status}
        $focused={focused}
        onClick={() => {
          if (!disabled) {
            setIsOpen(!isOpen);
            setFocused(!isOpen);
          }
        }}
      >
        <SelectValue className={getDisplayValue() === placeholder ? 'placeholder' : ''}>
          {getDisplayValue()}
        </SelectValue>
        <SelectArrow $open={isOpen}>
          ▼
        </SelectArrow>
      </SelectTrigger>
      
      <SelectDropdown $open={isOpen}>
        {searchable && (
          <SearchInput
            type="text"
            placeholder="搜尋選項..."
            value={searchText}
            onChange={(e) => handleSearch(e.target.value)}
            onClick={(e) => e.stopPropagation()}
          />
        )}
        
        {filteredOptions.map((option) => {
          const isSelected = multiple
            ? (internalValue as (string | number)[]).includes(option.value)
            : internalValue === option.value;
            
          return (
            <SelectOption
              key={option.value}
              $selected={isSelected}
              $disabled={option.disabled}
              onClick={() => !option.disabled && handleOptionClick(option.value)}
            >
              {option.icon && <span style={{ marginRight: 8 }}>{option.icon}</span>}
              {option.label}
            </SelectOption>
          );
        })}
        
        {filteredOptions.length === 0 && (
          <SelectOption $selected={false}>
            無匹配選項
          </SelectOption>
        )}
      </SelectDropdown>
    </SelectContainer>
  );
};

export default Select;