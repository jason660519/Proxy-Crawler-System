/**
 * URL2Parquet API 封裝
 * 
 * 提供 URL2Parquet 相關的 API 調用功能，包括：
 * - 任務創建和管理
 * - 文件下載
 * - 重定向處理
 * - 本地文件管理
 */

import { apiClient } from './client';

// ============= 類型定義 =============

export interface CreateJobRequest {
  urls: string[];
  engine?: string;
  output_formats?: string[];
  obey_robots_txt?: boolean;
  timeout_seconds?: number;
  max_concurrency?: number;
  work_dir?: string;
}

export interface JobResult {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'redirected';
  result?: {
    files: FileInfo[];
  };
  urls?: string[];
  error?: string;
  redirects?: RedirectInfo[];
  message?: string;
}

export interface FileInfo {
  format: string;
  path: string;
  size: number;
}

export interface RedirectInfo {
  url: string;
  status: 'redirected';
  original_url: string;
  final_url: string;
  message: string;
}

export interface LocalMarkdownFile {
  filename: string;
  size: number;
  modified: number;
}

export interface LocalMarkdownContent {
  filename: string;
  content: string;
  size: number;
}

// ============= API 函數 =============

/**
 * 創建 URL2Parquet 轉換任務
 */
export async function createJob(request: CreateJobRequest): Promise<JobResult> {
  try {
    const response = await apiClient.post<JobResult>('/api/url2parquet/jobs', {
      urls: request.urls,
      engine: request.engine || 'smart',
      output_formats: request.output_formats || ['md', 'json', 'parquet'],
      obey_robots_txt: request.obey_robots_txt ?? true,
      timeout_seconds: request.timeout_seconds || 20,
      max_concurrency: request.max_concurrency || 4,
      work_dir: request.work_dir || 'data/url2parquet'
    });

    return response.data;
  } catch (error) {
    console.error('創建任務失敗:', error);
    throw error;
  }
}

/**
 * 獲取任務狀態
 */
export async function getJob(jobId: string): Promise<JobResult> {
  try {
    const response = await apiClient.get<JobResult>(`/api/url2parquet/jobs/${jobId}`);
    return response.data;
  } catch (error) {
    console.error('獲取任務狀態失敗:', error);
    throw error;
  }
}

/**
 * 獲取任務文件列表
 */
export async function getJobFiles(jobId: string): Promise<{ files: FileInfo[] }> {
  try {
    const response = await apiClient.get<{ files: FileInfo[] }>(`/api/url2parquet/jobs/${jobId}/download`);
    return response.data;
  } catch (error) {
    console.error('獲取文件列表失敗:', error);
    throw error;
  }
}

/**
 * 獲取特定格式的文件內容
 */
export async function getFileContent(jobId: string, format: string): Promise<{
  format: string;
  content: string;
  size: number;
}> {
  try {
    const response = await apiClient.get<{
      format: string;
      content: string;
      size: number;
    }>(`/api/url2parquet/jobs/${jobId}/files/${format}`);
    return response.data;
  } catch (error) {
    console.error('獲取文件內容失敗:', error);
    throw error;
  }
}

/**
 * 下載特定格式的文件
 */
export async function downloadFile(jobId: string, format: string, filename?: string): Promise<void> {
  try {
    await apiClient.download(`/api/url2parquet/jobs/${jobId}/files/${format}/download`, filename);
  } catch (error) {
    console.error('下載文件失敗:', error);
    throw error;
  }
}

/**
 * 確認重定向並重新處理
 */
export async function confirmRedirect(jobId: string, redirectUrls: string[]): Promise<JobResult> {
  try {
    const response = await apiClient.post<JobResult>(`/api/url2parquet/jobs/${jobId}/confirm-redirect`, redirectUrls);
    return response.data;
  } catch (error) {
    console.error('確認重定向失敗:', error);
    throw error;
  }
}

/**
 * 獲取本地 Markdown 文件列表
 */
export async function getLocalMarkdownFiles(workDir?: string, limit: number = 50): Promise<{ files: LocalMarkdownFile[] }> {
  try {
    const params = new URLSearchParams();
    if (workDir) params.append('work_dir', workDir);
    params.append('limit', limit.toString());
    
    const response = await apiClient.get<{ files: LocalMarkdownFile[] }>(`/api/url2parquet/local-md?${params}`);
    return response.data;
  } catch (error) {
    console.error('獲取本地文件列表失敗:', error);
    throw error;
  }
}

/**
 * 讀取本地 Markdown 文件內容
 */
