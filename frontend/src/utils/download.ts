/**
 * 下載工具函數
 * 
 * 提供各種文件下載功能，包括：
 * - 文本文件下載
 * - JSON 數據下載
 * - CSV 文件下載
 * - 二進制文件下載
 * - 批量下載
 */

// ============= 類型定義 =============

/**
 * 下載選項
 */
export interface DownloadOptions {
  /** 文件名 */
  filename?: string;
  /** MIME 類型 */
  mimeType?: string;
  /** 字符編碼 */
  encoding?: string;
}

/**
 * CSV 下載選項
 */
export interface CsvDownloadOptions extends DownloadOptions {
  /** 分隔符 */
  delimiter?: string;
  /** 是否包含標題行 */
  includeHeaders?: boolean;
  /** 自定義標題 */
  headers?: string[];
}

/**
 * 批量下載項目
 */
export interface DownloadItem {
  /** 文件名 */
  filename: string;
  /** 文件內容或 URL */
  content: string | Blob | ArrayBuffer;
  /** MIME 類型 */
  mimeType?: string;
}

// ============= 核心下載函數 =============

/**
 * 創建下載鏈接並觸發下載
 * 
 * @param blob 文件 Blob 對象
 * @param filename 文件名
 */
function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // 清理 URL 對象
  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 100);
}

/**
 * 通用文件下載函數
 * 
 * @param content 文件內容
 * @param options 下載選項
 */
export function downloadFile(
  content: string | Blob | ArrayBuffer,
  options: DownloadOptions = {}
): void {
  const {
    filename = 'download.txt',
    mimeType = 'text/plain',
    encoding = 'utf-8'
  } = options;
  
  let blob: Blob;
  
  if (content instanceof Blob) {
    blob = content;
  } else if (content instanceof ArrayBuffer) {
    blob = new Blob([content], { type: mimeType });
  } else {
    blob = new Blob([content], { type: `${mimeType};charset=${encoding}` });
  }
  
  triggerDownload(blob, filename);
}

// ============= 文本文件下載 =============

/**
 * 下載文本文件
 * 
 * @param text 文本內容
 * @param filename 文件名
 * @param encoding 字符編碼
 */
export function downloadText(
  text: string,
  filename: string = 'text.txt',
  encoding: string = 'utf-8'
): void {
  downloadFile(text, {
    filename,
    mimeType: 'text/plain',
    encoding
  });
}

/**
 * 下載 HTML 文件
 * 
 * @param html HTML 內容
 * @param filename 文件名
 */
export function downloadHtml(
  html: string,
  filename: string = 'document.html'
): void {
  downloadFile(html, {
    filename,
    mimeType: 'text/html',
    encoding: 'utf-8'
  });
}

/**
 * 下載 CSS 文件
 * 
 * @param css CSS 內容
 * @param filename 文件名
 */
export function downloadCss(
  css: string,
  filename: string = 'styles.css'
): void {
  downloadFile(css, {
    filename,
    mimeType: 'text/css',
    encoding: 'utf-8'
  });
}

/**
 * 下載 JavaScript 文件
 * 
 * @param js JavaScript 內容
 * @param filename 文件名
 */
export function downloadJavaScript(
  js: string,
  filename: string = 'script.js'
): void {
  downloadFile(js, {
    filename,
    mimeType: 'application/javascript',
    encoding: 'utf-8'
  });
}

// ============= JSON 數據下載 =============

/**
 * 下載 JSON 文件
 * 
 * @param data 要下載的數據對象
 * @param filename 文件名
 * @param pretty 是否格式化 JSON
 */
export function downloadJson(
  data: any,
  filename: string = 'data.json',
  pretty: boolean = true
): void {
  const jsonString = pretty 
    ? JSON.stringify(data, null, 2)
    : JSON.stringify(data);
    
  downloadFile(jsonString, {
    filename,
    mimeType: 'application/json',
    encoding: 'utf-8'
  });
}

/**
 * 下載 JSONL 文件（每行一個 JSON 對象）
 * 
 * @param dataArray 數據對象數組
 * @param filename 文件名
 */
