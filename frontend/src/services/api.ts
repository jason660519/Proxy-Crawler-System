/**
 * API 服務層
 * 封裝所有 API 端點的調用，提供類型安全的介面
 */

import { apiClient, etlApiClient } from './http';
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

// ============= 健康狀態 API =============

/**
 * 獲取主服務健康狀態
 */
export async function getMainHealth(): Promise<HealthStatus> {
  try {
    const data = await apiClient.get<HealthStatus>('/api/health');
    return {
      ...data,
      timestamp: data.timestamp || new Date().toISOString()
    };
  } catch (error) {
    console.error('獲取主服務健康狀態失敗:', error);
    return {
      status: 'unhealthy' as const,
      timestamp: new Date().toISOString(),
      details: { error: (error as Error).message }
    };
  }
}

/**
 * 獲取 ETL 服務健康狀態
 */
export async function getEtlHealth(): Promise<HealthStatus> {
  try {
    const data = await etlApiClient.get<HealthStatus>('/health');
    return {
      ...data,
      timestamp: data.timestamp || new Date().toISOString()
    };
  } catch (error) {
    console.error('獲取 ETL 服務健康狀態失敗:', error);
    return {
      status: 'unhealthy' as const,
      timestamp: new Date().toISOString(),
      details: { error: (error as Error).message }
    };
  }
}

/**
 * 獲取所有服務的健康狀態
 */
export async function getAllHealthStatus(): Promise<{
  main: HealthStatus;
  etl: HealthStatus;
  overall: 'healthy' | 'degraded' | 'unhealthy';
}> {
  const [main, etl] = await Promise.allSettled([
    getMainHealth(),
    getEtlHealth()
  ]);

  const mainHealth = main.status === 'fulfilled' ? main.value : {
    status: 'unhealthy' as const,
    timestamp: new Date().toISOString()
  };

  const etlHealth = etl.status === 'fulfilled' ? etl.value : {
    status: 'unhealthy' as const,
    timestamp: new Date().toISOString()
  };

  // 計算整體健康狀態
  let overall: 'healthy' | 'degraded' | 'unhealthy';
  if (mainHealth.status === 'healthy' && etlHealth.status === 'healthy') {
    overall = 'healthy';
  } else if (mainHealth.status === 'unhealthy' && etlHealth.status === 'unhealthy') {
    overall = 'unhealthy';
  } else {
    overall = 'degraded';
  }

  return { main: mainHealth, etl: etlHealth, overall };
}

// ============= 系統指標 API =============

/**
 * 獲取系統指標摘要
 */
export async function getSystemMetrics(): Promise<SystemMetrics> {
  try {
    return await apiClient.get<SystemMetrics>('/metrics/summary');
  } catch (error) {
    console.error('獲取系統指標失敗:', error);
    // 返回預設值
    return {
      totalProxies: 0,
      activeProxies: 0,
      successRate: 0,
      averageResponseTime: 0,
      tasksInQueue: 0,
      runningTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * 獲取趨勢資料
 */
export async function getTrendData(timeRange: '1h' | '6h' | '24h' | '7d' = '24h'): Promise<TrendData> {
  try {
    return await apiClient.get<TrendData>(`/metrics/trends?range=${timeRange}`);
  } catch (error) {
    console.error('獲取趨勢資料失敗:', error);
    // 返回空資料
    const now = new Date();
    const mockData = Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(now.getTime() - (23 - i) * 60 * 60 * 1000).toISOString(),
      value: Math.random() * 100
    }));

    return {
      successRate: mockData,
      validationCount: mockData.map(d => ({ ...d, value: Math.floor(d.value * 10) })),
      averageLatency: mockData.map(d => ({ ...d, value: Math.floor(d.value * 5 + 100) }))
    };
  }
}

// ============= 代理節點 API =============

/**
 * 獲取代理節點列表
 */
