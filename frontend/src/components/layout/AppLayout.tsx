/**
 * 應用程式主要佈局組件
 * 包含 Header、ActivityBar 和主要內容區域
 * 使用 React Router 的 Outlet 來渲染子路由
 */

import React from 'react';
import { Outlet } from 'react-router-dom';
import styled from 'styled-components';
import { Header } from './Header';
import { ActivityBar } from './ActivityBar';

/**
 * 主要佈局容器
 */
const LayoutContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-background);
  color: var(--color-text-primary);
`;

/**
 * 內容區域容器
 */
const ContentContainer = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

/**
 * 主要內容區域
 */
const MainContent = styled.main`
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--color-background);
  
  /* 自定義滾動條樣式 */
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--color-background-secondary);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--color-border);
    border-radius: 4px;
    
    &:hover {
      background: var(--color-text-secondary);
    }
  }
`;

/**
 * 頁面標題容器
 */
const PageHeader = styled.div`
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
`;

/**
 * 頁面標題
 */
const PageTitle = styled.h1`
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  line-height: 1.2;
`;

/**
 * 頁面描述
 */
const PageDescription = styled.p`
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 8px 0 0 0;
  line-height: 1.5;
`;

/**
 * 應用程式佈局組件接口
 */
interface AppLayoutProps {
  theme: string;
  onNotificationClick: () => void;
}

/**
 * 應用程式佈局組件
 * 提供統一的頁面結構和導航
 */
export const AppLayout: React.FC<AppLayoutProps> = ({ theme, onNotificationClick }) => {
  return (
    <LayoutContainer>
      {/* 頂部標題欄 */}
      <Header 
        showSearch={true}
        showQuickActions={true}
        showNotifications={true}
        themeName={theme as 'light' | 'dark'}
        onToggleTheme={() => {
          // 與 useTheme 保持同一來源，避免多實例不同步
          try { (window as any).dispatchEvent?.(new CustomEvent('js-theme-request-toggle')); } catch {}
        }}
        onNotificationClick={onNotificationClick}
      />
      
      {/* 主要內容區域 */}
      <ContentContainer>
        {/* 左側活動欄 */}
        <ActivityBar />
        
        {/* 主要內容 */}
        <MainContent>
          {/* 使用 Outlet 渲染當前路由的組件 */}
          <Outlet />
        </MainContent>
      </ContentContainer>
    </LayoutContainer>
  );
};

/**
 * 頁面包裝器組件
 * 為頁面提供統一的標題和描述格式
 */
interface PageWrapperProps {
  title: string;
  description?: string;
  children: React.ReactNode;
}

export const PageWrapper: React.FC<PageWrapperProps> = ({ 
  title, 
  description, 
  children 
}) => {
  return (
    <>
      <PageHeader>
        <PageTitle>{title}</PageTitle>
        {description && (
          <PageDescription>{description}</PageDescription>
        )}
      </PageHeader>
      {children}
    </>
  );
};

export default AppLayout;