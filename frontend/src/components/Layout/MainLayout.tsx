/**
 * 主要布局組件 - VS Code 風格五區域布局
 * 實現 Header、Activity Bar、Side Panel、Main Content、Status Bar 的完整布局
 */

import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, transitions } from '../../styles/GlobalStyles';
import type { SidebarMenuItem } from '../../types/index';

// 布局容器
const LayoutContainer = styled.div<{ theme: 'light' | 'dark' }>`
  display: grid;
  grid-template-areas:
    "header header header"
    "activity sidebar content"
    "status status status";
  grid-template-rows: 64px 1fr 24px;
  grid-template-columns: 60px 300px 1fr;
  width: 100vw;
  height: 100vh;
  background-color: ${props => getThemeColors(props.theme).background.primary};
  transition: grid-template-columns ${transitions.normal} ease;
  
  &.sidebar-collapsed {
    grid-template-columns: 60px 48px 1fr;
  }
`;

// Header 區域
const Header = styled.header<{ theme: 'light' | 'dark' }>`
  grid-area: header;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 ${spacing.lg};
  background-color: ${props => getThemeColors(props.theme).header.background};
  border-bottom: 1px solid ${props => getThemeColors(props.theme).header.border};
  color: ${props => getThemeColors(props.theme).header.foreground};
  z-index: 100;
`;

// Activity Bar 區域
const ActivityBar = styled.nav<{ theme: 'light' | 'dark' }>`
  grid-area: activity;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: ${spacing.sm} 0;
  background-color: ${props => getThemeColors(props.theme).activityBar.background};
  border-right: 1px solid ${props => getThemeColors(props.theme).activityBar.border};
  z-index: 90;
`;

// Side Panel 區域
const SidePanel = styled.aside<{ theme: 'light' | 'dark'; collapsed: boolean }>`
  grid-area: sidebar;
  display: flex;
  flex-direction: column;
  background-color: ${props => getThemeColors(props.theme).sidePanel.background};
  border-right: 1px solid ${props => getThemeColors(props.theme).sidePanel.border};
  color: ${props => getThemeColors(props.theme).sidePanel.foreground};
  overflow: hidden;
  transition: width ${transitions.normal} ease;
  z-index: 80;
  
  ${props => props.collapsed && `
    width: 48px;
    min-width: 48px;
  `}
`;

// Main Content 區域
const MainContent = styled.main<{ theme: 'light' | 'dark' }>`
  grid-area: content;
  display: flex;
  flex-direction: column;
  background-color: ${props => getThemeColors(props.theme).background.primary};
  overflow: hidden;
  position: relative;
`;

// Status Bar 區域
const StatusBar = styled.footer<{ theme: 'light' | 'dark' }>`
  grid-area: status;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 ${spacing.lg};
  background-color: ${props => getThemeColors(props.theme).statusBar.background};
  color: ${props => getThemeColors(props.theme).statusBar.foreground};
  font-size: 11px;
  z-index: 100;
`;

// Activity Bar 按鈕
const ActivityButton = styled.button<{ theme: 'light' | 'dark'; active?: boolean }>`
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: ${spacing.xs};
  background-color: ${props => props.active 
    ? getThemeColors(props.theme).interactive.selected 
    : 'transparent'
  };
  color: ${props => props.active 
    ? getThemeColors(props.theme).activityBar.foreground 
    : getThemeColors(props.theme).activityBar.inactiveForeground
  };
  border-radius: 0;
  transition: all ${transitions.fast} ease;
  
  &:hover {
    background-color: ${props => getThemeColors(props.theme).interactive.hover};
    color: ${props => getThemeColors(props.theme).activityBar.foreground};
  }
  
  &:focus {
    outline: 1px solid ${props => getThemeColors(props.theme).border.focus};
    outline-offset: -1px;
  }
  
  svg {
    width: 24px;
    height: 24px;
  }
`;

// Side Panel Header
const SidePanelHeader = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing.md} ${spacing.lg};
  border-bottom: 1px solid ${props => getThemeColors(props.theme).border.primary};
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

// Side Panel Content
const SidePanelContent = styled.div`
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
`;

