/**
 * API 相關類型定義
 * 定義與後端 API 交互的類型
 */

import type {
  ProxyNode,
  ProxyStats,
  ProxyTestResult,
  Task,
  TaskStats,
  CrawlerSource,
  User,
  SystemStatus,
  Alert,
  PaginatedResponse,
  PaginationParams,
  FilterParams
} from './index';

// ============================================================================
// API 基礎類型
// ============================================================================

/**
 * HTTP 方法類型
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/**
 * API 錯誤類型
 */
export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  path?: string;
  method?: HttpMethod;
}

/**
 * API 請求配置接口
 */
export interface ApiRequestConfig {
  method?: HttpMethod;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
  timeout?: number;
  retries?: number;
  cache?: boolean;
  signal?: AbortSignal;
}

/**
 * API 響應接口
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: ApiError;
  timestamp: string;
  requestId?: string;
}

/**
 * API 端點配置接口
 */
export interface ApiEndpoint {
  url: string;
  method: HttpMethod;
  description?: string;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  cache?: boolean;
  timeout?: number;
}

// ============================================================================
// 代理 API 類型
// ============================================================================

/**
 * 代理列表請求參數
 */
export interface ProxyListParams extends PaginationParams, FilterParams {
  protocol?: string;
  anonymity?: string;
  status?: string;
  country?: string;
  minSpeed?: number;
  maxSpeed?: number;
  tags?: string[];
}

/**
 * 代理列表響應
 */
export type ProxyListResponse = PaginatedResponse<ProxyNode>;

/**
 * 代理創建請求
 */
export interface CreateProxyRequest {
  ip: string;
  port: number;
  protocol: string;
  anonymity?: string;
  username?: string;
  password?: string;
  tags?: string[];
  notes?: string;
}

/**
 * 代理更新請求
 */
export interface UpdateProxyRequest extends Partial<CreateProxyRequest> {
  id: string;
}

/**
 * 代理測試請求
 */
export interface TestProxyRequest {
  proxyIds: string[];
  testUrl?: string;
  timeout?: number;
  concurrent?: number;
}

/**
 * 代理測試響應
 */
export interface TestProxyResponse {
  results: ProxyTestResult[];
  summary: {
    total: number;
    success: number;
    failed: number;
    averageSpeed: number;
  };
}

/**
 * 代理批量操作請求
 */
export interface ProxyBatchRequest {
  action: 'delete' | 'test' | 'export' | 'tag' | 'untag';
  proxyIds: string[];
  params?: {
    tags?: string[];
    format?: 'json' | 'csv' | 'txt';
    testUrl?: string;
    timeout?: number;
  };
}

/**
 * 代理導入請求
 */
export interface ImportProxyRequest {
  format: 'json' | 'csv' | 'txt';
  data: string;
  options?: {
    skipDuplicates?: boolean;
    validateOnImport?: boolean;
    defaultTags?: string[];
  };
}

/**
 * 代理導入響應
 */
export interface ImportProxyResponse {
  imported: number;
  skipped: number;
  failed: number;
  errors?: string[];
  duplicates?: string[];
}

/**
 * 代理統計響應
 */
export type ProxyStatsResponse = ProxyStats;

// ============================================================================
// 任務 API 類型
// ============================================================================

/**
 * 任務列表請求參數
 */
export interface TaskListParams extends PaginationParams, FilterParams {
  type?: string;
  status?: string;
  priority?: string;
  dateFrom?: string;
  dateTo?: string;
}

/**
 * 任務列表響應
 */
export type TaskListResponse = PaginatedResponse<Task>;

/**
 * 任務創建請求
 */
export interface CreateTaskRequest {
  name: string;
  type: string;
  priority?: string;
  config?: Record<string, any>;
  scheduledAt?: string;
}

/**
 * 任務更新請求
 */
export interface UpdateTaskRequest extends Partial<CreateTaskRequest> {
  id: string;
}

/**
 * 任務執行請求
 */
export interface ExecuteTaskRequest {
  taskId: string;
  params?: Record<string, any>;
}

/**
 * 任務統計響應
 */
export type TaskStatsResponse = TaskStats;

// ============================================================================
// 爬蟲 API 類型
// ============================================================================

/**
 * 爬蟲來源列表響應
 */
export type CrawlerSourceListResponse = CrawlerSource[];

/**
 * 爬蟲來源創建請求
 */
