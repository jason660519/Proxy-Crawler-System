/**
 * 應用程式類型定義
 * 定義整個應用程式使用的 TypeScript 類型
 */

// ============================================================================
// 基礎類型
// ============================================================================

/**
 * 基礎實體接口
 */
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * API 響應基礎接口
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
}

/**
 * 分頁參數接口
 */
export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/**
 * 分頁響應接口
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

/**
 * 篩選參數接口
 */
export interface FilterParams {
  search?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  [key: string]: any;
}

// ============================================================================
// 代理相關類型
// ============================================================================

/**
 * 代理協議類型
 */
export type ProxyProtocol = 'http' | 'https' | 'socks4' | 'socks5';

/**
 * 匿名等級類型
 */
export type AnonymityLevel = 'elite' | 'anonymous' | 'transparent';

/**
 * 代理狀態類型
 */
export type ProxyStatus = 'online' | 'offline' | 'unknown';

/**
 * 地理位置信息接口
 */
export interface GeoLocation {
  country: string;
  countryCode: string;
  region?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  timezone?: string;
}

/**
 * 代理節點接口
 */
export interface ProxyNode extends BaseEntity {
  ip: string;
  port: number;
  protocol: ProxyProtocol;
  anonymity: AnonymityLevel;
  status: ProxyStatus;
  speed?: number; // 響應時間（毫秒）
  uptime?: number; // 正常運行時間百分比
  lastChecked?: string;
  location?: GeoLocation;
  source?: string; // 代理來源
  username?: string;
  password?: string;
  tags?: string[];
  notes?: string;
}

/**
 * 代理統計信息接口
 */
export interface ProxyStats {
  total: number;
  online: number;
  offline: number;
  unknown: number;
  byProtocol: Record<ProxyProtocol, number>;
  byAnonymity: Record<AnonymityLevel, number>;
  byCountry: Record<string, number>;
  averageSpeed: number;
  averageUptime: number;
}

/**
 * 代理測試結果接口
 */
export interface ProxyTestResult {
  proxyId: string;
  success: boolean;
  speed?: number;
  error?: string;
  timestamp: string;
  testUrl?: string;
  responseCode?: number;
  anonymityLevel?: AnonymityLevel;
}

/**
 * 代理批量操作接口
 */
export interface ProxyBatchOperation {
  action: 'test' | 'delete' | 'export' | 'tag';
  proxyIds: string[];
  params?: Record<string, any>;
}

// ============================================================================
// 任務相關類型
// ============================================================================

/**
 * 任務狀態類型
 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * 任務類型
 */
export type TaskType = 'crawl' | 'test' | 'export' | 'import' | 'cleanup';

/**
 * 任務優先級類型
 */
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

/**
 * 任務接口
 */
export interface Task extends BaseEntity {
  name: string;
  type: TaskType;
  status: TaskStatus;
  priority: TaskPriority;
  progress: number; // 0-100
  startedAt?: string;
  completedAt?: string;
  duration?: number; // 執行時間（毫秒）
  result?: any;
  error?: string;
  config?: Record<string, any>;
  logs?: TaskLog[];
}

/**
 * 任務日誌接口
 */
export interface TaskLog {
  id: string;
  taskId: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  timestamp: string;
  data?: any;
}

/**
 * 任務統計信息接口
 */
export interface TaskStats {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
  byType: Record<TaskType, number>;
  averageDuration: number;
  successRate: number;
}

// ============================================================================
// 爬蟲相關類型
// ============================================================================

/**
 * 爬蟲來源接口
 */
export interface CrawlerSource {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
  lastCrawled?: string;
  nextCrawl?: string;
  interval: number; // 爬取間隔（分鐘）
  config?: Record<string, any>;
  stats?: {
    totalCrawled: number;
    successRate: number;
    averageProxies: number;
    lastError?: string;
  };
}

/**
 * 爬蟲配置接口
 */
export interface CrawlerConfig {
  userAgent?: string;
  timeout: number;
  retries: number;
  delay: number;
  concurrent: number;
  respectRobots: boolean;
  headers?: Record<string, string>;
  cookies?: Record<string, string>;
  proxy?: {
    enabled: boolean;
    rotation: boolean;
    protocols: ProxyProtocol[];
  };
}