export async function getLocalMarkdownContent(filename: string, workDir?: string): Promise<LocalMarkdownContent> {
  try {
    const params = new URLSearchParams();
    params.append('filename', filename);
    if (workDir) params.append('work_dir', workDir);
    
    const response = await apiClient.get<LocalMarkdownContent>(`/api/url2parquet/local-md/content?${params}`);
    return response.data;
  } catch (error) {
    console.error('讀取本地文件內容失敗:', error);
    throw error;
  }
}

// ============= 輪詢工具 =============

/**
 * 輪詢任務狀態直到完成
 */
export async function pollJobUntilComplete(
  jobId: string,
  onProgress?: (job: JobResult) => void,
  options: {
    interval?: number;
    timeout?: number;
    maxAttempts?: number;
  } = {}
): Promise<JobResult> {
  const {
    interval = 2000, // 2秒
    timeout = 60000, // 60秒
    maxAttempts = 30 // 最多30次嘗試
  } = options;

  const startTime = Date.now();
  let attempts = 0;

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        attempts++;
        const job = await getJob(jobId);
        
        if (onProgress) {
          onProgress(job);
        }

        // 檢查是否完成
        if (job.status === 'completed' || job.status === 'failed') {
          resolve(job);
          return;
        }

        // 檢查超時
        if (Date.now() - startTime > timeout) {
          reject(new Error('輪詢超時'));
          return;
        }

        // 檢查最大嘗試次數
        if (attempts >= maxAttempts) {
          reject(new Error('達到最大輪詢次數'));
          return;
        }

        // 繼續輪詢
        setTimeout(poll, interval);
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
}

/**
 * 輪詢文件列表直到有文件生成
 */
export async function pollJobFilesUntilReady(
  jobId: string,
  onProgress?: (files: FileInfo[]) => void,
  options: {
    interval?: number;
    timeout?: number;
    maxAttempts?: number;
  } = {}
): Promise<FileInfo[]> {
  const {
    interval = 2000, // 2秒
    timeout = 60000, // 60秒
    maxAttempts = 30 // 最多30次嘗試
  } = options;

  const startTime = Date.now();
  let attempts = 0;

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        attempts++;
        const { files } = await getJobFiles(jobId);
        
        if (onProgress) {
          onProgress(files);
        }

        // 檢查是否有文件
        if (files && files.length > 0) {
          resolve(files);
          return;
        }

        // 檢查超時
        if (Date.now() - startTime > timeout) {
          reject(new Error('輪詢文件超時'));
          return;
        }

        // 檢查最大嘗試次數
        if (attempts >= maxAttempts) {
          reject(new Error('達到最大輪詢次數'));
          return;
        }

        // 繼續輪詢
        setTimeout(poll, interval);
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
}

// ============= 批量操作 =============

/**
 * 批量下載任務的所有文件
 */
export async function downloadAllFiles(jobId: string, files: FileInfo[]): Promise<void> {
  const downloadPromises = files.map(file => 
    downloadFile(jobId, file.format, `${file.format}_${jobId}.${file.format}`)
  );
  
  await Promise.allSettled(downloadPromises);
}

/**
 * 批量獲取任務的所有文件內容
 */
export async function getAllFileContents(jobId: string, files: FileInfo[]): Promise<Record<string, string>> {
  const contentPromises = files.map(async file => {
    try {
      const content = await getFileContent(jobId, file.format);
      return { format: file.format, content: content.content };
    } catch (error) {
      console.warn(`獲取 ${file.format} 文件內容失敗:`, error);
      return { format: file.format, content: '' };
    }
  });

  const results = await Promise.allSettled(contentPromises);
  const contents: Record<string, string> = {};

  results.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      contents[result.value.format] = result.value.content;
    }
  });

  return contents;
}

// ============= 錯誤處理 =============

/**
 * 檢查是否為重定向響應
 */
export function isRedirectResponse(job: JobResult): boolean {
  return job.status === 'redirected' && Array.isArray(job.redirects) && job.redirects.length > 0;
}

/**
 * 檢查任務是否完成
 */
export function isJobComplete(job: JobResult): boolean {
  return job.status === 'completed' || job.status === 'failed';
}

/**
 * 檢查任務是否成功
 */
export function isJobSuccessful(job: JobResult): boolean {
  return job.status === 'completed' && job.result && job.result.files && job.result.files.length > 0;
}

// ============= 默認配置 =============

export const DEFAULT_JOB_CONFIG: Partial<CreateJobRequest> = {
  engine: 'smart',
  output_formats: ['md', 'json', 'parquet'],
  obey_robots_txt: true,
  timeout_seconds: 20,
  max_concurrency: 4,
  work_dir: 'data/url2parquet'
};

export const DEFAULT_POLLING_CONFIG = {
  interval: 2000,
  timeout: 60000,
  maxAttempts: 30
};
