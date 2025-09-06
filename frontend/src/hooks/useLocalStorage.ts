import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * localStorage Hook 的選項配置
 */
interface UseLocalStorageOptions<T> {
  /** 序列化函數，預設使用 JSON.stringify */
  serializer?: {
    read: (value: string) => T;
    write: (value: T) => string;
  };
  /** 是否在多個標籤頁間同步 */
  syncAcrossTabs?: boolean;
  /** 錯誤處理函數 */
  onError?: (error: Error) => void;
}

/**
 * 預設的序列化器
 */
const defaultSerializer = {
  read: <T>(value: string): T => {
    try {
      return JSON.parse(value);
    } catch {
      return value as unknown as T;
    }
  },
  write: <T>(value: T): string => {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  },
};

/**
 * 類型安全的 localStorage Hook
 * 提供自動序列化、跨標籤頁同步、錯誤處理等功能
 * 
 * @param key localStorage 鍵名
 * @param initialValue 初始值
 * @param options 配置選項
 * @returns [value, setValue, removeValue] 元組
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {}
): [T, (value: T | ((prevValue: T) => T)) => void, () => void] {
  const {
    serializer = defaultSerializer,
    syncAcrossTabs = true,
    onError = (error) => console.error(`useLocalStorage error for key "${key}":`, error),
  } = options;

  // 使用 ref 來避免不必要的重新渲染
  const initialValueRef = useRef(initialValue);
  
  // 讀取 localStorage 中的值
  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValueRef.current;
    }

    try {
      const item = window.localStorage.getItem(key);
      if (item === null) {
        return initialValueRef.current;
      }
      return serializer.read(item);
    } catch (error) {
      onError(error as Error);
      return initialValueRef.current;
    }
  }, [key, serializer, onError]);

  // 狀態初始化
  const [storedValue, setStoredValue] = useState<T>(readValue);

  // 寫入 localStorage
  const setValue = useCallback(
    (value: T | ((prevValue: T) => T)) => {
      if (typeof window === 'undefined') {
        console.warn(`Tried setting localStorage key "${key}" even though environment is not a client`);
        return;
      }

      try {
        // 計算新值
        const newValue = value instanceof Function ? value(storedValue) : value;
        
        // 更新狀態
        setStoredValue(newValue);
        
        // 寫入 localStorage
        const serializedValue = serializer.write(newValue);
        window.localStorage.setItem(key, serializedValue);
        
        // 觸發自定義事件以支援跨標籤頁同步
        if (syncAcrossTabs) {
          window.dispatchEvent(
            new CustomEvent('local-storage-change', {
              detail: {
                key,
                newValue: serializedValue,
              },
            })
          );
        }
      } catch (error) {
        onError(error as Error);
      }
    },
    [key, storedValue, serializer, syncAcrossTabs, onError]
  );

  // 移除 localStorage 中的值
  const removeValue = useCallback(() => {
    if (typeof window === 'undefined') {
      console.warn(`Tried removing localStorage key "${key}" even though environment is not a client`);
      return;
    }

    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValueRef.current);
      
      // 觸發自定義事件
      if (syncAcrossTabs) {
        window.dispatchEvent(
          new CustomEvent('local-storage-change', {
            detail: {
              key,
              newValue: null,
            },
          })
        );
      }
    } catch (error) {
      onError(error as Error);
    }
  }, [key, syncAcrossTabs, onError]);

  // 監聽 localStorage 變化（原生事件）
  useEffect(() => {
    if (!syncAcrossTabs) return;

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key !== key || e.storageArea !== window.localStorage) {
        return;
      }

      try {
        if (e.newValue === null) {
          setStoredValue(initialValueRef.current);
        } else {
          setStoredValue(serializer.read(e.newValue));
        }
      } catch (error) {
        onError(error as Error);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, serializer, syncAcrossTabs, onError]);

  // 監聽自定義事件（同一標籤頁內的變化）
  useEffect(() => {
    if (!syncAcrossTabs) return;

    const handleCustomStorageChange = (e: CustomEvent) => {
      if (e.detail.key !== key) {
        return;
      }

      try {
        if (e.detail.newValue === null) {
          setStoredValue(initialValueRef.current);
        } else {
          setStoredValue(serializer.read(e.detail.newValue));
        }
      } catch (error) {
        onError(error as Error);
      }
    };

    window.addEventListener('local-storage-change', handleCustomStorageChange as EventListener);
    return () => window.removeEventListener('local-storage-change', handleCustomStorageChange as EventListener);
  }, [key, serializer, syncAcrossTabs, onError]);

  // 頁面載入時重新讀取值
  useEffect(() => {
    const value = readValue();
    if (value !== storedValue) {
      setStoredValue(value);
    }
  }, [readValue, storedValue]);

  return [storedValue, setValue, removeValue];
}

/**
 * 簡化版的 localStorage Hook，只返回值和設置函數
 * 
 * @param key localStorage 鍵名
 * @param initialValue 初始值
 * @returns [value, setValue] 元組
 */