// ============================================================================
// 用戶相關類型
// ============================================================================

/**
 * 用戶角色類型
 */
export type UserRole = 'admin' | 'user' | 'viewer';

/**
 * 用戶接口
 */
export interface User extends BaseEntity {
  username: string;
  email: string;
  role: UserRole;
  avatar?: string;
  lastLogin?: string;
  preferences?: UserPreferences;
  permissions?: string[];
}

/**
 * 用戶偏好設定接口
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-TW' | 'en';
  timezone: string;
  notifications: {
    email: boolean;
    browser: boolean;
    taskComplete: boolean;
    proxyOffline: boolean;
  };
  dashboard: {
    refreshInterval: number;
    defaultView: string;
    widgets: string[];
  };
  table: {
    pageSize: number;
    autoRefresh: boolean;
    columns: Record<string, boolean>;
  };
}

// ============================================================================
// 系統相關類型
// ============================================================================

/**
 * 系統狀態接口
 */
export interface SystemStatus {
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  version: string;
  environment: 'development' | 'staging' | 'production';
  services: ServiceStatus[];
  resources: SystemResources;
  lastUpdated: string;
}

/**
 * 服務狀態接口
 */
export interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  url?: string;
  responseTime?: number;
  lastCheck: string;
  error?: string;
}

/**
 * 系統資源接口
 */
export interface SystemResources {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    used: number;
    total: number;
    usage: number;
  };
  disk: {
    used: number;
    total: number;
    usage: number;
  };
  network: {
    bytesIn: number;
    bytesOut: number;
  };
}

/**
 * 系統配置接口
 */
export interface SystemConfig {
  app: {
    name: string;
    version: string;
    environment: string;
    debug: boolean;
  };
  api: {
    baseUrl: string;
    timeout: number;
    retries: number;
  };
  database: {
    type: string;
    host: string;
    port: number;
    name: string;
  };
  cache: {
    enabled: boolean;
    ttl: number;
    maxSize: number;
  };
  security: {
    cors: boolean;
    rateLimit: {
      enabled: boolean;
      requests: number;
      window: number;
    };
  };
}

// ============================================================================
// 監控相關類型
// ============================================================================

/**
 * 監控指標接口
 */
export interface Metric {
  name: string;
  value: number;
  unit: string;
  timestamp: string;
  tags?: Record<string, string>;
}

/**
 * 監控警報接口
 */
export interface Alert {
  id: string;
  name: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  source: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
  resolved: boolean;
  resolvedAt?: string;
  data?: any;
}

/**
 * 監控儀表板配置接口
 */
export interface DashboardConfig {
  id: string;
  name: string;
  layout: DashboardWidget[];
  refreshInterval: number;
  timeRange: {
    from: string;
    to: string;
  };
  filters?: Record<string, any>;
}

/**
 * 儀表板小工具接口
 */
export interface DashboardWidget {
  id: string;
  type: 'chart' | 'table' | 'stat' | 'gauge' | 'text';
  title: string;
  position: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  config: Record<string, any>;
  dataSource?: string;
  query?: string;
}

// ============================================================================
// 表單相關類型
// ============================================================================

/**
 * 表單欄位類型
 */
export type FormFieldType = 
  | 'text'
  | 'email'
  | 'password'
  | 'number'
  | 'url'
  | 'tel'
  | 'textarea'
  | 'select'
  | 'multiselect'
  | 'checkbox'
  | 'radio'
  | 'switch'
  | 'date'
  | 'datetime'
  | 'time'
  | 'file'
  | 'color'
  | 'range';

/**
 * 表單欄位接口
 */
export interface FormField {
  name: string;
  type: FormFieldType;
  label: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  defaultValue?: any;
  options?: FormOption[];
  validation?: FormValidation;
  help?: string;
  className?: string;
}

/**
 * 表單選項接口
 */
export interface FormOption {
  label: string;
  value: any;
  disabled?: boolean;
  group?: string;
}

