/**
 * Space 間距組件
 * 設置組件之間的間距
 */

import React from 'react';
import styled from 'styled-components';
import { spacing } from '../../styles';

// ============= 類型定義 =============

export interface SpaceProps {
  /** 間距方向 */
  direction?: 'horizontal' | 'vertical';
  /** 間距大小 */
  size?: 'small' | 'middle' | 'large' | number;
  /** 對齊方式 */
  align?: 'start' | 'end' | 'center' | 'baseline';
  /** 是否自動換行，僅在 horizontal 時有效 */
  wrap?: boolean;
  /** 分隔符 */
  split?: React.ReactNode;
  /** 子元素 */
  children?: React.ReactNode;
  /** 自定義樣式類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

// ============= 樣式定義 =============

const SpaceContainer = styled.div<{
  direction: 'horizontal' | 'vertical';
  align?: 'start' | 'end' | 'center' | 'baseline';
  wrap?: boolean;
}>`
  display: flex;
  flex-direction: ${props => props.direction === 'vertical' ? 'column' : 'row'};
  align-items: ${props => {
    switch (props.align) {
      case 'start': return 'flex-start';
      case 'end': return 'flex-end';
      case 'center': return 'center';
      case 'baseline': return 'baseline';
      default: return props.direction === 'vertical' ? 'stretch' : 'center';
    }
  }};
  
  ${props => props.direction === 'horizontal' && props.wrap && `
    flex-wrap: wrap;
  `}
`;

const SpaceItem = styled.div<{
  direction: 'horizontal' | 'vertical';
  size: number;
  isLast: boolean;
}>`
  ${props => !props.isLast && (
    props.direction === 'vertical' 
      ? `margin-bottom: ${props.size}px;`
      : `margin-right: ${props.size}px;`
  )}
`;

const SpaceSplit = styled.div<{
  direction: 'horizontal' | 'vertical';
  size: number;
}>`
  ${props => props.direction === 'vertical' 
    ? `margin: ${props.size / 2}px 0;`
    : `margin: 0 ${props.size / 2}px;`
  }
  display: flex;
  align-items: center;
  justify-content: center;
`;

// ============= 工具函數 =============

const getSizeValue = (size: 'small' | 'middle' | 'large' | number): number => {
  if (typeof size === 'number') {
    return size;
  }
  
  switch (size) {
    case 'small':
      return parseInt(spacing[2]); // 8px
    case 'large':
      return parseInt(spacing[6]); // 24px
    case 'middle':
    default:
      return parseInt(spacing[4]); // 16px
  }
};

// ============= 主要組件 =============

export const Space: React.FC<SpaceProps> = ({
  direction = 'horizontal',
  size = 'middle',
  align,
  wrap = false,
  split,
  children,
  className,
  style,
}) => {
  const sizeValue = getSizeValue(size);
  
  const childrenArray = React.Children.toArray(children).filter(child => 
    React.isValidElement(child) || typeof child === 'string' || typeof child === 'number'
  );
  
  if (childrenArray.length === 0) {
    return null;
  }
  
  return (
    <SpaceContainer
      direction={direction}
      align={align}
      wrap={wrap}
      className={className}
      style={style}
    >
      {childrenArray.map((child, index) => {
        const isLast = index === childrenArray.length - 1;
        
        return (
          <React.Fragment key={index}>
            <SpaceItem
              direction={direction}
              size={sizeValue}
              isLast={isLast}
            >
              {child}
            </SpaceItem>
            
            {!isLast && split && (
              <SpaceSplit
                direction={direction}
                size={sizeValue}
              >
                {split}
              </SpaceSplit>
            )}
          </React.Fragment>
        );
      })}
    </SpaceContainer>
  );
};

export default Space;