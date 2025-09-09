/**
 * App 主組件
 * 應用程式的根組件，整合所有佈局和路由
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components';
import { ThemeDebugger } from './components/debug';
import { useTheme, useHealthStatus } from './hooks';
import { createGlobalStyles, lightTheme, darkTheme } from './styles';
import { AppRouter } from './router';


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

// 移除未使用的styled組件



// ============= 組件實作 =============

const App: React.FC = () => {
  const { isDark, theme } = useTheme();
  useHealthStatus();
  const [isInitializing, setIsInitializing] = useState(true);
  
  // 控制是否顯示主題調試器（僅開發環境，且需使用者顯式開啟）
  const isThemeDebugVisible = (() => {
    try {
      const url = new URL(window.location.href);
      const qp = url.searchParams.get('debugTheme');
      if (qp === '1') {
        window.sessionStorage.setItem('js-theme-debugger', '1');
      } else if (qp === '0') {
        window.sessionStorage.removeItem('js-theme-debugger');
      }
      return Boolean(import.meta.env.DEV && window.sessionStorage.getItem('js-theme-debugger') === '1');
    } catch {
      return false;
    }
  })();

  // 模擬初始化過程
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitializing(false);
    }, 1500);

    return () => clearTimeout(timer);
  }, []);

  // 處理通知點擊
  const handleNotificationClick = () => {
    console.log('Open notifications panel');
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
      <BrowserRouter>
        <AppContainer>
          <AppRouter 
            theme={theme}
            onNotificationClick={handleNotificationClick}
          />
          
          {/* 主題調試器 - 只在開發環境顯示 */}
          {isThemeDebugVisible && (
            <ThemeDebugger 
              theme={theme} 
              isDark={isDark} 
              isVisible={true}
            />
          )}
        </AppContainer>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;