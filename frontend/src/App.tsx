/**
 * 主應用程式組件
 * 整合布局、路由、主題管理等核心功能
 */

import React, { useState, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import { GlobalStyles } from './styles/GlobalStyles';
import { MainLayout } from './components/Layout/MainLayout';
import { Dashboard } from './pages/Dashboard';
import type { SidebarMenuItem } from './types/index';

// 主題切換按鈕組件
const ThemeToggle: React.FC<{ theme: 'light' | 'dark'; onToggle: () => void }> = ({ theme, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      style={{
        background: 'transparent',
        border: 'none',
        color: 'inherit',
        cursor: 'pointer',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px'
      }}
      title={`切換到${theme === 'dark' ? '淺色' : '深色'}主題`}
    >
      {theme === 'dark' ? '🌙' : '☀️'}
    </button>
  );
};

// 狀態指示器組件
const StatusIndicator: React.FC<{ theme: 'light' | 'dark' }> = ({ theme }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
      <span style={{ color: '#00ff00' }}>●</span>
      <span>系統正常</span>
      <span style={{ marginLeft: '16px' }}>v1.0.0</span>
    </div>
  );
};

// 連接狀態組件
const ConnectionStatus: React.FC<{ theme: 'light' | 'dark' }> = ({ theme }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '11px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <span style={{ color: '#00ff00' }}>●</span>
        <span>後端已連接</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <span style={{ color: '#ffaa00' }}>●</span>
        <span>8 個任務執行中</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <span>代理池: 892/1247</span>
      </div>
    </div>
  );
};

/**
 * 主應用程式組件
 */
function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [activeView, setActiveView] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 主題切換處理
  const handleThemeToggle = useCallback(() => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  }, []);

  // 視圖切換處理
  const handleViewChange = useCallback((viewId: string) => {
    setActiveView(viewId);
  }, []);

  // 側邊欄切換處理
  const handleSidebarToggle = useCallback((collapsed: boolean) => {
    setSidebarCollapsed(collapsed);
  }, []);

  // 側邊欄選單項目
  const menuItems: SidebarMenuItem[] = [
    {
      id: 'dashboard',
      label: '儀表板',
      icon: 'dashboard-icon',
      path: '/dashboard'
    },
    {
      id: 'proxies',
      label: '代理池管理',
      icon: 'proxy-icon',
      path: '/proxies'
    },
    {
      id: 'etl',
      label: 'ETL 監控',
      icon: 'etl-icon',
      path: '/etl'
    },
    {
      id: 'settings',
      label: '系統設置',
      icon: 'settings-icon',
      path: '/settings'
    }
  ];

  // Header 操作按鈕
  const headerActions = (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <button
        style={{
          background: 'transparent',
          border: 'none',
          color: 'inherit',
          cursor: 'pointer',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px'
        }}
        title="通知"
      >
        🔔
      </button>
      <button
        style={{
          background: 'transparent',
          border: 'none',
          color: 'inherit',
          cursor: 'pointer',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px'
        }}
        title="使用者選單"
      >
        👤
      </button>
      <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
    </div>
  );

  return (
    <ThemeProvider theme={{ mode: theme }}>
      <GlobalStyles theme={theme} />
      <Router>
        <MainLayout
          theme={theme}
          title="Proxy Spider Manager"
          activeView={activeView}
          sidebarCollapsed={sidebarCollapsed}
          menuItems={menuItems}
          headerActions={headerActions}
          statusLeft={<StatusIndicator theme={theme} />}
          statusRight={<ConnectionStatus theme={theme} />}
          onViewChange={handleViewChange}
          onSidebarToggle={handleSidebarToggle}
        >
          <Routes>
            {/* 預設路由重定向到儀表板 */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* 儀表板頁面 */}
            <Route 
              path="/dashboard" 
              element={<Dashboard theme={theme} />} 
            />
            
            {/* 代理池管理頁面 */}
            <Route 
              path="/proxies" 
              element={
                <div style={{ 
                  padding: '24px', 
                  textAlign: 'center',
                  color: theme === 'dark' ? '#cccccc' : '#666666'
                }}>
                  <h2>代理池管理</h2>
                  <p>此頁面正在開發中...</p>
                </div>
              } 
            />
            
            {/* ETL 監控頁面 */}
            <Route 
              path="/etl" 
              element={
                <div style={{ 
                  padding: '24px', 
                  textAlign: 'center',
                  color: theme === 'dark' ? '#cccccc' : '#666666'
                }}>
                  <h2>ETL 監控</h2>
                  <p>此頁面正在開發中...</p>
                </div>
              } 
            />
            
            {/* 系統設置頁面 */}
            <Route 
              path="/settings" 
              element={
                <div style={{ 
                  padding: '24px', 
                  textAlign: 'center',
                  color: theme === 'dark' ? '#cccccc' : '#666666'
                }}>
                  <h2>系統設置</h2>
                  <p>此頁面正在開發中...</p>
                </div>
              } 
            />
            
            {/* 404 頁面 */}
            <Route 
              path="*" 
              element={
                <div style={{ 
                  padding: '24px', 
                  textAlign: 'center',
                  color: theme === 'dark' ? '#cccccc' : '#666666'
                }}>
                  <h2>頁面未找到</h2>
                  <p>您訪問的頁面不存在</p>
                </div>
              } 
            />
          </Routes>
        </MainLayout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
