/**
 * App 主組件
 * 應用程式的根組件，整合所有佈局和路由
 */

import React, { useState, useEffect } from 'react';
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components';
import { Header, ActivityBar } from './components/layout';
import { Dashboard } from './components/dashboard';
import { useTheme, useHealthStatus } from './hooks';
import { lightTheme, darkTheme, globalStyles } from './styles';


// ============= 全域樣式 =============

const GlobalStyle = createGlobalStyle`
  ${globalStyles}
  
  :root {
    /* 背景色變數 */
    --color-background-primary: ${props => props.theme.colors.background.primary};
    --color-background-secondary: ${props => props.theme.colors.background.secondary};
    --color-background-tertiary: ${props => props.theme.colors.background.tertiary};
    --color-background-elevated: ${props => props.theme.colors.background.elevated};
    --color-background-card: ${props => props.theme.colors.background.elevated};
    --color-background-hover: ${props => props.theme.colors.background.secondary};
    --color-background-disabled: ${props => props.theme.colors.background.secondary};
    --color-background-tooltip: ${props => props.theme.colors.background.tertiary};
    --color-background-primary-80: ${props => props.theme.colors.background.primary};
    
    /* 文字顏色變數 */
    --color-text-primary: ${props => props.theme.colors.text.primary};
    --color-text-secondary: ${props => props.theme.colors.text.secondary};
    --color-text-tertiary: ${props => props.theme.colors.text.tertiary};
    --color-text-inverse: ${props => props.theme.colors.text.inverse};
    --color-text-disabled: ${props => props.theme.colors.text.disabled};
    
    /* 邊框顏色變數 */
    --color-border-primary: ${props => props.theme.colors.border.primary};
    --color-border-secondary: ${props => props.theme.colors.border.secondary};
    --color-border-focus: ${props => props.theme.colors.border.focus};
    --color-border-default: ${props => props.theme.colors.border.primary};
    --color-border-light: ${props => props.theme.colors.border.secondary};
    --color-border-hover: ${props => props.theme.colors.border.focus};
    --color-border-focus-shadow: ${props => props.theme.colors.border.focus}33;
    
    /* 狀態顏色變數 */
    --color-status-success: ${props => props.theme.colors.status.success};
    --color-status-warning: ${props => props.theme.colors.status.warning};
    --color-status-error: ${props => props.theme.colors.status.error};
    --color-status-info: ${props => props.theme.colors.status.info};
    --color-status-success-bg: ${props => props.theme.colors.status.success}20;
    --color-status-warning-bg: ${props => props.theme.colors.status.warning}20;
    --color-status-error-bg: ${props => props.theme.colors.status.error}20;
    --color-status-success-light: ${props => props.theme.colors.status.success}20;
    --color-status-error-light: ${props => props.theme.colors.status.error}20;
    --color-status-warning-light: ${props => props.theme.colors.status.warning}20;
    
    /* 互動顏色變數 */
    --color-interactive-primary: ${props => props.theme.colors.interactive.primary};
    --color-interactive-primaryHover: ${props => props.theme.colors.interactive.primaryHover};
    --color-interactive-primaryActive: ${props => props.theme.colors.interactive.primaryActive};
    --color-interactive-secondary: ${props => props.theme.colors.interactive.secondary};
    --color-interactive-secondaryHover: ${props => props.theme.colors.interactive.secondaryHover};
    --color-interactive-secondaryActive: ${props => props.theme.colors.interactive.secondaryActive};
    
    /* Primary 色系變數 */
    --color-primary-400: ${props => props.theme.name === 'light' ? '#60a5fa' : '#60a5fa'};
    --color-primary-500: ${props => props.theme.colors.interactive.primary};
    --color-primary-600: ${props => props.theme.colors.interactive.primaryHover};
    --color-primary-700: ${props => props.theme.colors.interactive.primaryActive};
    --color-primary-100: ${props => props.theme.name === 'light' ? '#dbeafe' : '#1e3a8a'};
    --color-primary-500-alpha-20: ${props => props.theme.colors.interactive.primary}33;
    
    /* Neutral/Gray 色系變數 */
    --color-neutral-100: ${props => props.theme.name === 'light' ? '#f5f5f5' : '#262626'};
    --color-neutral-200: ${props => props.theme.name === 'light' ? '#e5e5e5' : '#404040'};
    --color-neutral-300: ${props => props.theme.name === 'light' ? '#d4d4d4' : '#525252'};
    --color-neutral-400: ${props => props.theme.colors.text.tertiary};
    --color-neutral-500: ${props => props.theme.name === 'light' ? '#737373' : '#737373'};
    --color-neutral-600: ${props => props.theme.name === 'light' ? '#525252' : '#a3a3a3'};
    --color-neutral-700: ${props => props.theme.name === 'light' ? '#404040' : '#d4d4d4'};
    --color-neutral-800: ${props => props.theme.colors.background.secondary};
    --color-neutral-900: ${props => props.theme.colors.background.primary};
    --color-neutral-800-50: ${props => props.theme.colors.background.secondary}80;
    
    /* 其他顏色變數 */
    --color-white: ${props => props.theme.name === 'light' ? '#ffffff' : '#000000'};
  }
`;

