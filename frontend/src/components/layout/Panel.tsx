/**
 * VS Code 風格的面板區域組件
 * 提供底部面板功能，包含終端、輸出、問題、調試控制台等
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  XMarkIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  EllipsisHorizontalIcon,
  CommandLineIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  BugAntIcon,
  ClipboardDocumentListIcon,
  TrashIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';
import { cn } from '../../utils/cn';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import type { BaseComponentProps } from '../../types/components';

// ============================================================================
// 類型定義
// ============================================================================

/**
 * 面板類型
 */
export interface PanelTab {
  id: string;
  title: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
  badge?: number | string;
  closable?: boolean;
  actions?: React.ReactNode;
  searchable?: boolean;
  clearable?: boolean;
  refreshable?: boolean;
  onSearch?: (query: string) => void;
  onClear?: () => void;
  onRefresh?: () => void;
}

/**
 * 面板狀態
 */
export interface PanelState {
  isVisible: boolean;
  height: number;
  activeTabId?: string;
  maximized: boolean;
}

/**
 * 面板 Props
 */
export interface PanelProps extends BaseComponentProps {
  tabs?: PanelTab[];
  activeTab?: string;
  defaultActiveTab?: string;
  visible?: boolean;
  defaultVisible?: boolean;
  height?: number;
  defaultHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  maximized?: boolean;
  resizable?: boolean;
  collapsible?: boolean;
  onTabChange?: (tabId: string) => void;
  onVisibilityChange?: (visible: boolean) => void;
  onHeightChange?: (height: number) => void;
  onMaximize?: (maximized: boolean) => void;
  emptyState?: React.ReactNode;
}

/**
 * 面板標籤 Props
 */
interface PanelTabProps {
  tab: PanelTab;
  active: boolean;
  onActivate: () => void;
  onClose?: () => void;
}

/**
 * 面板工具欄 Props
 */
interface PanelToolbarProps {
  activeTab?: PanelTab;
  onClose: () => void;
  onMaximize: () => void;
  onMinimize: () => void;
  maximized: boolean;
  searchQuery?: string;
  onSearch?: (query: string) => void;
}

// ============================================================================
// 面板標籤組件
// ============================================================================

const PanelTabComponent: React.FC<PanelTabProps> = ({
  tab,
  active,
  onActivate,
  onClose,
}) => {
  const { t } = useTranslation();
  
  return (
    <div
      className={cn(
        'group flex items-center px-3 py-2 cursor-pointer select-none',
        'border-r border-vscode-panel-border',
        'transition-colors duration-150',
        {
          'bg-vscode-panel-background text-vscode-panel-foreground border-b-2 border-vscode-panelTitle-activeBorder': active,
          'bg-vscode-panelTitle-inactiveBackground text-vscode-panelTitle-inactiveForeground hover:bg-vscode-panelTitle-hoverBackground': !active,
        }
      )}
      onClick={onActivate}
    >
      {/* 圖標 */}
      {tab.icon && (
        <div className="w-4 h-4 mr-2 flex-shrink-0">
          {tab.icon}
        </div>
      )}
      
      {/* 標題 */}
      <span className="text-sm font-medium">
        {t(tab.title)}
      </span>
      
      {/* 徽章 */}
      {tab.badge && (
        <span
          className={cn(
            'ml-2 px-1.5 py-0.5',
            'bg-vscode-badge-background text-vscode-badge-foreground',
            'text-xs font-medium rounded',
            'flex-shrink-0'
          )}
        >
          {typeof tab.badge === 'number' && tab.badge > 99 ? '99+' : tab.badge}
        </span>
      )}
      
      {/* 關閉按鈕 */}
      {tab.closable && onClose && (
        <button
          className={cn(
            'ml-2 w-4 h-4 flex-shrink-0',
            'text-vscode-panelTitle-inactiveForeground',
            'hover:text-vscode-panelTitle-activeForeground',
            'hover:bg-vscode-toolbar-hoverBackground',
            'rounded transition-colors',
            'opacity-0 group-hover:opacity-100',
            {
              'opacity-100': active,
            }
          )}
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          title={t('panel.close_tab')}
        >
          <XMarkIcon className="w-full h-full" />
        </button>
      )}
    </div>
  );
};

// ============================================================================
// 面板工具欄組件
// ============================================================================

