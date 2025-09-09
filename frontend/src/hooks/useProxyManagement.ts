/**
 * 代理管理 Hook
 * 
 * 提供代理管理相關的狀態管理和操作方法
 */

import { useState, useCallback } from 'react';
import type { 
  ProxyNode, 
  ProxyFilters, 
  ProxyManagementState,
  BulkOperationResult,
  PaginationParams,
  SortConfig,
  ProxyTestResult
} from '../types';

import { proxyApi } from '../api/proxyApi';

/**
 * 代理管理 Hook
 * 
 * @returns 代理管理狀態和操作方法
 */
export const useProxyManagement = () => {
  const [state, setState] = useState<ProxyManagementState>({
    proxies: [],
    selectedProxies: [],
    filters: {
      status: [],
      protocol: [],
      country: [],
      anonymity: [],
      search: ''
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
    total: 0,
    totalCount: 0
  });

  /**
   * 載入代理列表
   */
  const loadProxies = useCallback(async (params: {
    filters?: ProxyFilters;
    pagination?: PaginationParams;
    sort?: SortConfig;
  }) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const response = await proxyApi.getProxies(params);
      setState(prev => ({
        ...prev,
        proxies: response.data || [],
        total: response.pagination?.total || 0,
        totalCount: response.pagination?.total || 0,
        loading: false
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '載入代理列表失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 建立新代理
   */
  const createProxy = useCallback(async (proxyData: Partial<ProxyNode>) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const newProxy = await proxyApi.createProxy(proxyData);
      setState(prev => ({
        ...prev,
        proxies: [newProxy, ...prev.proxies],
        totalCount: prev.totalCount + 1,
        loading: false
      }));
      return newProxy;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '建立代理失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 更新代理
   */
  const updateProxy = useCallback(async (id: string, proxyData: Partial<ProxyNode>) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const updatedProxy = await proxyApi.updateProxy(id, proxyData);
      setState(prev => ({
        ...prev,
        proxies: prev.proxies.map(proxy => 
          proxy.id === id ? updatedProxy : proxy
        ),
        loading: false
      }));
      return updatedProxy;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '更新代理失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 刪除代理
   */
  const deleteProxy = useCallback(async (id: string) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      await proxyApi.deleteProxy(id);
      setState(prev => ({
        ...prev,
        proxies: prev.proxies.filter(proxy => proxy.id !== id),
        totalCount: prev.totalCount - 1,
        loading: false
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '刪除代理失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 測試代理
   */
  const testProxy = useCallback(async (id: string): Promise<ProxyTestResult> => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const result = await proxyApi.testProxy(id);
      
      // 更新代理狀態
      setState(prev => ({
        ...prev,
        proxies: prev.proxies.map(proxy => 
          proxy.id === id ? {
            ...proxy,
            status: result.success ? 'active' : 'error',
            lastChecked: new Date().toISOString(),
            responseTime: result.response_time
          } : proxy
        ),
        loading: false
      }));
      
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '測試代理失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 批量操作
   */
  const bulkOperation = useCallback(async (
    operation: string, 
    proxyIds: string[]
  ): Promise<BulkOperationResult> => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const result = await proxyApi.bulkOperation(operation, proxyIds);
      
      // 根據操作類型更新狀態
      if (operation === 'delete') {
        setState(prev => ({
          ...prev,
          proxies: prev.proxies.filter(proxy => !proxyIds.includes(proxy.id)),
          total: prev.total - proxyIds.length,
          totalCount: prev.totalCount - proxyIds.length,
          loading: false
        }));
      } else {
        // 重新載入列表以獲取最新狀態
        await loadProxies({});
      }
      
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '批量操作失敗'
      }));
      throw error;
    }
  }, [loadProxies]);

  /**
   * 設置選中的代理
   */
  const setSelectedProxies = useCallback((proxyIds: string[]) => {
    setState(prev => ({ ...prev, selectedProxies: proxyIds }));
  }, []);

  /**
   * 清除錯誤
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: undefined }));
  }, []);

  return {
    state,
    actions: {
      loadProxies,
      createProxy,
      updateProxy,
      deleteProxy,
      testProxy,
      bulkOperation,
      setSelectedProxies,
      clearError
    }
  };
};

export default useProxyManagement;