export function downloadJsonLines(
  dataArray: any[],
  filename: string = 'data.jsonl'
): void {
  const jsonlString = dataArray
    .map(item => JSON.stringify(item))
    .join('\n');
    
  downloadFile(jsonlString, {
    filename,
    mimeType: 'application/x-jsonlines',
    encoding: 'utf-8'
  });
}

// ============= CSV 文件下載 =============

/**
 * 將數據轉換為 CSV 格式
 * 
 * @param data 數據數組
 * @param options CSV 選項
 * @returns CSV 字符串
 */
function arrayToCsv(
  data: any[],
  options: CsvDownloadOptions = {}
): string {
  const {
    delimiter = ',',
    includeHeaders = true,
    headers
  } = options;
  
  if (!data || data.length === 0) {
    return '';
  }
  
  const rows: string[] = [];
  
  // 獲取標題行
  const headerRow = headers || Object.keys(data[0]);
  
  if (includeHeaders) {
    rows.push(headerRow.map(escapeCSVField).join(delimiter));
  }
  
  // 添加數據行
  data.forEach(item => {
    const row = headerRow.map(key => {
      const value = item[key];
      return escapeCSVField(String(value ?? ''));
    });
    rows.push(row.join(delimiter));
  });
  
  return rows.join('\n');
}

/**
 * 轉義 CSV 字段
 * 
 * @param field 字段值
 * @returns 轉義後的字段值
 */
