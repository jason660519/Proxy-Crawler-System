/**
 * 通用工具函數集合
 * 提供各種實用的輔助功能
 */

import { REGEX, PROXY } from './constants';
import type { ProxyProtocol, AnonymityLevel, ProxyStatus } from './constants';

/**
 * 延遲執行函數
 * @param ms 延遲時間（毫秒）
 * @returns Promise
 */
export const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * 防抖函數
 * @param func 要防抖的函數
 * @param wait 等待時間（毫秒）
 * @param immediate 是否立即執行
 * @returns 防抖後的函數
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      if (!immediate) func(...args);
    };
    
    const callNow = immediate && !timeout;
    
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    
    if (callNow) func(...args);
  };
}

/**
 * 節流函數
 * @param func 要節流的函數
 * @param limit 限制時間（毫秒）
 * @returns 節流後的函數
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * 深度複製物件
 * @param obj 要複製的物件
 * @returns 複製後的物件
 */
export const deepClone = <T>(obj: T): T => {
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
    const clonedObj = {} as { [key: string]: any };
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj as T;
  }
  
  return obj;
};

/**
 * 深度比較兩個物件是否相等
 * @param obj1 物件1
 * @param obj2 物件2
 * @returns 是否相等
 */
export const deepEqual = (obj1: any, obj2: any): boolean => {
  if (obj1 === obj2) {
    return true;
  }
  
  if (obj1 == null || obj2 == null) {
    return false;
  }
  
  if (typeof obj1 !== typeof obj2) {
    return false;
  }
  
  if (typeof obj1 !== 'object') {
    return obj1 === obj2;
  }
  
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  
  if (keys1.length !== keys2.length) {
    return false;
  }
  
  for (const key of keys1) {
    if (!keys2.includes(key)) {
      return false;
    }
    
    if (!deepEqual(obj1[key], obj2[key])) {
      return false;
    }
  }
  
  return true;
};

/**
 * 合併物件（深度合併）
 * @param target 目標物件
 * @param sources 來源物件
 * @returns 合併後的物件
 */
export const deepMerge = <T extends Record<string, any>>(
  target: T,
  ...sources: Partial<T>[]
): T => {
  if (!sources.length) return target;
  const source = sources.shift();
  
  if (isObject(target) && isObject(source)) {
    for (const key in source) {
      if (isObject(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} });
        deepMerge(target[key], source[key]);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }
  
  return deepMerge(target, ...sources);
};

/**
 * 判斷是否為物件
 * @param item 要判斷的項目
 * @returns 是否為物件
 */
export const isObject = (item: any): item is Record<string, any> => {
  return item && typeof item === 'object' && !Array.isArray(item);
};

/**
 * 判斷是否為空值
 * @param value 要判斷的值
 * @returns 是否為空值
 */
export const isEmpty = (value: any): boolean => {
  if (value == null) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

/**
 * 判斷是否為有效的值
 * @param value 要判斷的值
 * @returns 是否為有效值
 */
export const isValid = (value: any): boolean => {
  return !isEmpty(value);
};

/**
 * 生成唯一 ID
 * @param prefix 前綴
 * @returns 唯一 ID
 */
export const generateId = (prefix = 'id'): string => {
  const timestamp = Date.now().toString(36);
  const randomStr = Math.random().toString(36).substring(2, 8);
  return `${prefix}_${timestamp}_${randomStr}`;
};

/**
 * 生成 UUID v4
 * @returns UUID 字串
 */
export const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

/**
 * 隨機選擇陣列中的元素
 * @param array 陣列
 * @returns 隨機元素
 */
export const randomChoice = <T>(array: T[]): T | undefined => {
  if (array.length === 0) return undefined;
  return array[Math.floor(Math.random() * array.length)];
};

/**
 * 隨機打亂陣列
 * @param array 陣列
 * @returns 打亂後的陣列
 */
export const shuffle = <T>(array: T[]): T[] => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

/**
 * 陣列去重
 * @param array 陣列
 * @param key 去重的鍵（可選）
 * @returns 去重後的陣列
 */
export const unique = <T>(
  array: T[],
  key?: keyof T
): T[] => {
  if (!key) {
    return [...new Set(array)];
  }
  
  const seen = new Set();
  return array.filter(item => {
    const value = item[key];
    if (seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
};

/**
 * 陣列分組
 * @param array 陣列
 * @param key 分組的鍵
 * @returns 分組後的物件
 */
export const groupBy = <T, K extends keyof T>(
  array: T[],
  key: K
): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const groupKey = String(item[key]);
    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

/**
 * 陣列分塊
 * @param array 陣列
 * @param size 每塊大小
 * @returns 分塊後的陣列
 */
export const chunk = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

/**
 * 範圍生成器
 * @param start 開始值
 * @param end 結束值
 * @param step 步長
 * @returns 範圍陣列
 */
export const range = (start: number, end: number, step = 1): number[] => {
  const result: number[] = [];
  for (let i = start; i < end; i += step) {
    result.push(i);
  }
  return result;
};

/**
 * 複製文字到剪貼板
 * @param text 要複製的文字
 * @returns Promise<boolean> 是否成功
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
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
      document.body.removeChild(textArea);
      return result;
    }
  } catch (error) {
    console.error('複製到剪貼板失敗:', error);
    return false;
  }
};

/**
 * 從剪貼板讀取文字
 * @returns Promise<string> 剪貼板內容
 */
export const readFromClipboard = async (): Promise<string> => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      return await navigator.clipboard.readText();
    } else {
      throw new Error('剪貼板 API 不可用');
    }
  } catch (error) {
    console.error('從剪貼板讀取失敗:', error);
    return '';
  }
};

/**
 * 下載檔案
 * @param data 檔案內容
 * @param filename 檔案名稱
 * @param type MIME 類型
 */
export const downloadFile = (
  data: string | Blob,
  filename: string,
  type = 'text/plain'
): void => {
  const blob = data instanceof Blob ? data : new Blob([data], { type });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
};

/**
 * 讀取檔案內容
 * @param file 檔案物件
 * @returns Promise<string> 檔案內容
 */
export const readFile = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
};

