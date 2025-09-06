import { QueryClient } from '@tanstack/react-query';

/**
 * API 基礎配置
 */
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 30000, // 30 秒
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 秒
} as const;

/**
 * HTTP 狀態碼常數
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
} as const;

/**
 * API 錯誤類型
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message?: string,
    public data?: any
  ) {
    super(message || `API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

/**
 * 網路錯誤類型
 */
export class NetworkError extends Error {
  constructor(message: string, public originalError?: Error) {
    super(message);
    this.name = 'NetworkError';
  }
}

/**
 * 請求配置介面
 */
export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  signal?: AbortSignal;
}

/**
 * API 回應介面
 */
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Headers;
}

/**
 * 分頁回應介面
 */
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

/**
 * 代理節點介面
 */
export interface ProxyNode {
  id: string;
  ip: string;
  port: number;
  protocol: 'http' | 'https' | 'socks4' | 'socks5';
  country?: string;
  city?: string;
  anonymity: 'elite' | 'anonymous' | 'transparent';
  speed: number; // ms
  uptime: number; // percentage
  lastChecked: string; // ISO date string
  isOnline: boolean;
  source: string;
  tags?: string[];
}

/**
 * 代理統計介面
 */
export interface ProxyStats {
  total: number;
  online: number;
  offline: number;
  byCountry: Record<string, number>;
  byProtocol: Record<string, number>;
  byAnonymity: Record<string, number>;
  averageSpeed: number;
  averageUptime: number;
}

/**
 * 系統狀態介面
 */
export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  version: string;
  lastUpdate: string;
  services: {
    database: 'up' | 'down';
    crawler: 'up' | 'down';
    validator: 'up' | 'down';
  };
}

/**
 * 建立帶有重試機制的 fetch 函數
 */
async function fetchWithRetry(
  url: string,
  config: RequestConfig = {},
  attempt = 1
): Promise<Response> {
  const {
    method = 'GET',
    headers = {},
    body,
    timeout = API_CONFIG.TIMEOUT,
    retries = API_CONFIG.RETRY_ATTEMPTS,
    retryDelay = API_CONFIG.RETRY_DELAY,
    signal,
  } = config;

  // 建立 AbortController 用於超時控制
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // 合併 signal
  const combinedSignal = signal
    ? (() => {
        const combinedController = new AbortController();
        signal.addEventListener('abort', () => combinedController.abort());
        controller.signal.addEventListener('abort', () => combinedController.abort());
        return combinedController.signal;
      })()
    : controller.signal;

  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: combinedSignal,
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    // 如果是中止錯誤且不是超時，直接拋出
    if (error instanceof Error && error.name === 'AbortError' && signal?.aborted) {
      throw error;
    }

    // 如果還有重試次數，進行重試
    if (attempt < retries) {
      await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
      return fetchWithRetry(url, config, attempt + 1);
    }

    // 包裝網路錯誤
    if (error instanceof Error) {
      throw new NetworkError(
        `網路請求失敗: ${error.message}`,
        error
      );
    }

    throw error;
  }
}

/**
 * 處理 API 回應
 */
async function handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
  const { status, statusText, headers } = response;

  // 檢查回應狀態
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      // 如果無法解析 JSON，使用狀態文字
    }

    throw new ApiError(
      status,
      statusText,
      errorData?.message || errorData?.error || `HTTP ${status}: ${statusText}`,
      errorData
    );
  }

  // 解析回應內容
  let data: T;
  const contentType = headers.get('content-type');

  if (contentType?.includes('application/json')) {
    data = await response.json();
  } else if (contentType?.includes('text/')) {
    data = (await response.text()) as unknown as T;
  } else {
    data = (await response.blob()) as unknown as T;
  }

  return {
    data,
    status,
    statusText,
    headers,
  };
}

/**
 * API 客戶端類別
 */