export function useLocalStorageValue<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prevValue: T) => T)) => void] {
  const [value, setValue] = useLocalStorage(key, initialValue);
  return [value, setValue];
}

/**
 * localStorage 工具函數集合
 */
export const localStorageUtils = {
  /**
   * 檢查 localStorage 是否可用
   */
  isAvailable: (): boolean => {
    try {
      const testKey = '__localStorage_test__';
      window.localStorage.setItem(testKey, 'test');
      window.localStorage.removeItem(testKey);
      return true;
    } catch {
      return false;
    }
  },

  /**
   * 獲取 localStorage 中的所有鍵
   */
  getAllKeys: (): string[] => {
    if (typeof window === 'undefined') return [];
    return Object.keys(window.localStorage);
  },

  /**
   * 清空 localStorage
   */
  clear: (): void => {
    if (typeof window !== 'undefined') {
      window.localStorage.clear();
    }
  },

  /**
   * 獲取 localStorage 使用的空間大小（字節）
   */
  getSize: (): number => {
    if (typeof window === 'undefined') return 0;
    
    let total = 0;
    for (const key in window.localStorage) {
      if (window.localStorage.hasOwnProperty(key)) {
        total += window.localStorage[key].length + key.length;
      }
    }
    return total;
  },

  /**
   * 獲取格式化的 localStorage 使用空間
   */
  getFormattedSize: (): string => {
    const bytes = localStorageUtils.getSize();
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  /**
   * 批量設置 localStorage 項目
   */
  setMultiple: (items: Record<string, any>): void => {
    if (typeof window === 'undefined') return;
    
    Object.entries(items).forEach(([key, value]) => {
      try {
        window.localStorage.setItem(key, JSON.stringify(value));
      } catch (error) {
        console.error(`Failed to set localStorage item "${key}":`, error);
      }
    });
  },

  /**
   * 批量獲取 localStorage 項目
   */
  getMultiple: <T = any>(keys: string[]): Record<string, T | null> => {
    if (typeof window === 'undefined') return {};
    
    const result: Record<string, T | null> = {};
    keys.forEach(key => {
      try {
        const item = window.localStorage.getItem(key);
        result[key] = item ? JSON.parse(item) : null;
      } catch (error) {
        console.error(`Failed to get localStorage item "${key}":`, error);
        result[key] = null;
      }
    });
    return result;
  },

  /**
   * 批量移除 localStorage 項目
   */
  removeMultiple: (keys: string[]): void => {
    if (typeof window === 'undefined') return;
    
    keys.forEach(key => {
      try {
        window.localStorage.removeItem(key);
      } catch (error) {
        console.error(`Failed to remove localStorage item "${key}":`, error);
      }
    });
  },
};

/**
 * 專案特定的 localStorage 鍵名常數
 */
export const STORAGE_KEYS = {
  THEME: 'proxy-manager-theme',
  APP_STATE: 'proxy-manager-app-state',
  USER_PREFERENCES: 'proxy-manager-user-preferences',
  DASHBOARD_LAYOUT: 'proxy-manager-dashboard-layout',
  PROXY_FILTERS: 'proxy-manager-proxy-filters',
  TASK_SETTINGS: 'proxy-manager-task-settings',
  EXPORT_SETTINGS: 'proxy-manager-export-settings',
  MONITORING_CONFIG: 'proxy-manager-monitoring-config',
  RECENT_SEARCHES: 'proxy-manager-recent-searches',
  SIDEBAR_STATE: 'proxy-manager-sidebar-state',
} as const;

/**
 * 類型安全的專案 localStorage Hook
 */
export const useProjectStorage = {
  theme: () => useLocalStorage(STORAGE_KEYS.THEME, { theme: 'dark', followSystem: false }),
  appState: () => useLocalStorage(STORAGE_KEYS.APP_STATE, {
    activeView: 'dashboard',
    sidePanelCollapsed: false,
    sidePanelWidth: 300,
  }),
  userPreferences: () => useLocalStorage(STORAGE_KEYS.USER_PREFERENCES, {
    language: 'zh-TW',
    timezone: 'Asia/Taipei',
    dateFormat: 'YYYY-MM-DD',
    timeFormat: '24h',
  }),
};