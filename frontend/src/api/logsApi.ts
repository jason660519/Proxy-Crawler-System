/**
 * 系統日誌 API 客戶端
 * 
 * 提供系統日誌相關的 API 呼叫方法
 */

import type {
  LogEntry,
  LogFilters,
  PaginatedResponse,
  PaginationParams,
  SortConfig,
  ApiResponse
} from '../types';
import { apiClient } from './client';

/**
 * 日誌 API 類別
 */
class LogsApi {
  private readonly basePath = '/api/logs';

  /**
   * 獲取日誌列表
   */
  async getLogs(params: {
    filters?: LogFilters;
    pagination?: PaginationParams;
    sort?: SortConfig;
  } = {}): Promise<PaginatedResponse<LogEntry>> {
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
    
    const response = await apiClient.get<PaginatedResponse<LogEntry>>(
      `${this.basePath}?${queryParams.toString()}`
    );
    
    return response.data;
  }

  /**
   * 搜尋日誌
   */
  async searchLogs(params: {
    query: string;
    filters?: LogFilters;
    pagination?: PaginationParams;
  }): Promise<PaginatedResponse<LogEntry>> {
    const queryParams = new URLSearchParams();
    queryParams.append('q', params.query);
    
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
    
    const response = await apiClient.get<PaginatedResponse<LogEntry>>(
      `${this.basePath}/search?${queryParams.toString()}`
    );
    
    return response.data;
  }

  /**
   * 獲取日誌統計資料
   */
  async getStatistics(filters?: LogFilters): Promise<any> {
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
    
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/statistics?${queryParams.toString()}`
    );
    
    return response.data.data!;
  }

  /**
   * 導出日誌
   */
  async exportLogs(params: {
    filters?: LogFilters;
    format: 'csv' | 'json' | 'txt';
    dateRange?: {
      start: string;
      end: string;
    };
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('format', params.format);
    
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
    
    // 添加日期範圍
    if (params.dateRange) {
      queryParams.append('startDate', params.dateRange.start);
      queryParams.append('endDate', params.dateRange.end);
    }
    
    const response = await apiClient.post<ApiResponse<any>>(
      `${this.basePath}/export`,
      {},
      {
        params: queryParams
      }
    );
    
    return response.data.data!;
  }

  /**
   * 下載導出的日誌檔案
   */
  async downloadExport(exportId: string): Promise<Blob> {
    const response = await apiClient.get(
      `${this.basePath}/export/${exportId}/download`,
      {
        responseType: 'blob'
      }
    );
    
    return response.data;
  }

  /**
   * 獲取日誌級別統計
   */
  async getLevelStatistics(filters?: LogFilters): Promise<{
    debug: number;
    info: number;
    warning: number;
    error: number;
    critical: number;
  }> {
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
    
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/statistics/levels?${queryParams.toString()}`
    );
    
    return response.data.data!;
  }

  /**
   * 獲取日誌趨勢資料
   */
  async getTrends(params: {
    period: 'hour' | 'day' | 'week' | 'month';
    startDate: string;
    endDate: string;
    filters?: LogFilters;
  }): Promise<Array<{
    timestamp: string;
    count: number;
    levels: {
      debug: number;
      info: number;
      warning: number;
      error: number;
      critical: number;
    };
  }>> {
    const queryParams = new URLSearchParams();
    queryParams.append('period', params.period);
    queryParams.append('startDate', params.startDate);
    queryParams.append('endDate', params.endDate);
    
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
    
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/trends?${queryParams.toString()}`
    );
    
    return response.data.data!;
  }

  /**
   * 清除日誌（管理員功能）
   */
  async clearLogs(filters?: LogFilters): Promise<{
    deletedCount: number;
  }> {
    const response = await apiClient.delete<ApiResponse<any>>(
      `${this.basePath}/clear`,
      {
        data: filters
      }
    );
    
    return response.data.data!;
  }

  /**
   * 獲取日誌配置
   */
  async getLogConfig(): Promise<{
    levels: string[];
    sources: string[];
    retentionDays: number;
    maxFileSize: number;
  }> {
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/config`
    );
    
    return response.data.data!;
  }

  /**
   * 更新日誌配置
   */
  async updateLogConfig(config: {
    retentionDays?: number;
    maxFileSize?: number;
    enabledLevels?: string[];
  }): Promise<void> {
    await apiClient.put(
      `${this.basePath}/config`,
      config
    );
  }

  /**
   * 獲取即時日誌流 WebSocket URL
   */
  getStreamUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}${this.basePath}/stream`;
  }

  /**
   * 測試日誌系統
   */
  async testLogging(): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.post<ApiResponse<any>>(
      `${this.basePath}/test`
    );
    
    return response.data.data!;
  }
}

// 導出單例實例
export const logsApi = new LogsApi();
export default logsApi;