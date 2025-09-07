/**
 * 下拉選擇組件 - VS Code 風格的選擇器
 * 提供單選和多選功能
 */

import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 選擇器容器
const SelectContainer = styled.div<{ fullWidth?: boolean }>`
  position: relative;
  display: inline-flex;
  flex-direction: column;
  gap: ${spacing.xs};
  ${props => props.fullWidth && 'width: 100%;'}
`;

// 選擇器標籤
const SelectLabel = styled.label<{ theme: 'light' | 'dark'; required?: boolean }>`
  font-size: 11px;
  font-weight: 500;
  color: ${props => getThemeColors(props.theme).text.secondary};
  
  ${props => props.required && `
    &::after {
      content: ' *';
      color: ${getThemeColors(props.theme).status.error};
    }
  `}
`;

// 選擇器觸發器
const SelectTrigger = styled.button<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  hasError?: boolean;
  disabled?: boolean;
  open?: boolean;
}>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background-color: ${props => getThemeColors(props.theme).input.background};
  border: 1px solid ${props => {
    const colors = getThemeColors(props.theme);
    if (props.hasError) return colors.status.error;
    if (props.open) return colors.border.focus;
    return colors.input.border;
  }};
  border-radius: ${borderRadius.sm};
  color: ${props => getThemeColors(props.theme).input.foreground};
  font-size: 12px;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: all ${transitions.fast} ease;
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          padding: ${spacing.xs} ${spacing.sm};
          height: 24px;
        `;
      case 'large':
        return `
          padding: ${spacing.md} ${spacing.lg};
          height: 40px;
          font-size: 14px;
        `;
      default:
        return `
          padding: ${spacing.sm} ${spacing.md};
          height: 32px;
        `;
    }
  }}
  
  &:hover:not(:disabled) {
    border-color: ${props => getThemeColors(props.theme).input.borderHover};
  }
  
  &:focus {
    outline: none;
    border-color: ${props => getThemeColors(props.theme).border.focus};
    box-shadow: 0 0 0 1px ${props => getThemeColors(props.theme).border.focus};
  }
  
  ${props => props.disabled && `
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      border-color: ${getThemeColors(props.theme).input.border};
    }
  `}
`;

// 選擇器值顯示
const SelectValue = styled.span<{ theme: 'light' | 'dark'; placeholder?: boolean }>`
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  
  ${props => props.placeholder && `
    color: ${getThemeColors(props.theme).input.placeholder};
  `}
`;

// 下拉箭頭
const SelectArrow = styled.div<{ theme: 'light' | 'dark'; open?: boolean }>`
  display: flex;
  align-items: center;
  margin-left: ${spacing.sm};
  color: ${props => getThemeColors(props.theme).text.secondary};
  transition: transform ${transitions.fast} ease;
  
  ${props => props.open && 'transform: rotate(180deg);'}
  
  svg {
    width: 12px;
    height: 12px;
  }
`;

// 下拉選項容器
const SelectDropdown = styled.div<{
  theme: 'light' | 'dark';
  open?: boolean;
  maxHeight?: number;
}>`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  background-color: ${props => getThemeColors(props.theme).dropdown.background};
  border: 1px solid ${props => getThemeColors(props.theme).dropdown.border};
  border-radius: ${borderRadius.sm};
  box-shadow: 0 4px 12px ${props => getThemeColors(props.theme).shadow.dropdown};
  max-height: ${props => props.maxHeight || 200}px;
  overflow-y: auto;
  margin-top: 2px;
  
  opacity: ${props => props.open ? 1 : 0};
  visibility: ${props => props.open ? 'visible' : 'hidden'};
  transform: ${props => props.open ? 'translateY(0)' : 'translateY(-8px)'};
  transition: all ${transitions.fast} ease;
`;

// 選項項目
const SelectOption = styled.div<{
  theme: 'light' | 'dark';
  selected?: boolean;
  disabled?: boolean;
}>`
  display: flex;
  align-items: center;
  padding: ${spacing.sm} ${spacing.md};
  font-size: 12px;
  cursor: pointer;
  transition: all ${transitions.fast} ease;
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    if (props.disabled) {
      return `
        color: ${colors.text.disabled};
        cursor: not-allowed;
        opacity: 0.5;
      `;
    }
    
    if (props.selected) {
      return `
        background-color: ${colors.interactive.selected};
        color: ${colors.text.primary};
      `;
    }
    
    return `
      color: ${colors.text.primary};
      
      &:hover {
        background-color: ${colors.interactive.hover};
      }
    `;
  }}
`;

// 選項組標題
const SelectGroup = styled.div<{ theme: 'light' | 'dark' }>`
  padding: ${spacing.sm} ${spacing.md};
  font-size: 11px;
  font-weight: 600;
  color: ${props => getThemeColors(props.theme).text.secondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid ${props => getThemeColors(props.theme).border.secondary};
`;

// 錯誤訊息
const ErrorMessage = styled.div<{ theme: 'light' | 'dark' }>`
  font-size: 11px;
  color: ${props => getThemeColors(props.theme).status.error};
  margin-top: ${spacing.xs};
`;

// 選項介面
export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  group?: string;
}