// ============= 樣式定義 =============

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--color-background-primary);
  color: var(--color-text-primary);
`;

const MainContainer = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

const ContentArea = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--color-background-primary);
`;

const PageContent = styled.div`
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: var(--color-background-primary);
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: var(--color-background-primary);
  color: var(--color-text-primary);
`;

const LoadingSpinner = styled.div`
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-border-primary);
  border-top: 4px solid var(--color-interactive-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const WelcomeMessage = styled.div`
  text-align: center;
  padding: 48px 24px;
`;

const WelcomeTitle = styled.h1`
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 16px;
  background: linear-gradient(135deg, var(--color-interactive-primary), var(--color-interactive-primaryHover));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const WelcomeSubtitle = styled.p`
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  margin-bottom: 32px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
`;



// ============= 組件實作 =============

const App: React.FC = () => {
  const { isDark } = useTheme();
  useHealthStatus();
  const [activeView, setActiveView] = useState('dashboard');
  const [isInitializing, setIsInitializing] = useState(true);

  // 模擬初始化過程
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitializing(false);
    }, 1500);

    return () => clearTimeout(timer);
  }, []);

  // 處理活動項目變更
  const handleActivityChange = (itemId: string) => {
    setActiveView(itemId);
  };

  // 處理通知點擊
  const handleNotificationClick = () => {
    console.log('Open notifications panel');
  };

  // 渲染頁面內容
  const renderPageContent = () => {
    switch (activeView) {
      case 'dashboard':
        return (
          <Dashboard />
        );
      
      case 'proxies':
        return (
          <WelcomeMessage>
            <WelcomeTitle>代理管理</WelcomeTitle>
            <WelcomeSubtitle>代理節點管理功能正在開發中...</WelcomeSubtitle>
          </WelcomeMessage>
        );
      
      case 'tasks':
        return (
          <WelcomeMessage>
            <WelcomeTitle>任務佇列</WelcomeTitle>
            <WelcomeSubtitle>任務管理功能正在開發中...</WelcomeSubtitle>
          </WelcomeMessage>
        );
      
      case 'logs':
        return (
          <WelcomeMessage>
            <WelcomeTitle>系統日誌</WelcomeTitle>
            <WelcomeSubtitle>日誌查看功能正在開發中...</WelcomeSubtitle>
          </WelcomeMessage>
        );
      
      case 'analytics':
        return (
          <WelcomeMessage>
            <WelcomeTitle>數據分析</WelcomeTitle>
            <WelcomeSubtitle>數據分析功能正在開發中...</WelcomeSubtitle>
          </WelcomeMessage>
        );
      
      case 'settings':
        return (
          <WelcomeMessage>
            <WelcomeTitle>系統設定</WelcomeTitle>
            <WelcomeSubtitle>系統設定功能正在開發中...</WelcomeSubtitle>
          </WelcomeMessage>
        );
      
      default:
        return (
          <WelcomeMessage>
            <WelcomeTitle>頁面未找到</WelcomeTitle>
            <WelcomeSubtitle>請選擇左側導航中的功能項目。</WelcomeSubtitle>
          </WelcomeMessage>
        );
    }
  };

  // 顯示載入畫面
  if (isInitializing) {
    return (
      <ThemeProvider theme={isDark ? darkTheme : lightTheme}>
        <GlobalStyle theme={isDark ? darkTheme : lightTheme} />
        <LoadingContainer>
          <div style={{ textAlign: 'center' }}>
            <LoadingSpinner />
            <div style={{ marginTop: '16px', fontSize: '1.125rem' }}>
              JasonSpider 正在啟動...
            </div>
          </div>
        </LoadingContainer>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={isDark ? darkTheme : lightTheme}>
      <GlobalStyle theme={isDark ? darkTheme : lightTheme} />
      <AppContainer>
        <Header
          showSearch={true}
          showQuickActions={true}
          showNotifications={true}
          onNotificationClick={handleNotificationClick}
        />
        
        <MainContainer>
          <ActivityBar
            activeItem={activeView}
            onItemChange={handleActivityChange}
          />
          
          <ContentArea>
            <PageContent>
              {renderPageContent()}
            </PageContent>
          </ContentArea>
        </MainContainer>
      </AppContainer>
    </ThemeProvider>
  );
};

export default App;