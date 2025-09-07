/**
 * 代理爬蟲管理系統 - TypeScript 類型定義
 * 定義系統中使用的所有資料結構和介面
 */

// 代理節點狀態枚舉
export enum ProxyStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TESTING = 'testing',
  ERROR = 'error',
  UNKNOWN = 'unknown'
}

// 代理協議類型
export enum ProxyProtocol {
  HTTP = 'http',
  HTTPS = 'https',
  SOCKS4 = 'socks4',
  SOCKS5 = 'socks5'
}

// 代理匿名等級
export enum AnonymityLevel {
  TRANSPARENT = 'transparent',
  ANONYMOUS = 'anonymous',
  ELITE = 'elite'
}

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
  lastChecked?: Date;
  uptime?: number; // 百分比
  source?: string; // 來源網站
  createdAt: Date;
  updatedAt: Date;
}

// ETL 流程狀態
export enum ETLStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// ETL 任務介面
export interface ETLTask {
  id: string;
  name: string;
  status: ETLStatus;
  startTime?: Date;
  endTime?: Date;
  duration?: number; // 秒
  processedCount: number;
  successCount: number;
  errorCount: number;
  progress: number; // 0-100
  logs: string[];
  createdAt: Date;
  proxiesFound?: number; // Dashboard需要的屬性
}

// 系統監控指標
export interface SystemMetrics {
  timestamp: Date;
  cpuUsage: number; // 百分比
  memoryUsage: number; // 百分比
  diskUsage: number; // 百分比
  networkIn: number; // bytes/s
  networkOut: number; // bytes/s
  activeProxies: number;
  totalProxies: number;
  etlTasksRunning: number;
}

// 側邊欄選單項目介面
export interface SidebarMenuItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  badge?: string | number;
  children?: SidebarMenuItem[];
}

// 表格欄位定義
export interface TableColumn<T = any> {
  key: keyof T;
  title: string;
  width?: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T) => React.ReactNode;
}

// API 回應介面
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: Date;
}

// 分頁參數
export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 分頁回應
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// 主題設定
export interface ThemeConfig {
  mode: 'light' | 'dark';
  primaryColor: string;
  accentColor: string;
  fontSize: 'small' | 'medium' | 'large';
}