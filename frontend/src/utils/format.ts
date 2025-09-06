/**
 * 格式化工具函數集合
 * 提供日期、數字、文字、檔案大小等格式化功能
 */

/**
 * 日期格式化選項
 */
export interface DateFormatOptions {
  locale?: string;
  timeZone?: string;
  format?: 'full' | 'long' | 'medium' | 'short' | 'relative' | 'custom';
  customFormat?: Intl.DateTimeFormatOptions;
}

/**
 * 數字格式化選項
 */
export interface NumberFormatOptions {
  locale?: string;
  style?: 'decimal' | 'currency' | 'percent' | 'unit';
  currency?: string;
  unit?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  notation?: 'standard' | 'scientific' | 'engineering' | 'compact';
}

/**
 * 日期格式化工具
 */
export const dateFormat = {
  /**
   * 格式化日期
   * @param date 日期物件、時間戳或日期字串
   * @param options 格式化選項
   * @returns 格式化後的日期字串
   */
  format: (
    date: Date | number | string,
    options: DateFormatOptions = {}
  ): string => {
    const {
      locale = 'zh-TW',
      timeZone = 'Asia/Taipei',
      format = 'medium',
      customFormat,
    } = options;

    const dateObj = new Date(date);
    
    if (isNaN(dateObj.getTime())) {
      return '無效日期';
    }

    if (format === 'relative') {
      return dateFormat.relative(dateObj, { locale });
    }

    if (format === 'custom' && customFormat) {
      return new Intl.DateTimeFormat(locale, {
        timeZone,
        ...customFormat,
      }).format(dateObj);
    }

    const formatOptions: Record<string, Intl.DateTimeFormatOptions> = {
      full: {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      },
      long: {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      },
      medium: {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      },
      short: {
        year: '2-digit',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      },
    };

    return new Intl.DateTimeFormat(locale, {
      timeZone,
      ...formatOptions[format],
    }).format(dateObj);
  },

  /**
   * 相對時間格式化
   * @param date 日期
   * @param options 選項
   * @returns 相對時間字串（如：「2 小時前」）
   */
  relative: (
    date: Date | number | string,
    options: { locale?: string } = {}
  ): string => {
    const { locale = 'zh-TW' } = options;
    const dateObj = new Date(date);
    const now = new Date();
    const diffMs = now.getTime() - dateObj.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    const diffWeek = Math.floor(diffDay / 7);
    const diffMonth = Math.floor(diffDay / 30);
    const diffYear = Math.floor(diffDay / 365);

    if (diffSec < 60) {
      return '剛剛';
    } else if (diffMin < 60) {
      return `${diffMin} 分鐘前`;
    } else if (diffHour < 24) {
      return `${diffHour} 小時前`;
    } else if (diffDay < 7) {
      return `${diffDay} 天前`;
    } else if (diffWeek < 4) {
      return `${diffWeek} 週前`;
    } else if (diffMonth < 12) {
      return `${diffMonth} 個月前`;
    } else {
      return `${diffYear} 年前`;
    }
  },

  /**
   * 格式化為 ISO 字串
   */
  toISOString: (date: Date | number | string): string => {
    return new Date(date).toISOString();
  },

  /**
   * 格式化為本地日期字串
   */
  toLocaleDateString: (
    date: Date | number | string,
    locale = 'zh-TW'
  ): string => {
    return new Date(date).toLocaleDateString(locale);
  },

  /**
   * 格式化為本地時間字串
   */
  toLocaleTimeString: (
    date: Date | number | string,
    locale = 'zh-TW'
  ): string => {
    return new Date(date).toLocaleTimeString(locale);
  },

  /**
   * 格式化持續時間（毫秒轉為可讀格式）
   */
  duration: (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days} 天 ${hours % 24} 小時`;
    } else if (hours > 0) {
      return `${hours} 小時 ${minutes % 60} 分鐘`;
    } else if (minutes > 0) {
      return `${minutes} 分鐘 ${seconds % 60} 秒`;
    } else {
      return `${seconds} 秒`;
    }
  },
};

/**
 * 數字格式化工具
 */
export const numberFormat = {
  /**
   * 格式化數字
   */
  format: (
    number: number,
    options: NumberFormatOptions = {}
  ): string => {
    const {
      locale = 'zh-TW',
      style = 'decimal',
      currency = 'TWD',
      unit,
      minimumFractionDigits,
      maximumFractionDigits,
      notation = 'standard',
    } = options;

    const formatOptions: Intl.NumberFormatOptions = {
      style,
      notation,
    };

    if (style === 'currency') {
      formatOptions.currency = currency;
    }

    if (style === 'unit' && unit) {
      formatOptions.unit = unit;
    }

    if (minimumFractionDigits !== undefined) {
      formatOptions.minimumFractionDigits = minimumFractionDigits;
    }

    if (maximumFractionDigits !== undefined) {
      formatOptions.maximumFractionDigits = maximumFractionDigits;
    }

    return new Intl.NumberFormat(locale, formatOptions).format(number);
  },

  /**
   * 格式化百分比
   */
  percent: (number: number, decimals = 1): string => {
    return numberFormat.format(number / 100, {
      style: 'percent',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  },

  /**
   * 格式化貨幣
   */
  currency: (number: number, currency = 'TWD'): string => {
    return numberFormat.format(number, {
      style: 'currency',
      currency,
    });
  },

  /**
   * 格式化為緊湊形式（如：1.2K, 3.4M）
   */
  compact: (number: number): string => {
    return numberFormat.format(number, {
      notation: 'compact',
      maximumFractionDigits: 1,
    });
  },

  /**
   * 格式化檔案大小
   */
  fileSize: (bytes: number, decimals = 2): string => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
  },

  /**
   * 格式化速度（毫秒）
   */
  speed: (ms: number): string => {
    if (ms < 1000) {
      return `${Math.round(ms)} ms`;
    } else {
      return `${(ms / 1000).toFixed(2)} s`;
    }
  },

  /**
   * 格式化延遲等級
   */
  latency: (ms: number): { text: string; level: 'fast' | 'medium' | 'slow' } => {
    if (ms < 100) {
      return { text: `${Math.round(ms)} ms`, level: 'fast' };
    } else if (ms < 500) {
      return { text: `${Math.round(ms)} ms`, level: 'medium' };
    } else {
      return { text: `${Math.round(ms)} ms`, level: 'slow' };
    }
  },
};

/**
 * 文字格式化工具
 */
export const textFormat = {
  /**
   * 截斷文字
   */
  truncate: (text: string, maxLength: number, suffix = '...'): string => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength - suffix.length) + suffix;
  },

  /**
   * 首字母大寫
   */
  capitalize: (text: string): string => {
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  },

  /**
   * 標題格式（每個單字首字母大寫）
   */
  titleCase: (text: string): string => {
    return text
      .split(' ')
      .map(word => textFormat.capitalize(word))
      .join(' ');
  },

  /**
   * 駝峰命名轉換
   */
  camelCase: (text: string): string => {
    return text
      .replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) => {
        return index === 0 ? word.toLowerCase() : word.toUpperCase();
      })
      .replace(/\s+/g, '');
  },

  /**
   * 蛇形命名轉換
   */
  snakeCase: (text: string): string => {
    return text
      .replace(/\W+/g, ' ')
      .split(/ |\s/)
      .map(word => word.toLowerCase())
      .join('_');
  },

  /**
   * 短橫線命名轉換
   */
  kebabCase: (text: string): string => {
    return text
      .replace(/\W+/g, ' ')
      .split(/ |\s/)
      .map(word => word.toLowerCase())
      .join('-');
  },

  /**
   * 移除 HTML 標籤
   */
  stripHtml: (html: string): string => {
    return html.replace(/<[^>]*>/g, '');
  },

  /**
   * 轉義 HTML 字符
   */
  escapeHtml: (text: string): string => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  /**
   * 反轉義 HTML 字符
   */
  unescapeHtml: (html: string): string => {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || div.innerText || '';
  },

  /**
   * 格式化電話號碼
   */
  phone: (phone: string): string => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
      return cleaned.replace(/(\d{4})(\d{3})(\d{3})/, '$1-$2-$3');
    }
    return phone;
  },

  /**
   * 格式化信用卡號
   */
  creditCard: (cardNumber: string): string => {
    const cleaned = cardNumber.replace(/\D/g, '');
    return cleaned.replace(/(\d{4})(?=\d)/g, '$1 ');
  },

  /**
   * 遮罩敏感資訊
   */
  mask: (text: string, visibleStart = 2, visibleEnd = 2, maskChar = '*'): string => {
    if (text.length <= visibleStart + visibleEnd) {
      return text;
    }
    const start = text.slice(0, visibleStart);
    const end = text.slice(-visibleEnd);
    const middle = maskChar.repeat(text.length - visibleStart - visibleEnd);
    return start + middle + end;
  },
};

/**
 * URL 格式化工具
 */
export const urlFormat = {
  /**
   * 格式化 URL
   */
  format: (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.toString();
    } catch {
      return url;
    }
  },

  /**
   * 獲取域名
   */
  getDomain: (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch {
      return url;
    }
  },

  /**
   * 獲取路徑
   */
  getPath: (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname;
    } catch {
      return '';
    }
  },

  /**
   * 添加查詢參數
   */
  addParams: (url: string, params: Record<string, string>): string => {
    try {
      const urlObj = new URL(url);
      Object.entries(params).forEach(([key, value]) => {
        urlObj.searchParams.set(key, value);
      });
      return urlObj.toString();
    } catch {
      return url;
    }
  },

  /**
   * 移除查詢參數
   */
  removeParams: (url: string, paramNames: string[]): string => {
    try {
      const urlObj = new URL(url);
      paramNames.forEach(name => {
        urlObj.searchParams.delete(name);
      });
      return urlObj.toString();
    } catch {
      return url;
    }
  },
};

/**
 * 代理相關格式化工具
 */
export const proxyFormat = {
  /**
   * 格式化代理地址
   */
  address: (ip: string, port: number, protocol?: string): string => {
    const protocolPrefix = protocol ? `${protocol}://` : '';
    return `${protocolPrefix}${ip}:${port}`;
  },

  /**
   * 格式化匿名等級
   */
  anonymity: (level: string): string => {
    const levels: Record<string, string> = {
      elite: '精英級',
      anonymous: '匿名級',
      transparent: '透明級',
    };
    return levels[level] || level;
  },

  /**
   * 格式化協議類型
   */
  protocol: (protocol: string): string => {
    return protocol.toUpperCase();
  },

  /**
   * 格式化國家代碼
   */
  country: (countryCode: string): string => {
    // 這裡可以添加國家代碼到中文名稱的映射
    const countries: Record<string, string> = {
      US: '美國',
      CN: '中國',
      JP: '日本',
      KR: '韓國',
      TW: '台灣',
      HK: '香港',
      SG: '新加坡',
      // 可以添加更多國家
    };
    return countries[countryCode] || countryCode;
  },

  /**
   * 格式化上線時間百分比
   */
  uptime: (percentage: number): string => {
    return numberFormat.percent(percentage, 1);
  },

  /**
   * 格式化代理狀態
   */
  status: (isOnline: boolean): { text: string; variant: 'online' | 'offline' } => {
    return isOnline
      ? { text: '線上', variant: 'online' }
      : { text: '離線', variant: 'offline' };
  },
};

/**
 * 驗證工具
 */
export const validation = {
  /**
   * 驗證 IP 地址
   */
  isValidIP: (ip: string): boolean => {
    const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
    return ipv4Regex.test(ip) || ipv6Regex.test(ip);
  },

  /**
   * 驗證端口號
   */
  isValidPort: (port: number): boolean => {
    return Number.isInteger(port) && port >= 1 && port <= 65535;
  },

  /**
   * 驗證 URL
   */
  isValidURL: (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },

  /**
   * 驗證電子郵件
   */
  isValidEmail: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },
};

/**
 * 顏色格式化工具
 */
export const colorFormat = {
  /**
   * HEX 轉 RGB
   */
  hexToRgb: (hex: string): { r: number; g: number; b: number } | null => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : null;
  },

  /**
   * RGB 轉 HEX
   */
  rgbToHex: (r: number, g: number, b: number): string => {
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  },

  /**
   * 獲取對比色
   */
  getContrastColor: (hex: string): string => {
    const rgb = colorFormat.hexToRgb(hex);
    if (!rgb) return '#000000';
    
    const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
    return brightness > 128 ? '#000000' : '#ffffff';
  },
};