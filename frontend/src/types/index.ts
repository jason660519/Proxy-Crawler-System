/**
 * 代理爬蟲管理系統 - TypeScript 類型定義
 * 定義系統中使用的所有資料結構和介面
 */

// ============= 基礎類型 =============

// 代理節點狀態
export const ProxyStatus = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  TESTING: 'testing',
  ERROR: 'error',
  UNKNOWN: 'unknown'
} as const;
export type ProxyStatus = typeof ProxyStatus[keyof typeof ProxyStatus];

// 代理協議類型
export const ProxyProtocolValues = {
  HTTP: 'http',
  HTTPS: 'https',
  SOCKS4: 'socks4',
  SOCKS5: 'socks5'
} as const;
export type ProxyProtocol = typeof ProxyProtocolValues[keyof typeof ProxyProtocolValues];

// 代理匿名等級
export const AnonymityLevel = {
  TRANSPARENT: 'transparent',
  ANONYMOUS: 'anonymous',
  ELITE: 'elite'
} as const;
export type AnonymityLevel = typeof AnonymityLevel[keyof typeof AnonymityLevel];

// 任務狀態
export const TaskStatus = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  PAUSED: 'paused'
} as const;
export type TaskStatus = typeof TaskStatus[keyof typeof TaskStatus];

// 系統服務狀態
export const ServiceStatus = {
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  UNHEALTHY: 'unhealthy',
  UNKNOWN: 'unknown'
} as const;
export type ServiceStatus = typeof ServiceStatus[keyof typeof ServiceStatus];

// 日誌等級
export const LogLevel = {
  DEBUG: 'debug',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error'
} as const;
export type LogLevel = typeof LogLevel[keyof typeof LogLevel];

// ============= 資料介面 =============

// 代理節點介面
export interface ProxyNode {
  id: string;
  ip: string;
  port: number;
  protocol: ProxyProtocol;
  country?: string;
  countryCode?: string;
  city?: string;
  anonymity: AnonymityLevel;
  status: ProxyStatus;
  responseTime?: number; // 毫秒
  lastChecked?: string; // ISO 日期字串
  uptime?: number; // 百分比
  source?: string; // 來源網站
  maxConcurrent?: number; // 最大併發數
  timeout?: number; // 超時時間（毫秒）
  enabled?: boolean; // 是否啟用
  username?: string; // 用戶名
  password?: string; // 密碼
  url?: string; // 完整代理 URL
  type?: string; // 代理類型（向後兼容）
  healthScore?: number; // 健康分數
  tags?: string[]; // 標籤
  createdAt: string;
  updatedAt: string;
}

// 任務介面
export interface Task {
  id: string;
  name: string;
  type: string;
  status: TaskStatus;
  priority: TaskPriority;
  progress?: number; // 0-100
  startTime?: string;
  endTime?: string;
  duration?: number; // 毫秒
  result?: any;
  error?: string;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

// 任務創建請求
export interface TaskCreateRequest {
  name: string;
  type: string;
  priority?: TaskPriority;
  metadata?: Record<string, any>;
}

// 任務更新請求
export interface TaskUpdateRequest {
  name?: string;
  priority?: TaskPriority;
  metadata?: Record<string, any>;
}

// 任務統計介面
export interface TaskStatistics {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
  paused: number;
  successRate: number;
  averageExecutionTime: number;
  totalExecutionTime: number;
}

// 佇列狀態介面
export interface QueueStatus {
  isRunning: boolean;
  queueSize: number;
  activeWorkers: number;
  maxWorkers: number;
  processingRate: number;
  lastProcessedAt?: string;
}

// 任務操作類型
export const TaskOperation = {
  START: 'start',
  PAUSE: 'pause',
  RESUME: 'resume',
  CANCEL: 'cancel',
  RETRY: 'retry',
  DELETE: 'delete'
} as const;
export type TaskOperation = typeof TaskOperation[keyof typeof TaskOperation];

// 佇列操作類型
export const QueueOperation = {
  START: 'start',
  STOP: 'stop',
  PAUSE: 'pause',
  RESUME: 'resume',
  CLEAR: 'clear'
} as const;
export type QueueOperation = typeof QueueOperation[keyof typeof QueueOperation];

// 爬蟲任務介面（擴展基礎任務）
export interface CrawlTask extends Task {
  url: string;
  description?: string;
  priority: TaskPriority;
  maxRetries: number;
  timeout: number;
  proxyIds: string[];
  headers: Record<string, string>;
  cookies: Record<string, string>;
  scheduledAt?: Date;
  recurring: boolean;
  recurringPattern?: string;
  enabled: boolean;
}

// 任務執行結果
export interface TaskExecutionResult {
  taskId: string;
  success: boolean;
  data?: any;
  error?: string;
  duration: number;
  timestamp: string;
}

// 批量操作結果
export interface BulkOperationResult {
  success: boolean;
  processed: number;
  failed: number;
  errors?: string[];
  message: string;
}

// 排序配置
export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

// 健康狀態介面
export interface HealthStatus {
  status: ServiceStatus;
  timestamp: string;
  services?: Record<string, ServiceStatus>;
  details?: Record<string, any>;
  responseTime?: number;
}

// 系統指標介面
export interface SystemMetrics {
  totalProxies: number;
  activeProxies: number;
  successRate: number;
  averageResponseTime: number;
  tasksInQueue: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  timestamp: string;
}

// 趨勢資料點
export interface TrendDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

// 趨勢資料集
export interface TrendData {
  successRate: TrendDataPoint[];
  validationCount: TrendDataPoint[];
  averageLatency: TrendDataPoint[];
}

// 日誌條目
export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  source: string;
  message: string;
  details?: Record<string, any>;
  category?: string;
  userId?: string;
  requestId?: string;
}

