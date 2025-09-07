/**
 * 進度條組件 - VS Code 風格的進度指示器
 * 提供多種樣式和動畫效果的進度條
 */

import React from 'react';
import styled, { keyframes } from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 進度條動畫
const progressAnimation = keyframes`
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
`;

const indeterminateAnimation = keyframes`
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
`;

// 進度條容器
const ProgressContainer = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  display: flex;
  flex-direction: column;
  gap: ${spacing.xs};
  width: 100%;
`;

// 進度條信息
const ProgressInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  line-height: 1;
`;

// 進度條標籤
const ProgressLabel = styled.span<{ theme: 'light' | 'dark' }>`
  color: ${props => getThemeColors(props.theme).text.primary};
  font-weight: 500;
`;

// 進度條百分比
const ProgressPercent = styled.span<{ theme: 'light' | 'dark' }>`
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-variant-numeric: tabular-nums;
`;

// 進度條軌道
const ProgressTrack = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  variant: 'line' | 'circle' | 'dashboard';
}>`
  position: relative;
  width: 100%;
  height: ${props => {
    switch (props.size) {
      case 'small': return '4px';
      case 'large': return '8px';
      default: return '6px';
    }
  }};
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  border-radius: ${props => props.variant === 'line' ? borderRadius.full : '0'};
  overflow: hidden;
`;

// 進度條填充
const ProgressFill = styled.div<{
  theme: 'light' | 'dark';
  percent: number;
  status: 'normal' | 'success' | 'error' | 'warning';
  animated?: boolean;
  indeterminate?: boolean;
}>`
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: ${props => props.indeterminate ? '30%' : `${props.percent}%`};
  background-color: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'success': return colors.status.success;
      case 'error': return colors.status.error;
      case 'warning': return colors.status.warning;
      default: return colors.accent.primary;
    }
  }};
  border-radius: inherit;
  transition: ${props => props.animated && !props.indeterminate ? `width ${transitions.normal} ease` : 'none'};
  
  ${props => props.indeterminate ? `
    animation: ${indeterminateAnimation} 1.5s ease-in-out infinite;
  ` : ''}
`;

// 圓形進度條容器
const CircleProgressContainer = styled.div<{
  size: 'small' | 'medium' | 'large';
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: ${props => {
    switch (props.size) {
      case 'small': return '64px';
      case 'large': return '120px';
      default: return '80px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '64px';
      case 'large': return '120px';
      default: return '80px';
    }
  }};
`;

// 圓形進度條 SVG
const CircleProgressSvg = styled.svg`
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
`;

// 圓形進度條軌道
const CircleProgressTrack = styled.circle<{ theme: 'light' | 'dark' }>`
  fill: none;
  stroke: ${props => getThemeColors(props.theme).background.secondary};
  stroke-width: 4;
`;

// 圓形進度條填充
const CircleProgressFill = styled.circle<{
  theme: 'light' | 'dark';
  status: 'normal' | 'success' | 'error' | 'warning';
  animated?: boolean;
}>`
  fill: none;
  stroke: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'success': return colors.status.success;
      case 'error': return colors.status.error;
      case 'warning': return colors.status.warning;
      default: return colors.accent.primary;
    }
  }};
  stroke-width: 4;
  stroke-linecap: round;
  transition: ${props => props.animated ? `stroke-dashoffset ${transitions.normal} ease` : 'none'};
