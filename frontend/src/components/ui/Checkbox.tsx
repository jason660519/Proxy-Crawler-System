/**
 * 複選框組件 - VS Code 風格的多選控制元件
 * 提供單選和多選功能，支持不確定狀態和自定義樣式
 */

import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 複選框容器
const CheckboxContainer = styled.label<{
  theme: 'light' | 'dark';
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
}>`
  display: inline-flex;
  align-items: flex-start;
  gap: ${spacing.sm};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.disabled ? 0.6 : 1};
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          font-size: 12px;
          line-height: 1.4;
        `;
      case 'large':
        return `
          font-size: 16px;
          line-height: 1.5;
        `;
      default:
        return `
          font-size: 14px;
          line-height: 1.5;
        `;
    }
  }}
`;

// 隱藏的原生 input
const HiddenInput = styled.input`
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
`;

// 複選框外觀
const CheckboxBox = styled.div<{
  theme: 'light' | 'dark';
  checked: boolean;
  indeterminate: boolean;
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error';
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  border-radius: ${borderRadius.sm};
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 14px;
          height: 14px;
          margin-top: 1px;
        `;
      case 'large':
        return `
          width: 20px;
          height: 20px;
          margin-top: 2px;
        `;
      default:
        return `
          width: 16px;
          height: 16px;
          margin-top: 2px;
        `;
    }
  }}
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    if (props.checked || props.indeterminate) {
      switch (props.variant) {
        case 'primary':
          return `
            background-color: ${colors.accent.primary};
            border: 1px solid ${colors.accent.primary};
          `;
        case 'success':
          return `
            background-color: ${colors.status.success};
            border: 1px solid ${colors.status.success};
          `;
        case 'warning':
          return `
            background-color: ${colors.status.warning};
            border: 1px solid ${colors.status.warning};
          `;
        case 'error':
          return `
            background-color: ${colors.status.error};
            border: 1px solid ${colors.status.error};
          `;
        default:
          return `
            background-color: ${colors.accent.primary};
            border: 1px solid ${colors.accent.primary};
          `;
      }
    } else {
      return `
        background-color: ${colors.background.primary};
        border: 1px solid ${colors.border.primary};
      `;
    }
  }}
  
  &:hover {
    ${props => {
      if (props.disabled) return '';
      const colors = getThemeColors(props.theme);
      
      if (props.checked || props.indeterminate) {
        switch (props.variant) {
          case 'primary':
            return `background-color: ${colors.accent.hover};`;
          case 'success':
            return `filter: brightness(1.1);`;
          case 'warning':
            return `filter: brightness(1.1);`;
          case 'error':
            return `filter: brightness(1.1);`;
          default:
            return `background-color: ${colors.accent.hover};`;
        }
      } else {
        return `
          border-color: ${colors.border.hover};
          background-color: ${colors.background.hover};
        `;
      }
    }}
  }
  
  &:focus-within {
    outline: 2px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: 2px;
  }
`;

// 勾選標記
const CheckIcon = styled.svg<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  visible: boolean;
}>`
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 8px;
          height: 8px;
        `;
      case 'large':
        return `
          width: 12px;
          height: 12px;
        `;
      default:
        return `
          width: 10px;
          height: 10px;
        `;
    }
  }}
  
  fill: ${props => getThemeColors(props.theme).text.inverse};
  opacity: ${props => props.visible ? 1 : 0};
  transform: ${props => props.visible ? 'scale(1)' : 'scale(0.5)'};
  transition: ${transitions.fast};
`;

// 不確定狀態標記
const IndeterminateIcon = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  visible: boolean;
}>`
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 6px;
          height: 2px;
        `;
      case 'large':
        return `
          width: 10px;
          height: 2px;
        `;
      default:
        return `
          width: 8px;
          height: 2px;
        `;
    }
  }}
  
  background-color: ${props => getThemeColors(props.theme).text.inverse};
  border-radius: ${borderRadius.xs};
  opacity: ${props => props.visible ? 1 : 0};
  transform: ${props => props.visible ? 'scale(1)' : 'scale(0.5)'};
  transition: ${transitions.fast};
`;

// 複選框標籤
const CheckboxLabel = styled.div<{
  theme: 'light' | 'dark';
}>`
  color: ${props => getThemeColors(props.theme).text.primary};
  user-select: none;
  flex: 1;
`;

// 複選框描述
const CheckboxDescription = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  color: ${props => getThemeColors(props.theme).text.secondary};
  margin-top: ${spacing.xs};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `font-size: 11px;`;
      case 'large':
        return `font-size: 14px;`;
      default:
        return `font-size: 12px;`;
    }
  }}
`;

// 複選框組件介面
export interface CheckboxProps {
  theme: 'light' | 'dark';
  checked?: boolean;
  defaultChecked?: boolean;
  indeterminate?: boolean;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  label?: React.ReactNode;
  description?: React.ReactNode;
  value?: string;
  onChange?: (checked: boolean, value?: string) => void;
  className?: string;
  id?: string;
}

/**
 * 複選框組件
 * 用於多選狀態控制
 */
