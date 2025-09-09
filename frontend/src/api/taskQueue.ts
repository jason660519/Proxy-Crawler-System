import { apiClient } from './client';
import type {
  Task,
  CrawlTask,
  TaskStatus,
  TaskQueryParams,
  TaskExecutionResult,
  BulkOperationResult,
  PaginatedResponse,
  ApiResponse
} from '../types';

/**
 * 任務佇列 API 服務類
 * 提供任務管理相關的 API 操作
 */
export class TaskQueueService {
  private readonly baseUrl = '/api/task-queue';

  /**
   * 獲取任務列表
   * @param params 查詢參數
   * @returns 分頁任務列表
   */
  async getTasks(params?: TaskQueryParams): Promise<PaginatedResponse<Task>> {
    const response = await apiClient.get<PaginatedResponse<Task>>(
      `${this.baseUrl}/tasks`,
      { params }
    );
    return response.data;
  }

  /**
   * 根據 ID 獲取單個任務
   * @param taskId 任務 ID
   * @returns 任務詳情
   */
  async getTask(taskId: string): Promise<Task> {
    const response = await apiClient.get<ApiResponse<Task>>(
      `${this.baseUrl}/tasks/${taskId}`
    );
    return response.data.data!;
  }

  /**
   * 創建新任務
   * @param taskData 任務數據
   * @returns 創建的任務
   */
  async createTask(taskData: Partial<CrawlTask>): Promise<Task> {
    const response = await apiClient.post<ApiResponse<Task>>(
      `${this.baseUrl}/tasks`,
      taskData
    );
    return response.data.data!;
  }

  /**
   * 更新任務
   * @param taskId 任務 ID
   * @param taskData 更新的任務數據
   * @returns 更新後的任務
   */
  async updateTask(taskId: string, taskData: Partial<Task>): Promise<Task> {
    const response = await apiClient.put<ApiResponse<Task>>(
      `${this.baseUrl}/tasks/${taskId}`,
      taskData
    );
    return response.data.data!;
  }

  /**
   * 刪除任務
   * @param taskId 任務 ID
   * @returns 操作結果
   */
  async deleteTask(taskId: string): Promise<boolean> {
    const response = await apiClient.delete<ApiResponse<boolean>>(
      `${this.baseUrl}/tasks/${taskId}`
    );
    return response.data.success;
  }

  /**
   * 批量刪除任務
   * @param taskIds 任務 ID 列表
   * @returns 批量操作結果
   */
  async deleteTasks(taskIds: string[]): Promise<BulkOperationResult> {
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.baseUrl}/tasks/bulk-delete`,
      { task_ids: taskIds }
    );
    return response.data.data!;
  }

  /**
   * 啟動任務
   * @param taskId 任務 ID
   * @returns 操作結果
   */
  async startTask(taskId: string): Promise<TaskExecutionResult> {
    const response = await apiClient.post<ApiResponse<TaskExecutionResult>>(
      `${this.baseUrl}/tasks/${taskId}/start`
    );
    return response.data.data!;
  }

  /**
   * 停止任務
   * @param taskId 任務 ID
   * @returns 操作結果
   */
  async stopTask(taskId: string): Promise<boolean> {
    const response = await apiClient.post<ApiResponse<boolean>>(
      `${this.baseUrl}/tasks/${taskId}/stop`
    );
    return response.data.success;
  }

  /**
   * 重新啟動任務
   * @param taskId 任務 ID
   * @returns 操作結果
   */
  async restartTask(taskId: string): Promise<TaskExecutionResult> {
    const response = await apiClient.post<ApiResponse<TaskExecutionResult>>(
      `${this.baseUrl}/tasks/${taskId}/restart`
    );
    return response.data.data!;
  }

  /**
   * 批量啟動任務
   * @param taskIds 任務 ID 列表
   * @returns 批量操作結果
   */
  async startTasks(taskIds: string[]): Promise<BulkOperationResult> {
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.baseUrl}/tasks/bulk-start`,
      { task_ids: taskIds }
    );
    return response.data.data!;
  }

  /**
   * 批量停止任務
   * @param taskIds 任務 ID 列表
   * @returns 批量操作結果
   */
  async stopTasks(taskIds: string[]): Promise<BulkOperationResult> {
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.baseUrl}/tasks/bulk-stop`,
      { task_ids: taskIds }
    );
    return response.data.data!;
  }

  /**
   * 獲取任務統計信息
   * @returns 統計數據
   */
  async getStatistics(): Promise<{
    total: number;
    pending: number;
    running: number;
    completed: number;
    failed: number;
    cancelled: number;
  }> {
    const response = await apiClient.get<ApiResponse<{
      total: number;
      pending: number;
      running: number;
      completed: number;
      failed: number;
      cancelled: number;
    }>>(`${this.baseUrl}/statistics`);
    return response.data.data!;
  }

  /**
   * 獲取任務執行歷史
   * @param taskId 任務 ID
   * @param params 查詢參數
   * @returns 執行歷史列表
   */
  async getTaskHistory(
    taskId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<TaskExecutionResult[]> {
    const response = await apiClient.get<ApiResponse<TaskExecutionResult[]>>(
      `${this.baseUrl}/tasks/${taskId}/history`,
      { params }
    );
    return response.data.data!;
  }

  /**
   * 清理已完成的任務
   * @param olderThan 清理多久之前的任務（ISO 日期字串）
   * @returns 清理結果
   */
  async cleanupTasks(olderThan?: string): Promise<BulkOperationResult> {
    const response = await apiClient.post<ApiResponse<BulkOperationResult>>(
      `${this.baseUrl}/cleanup`,
      { older_than: olderThan }
    );
    return response.data.data!;
  }

  /**
   * 匯出任務數據
   * @param params 匯出參數
   * @returns 匯出檔案的下載 URL
   */
  async exportTasks(params?: {
    format?: 'csv' | 'json' | 'xlsx';
    status?: TaskStatus[];
    dateRange?: [string, string];
  }): Promise<string> {
    const response = await apiClient.post<ApiResponse<{ download_url: string }>>(
      `${this.baseUrl}/export`,
      params
    );
    return response.data.data!.download_url;
  }

  /**
   * 匯入任務數據
   * @param file 匯入檔案
   * @returns 匯入結果
   */
  async importTasks(file: File): Promise<BulkOperationResult> {
    const response = await apiClient.upload<ApiResponse<BulkOperationResult>>(
      `${this.baseUrl}/import`,
      file
    );
    return response.data.data!;
  }
}

// 創建單例實例
export const taskQueueService = new TaskQueueService();
export default taskQueueService;