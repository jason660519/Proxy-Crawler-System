/**
 * 滑動條組件 - VS Code 風格的數值範圍選擇控制元件
 * 提供單值和範圍選擇功能，支持自定義樣式和標記
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 滑動條容器
const SliderContainer = styled.div<{
  theme: 'light' | 'dark';
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
}>`
  position: relative;
  width: 100%;
  opacity: ${props => props.disabled ? 0.6 : 1};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          padding: ${spacing.sm} 0;
        `;
      case 'large':
        return `
          padding: ${spacing.lg} 0;
        `;
      default:
        return `
          padding: ${spacing.md} 0;
        `;
    }
  }}
`;

// 滑動條軌道
const SliderTrack = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  position: relative;
  width: 100%;
  background-color: ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.full};
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `height: 4px;`;
      case 'large':
        return `height: 8px;`;
      default:
        return `height: 6px;`;
    }
  }}
`;

// 滑動條填充區域
const SliderFill = styled.div<{
  theme: 'light' | 'dark';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error';
  size: 'small' | 'medium' | 'large';
  left: number;
  width: number;
}>`
  position: absolute;
  top: 0;
  left: ${props => props.left}%;
  width: ${props => props.width}%;
  height: 100%;
  border-radius: ${borderRadius.full};
  transition: ${transitions.fast};
  
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
`;

// 滑動條手柄
const SliderThumb = styled.div<{
  theme: 'light' | 'dark';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error';
  size: 'small' | 'medium' | 'large';
  position: number;
  active?: boolean;
  disabled?: boolean;
}>`
  position: absolute;
  top: 50%;
  left: ${props => props.position}%;
  transform: translate(-50%, -50%);
  
  background-color: ${props => getThemeColors(props.theme).background.primary};
  border-radius: 50%;
  cursor: ${props => props.disabled ? 'not-allowed' : 'grab'};
  transition: ${transitions.fast};
  z-index: 2;
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 14px;
          height: 14px;
        `;
      case 'large':
        return `
          width: 22px;
          height: 22px;
        `;
      default:
        return `
          width: 18px;
          height: 18px;
        `;
    }
  }}
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    switch (props.variant) {
      case 'primary':
        return `border: 2px solid ${colors.accent.primary};`;
      case 'success':
        return `border: 2px solid ${colors.status.success};`;
      case 'warning':
        return `border: 2px solid ${colors.status.warning};`;
      case 'error':
        return `border: 2px solid ${colors.status.error};`;
      default:
        return `border: 2px solid ${colors.accent.primary};`;
    }
  }}
  
  &:hover {
    ${props => {
      if (props.disabled) return '';
      
      return `
        transform: translate(-50%, -50%) scale(1.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      `;
    }}
  }
  
  &:active {
    cursor: grabbing;
    transform: translate(-50%, -50%) scale(1.15);
  }
  
  &:focus {
    outline: 2px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: 2px;
  }
  
  ${props => props.active && `
    transform: translate(-50%, -50%) scale(1.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  `}
`;

// 滑動條標記
const SliderMark = styled.div<{
  theme: 'light' | 'dark';
  position: number;
  active?: boolean;
}>`
  position: absolute;
  top: 50%;
  left: ${props => props.position}%;
  transform: translate(-50%, -50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background-color: ${props => {
    const colors = getThemeColors(props.theme);
    return props.active ? colors.accent.primary : colors.border.secondary;
  }};
  z-index: 1;
`;

// 滑動條標籤
const SliderLabel = styled.div<{
  theme: 'light' | 'dark';
  position: number;
  size: 'small' | 'medium' | 'large';
}>`
  position: absolute;
  top: 100%;
  left: ${props => props.position}%;
  transform: translateX(-50%);
  margin-top: ${spacing.xs};
  
  color: ${props => getThemeColors(props.theme).text.secondary};
  white-space: nowrap;
  user-select: none;
  
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

// 滑動條數值顯示
const SliderValue = styled.div<{
  theme: 'light' | 'dark';
  position: number;
  size: 'small' | 'medium' | 'large';
}>`
  position: absolute;
  bottom: 100%;
  left: ${props => props.position}%;
  transform: translateX(-50%);
  margin-bottom: ${spacing.xs};
  
  padding: ${spacing.xs} ${spacing.sm};
  background-color: ${props => getThemeColors(props.theme).background.tooltip};
  color: ${props => getThemeColors(props.theme).text.primary};
  border-radius: ${borderRadius.sm};
  white-space: nowrap;
  user-select: none;
  
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
  
  &::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: ${props => getThemeColors(props.theme).background.tooltip};
  }
`;

// 標記介面
export interface SliderMark {
  value: number;
  label?: React.ReactNode;
}

// 滑動條組件介面
export interface SliderProps {
  theme: 'light' | 'dark';
  value?: number;
  defaultValue?: number;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  marks?: SliderMark[];
  showValue?: boolean;
  formatValue?: (value: number) => string;
  onChange?: (value: number) => void;
  onChangeComplete?: (value: number) => void;
  className?: string;
}

/**
 * 滑動條組件
 * 用於數值範圍選擇
 */
