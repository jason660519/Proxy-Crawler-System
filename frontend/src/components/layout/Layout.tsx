import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { useTheme } from '../../hooks';
import { ActivityBar } from './ActivityBar';
import { Header } from './Header';
import { ThemeDebugger } from '../debug';

/**
 * 應用容器樣式
 */
const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  background-color: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
`;

/**
 * 主容器樣式
 */
const MainContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

/**
 * 內容區域樣式
 */
const ContentArea = styled.main`
  flex: 1;
  overflow-y: auto;
  background-color: ${props => props.theme.colors.background};
`;

/**
 * 佈局組件
 * 提供應用程式的整體佈局結構，包括導航欄、標題欄和內容區域
 */
const Layout: React.FC = () => {
  const location = useLocation();
  const { themeName, theme } = useTheme();
  const isHomepage = location.pathname === '/';

  return (
    <AppContainer>
      {/* 只在非首頁顯示側邊欄 */}
      {!isHomepage && <ActivityBar />}
      
      <MainContainer>
        {/* 只在非首頁顯示頭部 */}
        {!isHomepage && <Header />}
        
        <ContentArea>
          {/* 路由內容 */}
          <Outlet />
        </ContentArea>
      </MainContainer>
      
      {/* 主題調試器 */}
      <ThemeDebugger 
        theme={themeName}
        isDark={themeName === 'dark'}
        isVisible={false}
      />
    </AppContainer>
  );
};

export default Layout;