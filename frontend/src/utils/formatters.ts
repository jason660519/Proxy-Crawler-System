/**
 * 格式化工具函數
 * 
 * 提供各種數據格式化功能，包括：
 * - 日期時間格式化
 * - 數字格式化
 * - 文件大小格式化
 * - 持續時間格式化
 * - 狀態格式化
 */

// ============= 日期時間格式化 =============

/**
 * 格式化日期時間
 * 
 * @param date 日期對象、時間戳或日期字符串
 * @param format 格式類型
 * @returns 格式化後的日期時間字符串
 */
export function formatDateTime(
  date: Date | string | number,
  format: 'full' | 'date' | 'time' | 'relative' = 'full'
): string {
  if (!date) return '-';
  
  const dateObj = new Date(date);
  if (isNaN(dateObj.getTime())) return '-';
  
  const now = new Date();
  const diff = now.getTime() - dateObj.getTime();
  
  switch (format) {
    case 'full':
      return dateObj.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
      
    case 'date':
      return dateObj.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
      
    case 'time':
      return dateObj.toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
      
    case 'relative':
      return formatRelativeTime(diff);
      
    default:
      return dateObj.toLocaleString('zh-TW');
  }
}

/**
 * 格式化相對時間
 * 
 * @param diff 時間差（毫秒）
 * @returns 相對時間字符串
 */
export function formatRelativeTime(diff: number): string {
  const seconds = Math.floor(Math.abs(diff) / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  const isFuture = diff < 0;
  const prefix = isFuture ? '' : '';
  const suffix = isFuture ? '後' : '前';
  
  if (days > 0) {
    return `${prefix}${days} 天${suffix}`;
  } else if (hours > 0) {
    return `${prefix}${hours} 小時${suffix}`;
  } else if (minutes > 0) {
    return `${prefix}${minutes} 分鐘${suffix}`;
  } else if (seconds > 0) {
    return `${prefix}${seconds} 秒${suffix}`;
  } else {
    return '剛剛';
  }
}

// ============= 持續時間格式化 =============

/**
 * 格式化持續時間
 * 
 * @param duration 持續時間（毫秒）
 * @param format 格式類型
 * @returns 格式化後的持續時間字符串
 */
export function formatDuration(
  duration: number,
  format: 'full' | 'short' | 'minimal' = 'full'
): string {
  if (!duration || duration < 0) return '-';
  
  const seconds = Math.floor(duration / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  const remainingHours = hours % 24;
  const remainingMinutes = minutes % 60;
  const remainingSeconds = seconds % 60;
  
  switch (format) {
    case 'full':
      const parts: string[] = [];
      if (days > 0) parts.push(`${days} 天`);
      if (remainingHours > 0) parts.push(`${remainingHours} 小時`);
      if (remainingMinutes > 0) parts.push(`${remainingMinutes} 分鐘`);
      if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds} 秒`);
      return parts.join(' ');
      
    case 'short':
      if (days > 0) return `${days}d ${remainingHours}h`;
      if (hours > 0) return `${hours}h ${remainingMinutes}m`;
      if (minutes > 0) return `${minutes}m ${remainingSeconds}s`;
      return `${seconds}s`;
      
    case 'minimal':
      if (days > 0) return `${days}d`;
      if (hours > 0) return `${hours}h`;
      if (minutes > 0) return `${minutes}m`;
      return `${seconds}s`;
      
    default:
      return `${duration}ms`;
  }
}

// ============= 數字格式化 =============

/**
 * 格式化數字
 * 
 * @param num 數字
 * @param options 格式化選項
 * @returns 格式化後的數字字符串
 */
export function formatNumber(
  num: number,
  options: {
    decimals?: number;
    separator?: boolean;
    unit?: string;
    prefix?: string;
  } = {}
): string {
  if (typeof num !== 'number' || isNaN(num)) return '-';
  
  const { decimals = 0, separator = true, unit = '', prefix = '' } = options;
  
  let formatted = num.toFixed(decimals);
  
  if (separator) {
    formatted = formatted.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }
  
  return `${prefix}${formatted}${unit}`;
}

/**
 * 格式化百分比
 * 
 * @param value 數值（0-1 或 0-100）
 * @param decimals 小數位數
 * @param isDecimal 是否為小數形式（0-1）
 * @returns 格式化後的百分比字符串
 */
export function formatPercentage(
  value: number,
  decimals: number = 1,
  isDecimal: boolean = true
): string {
  if (typeof value !== 'number' || isNaN(value)) return '-';
  
  const percentage = isDecimal ? value * 100 : value;
  return `${percentage.toFixed(decimals)}%`;
}

// ============= 文件大小格式化 =============

/**
 * 格式化文件大小
 * 
 * @param bytes 字節數
 * @param decimals 小數位數
 * @returns 格式化後的文件大小字符串
 */
export function formatFileSize(bytes: number, decimals: number = 2): string {
  if (!bytes || bytes === 0) return '0 B';
  if (bytes < 0) return '-';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  const value = bytes / Math.pow(k, i);
  return `${value.toFixed(decimals)} ${sizes[i]}`;
}

// ============= 狀態格式化 =============

/**
 * 格式化任務狀態
 * 
 * @param status 狀態值
 * @returns 格式化後的狀態字符串
 */
export function formatTaskStatus(status: string): string {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'running': '執行中',
    'completed': '已完成',
    'failed': '失敗',
    'cancelled': '已取消',
    'paused': '已暫停'
  };
  
  return statusMap[status] || status;
}

/**
 * 格式化代理狀態
 * 
 * @param status 狀態值
 * @returns 格式化後的狀態字符串
 */
export function formatProxyStatus(status: string): string {
  const statusMap: Record<string, string> = {
    'active': '活躍',
    'inactive': '非活躍',
    'testing': '測試中',
    'failed': '失效',
    'unknown': '未知'
  };
  
  return statusMap[status] || status;
}

/**
 * 格式化優先級
 * 
 * @param priority 優先級值
 * @returns 格式化後的優先級字符串
 */
export function formatPriority(priority: string): string {
  const priorityMap: Record<string, string> = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'urgent': '緊急'
  };
  
  return priorityMap[priority] || priority;
}

// ============= 網路相關格式化 =============

/**
 * 格式化 URL
 * 
 * @param url URL 字符串
 * @param maxLength 最大長度
 * @returns 格式化後的 URL 字符串
 */
export function formatUrl(url: string, maxLength: number = 50): string {
  if (!url) return '-';
  
  if (url.length <= maxLength) return url;
  
  const start = url.substring(0, Math.floor(maxLength / 2) - 2);
  const end = url.substring(url.length - Math.floor(maxLength / 2) + 2);
  
  return `${start}...${end}`;
}

/**
 * 格式化 IP 地址
 * 
 * @param ip IP 地址字符串
 * @returns 格式化後的 IP 地址字符串
 */
export function formatIpAddress(ip: string): string {
  if (!ip) return '-';
  
  // 簡單的 IP 地址驗證和格式化
  const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
  const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
  
  if (ipv4Regex.test(ip) || ipv6Regex.test(ip)) {
    return ip;
  }
  
  return ip; // 返回原始值，讓調用者決定如何處理
}

// ============= 導出所有格式化函數 =============

export default {
  formatDateTime,
  formatRelativeTime,
  formatDuration,
  formatNumber,
  formatPercentage,
  formatFileSize,
  formatTaskStatus,
  formatProxyStatus,
  formatPriority,
  formatUrl,
  formatIpAddress
};