`;

// 圓形進度條內容
const CircleProgressContent = styled.div<{ theme: 'light' | 'dark' }>`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: ${props => getThemeColors(props.theme).text.primary};
`;

// 進度條組件介面
export interface ProgressProps {
  theme: 'light' | 'dark';
  percent?: number;
  status?: 'normal' | 'success' | 'error' | 'warning';
  variant?: 'line' | 'circle' | 'dashboard';
  size?: 'small' | 'medium' | 'large';
  showInfo?: boolean;
  showPercent?: boolean;
  label?: React.ReactNode;
  format?: (percent: number) => React.ReactNode;
  animated?: boolean;
  indeterminate?: boolean;
  strokeWidth?: number;
  className?: string;
}

/**
 * 進度條組件
 * 提供線性和圓形進度指示器
 */
export const Progress: React.FC<ProgressProps> = ({
  theme,
  percent = 0,
  status = 'normal',
  variant = 'line',
  size = 'medium',
  showInfo = true,
  showPercent = true,
  label,
  format,
  animated = true,
  indeterminate = false,
  strokeWidth = 4,
  className
}) => {
  // 確保百分比在有效範圍內
  const normalizedPercent = Math.max(0, Math.min(100, percent));
  
  // 格式化顯示文字
  const formatText = (value: number): React.ReactNode => {
    if (format) {
      return format(value);
    }
    if (showPercent) {
      return `${Math.round(value)}%`;
    }
    return null;
  };
  
  // 渲染線性進度條
  const renderLineProgress = () => (
    <ProgressContainer theme={theme} size={size} className={className}>
      {showInfo && (label || showPercent) && (
        <ProgressInfo>
          {label && (
            <ProgressLabel theme={theme}>
              {label}
            </ProgressLabel>
          )}
          {showPercent && (
            <ProgressPercent theme={theme}>
              {formatText(normalizedPercent)}
            </ProgressPercent>
          )}
        </ProgressInfo>
      )}
      
      <ProgressTrack theme={theme} size={size} variant={variant}>
        <ProgressFill
          theme={theme}
          percent={normalizedPercent}
          status={status}
          animated={animated}
          indeterminate={indeterminate}
        />
      </ProgressTrack>
    </ProgressContainer>
  );
  
  // 渲染圓形進度條
  const renderCircleProgress = () => {
    const radius = 32;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (normalizedPercent / 100) * circumference;
    
    return (
      <CircleProgressContainer size={size} className={className}>
        <CircleProgressSvg>
          <CircleProgressTrack
            theme={theme}
            cx="50%"
            cy="50%"
            r={radius}
            strokeWidth={strokeWidth}
          />
          <CircleProgressFill
            theme={theme}
            status={status}
            animated={animated}
            cx="50%"
            cy="50%"
            r={radius}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={indeterminate ? 0 : strokeDashoffset}
            style={{
              animation: indeterminate ? `${progressAnimation} 2s ease-in-out infinite` : 'none'
            }}
          />
        </CircleProgressSvg>
        
        {showInfo && (
          <CircleProgressContent theme={theme}>
            {label && (
              <div style={{ fontSize: size === 'small' ? '10px' : size === 'large' ? '16px' : '12px', marginBottom: '2px' }}>
                {label}
              </div>
            )}
            {showPercent && (
              <div style={{ 
                fontSize: size === 'small' ? '12px' : size === 'large' ? '20px' : '16px',
                fontWeight: 600,
                fontVariantNumeric: 'tabular-nums'
              }}>
                {formatText(normalizedPercent)}
              </div>
            )}
          </CircleProgressContent>
        )}
      </CircleProgressContainer>
    );
  };
  
  // 根據變體渲染對應的進度條
  switch (variant) {
    case 'circle':
    case 'dashboard':
      return renderCircleProgress();
    default:
      return renderLineProgress();
  }
};

// 進度條步驟項目介面
export interface ProgressStepItem {
  title: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  status?: 'wait' | 'process' | 'finish' | 'error';
}

// 步驟進度條組件介面
export interface ProgressStepsProps {
  theme: 'light' | 'dark';
  items: ProgressStepItem[];
  current?: number;
  direction?: 'horizontal' | 'vertical';
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

// 步驟進度條容器
const StepsContainer = styled.div<{
  direction: 'horizontal' | 'vertical';
}>`
  display: flex;
  flex-direction: ${props => props.direction === 'vertical' ? 'column' : 'row'};
  gap: ${props => props.direction === 'vertical' ? spacing.md : spacing.lg};
