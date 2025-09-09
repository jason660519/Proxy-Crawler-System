/**
 * HTTP 服務層
 * 提供統一的 API 請求處理，包含錯誤處理、重試機制等
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import type { ApiResponse } from '../types';

// 從環境變數讀取配置
const getEnvVar = (key: string, defaultValue: string): string => {
  if (typeof import.meta !== 'undefined') {
    return (import.meta as any).env?.[key] || defaultValue;
  }
  return (window as any)?.[`__${key}__`] || defaultValue;
};

// 預設使用 Vite 開發代理，將 API 基底路徑設為 /api
const RAW_API_BASE_URL = getEnvVar('VITE_API_BASE_URL', '/api');
const RAW_ETL_BASE_URL = getEnvVar('VITE_ETL_BASE_URL', '/etl');

// 在開發環境（Vite dev server）強制走代理，以避免瀏覽器直連 localhost:8000 造成 CORS
const isDev = typeof import.meta !== 'undefined' && (import.meta as any).env?.DEV;
const runningOnVite = typeof window !== 'undefined' && /:5173$/.test(window.location.host);

const API_BASE_URL = (isDev || runningOnVite) ? '/api' : RAW_API_BASE_URL;
const ETL_BASE_URL = (isDev || runningOnVite) ? '/etl' : RAW_ETL_BASE_URL;
const REQUEST_TIMEOUT = parseInt(getEnvVar('VITE_REQUEST_TIMEOUT', '60000'));
const API_KEY = getEnvVar('VITE_API_KEY', '');

// 請求攔截器：添加通用標頭
const requestInterceptor = (config: any): any => {
  // 添加時間戳防止快取
  if (config.method === 'get') {
    config.params = {
      ...config.params,
      _t: Date.now()
    };
  }

  // 添加通用標頭
  config.headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
    ...config.headers
  };

  // 規範 URL：避免 baseURL 已含 /api 或 /etl 又傳入以 /api 或 /etl 開頭的路徑，導致 /api/api/xxx
  try {
    const base: string = config.baseURL || '';
    if (typeof config.url === 'string') {
      if (/\/api\/?$/.test(base) && config.url.startsWith('/api/')) {
        config.url = config.url.replace(/^\/api\//, '/');
      }
      if (/\/etl\/?$/.test(base) && config.url.startsWith('/etl/')) {
        config.url = config.url.replace(/^\/etl\//, '/');
      }
    }
  } catch {}

  return config;
};

// 回應攔截器：統一錯誤處理
const responseInterceptor = {
  onFulfilled: (response: AxiosResponse): AxiosResponse => {
    return response;
  },
  onRejected: (error: any): Promise<never> => {
    // 網路錯誤
    if (!error.response) {
      // axios 超時或中斷大多沒有 response
      if (error.code === 'ECONNABORTED' || /timeout/i.test(error.message)) {
        console.error('請求逾時:', error.message);
        return Promise.reject(new Error('請求逾時，請稍後再試'));
      }
      console.error('網路錯誤:', error.message);
      return Promise.reject(new Error('網路連線失敗，請檢查網路狀態'));
    }

    // HTTP 錯誤
    const { status, data } = error.response;
    let message = '請求失敗';

    switch (status) {
      case 400:
        message = data?.message || '請求參數錯誤';
        break;
      case 401:
        message = '未授權，請重新登入';
        break;
      case 403:
        message = '權限不足';
        break;
      case 404:
        message = '請求的資源不存在';
        break;
      case 429:
        message = '請求過於頻繁，請稍後再試';
        break;
      case 500:
        message = '伺服器內部錯誤';
        break;
      case 502:
      case 503:
      case 504:
        message = '服務暫時不可用，請稍後再試';
        break;
      default:
        message = data?.message || `請求失敗 (${status})`;
    }

    console.error(`API 錯誤 [${status}]:`, message, data);
    return Promise.reject(new Error(message));
  }
};

// 建立主 API 實例
export const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  // 添加 CORS 相關配置
  withCredentials: false,
  // 添加調試配置
  validateStatus: function (status) {
    return status >= 200 && status < 300;
  }
});

// 添加請求攔截器進行調試
http.interceptors.request.use(
  (config) => {
    console.log('API Request:', {
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL || ''}${config.url || ''}`,
      method: config.method
    });
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// 建立 ETL API 實例
export const etlHttp: AxiosInstance = axios.create({
  baseURL: ETL_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  // 添加 CORS 相關配置
  withCredentials: false,
  // 添加調試配置
  validateStatus: function (status) {
    return status >= 200 && status < 300;
  }
});

// 添加攔截器
[http, etlHttp].forEach(instance => {
  instance.interceptors.request.use(requestInterceptor);
  instance.interceptors.response.use(
    responseInterceptor.onFulfilled,
    responseInterceptor.onRejected
  );
});

// 重試機制
interface RetryConfig {
  retries?: number;
  retryDelay?: number;
  retryCondition?: (error: any) => boolean;
}

const defaultRetryConfig: RetryConfig = {
  retries: 3,
  retryDelay: 1000,
  retryCondition: (error) => {
    // 只對網路錯誤和 5xx 錯誤重試
    return !error.response || (error.response.status >= 500);
  }
};

/**
 * 帶重試機制的請求函數
 */
export async function requestWithRetry<T>(
  instance: AxiosInstance,
  config: AxiosRequestConfig,
  retryConfig: RetryConfig = {}
): Promise<AxiosResponse<T>> {
  const finalConfig = { ...defaultRetryConfig, ...retryConfig };
  let lastError: any;

  for (let attempt = 0; attempt <= finalConfig.retries!; attempt++) {
    try {
      return await instance.request<T>(config);
    } catch (error) {
      lastError = error;

      // 最後一次嘗試或不符合重試條件
      if (attempt === finalConfig.retries! || !finalConfig.retryCondition!(error)) {
        throw error;
      }

      // 等待後重試
      const delay = finalConfig.retryDelay! * Math.pow(2, attempt); // 指數退避
      console.warn(`請求失敗，${delay}ms 後重試 (${attempt + 1}/${finalConfig.retries})`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * 通用 API 請求方法
 */
export class ApiClient {
  private instance: AxiosInstance;
  
  constructor(instance: AxiosInstance) {
    this.instance = instance;
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await requestWithRetry<ApiResponse<T>>(this.instance, {
      method: 'GET',
      url,
      ...config
    });
    return (response.data.data || response.data) as T;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await requestWithRetry<ApiResponse<T>>(this.instance, {
      method: 'POST',
      url,
      data,
      ...config
    });
    return (response.data.data || response.data) as T;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await requestWithRetry<ApiResponse<T>>(this.instance, {
      method: 'PUT',
      url,
      data,
      ...config
    });
    return (response.data.data || response.data) as T;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await requestWithRetry<ApiResponse<T>>(this.instance, {
      method: 'PATCH',
      url,
      data,
      ...config
    });
    return (response.data.data || response.data) as T;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await requestWithRetry<ApiResponse<T>>(this.instance, {
      method: 'DELETE',
      url,
      ...config
    });
    return (response.data.data || response.data) as T;
  }
}

// 匯出 API 客戶端實例
export const apiClient = new ApiClient(http);
export const etlApiClient = new ApiClient(etlHttp);

// 預設匯出主 HTTP 實例
export default http;