export interface CreateCrawlerSourceRequest {
  name: string;
  url: string;
  enabled?: boolean;
  interval?: number;
  config?: Record<string, any>;
}

/**
 * 爬蟲來源更新請求
 */
export interface UpdateCrawlerSourceRequest extends Partial<CreateCrawlerSourceRequest> {
  id: string;
}

/**
 * 爬蟲執行請求
 */
export interface ExecuteCrawlerRequest {
  sourceId: string;
  options?: {
    immediate?: boolean;
    testMode?: boolean;
    maxProxies?: number;
  };
}

/**
 * 爬蟲執行響應
 */
export interface ExecuteCrawlerResponse {
  taskId: string;
  message: string;
  estimatedDuration?: number;
}

// ============================================================================
// 用戶 API 類型
// ============================================================================

/**
 * 用戶登入請求
 */
export interface LoginRequest {
  username: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * 用戶登入響應
 */
export interface LoginResponse {
  user: User;
  token: string;
  refreshToken?: string;
  expiresIn: number;
}

/**
 * 用戶註冊請求
 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

/**
 * 用戶資料更新請求
 */
export interface UpdateUserRequest {
  username?: string;
  email?: string;
  avatar?: string;
  preferences?: any;
}

/**
 * 密碼更改請求
 */
export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

/**
 * 密碼重設請求
 */
export interface ResetPasswordRequest {
  email: string;
}

/**
 * 用戶列表請求參數
 */
export interface UserListParams extends PaginationParams, FilterParams {
  role?: string;
  status?: string;
}

/**
 * 用戶列表響應
 */
export type UserListResponse = PaginatedResponse<User>;

// ============================================================================
// 系統 API 類型
// ============================================================================

/**
 * 系統狀態響應
 */
export type SystemStatusResponse = SystemStatus;

/**
 * 系統配置更新請求
 */
export interface UpdateSystemConfigRequest {
  section: string;
  config: Record<string, any>;
}

/**
 * 系統日誌請求參數
 */
export interface SystemLogParams extends PaginationParams {
  level?: string;
  source?: string;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

/**
 * 系統日誌項目
 */
export interface SystemLogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  source: string;
  message: string;
  data?: any;
}

/**
 * 系統日誌響應
 */
export type SystemLogResponse = PaginatedResponse<SystemLogEntry>;

/**
 * 系統備份請求
 */
export interface CreateBackupRequest {
  name?: string;
  includeData?: boolean;
  includeConfig?: boolean;
  compression?: boolean;
}

/**
 * 系統備份響應
 */
export interface CreateBackupResponse {
  backupId: string;
  filename: string;
  size: number;
  createdAt: string;
}

/**
 * 系統還原請求
 */
export interface RestoreBackupRequest {
  backupId: string;
  options?: {
    restoreData?: boolean;
    restoreConfig?: boolean;
    overwrite?: boolean;
  };
}

// ============================================================================
// 監控 API 類型
// ============================================================================

/**
 * 警報列表請求參數
 */
export interface AlertListParams extends PaginationParams, FilterParams {
  level?: string;
  source?: string;
  acknowledged?: boolean;
  resolved?: boolean;
}

/**
 * 警報列表響應
 */
export type AlertListResponse = PaginatedResponse<Alert>;

/**
 * 警報確認請求
 */
export interface AcknowledgeAlertRequest {
  alertIds: string[];
  note?: string;
}

/**
 * 警報解決請求
 */
export interface ResolveAlertRequest {
  alertIds: string[];
  note?: string;
}

/**
 * 指標查詢請求
 */
export interface MetricQueryRequest {
  metric: string;
  timeRange: {
    from: string;
    to: string;
  };
  interval?: string;
  aggregation?: 'avg' | 'sum' | 'min' | 'max' | 'count';
  groupBy?: string[];
  filters?: Record<string, any>;
}

/**
 * 指標數據點
 */
export interface MetricDataPoint {
  timestamp: string;
  value: number;
  tags?: Record<string, string>;
}

/**
 * 指標查詢響應
 */
export interface MetricQueryResponse {
  metric: string;
  data: MetricDataPoint[];
  summary?: {
    min: number;
    max: number;
    avg: number;
    sum: number;
    count: number;
  };
}

// ============================================================================
// WebSocket API 類型
// ============================================================================

/**
 * WebSocket 消息類型
 */
export type WebSocketMessageType = 
  | 'ping'
  | 'pong'
  | 'subscribe'
  | 'unsubscribe'
  | 'notification'
  | 'update'
  | 'error';

/**
 * WebSocket 消息接口
 */
export interface WebSocketMessage<T = any> {
  type: WebSocketMessageType;
  id?: string;
  channel?: string;
  data?: T;
  timestamp: string;
}

/**
 * WebSocket 訂閱請求
 */
export interface WebSocketSubscribeRequest {
  channels: string[];
  filters?: Record<string, any>;
}

/**
 * WebSocket 通知消息
 */
export interface WebSocketNotification {
  type: 'task_update' | 'proxy_status' | 'system_alert' | 'user_action';
  data: any;
  timestamp: string;
}

// ============================================================================
// 文件上傳 API 類型
// ============================================================================

/**
 * 文件上傳請求
 */
export interface FileUploadRequest {
  file: File;
  type?: 'avatar' | 'backup' | 'import' | 'config';
  metadata?: Record<string, any>;
}

/**
 * 文件上傳響應
 */
export interface FileUploadResponse {
  fileId: string;
  filename: string;
  size: number;
  type: string;
  url: string;
  uploadedAt: string;
}

/**
 * 文件下載請求
 */
export interface FileDownloadRequest {
  fileId: string;
  filename?: string;
}

// ============================================================================
// 搜索 API 類型
// ============================================================================

/**
 * 搜索請求
 */
export interface SearchRequest {
  query: string;
  type?: 'proxy' | 'task' | 'user' | 'log' | 'all';
  filters?: Record<string, any>;
  limit?: number;
  offset?: number;
}

/**
 * 搜索結果項目
 */
export interface SearchResultItem {
  id: string;
  type: string;
  title: string;
  description?: string;
  url?: string;
  score: number;
  highlight?: Record<string, string[]>;
}

/**
 * 搜索響應
 */
export interface SearchResponse {
  query: string;
  total: number;
  took: number;
  results: SearchResultItem[];
  aggregations?: Record<string, any>;
}

// ============================================================================
// 導出 API 類型
// ============================================================================

/**
 * 導出請求
 */
export interface ExportRequest {
  type: 'proxy' | 'task' | 'log' | 'config';
  format: 'json' | 'csv' | 'xlsx' | 'pdf';
  filters?: Record<string, any>;
  fields?: string[];
  options?: {
    includeHeaders?: boolean;
    dateFormat?: string;
    timezone?: string;
  };
}

/**
 * 導出響應
 */
export interface ExportResponse {
  exportId: string;
  filename: string;
  format: string;
  size?: number;
  downloadUrl: string;
  expiresAt: string;
}

// ============================================================================
// API 客戶端類型
// ============================================================================

/**
 * API 客戶端配置
 */
export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  headers?: Record<string, string>;
  interceptors?: {
    request?: (config: ApiRequestConfig) => ApiRequestConfig;
    response?: (response: any) => any;
    error?: (error: any) => any;
  };
}