const PanelToolbar: React.FC<PanelToolbarProps> = ({
  activeTab,
  onClose,
  onMaximize,
  onMinimize,
  maximized,
  searchQuery = '',
  onSearch,
}) => {
  const { t } = useTranslation();
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);
  const [showSearch, setShowSearch] = useState(false);
  
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalSearchQuery(value);
    onSearch?.(value);
  }, [onSearch]);
  
  const handleSearchToggle = useCallback(() => {
    setShowSearch(!showSearch);
    if (showSearch) {
      setLocalSearchQuery('');
      onSearch?.('');
    }
  }, [showSearch, onSearch]);
  
  return (
    <div className="flex items-center justify-between h-9 px-3 bg-vscode-panelTitle-background border-b border-vscode-panel-border">
      <div className="flex items-center space-x-2">
        {/* 搜索框 */}
        {showSearch && activeTab?.searchable && (
          <div className="relative">
            <input
              type="text"
              value={localSearchQuery}
              onChange={handleSearchChange}
              placeholder={t('panel.search_placeholder')}
              className={cn(
                'w-48 px-2 py-1 text-sm',
                'bg-vscode-input-background text-vscode-input-foreground',
                'border border-vscode-input-border rounded',
                'focus:outline-none focus:ring-1 focus:ring-vscode-focusBorder',
                'placeholder:text-vscode-input-placeholderForeground'
              )}
              autoFocus
            />
          </div>
        )}
      </div>
      
      <div className="flex items-center space-x-1">
        {/* 搜索按鈕 */}
        {activeTab?.searchable && (
          <button
            onClick={handleSearchToggle}
            className={cn(
              'w-6 h-6 flex items-center justify-center',
              'text-vscode-panelTitle-inactiveForeground',
              'hover:text-vscode-panelTitle-activeForeground',
              'hover:bg-vscode-toolbar-hoverBackground',
              'rounded transition-colors',
              {
                'bg-vscode-toolbar-activeBackground text-vscode-panelTitle-activeForeground': showSearch,
              }
            )}
            title={t('panel.search')}
          >
            <MagnifyingGlassIcon className="w-4 h-4" />
          </button>
        )}
        
        {/* 清除按鈕 */}
        {activeTab?.clearable && (
          <button
            onClick={activeTab.onClear}
            className={cn(
              'w-6 h-6 flex items-center justify-center',
              'text-vscode-panelTitle-inactiveForeground',
              'hover:text-vscode-panelTitle-activeForeground',
              'hover:bg-vscode-toolbar-hoverBackground',
              'rounded transition-colors'
            )}
            title={t('panel.clear')}
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        )}
        
        {/* 刷新按鈕 */}
        {activeTab?.refreshable && (
          <button
            onClick={activeTab.onRefresh}
            className={cn(
              'w-6 h-6 flex items-center justify-center',
              'text-vscode-panelTitle-inactiveForeground',
              'hover:text-vscode-panelTitle-activeForeground',
              'hover:bg-vscode-toolbar-hoverBackground',
              'rounded transition-colors'
            )}
            title={t('panel.refresh')}
          >
            <ArrowPathIcon className="w-4 h-4" />
          </button>
        )}
        
        {/* 自定義操作 */}
        {activeTab?.actions && (
          <div className="flex items-center space-x-1">
            {activeTab.actions}
          </div>
        )}
        
        {/* 分隔線 */}
        <div className="w-px h-4 bg-vscode-panel-border mx-1" />
        
        {/* 最大化/還原按鈕 */}
        <button
          onClick={maximized ? onMinimize : onMaximize}
          className={cn(
            'w-6 h-6 flex items-center justify-center',
            'text-vscode-panelTitle-inactiveForeground',
            'hover:text-vscode-panelTitle-activeForeground',
            'hover:bg-vscode-toolbar-hoverBackground',
            'rounded transition-colors'
          )}
          title={maximized ? t('panel.restore') : t('panel.maximize')}
        >
          {maximized ? (
            <ChevronDownIcon className="w-4 h-4" />
          ) : (
            <ChevronUpIcon className="w-4 h-4" />
          )}
        </button>
        
        {/* 關閉按鈕 */}
        <button
          onClick={onClose}
          className={cn(
            'w-6 h-6 flex items-center justify-center',
            'text-vscode-panelTitle-inactiveForeground',
            'hover:text-vscode-panelTitle-activeForeground',
            'hover:bg-vscode-toolbar-hoverBackground',
            'rounded transition-colors'
          )}
          title={t('panel.close')}
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// 主要面板組件
// ============================================================================

export const Panel: React.FC<PanelProps> = ({
  tabs = [],
  activeTab,
  defaultActiveTab,
  visible,
  defaultVisible = false,
  height,
  defaultHeight = 200,
  minHeight = 100,
  maxHeight = 600,
  maximized = false,
  resizable = true,
  collapsible = true,
  onTabChange,
  onVisibilityChange,
  onHeightChange,
  onMaximize,
  emptyState,
  className,
  children,
  ...props
}) => {
  const { t } = useTranslation();
  
  // 面板狀態
  const [panelState, setPanelState] = useLocalStorage<PanelState>(
    'panel-state',
    {
      isVisible: visible ?? defaultVisible,
      height: height ?? defaultHeight,
      activeTabId: activeTab || defaultActiveTab || tabs[0]?.id,
      maximized: false,
    }
  );
  
  // 搜索狀態
  const [searchQuery, setSearchQuery] = useState('');
  
  // 拖拽調整大小
  const [isDragging, setIsDragging] = useState(false);
  const dragStartY = useRef<number>(0);
  const dragStartHeight = useRef<number>(0);
  
  // 當前活動標籤
  const currentActiveTab = tabs.find(tab => tab.id === panelState.activeTabId);
  
  // 同步外部狀態
  useEffect(() => {
    if (visible !== undefined && visible !== panelState.isVisible) {
      setPanelState(prev => ({ ...prev, isVisible: visible }));
    }
  }, [visible, panelState.isVisible, setPanelState]);
  
  useEffect(() => {
    if (height !== undefined && height !== panelState.height) {
      setPanelState(prev => ({ ...prev, height }));
    }
  }, [height, panelState.height, setPanelState]);
  
  useEffect(() => {
    if (activeTab && activeTab !== panelState.activeTabId) {
      setPanelState(prev => ({ ...prev, activeTabId: activeTab }));
    }
  }, [activeTab, panelState.activeTabId, setPanelState]);
  
  // 處理標籤切換
  const handleTabChange = useCallback((tabId: string) => {
    setPanelState(prev => ({ ...prev, activeTabId: tabId }));
    onTabChange?.(tabId);
  }, [setPanelState, onTabChange]);
  
  // 處理可見性切換
  const handleVisibilityChange = useCallback((newVisible: boolean) => {
    setPanelState(prev => ({ ...prev, isVisible: newVisible }));
    onVisibilityChange?.(newVisible);
  }, [setPanelState, onVisibilityChange]);
  
  // 處理最大化
  const handleMaximize = useCallback(() => {
    const newMaximized = !panelState.maximized;
    setPanelState(prev => ({ ...prev, maximized: newMaximized }));
    onMaximize?.(newMaximized);
  }, [panelState.maximized, setPanelState, onMaximize]);
  
  // 處理高度調整
  const handleHeightChange = useCallback((newHeight: number) => {
    const clampedHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));
    setPanelState(prev => ({ ...prev, height: clampedHeight }));
    onHeightChange?.(clampedHeight);
  }, [minHeight, maxHeight, setPanelState, onHeightChange]);
  
  // 拖拽開始
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    if (!resizable) return;
    
    setIsDragging(true);
    dragStartY.current = e.clientY;
    dragStartHeight.current = panelState.height;
    
    e.preventDefault();
  }, [resizable, panelState.height]);
  
  // 拖拽處理
  useEffect(() => {
    if (!isDragging) return;
    
    const handleMouseMove = (e: MouseEvent) => {
      const deltaY = dragStartY.current - e.clientY;
      const newHeight = dragStartHeight.current + deltaY;
      handleHeightChange(newHeight);
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleHeightChange]);
  
  // 處理搜索
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    currentActiveTab?.onSearch?.(query);
  }, [currentActiveTab]);
  
  // 如果不可見，返回 null
  if (!panelState.isVisible) {
    return null;
  }
  
  // 默認空狀態
  const defaultEmptyState = (
    <div className="h-full flex items-center justify-center text-vscode-descriptionForeground">
      <div className="text-center">
        <ClipboardDocumentListIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
        <h3 className="text-lg font-medium mb-2">{t('panel.no_content')}</h3>
        <p className="text-sm">{t('panel.no_content_description')}</p>
      </div>
    </div>
  );
  
  return (
    <div
      className={cn(
        'flex flex-col bg-vscode-panel-background border-t border-vscode-panel-border',
        {
          'h-full': panelState.maximized,
        },
        className
      )}
      style={{
        height: panelState.maximized ? '100%' : panelState.height,
      }}
      {...props}
    >
      {/* 拖拽調整大小的手柄 */}
      {resizable && !panelState.maximized && (
        <div
          className={cn(
            'h-1 cursor-row-resize',
            'hover:bg-vscode-sash-hoverBorder',
            'transition-colors',
            {
              'bg-vscode-sash-activeBorder': isDragging,
            }
          )}
          onMouseDown={handleDragStart}
        />
      )}
      
      {/* 標籤欄 */}
      <div className="flex items-center bg-vscode-panelTitle-background">
        {/* 標籤列表 */}
        <div className="flex flex-1 overflow-x-auto scrollbar-none">
          {tabs.map((tab) => (
            <PanelTabComponent
              key={tab.id}
              tab={tab}
              active={tab.id === panelState.activeTabId}
              onActivate={() => handleTabChange(tab.id)}
            />
          ))}
        </div>
        
        {/* 工具欄 */}
        <PanelToolbar
          activeTab={currentActiveTab}
          onClose={() => handleVisibilityChange(false)}
          onMaximize={handleMaximize}
          onMinimize={handleMaximize}
          maximized={panelState.maximized}
          searchQuery={searchQuery}
          onSearch={handleSearch}
        />
      </div>
      
      {/* 面板內容 */}
      <div className="flex-1 overflow-hidden">
        {currentActiveTab ? (
          <div className="h-full">
            {currentActiveTab.content}
          </div>
        ) : children ? (
          <div className="h-full">
            {children}
          </div>
        ) : (
          emptyState || defaultEmptyState
        )}
      </div>
    </div>
  );
};

