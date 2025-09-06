import { useState, useEffect, useCallback } from 'react';
import { useLocalStorage } from './useLocalStorage';

/**
 * 主題類型定義
 */
export type Theme = 'light' | 'dark';

/**
 * 主題配置介面
 */
interface ThemeConfig {
  theme: Theme;
  systemPreference: Theme;
  followSystem: boolean;
}

/**
 * useTheme Hook 返回值介面
 */
interface UseThemeReturn {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  followSystem: boolean;
  setFollowSystem: (follow: boolean) => void;
  systemPreference: Theme;
}

/**
 * 檢測系統主題偏好
 * @returns 系統主題偏好
 */
const getSystemTheme = (): Theme => {
  if (typeof window === 'undefined') return 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

/**
 * 應用主題到DOM
 * @param theme 要應用的主題
 */
const applyTheme = (theme: Theme): void => {
  const root = document.documentElement;
  
  // 移除舊的主題類別
  root.classList.remove('light', 'dark');
  
  // 添加新的主題類別
  root.classList.add(theme);
  
  // 設置CSS變數
  if (theme === 'dark') {
    root.style.setProperty('--vscode-background', '#1e1e1e');
    root.style.setProperty('--vscode-foreground', '#cccccc');
    root.style.setProperty('--vscode-panel-background', '#252526');
    root.style.setProperty('--vscode-panel-border', '#3c3c3c');
    root.style.setProperty('--vscode-button-background', '#0e639c');
    root.style.setProperty('--vscode-button-hover-background', '#1177bb');
    root.style.setProperty('--vscode-input-background', '#3c3c3c');
    root.style.setProperty('--vscode-input-border', '#3c3c3c');
    root.style.setProperty('--vscode-list-hover-background', '#2a2d2e');
    root.style.setProperty('--vscode-list-active-background', '#094771');
    root.style.setProperty('--vscode-sidebar-background', '#252526');
    root.style.setProperty('--vscode-activitybar-background', '#333333');
    root.style.setProperty('--vscode-statusbar-background', '#007acc');
    root.style.setProperty('--vscode-tab-active-background', '#1e1e1e');
    root.style.setProperty('--vscode-tab-inactive-background', '#2d2d30');
    root.style.setProperty('--vscode-editor-background', '#1e1e1e');
    root.style.setProperty('--vscode-editor-line-highlight', '#2a2d2e');
  } else {
    root.style.setProperty('--vscode-background', '#ffffff');
    root.style.setProperty('--vscode-foreground', '#333333');
    root.style.setProperty('--vscode-panel-background', '#f3f3f3');
    root.style.setProperty('--vscode-panel-border', '#e5e5e5');
    root.style.setProperty('--vscode-button-background', '#0078d4');
    root.style.setProperty('--vscode-button-hover-background', '#106ebe');
    root.style.setProperty('--vscode-input-background', '#ffffff');
    root.style.setProperty('--vscode-input-border', '#cecece');
    root.style.setProperty('--vscode-list-hover-background', '#f0f0f0');
    root.style.setProperty('--vscode-list-active-background', '#e4f3ff');
    root.style.setProperty('--vscode-sidebar-background', '#f3f3f3');
    root.style.setProperty('--vscode-activitybar-background', '#2c2c2c');
    root.style.setProperty('--vscode-statusbar-background', '#007acc');
    root.style.setProperty('--vscode-tab-active-background', '#ffffff');
    root.style.setProperty('--vscode-tab-inactive-background', '#ececec');
    root.style.setProperty('--vscode-editor-background', '#ffffff');
    root.style.setProperty('--vscode-editor-line-highlight', '#f0f0f0');
  }
  
  // 更新meta標籤
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', theme === 'dark' ? '#1e1e1e' : '#ffffff');
  }
};

/**
 * 主題管理Hook
 * 提供主題切換、系統主題跟隨等功能
 * 
 * @returns 主題管理相關的狀態和方法
 */