export const Checkbox: React.FC<CheckboxProps> = ({
  theme,
  checked: controlledChecked,
  defaultChecked = false,
  indeterminate = false,
  disabled = false,
  size = 'medium',
  variant = 'default',
  label,
  description,
  value,
  onChange,
  className,
  id
}) => {
  const [internalChecked, setInternalChecked] = useState(defaultChecked);
  
  // 判斷是否為受控組件
  const isControlled = controlledChecked !== undefined;
  const checked = isControlled ? controlledChecked : internalChecked;
  
  // 處理狀態變更
  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    
    const newChecked = event.target.checked;
    
    if (!isControlled) {
      setInternalChecked(newChecked);
    }
    
    onChange?.(newChecked, value);
  }, [disabled, isControlled, onChange, value]);
  
  return (
    <div className={className}>
      <CheckboxContainer
        theme={theme}
        disabled={disabled}
        size={size}
      >
        <HiddenInput
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={handleChange}
          value={value}
          id={id}
        />
        
        <CheckboxBox
          theme={theme}
          checked={checked}
          indeterminate={indeterminate}
          disabled={disabled}
          size={size}
          variant={variant}
        >
          <CheckIcon
            theme={theme}
            size={size}
            visible={checked && !indeterminate}
            viewBox="0 0 16 16"
          >
            <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
          </CheckIcon>
          
          <IndeterminateIcon
            theme={theme}
            size={size}
            visible={indeterminate}
          />
        </CheckboxBox>
        
        {label && (
          <CheckboxLabel theme={theme}>
            {label}
          </CheckboxLabel>
        )}
      </CheckboxContainer>
      
      {description && (
        <CheckboxDescription theme={theme} size={size}>
          {description}
        </CheckboxDescription>
      )}
    </div>
  );
};

// 複選框組合容器
const CheckboxGroupContainer = styled.div<{
  direction: 'horizontal' | 'vertical';
}>`
  display: flex;
  flex-direction: ${props => props.direction === 'vertical' ? 'column' : 'row'};
  gap: ${props => props.direction === 'vertical' ? spacing.md : spacing.lg};
  align-items: ${props => props.direction === 'vertical' ? 'flex-start' : 'center'};
  flex-wrap: wrap;
`;

// 複選框選項介面
export interface CheckboxOption {
  label: React.ReactNode;
  value: string;
  disabled?: boolean;
  description?: React.ReactNode;
}

// 複選框組合組件介面
export interface CheckboxGroupProps {
  theme: 'light' | 'dark';
  options: CheckboxOption[];
  value?: string[];
  defaultValue?: string[];
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  direction?: 'horizontal' | 'vertical';
  onChange?: (values: string[]) => void;
  className?: string;
}

/**
 * 複選框組合組件
 * 用於管理多個複選框的狀態
 */
export const CheckboxGroup: React.FC<CheckboxGroupProps> = ({
  theme,
  options,
  value: controlledValue,
  defaultValue = [],
  disabled = false,
  size = 'medium',
  variant = 'default',
  direction = 'vertical',
  onChange,
  className
}) => {
  const [internalValue, setInternalValue] = useState<string[]>(defaultValue);
  
  // 判斷是否為受控組件
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;
  
  // 處理選項變更
  const handleOptionChange = useCallback((checked: boolean, optionValue: string) => {
    let newValue: string[];
    
    if (checked) {
      newValue = [...value, optionValue];
    } else {
      newValue = value.filter(v => v !== optionValue);
    }
    
    if (!isControlled) {
      setInternalValue(newValue);
    }
    
    onChange?.(newValue);
  }, [value, isControlled, onChange]);
  
  return (
    <CheckboxGroupContainer
      direction={direction}
      className={className}
    >
      {options.map((option) => (
        <Checkbox
          key={option.value}
          theme={theme}
          checked={value.includes(option.value)}
          disabled={disabled || option.disabled}
          size={size}
          variant={variant}
          label={option.label}
          description={option.description}
          value={option.value}
          onChange={handleOptionChange}
        />
      ))}
    </CheckboxGroupContainer>
  );
};

// 全選複選框組件介面
export interface SelectAllCheckboxProps {
  theme: 'light' | 'dark';
  options: CheckboxOption[];
  value?: string[];
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  label?: React.ReactNode;
  onChange?: (values: string[]) => void;
  className?: string;
}

/**
 * 全選複選框組件
 * 提供全選/取消全選功能
 */
export const SelectAllCheckbox: React.FC<SelectAllCheckboxProps> = ({
  theme,
  options,
  value = [],
  disabled = false,
  size = 'medium',
  variant = 'default',
  label = '全選',
  onChange,
  className
}) => {
  const enabledOptions = options.filter(option => !option.disabled);
  const enabledValues = enabledOptions.map(option => option.value);
  
  const checkedCount = enabledValues.filter(val => value.includes(val)).length;
  const isAllChecked = checkedCount === enabledValues.length && enabledValues.length > 0;
  const isIndeterminate = checkedCount > 0 && checkedCount < enabledValues.length;
  
  const handleChange = useCallback((checked: boolean) => {
    if (checked) {
      // 全選：添加所有未選中的啟用選項
      const newValue = [...new Set([...value, ...enabledValues])];
      onChange?.(newValue);
    } else {
      // 取消全選：移除所有啟用選項
      const newValue = value.filter(val => !enabledValues.includes(val));
      onChange?.(newValue);
    }
  }, [value, enabledValues, onChange]);
  
  return (
    <Checkbox
      theme={theme}
      checked={isAllChecked}
      indeterminate={isIndeterminate}
      disabled={disabled || enabledOptions.length === 0}
      size={size}
      variant={variant}
      label={label}
      onChange={handleChange}
      className={className}
    />
  );
};

export default Checkbox;