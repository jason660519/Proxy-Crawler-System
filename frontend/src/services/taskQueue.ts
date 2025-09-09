/**
 * 任務佇列服務模組
 * 
 * 提供任務管理的完整 API 介面，包括：
 * - 任務 CRUD 操作
 * - 任務狀態管理
 * - 批量操作
 * - 統計資料獲取
 */

import { http } from './http';
import type {
  Task,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskFilters,
  TaskStatistics,
  PaginatedResponse,
  PaginationParams,
  ApiResponse
} from '../types';

/**
 * 任務操作類型
 */
export type TaskAction = 'start' | 'pause' | 'resume' | 'cancel' | 'retry' | 'delete';

/**
 * 佇列操作類型
 */
export type QueueAction = 'start_all' | 'pause_all' | 'clear_completed' | 'clear_failed' | 'clear_all';

/**
 * 任務操作請求
 */
export interface TaskActionRequest {
  action: TaskAction;
  reason?: string;
  options?: Record<string, any>;
}

/**
 * 批量任務操作請求
 */
export interface BatchTaskRequest {
  task_ids: string[];
  action: TaskAction;
  reason?: string;
}

/**
 * 佇列操作請求
 */
export interface QueueOperationRequest {
  action: QueueAction;
  filters?: Record<string, any>;
  reason?: string;
}

/**
 * 任務日誌項目
 */
export interface TaskLogEntry {
  timestamp: string;
  level: string;
  message: string;
  details?: Record<string, any>;
}

/**
 * 佇列狀態
 */
export interface QueueStatus {
  is_running: boolean;
  worker_count: number;
  pending_tasks: number;
  running_tasks: number;
  max_concurrent: number;
  throughput: number;
  average_wait_time?: number;
  last_processed?: string;
}

/**
 * 任務模板
 */
export interface TaskTemplate {
  id: string;
  name: string;
  task_type: string;
  config: Record<string, any>;
}

/**
 * 任務佇列服務類別
 */
export class TaskQueueService {
  private readonly baseUrl = '/api/tasks';

