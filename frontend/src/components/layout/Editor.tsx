/**
 * VS Code 風格的編輯器區域組件
 * 提供多標籤頁編輯器功能，支持標籤管理、內容切換等
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  XMarkIcon,
  EllipsisHorizontalIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  DocumentIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { cn } from '../../utils/cn';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import type { BaseComponentProps } from '../../types/components';

// ============================================================================
// 類型定義
// ============================================================================

/**
 * 編輯器標籤頁類型
 */
export interface EditorTab {
  id: string;
  title: string;
  content: React.ReactNode;
  icon?: React.ReactNode;
  modified?: boolean;
  closable?: boolean;
  pinned?: boolean;
  path?: string;
  language?: string;
  encoding?: string;
  lineEnding?: 'LF' | 'CRLF';
  metadata?: Record<string, any>;
}

/**
 * 編輯器狀態
 */
export interface EditorState {
  activeTabId?: string;
  tabs: EditorTab[];
  tabOrder: string[];
}

/**
 * 編輯器 Props
 */
export interface EditorProps extends BaseComponentProps {
  tabs?: EditorTab[];
  activeTab?: string;
  defaultActiveTab?: string;
  maxTabs?: number;
  showTabBar?: boolean;
  showStatusBar?: boolean;
  allowTabReorder?: boolean;
  allowTabClose?: boolean;
  onTabChange?: (tabId: string) => void;
  onTabClose?: (tabId: string) => void;
  onTabAdd?: () => void;
  onTabReorder?: (fromIndex: number, toIndex: number) => void;
  emptyState?: React.ReactNode;
  statusBarContent?: React.ReactNode;
}

/**
 * 標籤頁 Props
 */
interface TabProps {
  tab: EditorTab;
  active: boolean;
  onActivate: () => void;
  onClose?: () => void;
  onMiddleClick?: () => void;
  draggable?: boolean;
  onDragStart?: (e: React.DragEvent) => void;
  onDragOver?: (e: React.DragEvent) => void;
  onDrop?: (e: React.DragEvent) => void;
}

/**
 * 標籤欄 Props
 */
interface TabBarProps {
  tabs: EditorTab[];
  activeTabId?: string;
  onTabChange: (tabId: string) => void;
  onTabClose?: (tabId: string) => void;
  onTabAdd?: () => void;
  allowReorder?: boolean;
  onTabReorder?: (fromIndex: number, toIndex: number) => void;
  maxTabs?: number;
}

// ============================================================================
// 標籤頁組件
// ============================================================================

const Tab: React.FC<TabProps> = ({
  tab,
  active,
  onActivate,
  onClose,
  onMiddleClick,
  draggable = false,
  onDragStart,
  onDragOver,
  onDrop,
}) => {
  const { t } = useTranslation();
  const [isDragging, setIsDragging] = useState(false);
  
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 1) { // 中鍵點擊
      e.preventDefault();
      onMiddleClick?.();
    }
  }, [onMiddleClick]);
  
  const handleDragStart = useCallback((e: React.DragEvent) => {
    setIsDragging(true);
    e.dataTransfer.setData('text/plain', tab.id);
    onDragStart?.(e);
  }, [tab.id, onDragStart]);
  
  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    onDragOver?.(e);
  }, [onDragOver]);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    onDrop?.(e);
  }, [onDrop]);
  
  return (
    <div
      className={cn(
        'group relative flex items-center',
        'h-9 px-3 border-r border-vscode-tab-border',
        'cursor-pointer select-none',
        'transition-all duration-150',
        {
          'bg-vscode-tab-activeBackground text-vscode-tab-activeForeground border-b-2 border-vscode-tab-activeBorder': active,
          'bg-vscode-tab-inactiveBackground text-vscode-tab-inactiveForeground hover:bg-vscode-tab-hoverBackground': !active,
          'opacity-50': isDragging,
          'min-w-0 max-w-xs': true,
        }
      )}
      onClick={onActivate}
      onMouseDown={handleMouseDown}
      draggable={draggable}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      title={tab.path || tab.title}
    >
      {/* 固定圖釘 */}
      {tab.pinned && (
        <div className="w-2 h-2 bg-vscode-tab-activeForeground rounded-full mr-2 flex-shrink-0" />
      )}
      
      {/* 圖標 */}
      {tab.icon && (
        <div className="w-4 h-4 mr-2 flex-shrink-0">
          {tab.icon}
        </div>
      )}
      
      {/* 標題 */}
      <span className="truncate text-sm flex-1 min-w-0">
        {t(tab.title)}
      </span>
      
      {/* 修改指示器 */}
      {tab.modified && (
        <div className="w-2 h-2 bg-vscode-tab-activeForeground rounded-full ml-2 flex-shrink-0" />
      )}
      
      {/* 關閉按鈕 */}
      {tab.closable !== false && onClose && (
        <button
          className={cn(
            'ml-2 w-4 h-4 flex-shrink-0',
            'text-vscode-tab-inactiveForeground',
            'hover:text-vscode-tab-activeForeground',
            'hover:bg-vscode-toolbar-hoverBackground',
            'rounded transition-colors',
            'opacity-0 group-hover:opacity-100',
            {
              'opacity-100': active || tab.modified,
            }
          )}
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          title={t('editor.close_tab')}
        >
          {tab.modified ? (
            <div className="w-2 h-2 bg-current rounded-full mx-auto" />
          ) : (
            <XMarkIcon className="w-full h-full" />
          )}
        </button>
      )}
    </div>
  );
};

