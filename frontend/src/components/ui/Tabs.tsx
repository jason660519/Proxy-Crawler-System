/**
 * 標籤頁組件 - VS Code 風格的標籤頁系統
 * 提供多種樣式和功能的標籤頁組件
 */

import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 標籤頁容器
const TabsContainer = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  flex-direction: column;
  width: 100%;
  background-color: ${props => getThemeColors(props.theme).background.primary};
`;

// 標籤頁頭部
const TabsHeader = styled.div<{ theme: 'light' | 'dark'; variant: 'line' | 'card' | 'segment' }>`
  display: flex;
  align-items: center;
  position: relative;
  background-color: ${props => {
    if (props.variant === 'card') {
      return getThemeColors(props.theme).background.secondary;
    }
    return getThemeColors(props.theme).background.primary;
  }};
  border-bottom: ${props => {
    if (props.variant === 'line') {
      return `1px solid ${getThemeColors(props.theme).border.primary}`;
    }
    return 'none';
  }};
  overflow-x: auto;
  overflow-y: hidden;
  
  /* 隱藏滾動條但保持滾動功能 */
  scrollbar-width: none;
  -ms-overflow-style: none;
  &::-webkit-scrollbar {
    display: none;
  }
`;

// 標籤頁項目
const TabItem = styled.button<{
  theme: 'light' | 'dark';
  variant: 'line' | 'card' | 'segment';
  active?: boolean;
  disabled?: boolean;
  closable?: boolean;
}>`
  display: flex;
  align-items: center;
  gap: ${spacing.xs};
  padding: ${props => {
    if (props.variant === 'segment') {
      return `${spacing.xs} ${spacing.sm}`;
    }
    return `${spacing.sm} ${spacing.md}`;
  }};
  border: none;
  background: none;
  color: ${props => {
    if (props.disabled) {
      return getThemeColors(props.theme).text.disabled;
    }
    if (props.active) {
      return getThemeColors(props.theme).text.primary;
    }
    return getThemeColors(props.theme).text.secondary;
  }};
  font-size: 13px;
  font-weight: ${props => props.active ? 500 : 400};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  white-space: nowrap;
  position: relative;
  transition: all ${transitions.fast} ease;
  min-width: 0;
  flex-shrink: 0;
  
  ${props => {
    if (props.variant === 'card') {
      return `
        background-color: ${props.active 
          ? getThemeColors(props.theme).background.primary 
          : getThemeColors(props.theme).background.secondary};
        border: 1px solid ${getThemeColors(props.theme).border.primary};
        border-bottom: ${props.active ? 'none' : `1px solid ${getThemeColors(props.theme).border.primary}`};
        border-radius: ${borderRadius.sm} ${borderRadius.sm} 0 0;
        margin-bottom: ${props.active ? '1px' : '0'};
        z-index: ${props.active ? 2 : 1};
      `;
    }
    
    if (props.variant === 'segment') {
      return `
        background-color: ${props.active 
          ? getThemeColors(props.theme).accent.primary 
          : 'transparent'};
        color: ${props.active 
          ? getThemeColors(props.theme).accent.foreground 
          : getThemeColors(props.theme).text.secondary};
        border-radius: ${borderRadius.sm};
        margin: 2px;
      `;
    }
    
    return '';
  }}
  
  &:hover:not(:disabled) {
    ${props => {
      if (props.variant === 'segment') {
        return `
          background-color: ${props.active 
            ? getThemeColors(props.theme).accent.primary 
            : getThemeColors(props.theme).background.hover};
        `;
      }
      return `
        color: ${getThemeColors(props.theme).text.primary};
        background-color: ${getThemeColors(props.theme).background.hover};
      `;
    }}
  }
  
  &:focus-visible {
    outline: 2px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: -2px;
  }
  
  /* 底部指示線 (僅 line 變體) */
  ${props => props.variant === 'line' && props.active ? `
    &::after {
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0;
      right: 0;
      height: 2px;
      background-color: ${getThemeColors(props.theme).accent.primary};
    }
  ` : ''}
`;

// 標籤頁圖標
const TabIcon = styled.span`
  display: flex;
  align-items: center;
  font-size: 14px;
  flex-shrink: 0;
`;

// 標籤頁文字
const TabText = styled.span`
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
`;

// 關閉按鈕
const CloseButton = styled.button<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: none;
  background: none;
  color: ${props => getThemeColors(props.theme).text.secondary};
  cursor: pointer;
  border-radius: ${borderRadius.xs};
  transition: all ${transitions.fast} ease;
  flex-shrink: 0;
  
  &:hover {
    background-color: ${props => getThemeColors(props.theme).background.hover};
    color: ${props => getThemeColors(props.theme).text.primary};
  }
  
  &:focus-visible {
    outline: 1px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: 1px;
  }
`;

