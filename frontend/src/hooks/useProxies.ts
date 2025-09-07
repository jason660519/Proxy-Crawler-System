import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { proxyApi, queryKeys } from '../utils/api';
import type { ProxyNode, ProxyStats } from '../utils/api';

/**
 * 獲取代理列表的自定義 Hook
 */
export const useProxies = (params?: {
  page?: number;
  limit?: number;
  country?: string;
  protocol?: string;
  anonymity?: string;
  status?: 'online' | 'offline';
  search?: string;
}) => {
  return useQuery({
    queryKey: queryKeys.proxies.list(params),
    queryFn: () => proxyApi.getProxies(params),
    staleTime: 5 * 60 * 1000, // 5 分鐘
  });
};

/**
 * 獲取代理統計信息的自定義 Hook
 */
export const useProxyStats = () => {
  return useQuery({
    queryKey: queryKeys.proxies.stats(),
    queryFn: () => proxyApi.getStats(),
    staleTime: 10 * 60 * 1000, // 10 分鐘
  });
};

/**
 * 測試單個代理的自定義 Hook
 */
export const useTestProxy = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => proxyApi.testProxy(id),
    onSuccess: () => {
      // 測試成功後刷新代理列表
      queryClient.invalidateQueries({ queryKey: queryKeys.proxies.lists() });
    },
  });
};

/**
 * 刷新代理數據的自定義 Hook
 */
export const useRefreshProxies = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => proxyApi.refreshProxies(),
    onSuccess: () => {
      // 刷新成功後刷新代理列表和統計信息
      queryClient.invalidateQueries({ queryKey: queryKeys.proxies.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.proxies.stats() });
    },
  });
};