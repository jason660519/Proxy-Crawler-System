/**
 * 驗證工具函數
 * 提供各種數據驗證功能
 */

/**
 * 驗證 URL 格式
 * @param url - 要驗證的 URL 字符串
 * @returns 是否為有效的 URL
 */
export function validateUrl(url: string): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  try {
    const urlObj = new URL(url);
    return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
  } catch {
    return false;
  }
}

/**
 * 驗證代理 URL 格式
 * @param url - 要驗證的代理 URL 字符串
 * @returns 是否為有效的代理 URL
 */
export function validateProxyUrl(url: string): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  try {
    const urlObj = new URL(url);
    const validProtocols = ['http:', 'https:', 'socks4:', 'socks5:'];
    return validProtocols.includes(urlObj.protocol);
  } catch {
    return false;
  }
}

/**
 * 驗證 IP 地址格式
 * @param ip - 要驗證的 IP 地址字符串
 * @returns 是否為有效的 IP 地址
 */
export function validateIpAddress(ip: string): boolean {
  if (!ip || typeof ip !== 'string') {
    return false;
  }

  const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
  
  return ipv4Regex.test(ip) || ipv6Regex.test(ip);
}

/**
 * 驗證端口號
 * @param port - 要驗證的端口號
 * @returns 是否為有效的端口號
 */
export function validatePort(port: number | string): boolean {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port;
  return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
}

/**
 * 驗證電子郵件格式
 * @param email - 要驗證的電子郵件地址
 * @returns 是否為有效的電子郵件格式
 */
export function validateEmail(email: string): boolean {
  if (!email || typeof email !== 'string') {
    return false;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 驗證密碼強度
 * @param password - 要驗證的密碼
 * @param minLength - 最小長度（預設 8）
 * @returns 密碼強度驗證結果
 */
export function validatePassword(
  password: string,
  minLength: number = 8
): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!password || typeof password !== 'string') {
    errors.push('密碼不能為空');
    return { isValid: false, errors };
  }

  if (password.length < minLength) {
    errors.push(`密碼長度至少需要 ${minLength} 個字符`);
  }

  if (!/[a-z]/.test(password)) {
    errors.push('密碼需要包含至少一個小寫字母');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('密碼需要包含至少一個大寫字母');
  }

  if (!/[0-9]/.test(password)) {
    errors.push('密碼需要包含至少一個數字');
  }

  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('密碼需要包含至少一個特殊字符');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * 驗證 JSON 格式
 * @param jsonString - 要驗證的 JSON 字符串
 * @returns 是否為有效的 JSON 格式
 */
export function validateJson(jsonString: string): boolean {
  if (!jsonString || typeof jsonString !== 'string') {
    return false;
  }

  try {
    JSON.parse(jsonString);
    return true;
  } catch {
    return false;
  }
}

/**
 * 驗證檔案大小
 * @param file - 要驗證的檔案
 * @param maxSizeInMB - 最大檔案大小（MB）
 * @returns 是否符合大小限制
 */
export function validateFileSize(file: File, maxSizeInMB: number): boolean {
  if (!file || !file.size) {
    return false;
  }

  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  return file.size <= maxSizeInBytes;
}

/**
 * 驗證檔案類型
 * @param file - 要驗證的檔案
 * @param allowedTypes - 允許的檔案類型陣列
 * @returns 是否為允許的檔案類型
 */
export function validateFileType(file: File, allowedTypes: string[]): boolean {
  if (!file || !file.type) {
    return false;
  }

  return allowedTypes.includes(file.type);
}