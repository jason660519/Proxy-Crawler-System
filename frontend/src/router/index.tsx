/**
 * 路由配置
 * 定義應用程式的所有路由和對應的組件
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { Dashboard, OperationsDashboard, MetricsOverview, Settings } from '../components/dashboard';
import ProxyManagement from '../pages/ProxyManagement';
import TaskQueue from '../pages/TaskQueue';
import SystemLogs from '../pages/SystemLogs';
import UrlToParquetWizard from '../pages/UrlToParquetWizard';



/**
 * 路由路徑常量
 * 用於在組件中引用路由路徑，避免硬編碼
 */
export const ROUTES = {
  DASHBOARD: '/',
  PROXIES: '/proxies',
  TASKS: '/tasks',
  LOGS: '/logs',
  ANALYTICS: '/analytics',
  URL2PARQUET: '/url2parquet',
  ANALYSIS: '/analysis',
  SETTINGS: '/settings'
} as const;

/**
 * 導航項目配置
 * 用於 ActivityBar 組件的導航項目定義
 */
export const ROUTE_ITEMS = [
  {
    id: 'dashboard',
    path: ROUTES.DASHBOARD,
    label: '儀表板',
    icon: 'dashboard',
    description: '系統概覽和關鍵指標'
  },
  {
    id: 'proxies', 
    path: ROUTES.PROXIES,
    label: '代理管理',
    icon: 'proxy',
    description: '代理伺服器配置和狀態監控'
  },
  {
    id: 'tasks',
    path: ROUTES.TASKS,
    label: '任務佇列',
    icon: 'tasks',
    description: '爬蟲任務管理和執行狀態'
  },
  {
    id: 'logs',
    path: ROUTES.LOGS,
    label: '系統日誌',
    icon: 'logs',
    description: '系統運行日誌和錯誤追蹤'
  },
  {
    id: 'analytics',
    path: ROUTES.ANALYTICS,
    label: '數據分析',
    icon: 'analytics',
    description: '數據統計和性能分析'
  },
  {
    id: 'url2parquet',
    path: ROUTES.URL2PARQUET,
    label: 'URL 轉換',
    icon: 'convert',
    description: 'URL 到 Parquet 文件轉換工具'
  },
  {
    id: 'analysis',
    path: ROUTES.ANALYSIS,
    label: '系統分析',
    icon: 'analysis',
    description: '系統性能和運行狀態分析'
  },
  {
    id: 'settings',
    path: ROUTES.SETTINGS,
    label: '系統設定',
    icon: 'settings',
    description: '應用程式配置和偏好設定'
  }
] as const;

// AppRouter 組件接口
interface AppRouterProps {
  theme: string;
  onNotificationClick: () => void;
}

// 主路由組件
export const AppRouter: React.FC<AppRouterProps> = ({ theme, onNotificationClick }) => {
  return (
    <Routes>
      <Route path="/" element={<AppLayout theme={theme} onNotificationClick={onNotificationClick} />}>
        <Route index element={<Dashboard />} />
        <Route path="proxies" element={<ProxyManagement />} />
        <Route path="tasks" element={<TaskQueue />} />
        <Route path="logs" element={<SystemLogs />} />
        <Route path="analytics" element={
          <>
            <OperationsDashboard />
            <div style={{ marginTop: 24 }}>
              <MetricsOverview />
            </div>
          </>
        } />
        <Route path="url2parquet" element={<UrlToParquetWizard />} />
        <Route path="analysis" element={<div>系統分析功能開發中...</div>} />
        <Route path="settings" element={<Settings />} />
      </Route>
      
      {/* 404 重定向到首頁 */}
      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  );
};

export default AppRouter;