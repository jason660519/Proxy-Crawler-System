/**
 * 單選框組件 - VS Code 風格的單選控制元件
 * 提供單選功能，支持組合使用和自定義樣式
 */

import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 單選框容器
const RadioContainer = styled.label<{
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

// 單選框外觀
const RadioBox = styled.div<{
  theme: 'light' | 'dark';
  checked: boolean;
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error';
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  border-radius: 50%;
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
    
    if (props.checked) {
      switch (props.variant) {
        case 'primary':
          return `
            background-color: ${colors.background.primary};
            border: 2px solid ${colors.accent.primary};
          `;
        case 'success':
          return `
            background-color: ${colors.background.primary};
            border: 2px solid ${colors.status.success};
          `;
        case 'warning':
          return `
            background-color: ${colors.background.primary};
            border: 2px solid ${colors.status.warning};
          `;
        case 'error':
          return `
            background-color: ${colors.background.primary};
            border: 2px solid ${colors.status.error};
          `;
        default:
          return `
            background-color: ${colors.background.primary};
            border: 2px solid ${colors.accent.primary};
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
      
      if (props.checked) {
        switch (props.variant) {
          case 'primary':
            return `border-color: ${colors.accent.hover};`;
          case 'success':
            return `filter: brightness(1.1);`;
          case 'warning':
            return `filter: brightness(1.1);`;
          case 'error':
            return `filter: brightness(1.1);`;
          default:
            return `border-color: ${colors.accent.hover};`;
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

// 選中標記
const RadioDot = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error';
  visible: boolean;
}>`
  border-radius: 50%;
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 6px;
          height: 6px;
        `;
      case 'large':
        return `
          width: 10px;
          height: 10px;
        `;
      default:
        return `
          width: 8px;
          height: 8px;
        `;
    }
  }}
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    switch (props.variant) {
      case 'primary':
        return `background-color: ${colors.accent.primary};`;
      case 'success':
        return `background-color: ${colors.status.success};`;
      case 'warning':
        return `background-color: ${colors.status.warning};`;
      case 'error':
        return `background-color: ${colors.status.error};`;
      default:
        return `background-color: ${colors.accent.primary};`;
    }
  }}
  
  opacity: ${props => props.visible ? 1 : 0};
  transform: ${props => props.visible ? 'scale(1)' : 'scale(0.5)'};
`;

// 單選框標籤
const RadioLabel = styled.div<{
  theme: 'light' | 'dark';
}>`
  color: ${props => getThemeColors(props.theme).text.primary};
  user-select: none;
  flex: 1;
`;

// 單選框描述
const RadioDescription = styled.div<{
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

// 單選框組件介面
export interface RadioProps {
  theme: 'light' | 'dark';
  checked?: boolean;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  label?: React.ReactNode;
  description?: React.ReactNode;
  value?: string;
  name?: string;
  onChange?: (value: string) => void;
  className?: string;
  id?: string;
}

/**
 * 單選框組件
 * 用於單選狀態控制
 */
export const Radio: React.FC<RadioProps> = ({
  theme,
  checked = false,
  disabled = false,
  size = 'medium',
  variant = 'default',
  label,
  description,
  value = '',
  name,
  onChange,
  className,
  id
}) => {
  // 處理狀態變更
  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    
    onChange?.(event.target.value);
  }, [disabled, onChange]);
  
  return (
    <div className={className}>
      <RadioContainer
        theme={theme}
        disabled={disabled}
        size={size}
      >
        <HiddenInput
          type="radio"
          checked={checked}
          disabled={disabled}
          onChange={handleChange}
          value={value}
          name={name}
          id={id}
        />
        
        <RadioBox
          theme={theme}
          checked={checked}
          disabled={disabled}
          size={size}
          variant={variant}
        >
          <RadioDot
            theme={theme}
            size={size}
            variant={variant}
            visible={checked}
          />
        </RadioBox>
        
        {label && (
          <RadioLabel theme={theme}>
            {label}
          </RadioLabel>
        )}
      </RadioContainer>
      
      {description && (
        <RadioDescription theme={theme} size={size}>
          {description}
        </RadioDescription>
      )}
    </div>
  );
};

// 單選框組合容器
const RadioGroupContainer = styled.div<{
  direction: 'horizontal' | 'vertical';
}>`
  display: flex;
  flex-direction: ${props => props.direction === 'vertical' ? 'column' : 'row'};
  gap: ${props => props.direction === 'vertical' ? spacing.md : spacing.lg};
  align-items: ${props => props.direction === 'vertical' ? 'flex-start' : 'center'};
  flex-wrap: wrap;
`;

// 單選框選項介面
export interface RadioOption {
  label: React.ReactNode;
  value: string;
  disabled?: boolean;
  description?: React.ReactNode;
}

// 單選框組合組件介面
export interface RadioGroupProps {
  theme: 'light' | 'dark';
  options: RadioOption[];
  value?: string;
  defaultValue?: string;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  direction?: 'horizontal' | 'vertical';
  name?: string;
  onChange?: (value: string) => void;
  className?: string;
}

/**
 * 單選框組合組件
 * 用於管理多個單選框的狀態
 */
export const RadioGroup: React.FC<RadioGroupProps> = ({
  theme,
  options,
  value: controlledValue,
  defaultValue = '',
  disabled = false,
  size = 'medium',
  variant = 'default',
  direction = 'vertical',
  name,
  onChange,
  className
}) => {
  const [internalValue, setInternalValue] = useState<string>(defaultValue);
  
  // 判斷是否為受控組件
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;
  
  // 生成唯一的 name 屬性
  const groupName = name || `radio-group-${Math.random().toString(36).substr(2, 9)}`;
  
  // 處理選項變更
  const handleOptionChange = useCallback((optionValue: string) => {
    if (!isControlled) {
      setInternalValue(optionValue);
    }
    
    onChange?.(optionValue);
  }, [isControlled, onChange]);
  
  return (
    <RadioGroupContainer
      direction={direction}
      className={className}
    >
      {options.map((option, index) => (
        <Radio
          key={option.value}
          theme={theme}
          checked={value === option.value}
          disabled={disabled || option.disabled}
          size={size}
          variant={variant}
          label={option.label}
          description={option.description}
          value={option.value}
          name={groupName}
          onChange={handleOptionChange}
          id={`${groupName}-${index}`}
        />
      ))}
    </RadioGroupContainer>
  );
};

// 卡片式單選框容器
const RadioCardContainer = styled.div<{
  theme: 'light' | 'dark';
  checked: boolean;
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
}>`
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: ${spacing.md};
  
  padding: ${props => {
    switch (props.size) {
      case 'small': return spacing.sm;
      case 'large': return spacing.lg;
      default: return spacing.md;
    }
  }};
  
  background-color: ${props => {
    const colors = getThemeColors(props.theme);
    return props.checked ? colors.background.hover : colors.background.primary;
  }};
  
  border: 1px solid ${props => {
    const colors = getThemeColors(props.theme);
    return props.checked ? colors.accent.primary : colors.border.primary;
  }};
  
  border-radius: ${borderRadius.md};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.disabled ? 0.6 : 1};
  transition: ${transitions.fast};
  
  &:hover {
    ${props => {
      if (props.disabled) return '';
      const colors = getThemeColors(props.theme);
      
      return `
        border-color: ${props.checked ? colors.accent.hover : colors.border.hover};
        background-color: ${colors.background.hover};
      `;
    }}
  }
`;

// 卡片式單選框內容
const RadioCardContent = styled.div`
  flex: 1;
`;

// 卡片式單選框組件介面
export interface RadioCardProps extends Omit<RadioProps, 'label'> {
  title: React.ReactNode;
  content?: React.ReactNode;
}

/**
 * 卡片式單選框組件
 * 提供更豐富的視覺呈現
 */
export const RadioCard: React.FC<RadioCardProps> = ({
  theme,
  checked = false,
  disabled = false,
  size = 'medium',
  variant = 'default',
  title,
  content,
  description,
  value = '',
  name,
  onChange,
  className,
  id
}) => {
  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    onChange?.(event.target.value);
  }, [disabled, onChange]);
  
  const handleCardClick = useCallback(() => {
    if (disabled) return;
    onChange?.(value);
  }, [disabled, onChange, value]);
  
  return (
    <RadioCardContainer
      theme={theme}
      checked={checked}
      disabled={disabled}
      size={size}
      onClick={handleCardClick}
      className={className}
    >
      <HiddenInput
        type="radio"
        checked={checked}
        disabled={disabled}
        onChange={handleChange}
        value={value}
        name={name}
        id={id}
      />
      
      <RadioBox
        theme={theme}
        checked={checked}
        disabled={disabled}
        size={size}
        variant={variant}
      >
        <RadioDot
          theme={theme}
          size={size}
          variant={variant}
          visible={checked}
        />
      </RadioBox>
      
      <RadioCardContent>
        <RadioLabel theme={theme}>
          {title}
        </RadioLabel>
        
        {content && (
          <div style={{ marginTop: spacing.xs }}>
            {content}
          </div>
        )}
        
        {description && (
          <RadioDescription theme={theme} size={size}>
            {description}
          </RadioDescription>
        )}
      </RadioCardContent>
    </RadioCardContainer>
  );
};

export default Radio;