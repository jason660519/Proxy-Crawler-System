/**
 * Spin 載入中組件
 * 提供載入狀態的視覺反饋
 */

import React from 'react';
import styled, { keyframes } from 'styled-components';
import { colors } from '../../styles';

// ============= 類型定義 =============

export interface SpinProps {
  /** 是否載入中 */
  spinning?: boolean;
  /** 載入文字 */
  tip?: string;
  /** 尺寸 */
  size?: 'small' | 'default' | 'large';
  /** 延遲顯示載入效果的時間 (毫秒) */
  delay?: number;
  /** 子元素 */
  children?: React.ReactNode;
  /** 自定義樣式類名 */
  className?: string;
}

// ============= 樣式定義 =============

const spinAnimation = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

const SpinContainer = styled.div<{ spinning: boolean; hasChildren: boolean }>`
  position: ${props => props.hasChildren ? 'relative' : 'static'};
  display: ${props => props.hasChildren ? 'block' : 'inline-block'};
  
  ${props => props.spinning && props.hasChildren && `
    pointer-events: none;
    
    > *:not(.spin-overlay) {
      filter: blur(0.5px);
      opacity: 0.5;
      transition: all 0.3s;
    }
  `}
`;

const SpinOverlay = styled.div<{ hasChildren: boolean }>`
  position: ${props => props.hasChildren ? 'absolute' : 'static'};
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  
  ${props => props.hasChildren && `
    background-color: rgba(255, 255, 255, 0.8);
  `}
`;

const SpinIcon = styled.div<{ size: 'small' | 'default' | 'large' }>`
  width: ${props => {
    switch (props.size) {
      case 'small': return '14px';
      case 'large': return '32px';
      default: return '20px';
    }
  }};
  height: ${props => {
    switch (props.size) {
      case 'small': return '14px';
      case 'large': return '32px';
      default: return '20px';
    }
  }};
  border: 2px solid ${colors.primary[200]};
  border-top-color: ${colors.primary[500]};
  border-radius: 50%;
  animation: ${spinAnimation} 1s linear infinite;
`;

const SpinTip = styled.div<{ size: 'small' | 'default' | 'large' }>`
  margin-top: 8px;
  color: ${colors.primary[500]};
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '12px';
      case 'large': return '16px';
      default: return '14px';
    }
  }};
  line-height: 1.5;
`;

// ============= 主要組件 =============

export const Spin: React.FC<SpinProps> = ({
  spinning = true,
  tip,
  size = 'default',
  delay = 0,
  children,
  className,
}) => {
  const [showSpin, setShowSpin] = React.useState(delay === 0 ? spinning : false);
  
  React.useEffect(() => {
    if (spinning && delay > 0) {
      const timer = setTimeout(() => {
        setShowSpin(true);
      }, delay);
      
      return () => clearTimeout(timer);
    } else {
      setShowSpin(spinning);
    }
  }, [spinning, delay]);
  
  const hasChildren = Boolean(children);
  
  if (!showSpin && !hasChildren) {
    return null;
  }
  
  return (
    <SpinContainer 
      spinning={showSpin} 
      hasChildren={hasChildren}
      className={className}
    >
      {children}
      {showSpin && (
        <SpinOverlay hasChildren={hasChildren} className="spin-overlay">
          <SpinIcon size={size} />
          {tip && <SpinTip size={size}>{tip}</SpinTip>}
        </SpinOverlay>
      )}
    </SpinContainer>
  );
};

export default Spin;