// ============= UI 相關類型 =============

// 主題類型
export type Theme = 'light' | 'dark';

// 搜尋結果
export interface SearchResult {
  id: string;
  type: 'proxy' | 'task' | 'log';
  title: string;
  subtitle?: string;
  data: any;
}

// 篩選器選項
export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

// 篩選器狀態
export interface FilterState {
  protocol?: ProxyProtocol[];
  country?: string[];
  anonymity?: AnonymityLevel[];
  status?: ProxyStatus[];
  speedRange?: [number, number];
  search?: string;
}

// 保存的視圖
export interface SavedView {
  id: string;
  name: string;
  filters: FilterState;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  createdAt: string;
}

// 通知
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: NotificationAction[];
}

// 通知動作
export interface NotificationAction {
  label: string;
  action: () => void;
  primary?: boolean;
}

// ============= API 相關類型 =============

// API 回應基礎介面
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

// 分頁回應
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    size: number;
    total: number;
    totalPages: number;
  };
}

// 分頁參數
export interface PaginationParams {
  page?: number;
  size?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 代理查詢參數
export interface ProxyQueryParams extends PaginationParams {
  status?: ProxyStatus[];
  protocol?: ProxyProtocol[];
  country?: string[];
  anonymity?: AnonymityLevel[];
  search?: string;
  minSpeed?: number;
  maxSpeed?: number;
}

// 任務查詢參數
export interface TaskQueryParams extends PaginationParams {
  status?: TaskStatus[];
  type?: string[];
  search?: string;
  startDate?: string;
  endDate?: string;
}

// 日誌查詢參數
export interface LogQueryParams {
  source?: string[];
  level?: string[];
  since?: string;
  until?: string;
  search?: string;
  limit?: number;
}

// ============= 組件 Props 類型 =============

// 基礎組件 Props
export interface BaseComponentProps {
  className?: string;
  theme?: Theme;
}

// 卡片組件 Props
export interface CardProps extends BaseComponentProps {
  title?: string;
  subtitle?: string;
  loading?: boolean;
  error?: string;
  children: React.ReactNode;
}

// 表格組件 Props
export interface TableProps<T = any> extends BaseComponentProps {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  pagination?: PaginationParams;
  onPaginationChange?: (params: PaginationParams) => void;
  onRowClick?: (row: T) => void;
}

// 表格欄位定義
export interface TableColumn<T = any> {
  key: keyof T;
  title: string;
  width?: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
}

// 狀態指示器 Props
export interface StatusIndicatorProps extends BaseComponentProps {
  status: ServiceStatus;
  label?: string;
  size?: 'small' | 'medium' | 'large';
}

// 搜尋框 Props
export interface SearchBoxProps extends BaseComponentProps {
  value: string;
  placeholder?: string;
  onSearch: (query: string) => void;
  onClear?: () => void;
  loading?: boolean;
}

// ============= 分頁管理相關類型 =============

// 代理管理分頁
export interface ProxyManagementState {
  proxies: ProxyNode[];
  selectedProxies: string[];
  filters: ProxyFilters;
  pagination: PaginationState;
  loading: boolean;
  error?: string;
  total: number;
  totalCount: number;
}

export interface ProxyFilters {
  status?: ProxyStatus[];
  protocol?: ProxyProtocol[];
  country?: string[];
  anonymity?: AnonymityLevel[];
  search?: string;
  speedRange?: [number, number];
  healthScore?: { min: number; max: number };
  type?: ProxyProtocol;
  tags?: string[];
}

export interface ProxyBatchOperation {
  type: 'test' | 'delete' | 'export' | 'tag';
  proxyIds: string[];
  options?: Record<string, any>;
}

// 任務佇列分頁
export interface TaskQueueState {
  tasks: Task[];
  selectedTasks: string[];
  filters: TaskFilters;
  pagination: PaginationState;
  loading: boolean;
  error?: string;
  totalCount: number;
}

export interface TaskFilters {
  status?: TaskStatus[];
  type?: string[];
  search?: string;
  dateRange?: [string, string];
  priority?: TaskPriority[];
}

// 任務優先級
export const TaskPriority = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
} as const;
export type TaskPriority = typeof TaskPriority[keyof typeof TaskPriority];