function escapeCSVField(field: string): string {
  // 如果字段包含逗號、引號或換行符，需要用引號包圍
  if (field.includes(',') || field.includes('"') || field.includes('\n')) {
    // 將字段中的引號轉義為雙引號
    const escaped = field.replace(/"/g, '""');
    return `"${escaped}"`;
  }
  return field;
}

/**
 * 下載 CSV 文件
 * 
 * @param data 數據數組
 * @param options CSV 下載選項
 */
export function downloadCsv(
  data: any[],
  options: CsvDownloadOptions = {}
): void {
  const {
    filename = 'data.csv',
    encoding = 'utf-8'
  } = options;
  
  const csvString = arrayToCsv(data, options);
  
  downloadFile(csvString, {
    filename,
    mimeType: 'text/csv',
    encoding
  });
}

/**
 * 下載 Excel 兼容的 CSV 文件（使用 BOM）
 * 
 * @param data 數據數組
 * @param options CSV 下載選項
 */
export function downloadExcelCsv(
  data: any[],
  options: CsvDownloadOptions = {}
): void {
  const {
    filename = 'data.csv'
  } = options;
  
  const csvString = arrayToCsv(data, options);
  
  // 添加 BOM 以確保 Excel 正確識別 UTF-8 編碼
  const bom = '\uFEFF';
  const csvWithBom = bom + csvString;
  
  downloadFile(csvWithBom, {
    filename,
    mimeType: 'text/csv',
    encoding: 'utf-8'
  });
}

// ============= 二進制文件下載 =============

/**
 * 下載二進制文件
 * 
 * @param data 二進制數據
 * @param filename 文件名
 * @param mimeType MIME 類型
 */
export function downloadBinary(
  data: ArrayBuffer | Uint8Array,
  filename: string,
  mimeType: string = 'application/octet-stream'
): void {
  const blob = new Blob([data], { type: mimeType });
  triggerDownload(blob, filename);
}

/**
 * 下載圖片文件
 * 
 * @param imageData 圖片數據（base64 或 ArrayBuffer）
 * @param filename 文件名
 * @param format 圖片格式
 */
export function downloadImage(
  imageData: string | ArrayBuffer,
  filename: string,
  format: 'png' | 'jpg' | 'jpeg' | 'gif' | 'webp' = 'png'
): void {
  let blob: Blob;
  
  if (typeof imageData === 'string') {
    // 處理 base64 數據
    const base64Data = imageData.replace(/^data:image\/[a-z]+;base64,/, '');
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    blob = new Blob([bytes], { type: `image/${format}` });
  } else {
    blob = new Blob([imageData], { type: `image/${format}` });
  }
  
  triggerDownload(blob, filename);
}

// ============= URL 下載 =============

/**
 * 從 URL 下載文件
 * 
 * @param url 文件 URL
 * @param filename 保存的文件名
 * @returns Promise
 */
export async function downloadFromUrl(
  url: string,
  filename?: string
): Promise<void> {
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    const finalFilename = filename || extractFilenameFromUrl(url) || 'download';
    
    triggerDownload(blob, finalFilename);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
}

/**
 * 從 URL 提取文件名
 * 
 * @param url URL 字符串
 * @returns 文件名或 null
 */
function extractFilenameFromUrl(url: string): string | null {
  try {
    const urlObj = new URL(url);
    const pathname = urlObj.pathname;
    const filename = pathname.split('/').pop();
    return filename && filename.includes('.') ? filename : null;
  } catch {
    return null;
  }
}

// ============= 批量下載 =============

/**
 * 批量下載文件（打包為 ZIP）
 * 注意：此功能需要額外的 ZIP 庫支持
 * 
 * @param items 下載項目數組
 * @param zipFilename ZIP 文件名
 */
export function downloadMultipleAsZip(
  items: DownloadItem[],
  zipFilename: string = 'files.zip'
): void {
  // 這裡需要使用 JSZip 或類似的庫
  // 由於沒有引入外部依賴，這裡提供一個基本實現
  console.warn(`批量下載功能需要 JSZip 庫支持，預期檔名：${zipFilename}`);
  console.log(`將下載 ${items.length} 個檔案`);
  
  // 作為替代方案，逐個下載文件
  items.forEach((item, index) => {
    setTimeout(() => {
      if (typeof item.content === 'string') {
        downloadFile(item.content, {
          filename: item.filename,
          mimeType: item.mimeType
        });
      } else {
        downloadFile(item.content, {
          filename: item.filename,
          mimeType: item.mimeType || 'application/octet-stream'
        });
      }
    }, index * 100); // 延遲下載避免瀏覽器阻止
  });
}

/**
 * 順序下載多個文件
 * 
 * @param items 下載項目數組
 * @param delay 下載間隔（毫秒）
 */
export function downloadMultipleSequentially(
  items: DownloadItem[],
  delay: number = 500
): void {
  items.forEach((item, index) => {
    setTimeout(() => {
      if (typeof item.content === 'string') {
        downloadFile(item.content, {
          filename: item.filename,
          mimeType: item.mimeType
        });
      } else {
        downloadFile(item.content, {
          filename: item.filename,
          mimeType: item.mimeType || 'application/octet-stream'
        });
      }
    }, index * delay);
  });
}

// ============= 工具函數 =============

/**
 * 檢查瀏覽器是否支持下載功能
 * 
 * @returns 是否支持
 */
export function isDownloadSupported(): boolean {
  return typeof document !== 'undefined' && 'createElement' in document;
}

/**
 * 獲取文件擴展名對應的 MIME 類型
 * 
 * @param filename 文件名
 * @returns MIME 類型
 */
export function getMimeTypeFromFilename(filename: string): string {
  const extension = filename.split('.').pop()?.toLowerCase();
  
  const mimeTypes: Record<string, string> = {
    'txt': 'text/plain',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'json': 'application/json',
    'csv': 'text/csv',
    'xml': 'application/xml',
    'pdf': 'application/pdf',
    'zip': 'application/zip',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'svg': 'image/svg+xml',
    'mp3': 'audio/mpeg',
    'mp4': 'video/mp4',
    'webm': 'video/webm'
  };
  
  return mimeTypes[extension || ''] || 'application/octet-stream';
}

// ============= 導出所有函數 =============

export default {
  downloadFile,
  downloadText,
  downloadHtml,
  downloadCss,
  downloadJavaScript,
  downloadJson,
  downloadJsonLines,
  downloadCsv,
  downloadExcelCsv,
  downloadBinary,
  downloadImage,
  downloadFromUrl,
  downloadMultipleAsZip,
  downloadMultipleSequentially,
  isDownloadSupported,
  getMimeTypeFromFilename
};