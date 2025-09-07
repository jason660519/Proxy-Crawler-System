/**
 * 加載組件 - VS Code 風格的加載指示器
 * 提供多種樣式和動畫效果的加載組件
 */

import React from 'react';
import styled, { keyframes } from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 旋轉動畫
const spin = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

// 脈衝動畫
const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
`;

// 彈跳動畫
const bounce = keyframes`
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
`;

// 波浪動畫
const wave = keyframes`
  0%, 60%, 100% {
    transform: initial;
  }
  30% {
    transform: translateY(-15px);
  }
`;

// 進度條動畫
const progress = keyframes`
  0% {
    left: -35%;
    right: 100%;
  }
  60% {
    left: 100%;
    right: -90%;
  }
  100% {
    left: 100%;
    right: -90%;
  }
`;

// 加載容器
const LoadingContainer = styled.div<{
  theme: 'light' | 'dark';
  overlay?: boolean;
  size: 'small' | 'medium' | 'large';
}>`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: ${spacing.md};
  
  ${props => props.overlay ? `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: ${getThemeColors(props.theme).background.overlay};
    backdrop-filter: blur(2px);
    z-index: 9999;
  ` : ''}
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          min-height: 60px;
          padding: ${spacing.sm};
        `;
      case 'large':
        return `
          min-height: 120px;
          padding: ${spacing.xl};
        `;
      default:
        return `
          min-height: 80px;
          padding: ${spacing.md};
        `;
    }
  }}
`;

// 旋轉加載器
const SpinLoader = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  width: ${props => {
    switch (props.size) {
      case 'small': return '16px';
      case 'large': return '32px';
      default: return '24px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '16px';
      case 'large': return '32px';
      default: return '24px';
    }
  }};
  border: 2px solid ${props => getThemeColors(props.theme).border.primary};
  border-top: 2px solid ${props => getThemeColors(props.theme).accent.primary};
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
`;

// 點狀加載器
const DotsLoader = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  display: flex;
  gap: ${props => {
    switch (props.size) {
      case 'small': return '4px';
      case 'large': return '8px';
      default: return '6px';
    }
  }};
`;

const Dot = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  delay: number;
}>`
  width: ${props => {
    switch (props.size) {
      case 'small': return '6px';
      case 'large': return '12px';
      default: return '8px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '6px';
      case 'large': return '12px';
      default: return '8px';
    }
  }};
  background-color: ${props => getThemeColors(props.theme).accent.primary};
  border-radius: 50%;
  animation: ${bounce} 1.4s ease-in-out infinite both;
  animation-delay: ${props => props.delay}s;
`;

// 波浪加載器
const WaveLoader = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  display: flex;
  gap: ${props => {
    switch (props.size) {
      case 'small': return '2px';
      case 'large': return '4px';
      default: return '3px';
    }
  }};
`;

const WaveBar = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  delay: number;
}>`
  width: ${props => {
    switch (props.size) {
      case 'small': return '3px';
      case 'large': return '6px';
      default: return '4px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '20px';
      case 'large': return '40px';
      default: return '30px';
    }
  }};
  background-color: ${props => getThemeColors(props.theme).accent.primary};
  border-radius: ${borderRadius.xs};
  animation: ${wave} 1.2s ease-in-out infinite;
  animation-delay: ${props => props.delay}s;
`;

// 進度條加載器
const ProgressLoader = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  position: relative;
  width: ${props => {
    switch (props.size) {
      case 'small': return '120px';
      case 'large': return '200px';
      default: return '160px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '3px';
      case 'large': return '6px';
      default: return '4px';
    }
  }};
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  border-radius: ${borderRadius.full};
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    height: 100%;
    background-color: ${props => getThemeColors(props.theme).accent.primary};
    border-radius: inherit;
    animation: ${progress} 2.1s cubic-bezier(0.65, 0.815, 0.735, 0.395) infinite;
  }
`;

// 脈衝加載器
const PulseLoader = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  width: ${props => {
    switch (props.size) {
      case 'small': return '20px';
      case 'large': return '40px';
      default: return '30px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '20px';
      case 'large': return '40px';
      default: return '30px';
    }
  }};
  background-color: ${props => getThemeColors(props.theme).accent.primary};
  border-radius: 50%;
  animation: ${pulse} 1.5s ease-in-out infinite;
