/**
 * 任務佇列 API 客戶端
 * 
 * 提供任務佇列相關的 API 呼叫方法
 */

import type { 
  Task, 
  TaskFilters, 
  TaskExecutionResult,
  BulkOperationResult,
  PaginatedResponse,
  PaginationParams,
  SortConfig,
  ApiResponse
} from '../types';
import { apiClient } from './client';

/**
 * 任務 API 類別
 */
class TaskApi {
  private readonly basePath = '/api/tasks';

  /**
   * 獲取任務列表
   */
  async getTasks(params: {
    filters?: TaskFilters;
    pagination?: PaginationParams;
    sort?: SortConfig;
  } = {}): Promise<PaginatedResponse<Task>> {
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
    
    const response = await apiClient.get<PaginatedResponse<Task>>(
      `${this.basePath}?${queryParams.toString()}`
    );
    
    return response.data;
  }

  /**
   * 獲取單個任務詳情
   */
  async getTask(id: string): Promise<Task> {
    const response = await apiClient.get<ApiResponse<Task>>(
      `${this.basePath}/${id}`
    );
    
    return response.data.data!;
  }

  /**
   * 建立新任務
   */
  async createTask(taskData: Partial<Task>): Promise<Task> {
    const response = await apiClient.post<ApiResponse<Task>>(
      this.basePath,
      taskData
    );
    
    return response.data.data!;
  }

  /**
   * 更新任務
   */
  async updateTask(id: string, taskData: Partial<Task>): Promise<Task> {
    const response = await apiClient.put<ApiResponse<Task>>(
      `${this.basePath}/${id}`,
      taskData
    );
    
    return response.data.data!;
  }

  /**
   * 刪除任務
   */
  async deleteTask(id: string): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  /**
   * 執行任務操作
   */
  async executeOperation(
    id: string, 
    operation: 'start' | 'pause' | 'resume' | 'stop' | 'restart'
  ): Promise<TaskExecutionResult> {
    const response = await apiClient.post<ApiResponse<TaskExecutionResult>>(
      `${this.basePath}/${id}/${operation}`
    );
    
    return response.data.data!;
  }

  /**
   * 批量操作任務
   */
  async bulkOperation(operation: string, ids: string[]): Promise<BulkOperationResult> {
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.basePath}/bulk`,
      { 
        operation,
        task_ids: ids 
      }
    );
    
    return response.data.data!;
  }

  /**
   * 獲取任務執行日誌
   */
  async getTaskLogs(id: string, params?: {
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<{
    timestamp: string;
    level: string;
    message: string;
    details?: any;
  }>> {
    const queryParams = new URLSearchParams();
    
    if (params?.page) {
      queryParams.append('page', params.page.toString());
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    
    const response = await apiClient.get<PaginatedResponse<any>>(
      `${this.basePath}/${id}/logs?${queryParams.toString()}`
    );
    
    return response.data;
  }

  /**
   * 獲取任務統計資料
   */
  async getStatistics(): Promise<{
    total: number;
    pending: number;
    running: number;
    completed: number;
    failed: number;
    paused: number;
  }> {
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/statistics`
    );
    
    return response.data.data!;
  }

  /**
   * 獲取任務執行歷史
   */
  async getTaskHistory(id: string): Promise<{
    executions: Array<{
      id: string;
      startTime: string;
      endTime?: string;
      status: string;
      result?: any;
      error?: string;
    }>;
  }> {
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/${id}/history`
    );
    
    return response.data.data!;
  }

  /**
   * 複製任務
   */
  async cloneTask(id: string, newName?: string): Promise<Task> {
    const response = await apiClient.post<ApiResponse<Task>>(
      `${this.basePath}/${id}/clone`,
      { name: newName }
    );
    
    return response.data.data!;
  }

  /**
   * 匯出任務配置
   */
  async exportTasks(ids?: string[]): Promise<Blob> {
    const queryParams = new URLSearchParams();
    
    if (ids && ids.length > 0) {
      ids.forEach(id => queryParams.append('ids', id));
    }
    
    const response = await apiClient.get(
      `${this.basePath}/export?${queryParams.toString()}`,
      {
        responseType: 'blob'
      }
    );
    
    return response.data;
  }

  /**
   * 匯入任務配置
   */
  async importTasks(file: File): Promise<BulkOperationResult> {
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
   * 獲取任務模板
   */
  async getTemplates(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    config: any;
  }>> {
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.basePath}/templates`
    );
    
    return response.data.data!;
  }

  /**
   * 從模板建立任務
   */
  async createFromTemplate(templateId: string, taskData: Partial<Task>): Promise<Task> {
    const response = await apiClient.post<ApiResponse<Task>>(
      `${this.basePath}/templates/${templateId}/create`,
      taskData
    );
    
    return response.data.data!;
  }
}

// 導出單例實例
export const taskApi = new TaskApi();
export default taskApi;