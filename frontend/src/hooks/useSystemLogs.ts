/**
 * 系統日誌管理 Hook
 * 
 * 提供系統日誌相關的狀態管理和操作方法
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import type {
  LogEntry,
  LogFilters,
  SystemLogsState,
  PaginationParams,
  SortConfig
} from '../types';
import { logsApi } from '../api/logsApi';

/**
 * 系統日誌管理 Hook
 * 
 * @returns 系統日誌狀態和操作方法
 */
export const useSystemLogs = () => {
  const [state, setState] = useState<SystemLogsState>({
    logs: [],
    filters: {
      level: undefined,
      source: undefined,
      search: undefined,
      timeRange: undefined
    },
    pagination: {
      current: 1,
      pageSize: 20,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true
    },
    loading: false,
    error: undefined,
    totalCount: 0,
    realTimeEnabled: false
  });

  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * 載入日誌列表
   */
  const loadLogs = useCallback(async (params: {
    filters?: LogFilters;
    pagination?: PaginationParams;
    sort?: SortConfig;
  }) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const response = await logsApi.getLogs(params);
      setState(prev => ({
        ...prev,
        logs: response.data || [],
        totalCount: response.pagination?.total || 0,
        loading: false
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '載入日誌列表失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 搜尋日誌
   */
  const searchLogs = useCallback(async (params: {
    query: string;
    filters?: LogFilters;
    pagination?: PaginationParams;
  }) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const response = await logsApi.searchLogs(params);
      setState(prev => ({
        ...prev,
        searchResults: response.data,
        loading: false
      }));
      return response;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '搜尋日誌失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 載入日誌統計
   */
  const loadStatistics = useCallback(async (filters?: LogFilters) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const statistics = await logsApi.getStatistics(filters);
      setState(prev => ({
        ...prev,
        statistics,
        loading: false
      }));
      return statistics;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '載入統計資料失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 導出日誌
   */
  const exportLogs = useCallback(async (params: {
    filters?: LogFilters;
    format: 'csv' | 'json' | 'txt';
    dateRange?: {
      start: string;
      end: string;
    };
  }): Promise<any> => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const result = await logsApi.exportLogs(params);
      setState(prev => ({ ...prev, loading: false }));
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '導出日誌失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 啟用/停用即時日誌流
   */
  const toggleRealTimeStream = useCallback((enabled: boolean) => {
    setState(prev => ({ ...prev, realTimeEnabled: enabled }));
    
    if (enabled) {
      // 建立 WebSocket 連接
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/logs/stream`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('即時日誌流已連接');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const newLog: LogEntry = JSON.parse(event.data);
          setState(prev => ({
            ...prev,
            logs: [newLog, ...prev.logs.slice(0, 999)] // 保持最新 1000 條日誌
          }));
        } catch (error) {
          console.error('解析即時日誌失敗:', error);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        setState(prev => ({
          ...prev,
          error: '即時日誌流連接失敗',
          realTimeEnabled: false
        }));
      };
      
      wsRef.current.onclose = () => {
        console.log('即時日誌流已斷開');
        setState(prev => ({ ...prev, realTimeEnabled: false }));
      };
    } else {
      // 關閉 WebSocket 連接
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }
  }, []);

  /**
   * 清除日誌（管理員功能）
   */
  const clearLogs = useCallback(async (filters?: LogFilters) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      await logsApi.clearLogs(filters);
      setState(prev => ({
        ...prev,
        logs: [],
        totalCount: 0,
        loading: false
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '清除日誌失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 清除搜尋結果
   */
  const clearSearchResults = useCallback(() => {
    setState(prev => ({ ...prev, searchResults: [] }));
  }, []);

  /**
   * 清除錯誤
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: undefined }));
  }, []);

  /**
   * 定期更新統計資料
   */
  const startStatisticsUpdates = useCallback(() => {
    intervalRef.current = setInterval(() => {
      loadStatistics();
    }, 30000); // 每 30 秒更新一次統計
  }, [loadStatistics]);

  const stopStatisticsUpdates = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  /**
   * 清理副作用
   */
  useEffect(() => {
    return () => {
      // 清理 WebSocket 連接
      if (wsRef.current) {
        wsRef.current.close();
      }
      
      // 清理定時器
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    state,
    actions: {
      loadLogs,
      searchLogs,
      loadStatistics,
      exportLogs,
      toggleRealTimeStream,
      clearLogs,
      clearSearchResults,
      clearError,
      startStatisticsUpdates,
      stopStatisticsUpdates
    }
  };
};

export default useSystemLogs;