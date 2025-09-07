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
export const ProxyProtocol = {
  HTTP: 'http',
  HTTPS: 'https',
  SOCKS4: 'socks4',
  SOCKS5: 'socks5'
} as const;
export type ProxyProtocol = typeof ProxyProtocol[keyof typeof ProxyProtocol];

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
  CANCELLED: 'cancelled'
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
  createdAt: string;
  updatedAt: string;
}

// 任務介面
export interface Task {
  id: string;
  name: string;
  type: string;
  status: TaskStatus;
  progress?: number; // 0-100
  startTime?: string;
  endTime?: string;
  duration?: number; // 毫秒
  result?: any;
  error?: string;
  createdAt: string;
  updatedAt: string;
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