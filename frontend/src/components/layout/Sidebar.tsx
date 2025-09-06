/**
 * VS Code 風格的側邊欄組件
 * 提供可摺疊的側邊欄功能，支持多個面板切換
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ChevronDownIcon,
  ChevronRightIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  EllipsisVerticalIcon,
} from '@heroicons/react/24/outline';
import { cn } from '../../utils/cn';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import type { BaseComponentProps } from '../../types/components';

// ============================================================================
// 類型定義
// ============================================================================

/**
 * 側邊欄面板類型
 */
export interface SidebarPanel {
  id: string;
  title: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  actions?: React.ReactNode;
  badge?: number | string;
  searchable?: boolean;
  onSearch?: (query: string) => void;
}

/**
 * 側邊欄 Props
 */
export interface SidebarProps extends BaseComponentProps {
  panels?: SidebarPanel[];
  activePanel?: string;
  defaultActivePanel?: string;
  collapsible?: boolean;
  resizable?: boolean;
  width?: number;
  minWidth?: number;
  maxWidth?: number;
  onPanelChange?: (panelId: string) => void;
  onResize?: (width: number) => void;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

/**
 * 面板標題 Props
 */
interface PanelHeaderProps {
  panel: SidebarPanel;
  isActive: boolean;
  isCollapsed: boolean;
  onToggle: () => void;
  onActivate: () => void;
}

/**
 * 搜索框 Props
 */
interface SearchBoxProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  className?: string;
}

// ============================================================================
// 搜索框組件
// ============================================================================

