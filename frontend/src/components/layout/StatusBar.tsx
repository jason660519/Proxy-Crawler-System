/**
 * VS Code 風格的狀態欄組件
 * 提供底部狀態欄功能，顯示各種狀態信息和快捷操作
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  WifiIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  CpuChipIcon,
  ServerIcon,
  BellIcon,
  Cog6ToothIcon,
  InformationCircleIcon,
  BugAntIcon,
  CommandLineIcon,
  DocumentTextIcon,
  FolderIcon,
  CodeBracketIcon,
  LanguageIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';
import { cn } from '../../utils/cn';
import { useTheme } from '../../hooks/useTheme.tsx';
import type { BaseComponentProps } from '../../types/components';

// ============================================================================
// 類型定義
// ============================================================================

/**
 * 狀態欄項目類型
 */
export interface StatusBarItem {
  id: string;
  content: React.ReactNode;
  tooltip?: string;
  priority?: number;
  alignment?: 'left' | 'right';
  visible?: boolean;
  clickable?: boolean;
  onClick?: () => void;
  className?: string;
}

/**
 * 狀態欄 Props
 */
export interface StatusBarProps extends BaseComponentProps {
  items?: StatusBarItem[];
  showBranchInfo?: boolean;
  showLanguageInfo?: boolean;
  showEncodingInfo?: boolean;
  showLineInfo?: boolean;
  showSelectionInfo?: boolean;
  showNotifications?: boolean;
  showProblems?: boolean;
  showConnectionStatus?: boolean;
  onItemClick?: (itemId: string) => void;
  customLeftItems?: React.ReactNode;
  customRightItems?: React.ReactNode;
}

/**
 * 狀態項目 Props
 */
interface StatusItemProps {
  item: StatusBarItem;
  onClick?: (itemId: string) => void;
}

/**
 * 連接狀態類型
 */
type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

/**
 * 問題統計類型
 */
interface ProblemStats {
  errors: number;
  warnings: number;
  infos: number;
}

// ============================================================================
// 狀態項目組件
// ============================================================================

const StatusItem: React.FC<StatusItemProps> = ({ item, onClick }) => {
  const handleClick = useCallback(() => {
    if (item.clickable && item.onClick) {
      item.onClick();
    } else if (onClick) {
      onClick(item.id);
    }
  }, [item, onClick]);
  
  if (!item.visible) {
    return null;
  }
  
  return (
    <div
      className={cn(
        'flex items-center px-2 py-1 text-xs',
        'text-vscode-statusBar-foreground',
        {
          'cursor-pointer hover:bg-vscode-statusBarItem-hoverBackground': item.clickable || item.onClick,
        },
        item.className
      )}
      onClick={handleClick}
      title={item.tooltip}
    >
      {item.content}
    </div>
  );
};

// ============================================================================
// 連接狀態組件
// ============================================================================

interface ConnectionStatusProps {
  status: ConnectionStatus;
  serverName?: string;
  onClick?: () => void;
}

const ConnectionStatusComponent: React.FC<ConnectionStatusProps> = ({
  status,
  serverName = 'Server',
  onClick,
}) => {
  const { t } = useTranslation();
  
  const getStatusIcon = () => {
    switch (status) {
      case 'connected':
        return <CheckCircleIcon className="w-3 h-3 text-green-500" />;
      case 'disconnected':
        return <XCircleIcon className="w-3 h-3 text-red-500" />;
      case 'connecting':
        return <ClockIcon className="w-3 h-3 text-yellow-500 animate-spin" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-3 h-3 text-red-500" />;
      default:
        return <ServerIcon className="w-3 h-3" />;
    }
  };
  
  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return t('status.connected_to', { server: serverName });
      case 'disconnected':
        return t('status.disconnected');
      case 'connecting':
        return t('status.connecting');
      case 'error':
        return t('status.connection_error');
      default:
        return t('status.unknown');
    }
  };
  
  return (
    <div
      className={cn(
        'flex items-center space-x-1 px-2 py-1 cursor-pointer',
        'hover:bg-vscode-statusBarItem-hoverBackground',
        'transition-colors'
      )}
      onClick={onClick}
      title={getStatusText()}
    >
      {getStatusIcon()}
      <span className="text-xs">{serverName}</span>
    </div>
  );
};

// ============================================================================
// 問題統計組件
// ============================================================================

interface ProblemStatsProps {
  stats: ProblemStats;
  onClick?: () => void;
}