/**
 * API 客戶端接口
 */
export interface ApiClient {
  get<T = any>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>>;
  post<T = any>(url: string, data?: any, config?: ApiRequestConfig): Promise<ApiResponse<T>>;
  put<T = any>(url: string, data?: any, config?: ApiRequestConfig): Promise<ApiResponse<T>>;
  patch<T = any>(url: string, data?: any, config?: ApiRequestConfig): Promise<ApiResponse<T>>;
  delete<T = any>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>>;
  upload<T = any>(url: string, file: File, config?: ApiRequestConfig): Promise<ApiResponse<T>>;
  download(url: string, config?: ApiRequestConfig): Promise<Blob>;
}

// ============================================================================
// React Query 類型
// ============================================================================

/**
 * 查詢鍵工廠類型
 */
export interface QueryKeyFactory {
  all: () => string[];
  lists: () => string[];
  list: (filters?: any) => string[];
  details: () => string[];
  detail: (id: string) => string[];
}

/**
 * 變更選項類型
 */
export interface MutationOptions<TData = any, TError = any, TVariables = any> {
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: TError, variables: TVariables) => void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables) => void;
}

/**
 * 查詢選項類型
 */
export interface QueryOptions<TData = any, TError = any> {
  enabled?: boolean;
  staleTime?: number;
  cacheTime?: number;
  refetchOnWindowFocus?: boolean;
  refetchOnMount?: boolean;
  retry?: boolean | number;
  onSuccess?: (data: TData) => void;
  onError?: (error: TError) => void;
}