const SearchBox: React.FC<SearchBoxProps> = ({
  placeholder = 'Search...',
  onSearch,
  className,
}) => {
  const [query, setQuery] = useState('');
  const { t } = useTranslation();
  
  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    onSearch(value);
  }, [onSearch]);
  
  const handleClear = useCallback(() => {
    setQuery('');
    onSearch('');
  }, [onSearch]);
  
  return (
    <div className={cn('relative', className)}>
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-vscode-input-placeholderForeground" />
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder={t(placeholder)}
          className={cn(
            'w-full pl-8 pr-8 py-1.5',
            'bg-vscode-input-background text-vscode-input-foreground',
            'border border-vscode-input-border',
            'rounded text-sm',
            'focus:outline-none focus:ring-1 focus:ring-vscode-focusBorder',
            'placeholder:text-vscode-input-placeholderForeground'
          )}
        />
        {query && (
          <button
            onClick={handleClear}
            className={cn(
              'absolute right-2 top-1/2 -translate-y-1/2',
              'w-4 h-4 text-vscode-input-placeholderForeground',
              'hover:text-vscode-input-foreground transition-colors'
            )}
          >
            <XMarkIcon className="w-full h-full" />
          </button>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// 面板標題組件
// ============================================================================

const PanelHeader: React.FC<PanelHeaderProps> = ({
  panel,
  isActive,
  isCollapsed,
  onToggle,
  onActivate,
}) => {
  const { t } = useTranslation();
  
  return (
    <div
      className={cn(
        'flex items-center justify-between px-3 py-2',
        'bg-vscode-sideBarSectionHeader-background',
        'border-b border-vscode-sideBarSectionHeader-border',
        'cursor-pointer select-none',
        'hover:bg-vscode-list-hoverBackground',
        'transition-colors duration-150',
        {
          'bg-vscode-list-activeSelectionBackground': isActive,
        }
      )}
      onClick={onActivate}
    >
      <div className="flex items-center space-x-2 flex-1 min-w-0">
        {/* 摺疊圖標 */}
        {panel.collapsible && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggle();
            }}
            className={cn(
              'w-4 h-4 text-vscode-sideBarSectionHeader-foreground',
              'hover:text-vscode-list-hoverForeground transition-colors',
              'flex-shrink-0'
            )}
          >
            {isCollapsed ? (
              <ChevronRightIcon className="w-full h-full" />
            ) : (
              <ChevronDownIcon className="w-full h-full" />
            )}
          </button>
        )}
        
        {/* 面板圖標 */}
        {panel.icon && (
          <div className="w-4 h-4 text-vscode-sideBarSectionHeader-foreground flex-shrink-0">
            {panel.icon}
          </div>
        )}
        
        {/* 面板標題 */}
        <span
          className={cn(
            'text-sm font-medium truncate',
            'text-vscode-sideBarSectionHeader-foreground',
            {
              'text-vscode-list-activeSelectionForeground': isActive,
            }
          )}
        >
          {t(panel.title)}
        </span>
        
        {/* 徽章 */}
        {panel.badge && (
          <span
            className={cn(
              'ml-auto px-1.5 py-0.5',
              'bg-vscode-badge-background text-vscode-badge-foreground',
              'text-xs font-medium rounded',
              'flex-shrink-0'
            )}
          >
            {typeof panel.badge === 'number' && panel.badge > 99 ? '99+' : panel.badge}
          </span>
        )}
      </div>
      
      {/* 操作按鈕 */}
      {panel.actions && (
        <div
          className="flex items-center space-x-1 ml-2 flex-shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          {panel.actions}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// 主要側邊欄組件
// ============================================================================

export const Sidebar: React.FC<SidebarProps> = ({
  panels = [],
  activePanel,
  defaultActivePanel,
  collapsible = true,
  resizable = true,
  width = 300,
  minWidth = 200,
  maxWidth = 600,
  onPanelChange,
  onResize,
  header,
  footer,
  className,
  children,
  ...props
}) => {
  const { t } = useTranslation();
  
  // 面板狀態管理
  const [currentActivePanel, setCurrentActivePanel] = useState(
    activePanel || defaultActivePanel || panels[0]?.id
  );
  
  // 面板摺疊狀態
  const [collapsedPanels, setCollapsedPanels] = useLocalStorage<Record<string, boolean>>(
    'sidebar-collapsed-panels',
    {}
  );
  
  // 搜索狀態
  const [searchQueries, setSearchQueries] = useState<Record<string, string>>({});
  
  // 同步外部 activePanel
  useEffect(() => {
    if (activePanel && activePanel !== currentActivePanel) {
      setCurrentActivePanel(activePanel);
    }
  }, [activePanel, currentActivePanel]);
  
  // 處理面板切換
  const handlePanelChange = useCallback((panelId: string) => {
    setCurrentActivePanel(panelId);
    onPanelChange?.(panelId);
  }, [onPanelChange]);
  
  // 處理面板摺疊
  const handlePanelToggle = useCallback((panelId: string) => {
    setCollapsedPanels(prev => ({
      ...prev,
      [panelId]: !prev[panelId]
    }));
  }, [setCollapsedPanels]);
  
  // 處理搜索
  const handleSearch = useCallback((panelId: string, query: string) => {
    setSearchQueries(prev => ({
      ...prev,
      [panelId]: query
    }));
    
    const panel = panels.find(p => p.id === panelId);
    panel?.onSearch?.(query);
  }, [panels]);
  
  // 獲取當前活動面板
  const activeCurrentPanel = panels.find(p => p.id === currentActivePanel);
  
  return (
    <div
      className={cn(
        'h-full flex flex-col',
        'bg-vscode-sideBar-background',
        'border-r border-vscode-sideBar-border',
        className
      )}
      style={{ width }}
      {...props}
    >
      {/* 標題區域 */}
      {header && (
        <div className="flex-shrink-0 border-b border-vscode-sideBar-border">
          {header}
        </div>
      )}
      
      {/* 面板標題列表 */}
      {panels.length > 0 && (
        <div className="flex-shrink-0">
          {panels.map((panel) => {
            const isActive = panel.id === currentActivePanel;
            const isCollapsed = collapsedPanels[panel.id] || false;
            
            return (
              <PanelHeader
                key={panel.id}
                panel={panel}
                isActive={isActive}
                isCollapsed={isCollapsed}
                onToggle={() => handlePanelToggle(panel.id)}
                onActivate={() => handlePanelChange(panel.id)}
              />
            );
          })}
        </div>
      )}
      
      {/* 搜索框 */}
      {activeCurrentPanel?.searchable && (
        <div className="flex-shrink-0 p-3 border-b border-vscode-sideBar-border">
          <SearchBox
            placeholder={`Search in ${activeCurrentPanel.title}...`}
            onSearch={(query) => handleSearch(activeCurrentPanel.id, query)}
          />
        </div>
      )}
      
      {/* 面板內容 */}
      <div className="flex-1 overflow-hidden">
        {activeCurrentPanel && !collapsedPanels[activeCurrentPanel.id] && (
          <div className="h-full overflow-auto">
            {activeCurrentPanel.content}
          </div>
        )}
        
        {/* 如果沒有活動面板，顯示子元素 */}
        {!activeCurrentPanel && children && (
          <div className="h-full overflow-auto p-3">
            {children}
          </div>
        )}
        
        {/* 空狀態 */}
        {!activeCurrentPanel && !children && (
          <div className="h-full flex items-center justify-center text-vscode-descriptionForeground">
            <div className="text-center">
              <div className="text-4xl mb-2">📁</div>
              <div className="text-sm">{t('sidebar.empty_state')}</div>
            </div>
          </div>
        )}
      </div>
      
      {/* 底部區域 */}
      {footer && (
        <div className="flex-shrink-0 border-t border-vscode-sideBar-border">
          {footer}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// 側邊欄面板組件
// ============================================================================

/**
 * 側邊欄面板內容組件
 */
export const SidebarPanelContent: React.FC<BaseComponentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'h-full overflow-auto',
        'text-vscode-sideBar-foreground',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * 側邊欄列表項目組件
 */
export interface SidebarListItemProps extends BaseComponentProps {
  icon?: React.ReactNode;
  label: string;
  badge?: number | string;
  active?: boolean;
  disabled?: boolean;
  indent?: number;
  actions?: React.ReactNode;
  onClick?: () => void;
}

export const SidebarListItem: React.FC<SidebarListItemProps> = ({
  icon,
  label,
  badge,
  active = false,
  disabled = false,
  indent = 0,
  actions,
  onClick,
  className,
  ...props
}) => {
  const { t } = useTranslation();
  
  return (
    <div
      className={cn(
        'flex items-center px-3 py-1.5 cursor-pointer select-none',
        'hover:bg-vscode-list-hoverBackground',
        'transition-colors duration-150',
        {
          'bg-vscode-list-activeSelectionBackground text-vscode-list-activeSelectionForeground': active,
          'opacity-50 cursor-not-allowed': disabled,
          'text-vscode-list-inactiveSelectionForeground': !active,
        },
        className
      )}
      style={{ paddingLeft: `${12 + indent * 16}px` }}
      onClick={disabled ? undefined : onClick}
      {...props}
    >
      {/* 圖標 */}
      {icon && (
        <div className="w-4 h-4 mr-2 flex-shrink-0">
          {icon}
        </div>
      )}
      
      {/* 標籤 */}
      <span className="flex-1 truncate text-sm">
        {t(label)}
      </span>
      
      {/* 徽章 */}
      {badge && (
        <span
          className={cn(
            'ml-2 px-1.5 py-0.5',
            'bg-vscode-badge-background text-vscode-badge-foreground',
            'text-xs font-medium rounded',
            'flex-shrink-0'
          )}
        >
          {typeof badge === 'number' && badge > 99 ? '99+' : badge}
        </span>
      )}
      
      {/* 操作按鈕 */}
      {actions && (
        <div
          className="ml-2 flex items-center space-x-1 flex-shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          {actions}
        </div>
      )}
    </div>
  );
};

/**
 * 側邊欄分組組件
 */
export interface SidebarGroupProps extends BaseComponentProps {
  title?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  actions?: React.ReactNode;
}

export const SidebarGroup: React.FC<SidebarGroupProps> = ({
  title,
  collapsible = false,
  defaultCollapsed = false,
  actions,
  className,
  children,
  ...props
}) => {
  const { t } = useTranslation();
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  
  const handleToggle = useCallback(() => {
    if (collapsible) {
      setIsCollapsed(!isCollapsed);
    }
  }, [collapsible, isCollapsed]);
  
  return (
    <div className={cn('', className)} {...props}>
      {/* 分組標題 */}
      {title && (
        <div
          className={cn(
            'flex items-center justify-between px-3 py-2',
            'text-xs font-semibold uppercase tracking-wide',
            'text-vscode-sideBarSectionHeader-foreground',
            'bg-vscode-sideBarSectionHeader-background',
            'border-b border-vscode-sideBarSectionHeader-border',
            {
              'cursor-pointer hover:bg-vscode-list-hoverBackground': collapsible,
            }
          )}
          onClick={handleToggle}
        >
          <div className="flex items-center space-x-2">
            {collapsible && (
              <div className="w-3 h-3">
                {isCollapsed ? (
                  <ChevronRightIcon className="w-full h-full" />
                ) : (
                  <ChevronDownIcon className="w-full h-full" />
                )}
              </div>
            )}
            <span>{t(title)}</span>
          </div>
          
          {actions && (
            <div
              className="flex items-center space-x-1"
              onClick={(e) => e.stopPropagation()}
            >
              {actions}
            </div>
          )}
        </div>
      )}
      
      {/* 分組內容 */}
      {(!collapsible || !isCollapsed) && (
        <div>{children}</div>
      )}
    </div>
  );
};

// ============================================================================
// 導出
// ============================================================================

export default Sidebar;
export type { SidebarPanel };