/**
 * VS Code 風格的五區域佈局組件
 * 實現活動欄、側邊欄、編輯器、面板和狀態欄的佈局結構
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import { useTheme } from '../../hooks/useTheme.tsx';
import type { BaseComponentProps } from '../../types/components';

// ============================================================================
// 類型定義
// ============================================================================

/**
 * 佈局區域類型
 */
export type LayoutArea = 'activityBar' | 'sidebar' | 'editor' | 'panel' | 'statusBar';

/**
 * 佈局配置
 */
export interface LayoutConfig {
  activityBar: {
    visible: boolean;
    width: number;
  };
  sidebar: {
    visible: boolean;
    width: number;
    position: 'left' | 'right';
  };
  editor: {
    visible: boolean;
  };
  panel: {
    visible: boolean;
    height: number;
    position: 'bottom' | 'right';
  };
  statusBar: {
    visible: boolean;
    height: number;
  };
}

/**
 * 佈局 Props
 */
export interface LayoutProps extends BaseComponentProps {
  config?: Partial<LayoutConfig>;
  activityBar?: React.ReactNode;
  sidebar?: React.ReactNode;
  editor?: React.ReactNode;
  panel?: React.ReactNode;
  statusBar?: React.ReactNode;
  onConfigChange?: (config: LayoutConfig) => void;
}

/**
 * 可調整大小的分隔器 Props
 */
interface ResizerProps {
  direction: 'horizontal' | 'vertical';
  onResize: (delta: number) => void;
  className?: string;
}

// ============================================================================
// 預設配置
// ============================================================================

const DEFAULT_CONFIG: LayoutConfig = {
  activityBar: {
    visible: true,
    width: 48,
  },
  sidebar: {
    visible: true,
    width: 300,
    position: 'left',
  },
  editor: {
    visible: true,
  },
  panel: {
    visible: true,
    height: 300,
    position: 'bottom',
  },
  statusBar: {
    visible: true,
    height: 24,
  },
};

// ============================================================================
// 可調整大小的分隔器組件
// ============================================================================

const Resizer: React.FC<ResizerProps> = ({ direction, onResize, className }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState(0);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    setStartPos(direction === 'horizontal' ? e.clientX : e.clientY);
  }, [direction]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    
    const currentPos = direction === 'horizontal' ? e.clientX : e.clientY;
    const delta = currentPos - startPos;
    onResize(delta);
    setStartPos(currentPos);
  }, [isDragging, direction, startPos, onResize]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize';
      document.body.style.userSelect = 'none';
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp, direction]);

  return (
    <div
      className={cn(
        'group relative flex-shrink-0 transition-colors',
        {
          'w-1 cursor-col-resize hover:bg-blue-500/20': direction === 'horizontal',
          'h-1 cursor-row-resize hover:bg-blue-500/20': direction === 'vertical',
          'bg-blue-500/40': isDragging,
        },
        className
      )}
      onMouseDown={handleMouseDown}
    >
      <div
        className={cn(
          'absolute bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity',
          {
            'w-0.5 h-full left-1/2 -translate-x-1/2': direction === 'horizontal',
            'h-0.5 w-full top-1/2 -translate-y-1/2': direction === 'vertical',
            'opacity-100': isDragging,
          }
        )}
      />
    </div>
  );
};

// ============================================================================
// 主要佈局組件
// ============================================================================