export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl = API_CONFIG.BASE_URL, defaultHeaders: Record<string, string> = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // 移除尾隨斜線
    this.defaultHeaders = defaultHeaders;
  }

  /**
   * 設定預設標頭
   */
  setDefaultHeaders(headers: Record<string, string>): void {
    this.defaultHeaders = { ...this.defaultHeaders, ...headers };
  }

  /**
   * 移除預設標頭
   */
  removeDefaultHeader(key: string): void {
    delete this.defaultHeaders[key];
  }

  /**
   * 建立完整的 URL
   */
  private createUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${this.baseUrl}${cleanEndpoint}`;
  }

  /**
   * 通用請求方法
   */
  async request<T = any>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = this.createUrl(endpoint);
    const mergedConfig: RequestConfig = {
      ...config,
      headers: {
        ...this.defaultHeaders,
        ...config.headers,
      },
    };

    const response = await fetchWithRetry(url, mergedConfig);
    return handleResponse<T>(response);
  }

  /**
   * GET 請求
   */
  async get<T = any>(
    endpoint: string,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST 請求
   */
  async post<T = any>(
    endpoint: string,
    body?: any,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body });
  }

  /**
   * PUT 請求
   */
  async put<T = any>(
    endpoint: string,
    body?: any,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body });
  }

  /**
   * DELETE 請求
   */
  async delete<T = any>(
    endpoint: string,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * PATCH 請求
   */
  async patch<T = any>(
    endpoint: string,
    body?: any,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PATCH', body });
  }
}

/**
 * 預設 API 客戶端實例
 */
export const apiClient = new ApiClient();

/**
 * 代理相關的 API 方法
 */
export const proxyApi = {
  /**
   * 獲取代理列表
   */
  getProxies: async (params?: {
    page?: number;
    limit?: number;
    country?: string;
    protocol?: string;
    anonymity?: string;
    status?: 'online' | 'offline';
    search?: string;
  }): Promise<PaginatedResponse<ProxyNode>> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value));
        }
      });
    }

    const endpoint = `/api/proxies${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    const response = await apiClient.get<PaginatedResponse<ProxyNode>>(endpoint);
    return response.data;
  },

  /**
   * 獲取單個代理詳情
   */
  getProxy: async (id: string): Promise<ProxyNode> => {
    const response = await apiClient.get<ProxyNode>(`/api/proxies/${id}`);
    return response.data;
  },

  /**
   * 測試代理
   */
  testProxy: async (id: string): Promise<{ success: boolean; speed: number; error?: string }> => {
    const response = await apiClient.post<{ success: boolean; speed: number; error?: string }>(
      `/api/proxies/${id}/test`
    );
    return response.data;
  },

  /**
   * 批量測試代理
   */
  testProxies: async (ids: string[]): Promise<Record<string, { success: boolean; speed: number; error?: string }>> => {
    const response = await apiClient.post<Record<string, { success: boolean; speed: number; error?: string }>>(
      '/api/proxies/test-batch',
      { ids }
    );
    return response.data;
  },

  /**
   * 獲取代理統計
   */
  getStats: async (): Promise<ProxyStats> => {
    const response = await apiClient.get<ProxyStats>('/api/proxies/stats');
    return response.data;
  },

  /**
   * 刷新代理數據
   */
  refreshProxies: async (): Promise<{ message: string; count: number }> => {
    const response = await apiClient.post<{ message: string; count: number }>('/api/proxies/refresh');
    return response.data;
  },
};

/**
 * 系統相關的 API 方法
 */
export const systemApi = {
  /**
   * 獲取系統狀態
   */
  getStatus: async (): Promise<SystemStatus> => {
    const response = await apiClient.get<SystemStatus>('/api/system/status');
    return response.data;
  },

  /**
   * 獲取系統健康檢查
   */
  healthCheck: async (): Promise<{ status: 'ok' | 'error'; timestamp: string }> => {
    const response = await apiClient.get<{ status: 'ok' | 'error'; timestamp: string }>('/api/health');
    return response.data;
  },
};

/**
 * React Query 配置
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 分鐘
      gcTime: 10 * 60 * 1000, // 10 分鐘
      retry: (failureCount, error) => {
        // 對於 4xx 錯誤不重試
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: (failureCount, error) => {
        // 對於 4xx 錯誤不重試
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
    },
  },
});

/**
 * React Query 查詢鍵工廠
 */
export const queryKeys = {
  // 代理相關
  proxies: {
    all: ['proxies'] as const,
    lists: () => [...queryKeys.proxies.all, 'list'] as const,
    list: (params?: any) => [...queryKeys.proxies.lists(), params] as const,
    details: () => [...queryKeys.proxies.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.proxies.details(), id] as const,
    stats: () => [...queryKeys.proxies.all, 'stats'] as const,
  },
  // 系統相關
  system: {
    all: ['system'] as const,
    status: () => [...queryKeys.system.all, 'status'] as const,
    health: () => [...queryKeys.system.all, 'health'] as const,
  },
} as const;

/**
 * 錯誤處理工具
 */
export const errorUtils = {
  /**
   * 判斷是否為 API 錯誤
   */
  isApiError: (error: unknown): error is ApiError => {
    return error instanceof ApiError;
  },

  /**
   * 判斷是否為網路錯誤
   */
  isNetworkError: (error: unknown): error is NetworkError => {
    return error instanceof NetworkError;
  },

  /**
   * 獲取錯誤訊息
   */
  getErrorMessage: (error: unknown): string => {
    if (error instanceof ApiError) {
      return error.message;
    }
    if (error instanceof NetworkError) {
      return error.message;
    }
    if (error instanceof Error) {
      return error.message;
    }
    return '未知錯誤';
  },

  /**
   * 獲取使用者友好的錯誤訊息
   */
  getUserFriendlyMessage: (error: unknown): string => {
    if (error instanceof ApiError) {
      switch (error.status) {
        case HTTP_STATUS.BAD_REQUEST:
          return '請求參數錯誤，請檢查輸入內容';
        case HTTP_STATUS.UNAUTHORIZED:
          return '未授權，請重新登入';
        case HTTP_STATUS.FORBIDDEN:
          return '權限不足，無法執行此操作';
        case HTTP_STATUS.NOT_FOUND:
          return '請求的資源不存在';
        case HTTP_STATUS.INTERNAL_SERVER_ERROR:
          return '伺服器內部錯誤，請稍後再試';
        case HTTP_STATUS.BAD_GATEWAY:
          return '閘道錯誤，請稍後再試';
        case HTTP_STATUS.SERVICE_UNAVAILABLE:
          return '服務暫時不可用，請稍後再試';
        default:
          return `伺服器錯誤 (${error.status}): ${error.statusText}`;
      }
    }
    if (error instanceof NetworkError) {
      return '網路連線錯誤，請檢查網路設定';
    }
    return '發生未知錯誤，請稍後再試';
  },
};