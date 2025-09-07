/**
 * App 主組件
 * 應用程式的根組件，整合所有佈局和路由
 */

import React, { useState, useEffect } from 'react';
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components';
import { Header, ActivityBar } from './components/layout';
import { Dashboard, OperationsDashboard } from './components/dashboard';
import { ThemeDebugger } from './components/debug';
import { useTheme, useHealthStatus } from './hooks';
import { createGlobalStyles, lightTheme, darkTheme } from './styles';


// ============= 全域樣式 =============

const GlobalStyle = createGlobalStyle<{ theme: typeof lightTheme }>`
  ${props => createGlobalStyles(props.theme)}
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
  const { isDark, theme } = useTheme();
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
          <>
            <OperationsDashboard />
            {/* Native metrics overview under Grafana embed */}
            {/* @ts-ignore: dynamically added component */}
            {require('./components/dashboard').MetricsOverview && (
              (React.createElement(require('./components/dashboard').MetricsOverview))
            )}
          </>
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
        
        {/* 主題調試器 - 只在開發環境顯示 */}
        {import.meta.env.DEV && (
          <ThemeDebugger 
            theme={theme} 
            isDark={isDark} 
            isVisible={true}
          />
        )}
      </AppContainer>
    </ThemeProvider>
  );
};

export default App;