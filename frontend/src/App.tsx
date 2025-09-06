import React, { Suspense, useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

// 樣式
import './styles/layout.css';

// Layout Components
import { Layout } from './components/layout/Layout';
import { ActivityBar } from './components/layout/ActivityBar';
import { Sidebar } from './components/layout/Sidebar';
import { Editor } from './components/layout/Editor';
import { Panel } from './components/layout/Panel';
import { StatusBar } from './components/layout/StatusBar';

// Pages
import { Dashboard } from './pages/Dashboard';
import { ProxyList } from './pages/ProxyList';
import { ProxyPool } from './pages/ProxyPool';
import { QualityAnalysis } from './pages/QualityAnalysis';
import { TaskScheduling } from './pages/TaskScheduling';
import { CrawlerTasks } from './pages/CrawlerTasks';
import { DataExport } from './pages/DataExport';
import { SystemSettings } from './pages/SystemSettings';
import { Monitoring } from './pages/Monitoring';
import { UserProfile } from './pages/UserProfile';

// Hooks and Utils
import { useTheme } from './hooks/useTheme';
import { useLocalStorage } from './hooks/useLocalStorage';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Types
import type {
  ActivityItem,
  SidebarPanel,
  EditorTab,
  PanelTab,
  StatusBarItem,
} from './types';

interface AppState {
  activeActivity: string;
  sidebarVisible: boolean;
  sidebarWidth: number;
  panelVisible: boolean;
  panelHeight: number;
  activeEditorTab: string | null;
  activePanelTab: string | null;
  editorTabs: EditorTab[];
  panelTabs: PanelTab[];
  theme: 'light' | 'dark';
  language: string;
}

/**
 * 主應用程式組件
 * 實現VS Code風格的五區域布局：頂部欄、活動欄、側邊面板、主內容區、狀態欄
 */
const App: React.FC = () => {
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  
  // 應用程式狀態管理
  const [appState, setAppState] = useLocalStorage<AppState>('proxy-manager-app-state', {
    activeActivity: 'explorer',
    sidebarVisible: true,
    sidebarWidth: 300,
    panelVisible: false,
    panelHeight: 200,
    activeEditorTab: null,
    activePanelTab: null,
    editorTabs: [],
    panelTabs: [],
    theme: 'dark',
    language: 'zh-TW'
  });

  // 響應式設計狀態
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);

  // React Query 客戶端配置
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5分鐘
        cacheTime: 10 * 60 * 1000, // 10分鐘
        retry: 3,
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: 1,
      },
    },
  }));

  // 響應式斷點檢測
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 768);
      setIsTablet(width >= 768 && width < 1024);
      
      // 在移動設備上自動收合側邊欄
      if (width < 768 && appState.sidebarVisible) {
        setAppState(prev => ({ ...prev, sidebarVisible: false }));
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [appState.sidebarVisible, setAppState]);

  // 主題同步
  useEffect(() => {
    if (appState.theme !== theme) {
      setAppState(prev => ({ ...prev, theme }));
    }
  }, [theme, appState.theme, setAppState]);

  // 鍵盤快捷鍵處理
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl/Cmd + K: 全域搜尋
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        // TODO: 開啟全域搜尋
      }
      
      // F5: 重新整理
      if (event.key === 'F5') {
        event.preventDefault();
        window.location.reload();
      }
      
      // Ctrl/Cmd + Shift + T: 切換主題
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'T') {
        event.preventDefault();
        toggleTheme();
      }
      
      // Ctrl/Cmd + B: 切換側邊欄
      if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
        event.preventDefault();
        setAppState(prev => ({ ...prev, sidebarVisible: !prev.sidebarVisible }));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleTheme, setAppState]);

  // 活動項目切換處理
  const handleActivityChange = (activityId: string) => {
    setAppState(prev => ({
      ...prev,
      activeActivity: activityId,
      sidebarVisible: prev.activeActivity === activityId ? !prev.sidebarVisible : true,
    }));
  };

  // 側邊欄切換
  const toggleSidebar = () => {
    setAppState(prev => ({ ...prev, sidebarVisible: !prev.sidebarVisible }));
  };

  // 面板切換
  const togglePanel = () => {
    setAppState(prev => ({ ...prev, panelVisible: !prev.panelVisible }));
  };

  // 側邊欄寬度調整
  const handleSidebarResize = (width: number) => {
    setAppState(prev => ({ ...prev, sidebarWidth: Math.max(200, Math.min(600, width)) }));
  };

  // 面板高度調整
  const handlePanelResize = (height: number) => {
    setAppState(prev => ({ ...prev, panelHeight: Math.max(100, Math.min(400, height)) }));
  };

  // 打開編輯器標籤
  const openEditorTab = (id: string, title: string, type: string) => {
    setAppState(prev => {
      const existingTab = prev.editorTabs.find(tab => tab.id === id);
      
      if (existingTab) {
        // 如果標籤已存在，只需激活它
        return {
          ...prev,
          activeEditorTab: id,
          editorTabs: prev.editorTabs.map(tab => ({
            ...tab,
            isActive: tab.id === id,
          })),
        };
      } else {
        // 創建新標籤
        const newTab: EditorTab = {
          id,
          title,
          type,
          isActive: true,
          isDirty: false,
          isClosable: true,
        };
        
        return {
          ...prev,
          activeEditorTab: id,
          editorTabs: [
            ...prev.editorTabs.map(tab => ({ ...tab, isActive: false })),
            newTab,
          ],
        };
      }
    });
  };

  // 編輯器標籤點擊操作
  const handleEditorTabClick = (tabId: string) => {
    setAppState(prev => ({
      ...prev,
      activeEditorTab: tabId,
      editorTabs: prev.editorTabs.map(tab => ({
        ...tab,
        isActive: tab.id === tabId,
      })),
    }));
  };

  const handleEditorTabClose = (tabId: string) => {
    setAppState(prev => {
      const newTabs = prev.editorTabs.filter(tab => tab.id !== tabId);
      const wasActive = prev.activeEditorTab === tabId;
      
      let newActiveTab = prev.activeEditorTab;
      if (wasActive && newTabs.length > 0) {
        newActiveTab = newTabs[0].id;
      } else if (newTabs.length === 0) {
        newActiveTab = null;
      }
      
      return {
        ...prev,
        editorTabs: newTabs.map(tab => ({
          ...tab,
          isActive: tab.id === newActiveTab,
        })),
        activeEditorTab: newActiveTab,
      };
    });
  };

  // 面板標籤操作
  const handlePanelTabClick = (tabId: string) => {
    setAppState(prev => ({
      ...prev,
      activePanelTab: tabId,
      panelTabs: prev.panelTabs.map(tab => ({
        ...tab,
        isActive: tab.id === tabId,
      })),
    }));
  };

  // 狀態欄項目點擊處理
  const handleStatusBarItemClick = (itemId: string) => {
    console.log('狀態欄項目點擊:', itemId);
    
    switch (itemId) {
      case 'problems':
        setAppState(prev => ({
          ...prev,
          panelVisible: true,
          activePanelTab: 'problems',
          panelTabs: prev.panelTabs.map(tab => ({
            ...tab,
            isActive: tab.id === 'problems',
          })),
        }));
        break;
      case 'notifications':
        // 打開通知面板
        break;
      case 'connection':
        // 打開連接設置
        break;
      default:
        break;
    }
  };

  // 路由渲染
  const renderEditorContent = () => {
    if (!appState.activeEditorTab) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <h3 className="text-lg font-medium mb-2">歡迎使用代理管理器</h3>
            <p>選擇一個活動項目開始使用</p>
          </div>
        </div>
      );
    }

    const activeTab = appState.editorTabs.find(tab => tab.id === appState.activeEditorTab);
    if (!activeTab) return null;

    switch (activeTab.type) {
      case 'dashboard':
        return <Dashboard />;
      case 'proxy-list':
        return <ProxyList />;
      case 'proxy-pool':
        return <ProxyPool />;
      case 'quality-analysis':
        return <QualityAnalysis />;
      case 'task-scheduling':
        return <TaskScheduling />;
      case 'crawler-tasks':
        return <CrawlerTasks />;
      case 'data-export':
        return <DataExport />;
      case 'system-settings':
        return <SystemSettings />;
      case 'monitoring':
        return <Monitoring />;
      case 'user-profile':
        return <UserProfile />;
      default:
        return <div>未知的標籤類型</div>;
    }
  };

  // 側邊欄面板渲染
  const renderSidebarPanels = (): SidebarPanel[] => {
    switch (appState.activeActivity) {
      case 'explorer':
        return [
          {
            id: 'proxy-explorer',
            title: '代理瀏覽器',
            icon: 'folder',
            content: (
              <div className="p-4">
                <h4 className="font-medium mb-2">代理資源</h4>
                <div className="space-y-1">
                  <div className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded"
                       onClick={() => openEditorTab('proxy-list', '代理列表', 'proxy-list')}>
                    📋 代理列表
                  </div>
                  <div className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded"
                       onClick={() => openEditorTab('dashboard', '儀表板', 'dashboard')}>
                    📊 儀表板
                  </div>
                </div>
              </div>
            ),
          },
        ];
      case 'search':
        return [
          {
            id: 'search-panel',
            title: '搜尋',
            icon: 'search',
            content: (
              <div className="p-4">
                <input
                  type="text"
                  placeholder="搜尋代理..."
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                />
              </div>
            ),
          },
        ];
      case 'tasks':
        return [
          {
            id: 'task-panel',
            title: '任務',
            icon: 'list',
            content: (
              <div className="p-4">
                <div className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded"
                     onClick={() => openEditorTab('task-scheduling', '任務排程', 'task-scheduling')}>
                  ⚙️ 任務排程
                </div>
                <div className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded"
                     onClick={() => openEditorTab('crawler-tasks', '爬蟲任務', 'crawler-tasks')}>
                  🕷️ 爬蟲任務
                </div>
              </div>
            ),
          },
        ];
      case 'settings':
        return [
          {
            id: 'settings-panel',
            title: '設定',
            icon: 'settings',
            content: (
              <div className="p-4">
                <div className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded"
                     onClick={() => openEditorTab('system-settings', '系統設定', 'system-settings')}>
                  ⚙️ 系統設定
                </div>
              </div>
            ),
          },
        ];
      default:
        return [];
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Router>
          <Layout
            activityBar={
              <ActivityBar
                activeActivity={appState.activeActivity}
                onActivityChange={handleActivityChange}
                theme={theme}
              />
            }
            sidebar={
              appState.sidebarVisible ? (
                <Sidebar
                  width={appState.sidebarWidth}
                  onResize={handleSidebarResize}
                  panels={renderSidebarPanels()}
                  theme={theme}
                  isMobile={isMobile}
                />
              ) : null
            }
            editor={
              <Editor
                tabs={appState.editorTabs}
                activeTabId={appState.activeEditorTab}
                onTabClick={handleEditorTabClick}
                onTabClose={handleEditorTabClose}
                theme={theme}
              >
                <Suspense fallback={
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                      <span className="text-gray-500">載入中...</span>
                    </div>
                  </div>
                }>
                  {renderEditorContent()}
                </Suspense>
              </Editor>
            }
            panel={
              appState.panelVisible ? (
                <Panel
                  height={appState.panelHeight}
                  onResize={handlePanelResize}
                  tabs={appState.panelTabs}
                  activeTabId={appState.activePanelTab}
                  onTabClick={handlePanelTabClick}
                  theme={theme}
                />
              ) : null
            }
            statusBar={
              <StatusBar
                theme={theme}
                language={appState.language}
                connectionStatus="connected"
                activeProxies={42}
                totalProxies={150}
                onItemClick={handleStatusBarItemClick}
              />
            }
            sidebarVisible={appState.sidebarVisible}
            panelVisible={appState.panelVisible}
            sidebarWidth={appState.sidebarWidth}
            panelHeight={appState.panelHeight}
            onSidebarResize={handleSidebarResize}
            onPanelResize={handlePanelResize}
          />
          
          {/* 全域通知 */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              className: 'bg-vscode-panel-bg text-vscode-foreground border border-vscode-border',
              style: {
                background: 'var(--vscode-panel-background)',
                color: 'var(--vscode-foreground)',
                border: '1px solid var(--vscode-panel-border)',
              },
            }}
          />
        </Router>
      </ErrorBoundary>
      
      {/* React Query 開發工具 */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

export default App;