export const useTheme = (): UseThemeReturn => {
  // 從localStorage獲取主題配置
  const [themeConfig, setThemeConfig] = useLocalStorage<ThemeConfig>('proxy-manager-theme', {
    theme: 'dark',
    systemPreference: getSystemTheme(),
    followSystem: false,
  });

  // 當前生效的主題
  const [currentTheme, setCurrentTheme] = useState<Theme>(
    themeConfig.followSystem ? themeConfig.systemPreference : themeConfig.theme
  );

  // 監聽系統主題變化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleSystemThemeChange = (e: MediaQueryListEvent) => {
      const newSystemTheme: Theme = e.matches ? 'dark' : 'light';
      
      setThemeConfig(prev => ({
        ...prev,
        systemPreference: newSystemTheme,
      }));
      
      // 如果跟隨系統主題，則更新當前主題
      if (themeConfig.followSystem) {
        setCurrentTheme(newSystemTheme);
      }
    };

    mediaQuery.addEventListener('change', handleSystemThemeChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
    };
  }, [themeConfig.followSystem, setThemeConfig]);

  // 應用主題到DOM
  useEffect(() => {
    applyTheme(currentTheme);
  }, [currentTheme]);

  // 更新當前主題當配置變化時
  useEffect(() => {
    const newTheme = themeConfig.followSystem ? themeConfig.systemPreference : themeConfig.theme;
    if (newTheme !== currentTheme) {
      setCurrentTheme(newTheme);
    }
  }, [themeConfig, currentTheme]);

  /**
   * 設置主題
   * @param theme 要設置的主題
   */
  const setTheme = useCallback((theme: Theme) => {
    setThemeConfig(prev => ({
      ...prev,
      theme,
      followSystem: false, // 手動設置主題時停止跟隨系統
    }));
    setCurrentTheme(theme);
  }, [setThemeConfig]);

  /**
   * 切換主題
   */
  const toggleTheme = useCallback(() => {
    const newTheme: Theme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }, [currentTheme, setTheme]);

  /**
   * 設置是否跟隨系統主題
   * @param follow 是否跟隨系統主題
   */
  const setFollowSystem = useCallback((follow: boolean) => {
    setThemeConfig(prev => ({
      ...prev,
      followSystem: follow,
    }));
    
    if (follow) {
      setCurrentTheme(themeConfig.systemPreference);
    }
  }, [setThemeConfig, themeConfig.systemPreference]);

  return {
    theme: currentTheme,
    setTheme,
    toggleTheme,
    followSystem: themeConfig.followSystem,
    setFollowSystem,
    systemPreference: themeConfig.systemPreference,
  };
};

/**
 * 主題提供者組件的Props
 */
interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  followSystem?: boolean;
}

/**
 * 主題提供者組件
 * 在應用程式根部使用，確保主題正確初始化
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'dark',
  followSystem = false,
}) => {
  const { theme } = useTheme();

  // 初始化主題
  useEffect(() => {
    if (!localStorage.getItem('proxy-manager-theme')) {
      const initialTheme = followSystem ? getSystemTheme() : defaultTheme;
      applyTheme(initialTheme);
    }
  }, [defaultTheme, followSystem]);

  return <>{children}</>;
};

/**
 * 獲取當前主題的工具函數
 * @returns 當前主題
 */
export const getCurrentTheme = (): Theme => {
  const root = document.documentElement;
  return root.classList.contains('dark') ? 'dark' : 'light';
};

/**
 * 主題相關的CSS類別工具函數
 */
export const themeClasses = {
  /**
   * 根據主題返回對應的CSS類別
   * @param lightClass 淺色主題類別
   * @param darkClass 深色主題類別
   * @returns 對應主題的CSS類別
   */
  conditional: (lightClass: string, darkClass: string): string => {
    const theme = getCurrentTheme();
    return theme === 'dark' ? darkClass : lightClass;
  },
  
  /**
   * 背景色類別
   */
  bg: {
    primary: 'bg-vscode-bg',
    secondary: 'bg-vscode-panel-bg',
    sidebar: 'bg-vscode-sidebar-bg',
    activitybar: 'bg-vscode-activitybar-bg',
    editor: 'bg-vscode-editor-bg',
  },
  
  /**
   * 文字色類別
   */
  text: {
    primary: 'text-vscode-foreground',
    secondary: 'text-vscode-foreground/70',
    muted: 'text-vscode-foreground/50',
  },
  
  /**
   * 邊框色類別
   */
  border: {
    default: 'border-vscode-border',
    panel: 'border-vscode-panel-border',
  },
};