/**
 * 格式化檔案大小
 * @param bytes 位元組數
 * @param decimals 小數位數
 * @returns 格式化後的大小
 */
export const formatFileSize = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
};

/**
 * 驗證 IP 地址
 * @param ip IP 地址
 * @returns 是否有效
 */
export const isValidIP = (ip: string): boolean => {
  return REGEX.IP_V4.test(ip) || REGEX.IP_V6.test(ip);
};

/**
 * 驗證端口號
 * @param port 端口號
 * @returns 是否有效
 */
export const isValidPort = (port: number | string): boolean => {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port;
  return Number.isInteger(portNum) && portNum >= 1 && portNum <= 65535;
};

/**
 * 驗證 URL
 * @param url URL 字串
 * @returns 是否有效
 */
export const isValidURL = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * 驗證電子郵件
 * @param email 電子郵件
 * @returns 是否有效
 */
export const isValidEmail = (email: string): boolean => {
  return REGEX.EMAIL.test(email);
};

/**
 * 解析代理字串
 * @param proxyString 代理字串（格式：protocol://ip:port 或 ip:port）
 * @returns 解析後的代理資訊
 */
export const parseProxy = (proxyString: string): {
  protocol?: ProxyProtocol;
  ip: string;
  port: number;
} | null => {
  try {
    // 嘗試解析完整 URL 格式
    if (proxyString.includes('://')) {
      const url = new URL(proxyString);
      const protocol = url.protocol.slice(0, -1) as ProxyProtocol;
      const ip = url.hostname;
      const port = parseInt(url.port, 10);
      
      if (isValidIP(ip) && isValidPort(port) && PROXY.PROTOCOLS.includes(protocol)) {
        return { protocol, ip, port };
      }
    } else {
      // 解析 ip:port 格式
      const [ip, portStr] = proxyString.split(':');
      const port = parseInt(portStr, 10);
      
      if (isValidIP(ip) && isValidPort(port)) {
        return { ip, port };
      }
    }
    
    return null;
  } catch {
    return null;
  }
};

/**
 * 格式化代理地址
 * @param ip IP 地址
 * @param port 端口號
 * @param protocol 協議（可選）
 * @returns 格式化後的代理地址
 */
export const formatProxyAddress = (
  ip: string,
  port: number,
  protocol?: ProxyProtocol
): string => {
  const address = `${ip}:${port}`;
  return protocol ? `${protocol}://${address}` : address;
};

/**
 * 獲取代理狀態顏色
 * @param status 代理狀態
 * @returns 狀態顏色
 */
export const getProxyStatusColor = (status: ProxyStatus): string => {
  switch (status) {
    case 'online':
      return '#22c55e'; // 綠色
    case 'offline':
      return '#ef4444'; // 紅色
    default:
      return '#6b7280'; // 灰色
  }
};

