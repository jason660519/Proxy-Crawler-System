import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark' | 'system';

/**
 * useTheme Hook - 主題管理
 * 管理應用程序的主題狀態和切換
 */
export const useTheme = () => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // 從 localStorage 獲取保存的主題，默認為 'system'
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('theme') as Theme) || 'system';
    }
    return 'system';
  });

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const root = window.document.documentElement;
    
    // 移除之前的主題類
    root.classList.remove('light', 'dark');
    
    let effectiveTheme: 'light' | 'dark';
    
    if (theme === 'system') {
      // 檢測系統主題偏好
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      effectiveTheme = systemTheme;
    } else {
      effectiveTheme = theme;
    }
    
    // 應用主題類到根元素
    root.classList.add(effectiveTheme);
    setResolvedTheme(effectiveTheme);
    
    // 保存主題到 localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    // 監聽系統主題變化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = () => {
      if (theme === 'system') {
        const systemTheme = mediaQuery.matches ? 'dark' : 'light';
        const root = window.document.documentElement;
        root.classList.remove('light', 'dark');
        root.classList.add(systemTheme);
        setResolvedTheme(systemTheme);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  return {
    theme,
    resolvedTheme,
    setTheme
  };
};