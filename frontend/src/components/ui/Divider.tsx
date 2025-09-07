/**
 * 分隔線組件 - VS Code 風格的內容分隔組件
 * 用於視覺上分隔不同的內容區域
 */

import React from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, transitions } from '../../styles/GlobalStyles';

// 分隔線容器
const DividerContainer = styled.div<{
  theme: 'light' | 'dark';
  orientation: 'horizontal' | 'vertical';
  variant: 'solid' | 'dashed' | 'dotted';
  spacing: 'none' | 'small' | 'medium' | 'large';
  withText?: boolean;
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  
  ${props => {
    const spacingMap = {
      'none': '0',
      'small': spacing.sm,
      'medium': spacing.md,
      'large': spacing.lg
    };
    
    if (props.orientation === 'horizontal') {
      return `
        width: 100%;
        margin: ${spacingMap[props.spacing]} 0;
        flex-direction: row;
      `;
    } else {
      return `
        height: 100%;
        margin: 0 ${spacingMap[props.spacing]};
        flex-direction: column;
        min-height: 20px;
      `;
    }
  }}
`;

// 分隔線
const DividerLine = styled.div<{
  theme: 'light' | 'dark';
  orientation: 'horizontal' | 'vertical';
  variant: 'solid' | 'dashed' | 'dotted';
  color?: string;
}>`
  background-color: ${props => props.color || getThemeColors(props.theme).border.primary};
  
  ${props => {
    const borderStyle = props.variant === 'solid' ? 'solid' : props.variant;
    
    if (props.orientation === 'horizontal') {
      return `
        width: 100%;
        height: 1px;
        ${props.variant !== 'solid' ? `
          height: 0;
          border-top: 1px ${borderStyle} ${props.color || getThemeColors(props.theme).border.primary};
          background: none;
        ` : ''}
      `;
    } else {
      return `
        width: 1px;
        height: 100%;
        ${props.variant !== 'solid' ? `
          width: 0;
          border-left: 1px ${borderStyle} ${props.color || getThemeColors(props.theme).border.primary};
          background: none;
        ` : ''}
      `;
    }
  }}
`;

// 分隔線文字容器
const DividerText = styled.div<{
  theme: 'light' | 'dark';
  orientation: 'horizontal' | 'vertical';
  position: 'left' | 'center' | 'right';
}>`
  background-color: ${props => getThemeColors(props.theme).background.primary};
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  
  ${props => {
    if (props.orientation === 'horizontal') {
      return `
        padding: 0 ${spacing.md};
        ${props.position === 'left' ? 'margin-right: auto;' : ''}
        ${props.position === 'right' ? 'margin-left: auto;' : ''}
      `;
    } else {
      return `
        padding: ${spacing.md} 0;
        writing-mode: vertical-rl;
        text-orientation: mixed;
        ${props.position === 'left' ? 'margin-bottom: auto;' : ''}
        ${props.position === 'right' ? 'margin-top: auto;' : ''}
      `;
    }
  }}
`;

// 分隔線左側線條
const DividerLeftLine = styled(DividerLine)<{
  hasText: boolean;
  textPosition: 'left' | 'center' | 'right';
}>`
  ${props => {
    if (!props.hasText) return '';
    
    if (props.orientation === 'horizontal') {
      if (props.textPosition === 'left') return 'width: 20%;';
      if (props.textPosition === 'right') return 'flex: 1;';
      return 'flex: 1;';
    } else {
      if (props.textPosition === 'left') return 'height: 20%;';
      if (props.textPosition === 'right') return 'flex: 1;';
      return 'flex: 1;';
    }
  }}
`;

// 分隔線右側線條
const DividerRightLine = styled(DividerLine)<{
  hasText: boolean;
  textPosition: 'left' | 'center' | 'right';
}>`
  ${props => {
    if (!props.hasText) return 'display: none;';
    
    if (props.orientation === 'horizontal') {
      if (props.textPosition === 'left') return 'flex: 1;';
      if (props.textPosition === 'right') return 'width: 20%;';
      return 'flex: 1;';
    } else {
      if (props.textPosition === 'left') return 'flex: 1;';
      if (props.textPosition === 'right') return 'height: 20%;';
      return 'flex: 1;';
    }
  }}
`;

// 圖標分隔線容器
const IconDivider = styled.div<{
  theme: 'light' | 'dark';
  orientation: 'horizontal' | 'vertical';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: ${props => getThemeColors(props.theme).background.primary};
  color: ${props => getThemeColors(props.theme).text.secondary};
  
  ${props => {
    if (props.orientation === 'horizontal') {
      return `
        padding: 0 ${spacing.md};
        font-size: 16px;
      `;
    } else {
      return `
        padding: ${spacing.md} 0;
        font-size: 16px;
      `;
    }
  }}
`;

// 分隔線組件介面
export interface DividerProps {
  theme: 'light' | 'dark';
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'dotted';
  spacing?: 'none' | 'small' | 'medium' | 'large';
  color?: string;
  children?: React.ReactNode;
  textPosition?: 'left' | 'center' | 'right';
  className?: string;
}

/**
 * 分隔線組件
 * 用於視覺上分隔不同的內容區域
 */
export const Divider: React.FC<DividerProps> = ({
  theme,
  orientation = 'horizontal',
  variant = 'solid',
  spacing = 'medium',
  color,
  children,
  textPosition = 'center',
  className
}) => {
  const hasText = !!children;
  
  return (
    <DividerContainer
      theme={theme}
      orientation={orientation}
      variant={variant}
      spacing={spacing}
      withText={hasText}
      className={className}
    >
      <DividerLeftLine
        theme={theme}
        orientation={orientation}
        variant={variant}
        color={color}
        hasText={hasText}
        textPosition={textPosition}
      />
      
      {hasText && (
        <DividerText
          theme={theme}
          orientation={orientation}
          position={textPosition}
        >
          {children}
        </DividerText>
      )}
      
      <DividerRightLine
        theme={theme}
        orientation={orientation}
        variant={variant}
        color={color}
        hasText={hasText}
        textPosition={textPosition}
      />
    </DividerContainer>
  );
};

// 圖標分隔線組件介面
export interface IconDividerProps {
  theme: 'light' | 'dark';
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'dotted';
  spacing?: 'none' | 'small' | 'medium' | 'large';
  color?: string;
  icon: React.ReactNode;
  className?: string;
}

/**
 * 圖標分隔線組件
 * 帶有圖標的分隔線
 */
export const IconDivider: React.FC<IconDividerProps> = ({
  theme,
  orientation = 'horizontal',
  variant = 'solid',
  spacing = 'medium',
  color,
  icon,
  className
}) => {
  return (
    <DividerContainer
      theme={theme}
      orientation={orientation}
      variant={variant}
      spacing={spacing}
      withText={true}
      className={className}
    >
      <DividerLeftLine
        theme={theme}
        orientation={orientation}
        variant={variant}
        color={color}
        hasText={true}
        textPosition="center"
      />
      
      <IconDivider theme={theme} orientation={orientation}>
        {icon}
      </IconDivider>
      
      <DividerRightLine
        theme={theme}
        orientation={orientation}
        variant={variant}
        color={color}
        hasText={true}
        textPosition="center"
      />
    </DividerContainer>
  );
};

// 標題分隔線組件介面
export interface TitleDividerProps {
  theme: 'light' | 'dark';
  title: string;
  subtitle?: string;
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'dotted';
  spacing?: 'none' | 'small' | 'medium' | 'large';
  color?: string;
  textPosition?: 'left' | 'center' | 'right';
  className?: string;
}

/**
 * 標題分隔線組件
 * 帶有標題和副標題的分隔線
 */
export const TitleDivider: React.FC<TitleDividerProps> = ({
  theme,
  title,
  subtitle,
  orientation = 'horizontal',
  variant = 'solid',
  spacing = 'medium',
  color,
  textPosition = 'center',
  className
}) => {
  const TitleContainer = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    background-color: ${getThemeColors(theme).background.primary};
    
    ${orientation === 'horizontal' ? `
      padding: 0 ${spacing.lg};
    ` : `
      padding: ${spacing.lg} 0;
      writing-mode: vertical-rl;
      text-orientation: mixed;
    `}
  `;
  
  const Title = styled.div`
    color: ${getThemeColors(theme).text.primary};
    font-size: 16px;
    font-weight: 600;
    line-height: 1.4;
  `;
  
  const Subtitle = styled.div`
    color: ${getThemeColors(theme).text.secondary};
    font-size: 12px;
    margin-top: 2px;
    line-height: 1.4;
  `;
  
  return (
    <DividerContainer
      theme={theme}
      orientation={orientation}
      variant={variant}
      spacing={spacing}
      withText={true}
      className={className}
    >
      <DividerLeftLine
        theme={theme}
        orientation={orientation}
        variant={variant}
        color={color}
        hasText={true}
        textPosition={textPosition}
      />
      
      <TitleContainer>
        <Title>{title}</Title>
        {subtitle && <Subtitle>{subtitle}</Subtitle>}
      </TitleContainer>
      
      <DividerRightLine
        theme={theme}
        orientation={orientation}
        variant={variant}
        color={color}
        hasText={true}
        textPosition={textPosition}
      />
    </DividerContainer>
  );
};

// 漸變分隔線組件介面
export interface GradientDividerProps {
  theme: 'light' | 'dark';
  orientation?: 'horizontal' | 'vertical';
  spacing?: 'none' | 'small' | 'medium' | 'large';
  startColor?: string;
  endColor?: string;
  className?: string;
}

/**
 * 漸變分隔線組件
 * 具有漸變效果的分隔線
 */
export const GradientDivider: React.FC<GradientDividerProps> = ({
  theme,
  orientation = 'horizontal',
  spacing = 'medium',
  startColor,
  endColor,
  className
}) => {
  const colors = getThemeColors(theme);
  const defaultStartColor = startColor || colors.accent.primary;
  const defaultEndColor = endColor || 'transparent';
  
  const GradientLine = styled.div`
    ${orientation === 'horizontal' ? `
      width: 100%;
      height: 1px;
      background: linear-gradient(to right, ${defaultStartColor}, ${defaultEndColor});
    ` : `
      width: 1px;
      height: 100%;
      background: linear-gradient(to bottom, ${defaultStartColor}, ${defaultEndColor});
    `}
  `;
  
  return (
    <DividerContainer
      theme={theme}
      orientation={orientation}
      variant="solid"
      spacing={spacing}
      className={className}
    >
      <GradientLine />
    </DividerContainer>
  );
};

export default Divider;