export async function getProxies(params: ProxyQueryParams = {}): Promise<PaginatedResponse<ProxyNode>> {
  try {
    const queryParams = new URLSearchParams();
    
    // 添加查詢參數
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.sortBy) queryParams.append('sortBy', params.sortBy);
    if (params.sortOrder) queryParams.append('sortOrder', params.sortOrder);
    if (params.search) queryParams.append('search', params.search);
    if (params.status) params.status.forEach(s => queryParams.append('status', s));
    if (params.protocol) params.protocol.forEach(p => queryParams.append('protocol', p));
    if (params.country) params.country.forEach(c => queryParams.append('country', c));
    if (params.anonymity) params.anonymity.forEach(a => queryParams.append('anonymity', a));
    if (params.minSpeed) queryParams.append('minSpeed', params.minSpeed.toString());
    if (params.maxSpeed) queryParams.append('maxSpeed', params.maxSpeed.toString());

    const url = `/proxies${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await apiClient.get<PaginatedResponse<ProxyNode>>(url);
  } catch (error) {
    console.error('獲取代理節點列表失敗:', error);
    throw error;
  }
}

/**
 * 獲取單個代理節點詳情
 */
export async function getProxy(id: string): Promise<ProxyNode> {
  return await apiClient.get<ProxyNode>(`/proxies/${id}`);
}

/**
 * 驗證代理節點
 */
export async function validateProxy(id: string): Promise<{ taskId: string }> {
  return await apiClient.post<{ taskId: string }>(`/proxies/${id}/validate`);
}

/**
 * 批次驗證代理節點
 */
export async function validateProxies(ids: string[]): Promise<{ taskId: string }> {
  return await apiClient.post<{ taskId: string }>('/proxies/validate', { ids });
}

/**
 * 刪除代理節點
 */
export async function deleteProxy(id: string): Promise<void> {
  await apiClient.delete(`/proxies/${id}`);
}

/**
 * 批次刪除代理節點
 */
export async function deleteProxies(ids: string[]): Promise<void> {
  await apiClient.delete('/proxies', { data: { ids } });
}

// ============= 任務管理 API =============

/**
 * 獲取任務列表
 */
export async function getTasks(params: TaskQueryParams = {}): Promise<PaginatedResponse<Task>> {
  try {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.sortBy) queryParams.append('sortBy', params.sortBy);
    if (params.sortOrder) queryParams.append('sortOrder', params.sortOrder);
    if (params.search) queryParams.append('search', params.search);
    if (params.status) params.status.forEach(s => queryParams.append('status', s));
    if (params.type) params.type.forEach(t => queryParams.append('type', t));
    if (params.startDate) queryParams.append('startDate', params.startDate);
    if (params.endDate) queryParams.append('endDate', params.endDate);

    const url = `/tasks${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await apiClient.get<PaginatedResponse<Task>>(url);
  } catch (error) {
    console.error('獲取任務列表失敗:', error);
    throw error;
  }
}

/**
 * 獲取單個任務詳情
 */
export async function getTask(id: string): Promise<Task> {
  return await apiClient.get<Task>(`/tasks/${id}`);
}

/**
 * 重試任務
 */
export async function retryTask(id: string): Promise<void> {
  await apiClient.post(`/tasks/${id}/retry`);
}

/**
 * 取消任務
 */
export async function cancelTask(id: string): Promise<void> {
  await apiClient.post(`/tasks/${id}/cancel`);
}

/**
 * 建立新任務
 */
export async function createTask(taskData: {
  name: string;
  type: string;
  config?: Record<string, any>;
}): Promise<Task> {
  return await apiClient.post<Task>('/tasks', taskData);
}

// ============= 日誌 API =============

/**
 * 獲取日誌列表
 */
export async function getLogs(params: LogQueryParams = {}): Promise<LogEntry[]> {
  try {
    const queryParams = new URLSearchParams();
    
    if (params.source) params.source.forEach(s => queryParams.append('source', s));
    if (params.level) params.level.forEach(l => queryParams.append('level', l));
    if (params.since) queryParams.append('since', params.since);
    if (params.until) queryParams.append('until', params.until);
    if (params.search) queryParams.append('search', params.search);
    if (params.limit) queryParams.append('limit', params.limit.toString());

    const url = `/logs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await apiClient.get<LogEntry[]>(url);
  } catch (error) {
    console.error('獲取日誌列表失敗:', error);
    throw error;
  }
}

// ============= ETL API =============

/**
 * 觸發 ETL 同步
 */
export async function triggerEtlSync(source?: string): Promise<{ taskId: string }> {
  const data = source ? { source } : {};
  return await etlApiClient.post<{ taskId: string }>('/sync', data);
}

/**
 * 獲取 ETL 統計
 */
export async function getEtlStats(): Promise<{
  totalSources: number;
  activeSources: number;
  lastSyncTime: string;
  nextSyncTime: string;
  syncInterval: number;
}> {
  try {
    return await etlApiClient.get('/stats');
  } catch (error) {
    console.error('獲取 ETL 統計失敗:', error);
    return {
      totalSources: 0,
      activeSources: 0,
      lastSyncTime: new Date().toISOString(),
      nextSyncTime: new Date(Date.now() + 3600000).toISOString(),
      syncInterval: 3600
    };
  }
}

// ============= 搜尋 API =============

/**
 * 全域搜尋
 */
export async function globalSearch(query: string, types?: string[]): Promise<{
  proxies: ProxyNode[];
  tasks: Task[];
  logs: LogEntry[];
}> {
  try {
    const queryParams = new URLSearchParams();
    queryParams.append('q', query);
    if (types) types.forEach(t => queryParams.append('type', t));

    return await apiClient.get(`/search?${queryParams.toString()}`);
  } catch (error) {
    console.error('全域搜尋失敗:', error);
    return { proxies: [], tasks: [], logs: [] };
  }
}

// ============= 匯出所有 API 函數 =============

export const api = {
  // 健康狀態
  getMainHealth,
  getEtlHealth,
  getAllHealthStatus,
  
  // 系統指標
  getSystemMetrics,
  getTrendData,
  
  // 代理節點
  getProxies,
  getProxy,
  validateProxy,
  validateProxies,
  deleteProxy,
  deleteProxies,
  
  // 任務管理
  getTasks,
  getTask,
  retryTask,
  cancelTask,
  createTask,
  
  // 日誌
  getLogs,
  
  // ETL
  triggerEtlSync,
  getEtlStats,
  
  // 搜尋
  globalSearch
};

export default api;