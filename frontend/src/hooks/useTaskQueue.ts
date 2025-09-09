/**
 * 任務佇列管理 Hook
 * 
 * 提供任務佇列相關的狀態管理和操作方法
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import type { 
  Task, 
  TaskFilters, 
  TaskQueueState,
  TaskExecutionResult,
  BulkOperationResult,
  PaginationParams,
  SortConfig
} from '../types';
import { taskQueueService } from '../services/taskQueue';

/**
 * 任務佇列管理 Hook
 * 
 * @returns 任務佇列狀態和操作方法
 */
export const useTaskQueue = () => {
  const [state, setState] = useState<TaskQueueState>({
    tasks: [],
    selectedTasks: [],
    filters: {
      status: undefined,
      type: undefined,
      search: undefined,
      dateRange: undefined,
      priority: undefined
    },
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true
    },
    loading: false,
    error: undefined,
    totalCount: 0
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * 載入任務列表
   */
  const loadTasks = useCallback(async (params: {
    filters?: TaskFilters;
    pagination?: PaginationParams;
    sort?: SortConfig;
  }) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const response = await taskQueueService.getTasks(
        params.pagination || { page: 1, size: 20 },
        params.filters || {}
      );
      setState(prev => ({
        ...prev,
        tasks: response.data || [],
        totalCount: response.pagination?.total || 0,
        loading: false
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '載入任務列表失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 建立新任務
   */
  const createTask = useCallback(async (taskData: Partial<Task>) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const newTask = await taskQueueService.createTask(taskData as any);
      setState(prev => ({
        ...prev,
        tasks: [newTask, ...prev.tasks],
        totalCount: prev.totalCount + 1,
        loading: false
      }));
      return newTask;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '建立任務失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 更新任務
   */
  const updateTask = useCallback(async (id: string, taskData: Partial<Task>) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const updatedTask = await taskQueueService.updateTask(id, taskData as any);
      setState(prev => ({
        ...prev,
        tasks: prev.tasks.map(task => 
          task.id === id ? updatedTask : task
        ),
        loading: false
      }));
      return updatedTask;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '更新任務失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 刪除任務
   */
  const deleteTask = useCallback(async (id: string) => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      await taskQueueService.deleteTask(id);
      setState(prev => ({
        ...prev,
        tasks: prev.tasks.filter(task => task.id !== id),
        totalCount: prev.totalCount - 1,
        loading: false
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '刪除任務失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 執行任務操作
   */
  const executeTaskOperation = useCallback(async (
    id: string, 
    operation: 'start' | 'pause' | 'resume' | 'stop' | 'restart'
  ): Promise<TaskExecutionResult> => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      let result: TaskExecutionResult;
      switch (operation) {
        case 'start':
          result = await taskQueueService.startTask(id);
          break;
        case 'pause':
          result = await taskQueueService.pauseTask(id);
          break;
        case 'resume':
          result = await taskQueueService.resumeTask(id);
          break;
        case 'stop':
          result = await taskQueueService.cancelTask(id);
          break;
        case 'restart':
          result = await taskQueueService.retryTask(id);
          break;
        default:
          throw new Error(`不支援的操作: ${operation}`);
      }
      
      // 更新任務狀態
      setState(prev => ({
        ...prev,
        tasks: prev.tasks.map(task => 
          task.id === id ? {
            ...task,
            updatedAt: new Date().toISOString()
          } : task
        ),
        loading: false
      }));
      
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : '執行任務操作失敗'
      }));
      throw error;
    }
  }, []);

  /**
   * 批量操作
   */
  const bulkOperation = useCallback(async (
    operation: string, 
    taskIds: string[]
  ): Promise<BulkOperationResult> => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      let result: BulkOperationResult;
      switch (operation) {
        case 'delete':
          result = await taskQueueService.batchTaskOperation(taskIds, 'delete');
          break;
        case 'start':
          result = await taskQueueService.batchTaskOperation(taskIds, 'start');
          break;
        case 'pause':
          result = await taskQueueService.batchTaskOperation(taskIds, 'pause');
          break;
        case 'resume':
          result = await taskQueueService.batchTaskOperation(taskIds, 'resume');
          break;
        case 'cancel':
          result = await taskQueueService.batchTaskOperation(taskIds, 'cancel');
          break;
        default:
          throw new Error(`不支援的批量操作: ${operation}`);
      }
      
      // 根據操作類型更新狀態
      if (operation === 'delete') {
        setState(prev => ({
          ...prev,
          tasks: prev.tasks.filter(task => !taskIds.includes(task.id)),
          totalCount: prev.totalCount - result.processed,
          loading: false
        }));
      } else {
        // 重新載入列表以獲取最新狀態
        await loadTasks({});
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
  }, [loadTasks]);

  /**
   * 設置選中的任務
   */
  const setSelectedTasks = useCallback((taskIds: string[]) => {
    setState(prev => ({ ...prev, selectedTasks: taskIds }));
  }, []);

  /**
   * 啟用/停用即時更新
   */
  const toggleRealTimeUpdates = useCallback((enabled: boolean) => {
    setState(prev => ({ ...prev, realTimeUpdates: enabled }));
    
    if (enabled) {
      // 每 5 秒更新一次任務狀態
      intervalRef.current = setInterval(() => {
        loadTasks({});
      }, 5000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [loadTasks]);

  /**
   * 清除錯誤
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: undefined }));
  }, []);

  /**
   * 清理副作用
   */
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    state,
    actions: {
      loadTasks,
      createTask,
      updateTask,
      deleteTask,
      executeTaskOperation,
      bulkOperation,
      setSelectedTasks,
      toggleRealTimeUpdates,
      clearError
    }
  };
};

export default useTaskQueue;