`;

// 骨架屏加載器
const SkeletonLoader = styled.div<{
  theme: 'light' | 'dark';
  width?: string;
  height?: string;
  variant: 'text' | 'rectangular' | 'circular';
}>`
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  background-image: linear-gradient(
    90deg,
    transparent,
    ${props => getThemeColors(props.theme).background.hover},
    transparent
  );
  background-size: 200px 100%;
  background-repeat: no-repeat;
  animation: ${progress} 1.2s ease-in-out infinite;
  
  width: ${props => props.width || '100%'};
  height: ${props => props.height || '1em'};
  
  border-radius: ${props => {
    switch (props.variant) {
      case 'circular': return '50%';
      case 'rectangular': return borderRadius.sm;
      default: return borderRadius.xs;
    }
  }};
`;

// 加載文字
const LoadingText = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '12px';
      case 'large': return '16px';
      default: return '14px';
    }
  }};
  font-weight: 400;
  text-align: center;
  animation: ${pulse} 2s ease-in-out infinite;
`;

// 加載組件介面
export interface LoadingProps {
  theme: 'light' | 'dark';
  variant?: 'spin' | 'dots' | 'wave' | 'progress' | 'pulse';
  size?: 'small' | 'medium' | 'large';
  text?: React.ReactNode;
  overlay?: boolean;
  className?: string;
}

/**
 * 加載組件
 * 提供多種樣式的加載指示器
 */
export const Loading: React.FC<LoadingProps> = ({
  theme,
  variant = 'spin',
  size = 'medium',
  text,
  overlay = false,
  className
}) => {
  // 渲染加載器
  const renderLoader = () => {
    switch (variant) {
      case 'dots':
        return (
          <DotsLoader theme={theme} size={size}>
            <Dot theme={theme} size={size} delay={-0.32} />
            <Dot theme={theme} size={size} delay={-0.16} />
            <Dot theme={theme} size={size} delay={0} />
          </DotsLoader>
        );
      
      case 'wave':
        return (
          <WaveLoader theme={theme} size={size}>
            <WaveBar theme={theme} size={size} delay={-0.4} />
            <WaveBar theme={theme} size={size} delay={-0.3} />
            <WaveBar theme={theme} size={size} delay={-0.2} />
            <WaveBar theme={theme} size={size} delay={-0.1} />
            <WaveBar theme={theme} size={size} delay={0} />
          </WaveLoader>
        );
      
      case 'progress':
        return <ProgressLoader theme={theme} size={size} />;
      
      case 'pulse':
        return <PulseLoader theme={theme} size={size} />;
      
      default:
        return <SpinLoader theme={theme} size={size} />;
    }
  };
  
  return (
    <LoadingContainer
      theme={theme}
      overlay={overlay}
      size={size}
      className={className}
    >
      {renderLoader()}
      
      {text && (
        <LoadingText theme={theme} size={size}>
          {text}
        </LoadingText>
      )}
    </LoadingContainer>
  );
};

// 骨架屏組件介面
export interface SkeletonProps {
  theme: 'light' | 'dark';
  variant?: 'text' | 'rectangular' | 'circular';
  width?: string;
  height?: string;
  className?: string;
}

/**
 * 骨架屏組件
 * 用於內容加載時的佔位符
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  theme,
  variant = 'text',
  width,
  height,
  className
}) => {
  return (
    <SkeletonLoader
      theme={theme}
      variant={variant}
      width={width}
      height={height}
      className={className}
    />
  );
};

// 加載包裝器組件介面
export interface LoadingWrapperProps {
  theme: 'light' | 'dark';
  loading: boolean;
  variant?: 'spin' | 'dots' | 'wave' | 'progress' | 'pulse';
  size?: 'small' | 'medium' | 'large';
  text?: React.ReactNode;
  overlay?: boolean;
  className?: string;
  children: React.ReactNode;
}

/**
 * 加載包裝器組件
 * 在子組件上覆蓋加載狀態
 */
export const LoadingWrapper: React.FC<LoadingWrapperProps> = ({
  theme,
  loading,
  variant = 'spin',
  size = 'medium',
  text,
  overlay = true,
  className,
  children
}) => {
  return (
    <div style={{ position: 'relative' }} className={className}>
      {children}
      
      {loading && (
        <Loading
          theme={theme}
          variant={variant}
          size={size}
          text={text}
          overlay={overlay}
        />
      )}
    </div>
  );
};

export default Loading;