// Header Title
const HeaderTitle = styled.h1`
  font-size: 14px;
  font-weight: 600;
  margin: 0;
`;

// Header Actions
const HeaderActions = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
`;

// Status Bar Section
const StatusSection = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
`;

// Collapse Toggle Button
const CollapseToggle = styled.button<{ theme: 'light' | 'dark' }>`
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  color: ${props => getThemeColors(props.theme).text.secondary};
  border-radius: 2px;
  transition: all ${transitions.fast} ease;
  
  &:hover {
    background-color: ${props => getThemeColors(props.theme).interactive.hover};
    color: ${props => getThemeColors(props.theme).text.primary};
  }
  
  svg {
    width: 16px;
    height: 16px;
  }
`;

// 主要布局組件介面
export interface MainLayoutProps {
  theme: 'light' | 'dark';
  title?: string;
  activeView?: string;
  sidebarCollapsed?: boolean;
  menuItems?: SidebarMenuItem[];
  headerActions?: React.ReactNode;
  statusLeft?: React.ReactNode;
  statusRight?: React.ReactNode;
  children: React.ReactNode;
  onViewChange?: (viewId: string) => void;
  onSidebarToggle?: (collapsed: boolean) => void;
}

/**
 * 主要布局組件
 * 提供 VS Code 風格的完整布局架構
 */
export const MainLayout: React.FC<MainLayoutProps> = ({
  theme = 'dark',
  title = 'Proxy Spider Manager',
  activeView = 'dashboard',
  sidebarCollapsed = false,
  menuItems = [],
  headerActions,
  statusLeft,
  statusRight,
  children,
  onViewChange,
  onSidebarToggle
}) => {
  const [collapsed, setCollapsed] = useState(sidebarCollapsed);
  
  // 處理側邊欄切換
  const handleSidebarToggle = useCallback(() => {
    const newCollapsed = !collapsed;
    setCollapsed(newCollapsed);
    onSidebarToggle?.(newCollapsed);
  }, [collapsed, onSidebarToggle]);
  
  // 處理視圖切換
  const handleViewChange = useCallback((viewId: string) => {
    onViewChange?.(viewId);
  }, [onViewChange]);
  
  return (
    <LayoutContainer 
      theme={theme} 
      className={collapsed ? 'sidebar-collapsed' : ''}
    >
      {/* Header 區域 */}
      <Header theme={theme}>
        <HeaderTitle>{title}</HeaderTitle>
        <HeaderActions>
          {headerActions}
        </HeaderActions>
      </Header>
      
      {/* Activity Bar 區域 */}
      <ActivityBar theme={theme}>
        {menuItems.map((item) => (
          <ActivityButton
            key={item.id}
            theme={theme}
            active={activeView === item.id}
            onClick={() => handleViewChange(item.id)}
            title={item.label}
          >
            <i className={item.icon} />
          </ActivityButton>
        ))}
      </ActivityBar>
      
      {/* Side Panel 區域 */}
      <SidePanel theme={theme} collapsed={collapsed}>
        <SidePanelHeader theme={theme}>
          {!collapsed && (
            <span>
              {menuItems.find(item => item.id === activeView)?.label || 'Explorer'}
            </span>
          )}
          <CollapseToggle 
            theme={theme} 
            onClick={handleSidebarToggle}
            title={collapsed ? '展開側邊欄' : '收縮側邊欄'}
          >
            <svg viewBox="0 0 16 16" fill="currentColor">
              <path d={collapsed 
                ? "M6 4l4 4-4 4v-8z" 
                : "M10 12l-4-4 4-4v8z"
              } />
            </svg>
          </CollapseToggle>
        </SidePanelHeader>
        
        <SidePanelContent>
          {/* 側邊欄內容將由子組件提供 */}
        </SidePanelContent>
      </SidePanel>
      
      {/* Main Content 區域 */}
      <MainContent theme={theme}>
        {children}
      </MainContent>
      
      {/* Status Bar 區域 */}
      <StatusBar theme={theme}>
        <StatusSection>
          {statusLeft}
        </StatusSection>
        <StatusSection>
          {statusRight}
        </StatusSection>
      </StatusBar>
    </LayoutContainer>
  );
};

export default MainLayout;