`;

// 步驟項目
const StepItem = styled.div<{
  theme: 'light' | 'dark';
  direction: 'horizontal' | 'vertical';
  status: 'wait' | 'process' | 'finish' | 'error';
}>`
  display: flex;
  flex-direction: ${props => props.direction === 'vertical' ? 'row' : 'column'};
  align-items: ${props => props.direction === 'vertical' ? 'flex-start' : 'center'};
  gap: ${spacing.sm};
  flex: ${props => props.direction === 'horizontal' ? 1 : 'none'};
  
  color: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'finish': return colors.status.success;
      case 'process': return colors.accent.primary;
      case 'error': return colors.status.error;
      default: return colors.text.secondary;
    }
  }};
`;

// 步驟圖標
const StepIcon = styled.div<{
  theme: 'light' | 'dark';
  status: 'wait' | 'process' | 'finish' | 'error';
  size: 'small' | 'medium' | 'large';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: ${props => {
    switch (props.size) {
      case 'small': return '24px';
      case 'large': return '36px';
      default: return '30px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '24px';
      case 'large': return '36px';
      default: return '30px';
    }
  }};
  border-radius: 50%;
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '12px';
      case 'large': return '16px';
      default: return '14px';
    }
  }};
  font-weight: 500;
  
  background-color: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'finish': return colors.status.success;
      case 'process': return colors.accent.primary;
      case 'error': return colors.status.error;
      default: return colors.background.secondary;
    }
  }};
  
  color: ${props => {
    const colors = getThemeColors(props.theme);
    if (props.status === 'wait') {
      return colors.text.secondary;
    }
    return colors.background.primary;
  }};
  
  border: 2px solid ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'finish': return colors.status.success;
      case 'process': return colors.accent.primary;
      case 'error': return colors.status.error;
      default: return colors.border.primary;
    }
  }};
`;

// 步驟內容
const StepContent = styled.div<{
  theme: 'light' | 'dark';
  direction: 'horizontal' | 'vertical';
}>`
  display: flex;
  flex-direction: column;
  gap: ${spacing.xs};
  text-align: ${props => props.direction === 'horizontal' ? 'center' : 'left'};
  flex: 1;
`;

// 步驟標題
const StepTitle = styled.div<{ theme: 'light' | 'dark' }>`
  font-size: 14px;
  font-weight: 500;
  color: ${props => getThemeColors(props.theme).text.primary};
`;

// 步驟描述
const StepDescription = styled.div<{ theme: 'light' | 'dark' }>`
  font-size: 12px;
  color: ${props => getThemeColors(props.theme).text.secondary};
  line-height: 1.4;
`;

/**
 * 步驟進度條組件
 * 顯示多步驟流程的進度
 */
export const ProgressSteps: React.FC<ProgressStepsProps> = ({
  theme,
  items,
  current = 0,
  direction = 'horizontal',
  size = 'medium',
  className
}) => {
  return (
    <StepsContainer direction={direction} className={className}>
      {items.map((item, index) => {
        let status = item.status;
        if (!status) {
          if (index < current) {
            status = 'finish';
          } else if (index === current) {
            status = 'process';
          } else {
            status = 'wait';
          }
        }
        
        return (
          <StepItem
            key={index}
            theme={theme}
            direction={direction}
            status={status}
          >
            <StepIcon theme={theme} status={status} size={size}>
              {item.icon || (index + 1)}
            </StepIcon>
            
            <StepContent theme={theme} direction={direction}>
              <StepTitle theme={theme}>
                {item.title}
              </StepTitle>
              
              {item.description && (
                <StepDescription theme={theme}>
                  {item.description}
                </StepDescription>
              )}
            </StepContent>
          </StepItem>
        );
      })}
    </StepsContainer>
  );
};

export default Progress;