// ============================================================================
// 面板內容組件
// ============================================================================

/**
 * 面板內容包裝組件
 */
export const PanelContent: React.FC<BaseComponentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'h-full overflow-auto',
        'bg-vscode-panel-background text-vscode-panel-foreground',
        'p-3',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * 終端面板組件
 */
export const TerminalPanel: React.FC<BaseComponentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'h-full font-mono text-sm',
        'bg-vscode-terminal-background text-vscode-terminal-foreground',
        'p-3 overflow-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * 輸出面板組件
 */
export const OutputPanel: React.FC<BaseComponentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'h-full font-mono text-sm',
        'bg-vscode-panel-background text-vscode-panel-foreground',
        'p-3 overflow-auto whitespace-pre-wrap',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

// ============================================================================
// 預設面板標籤
// ============================================================================

/**
 * 創建預設面板標籤
 */
export const createDefaultPanelTabs = (): PanelTab[] => [
  {
    id: 'terminal',
    title: 'Terminal',
    icon: <CommandLineIcon className="w-4 h-4" />,
    content: (
      <TerminalPanel>
        <div className="text-vscode-terminal-foreground">
          <div className="mb-2">$ Welcome to Terminal</div>
          <div className="text-vscode-terminal-ansiGreen">Ready for commands...</div>
        </div>
      </TerminalPanel>
    ),
    clearable: true,
    searchable: true,
    onClear: () => console.log('Clear terminal'),
    onSearch: (query) => console.log('Search terminal:', query),
  },
  {
    id: 'output',
    title: 'Output',
    icon: <DocumentTextIcon className="w-4 h-4" />,
    content: (
      <OutputPanel>
        <div>Application output will appear here...</div>
      </OutputPanel>
    ),
    clearable: true,
    searchable: true,
    onClear: () => console.log('Clear output'),
    onSearch: (query) => console.log('Search output:', query),
  },
  {
    id: 'problems',
    title: 'Problems',
    icon: <ExclamationTriangleIcon className="w-4 h-4" />,
    content: (
      <PanelContent>
        <div className="text-vscode-descriptionForeground">
          No problems detected.
        </div>
      </PanelContent>
    ),
    badge: 0,
    clearable: true,
    refreshable: true,
    onClear: () => console.log('Clear problems'),
    onRefresh: () => console.log('Refresh problems'),
  },
  {
    id: 'debug',
    title: 'Debug Console',
    icon: <BugAntIcon className="w-4 h-4" />,
    content: (
      <TerminalPanel>
        <div className="text-vscode-debugConsole-infoForeground">
          Debug console ready...
        </div>
      </TerminalPanel>
    ),
    clearable: true,
    searchable: true,
    onClear: () => console.log('Clear debug console'),
    onSearch: (query) => console.log('Search debug console:', query),
  },
];

// ============================================================================
// 導出
// ============================================================================

export default Panel;
export type { PanelTab, PanelState };