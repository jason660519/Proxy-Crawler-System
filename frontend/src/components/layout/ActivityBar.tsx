/**
 * VS Code 風格的活動欄組件
 * 提供主要功能區域的快速切換和導航
 */

import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  CogIcon,
  ChartBarIcon,
  ServerIcon,
  ClipboardDocumentListIcon,
  UserIcon,
  BellIcon,
  QuestionMarkCircleIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  CogIcon as CogIconSolid,
  ChartBarIcon as ChartBarIconSolid,
  ServerIcon as ServerIconSolid,
  ClipboardDocumentListIcon as ClipboardDocumentListIconSolid,
  UserIcon as UserIconSolid,
} from '@heroicons/react/24/solid';
import { cn } from '../../utils/cn';
import { useTheme } from '../../hooks/useTheme.tsx';
import type { BaseComponentProps } from '../../types/components';

// ============================================================================
// 類型定義
// ============================================================================

/**
 * 活動項目類型
 */
export interface ActivityItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  activeIcon?: React.ComponentType<{ className?: string }>;
  path?: string;
  badge?: number | string;
  disabled?: boolean;
  onClick?: () => void;
  tooltip?: string;
}

/**
 * 活動欄 Props
 */
export interface ActivityBarProps extends BaseComponentProps {
  items?: ActivityItem[];
  activeItem?: string;
  onItemClick?: (item: ActivityItem) => void;
  showLabels?: boolean;
  compact?: boolean;
}

/**
 * 活動項目 Props
 */
interface ActivityItemComponentProps {
  item: ActivityItem;
  isActive: boolean;
  showLabel?: boolean;
  compact?: boolean;
  onClick: () => void;
}

// ============================================================================
// 預設活動項目
// ============================================================================

const DEFAULT_ITEMS: ActivityItem[] = [
  {
    id: 'dashboard',
    label: 'dashboard.title',
    icon: HomeIcon,
    activeIcon: HomeIconSolid,
    path: '/',
    tooltip: 'dashboard.tooltip',
  },
  {
    id: 'proxies',
    label: 'navigation.proxies',
    icon: ServerIcon,
    activeIcon: ServerIconSolid,
    path: '/proxies',
    tooltip: 'navigation.proxies_tooltip',
  },
  {
    id: 'tasks',
    label: 'navigation.tasks',
    icon: ClipboardDocumentListIcon,
    activeIcon: ClipboardDocumentListIconSolid,
    path: '/tasks',
    tooltip: 'navigation.tasks_tooltip',
  },
  {
    id: 'monitoring',
    label: 'navigation.monitoring',
    icon: ChartBarIcon,
    activeIcon: ChartBarIconSolid,
    path: '/monitoring',
    tooltip: 'navigation.monitoring_tooltip',
  },
  {
    id: 'settings',
    label: 'navigation.settings',
    icon: CogIcon,
    activeIcon: CogIconSolid,
    path: '/settings',
    tooltip: 'navigation.settings_tooltip',
  },
];

const BOTTOM_ITEMS: ActivityItem[] = [
  {
    id: 'notifications',
    label: 'navigation.notifications',
    icon: BellIcon,
    tooltip: 'navigation.notifications_tooltip',
    badge: 3,
  },
  {
    id: 'user',
    label: 'navigation.user',
    icon: UserIcon,
    activeIcon: UserIconSolid,
    path: '/profile',
    tooltip: 'navigation.user_tooltip',
  },
  {
    id: 'help',
    label: 'navigation.help',
    icon: QuestionMarkCircleIcon,
    tooltip: 'navigation.help_tooltip',
  },
  {
    id: 'preferences',
    label: 'navigation.preferences',
    icon: Cog6ToothIcon,
    tooltip: 'navigation.preferences_tooltip',
  },
];

// ============================================================================
// 活動項目組件
// ============================================================================