// ============================================================================
// 標籤欄組件
// ============================================================================

const TabBar: React.FC<TabBarProps> = ({
  tabs,
  activeTabId,
  onTabChange,
  onTabClose,
  onTabAdd,
  allowReorder = true,
  onTabReorder,
  maxTabs = 20,
}) => {
  const { t } = useTranslation();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  
  // 檢查滾動狀態
  const checkScrollState = useCallback(() => {
    const element = scrollRef.current;
    if (!element) return;
    
    setCanScrollLeft(element.scrollLeft > 0);
    setCanScrollRight(
      element.scrollLeft < element.scrollWidth - element.clientWidth
    );
  }, []);
  
  useEffect(() => {
    checkScrollState();
    const element = scrollRef.current;
    if (element) {
      element.addEventListener('scroll', checkScrollState);
      return () => element.removeEventListener('scroll', checkScrollState);
    }
  }, [checkScrollState, tabs]);
  
  // 滾動控制
  const scrollLeft = useCallback(() => {
    scrollRef.current?.scrollBy({ left: -200, behavior: 'smooth' });
  }, []);
  
  const scrollRight = useCallback(() => {
    scrollRef.current?.scrollBy({ left: 200, behavior: 'smooth' });
  }, []);
  
  // 拖拽處理
  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    setDragOverIndex(index);
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    const draggedTabId = e.dataTransfer.getData('text/plain');
    const draggedIndex = tabs.findIndex(tab => tab.id === draggedTabId);
    
    if (draggedIndex !== -1 && draggedIndex !== dropIndex) {
      onTabReorder?.(draggedIndex, dropIndex);
    }
    
    setDragOverIndex(null);
  }, [tabs, onTabReorder]);
  
  const handleDragLeave = useCallback(() => {
    setDragOverIndex(null);
  }, []);
  
  return (
    <div className="flex items-center bg-vscode-editorGroupHeader-tabsBackground border-b border-vscode-editorGroupHeader-tabsBorder">
      {/* 左滾動按鈕 */}
      {canScrollLeft && (
        <button
          onClick={scrollLeft}
          className={cn(
            'w-8 h-9 flex items-center justify-center',
            'text-vscode-tab-inactiveForeground',
            'hover:text-vscode-tab-activeForeground',
            'hover:bg-vscode-toolbar-hoverBackground',
            'transition-colors'
          )}
          title={t('editor.scroll_left')}
        >
          <ChevronLeftIcon className="w-4 h-4" />
        </button>
      )}
      
      {/* 標籤頁容器 */}
      <div
        ref={scrollRef}
        className="flex-1 flex overflow-x-auto scrollbar-none"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {tabs.map((tab, index) => (
          <div
            key={tab.id}
            className={cn('relative', {
              'border-l-2 border-vscode-focusBorder': dragOverIndex === index,
            })}
            onDragOver={(e) => handleDragOver(e, index)}
            onDrop={(e) => handleDrop(e, index)}
            onDragLeave={handleDragLeave}
          >
            <Tab
              tab={tab}
              active={tab.id === activeTabId}
              onActivate={() => onTabChange(tab.id)}
              onClose={onTabClose ? () => onTabClose(tab.id) : undefined}
              onMiddleClick={onTabClose ? () => onTabClose(tab.id) : undefined}
              draggable={allowReorder}
            />
          </div>
        ))}
      </div>
      
      {/* 右滾動按鈕 */}
      {canScrollRight && (
        <button
          onClick={scrollRight}
          className={cn(
            'w-8 h-9 flex items-center justify-center',
            'text-vscode-tab-inactiveForeground',
            'hover:text-vscode-tab-activeForeground',
            'hover:bg-vscode-toolbar-hoverBackground',
            'transition-colors'
          )}
          title={t('editor.scroll_right')}
        >
          <ChevronRightIcon className="w-4 h-4" />
        </button>
      )}
      
      {/* 新增標籤按鈕 */}
      {onTabAdd && tabs.length < maxTabs && (
        <button
          onClick={onTabAdd}
          className={cn(
            'w-8 h-9 flex items-center justify-center',
            'text-vscode-tab-inactiveForeground',
            'hover:text-vscode-tab-activeForeground',
            'hover:bg-vscode-toolbar-hoverBackground',
            'transition-colors border-l border-vscode-tab-border'
          )}
          title={t('editor.new_tab')}
        >
          <PlusIcon className="w-4 h-4" />
        </button>
      )}
      
      {/* 更多選項 */}
      <button
        className={cn(
          'w-8 h-9 flex items-center justify-center',
          'text-vscode-tab-inactiveForeground',
          'hover:text-vscode-tab-activeForeground',
          'hover:bg-vscode-toolbar-hoverBackground',
          'transition-colors border-l border-vscode-tab-border'
        )}
        title={t('editor.more_options')}
      >
        <EllipsisHorizontalIcon className="w-4 h-4" />
      </button>
    </div>
  );
};

