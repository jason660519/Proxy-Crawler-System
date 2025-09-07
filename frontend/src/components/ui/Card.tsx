/**
 * Card 組件
 * 提供卡片容器樣式，用於包裝內容區塊
 */

import React from 'react';
import styled, { css } from 'styled-components';
import { spacing, borderRadius, shadows } from '../../styles';

// ============= 類型定義 =============

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 卡片變體 */
  variant?: 'default' | 'outlined' | 'elevated';
  /** 卡片尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否可點擊 */
  clickable?: boolean;
  /** 是否顯示邊框 */
  bordered?: boolean;
  /** 自定義陰影 */
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  /** 子元素 */
  children?: React.ReactNode;
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 標題 */
  title?: string;
  /** 副標題 */
  subtitle?: string;
  /** 右側動作區域 */
  actions?: React.ReactNode;
  /** 子元素 */
  children?: React.ReactNode;
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 子元素 */
  children?: React.ReactNode;
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 子元素 */
  children?: React.ReactNode;
}

// ============= 樣式定義 =============

const getVariantStyles = (variant: CardProps['variant']) => {
  switch (variant) {
    case 'outlined':
      return css`
        background-color: var(--color-background-primary);
        border: 1px solid var(--color-border-primary);
        box-shadow: none;
      `;
    
    case 'elevated':
      return css`
        background-color: var(--color-background-primary);
        border: none;
        box-shadow: ${shadows.lg};
      `;
    
    case 'default':
    default:
      return css`
        background-color: var(--color-background-primary);
        border: 1px solid var(--color-border-primary);
        box-shadow: ${shadows.sm};
      `;
  }
};

const getSizeStyles = (size: CardProps['size']) => {
  switch (size) {
    case 'sm':
      return css`
        padding: ${spacing[3]};
      `;
    
    case 'lg':
      return css`
        padding: ${spacing[6]};
      `;
    
    case 'md':
    default:
      return css`
        padding: ${spacing[4]};
      `;
  }
};

const getShadowStyles = (shadow: CardProps['shadow']) => {
  switch (shadow) {
    case 'none':
      return css`box-shadow: none;`;
    case 'sm':
      return css`box-shadow: ${shadows.sm};`;
    case 'md':
      return css`box-shadow: ${shadows.md};`;
    case 'lg':
      return css`box-shadow: ${shadows.lg};`;
    default:
      return css``;
  }
};

const StyledCard = styled.div<CardProps>`
  border-radius: ${borderRadius.lg};
  transition: all 0.2s ease-in-out;
  
  ${props => getVariantStyles(props.variant)}
  ${props => getSizeStyles(props.size)}
  ${props => props.shadow && getShadowStyles(props.shadow)}
  
  ${props => props.bordered && css`
    border: 1px solid var(--color-border-primary);
  `}
  
  ${props => props.clickable && css`
    cursor: pointer;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: ${shadows.lg};
    }
    
    &:active {
      transform: translateY(0);
    }
  `}
`;

const CardHeaderContainer = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: ${spacing[4]};
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const CardHeaderContent = styled.div`
  flex: 1;
  min-width: 0;
`;

const CardTitle = styled.h3`
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.5;
  color: var(--color-text-primary);
`;

const CardSubtitle = styled.p`
  margin: ${spacing[1]} 0 0 0;
  font-size: 0.875rem;
  line-height: 1.4;
  color: var(--color-text-secondary);
`;

const CardActions = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[2]};
  margin-left: ${spacing[4]};
  flex-shrink: 0;
`;

const CardContentContainer = styled.div`
  &:not(:first-child) {
    margin-top: ${spacing[4]};
  }
  
  &:not(:last-child) {
    margin-bottom: ${spacing[4]};
  }
`;

const CardFooterContainer = styled.div`
  margin-top: ${spacing[4]};
  padding-top: ${spacing[4]};
  border-top: 1px solid var(--color-border-primary);
  
  &:first-child {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
  }
`;

// ============= 組件實作 =============

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      size = 'md',
      clickable = false,
      bordered = false,
      shadow,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <StyledCard
        ref={ref}
        variant={variant}
        size={size}
        clickable={clickable}
        bordered={bordered}
        shadow={shadow}
        {...props}
      >
        {children}
      </StyledCard>
    );
  }
);

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, subtitle, actions, children, ...props }, ref) => {
    if (children) {
      return (
        <CardHeaderContainer ref={ref} {...props}>
          {children}
        </CardHeaderContainer>
      );
    }

    return (
      <CardHeaderContainer ref={ref} {...props}>
        <CardHeaderContent>
          {title && <CardTitle>{title}</CardTitle>}
          {subtitle && <CardSubtitle>{subtitle}</CardSubtitle>}
        </CardHeaderContent>
        {actions && <CardActions>{actions}</CardActions>}
      </CardHeaderContainer>
    );
  }
);

export const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ children, ...props }, ref) => {
    return (
      <CardContentContainer ref={ref} {...props}>
        {children}
      </CardContentContainer>
    );
  }
);

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ children, ...props }, ref) => {
    return (
      <CardFooterContainer ref={ref} {...props}>
        {children}
      </CardFooterContainer>
    );
  }
);

// 設定 displayName
Card.displayName = 'Card';
CardHeader.displayName = 'CardHeader';
CardContent.displayName = 'CardContent';
CardFooter.displayName = 'CardFooter';

export default Card;