export const Slider: React.FC<SliderProps> = ({
  theme,
  value: controlledValue,
  defaultValue = 0,
  min = 0,
  max = 100,
  step = 1,
  disabled = false,
  size = 'medium',
  variant = 'default',
  marks = [],
  showValue = false,
  formatValue = (value) => value.toString(),
  onChange,
  onChangeComplete,
  className
}) => {
  const [internalValue, setInternalValue] = useState<number>(defaultValue);
  const [isDragging, setIsDragging] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);
  
  // 判斷是否為受控組件
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;
  
  // 計算位置百分比
  const getPositionFromValue = useCallback((val: number) => {
    return ((val - min) / (max - min)) * 100;
  }, [min, max]);
  
  // 從位置計算數值
  const getValueFromPosition = useCallback((position: number) => {
    const percentage = Math.max(0, Math.min(100, position));
    const rawValue = min + (percentage / 100) * (max - min);
    return Math.round(rawValue / step) * step;
  }, [min, max, step]);
  
  // 處理數值變更
  const handleValueChange = useCallback((newValue: number) => {
    const clampedValue = Math.max(min, Math.min(max, newValue));
    
    if (!isControlled) {
      setInternalValue(clampedValue);
    }
    
    onChange?.(clampedValue);
  }, [isControlled, min, max, onChange]);
  
  // 處理滑鼠事件
  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    if (disabled || !trackRef.current) return;
    
    event.preventDefault();
    setIsDragging(true);
    
    const rect = trackRef.current.getBoundingClientRect();
    const position = ((event.clientX - rect.left) / rect.width) * 100;
    const newValue = getValueFromPosition(position);
    
    handleValueChange(newValue);
  }, [disabled, getValueFromPosition, handleValueChange]);
  
  // 處理滑鼠移動
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!isDragging || !trackRef.current) return;
    
    const rect = trackRef.current.getBoundingClientRect();
    const position = ((event.clientX - rect.left) / rect.width) * 100;
    const newValue = getValueFromPosition(position);
    
    handleValueChange(newValue);
  }, [isDragging, getValueFromPosition, handleValueChange]);
  
  // 處理滑鼠釋放
  const handleMouseUp = useCallback(() => {
    if (isDragging) {
      setIsDragging(false);
      onChangeComplete?.(value);
    }
  }, [isDragging, value, onChangeComplete]);
  
  // 處理鍵盤事件
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (disabled) return;
    
    let newValue = value;
    
    switch (event.key) {
      case 'ArrowLeft':
      case 'ArrowDown':
        newValue = Math.max(min, value - step);
        break;
      case 'ArrowRight':
      case 'ArrowUp':
        newValue = Math.min(max, value + step);
        break;
      case 'Home':
        newValue = min;
        break;
      case 'End':
        newValue = max;
        break;
      default:
        return;
    }
    
    event.preventDefault();
    handleValueChange(newValue);
    onChangeComplete?.(newValue);
  }, [disabled, value, min, max, step, handleValueChange, onChangeComplete]);
  
  // 綁定全域滑鼠事件
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);
  
  const position = getPositionFromValue(value);
  
  return (
    <SliderContainer
      theme={theme}
      disabled={disabled}
      size={size}
      className={className}
    >
      <SliderTrack
        ref={trackRef}
        theme={theme}
        size={size}
        onMouseDown={handleMouseDown}
      >
        <SliderFill
          theme={theme}
          variant={variant}
          size={size}
          left={0}
          width={position}
        />
        
        {marks.map((mark) => {
          const markPosition = getPositionFromValue(mark.value);
          return (
            <SliderMark
              key={mark.value}
              theme={theme}
              position={markPosition}
              active={mark.value <= value}
            />
          );
        })}
      </SliderTrack>
      
      <SliderThumb
        theme={theme}
        variant={variant}
        size={size}
        position={position}
        active={isDragging}
        disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onKeyDown={handleKeyDown}
      />
      
      {showValue && (
        <SliderValue
          theme={theme}
          position={position}
          size={size}
        >
          {formatValue(value)}
        </SliderValue>
      )}
      
      {marks.map((mark) => {
        if (!mark.label) return null;
        
        const markPosition = getPositionFromValue(mark.value);
        return (
          <SliderLabel
            key={`label-${mark.value}`}
            theme={theme}
            position={markPosition}
            size={size}
          >
            {mark.label}
          </SliderLabel>
        );
      })}
    </SliderContainer>
  );
};

