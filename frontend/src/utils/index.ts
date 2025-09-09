/**
 * 工具函數庫
 * 提供常用的輔助功能和實用工具
 */

import type { ProxyStatus, TaskStatus, LogLevel } from '../types';

// 導出驗證工具
export * from './validators';

// 導出格式化工具
export * from './formatters';

// ============= 時間處理工具 =============

/**
 * 格式化時間戳
 */
export function formatTimestamp(
  timestamp: string | number | Date,
  format: 'full' | 'date' | 'time' | 'relative' = 'full'
): string {
  const date = new Date(timestamp);
  
  if (isNaN(date.getTime())) {
    return '無效時間';
  }

  const now = new Date();
  const diff = now.getTime() - date.getTime();

  switch (format) {
    case 'relative':
      return formatRelativeTime(diff);
    case 'date':
      return date.toLocaleDateString('zh-TW');
    case 'time':
      return date.toLocaleTimeString('zh-TW');
    case 'full':
    default:
      return date.toLocaleString('zh-TW');
  }
}

/**
 * 格式化相對時間
 */
export function formatRelativeTime(milliseconds: number): string {
  const seconds = Math.floor(Math.abs(milliseconds) / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  const isPast = milliseconds > 0;
  const suffix = isPast ? '前' : '後';

  if (days > 0) {
    return `${days} 天${suffix}`;
  } else if (hours > 0) {
    return `${hours} 小時${suffix}`;
  } else if (minutes > 0) {
    return `${minutes} 分鐘${suffix}`;
  } else if (seconds > 30) {
    return `${seconds} 秒${suffix}`;
  } else {
    return isPast ? '剛剛' : '即將';
  }
}

/**
 * 格式化持續時間
 */
export function formatDuration(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}天 ${hours % 24}時 ${minutes % 60}分`;
  } else if (hours > 0) {
    return `${hours}時 ${minutes % 60}分 ${seconds % 60}秒`;
  } else if (minutes > 0) {
    return `${minutes}分 ${seconds % 60}秒`;
  } else {
    return `${seconds}秒`;
  }
}

// ============= 數字格式化工具 =============

/**
 * 格式化數字（添加千分位分隔符）
 */
export function formatNumber(num: number, decimals: number = 0): string {
  return num.toLocaleString('zh-TW', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

/**
 * 格式化百分比
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * 格式化檔案大小
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

/**
 * 格式化延遲時間
 */
export function formatLatency(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  } else {
    return `${(ms / 1000).toFixed(1)}s`;
  }
}

// ============= 字串處理工具 =============

/**
 * 截斷字串
 */
export function truncateString(str: string, maxLength: number, suffix: string = '...'): string {
  if (str.length <= maxLength) {
    return str;
  }
  return str.slice(0, maxLength - suffix.length) + suffix;
}

/**
 * 高亮搜尋關鍵字
 */
export function highlightText(text: string, query: string): string {
  if (!query.trim()) {
    return text;
  }

  const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

/**
 * 轉義正則表達式特殊字符
 */
export function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * 生成隨機 ID
 */
export function generateId(prefix: string = '', length: number = 8): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return prefix ? `${prefix}_${result}` : result;
}

// ============= 陣列處理工具 =============

/**
 * 陣列去重
 */
export function uniqueArray<T>(array: T[], keyFn?: (item: T) => any): T[] {
  if (!keyFn) {
    return [...new Set(array)];
  }

  const seen = new Set();
  return array.filter(item => {
    const key = keyFn(item);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

/**
 * 陣列分組
 */
export function groupBy<T, K extends string | number | symbol>(
  array: T[],
  keyFn: (item: T) => K
): Record<K, T[]> {
  return array.reduce((groups, item) => {
    const key = keyFn(item);
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {} as Record<K, T[]>);
}

/**
 * 陣列排序
 */
export function sortBy<T>(
  array: T[],
  keyFn: (item: T) => any,
  direction: 'asc' | 'desc' = 'asc'
): T[] {
  return [...array].sort((a, b) => {
    const aVal = keyFn(a);
    const bVal = keyFn(b);
    
    if (aVal < bVal) {
      return direction === 'asc' ? -1 : 1;
    }
    if (aVal > bVal) {
      return direction === 'asc' ? 1 : -1;
    }
    return 0;
  });
}

// ============= 物件處理工具 =============

/**
 * 深度複製
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as unknown as T;
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as unknown as T;
  }

  if (typeof obj === 'object') {
    const cloned = {} as { [key: string]: any };
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = deepClone((obj as any)[key]);
      }
    }
    return cloned as T;
  }

  return obj;
}

/**
 * 物件合併
 */
export function mergeDeep<T extends Record<string, any>>(...objects: Partial<T>[]): T {
  const result = {} as T;

  for (const obj of objects) {
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const value = obj[key];
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          (result as any)[key] = mergeDeep((result as any)[key] || {}, value);
        } else {
          (result as any)[key] = value;
        }
      }
    }
  }

  return result;
}

/**
 * 移除物件中的空值
 */
export function removeEmpty<T extends Record<string, any>>(obj: T): Partial<T> {
  const result: Partial<T> = {};
  
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      const value = obj[key];
      if (value !== null && value !== undefined && value !== '') {
        if (typeof value === 'object' && !Array.isArray(value)) {
          const cleaned = removeEmpty(value);
          if (Object.keys(cleaned).length > 0) {
            result[key] = cleaned as T[Extract<keyof T, string>];
          }
        } else {
          result[key] = value;
        }
      }
    }
  }
  
  return result;
}

// ============= 驗證工具 =============

/**
 * 驗證 IP 地址
 */
export function isValidIP(ip: string): boolean {
  const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
  return ipv4Regex.test(ip) || ipv6Regex.test(ip);
}

/**
 * 驗證端口號
 */
export function isValidPort(port: number | string): boolean {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port;
  return Number.isInteger(portNum) && portNum >= 1 && portNum <= 65535;
}

/**
 * 驗證 URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * 驗證電子郵件
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// ============= 狀態處理工具 =============

/**
 * 獲取代理狀態顏色
 */
export function getProxyStatusColor(status: ProxyStatus): string {
  switch (status) {
    case 'active':
      return '#10b981'; // green-500
    case 'inactive':
      return '#ef4444'; // red-500
    case 'testing':
      return '#f59e0b'; // amber-500
    case 'unknown':
    default:
      return '#6b7280'; // gray-500
  }
}

/**
 * 獲取代理狀態文字
 */
export function getProxyStatusText(status: ProxyStatus): string {
  switch (status) {
    case 'active':
      return '正常';
    case 'inactive':
      return '失效';
    case 'testing':
      return '測試中';
    case 'unknown':
    default:
      return '未知';
  }
}

/**
 * 獲取任務狀態顏色
 */
export function getTaskStatusColor(status: TaskStatus): string {
  switch (status) {
    case 'completed':
      return '#10b981'; // green-500
    case 'failed':
      return '#ef4444'; // red-500
    case 'running':
      return '#3b82f6'; // blue-500
    case 'pending':
      return '#f59e0b'; // amber-500
    case 'cancelled':
      return '#6b7280'; // gray-500
    default:
      return '#6b7280';
  }
}

/**
 * 獲取任務狀態文字
 */
export function getTaskStatusText(status: TaskStatus): string {
  switch (status) {
    case 'completed':
      return '已完成';
    case 'failed':
      return '失敗';
    case 'running':
      return '執行中';
    case 'pending':
      return '等待中';
    case 'cancelled':
      return '已取消';
    default:
      return '未知';
  }
}

/**
 * 獲取日誌級別顏色
 */
export function getLogLevelColor(level: LogLevel): string {
  switch (level) {
    case 'error':
      return '#ef4444'; // red-500
    case 'warning':
      return '#f59e0b'; // amber-500
    case 'info':
      return '#3b82f6'; // blue-500
    case 'debug':
      return '#6b7280'; // gray-500
    default:
      return '#6b7280';
  }
}

/**
 * 獲取日誌級別文字
 */
export function getLogLevelText(level: LogLevel): string {
  switch (level) {
    case 'error':
      return '錯誤';
    case 'warning':
      return '警告';
    case 'info':
      return '資訊';
    case 'debug':
      return '除錯';
    default:
      return '未知';
  }
}

// ============= 瀏覽器工具 =============

/**
 * 複製到剪貼板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // 降級方案
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const result = document.execCommand('copy');
      textArea.remove();
      return result;
    }
  } catch (error) {
    console.error('複製到剪貼板失敗:', error);
    return false;
  }
}

/**
 * 下載檔案
 */
export function downloadFile(content: string, filename: string, mimeType: string = 'text/plain'): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * 獲取瀏覽器資訊
 */
export function getBrowserInfo(): {
  name: string;
  version: string;
  platform: string;
} {
  const userAgent = navigator.userAgent;
  let name = 'Unknown';
  let version = 'Unknown';
  
  if (userAgent.includes('Chrome')) {
    name = 'Chrome';
    const match = userAgent.match(/Chrome\/(\d+\.\d+)/);
    version = match ? match[1] : 'Unknown';
  } else if (userAgent.includes('Firefox')) {
    name = 'Firefox';
    const match = userAgent.match(/Firefox\/(\d+\.\d+)/);
    version = match ? match[1] : 'Unknown';
  } else if (userAgent.includes('Safari')) {
    name = 'Safari';
    const match = userAgent.match(/Version\/(\d+\.\d+)/);
    version = match ? match[1] : 'Unknown';
  } else if (userAgent.includes('Edge')) {
    name = 'Edge';
    const match = userAgent.match(/Edge\/(\d+\.\d+)/);
    version = match ? match[1] : 'Unknown';
  }
  
  return {
    name,
    version,
    platform: navigator.platform
  };
}

// ============= 錯誤處理工具 =============

/**
 * 錯誤邊界處理
 */
export function handleError(error: Error, context?: string): void {
  console.error(`錯誤發生${context ? ` (${context})` : ''}:`, error);
  
  // 可以在這裡添加錯誤報告邏輯
  // 例如發送到錯誤追蹤服務
}

/**
 * 安全的 JSON 解析
 */
export function safeJsonParse<T>(json: string, defaultValue: T): T {
  try {
    return JSON.parse(json);
  } catch (error) {
    console.warn('JSON 解析失敗:', error);
    return defaultValue;
  }
}

/**
 * 重試函數
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      if (attempt === maxAttempts) {
        throw lastError;
      }
      
      // 等待後重試
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }
  
  throw lastError!;
}

// ============= 匯出所有工具函數 =============

export const utils = {
  // 時間處理
  formatTimestamp,
  formatRelativeTime,
  formatDuration,
  
  // 數字格式化
  formatNumber,
  formatPercentage,
  formatFileSize,
  formatLatency,
  
  // 字串處理
  truncateString,
  highlightText,
  escapeRegExp,
  generateId,
  
  // 陣列處理
  uniqueArray,
  groupBy,
  sortBy,
  
  // 物件處理
  deepClone,
  mergeDeep,
  removeEmpty,
  
  // 驗證
  isValidIP,
  isValidPort,
  isValidUrl,
  isValidEmail,
  
  // 狀態處理
  getProxyStatusColor,
  getProxyStatusText,
  getTaskStatusColor,
  getTaskStatusText,
  getLogLevelColor,
  getLogLevelText,
  
  // 瀏覽器
  copyToClipboard,
  downloadFile,
  getBrowserInfo,
  
  // 錯誤處理
  handleError,
  safeJsonParse,
  retry
};

export default utils;