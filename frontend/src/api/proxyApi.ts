/**
 * 代理管理 API 客戶端
 * 
 * 提供代理管理相關的 API 呼叫方法
 */

import type {
  ProxyNode,
  ProxyFilters,
  ProxyTestResult,
  BulkOperationResult,
  PaginatedResponse,
  PaginationParams,
  SortConfig,
  ApiResponse
} from '../types';
import { apiClient } from './client';

/**
 * 代理 API 類別
 */
class ProxyApi {
  private readonly basePath = '/api/proxies';

  /**
   * 獲取代理列表
   */
  async getProxies(params: {
    filters?: ProxyFilters;
    pagination?: PaginationParams;
    sort?: SortConfig;
  } = {}): Promise<PaginatedResponse<ProxyNode>> {
    const queryParams = new URLSearchParams();
    
    // 添加篩選參數
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, v.toString()));
          } else {
            queryParams.append(key, value.toString());
          }
        }
      });
    }
    
    // 添加分頁參數
    if (params.pagination) {
      queryParams.append('page', params.pagination.page?.toString() || '1');
      queryParams.append('limit', params.pagination.size?.toString() || '20');
    }
    
    // 添加排序參數
    if (params.sort) {
      queryParams.append('sortBy', params.sort.field);
      queryParams.append('sortOrder', params.sort.direction);
    }
    
    const response = await apiClient.get<PaginatedResponse<ProxyNode>>(
      `${this.basePath}?${queryParams.toString()}`
    );
    
    return response.data;
  }

  /**
   * 獲取單個代理詳情
   */
  async getProxy(id: string): Promise<ProxyNode> {
    const response = await apiClient.get<ApiResponse<ProxyNode>>(
      `${this.basePath}/${id}`
    );
    
    return response.data.data!;
  }

  /**
   * 建立新代理
   */
  async createProxy(proxyData: Partial<ProxyNode>): Promise<ProxyNode> {
    const response = await apiClient.post<ApiResponse<ProxyNode>>(
      this.basePath,
      proxyData
    );
    
    return response.data.data!;
  }

  /**
   * 更新代理
   */
  async updateProxy(id: string, proxyData: Partial<ProxyNode>): Promise<ProxyNode> {
    const response = await apiClient.put<ApiResponse<ProxyNode>>(
      `${this.basePath}/${id}`,
      proxyData
    );
    
    return response.data.data!;
  }

  /**
   * 刪除代理
   */
  async deleteProxy(id: string): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  /**
   * 測試代理連接
   */
  async testProxy(id: string): Promise<ProxyTestResult> {
    const response = await apiClient.post<ApiResponse<ProxyTestResult>>(
      `${this.basePath}/${id}/test`
    );
    
    return response.data.data!;
  }

  /**
   * 批量測試代理
   */
  async testProxies(ids: string[]): Promise<BulkOperationResult> {
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.basePath}/test/batch`,
      { proxy_ids: ids }
    );
    
    return response.data.data!;
  }

  /**
   * 批量操作代理
   */
  async bulkOperation(operation: string, ids: string[]): Promise<BulkOperationResult> {
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.basePath}/bulk`,
      { 
        operation,
        proxy_ids: ids 
      }
    );
    
    return response.data.data!;
  }

  /**
   * 獲取代理統計資料
   */
  async getStatistics(): Promise<{
    total: number;
    active: number;
    inactive: number;
    error: number;
    averageResponseTime: number;
  }> {
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/statistics`
    );
    
    return response.data.data!;
  }

  /**
   * 匯入代理列表
   */
  async importProxies(file: File): Promise<BulkOperationResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.basePath}/import`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    
    return response.data.data!;
}

  /**
   * 匯出代理列表
   */
  async exportProxies(filters?: ProxyFilters): Promise<Blob> {
    const queryParams = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, v.toString()));
          } else {
            queryParams.append(key, value.toString());
          }
        }
      });
    }
    
    const response = await apiClient.get(
      `${this.basePath}/export?${queryParams.toString()}`,
      {
        responseType: 'blob'
      }
    );
    
    return response.data;
  }
}

// 導出單例實例
export const proxyApi = new ProxyApi();
export default proxyApi;