export const Layout: React.FC<LayoutProps> = ({
  config: configProp,
  activityBar,
  sidebar,
  editor,
  panel,
  statusBar,
  onConfigChange,
  className,
  children,
  ...props
}) => {
  const { t } = useTranslation();
  const { theme } = useTheme();
  
  // 從本地存儲載入佈局配置
  const [storedConfig, setStoredConfig] = useLocalStorage<LayoutConfig>(
    'layout-config',
    DEFAULT_CONFIG
  );
  
  // 合併配置
  const config = { ...storedConfig, ...configProp };
  
  // 更新配置的處理函數
  const updateConfig = useCallback((newConfig: Partial<LayoutConfig>) => {
    const updatedConfig = { ...config, ...newConfig };
    setStoredConfig(updatedConfig);
    onConfigChange?.(updatedConfig);
  }, [config, setStoredConfig, onConfigChange]);
  
  // 調整活動欄寬度
  const handleActivityBarResize = useCallback((delta: number) => {
    const newWidth = Math.max(32, Math.min(80, config.activityBar.width + delta));
    updateConfig({
      activityBar: { ...config.activityBar, width: newWidth }
    });
  }, [config, updateConfig]);
  
  // 調整側邊欄寬度
  const handleSidebarResize = useCallback((delta: number) => {
    const newWidth = Math.max(200, Math.min(600, config.sidebar.width + delta));
    updateConfig({
      sidebar: { ...config.sidebar, width: newWidth }
    });
  }, [config, updateConfig]);
  
  // 調整面板高度
  const handlePanelResize = useCallback((delta: number) => {
    const newHeight = Math.max(100, Math.min(500, config.panel.height - delta));
    updateConfig({
      panel: { ...config.panel, height: newHeight }
    });
  }, [config, updateConfig]);
  
  // 切換區域可見性
  const toggleArea = useCallback((area: LayoutArea) => {
    updateConfig({
      [area]: { ...config[area], visible: !config[area].visible }
    });
  }, [config, updateConfig]);
  
  // 計算佈局樣式
  const layoutStyles = {
    '--activity-bar-width': `${config.activityBar.width}px`,
    '--sidebar-width': `${config.sidebar.width}px`,
    '--panel-height': `${config.panel.height}px`,
    '--status-bar-height': `${config.statusBar.height}px`,
  } as React.CSSProperties;
  
  return (
    <div
      className={cn(
        'h-screen w-full flex flex-col overflow-hidden',
        'bg-vscode-editor-background text-vscode-editor-foreground',
        'font-mono text-sm',
        className
      )}
      style={layoutStyles}
      {...props}
    >
      {/* 主要內容區域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 活動欄 */}
        {config.activityBar.visible && (
          <>
            <div
              className={cn(
                'flex-shrink-0 flex flex-col',
                'bg-vscode-activityBar-background border-r border-vscode-activityBar-border',
                'transition-all duration-200'
              )}
              style={{ width: config.activityBar.width }}
            >
              {activityBar}
            </div>
            <Resizer
              direction="horizontal"
              onResize={handleActivityBarResize}
              className="bg-vscode-activityBar-border"
            />
          </>
        )}
        
        {/* 側邊欄 */}
        {config.sidebar.visible && config.sidebar.position === 'left' && (
          <>
            <div
              className={cn(
                'flex-shrink-0 flex flex-col',
                'bg-vscode-sideBar-background border-r border-vscode-sideBar-border',
                'transition-all duration-200'
              )}
              style={{ width: config.sidebar.width }}
            >
              {sidebar}
            </div>
            <Resizer
              direction="horizontal"
              onResize={handleSidebarResize}
              className="bg-vscode-sideBar-border"
            />
          </>
        )}
        
        {/* 編輯器和面板區域 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 編輯器區域 */}
          {config.editor.visible && (
            <div className="flex-1 flex overflow-hidden">
              {/* 主編輯器 */}
              <div className="flex-1 flex flex-col overflow-hidden bg-vscode-editor-background">
                {editor || children}
              </div>
              
              {/* 右側面板 */}
              {config.panel.visible && config.panel.position === 'right' && (
                <>
                  <Resizer
                    direction="horizontal"
                    onResize={(delta) => {
                      const newWidth = Math.max(200, Math.min(600, config.panel.height + delta));
                      updateConfig({
                        panel: { ...config.panel, height: newWidth }
                      });
                    }}
                    className="bg-vscode-panel-border"
                  />
                  <div
                    className={cn(
                      'flex-shrink-0 flex flex-col',
                      'bg-vscode-panel-background border-l border-vscode-panel-border',
                      'transition-all duration-200'
                    )}
                    style={{ width: config.panel.height }}
                  >
                    {panel}
                  </div>
                </>
              )}
            </div>
          )}
          
          {/* 底部面板 */}
          {config.panel.visible && config.panel.position === 'bottom' && (
            <>
              <Resizer
                direction="vertical"
                onResize={handlePanelResize}
                className="bg-vscode-panel-border"
              />
              <div
                className={cn(
                  'flex-shrink-0 flex flex-col',
                  'bg-vscode-panel-background border-t border-vscode-panel-border',
                  'transition-all duration-200'
                )}
                style={{ height: config.panel.height }}
              >
                {panel}
              </div>
            </>
          )}
        </div>
        
        {/* 右側邊欄 */}
        {config.sidebar.visible && config.sidebar.position === 'right' && (
          <>
            <Resizer
              direction="horizontal"
              onResize={handleSidebarResize}
              className="bg-vscode-sideBar-border"
            />
            <div
              className={cn(
                'flex-shrink-0 flex flex-col',
                'bg-vscode-sideBar-background border-l border-vscode-sideBar-border',
                'transition-all duration-200'
              )}
              style={{ width: config.sidebar.width }}
            >
              {sidebar}
            </div>
          </>
        )}
      </div>
      
      {/* 狀態欄 */}
      {config.statusBar.visible && (
        <div
          className={cn(
            'flex-shrink-0 flex items-center px-4',
            'bg-vscode-statusBar-background text-vscode-statusBar-foreground',
            'border-t border-vscode-statusBar-border',
            'transition-all duration-200'
          )}
          style={{ height: config.statusBar.height }}
        >
          {statusBar}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// 佈局控制 Hook
// ============================================================================

/**
 * 佈局控制 Hook
 * 提供佈局配置管理和控制功能
 */
export const useLayout = () => {
  const [config, setConfig] = useLocalStorage<LayoutConfig>(
    'layout-config',
    DEFAULT_CONFIG
  );
  
  const toggleArea = useCallback((area: LayoutArea) => {
    setConfig(prev => ({
      ...prev,
      [area]: { ...prev[area], visible: !prev[area].visible }
    }));
  }, [setConfig]);
  
  const updateArea = useCallback((area: LayoutArea, updates: Partial<LayoutConfig[typeof area]>) => {
    setConfig(prev => ({
      ...prev,
      [area]: { ...prev[area], ...updates }
    }));
  }, [setConfig]);
  
  const resetLayout = useCallback(() => {
    setConfig(DEFAULT_CONFIG);
  }, [setConfig]);
  
  const isAreaVisible = useCallback((area: LayoutArea) => {
    return config[area].visible;
  }, [config]);
  
  return {
    config,
    setConfig,
    toggleArea,
    updateArea,
    resetLayout,
    isAreaVisible,
  };
};

// ============================================================================
// 導出
// ============================================================================

export default Layout;
export type { LayoutConfig, LayoutArea };