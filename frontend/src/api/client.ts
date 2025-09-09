/**
 * API 客戶端基礎配置
 * 
 * 提供統一的 HTTP 請求處理和錯誤管理
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';


/**
 * API 錯誤類別
 */
export class ApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly details?: any;

  constructor(message: string, status: number, code?: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/**
 * API 客戶端類別
 */
class ApiClient {
  private instance: AxiosInstance;
  private baseURL: string;

  constructor() {
    // 根據環境設置基礎 URL
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    
    this.instance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 秒超時
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    this.setupInterceptors();
  }

  /**
   * 設置請求和回應攔截器
   */
  private setupInterceptors(): void {
    // 請求攔截器
    this.instance.interceptors.request.use(
      (config) => {
        // 添加認證 token（如果存在）
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // 添加請求 ID 用於追蹤
        config.headers['X-Request-ID'] = this.generateRequestId();

        // 記錄請求（開發環境）
        if (process.env.NODE_ENV === 'development') {
          console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
            params: config.params,
            data: config.data
          });
        }

        return config;
      },
      (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
      }
    );

    // 回應攔截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        // 記錄回應（開發環境）
        if (process.env.NODE_ENV === 'development') {
          console.log(`[API Response] ${response.status} ${response.config.url}`, response.data);
        }

        return response;
      },
      (error: AxiosError) => {
        return this.handleError(error);
      }
    );
  }

  /**
   * 錯誤處理
   */
  private handleError(error: AxiosError): Promise<never> {
    let apiError: ApiError;

    if (error.response) {
      // 伺服器回應錯誤
      const { status, data } = error.response;
      const errorData = data as any;
      
      apiError = new ApiError(
        errorData?.message || errorData?.detail || `HTTP ${status} Error`,
        status,
        errorData?.code,
        errorData?.details
      );

      // 特殊狀態碼處理
      switch (status) {
        case 401:
          // 未授權，清除 token 並重定向到登入頁
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          break;
        case 403:
          // 禁止訪問
          console.warn('[API] Access forbidden:', errorData);
          break;
        case 429:
          // 請求過於頻繁
          console.warn('[API] Rate limit exceeded:', errorData);
          break;
        case 500:
          // 伺服器內部錯誤
          console.error('[API] Server error:', errorData);
          break;
      }
    } else if (error.request) {
      // 網路錯誤
      apiError = new ApiError(
        '網路連接失敗，請檢查您的網路連接',
        0,
        'NETWORK_ERROR'
      );
    } else {
      // 其他錯誤
      apiError = new ApiError(
        error.message || '未知錯誤',
        0,
        'UNKNOWN_ERROR'
      );
    }

    console.error('[API Error]', apiError);
    return Promise.reject(apiError);
  }

  /**
   * 生成請求 ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * GET 請求
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.get<T>(url, config);
  }

  /**
   * POST 請求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.post<T>(url, data, config);
  }

  /**
   * PUT 請求
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.put<T>(url, data, config);
  }

  /**
   * PATCH 請求
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.patch<T>(url, data, config);
  }

  /**
   * DELETE 請求
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.delete<T>(url, config);
  }

  /**
   * 上傳檔案
   */
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.instance.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      }
    });
  }

  /**
   * 下載檔案
   */
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob'
    });

    // 建立下載連結
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  /**
   * 設置認證 token
   */
  setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
    this.instance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  /**
   * 清除認證 token
   */
  clearAuthToken(): void {
    localStorage.removeItem('auth_token');
    delete this.instance.defaults.headers.common['Authorization'];
  }

  /**
   * 獲取基礎 URL
   */
  getBaseURL(): string {
    return this.baseURL;
  }

  /**
   * 設置基礎 URL
   */
  setBaseURL(baseURL: string): void {
    this.baseURL = baseURL;
    this.instance.defaults.baseURL = baseURL;
  }

  /**
   * 健康檢查
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health');
      return true;
    } catch (error) {
      return false;
    }
  }
}

// 導出單例實例
export const apiClient = new ApiClient();
export default apiClient;

// 導出類型