const ActivityItemComponent: React.FC<ActivityItemComponentProps> = ({
  item,
  isActive,
  showLabel = false,
  compact = false,
  onClick,
}) => {
  const { t } = useTranslation();
  const [isHovered, setIsHovered] = useState(false);
  
  const IconComponent = isActive && item.activeIcon ? item.activeIcon : item.icon;
  
  return (
    <div className="relative group">
      <button
        className={cn(
          'relative w-full flex flex-col items-center justify-center',
          'transition-all duration-200 ease-in-out',
          'hover:bg-vscode-activityBar-activeBorder/10',
          'focus:outline-none focus:ring-2 focus:ring-vscode-focusBorder',
          {
            'h-12 px-2': compact,
            'h-16 px-3': !compact,
            'bg-vscode-activityBar-activeBorder/20 border-l-2 border-vscode-activityBar-activeBorder': isActive,
            'opacity-50 cursor-not-allowed': item.disabled,
          }
        )}
        onClick={onClick}
        disabled={item.disabled}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        title={item.tooltip ? t(item.tooltip) : t(item.label)}
      >
        {/* 圖標 */}
        <div className="relative">
          <IconComponent
            className={cn(
              'transition-all duration-200',
              {
                'w-5 h-5': compact,
                'w-6 h-6': !compact,
                'text-vscode-activityBar-activeForeground': isActive,
                'text-vscode-activityBar-foreground': !isActive,
                'scale-110': isHovered && !item.disabled,
              }
            )}
          />
          
          {/* 徽章 */}
          {item.badge && (
            <div
              className={cn(
                'absolute -top-1 -right-1',
                'min-w-[16px] h-4 px-1',
                'bg-vscode-badge-background text-vscode-badge-foreground',
                'text-xs font-medium rounded-full',
                'flex items-center justify-center',
                'border border-vscode-activityBar-background'
              )}
            >
              {typeof item.badge === 'number' && item.badge > 99 ? '99+' : item.badge}
            </div>
          )}
        </div>
        
        {/* 標籤 */}
        {showLabel && (
          <span
            className={cn(
              'mt-1 text-xs font-medium truncate max-w-full',
              'transition-colors duration-200',
              {
                'text-vscode-activityBar-activeForeground': isActive,
                'text-vscode-activityBar-foreground': !isActive,
              }
            )}
          >
            {t(item.label)}
          </span>
        )}
        
        {/* 活動指示器 */}
        {isActive && (
          <div
            className={cn(
              'absolute left-0 top-1/2 -translate-y-1/2',
              'w-0.5 h-8 bg-vscode-activityBar-activeBorder',
              'rounded-r-sm'
            )}
          />
        )}
      </button>
      
      {/* 工具提示 */}
      {!showLabel && isHovered && item.tooltip && (
        <div
          className={cn(
            'absolute left-full ml-2 top-1/2 -translate-y-1/2 z-50',
            'px-2 py-1 bg-vscode-editorHoverWidget-background',
            'border border-vscode-editorHoverWidget-border',
            'text-vscode-editorHoverWidget-foreground text-xs',
            'rounded shadow-lg whitespace-nowrap',
            'pointer-events-none'
          )}
        >
          {t(item.tooltip)}
          <div
            className={cn(
              'absolute right-full top-1/2 -translate-y-1/2',
              'border-4 border-transparent border-r-vscode-editorHoverWidget-border'
            )}
          />
        </div>
      )}
    </div>
  );
};

// ============================================================================
// 主要活動欄組件
// ============================================================================

export const ActivityBar: React.FC<ActivityBarProps> = ({
  items = DEFAULT_ITEMS,
  activeItem,
  onItemClick,
  showLabels = false,
  compact = false,
  className,
  ...props
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  
  // 確定當前活動項目
  const currentActiveItem = activeItem || (() => {
    const currentPath = location.pathname;
    const matchedItem = [...items, ...BOTTOM_ITEMS].find(item => 
      item.path && currentPath.startsWith(item.path)
    );
    return matchedItem?.id || items[0]?.id;
  })();
  
  // 處理項目點擊
  const handleItemClick = useCallback((item: ActivityItem) => {
    if (item.disabled) return;
    
    // 執行自定義點擊處理
    if (item.onClick) {
      item.onClick();
    }
    
    // 導航到指定路徑
    if (item.path) {
      navigate(item.path);
    }
    
    // 執行外部點擊處理
    onItemClick?.(item);
  }, [navigate, onItemClick]);
  
  // 處理主題切換
  const handleThemeToggle = useCallback(() => {
    toggleTheme();
  }, [toggleTheme]);
  
  return (
    <div
      className={cn(
        'h-full flex flex-col',
        'bg-vscode-activityBar-background',
        'border-r border-vscode-activityBar-border',
        className
      )}
      {...props}
    >
      {/* 主要活動項目 */}
      <div className="flex-1 flex flex-col">
        {items.map((item) => (
          <ActivityItemComponent
            key={item.id}
            item={item}
            isActive={currentActiveItem === item.id}
            showLabel={showLabels}
            compact={compact}
            onClick={() => handleItemClick(item)}
          />
        ))}
      </div>
      
      {/* 分隔線 */}
      <div className="mx-2 h-px bg-vscode-activityBar-border" />
      
      {/* 底部活動項目 */}
      <div className="flex flex-col">
        {BOTTOM_ITEMS.map((item) => (
          <ActivityItemComponent
            key={item.id}
            item={item}
            isActive={currentActiveItem === item.id}
            showLabel={showLabels}
            compact={compact}
            onClick={() => handleItemClick(item)}
          />
        ))}
        
        {/* 主題切換按鈕 */}
        <button
          className={cn(
            'relative w-full flex flex-col items-center justify-center',
            'transition-all duration-200 ease-in-out',
            'hover:bg-vscode-activityBar-activeBorder/10',
            'focus:outline-none focus:ring-2 focus:ring-vscode-focusBorder',
            {
              'h-12 px-2': compact,
              'h-16 px-3': !compact,
            }
          )}
          onClick={handleThemeToggle}
          title={t('navigation.toggle_theme')}
        >
          <div
            className={cn(
              'transition-all duration-200',
              {
                'w-5 h-5': compact,
                'w-6 h-6': !compact,
              },
              'text-vscode-activityBar-foreground hover:text-vscode-activityBar-activeForeground'
            )}
          >
            {theme === 'dark' ? (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          
          {showLabels && (
            <span className="mt-1 text-xs font-medium text-vscode-activityBar-foreground">
              {t('navigation.theme')}
            </span>
          )}
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// 導出
// ============================================================================

export default ActivityBar;
export type { ActivityItem };