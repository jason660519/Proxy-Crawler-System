/**
 * 輸入框組件 - VS Code 風格的表單輸入元素
 * 提供多種類型和狀態的輸入框
 */

import React, { forwardRef } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 輸入框容器
const InputContainer = styled.div<{ fullWidth?: boolean }>`
  display: inline-flex;
  flex-direction: column;
  gap: ${spacing.xs};
  ${props => props.fullWidth && 'width: 100%;'}
`;

// 輸入框標籤
const InputLabel = styled.label<{ theme: 'light' | 'dark'; required?: boolean }>`
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

// 輸入框包裝器
const InputWrapper = styled.div<{ 
  theme: 'light' | 'dark';
  hasError?: boolean;
  disabled?: boolean;
  focused?: boolean;
}>`
  position: relative;
  display: flex;
  align-items: center;
  background-color: ${props => getThemeColors(props.theme).input.background};
  border: 1px solid ${props => {
    const colors = getThemeColors(props.theme);
    if (props.hasError) return colors.status.error;
    if (props.focused) return colors.border.focus;
    return colors.input.border;
  }};
  border-radius: ${borderRadius.sm};
  transition: all ${transitions.fast} ease;
  
  &:hover:not(:focus-within) {
    border-color: ${props => getThemeColors(props.theme).input.borderHover};
  }
  
  &:focus-within {
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

// 基礎輸入框
const BaseInput = styled.input<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  hasPrefix?: boolean;
  hasSuffix?: boolean;
}>`
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: ${props => getThemeColors(props.theme).input.foreground};
  font-size: 12px;
  font-family: inherit;
  
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
  
  ${props => props.hasPrefix && `padding-left: ${spacing.xs};`}
  ${props => props.hasSuffix && `padding-right: ${spacing.xs};`}
  
  &::placeholder {
    color: ${props => getThemeColors(props.theme).input.placeholder};
  }
  
  &:disabled {
    cursor: not-allowed;
  }
  
  /* 移除自動填充的背景色 */
  &:-webkit-autofill,
  &:-webkit-autofill:hover,
  &:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px ${props => getThemeColors(props.theme).input.background} inset;
    -webkit-text-fill-color: ${props => getThemeColors(props.theme).input.foreground};
    transition: background-color 5000s ease-in-out 0s;
  }
`;

// 前綴/後綴容器
const InputAffix = styled.div<{ theme: 'light' | 'dark'; position: 'prefix' | 'suffix' }>`
  display: flex;
  align-items: center;
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-size: 12px;
  
  ${props => props.position === 'prefix' && `
    padding-left: ${spacing.sm};
    padding-right: ${spacing.xs};
  `}
  
  ${props => props.position === 'suffix' && `
    padding-left: ${spacing.xs};
    padding-right: ${spacing.sm};
  `}
  
  svg {
    width: 14px;
    height: 14px;
  }
`;

// 錯誤訊息
const ErrorMessage = styled.div<{ theme: 'light' | 'dark' }>`
  font-size: 11px;
  color: ${props => getThemeColors(props.theme).status.error};
  margin-top: ${spacing.xs};
`;

// 幫助文字
const HelpText = styled.div<{ theme: 'light' | 'dark' }>`
  font-size: 11px;
  color: ${props => getThemeColors(props.theme).text.secondary};
  margin-top: ${spacing.xs};
`;

// 輸入框組件介面
export interface InputProps {
  theme: 'light' | 'dark';
  type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'url' | 'tel';
  size?: 'small' | 'medium' | 'large';
  label?: string;
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  disabled?: boolean;
  required?: boolean;
  readOnly?: boolean;
  fullWidth?: boolean;
  error?: string;
  helpText?: string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  className?: string;
  id?: string;
  name?: string;
  autoComplete?: string;
  autoFocus?: boolean;
  maxLength?: number;
  minLength?: number;
  pattern?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyUp?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyPress?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
}

/**
 * 輸入框組件
 * 提供統一的表單輸入樣式
 */
export const Input = forwardRef<HTMLInputElement, InputProps>((
  {
    theme,
    type = 'text',
    size = 'medium',
    label,
    placeholder,
    value,
    defaultValue,
    disabled = false,
    required = false,
    readOnly = false,
    fullWidth = false,
    error,
    helpText,
    prefix,
    suffix,
    className,
    id,
    name,
    autoComplete,
    autoFocus = false,
    maxLength,
    minLength,
    pattern,
    onChange,
    onBlur,
    onFocus,
    onKeyDown,
    onKeyUp,
    onKeyPress
  },
  ref
) => {
  const [focused, setFocused] = React.useState(false);
  
  const handleFocus = (event: React.FocusEvent<HTMLInputElement>) => {
    setFocused(true);
    onFocus?.(event);
  };
  
  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    setFocused(false);
    onBlur?.(event);
  };
  
  return (
    <InputContainer fullWidth={fullWidth} className={className}>
      {label && (
        <InputLabel theme={theme} required={required} htmlFor={id}>
          {label}
        </InputLabel>
      )}
      
      <InputWrapper
        theme={theme}
        hasError={!!error}
        disabled={disabled}
        focused={focused}
      >
        {prefix && (
          <InputAffix theme={theme} position="prefix">
            {prefix}
          </InputAffix>
        )}
        
        <BaseInput
          ref={ref}
          theme={theme}
          type={type}
          size={size}
          hasPrefix={!!prefix}
          hasSuffix={!!suffix}
          placeholder={placeholder}
          value={value}
          defaultValue={defaultValue}
          disabled={disabled}
          required={required}
          readOnly={readOnly}
          id={id}
          name={name}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
          maxLength={maxLength}
          minLength={minLength}
          pattern={pattern}
          onChange={onChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={onKeyDown}
          onKeyUp={onKeyUp}
          onKeyPress={onKeyPress}
        />
        
        {suffix && (
          <InputAffix theme={theme} position="suffix">
            {suffix}
          </InputAffix>
        )}
      </InputWrapper>
      
      {error && (
        <ErrorMessage theme={theme}>
          {error}
        </ErrorMessage>
      )}
      
      {helpText && !error && (
        <HelpText theme={theme}>
          {helpText}
        </HelpText>
      )}
    </InputContainer>
  );
});

Input.displayName = 'Input';

export default Input;