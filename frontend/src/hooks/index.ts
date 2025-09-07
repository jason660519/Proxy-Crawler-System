/**
 * React Hooks 集合
 * 提供狀態管理、資料獲取、副作用處理等功能
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { lightTheme, darkTheme, colors } from '../styles';
import type {
  HealthStatus,
  SystemMetrics,
  ProxyNode,
  Task,
  LogEntry,
  TrendData,
  PaginatedResponse,
  ProxyQueryParams,
  TaskQueryParams,
  LogQueryParams
} from '../types';
import { api } from '../services/api';

// ============= 基礎 Hooks =============

/**
 * 本地儲存 Hook
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`讀取 localStorage 失敗 (${key}):`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`寫入 localStorage 失敗 (${key}):`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue] as const;
}

/**
 * 防抖 Hook
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * 間隔執行 Hook
 */
export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef<() => void>(() => {});

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    function tick() {
      savedCallback.current?.();
    }
    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

/**
 * 非同步狀態 Hook
 */
export function useAsyncState<T>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async (asyncFunction: () => Promise<T>) => {
    try {
      setLoading(true);
      setError(null);
      const result = await asyncFunction();
      setData(result);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('未知錯誤');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}

// ============= 健康狀態 Hooks =============

/**
 * 健康狀態 Hook
 */
export function useHealthStatus() {
  const [mainHealth, setMainHealth] = useState<HealthStatus | null>(null);
  const [etlHealth, setEtlHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchHealthStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // 暫時只調用主服務健康檢查，避免 ETL 服務錯誤
      const main = await api.getMainHealth();
      setMainHealth(main);
      // 設置 ETL 為不可用狀態
      setEtlHealth({
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        details: { error: 'ETL 服務暫時不可用' }
      });
    } catch (err) {
      const error = err instanceof Error ? err : new Error('獲取健康狀態失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealthStatus();
  }, [fetchHealthStatus]);

  // 自動輪詢
  useInterval(fetchHealthStatus, 30000); // 每 30 秒更新一次

  const overallStatus = useMemo(() => {
    if (!mainHealth || !etlHealth) return 'unknown';
    if (mainHealth.status === 'healthy' && etlHealth.status === 'healthy') {
      return 'healthy';
    } else if (mainHealth.status === 'unhealthy' && etlHealth.status === 'unhealthy') {
      return 'unhealthy';
    } else {
      return 'degraded';
    }
  }, [mainHealth, etlHealth]);

  return {
    mainHealth,
    etlHealth,
    overallStatus,
    loading,
    error,
    refresh: fetchHealthStatus
  };
}

// ============= 系統指標 Hooks =============

/**
 * 系統指標 Hook
 */
export function useSystemMetrics() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSystemMetrics();
      setMetrics(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('獲取系統指標失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // 自動輪詢
  useInterval(fetchMetrics, 15000); // 每 15 秒更新一次

  return {
    metrics,
    loading,
    error,
    refresh: fetchMetrics
  };
}

/**
 * 趨勢資料 Hook
 */
export function useTrendData(timeRange: '1h' | '6h' | '24h' | '7d' = '24h') {
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchTrendData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getTrendData(timeRange);
      setTrendData(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('獲取趨勢資料失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchTrendData();
  }, [fetchTrendData]);

  // 自動輪詢
  useInterval(fetchTrendData, 60000); // 每分鐘更新一次

  return {
    trendData,
    loading,
    error,
    refresh: fetchTrendData
  };
}

// ============= 代理節點 Hooks =============

/**
 * 代理節點列表 Hook
 */
export function useProxies(initialParams: ProxyQueryParams = {}) {
  const [proxies, setProxies] = useState<PaginatedResponse<ProxyNode> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [params, setParams] = useState<ProxyQueryParams>(initialParams);

  const fetchProxies = useCallback(async (queryParams?: ProxyQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const finalParams = queryParams || params;
      const data = await api.getProxies(finalParams);
      setProxies(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('獲取代理節點失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchProxies();
  }, [fetchProxies]);

  const updateParams = useCallback((newParams: Partial<ProxyQueryParams>) => {
    setParams(prev => ({ ...prev, ...newParams }));
  }, []);

  const validateProxy = useCallback(async (id: string) => {
    try {
      await api.validateProxy(id);
      // 重新獲取資料以更新狀態
      await fetchProxies();
    } catch (err) {
      console.error('驗證代理節點失敗:', err);
      throw err;
    }
  }, [fetchProxies]);

  const deleteProxy = useCallback(async (id: string) => {
    try {
      await api.deleteProxy(id);
      // 重新獲取資料
      await fetchProxies();
    } catch (err) {
      console.error('刪除代理節點失敗:', err);
      throw err;
    }
  }, [fetchProxies]);

  return {
    proxies,
    loading,
    error,
    params,
    updateParams,
    refresh: fetchProxies,
    validateProxy,
    deleteProxy
  };
}

// ============= 任務管理 Hooks =============

/**
 * 任務列表 Hook
 */
export function useTasks(initialParams: TaskQueryParams = {}) {
  const [tasks, setTasks] = useState<PaginatedResponse<Task> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [params, setParams] = useState<TaskQueryParams>(initialParams);

  const fetchTasks = useCallback(async (queryParams?: TaskQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const finalParams = queryParams || params;
      const data = await api.getTasks(finalParams);
      setTasks(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('獲取任務列表失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // 自動輪詢運行中的任務
  useInterval(() => {
    if (tasks?.data?.some(task => task.status === 'running' || task.status === 'pending')) {
      fetchTasks();
    }
  }, 5000); // 每 5 秒檢查一次

  const updateParams = useCallback((newParams: Partial<TaskQueryParams>) => {
    setParams(prev => ({ ...prev, ...newParams }));
  }, []);

  const retryTask = useCallback(async (id: string) => {
    try {
      await api.retryTask(id);
      await fetchTasks();
    } catch (err) {
      console.error('重試任務失敗:', err);
      throw err;
    }
  }, [fetchTasks]);

  const cancelTask = useCallback(async (id: string) => {
    try {
      await api.cancelTask(id);
      await fetchTasks();
    } catch (err) {
      console.error('取消任務失敗:', err);
      throw err;
    }
  }, [fetchTasks]);

  return {
    tasks,
    loading,
    error,
    params,
    updateParams,
    refresh: fetchTasks,
    retryTask,
    cancelTask
  };
}

// ============= 日誌 Hooks =============

/**
 * 日誌 Hook
 */
export function useLogs(initialParams: LogQueryParams = {}) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [params, setParams] = useState<LogQueryParams>({
    limit: 100,
    ...initialParams
  });

  const fetchLogs = useCallback(async (queryParams?: LogQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const finalParams = queryParams || params;
      const data = await api.getLogs(finalParams);
      setLogs(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('獲取日誌失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // 自動輪詢新日誌
  useInterval(fetchLogs, 10000); // 每 10 秒更新一次

  const updateParams = useCallback((newParams: Partial<LogQueryParams>) => {
    setParams(prev => ({ ...prev, ...newParams }));
  }, []);

  return {
    logs,
    loading,
    error,
    params,
    updateParams,
    refresh: fetchLogs
  };
}

// ============= 搜尋 Hook =============

/**
 * 全域搜尋 Hook
 */
export function useGlobalSearch() {
  const [results, setResults] = useState<{
    proxies: ProxyNode[];
    tasks: Task[];
    logs: LogEntry[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const search = useCallback(async (query: string, types?: string[]) => {
    if (!query.trim()) {
      setResults(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await api.globalSearch(query, types);
      setResults(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('搜尋失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return {
    results,
    loading,
    error,
    search,
    clear
  };
}

// ============= 主題 Hook =============

/**
 * 主題 Hook
 */
export function useTheme() {
  const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'light');
  const [isInitialized, setIsInitialized] = useState(false);

  const applyCssVariables = useCallback((themeName: 'light' | 'dark') => {
    const themeObj = themeName === 'dark' ? darkTheme : lightTheme;
    const root = document.documentElement.style;
    // 背景
    root.setProperty('--color-background-primary', themeObj.colors.background.primary);
    root.setProperty('--color-background-secondary', themeObj.colors.background.secondary);
    root.setProperty('--color-background-tertiary', themeObj.colors.background.tertiary);
    root.setProperty('--color-background-elevated', themeObj.colors.background.elevated);
    root.setProperty('--color-background-card', themeObj.colors.background.elevated);
    root.setProperty('--color-background-hover', themeObj.colors.background.secondary);
    root.setProperty('--color-background-disabled', themeObj.colors.background.secondary);
    root.setProperty('--color-background-tooltip', themeObj.colors.background.tertiary);
    // 文字
    root.setProperty('--color-text-primary', themeObj.colors.text.primary);
    root.setProperty('--color-text-secondary', themeObj.colors.text.secondary);
    root.setProperty('--color-text-tertiary', themeObj.colors.text.tertiary);
    root.setProperty('--color-text-inverse', themeObj.colors.text.inverse);
    root.setProperty('--color-text-disabled', themeObj.colors.text.disabled);
    // 邊框
    root.setProperty('--color-border-primary', themeObj.colors.border.primary);
    root.setProperty('--color-border-secondary', themeObj.colors.border.secondary);
    root.setProperty('--color-border-focus', themeObj.colors.border.focus);
    // 狀態
    root.setProperty('--color-status-success', themeObj.colors.status.success);
    root.setProperty('--color-status-warning', themeObj.colors.status.warning);
    root.setProperty('--color-status-error', themeObj.colors.status.error);
    root.setProperty('--color-status-info', themeObj.colors.status.info);
    // 互動
    root.setProperty('--color-interactive-primary', themeObj.colors.interactive.primary);
    root.setProperty('--color-interactive-primaryHover', themeObj.colors.interactive.primaryHover);
    root.setProperty('--color-interactive-primaryActive', themeObj.colors.interactive.primaryActive);
    root.setProperty('--color-interactive-secondary', themeObj.colors.interactive.secondary);
    root.setProperty('--color-interactive-secondaryHover', themeObj.colors.interactive.secondaryHover);
    root.setProperty('--color-interactive-secondaryActive', themeObj.colors.interactive.secondaryActive);
    // Primary scale（固定來自 colors）
    root.setProperty('--color-primary-50', colors.primary[50]);
    root.setProperty('--color-primary-100', colors.primary[100]);
    root.setProperty('--color-primary-200', colors.primary[200]);
    root.setProperty('--color-primary-300', colors.primary[300]);
    root.setProperty('--color-primary-400', colors.primary[400]);
    root.setProperty('--color-primary-500', colors.primary[500]);
    root.setProperty('--color-primary-600', colors.primary[600]);
    root.setProperty('--color-primary-700', colors.primary[700]);
    root.setProperty('--color-primary-800', colors.primary[800]);
    root.setProperty('--color-primary-900', colors.primary[900]);
    // Neutral scale
    root.setProperty('--color-neutral-50', colors.gray[50]);
    root.setProperty('--color-neutral-100', colors.gray[100]);
    root.setProperty('--color-neutral-200', colors.gray[200]);
    root.setProperty('--color-neutral-300', colors.gray[300]);
    root.setProperty('--color-neutral-400', colors.gray[400]);
    root.setProperty('--color-neutral-500', colors.gray[500]);
    root.setProperty('--color-neutral-600', colors.gray[600]);
    root.setProperty('--color-neutral-700', colors.gray[700]);
    root.setProperty('--color-neutral-800', colors.gray[800]);
    root.setProperty('--color-neutral-900', colors.gray[900]);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      const newTheme = prev === 'light' ? 'dark' : 'light';
      console.log(`主題切換: ${prev} -> ${newTheme}`);
      // 同步通知其他 hook 實例
      try {
        window.dispatchEvent(new CustomEvent('js-theme-changed', { detail: newTheme }));
      } catch (err) {
        console.warn('js-theme-changed dispatch 失敗:', err);
      }
      // 立即套用 CSS 變數（即使 ThemeProvider 尚未重渲染）
      try {
        applyCssVariables(newTheme);
      } catch {}
      return newTheme;
    });
  }, [setTheme, applyCssVariables]);

  useEffect(() => {
    // 設置主題屬性
    document.documentElement.setAttribute('data-theme', theme);
    // 套用 CSS 變數，確保視覺立即更新
    try { applyCssVariables(theme); } catch {}
    
    // 設置系統偏好檢測
    if (!isInitialized) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      console.log(`系統偏好深色模式: ${prefersDark}, 當前主題: ${theme}`);
      setIsInitialized(true);
    }
    
    // 強制重新渲染以確保樣式更新
    setTimeout(() => {
      document.documentElement.style.setProperty('--theme-transition', 'all 0.3s ease');
    }, 0);
  }, [theme, isInitialized, applyCssVariables]);

  // 跨組件同步：監聽主題變更事件
  useEffect(() => {
    const handleThemeChanged = (e: Event) => {
      const newTheme = (e as CustomEvent<'light' | 'dark'>).detail;
      if (newTheme && newTheme !== theme) {
        setTheme(newTheme);
      }
    };

    window.addEventListener('js-theme-changed', handleThemeChanged as EventListener);
    return () => {
      window.removeEventListener('js-theme-changed', handleThemeChanged as EventListener);
    };
  }, [theme, setTheme]);

  // 保險同步：監聽 data-theme 屬性變化（MutationObserver）
  useEffect(() => {
    const target = document.documentElement;
    const observer = new MutationObserver(() => {
      const attr = target.getAttribute('data-theme') as 'light' | 'dark' | null;
      if (attr && attr !== theme) {
        setTheme(attr);
      }
    });
    observer.observe(target, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, [theme, setTheme]);

  return {
    theme,
    setTheme,
    toggleTheme,
    isDark: theme === 'dark',
    isInitialized
  };
}

/**
 * 任務佇列 Hook (簡化版本，用於 Activity Bar)
 */
export function useTaskQueue() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getTasks({ size: 10, status: ['running'] });
      setTasks(data.data || []);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('獲取任務佇列失敗');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // 自動輪詢任務狀態
  useInterval(fetchTasks, 5000); // 每 5 秒更新一次

  return {
    tasks,
    loading,
    error,
    refresh: fetchTasks
  };
}

// ============= 匯出所有 Hooks =============

export const hooks = {
  // 基礎
  useLocalStorage,
  useDebounce,
  useInterval,
  useAsyncState,
  
  // 健康狀態
  useHealthStatus,
  
  // 系統指標
  useSystemMetrics,
  useTrendData,
  
  // 代理節點
  useProxies,
  
  // 任務管理
  useTasks,
  useTaskQueue,
  
  // 日誌
  useLogs,
  
  // 搜尋
  useGlobalSearch,
  
  // 主題
  useTheme
};

export default hooks;