  /**
   * 獲取任務列表（分頁）
   */
  async getTasks(
    pagination: PaginationParams = { page: 1, size: 20 },
    filters: Partial<TaskFilters> = {}
  ): Promise<PaginatedResponse<Task>> {
    const params = new URLSearchParams();
    
    // 分頁參數
    if (pagination.page !== undefined) {
      params.append('page', pagination.page.toString());
    }
    if (pagination.size) {
      params.append('size', pagination.size.toString());
    }
    if (pagination.sortBy) {
      params.append('sort_by', pagination.sortBy);
    }
    if (pagination.sortOrder) {
      params.append('sort_order', pagination.sortOrder);
    }
    // 篩選參數
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v.toString()));
        } else {
          params.append(key, value.toString());
        }
      }
    });
    
    const response = await http.get<PaginatedResponse<Task>>(
      `${this.baseUrl}?${params.toString()}`
    );
    return response.data;
  }

  /**
   * 獲取單個任務詳情
   */
  async getTask(id: string): Promise<Task> {
    const response = await http.get<ApiResponse<Task>>(`${this.baseUrl}/${id}`);
    if (!response.data.data) {
      throw new Error('獲取任務失敗：無效的響應數據');
    }
    return response.data.data;
  }

  /**
   * 建立新任務
   */
  async createTask(request: TaskCreateRequest): Promise<Task> {
    const response = await http.post<ApiResponse<Task>>(this.baseUrl, request);
    if (!response.data.data) {
      throw new Error('創建任務失敗：無效的響應數據');
    }
    return response.data.data;
  }

  /**
   * 更新任務
   */
  async updateTask(taskId: string, request: TaskUpdateRequest): Promise<Task> {
    const response = await http.put<ApiResponse<Task>>(`${this.baseUrl}/${taskId}`, request);
    if (!response.data.data) {
      throw new Error('更新任務失敗：回應資料為空');
    }
    return response.data.data;
  }

  /**
   * 刪除任務
   */
  async deleteTask(taskId: string, force: boolean = false): Promise<void> {
    const params = force ? '?force=true' : '';
    await http.delete(`${this.baseUrl}/${taskId}${params}`);
  }

  /**
   * 執行任務操作
   */
  async executeTaskOperation(
    taskId: string, 
    action: TaskAction, 
    reason?: string,
    options?: Record<string, any>
  ): Promise<any> {
    const request: TaskActionRequest = { action, reason, options };
    const response = await http.post<ApiResponse<any>>(
      `${this.baseUrl}/${taskId}/action`, 
      request
    );
    return response.data.data;
  }

  /**
   * 批量任務操作
   */
  async batchTaskOperation(
    taskIds: string[], 
    action: TaskAction, 
    reason?: string
  ): Promise<any> {
    const request: BatchTaskRequest = { task_ids: taskIds, action, reason };
    const response = await http.post<ApiResponse<any>>(
      `${this.baseUrl}/batch`, 
      request
    );
    return response.data.data;
  }

  /**
   * 獲取任務統計資料
   */
  async getStatistics(): Promise<TaskStatistics> {
    const response = await http.get<ApiResponse<TaskStatistics>>(`${this.baseUrl}/statistics`);
    if (!response.data.data) {
      throw new Error('獲取任務統計失敗：回應資料為空');
    }
    return response.data.data;
  }

  /**
   * 獲取任務日誌
   */
  async getTaskLogs(
    taskId: string, 
    limit: number = 100, 
    level?: string
  ): Promise<TaskLogEntry[]> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (level) {
      params.append('level', level);
    }
    
    const response = await http.get<ApiResponse<TaskLogEntry[]>>(
      `${this.baseUrl}/${taskId}/logs?${params.toString()}`
    );
    return response.data.data || [];
  }

  /**
   * 獲取佇列狀態
   */
  async getQueueStatus(): Promise<QueueStatus> {
    const response = await http.get<ApiResponse<QueueStatus>>(`${this.baseUrl}/queue/status`);
    if (!response.data.data) {
      throw new Error('獲取佇列狀態失敗：回應資料為空');
    }
    return response.data.data;
  }

  /**
   * 執行佇列操作
   */
  async executeQueueOperation(
    action: QueueAction, 
    filters?: Record<string, any>, 
    reason?: string
  ): Promise<any> {
    const request: QueueOperationRequest = { action, filters, reason };
    const response = await http.post<ApiResponse<any>>(
      `${this.baseUrl}/queue/operation`, 
      request
    );
    return response.data.data;
  }

  /**
   * 獲取可用任務類型
   */
  async getTaskTypes(): Promise<string[]> {
    const response = await http.get<ApiResponse<string[]>>(`${this.baseUrl}/types`);
    return response.data.data || [];
  }

  /**
   * 獲取任務模板
   */
  async getTaskTemplates(taskType?: string): Promise<TaskTemplate[]> {
    const params = taskType ? `?task_type=${taskType}` : '';
    const response = await http.get<ApiResponse<TaskTemplate[]>>(
      `${this.baseUrl}/templates${params}`
    );
    return response.data.data || [];
  }

  // ============= 便利方法 =============

  /**
   * 啟動任務
   */
  async startTask(taskId: string, reason?: string): Promise<any> {
    return this.executeTaskOperation(taskId, 'start', reason);
  }

  /**
   * 暫停任務
   */
  async pauseTask(taskId: string, reason?: string): Promise<any> {
    return this.executeTaskOperation(taskId, 'pause', reason);
  }

  /**
   * 恢復任務
   */
  async resumeTask(taskId: string, reason?: string): Promise<any> {
    return this.executeTaskOperation(taskId, 'resume', reason);
  }

  /**
   * 取消任務
   */
  async cancelTask(taskId: string, reason?: string): Promise<any> {
    return this.executeTaskOperation(taskId, 'cancel', reason);
  }

  /**
   * 重試任務
   */
  async retryTask(taskId: string, reason?: string): Promise<any> {
    return this.executeTaskOperation(taskId, 'retry', reason);
  }

  /**
   * 啟動所有佇列處理
   */
  async startAllQueues(reason?: string): Promise<any> {
    return this.executeQueueOperation('start_all', undefined, reason);
  }

  /**
   * 暫停所有佇列處理
   */
  async pauseAllQueues(reason?: string): Promise<any> {
    return this.executeQueueOperation('pause_all', undefined, reason);
  }

  /**
   * 清理已完成任務
   */
  async clearCompletedTasks(reason?: string): Promise<any> {
    return this.executeQueueOperation('clear_completed', undefined, reason);
  }

  /**
   * 清理失敗任務
   */
  async clearFailedTasks(reason?: string): Promise<any> {
    return this.executeQueueOperation('clear_failed', undefined, reason);
  }

  /**
   * 清理所有任務
   */
  async clearAllTasks(reason?: string): Promise<any> {
    return this.executeQueueOperation('clear_all', undefined, reason);
  }
}

// 匯出服務實例
export const taskQueueService = new TaskQueueService();

// 預設匯出
export default taskQueueService;