/**
 * 開關組件 - VS Code 風格的切換開關
 * 提供布爾狀態切換功能，支持多種尺寸和樣式
 */

import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 開關容器
const SwitchContainer = styled.label<{
  theme: 'light' | 'dark';
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
}>`
  display: inline-flex;
  align-items: center;
  gap: ${spacing.sm};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.disabled ? 0.6 : 1};
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          font-size: 12px;
        `;
      case 'large':
        return `
          font-size: 16px;
        `;
      default:
        return `
          font-size: 14px;
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

// 開關軌道
const SwitchTrack = styled.div<{
  theme: 'light' | 'dark';
  checked: boolean;
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error';
}>`
  position: relative;
  display: inline-block;
  
  border-radius: ${borderRadius.full};
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 32px;
          height: 18px;
        `;
      case 'large':
        return `
          width: 48px;
          height: 26px;
        `;
      default:
        return `
          width: 40px;
          height: 22px;
        `;
    }
  }}
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    if (props.checked) {
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
    } else {
      return `background-color: ${colors.background.secondary};`;
    }
  }}
  
  border: 1px solid ${props => {
    const colors = getThemeColors(props.theme);
    return props.checked ? 'transparent' : colors.border.primary;
  }};
  
  &:hover {
    ${props => {
      if (props.disabled) return '';
      const colors = getThemeColors(props.theme);
      
      if (props.checked) {
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
        return `background-color: ${colors.background.hover};`;
      }
    }}
  }
  
  &:focus-within {
    outline: 2px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: 2px;
  }
`;

// 開關滑塊
const SwitchThumb = styled.div<{
  theme: 'light' | 'dark';
  checked: boolean;
  size: 'small' | 'medium' | 'large';
}>`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  
  background-color: ${props => getThemeColors(props.theme).background.primary};
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 14px;
          height: 14px;
          left: ${props.checked ? '16px' : '2px'};
        `;
      case 'large':
        return `
          width: 20px;
          height: 20px;
          left: ${props.checked ? '25px' : '3px'};
        `;
      default:
        return `
          width: 16px;
          height: 16px;
          left: ${props.checked ? '21px' : '3px'};
        `;
    }
  }}
`;

// 開關標籤
const SwitchLabel = styled.span<{
  theme: 'light' | 'dark';
  position: 'left' | 'right';
}>`
  color: ${props => getThemeColors(props.theme).text.primary};
  user-select: none;
  order: ${props => props.position === 'left' ? -1 : 1};
`;

// 開關描述
const SwitchDescription = styled.div<{
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

// 開關組件介面
export interface SwitchProps {
  theme: 'light' | 'dark';
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  label?: React.ReactNode;
  labelPosition?: 'left' | 'right';
  description?: React.ReactNode;
  onChange?: (checked: boolean) => void;
  className?: string;
  id?: string;
}

/**
 * 開關組件
 * 用於切換布爾狀態
 */
export const Switch: React.FC<SwitchProps> = ({
  theme,
  checked: controlledChecked,
  defaultChecked = false,
  disabled = false,
  size = 'medium',
  variant = 'default',
  label,
  labelPosition = 'right',
  description,
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
    
    onChange?.(newChecked);
  }, [disabled, isControlled, onChange]);
  
  return (
    <div className={className}>
      <SwitchContainer
        theme={theme}
        disabled={disabled}
        size={size}
      >
        <HiddenInput
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={handleChange}
          id={id}
        />
        
        {label && labelPosition === 'left' && (
          <SwitchLabel theme={theme} position="left">
            {label}
          </SwitchLabel>
        )}
        
        <SwitchTrack
          theme={theme}
          checked={checked}
          disabled={disabled}
          size={size}
          variant={variant}
        >
          <SwitchThumb
            theme={theme}
            checked={checked}
            size={size}
          />
        </SwitchTrack>
        
        {label && labelPosition === 'right' && (
          <SwitchLabel theme={theme} position="right">
            {label}
          </SwitchLabel>
        )}
      </SwitchContainer>
      
      {description && (
        <SwitchDescription theme={theme} size={size}>
          {description}
        </SwitchDescription>
      )}
    </div>
  );
};

// 開關組合容器
const SwitchGroupContainer = styled.div<{
  direction: 'horizontal' | 'vertical';
}>`
  display: flex;
  flex-direction: ${props => props.direction === 'vertical' ? 'column' : 'row'};
  gap: ${props => props.direction === 'vertical' ? spacing.md : spacing.lg};
  align-items: ${props => props.direction === 'vertical' ? 'flex-start' : 'center'};
  flex-wrap: wrap;
`;

// 開關組合組件介面
export interface SwitchGroupProps {
  direction?: 'horizontal' | 'vertical';
  children: React.ReactNode;
  className?: string;
}

/**
 * 開關組合組件
 * 用於組織多個開關的布局
 */
export const SwitchGroup: React.FC<SwitchGroupProps> = ({
  direction = 'vertical',
  children,
  className
}) => {
  return (
    <SwitchGroupContainer
      direction={direction}
      className={className}
    >
      {children}
    </SwitchGroupContainer>
  );
};

// 帶圖標的開關組件介面
export interface IconSwitchProps extends Omit<SwitchProps, 'label'> {
  checkedIcon?: React.ReactNode;
  uncheckedIcon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

/**
 * 帶圖標的開關組件
 * 在開關旁顯示不同狀態的圖標
 */
export const IconSwitch: React.FC<IconSwitchProps> = ({
  theme,
  checked: controlledChecked,
  defaultChecked = false,
  disabled = false,
  size = 'medium',
  variant = 'default',
  checkedIcon,
  uncheckedIcon,
  iconPosition = 'right',
  description,
  onChange,
  className,
  id
}) => {
  const [internalChecked, setInternalChecked] = useState(defaultChecked);
  
  const isControlled = controlledChecked !== undefined;
  const checked = isControlled ? controlledChecked : internalChecked;
  
  const handleChange = useCallback((newChecked: boolean) => {
    if (!isControlled) {
      setInternalChecked(newChecked);
    }
    onChange?.(newChecked);
  }, [isControlled, onChange]);
  
  const currentIcon = checked ? checkedIcon : uncheckedIcon;
  
  return (
    <Switch
      theme={theme}
      checked={checked}
      disabled={disabled}
      size={size}
      variant={variant}
      label={currentIcon}
      labelPosition={iconPosition}
      description={description}
      onChange={handleChange}
      className={className}
      id={id}
    />
  );
};

export default Switch;