const ProblemStatsComponent: React.FC<ProblemStatsProps> = ({ stats, onClick }) => {
  const { t } = useTranslation();
  const totalProblems = stats.errors + stats.warnings + stats.infos;
  
  if (totalProblems === 0) {
    return (
      <div
        className={cn(
          'flex items-center space-x-1 px-2 py-1',
          {
            'cursor-pointer hover:bg-vscode-statusBarItem-hoverBackground': onClick,
          }
        )}
        onClick={onClick}
        title={t('status.no_problems')}
      >
        <CheckCircleIcon className="w-3 h-3 text-green-500" />
        <span className="text-xs">{t('status.no_problems')}</span>
      </div>
    );
  }
  
  return (
    <div
      className={cn(
        'flex items-center space-x-2 px-2 py-1',
        {
          'cursor-pointer hover:bg-vscode-statusBarItem-hoverBackground': onClick,
        }
      )}
      onClick={onClick}
      title={t('status.problems_summary', {
        errors: stats.errors,
        warnings: stats.warnings,
        infos: stats.infos,
      })}
    >
      {stats.errors > 0 && (
        <div className="flex items-center space-x-1">
          <XCircleIcon className="w-3 h-3 text-red-500" />
          <span className="text-xs text-red-500">{stats.errors}</span>
        </div>
      )}
      
      {stats.warnings > 0 && (
        <div className="flex items-center space-x-1">
          <ExclamationTriangleIcon className="w-3 h-3 text-yellow-500" />
          <span className="text-xs text-yellow-500">{stats.warnings}</span>
        </div>
      )}
      
      {stats.infos > 0 && (
        <div className="flex items-center space-x-1">
          <InformationCircleIcon className="w-3 h-3 text-blue-500" />
          <span className="text-xs text-blue-500">{stats.infos}</span>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// 通知組件
// ============================================================================

interface NotificationProps {
  count: number;
  hasUnread?: boolean;
  onClick?: () => void;
}

const NotificationComponent: React.FC<NotificationProps> = ({
  count,
  hasUnread = false,
  onClick,
}) => {
  const { t } = useTranslation();
  
  if (count === 0 && !hasUnread) {
    return null;
  }
  
  return (
    <div
      className={cn(
        'flex items-center space-x-1 px-2 py-1 cursor-pointer',
        'hover:bg-vscode-statusBarItem-hoverBackground',
        'transition-colors'
      )}
      onClick={onClick}
      title={t('status.notifications', { count })}
    >
      <BellIcon className={cn('w-3 h-3', {
        'text-vscode-statusBar-foreground': !hasUnread,
        'text-blue-500': hasUnread,
      })} />
      {count > 0 && (
        <span className={cn('text-xs', {
          'text-vscode-statusBar-foreground': !hasUnread,
          'text-blue-500 font-medium': hasUnread,
        })}>
          {count > 99 ? '99+' : count}
        </span>
      )}
    </div>
  );
};

// ============================================================================
// 主要狀態欄組件
// ============================================================================

export const StatusBar: React.FC<StatusBarProps> = ({
  items = [],
  showBranchInfo = true,
  showLanguageInfo = true,
  showEncodingInfo = true,
  showLineInfo = true,
  showSelectionInfo = true,
  showNotifications = true,
  showProblems = true,
  showConnectionStatus = true,
  onItemClick,
  customLeftItems,
  customRightItems,
  className,
  ...props
}) => {
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  
  // 狀態數據（模擬）
  const [connectionStatus] = useState<ConnectionStatus>('connected');
  const [problemStats] = useState<ProblemStats>({
    errors: 0,
    warnings: 2,
    infos: 1,
  });
  const [notificationCount] = useState(3);
  const [hasUnreadNotifications] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  
  // 更新時間
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);
  
  // 分離左右對齊的項目
  const leftItems = items.filter(item => item.alignment !== 'right');
  const rightItems = items.filter(item => item.alignment === 'right');
  
  // 創建預設項目
  const createDefaultItems = useCallback(() => {
    const defaultLeftItems: StatusBarItem[] = [];
    const defaultRightItems: StatusBarItem[] = [];
    
    // 分支信息
    if (showBranchInfo) {
      defaultLeftItems.push({
        id: 'branch',
        content: (
          <div className="flex items-center space-x-1">
            <CodeBracketIcon className="w-3 h-3" />
            <span>main</span>
          </div>
        ),
        tooltip: t('status.current_branch'),
        clickable: true,
        onClick: () => console.log('Branch clicked'),
      });
    }
    
    // 問題統計
    if (showProblems) {
      defaultRightItems.push({
        id: 'problems',
        content: (
          <ProblemStatsComponent
            stats={problemStats}
            onClick={() => console.log('Problems clicked')}
          />
        ),
        alignment: 'right',
        clickable: true,
      });
    }
    
    // 連接狀態
    if (showConnectionStatus) {
      defaultRightItems.push({
        id: 'connection',
        content: (
          <ConnectionStatusComponent
            status={connectionStatus}
            serverName="Proxy Server"
            onClick={() => console.log('Connection clicked')}
          />
        ),
        alignment: 'right',
        clickable: true,
      });
    }
    
    // 通知
    if (showNotifications) {
      defaultRightItems.push({
        id: 'notifications',
        content: (
          <NotificationComponent
            count={notificationCount}
            hasUnread={hasUnreadNotifications}
            onClick={() => console.log('Notifications clicked')}
          />
        ),
        alignment: 'right',
        clickable: true,
      });
    }
    
    // 語言信息
    if (showLanguageInfo) {
      defaultRightItems.push({
        id: 'language',
        content: (
          <div className="flex items-center space-x-1">
            <LanguageIcon className="w-3 h-3" />
            <span>TypeScript</span>
          </div>
        ),
        tooltip: t('status.file_language'),
        alignment: 'right',
        clickable: true,
        onClick: () => console.log('Language clicked'),
      });
    }
    
    // 編碼信息
    if (showEncodingInfo) {
      defaultRightItems.push({
        id: 'encoding',
        content: <span>UTF-8</span>,
        tooltip: t('status.file_encoding'),
        alignment: 'right',
        clickable: true,
        onClick: () => console.log('Encoding clicked'),
      });
    }
    
    // 行信息
    if (showLineInfo) {
      defaultRightItems.push({
        id: 'line-info',
        content: <span>Ln 1, Col 1</span>,
        tooltip: t('status.cursor_position'),
        alignment: 'right',
        clickable: true,
        onClick: () => console.log('Line info clicked'),
      });
    }
    
    // 選擇信息
    if (showSelectionInfo) {
      defaultRightItems.push({
        id: 'selection',
        content: <span>(0 selected)</span>,
        tooltip: t('status.selection_info'),
        alignment: 'right',
        visible: false, // 只在有選擇時顯示
      });
    }
    
    // 主題切換
    defaultRightItems.push({
      id: 'theme',
      content: (
        <div className="flex items-center space-x-1">
          {theme === 'dark' ? (
            <EyeSlashIcon className="w-3 h-3" />
          ) : (
            <EyeIcon className="w-3 h-3" />
          )}
          <span>{theme === 'dark' ? 'Dark' : 'Light'}</span>
        </div>
      ),
      tooltip: t('status.toggle_theme'),
      alignment: 'right',
      clickable: true,
      onClick: toggleTheme,
    });
    
    // 時間
    defaultRightItems.push({
      id: 'time',
      content: (
        <div className="flex items-center space-x-1">
          <ClockIcon className="w-3 h-3" />
          <span>{currentTime.toLocaleTimeString()}</span>
        </div>
      ),
      tooltip: t('status.current_time'),
      alignment: 'right',
    });
    
    return { defaultLeftItems, defaultRightItems };
  }, [
    showBranchInfo,
    showLanguageInfo,
    showEncodingInfo,
    showLineInfo,
    showSelectionInfo,
    showNotifications,
    showProblems,
    showConnectionStatus,
    problemStats,
    connectionStatus,
    notificationCount,
    hasUnreadNotifications,
    currentTime,
    theme,
    toggleTheme,
    t,
  ]);
  
  const { defaultLeftItems, defaultRightItems } = createDefaultItems();
  
  // 合併項目
  const allLeftItems = [...defaultLeftItems, ...leftItems]
    .filter(item => item.visible !== false)
    .sort((a, b) => (b.priority || 0) - (a.priority || 0));
    
  const allRightItems = [...defaultRightItems, ...rightItems]
    .filter(item => item.visible !== false)
    .sort((a, b) => (b.priority || 0) - (a.priority || 0));
  
  return (
    <div
      className={cn(
        'flex items-center justify-between h-6',
        'bg-vscode-statusBar-background text-vscode-statusBar-foreground',
        'border-t border-vscode-statusBar-border',
        'text-xs select-none',
        className
      )}
      {...props}
    >
      {/* 左側項目 */}
      <div className="flex items-center">
        {customLeftItems}
        {allLeftItems.map((item) => (
          <StatusItem
            key={item.id}
            item={item}
            onClick={onItemClick}
          />
        ))}
      </div>
      
      {/* 右側項目 */}
      <div className="flex items-center">
        {allRightItems.map((item) => (
          <StatusItem
            key={item.id}
            item={item}
            onClick={onItemClick}
          />
        ))}
        {customRightItems}
      </div>
    </div>
  );
};

// ============================================================================
// 狀態欄項目創建工具
// ============================================================================

/**
 * 創建狀態欄項目的工具函數
 */
export const createStatusBarItem = (
  id: string,
  content: React.ReactNode,
  options: Partial<Omit<StatusBarItem, 'id' | 'content'>> = {}
): StatusBarItem => ({
  id,
  content,
  visible: true,
  clickable: false,
  alignment: 'left',
  priority: 0,
  ...options,
});

/**
 * 創建簡單文本狀態項目
 */
export const createTextStatusItem = (
  id: string,
  text: string,
  options: Partial<Omit<StatusBarItem, 'id' | 'content'>> = {}
): StatusBarItem => createStatusBarItem(
  id,
  <span>{text}</span>,
  options
);

/**
 * 創建帶圖標的狀態項目
 */
export const createIconStatusItem = (
  id: string,
  icon: React.ReactNode,
  text?: string,
  options: Partial<Omit<StatusBarItem, 'id' | 'content'>> = {}
): StatusBarItem => createStatusBarItem(
  id,
  (
    <div className="flex items-center space-x-1">
      <div className="w-3 h-3">{icon}</div>
      {text && <span>{text}</span>}
    </div>
  ),
  options
);

// ============================================================================
// 導出
// ============================================================================

export default StatusBar;
export type { StatusBarItem, ConnectionStatus, ProblemStats };