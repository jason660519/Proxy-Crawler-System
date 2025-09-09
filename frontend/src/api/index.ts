/**
 * API 模組統一導出
 * 
 * 提供所有 API 客戶端的統一入口
 */

// 基礎客戶端
export { apiClient } from './client';
export type { ApiError } from './client';
export type { ApiError as ApiErrorType } from './client';

// API 客戶端
import { apiClient } from './client';
import { proxyApi } from './proxyApi';
import { taskApi } from './taskApi';
import { logsApi } from './logsApi';

export { proxyApi, taskApi, logsApi };

// 預設導出
export default {
  client: apiClient,
  proxy: proxyApi,
  task: taskApi,
  logs: logsApi
};