/**
 * 獲取速度等級
 * @param speed 速度（毫秒）
 * @returns 速度等級
 */
export const getSpeedLevel = (speed: number): 'fast' | 'medium' | 'slow' => {
  if (speed < 100) return 'fast';
  if (speed < 500) return 'medium';
  return 'slow';
};

/**
 * 獲取匿名等級顯示文字
 * @param anonymity 匿名等級
 * @returns 顯示文字
 */
export const getAnonymityText = (anonymity: AnonymityLevel): string => {
  switch (anonymity) {
    case 'elite':
      return '精英級';
    case 'anonymous':
      return '匿名級';
    case 'transparent':
      return '透明級';
    default:
      return anonymity;
  }
};

/**
 * 計算兩個日期之間的差異
 * @param date1 日期1
 * @param date2 日期2
 * @returns 差異（毫秒）
 */
export const dateDiff = (date1: Date | string, date2: Date | string): number => {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  return Math.abs(d1.getTime() - d2.getTime());
};

/**
 * 檢查是否為今天
 * @param date 日期
 * @returns 是否為今天
 */
export const isToday = (date: Date | string): boolean => {
  const today = new Date();
  const checkDate = new Date(date);
  
  return (
    today.getFullYear() === checkDate.getFullYear() &&
    today.getMonth() === checkDate.getMonth() &&
    today.getDate() === checkDate.getDate()
  );
};

/**
 * 檢查是否為本週
 * @param date 日期
 * @returns 是否為本週
 */
export const isThisWeek = (date: Date | string): boolean => {
  const today = new Date();
  const checkDate = new Date(date);
  
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay());
  startOfWeek.setHours(0, 0, 0, 0);
  
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  endOfWeek.setHours(23, 59, 59, 999);
  
  return checkDate >= startOfWeek && checkDate <= endOfWeek;
};

/**
 * 重試函數
 * @param fn 要重試的函數
 * @param retries 重試次數
 * @param delay 延遲時間（毫秒）
 * @returns Promise
 */
export const retry = async <T>(
  fn: () => Promise<T>,
  retries = 3,
  delayMs = 1000
): Promise<T> => {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0) {
      await delay(delayMs);
      return retry(fn, retries - 1, delayMs * 2); // 指數退避
    }
    throw error;
  }
};

/**
 * 安全的 JSON 解析
 * @param jsonString JSON 字串
 * @param defaultValue 預設值
 * @returns 解析結果
 */
export const safeJsonParse = <T>(
  jsonString: string,
  defaultValue: T
): T => {
  try {
    return JSON.parse(jsonString);
  } catch {
    return defaultValue;
  }
};

/**
 * 安全的 JSON 字串化
 * @param obj 物件
 * @param defaultValue 預設值
 * @returns JSON 字串
 */
export const safeJsonStringify = (
  obj: any,
  defaultValue = '{}'
): string => {
  try {
    return JSON.stringify(obj);
  } catch {
    return defaultValue;
  }
};

/**
 * 獲取物件的巢狀屬性值
 * @param obj 物件
 * @param path 屬性路徑（如：'user.profile.name'）
 * @param defaultValue 預設值
 * @returns 屬性值
 */
export const getNestedValue = (
  obj: any,
  path: string,
  defaultValue?: any
): any => {
  const keys = path.split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result == null || typeof result !== 'object') {
      return defaultValue;
    }
    result = result[key];
  }
  
  return result !== undefined ? result : defaultValue;
};

/**
 * 設定物件的巢狀屬性值
 * @param obj 物件
 * @param path 屬性路徑
 * @param value 值
 */
export const setNestedValue = (
  obj: any,
  path: string,
  value: any
): void => {
  const keys = path.split('.');
  const lastKey = keys.pop()!;
  let current = obj;
  
  for (const key of keys) {
    if (!(key in current) || typeof current[key] !== 'object') {
      current[key] = {};
    }
    current = current[key];
  }
  
  current[lastKey] = value;
};

/**
 * 創建可取消的 Promise
 * @param promise 原始 Promise
 * @returns 可取消的 Promise 和取消函數
 */
export const makeCancelable = <T>(promise: Promise<T>) => {
  let isCanceled = false;
  
  const wrappedPromise = new Promise<T>((resolve, reject) => {
    promise
      .then(value => {
        if (!isCanceled) {
          resolve(value);
        }
      })
      .catch(error => {
        if (!isCanceled) {
          reject(error);
        }
      });
  });
  
  return {
    promise: wrappedPromise,
    cancel: () => {
      isCanceled = true;
    },
  };
};