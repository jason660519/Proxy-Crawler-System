import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { ThemeProvider } from 'styled-components';
import { ConfigProvider } from '../components/ui';
import { useTheme } from '../hooks';
import { GlobalStyle } from '../styles/GlobalStyle';
import Layout from '../components/layout/Layout';
import {
  Homepage,
  DashboardPage,
  ProxiesPage,
  TasksPage,
  LogsPage,
  AnalyticsPage,
  SettingsPage
} from '../pages';

/**
 * 路由配置
 * 定義應用的所有路由和對應的頁面組件
 */
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Homepage />
      },
      {
        path: 'dashboard',
        element: <DashboardPage />
      },
      {
        path: 'proxies',
        element: <ProxiesPage />
      },
      {
        path: 'tasks',
        element: <TasksPage />
      },
      {
        path: 'logs',
        element: <LogsPage />
      },
      {
        path: 'analytics',
        element: <AnalyticsPage />
      },
      {
        path: 'settings',
        element: <SettingsPage />
      }
    ]
  }
]);

/**
 * 主題包裝組件
 * 為整個應用提供主題上下文
 */
const ThemeWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme } = useTheme();
  
  return (
    <HelmetProvider>
      <ThemeProvider theme={theme}>
        <ConfigProvider>
          <GlobalStyle />
          {children}
        </ConfigProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
};

/**
 * 應用路由組件
 * 提供整個應用的路由配置
 */
const AppRouter: React.FC = () => {
  return (
    <ThemeWrapper>
      <RouterProvider router={router} />
    </ThemeWrapper>
  );
};

export default AppRouter;