// 標籤頁內容
const TabContent = styled.div<{ theme: 'light' | 'dark' }>`
  flex: 1;
  padding: ${spacing.md};
  background-color: ${props => getThemeColors(props.theme).background.primary};
  overflow: auto;
`;

// 標籤頁面板
const TabPane = styled.div<{ active?: boolean }>`
  display: ${props => props.active ? 'block' : 'none'};
  width: 100%;
  height: 100%;
`;

// 分段控制器容器 (segment 變體專用)
const SegmentContainer = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  border-radius: ${borderRadius.md};
  padding: 2px;
  width: fit-content;
`;

// 標籤頁項目介面
export interface TabItem {
  key: string;
  label: React.ReactNode;
  children: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
  closable?: boolean;
}

// 標籤頁組件介面
export interface TabsProps {
  theme: 'light' | 'dark';
  items: TabItem[];
  activeKey?: string;
  defaultActiveKey?: string;
  variant?: 'line' | 'card' | 'segment';
  size?: 'small' | 'medium' | 'large';
  centered?: boolean;
  animated?: boolean;
  className?: string;
  onChange?: (activeKey: string) => void;
  onEdit?: (targetKey: string, action: 'add' | 'remove') => void;
}

/**
 * 標籤頁組件
 * 提供多種樣式的標籤頁切換功能
 */
export const Tabs: React.FC<TabsProps> = ({
  theme,
  items,
  activeKey,
  defaultActiveKey,
  variant = 'line',
  size = 'medium',
  centered = false,
  animated = true,
  className,
  onChange,
  onEdit
}) => {
  const [internalActiveKey, setInternalActiveKey] = useState(
    defaultActiveKey || items[0]?.key || ''
  );
  
  const currentActiveKey = activeKey !== undefined ? activeKey : internalActiveKey;
  const activeItem = items.find(item => item.key === currentActiveKey);
  
  // 處理標籤頁切換
  const handleTabChange = (key: string) => {
    const targetItem = items.find(item => item.key === key);
    if (!targetItem || targetItem.disabled) return;
    
    setInternalActiveKey(key);
    onChange?.(key);
  };
  
  // 處理關閉標籤頁
  const handleTabClose = (event: React.MouseEvent, key: string) => {
    event.stopPropagation();
    onEdit?.(key, 'remove');
  };
  
  // 渲染標籤頁項目
  const renderTabItem = (item: TabItem) => {
    const isActive = item.key === currentActiveKey;
    
    return (
      <TabItem
        key={item.key}
        theme={theme}
        variant={variant}
        active={isActive}
        disabled={item.disabled}
        closable={item.closable}
        onClick={() => handleTabChange(item.key)}
        role="tab"
        aria-selected={isActive}
        aria-controls={`tabpanel-${item.key}`}
        id={`tab-${item.key}`}
      >
        {item.icon && (
          <TabIcon>
            {item.icon}
          </TabIcon>
        )}
        
        <TabText>
          {item.label}
        </TabText>
        
        {item.closable && (
          <CloseButton
            theme={theme}
            onClick={(event) => handleTabClose(event, item.key)}
            aria-label={`關閉 ${item.label}`}
          >
            ×
          </CloseButton>
        )}
      </TabItem>
    );
  };
  
  // 渲染標籤頁頭部
  const renderTabsHeader = () => {
    const tabItems = items.map(renderTabItem);
    
    if (variant === 'segment') {
      return (
        <SegmentContainer theme={theme}>
          {tabItems}
        </SegmentContainer>
      );
    }
    
    return (
      <TabsHeader
        theme={theme}
        variant={variant}
        style={{
          justifyContent: centered ? 'center' : 'flex-start'
        }}
      >
        {tabItems}
      </TabsHeader>
    );
  };
  
  return (
    <TabsContainer theme={theme} className={className}>
      {renderTabsHeader()}
      
      <TabContent theme={theme}>
        {items.map(item => (
          <TabPane
            key={item.key}
            active={item.key === currentActiveKey}
            role="tabpanel"
            aria-labelledby={`tab-${item.key}`}
            id={`tabpanel-${item.key}`}
          >
            {item.children}
          </TabPane>
        ))}
      </TabContent>
    </TabsContainer>
  );
};

export default Tabs;