// 選擇器組件介面
export interface SelectProps {
  theme: 'light' | 'dark';
  size?: 'small' | 'medium' | 'large';
  label?: string;
  placeholder?: string;
  value?: string | number | (string | number)[];
  defaultValue?: string | number | (string | number)[];
  options: SelectOption[];
  multiple?: boolean;
  disabled?: boolean;
  required?: boolean;
  fullWidth?: boolean;
  error?: string;
  maxHeight?: number;
  className?: string;
  id?: string;
  name?: string;
  onChange?: (value: string | number | (string | number)[]) => void;
  onBlur?: () => void;
  onFocus?: () => void;
}

/**
 * 下拉選擇組件
 * 提供統一的選擇器樣式
 */
export const Select: React.FC<SelectProps> = ({
  theme,
  size = 'medium',
  label,
  placeholder = '請選擇...',
  value,
  defaultValue,
  options = [],
  multiple = false,
  disabled = false,
  required = false,
  fullWidth = false,
  error,
  maxHeight = 200,
  className,
  id,
  name,
  onChange,
  onBlur,
  onFocus
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState(value || defaultValue || (multiple ? [] : ''));
  const containerRef = useRef<HTMLDivElement>(null);
  
  // 處理點擊外部關閉下拉選單
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        onBlur?.();
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onBlur]);
  
  // 同步外部值變化
  useEffect(() => {
    if (value !== undefined) {
      setSelectedValue(value);
    }
  }, [value]);
  
  // 處理選項選擇
  const handleOptionSelect = (optionValue: string | number) => {
    if (disabled) return;
    
    let newValue;
    
    if (multiple) {
      const currentValues = Array.isArray(selectedValue) ? selectedValue : [];
      if (currentValues.includes(optionValue)) {
        newValue = currentValues.filter(v => v !== optionValue);
      } else {
        newValue = [...currentValues, optionValue];
      }
    } else {
      newValue = optionValue;
      setIsOpen(false);
    }
    
    setSelectedValue(newValue);
    onChange?.(newValue);
  };
  
  // 處理觸發器點擊
  const handleTriggerClick = () => {
    if (disabled) return;
    
    if (!isOpen) {
      onFocus?.();
    }
    
    setIsOpen(!isOpen);
  };
  
  // 獲取顯示文字
  const getDisplayText = () => {
    if (multiple && Array.isArray(selectedValue)) {
      if (selectedValue.length === 0) return placeholder;
      if (selectedValue.length === 1) {
        const option = options.find(opt => opt.value === selectedValue[0]);
        return option?.label || selectedValue[0];
      }
      return `已選擇 ${selectedValue.length} 項`;
    }
    
    if (!selectedValue && selectedValue !== 0) return placeholder;
    
    const option = options.find(opt => opt.value === selectedValue);
    return option?.label || selectedValue;
  };
  
  // 檢查選項是否被選中
  const isOptionSelected = (optionValue: string | number) => {
    if (multiple && Array.isArray(selectedValue)) {
      return selectedValue.includes(optionValue);
    }
    return selectedValue === optionValue;
  };
  
  // 按組分組選項
  const groupedOptions = options.reduce((groups, option) => {
    const group = option.group || 'default';
    if (!groups[group]) {
      groups[group] = [];
    }
    groups[group].push(option);
    return groups;
  }, {} as Record<string, SelectOption[]>);
  
  return (
    <SelectContainer ref={containerRef} fullWidth={fullWidth} className={className}>
      {label && (
        <SelectLabel theme={theme} required={required} htmlFor={id}>
          {label}
        </SelectLabel>
      )}
      
      <SelectTrigger
        theme={theme}
        size={size}
        hasError={!!error}
        disabled={disabled}
        open={isOpen}
        onClick={handleTriggerClick}
        id={id}
        name={name}
      >
        <SelectValue 
          theme={theme} 
          placeholder={!selectedValue && selectedValue !== 0}
        >
          {getDisplayText()}
        </SelectValue>
        
        <SelectArrow theme={theme} open={isOpen}>
          <svg viewBox="0 0 16 16" fill="currentColor">
            <path d="M4 6l4 4 4-4H4z" />
          </svg>
        </SelectArrow>
      </SelectTrigger>
      
      <SelectDropdown
        theme={theme}
        open={isOpen}
        maxHeight={maxHeight}
      >
        {Object.entries(groupedOptions).map(([groupName, groupOptions]) => (
          <React.Fragment key={groupName}>
            {groupName !== 'default' && (
              <SelectGroup theme={theme}>
                {groupName}
              </SelectGroup>
            )}
            
            {groupOptions.map((option) => (
              <SelectOption
                key={option.value}
                theme={theme}
                selected={isOptionSelected(option.value)}
                disabled={option.disabled}
                onClick={() => !option.disabled && handleOptionSelect(option.value)}
              >
                {option.label}
              </SelectOption>
            ))}
          </React.Fragment>
        ))}
      </SelectDropdown>
      
      {error && (
        <ErrorMessage theme={theme}>
          {error}
        </ErrorMessage>
      )}
    </SelectContainer>
  );
};

export default Select;