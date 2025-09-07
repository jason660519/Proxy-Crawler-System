/**
 * 提示框組件 - VS Code 風格的懸浮提示
 * 提供多種位置和觸發方式的提示框
 */

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 提示框容器
const TooltipContainer = styled.div`
  position: relative;
  display: inline-block;
`;

// 提示框內容
const TooltipContent = styled.div<{
  theme: 'light' | 'dark';
  placement: 'top' | 'bottom' | 'left' | 'right';
  visible?: boolean;
  x: number;
  y: number;
}>`
  position: fixed;
  z-index: 10000;
  background-color: ${props => getThemeColors(props.theme).tooltip.background};
  color: ${props => getThemeColors(props.theme).tooltip.foreground};
  border: 1px solid ${props => getThemeColors(props.theme).tooltip.border};
  border-radius: ${borderRadius.sm};
  padding: ${spacing.xs} ${spacing.sm};
  font-size: 11px;
  font-weight: 400;
  line-height: 1.4;
  max-width: 250px;
  word-wrap: break-word;
  box-shadow: 0 4px 12px ${props => getThemeColors(props.theme).shadow.tooltip};
  pointer-events: none;
  white-space: nowrap;
  
  left: ${props => props.x}px;
  top: ${props => props.y}px;
  
  opacity: ${props => props.visible ? 1 : 0};
  visibility: ${props => props.visible ? 'visible' : 'hidden'};
  transform: ${props => {
    const offset = props.visible ? '0' : '4px';
    switch (props.placement) {
      case 'top':
        return `translateX(-50%) translateY(-100%) translateY(${props.visible ? '-8px' : `-4px`})`;
      case 'bottom':
        return `translateX(-50%) translateY(${props.visible ? '8px' : '4px'})`;
      case 'left':
        return `translateX(-100%) translateY(-50%) translateX(${props.visible ? '-8px' : '-4px'})`;
      case 'right':
        return `translateY(-50%) translateX(${props.visible ? '8px' : '4px'})`;
      default:
        return `translateX(-50%) translateY(-100%) translateY(-8px)`;
    }
  }};
  transition: all ${transitions.fast} ease;
  
  /* 箭頭 */
  &::before {
    content: '';
    position: absolute;
    width: 0;
    height: 0;
    border: 4px solid transparent;
    
    ${props => {
      const borderColor = getThemeColors(props.theme).tooltip.background;
      switch (props.placement) {
        case 'top':
          return `
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-top-color: ${borderColor};
          `;
        case 'bottom':
          return `
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-bottom-color: ${borderColor};
          `;
        case 'left':
          return `
            left: 100%;
            top: 50%;
            transform: translateY(-50%);
            border-left-color: ${borderColor};
          `;
        case 'right':
          return `
            right: 100%;
            top: 50%;
            transform: translateY(-50%);
            border-right-color: ${borderColor};
          `;
        default:
          return `
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-top-color: ${borderColor};
          `;
      }
    }}
  }
  
  /* 箭頭邊框 */
  &::after {
    content: '';
    position: absolute;
    width: 0;
    height: 0;
    border: 5px solid transparent;
    
    ${props => {
      const borderColor = getThemeColors(props.theme).tooltip.border;
      switch (props.placement) {
        case 'top':
          return `
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-top-color: ${borderColor};
            margin-top: -1px;
          `;
        case 'bottom':
          return `
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-bottom-color: ${borderColor};
            margin-bottom: -1px;
          `;
        case 'left':
          return `
            left: 100%;
            top: 50%;
            transform: translateY(-50%);
            border-left-color: ${borderColor};
            margin-left: -1px;
          `;
        case 'right':
          return `
            right: 100%;
            top: 50%;
            transform: translateY(-50%);
            border-right-color: ${borderColor};
            margin-right: -1px;
          `;
        default:
          return `
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-top-color: ${borderColor};
            margin-top: -1px;
          `;
      }
    }}
  }
`;

// 提示框組件介面
export interface TooltipProps {
  theme: 'light' | 'dark';
  title: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: 'hover' | 'click' | 'focus' | 'manual';
  visible?: boolean;
  defaultVisible?: boolean;
  delay?: number;
  mouseEnterDelay?: number;
  mouseLeaveDelay?: number;
  disabled?: boolean;
  className?: string;
  children: React.ReactElement;
  onVisibleChange?: (visible: boolean) => void;
}

/**
 * 提示框組件
 * 提供統一的懸浮提示樣式
 */