/**
 * 表單驗證接口
 */
export interface FormValidation {
  required?: boolean;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  custom?: (value: any) => string | null;
}

/**
 * 表單錯誤接口
 */
export interface FormError {
  field: string;
  message: string;
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
}

// ============================================================================
// 表格相關類型
// ============================================================================

/**
 * 表格欄位接口
 */
export interface TableColumn<T = any> {
  key: keyof T | string;
  title: string;
  width?: number | string;
  minWidth?: number;
  maxWidth?: number;
  sortable?: boolean;
  filterable?: boolean;
  resizable?: boolean;
  fixed?: 'left' | 'right';
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: T, index: number) => React.ReactNode;
  className?: string;
  headerClassName?: string;
}

/**
 * 表格排序接口
 */
export interface TableSort {
  field: string;
  order: 'asc' | 'desc';
}

/**
 * 表格篩選接口
 */
export interface TableFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in' | 'nin';
  value: any;
}

/**
 * 表格選擇接口
 */
export interface TableSelection<T = any> {
  selectedRowKeys: string[];
  selectedRows: T[];
  onChange: (selectedRowKeys: string[], selectedRows: T[]) => void;
}

// ============================================================================
// 通知相關類型
// ============================================================================

/**
 * 通知類型
 */
export type NotificationType = 'success' | 'info' | 'warning' | 'error';

/**
 * 通知接口
 */
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  closable?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  timestamp: string;
}

// ============================================================================
// 主題相關類型
// ============================================================================

/**
 * 主題類型
 */
export type ThemeMode = 'light' | 'dark' | 'auto';

/**
 * 主題配置接口
 */
export interface ThemeConfig {
  mode: ThemeMode;
  primaryColor: string;
  borderRadius: number;
  fontSize: number;
  fontFamily: string;
  customColors?: Record<string, string>;
}

// ============================================================================
// 路由相關類型
// ============================================================================

/**
 * 路由項目接口
 */
export interface RouteItem {
  path: string;
  name: string;
  component?: React.ComponentType;
  icon?: string;
  children?: RouteItem[];
  meta?: RouteMeta;
}

/**
 * 路由元數據接口
 */
export interface RouteMeta {
  title?: string;
  description?: string;
  requiresAuth?: boolean;
  roles?: UserRole[];
  permissions?: string[];
  hidden?: boolean;
  keepAlive?: boolean;
  breadcrumb?: boolean;
}

// ============================================================================
// 工具類型
// ============================================================================

/**
 * 深度部分類型
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

/**
 * 深度必需類型
 */
export type DeepRequired<T> = {
  [P in keyof T]-?: T[P] extends object ? DeepRequired<T[P]> : T[P];
};

/**
 * 選擇性鍵類型
 */
export type PickByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};

/**
 * 排除性鍵類型
 */
export type OmitByType<T, U> = {
  [K in keyof T as T[K] extends U ? never : K]: T[K];
};

/**
 * 函數參數類型
 */
export type FunctionArgs<T> = T extends (...args: infer A) => any ? A : never;

/**
 * 函數返回類型
 */
export type FunctionReturn<T> = T extends (...args: any[]) => infer R ? R : never;

/**
 * 異步函數返回類型
 */
export type AsyncReturn<T> = T extends (...args: any[]) => Promise<infer R> ? R : never;

/**
 * 鍵值對類型
 */
export type KeyValuePair<K extends string | number | symbol = string, V = any> = {
  [key in K]: V;
};

/**
 * 可選鍵類型
 */
export type OptionalKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? K : never;
}[keyof T];

/**
 * 必需鍵類型
 */
export type RequiredKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? never : K;
}[keyof T];

/**
 * 聯合轉交集類型
 */
export type UnionToIntersection<U> = (
  U extends any ? (k: U) => void : never
) extends (k: infer I) => void
  ? I
  : never;

/**
 * 字面量聯合類型
 */
export type LiteralUnion<T extends U, U = string> = T | (U & Record<never, never>);

// ============================================================================
// 導出所有類型
// ============================================================================

export * from './api';
export * from './components';
export * from './hooks';
export * from './utils';