// 範圍滑動條組件介面
export interface RangeSliderProps {
  theme: 'light' | 'dark';
  value?: [number, number];
  defaultValue?: [number, number];
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  marks?: SliderMark[];
  showValue?: boolean;
  formatValue?: (value: number) => string;
  onChange?: (value: [number, number]) => void;
  onChangeComplete?: (value: [number, number]) => void;
  className?: string;
}

/**
 * 範圍滑動條組件
 * 用於選擇數值範圍
 */
export const RangeSlider: React.FC<RangeSliderProps> = ({
  theme,
  value: controlledValue,
  defaultValue = [0, 100],
  min = 0,
  max = 100,
  step = 1,
  disabled = false,
  size = 'medium',
  variant = 'default',
  marks = [],
  showValue = false,
  formatValue = (value) => value.toString(),
  onChange,
  onChangeComplete,
  className
}) => {
  const [internalValue, setInternalValue] = useState<[number, number]>(defaultValue);
  const [activeThumb, setActiveThumb] = useState<number | null>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  
  // 判斷是否為受控組件
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;
  
  // 計算位置百分比
  const getPositionFromValue = useCallback((val: number) => {
    return ((val - min) / (max - min)) * 100;
  }, [min, max]);
  
  // 從位置計算數值
  const getValueFromPosition = useCallback((position: number) => {
    const percentage = Math.max(0, Math.min(100, position));
    const rawValue = min + (percentage / 100) * (max - min);
    return Math.round(rawValue / step) * step;
  }, [min, max, step]);
  
  // 處理數值變更
  const handleValueChange = useCallback((newValue: [number, number]) => {
    const clampedValue: [number, number] = [
      Math.max(min, Math.min(max, newValue[0])),
      Math.max(min, Math.min(max, newValue[1]))
    ];
    
    // 確保範圍順序正確
    if (clampedValue[0] > clampedValue[1]) {
      clampedValue.reverse();
    }
    
    if (!isControlled) {
      setInternalValue(clampedValue);
    }
    
    onChange?.(clampedValue);
  }, [isControlled, min, max, onChange]);
  
  // 處理滑鼠事件
  const handleMouseDown = useCallback((event: React.MouseEvent, thumbIndex?: number) => {
    if (disabled || !trackRef.current) return;
    
    event.preventDefault();
    
    const rect = trackRef.current.getBoundingClientRect();
    const position = ((event.clientX - rect.left) / rect.width) * 100;
    const newValue = getValueFromPosition(position);
    
    if (thumbIndex !== undefined) {
      setActiveThumb(thumbIndex);
      const updatedValue: [number, number] = [...value];
      updatedValue[thumbIndex] = newValue;
      handleValueChange(updatedValue);
    } else {
      // 點擊軌道時，移動最近的手柄
      const distances = value.map(val => Math.abs(getPositionFromValue(val) - position));
      const closestIndex = distances[0] <= distances[1] ? 0 : 1;
      
      setActiveThumb(closestIndex);
      const updatedValue: [number, number] = [...value];
      updatedValue[closestIndex] = newValue;
      handleValueChange(updatedValue);
    }
  }, [disabled, getValueFromPosition, handleValueChange, value, getPositionFromValue]);
  
  // 處理滑鼠移動
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (activeThumb === null || !trackRef.current) return;
    
    const rect = trackRef.current.getBoundingClientRect();
    const position = ((event.clientX - rect.left) / rect.width) * 100;
    const newValue = getValueFromPosition(position);
    
    const updatedValue: [number, number] = [...value];
    updatedValue[activeThumb] = newValue;
    handleValueChange(updatedValue);
  }, [activeThumb, getValueFromPosition, handleValueChange, value]);
  
  // 處理滑鼠釋放
  const handleMouseUp = useCallback(() => {
    if (activeThumb !== null) {
      setActiveThumb(null);
      onChangeComplete?.(value);
    }
  }, [activeThumb, value, onChangeComplete]);
  
  // 綁定全域滑鼠事件
  useEffect(() => {
    if (activeThumb !== null) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [activeThumb, handleMouseMove, handleMouseUp]);
  
  const leftPosition = getPositionFromValue(value[0]);
  const rightPosition = getPositionFromValue(value[1]);
  
  return (
    <SliderContainer
      theme={theme}
      disabled={disabled}
      size={size}
      className={className}
    >
      <SliderTrack
        ref={trackRef}
        theme={theme}
        size={size}
        onMouseDown={(e) => handleMouseDown(e)}
      >
        <SliderFill
          theme={theme}
          variant={variant}
          size={size}
          left={leftPosition}
          width={rightPosition - leftPosition}
        />
        
        {marks.map((mark) => {
          const markPosition = getPositionFromValue(mark.value);
          return (
            <SliderMark
              key={mark.value}
              theme={theme}
              position={markPosition}
              active={mark.value >= value[0] && mark.value <= value[1]}
            />
          );
        })}
      </SliderTrack>
      
      {/* 左側手柄 */}
      <SliderThumb
        theme={theme}
        variant={variant}
        size={size}
        position={leftPosition}
        active={activeThumb === 0}
        disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onMouseDown={(e) => handleMouseDown(e, 0)}
      />
      
      {/* 右側手柄 */}
      <SliderThumb
        theme={theme}
        variant={variant}
        size={size}
        position={rightPosition}
        active={activeThumb === 1}
        disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onMouseDown={(e) => handleMouseDown(e, 1)}
      />
      
      {showValue && (
        <>
          <SliderValue
            theme={theme}
            position={leftPosition}
            size={size}
          >
            {formatValue(value[0])}
          </SliderValue>
          
          <SliderValue
            theme={theme}
            position={rightPosition}
            size={size}
          >
            {formatValue(value[1])}
          </SliderValue>
        </>
      )}
      
      {marks.map((mark) => {
        if (!mark.label) return null;
        
        const markPosition = getPositionFromValue(mark.value);
        return (
          <SliderLabel
            key={`label-${mark.value}`}
            theme={theme}
            position={markPosition}
            size={size}
          >
            {mark.label}
          </SliderLabel>
        );
      })}
    </SliderContainer>
  );
};

export default Slider;