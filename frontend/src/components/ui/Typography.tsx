/**
 * Typography 組件
 * 提供統一的文字樣式和排版
 */

import React from 'react';
import styled from 'styled-components';
import { colors, typography, lightTheme } from '../../styles';

// ============= 類型定義 =============

export interface TypographyProps {
  children: React.ReactNode;
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2' | 'caption' | 'overline';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'text';
  align?: 'left' | 'center' | 'right' | 'justify';
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold';
  className?: string;
  style?: React.CSSProperties;
}

// ============= 樣式組件 =============

const StyledTypography = styled.div<TypographyProps>`
  margin: 0;
  padding: 0;
  
  ${({ variant }) => {
    switch (variant) {
      case 'h1':
        return `
          font-size: ${typography.fontSize['4xl']};
          line-height: ${typography.lineHeight.tight};
          font-weight: ${typography.fontWeight.bold};
        `;
      case 'h2':
        return `
          font-size: ${typography.fontSize['3xl']};
          line-height: ${typography.lineHeight.tight};
          font-weight: ${typography.fontWeight.bold};
        `;
      case 'h3':
        return `
          font-size: ${typography.fontSize['2xl']};
          line-height: ${typography.lineHeight.snug};
          font-weight: ${typography.fontWeight.semibold};
        `;
      case 'h4':
        return `
          font-size: ${typography.fontSize.xl};
          line-height: ${typography.lineHeight.snug};
          font-weight: ${typography.fontWeight.semibold};
        `;
      case 'h5':
        return `
          font-size: ${typography.fontSize.lg};
          line-height: ${typography.lineHeight.normal};
          font-weight: ${typography.fontWeight.medium};
        `;
      case 'h6':
        return `
          font-size: ${typography.fontSize.base};
          line-height: ${typography.lineHeight.normal};
          font-weight: ${typography.fontWeight.medium};
        `;
      case 'body1':
        return `
          font-size: ${typography.fontSize.base};
          line-height: ${typography.lineHeight.relaxed};
          font-weight: ${typography.fontWeight.normal};
        `;
      case 'body2':
        return `
          font-size: ${typography.fontSize.sm};
          line-height: ${typography.lineHeight.relaxed};
          font-weight: ${typography.fontWeight.normal};
        `;
      case 'caption':
        return `
          font-size: ${typography.fontSize.xs};
          line-height: ${typography.lineHeight.normal};
          font-weight: ${typography.fontWeight.normal};
        `;
      case 'overline':
        return `
          font-size: ${typography.fontSize.xs};
          line-height: ${typography.lineHeight.normal};
          font-weight: ${typography.fontWeight.medium};
          text-transform: uppercase;
          letter-spacing: 0.5px;
        `;
      default:
        return `
          font-size: ${typography.fontSize.base};
          line-height: ${typography.lineHeight.normal};
          font-weight: ${typography.fontWeight.normal};
        `;
    }
  }}
  
  ${({ color }) => {
    switch (color) {
      case 'primary':
        return `color: ${colors.primary[600]};`;
      case 'secondary':
        return `color: ${colors.secondary[600]};`;
      case 'success':
        return `color: ${colors.success[600]};`;
      case 'warning':
        return `color: ${colors.warning[600]};`;
      case 'error':
        return `color: ${colors.error[600]};`;
      case 'info':
        return `color: ${colors.info[600]};`;
      case 'text':
      default:
        return `color: ${lightTheme.colors.text.primary};`;
    }
  }}
  
  text-align: ${({ align }) => align || 'left'};
  
  ${({ weight }) => {
    if (weight) {
      return `font-weight: ${typography.fontWeight[weight]};`;
    }
    return '';
  }}
`;

// ============= 主要組件 =============

/**
 * Typography 組件
 * 
 * @param props - Typography 屬性
 * @returns Typography 組件
 */
export const Typography: React.FC<TypographyProps> = ({
  children,
  variant = 'body1',
  color = 'text',
  align = 'left',
  weight,
  className,
  style,
  ...props
}) => {
  return (
    <StyledTypography
      variant={variant}
      color={color}
      align={align}
      weight={weight}
      className={className}
      style={style}
      {...props}
    >
      {children}
    </StyledTypography>
  );
};

export default Typography;