export interface TaskSchedule {
  id: string;
  name: string;
  type: string;
  schedule: string; // cron expression
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
  createdAt: string;
}

// 系統日誌分頁
export interface SystemLogsState {
  logs: LogEntry[];
  filters: LogFilters;
  pagination: PaginationState;
  loading: boolean;
  error?: string;
  realTimeEnabled: boolean;
  totalCount: number;
}

export interface LogFilters {
  level?: LogLevel[];
  source?: string[];
  search?: string;
  timeRange?: [string, string];
  dateRange?: [string, string];
  category?: string;
}

export interface LogSource {
  name: string;
  label: string;
  count: number;
  enabled: boolean;
}

// 數據分析分頁
export interface DataAnalyticsState {
  metrics: SystemMetrics;
  trends: TrendData;
  reports: AnalyticsReport[];
  loading: boolean;
  error?: string;
  timeRange: TimeRange;
}

export interface AnalyticsReport {
  id: string;
  name: string;
  type: 'proxy_performance' | 'task_summary' | 'system_health' | 'custom';
  data: any;
  generatedAt: string;
  format: 'chart' | 'table' | 'summary';
}

export interface TimeRange {
  start: string;
  end: string;
  preset?: '1h' | '6h' | '24h' | '7d' | '30d' | 'custom';
}

// 通用分頁狀態
export interface PaginationState {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger: boolean;
  showQuickJumper: boolean;
}

// 表格排序狀態
export interface SortState {
  field?: string;
  order?: 'asc' | 'desc';
}



// ============= 頁面導航相關類型 =============

export interface PageTab {
  key: string;
  label: string;
  icon?: string;
  badge?: number;
  disabled?: boolean;
}

export interface PageAction {
  key: string;
  label: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  onClick: () => void;
}

export interface PageToolbar {
  search?: {
    placeholder: string;
    value: string;
    onChange: (value: string) => void;
  };
  filters?: React.ReactNode;
  actions?: PageAction[];
  extra?: React.ReactNode;
}

// ============= Hook 類型 =============

// API Hook 回傳類型
export interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// 輪詢 Hook 選項
export interface UsePollingOptions {
  interval?: number;
  enabled?: boolean;
  onError?: (error: Error) => void;
}

// 本地儲存 Hook 選項
export interface UseLocalStorageOptions<T> {
  defaultValue: T;
  serializer?: {
    read: (value: string) => T;
    write: (value: T) => string;
  };
}

// 分頁 Hook 選項
export interface UsePaginationOptions {
  defaultPageSize?: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  onPageChange?: (page: number, pageSize: number) => void;
}

// 表格 Hook 選項
export interface UseTableOptions<T> {
  data: T[];
  pagination?: UsePaginationOptions;
  sorting?: {
    defaultSort?: SortState;
    onSortChange?: (sort: SortState) => void;
  };
  selection?: {
    type?: 'checkbox' | 'radio';
    onSelectionChange?: (selectedKeys: string[], selectedRows: T[]) => void;
  };
}

// 代理測試結果介面
export interface ProxyTestResult {
  proxy_id: string;
  success: boolean;
  response_time?: number;
  error?: string;
  tested_at: string;
}