// ============================================================================
// 狀態欄組件
// ============================================================================

interface StatusBarProps {
  activeTab?: EditorTab;
  customContent?: React.ReactNode;
}

const StatusBar: React.FC<StatusBarProps> = ({ activeTab, customContent }) => {
  const { t } = useTranslation();
  
  return (
    <div className="flex items-center justify-between h-6 px-3 bg-vscode-statusBar-background text-vscode-statusBar-foreground text-xs border-t border-vscode-statusBar-border">
      <div className="flex items-center space-x-4">
        {/* 文件信息 */}
        {activeTab && (
          <>
            {activeTab.language && (
              <span className="hover:bg-vscode-statusBarItem-hoverBackground px-1 py-0.5 rounded cursor-pointer">
                {activeTab.language}
              </span>
            )}
            
            {activeTab.encoding && (
              <span className="hover:bg-vscode-statusBarItem-hoverBackground px-1 py-0.5 rounded cursor-pointer">
                {activeTab.encoding}
              </span>
            )}
            
            {activeTab.lineEnding && (
              <span className="hover:bg-vscode-statusBarItem-hoverBackground px-1 py-0.5 rounded cursor-pointer">
                {activeTab.lineEnding}
              </span>
            )}
          </>
        )}
        
        {/* 自定義內容 */}
        {customContent}
      </div>
      
      <div className="flex items-center space-x-2">
        {/* 狀態指示器 */}
        {activeTab?.modified && (
          <div className="flex items-center space-x-1 text-vscode-statusBar-foreground">
            <ExclamationTriangleIcon className="w-3 h-3" />
            <span>{t('editor.unsaved_changes')}</span>
          </div>
        )}
        
        {!activeTab?.modified && activeTab && (
          <div className="flex items-center space-x-1 text-vscode-statusBar-foreground">
            <CheckCircleIcon className="w-3 h-3" />
            <span>{t('editor.saved')}</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// 主要編輯器組件
// ============================================================================

export const Editor: React.FC<EditorProps> = ({
  tabs = [],
  activeTab,
  defaultActiveTab,
  maxTabs = 20,
  showTabBar = true,
  showStatusBar = true,
  allowTabReorder = true,
  allowTabClose = true,
  onTabChange,
  onTabClose,
  onTabAdd,
  onTabReorder,
  emptyState,
  statusBarContent,
  className,
  children,
  ...props
}) => {
  const { t } = useTranslation();
  
  // 編輯器狀態
  const [editorState, setEditorState] = useLocalStorage<EditorState>(
    'editor-state',
    {
      activeTabId: activeTab || defaultActiveTab || tabs[0]?.id,
      tabs: [],
      tabOrder: [],
    }
  );
  
  // 當前活動標籤
  const currentActiveTab = tabs.find(tab => 
    tab.id === (activeTab || editorState.activeTabId)
  );
  
  // 同步外部 activeTab
  useEffect(() => {
    if (activeTab && activeTab !== editorState.activeTabId) {
      setEditorState(prev => ({
        ...prev,
        activeTabId: activeTab,
      }));
    }
  }, [activeTab, editorState.activeTabId, setEditorState]);
  
  // 處理標籤切換
  const handleTabChange = useCallback((tabId: string) => {
    setEditorState(prev => ({
      ...prev,
      activeTabId: tabId,
    }));
    onTabChange?.(tabId);
  }, [setEditorState, onTabChange]);
  
  // 處理標籤關閉
  const handleTabClose = useCallback((tabId: string) => {
    if (!allowTabClose) return;
    
    const tabIndex = tabs.findIndex(tab => tab.id === tabId);
    if (tabIndex === -1) return;
    
    // 如果關閉的是當前活動標籤，切換到相鄰標籤
    if (tabId === editorState.activeTabId) {
      const nextTab = tabs[tabIndex + 1] || tabs[tabIndex - 1];
      if (nextTab) {
        handleTabChange(nextTab.id);
      } else {
        setEditorState(prev => ({
          ...prev,
          activeTabId: undefined,
        }));
      }
    }
    
    onTabClose?.(tabId);
  }, [allowTabClose, tabs, editorState.activeTabId, handleTabChange, setEditorState, onTabClose]);
  
  // 處理標籤重新排序
  const handleTabReorder = useCallback((fromIndex: number, toIndex: number) => {
    if (!allowTabReorder) return;
    onTabReorder?.(fromIndex, toIndex);
  }, [allowTabReorder, onTabReorder]);
  
  // 默認空狀態
  const defaultEmptyState = (
    <div className="h-full flex items-center justify-center text-vscode-descriptionForeground">
      <div className="text-center">
        <DocumentIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
        <h3 className="text-lg font-medium mb-2">{t('editor.no_tabs_open')}</h3>
        <p className="text-sm mb-4">{t('editor.no_tabs_description')}</p>
        {onTabAdd && (
          <button
            onClick={onTabAdd}
            className={cn(
              'px-4 py-2 bg-vscode-button-background text-vscode-button-foreground',
              'hover:bg-vscode-button-hoverBackground',
              'rounded transition-colors'
            )}
          >
            {t('editor.create_new_tab')}
          </button>
        )}
      </div>
    </div>
  );
  
  return (
    <div
      className={cn(
        'h-full flex flex-col',
        'bg-vscode-editor-background',
        className
      )}
      {...props}
    >
      {/* 標籤欄 */}
      {showTabBar && tabs.length > 0 && (
        <TabBar
          tabs={tabs}
          activeTabId={editorState.activeTabId}
          onTabChange={handleTabChange}
          onTabClose={allowTabClose ? handleTabClose : undefined}
          onTabAdd={onTabAdd}
          allowReorder={allowTabReorder}
          onTabReorder={handleTabReorder}
          maxTabs={maxTabs}
        />
      )}
      
      {/* 編輯器內容 */}
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
      
      {/* 狀態欄 */}
      {showStatusBar && (
        <StatusBar
          activeTab={currentActiveTab}
          customContent={statusBarContent}
        />
      )}
    </div>
  );
};

// ============================================================================
// 編輯器內容組件
// ============================================================================

/**
 * 編輯器內容包裝組件
 */
export const EditorContent: React.FC<BaseComponentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'h-full overflow-auto',
        'bg-vscode-editor-background text-vscode-editor-foreground',
        'p-4',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

// ============================================================================
// 導出
// ============================================================================

export default Editor;
export type { EditorTab, EditorState };