export const Tooltip: React.FC<TooltipProps> = ({
  theme,
  title,
  placement = 'top',
  trigger = 'hover',
  visible,
  defaultVisible = false,
  delay = 0,
  mouseEnterDelay = 100,
  mouseLeaveDelay = 100,
  disabled = false,
  className,
  children,
  onVisibleChange
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const enterTimerRef = useRef<NodeJS.Timeout | null>(null);
  const leaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  const isVisible = visible !== undefined ? visible : internalVisible;
  
  // 清理定時器
  const clearTimers = () => {
    if (enterTimerRef.current) {
      clearTimeout(enterTimerRef.current);
      enterTimerRef.current = null;
    }
    if (leaveTimerRef.current) {
      clearTimeout(leaveTimerRef.current);
      leaveTimerRef.current = null;
    }
  };
  
  // 計算提示框位置
  const calculatePosition = () => {
    if (!containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;
    
    let x = 0;
    let y = 0;
    
    switch (placement) {
      case 'top':
        x = rect.left + scrollX + rect.width / 2;
        y = rect.top + scrollY;
        break;
      case 'bottom':
        x = rect.left + scrollX + rect.width / 2;
        y = rect.bottom + scrollY;
        break;
      case 'left':
        x = rect.left + scrollX;
        y = rect.top + scrollY + rect.height / 2;
        break;
      case 'right':
        x = rect.right + scrollX;
        y = rect.top + scrollY + rect.height / 2;
        break;
    }
    
    setPosition({ x, y });
  };
  
  // 顯示提示框
  const showTooltip = () => {
    if (disabled) return;
    
    clearTimers();
    
    const showDelay = trigger === 'hover' ? mouseEnterDelay : delay;
    
    if (showDelay > 0) {
      enterTimerRef.current = setTimeout(() => {
        calculatePosition();
        setInternalVisible(true);
        onVisibleChange?.(true);
      }, showDelay);
    } else {
      calculatePosition();
      setInternalVisible(true);
      onVisibleChange?.(true);
    }
  };
  
  // 隱藏提示框
  const hideTooltip = () => {
    clearTimers();
    
    const hideDelay = trigger === 'hover' ? mouseLeaveDelay : delay;
    
    if (hideDelay > 0) {
      leaveTimerRef.current = setTimeout(() => {
        setInternalVisible(false);
        onVisibleChange?.(false);
      }, hideDelay);
    } else {
      setInternalVisible(false);
      onVisibleChange?.(false);
    }
  };
  
  // 切換提示框顯示狀態
  const toggleTooltip = () => {
    if (isVisible) {
      hideTooltip();
    } else {
      showTooltip();
    }
  };
  
  // 處理鼠標進入
  const handleMouseEnter = () => {
    if (trigger === 'hover') {
      showTooltip();
    }
  };
  
  // 處理鼠標離開
  const handleMouseLeave = () => {
    if (trigger === 'hover') {
      hideTooltip();
    }
  };
  
  // 處理點擊
  const handleClick = () => {
    if (trigger === 'click') {
      toggleTooltip();
    }
  };
  
  // 處理焦點
  const handleFocus = () => {
    if (trigger === 'focus') {
      showTooltip();
    }
  };
  
  // 處理失焦
  const handleBlur = () => {
    if (trigger === 'focus') {
      hideTooltip();
    }
  };
  
  // 處理點擊外部
  useEffect(() => {
    if (trigger !== 'click') return;
    
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        hideTooltip();
      }
    };
    
    if (isVisible) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isVisible, trigger]);
  
  // 處理窗口大小變化
  useEffect(() => {
    const handleResize = () => {
      if (isVisible) {
        calculatePosition();
      }
    };
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleResize);
    };
  }, [isVisible]);
  
  // 清理定時器
  useEffect(() => {
    return () => {
      clearTimers();
    };
  }, []);
  
  // 如果沒有標題內容，直接返回子元素
  if (!title || disabled) {
    return children;
  }
  
  // 克隆子元素並添加事件處理器
  const childElement = React.cloneElement(children, {
    onMouseEnter: (event: React.MouseEvent) => {
      handleMouseEnter();
      children.props.onMouseEnter?.(event);
    },
    onMouseLeave: (event: React.MouseEvent) => {
      handleMouseLeave();
      children.props.onMouseLeave?.(event);
    },
    onClick: (event: React.MouseEvent) => {
      handleClick();
      children.props.onClick?.(event);
    },
    onFocus: (event: React.FocusEvent) => {
      handleFocus();
      children.props.onFocus?.(event);
    },
    onBlur: (event: React.FocusEvent) => {
      handleBlur();
      children.props.onBlur?.(event);
    }
  });
  
  return (
    <>
      <TooltipContainer ref={containerRef} className={className}>
        {childElement}
      </TooltipContainer>
      
      {createPortal(
        <TooltipContent
          theme={theme}
          placement={placement}
          visible={isVisible}
          x={position.x}
          y={position.y}
        >
          {title}
        </TooltipContent>,
        document.body
      )}
    </>
  );
};

export default Tooltip;