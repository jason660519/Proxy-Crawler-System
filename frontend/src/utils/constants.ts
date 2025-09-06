/**
 * 應用程式常數定義
 * 包含 API 端點、配置選項、預設值等
 */

/**
 * 應用程式基本資訊
 */
export const APP_INFO = {
  NAME: 'JasonSpider Proxy Manager',
  VERSION: '1.0.0',
  DESCRIPTION: '專業的代理伺服器管理與監控系統',
  AUTHOR: 'Jason',
  REPOSITORY: 'https://github.com/jason/jasonspider',
} as const;

/**
 * API 相關常數
 */
export const API = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  
  ENDPOINTS: {
    // 代理相關
    PROXIES: '/api/proxies',
    PROXY_DETAIL: (id: string) => `/api/proxies/${id}`,
    PROXY_TEST: (id: string) => `/api/proxies/${id}/test`,
    PROXY_TEST_BATCH: '/api/proxies/test-batch',
    PROXY_STATS: '/api/proxies/stats',
    PROXY_REFRESH: '/api/proxies/refresh',
    
    // 系統相關
    SYSTEM_STATUS: '/api/system/status',
    HEALTH_CHECK: '/api/health',
    
    // 認證相關（預留）
    AUTH_LOGIN: '/api/auth/login',
    AUTH_LOGOUT: '/api/auth/logout',
    AUTH_REFRESH: '/api/auth/refresh',
    
    // 設定相關（預留）
    SETTINGS: '/api/settings',
    USER_PREFERENCES: '/api/user/preferences',
  },
} as const;

/**
 * 本地儲存鍵名
 */
export const STORAGE_KEYS = {
  // 主題設定
  THEME: 'jasonspider_theme',
  THEME_MODE: 'jasonspider_theme_mode',
  
  // 使用者偏好
  LANGUAGE: 'jasonspider_language',
  SIDEBAR_COLLAPSED: 'jasonspider_sidebar_collapsed',
  PANEL_SIZES: 'jasonspider_panel_sizes',
  
  // 表格設定
  TABLE_COLUMNS: 'jasonspider_table_columns',
  TABLE_SORT: 'jasonspider_table_sort',
  TABLE_FILTERS: 'jasonspider_table_filters',
  TABLE_PAGE_SIZE: 'jasonspider_table_page_size',
  
  // 快取
  PROXY_CACHE: 'jasonspider_proxy_cache',
  STATS_CACHE: 'jasonspider_stats_cache',
  
  // 其他
  LAST_VISIT: 'jasonspider_last_visit',
  TOUR_COMPLETED: 'jasonspider_tour_completed',
} as const;

/**
 * 路由路徑
 */
export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  PROXIES: '/proxies',
  PROXY_DETAIL: (id: string) => `/proxies/${id}`,
  TASKS: '/tasks',
  DATA: '/data',
  SETTINGS: '/settings',
  MONITORING: '/monitoring',
  HELP: '/help',
  ABOUT: '/about',
} as const;

/**
 * 代理相關常數
 */
export const PROXY = {
  PROTOCOLS: ['http', 'https', 'socks4', 'socks5'] as const,
  ANONYMITY_LEVELS: ['elite', 'anonymous', 'transparent'] as const,
  STATUS_TYPES: ['online', 'offline', 'unknown'] as const,
  
  // 速度等級（毫秒）
  SPEED_LEVELS: {
    FAST: 100,
    MEDIUM: 500,
    SLOW: 1000,
  },
  
  // 預設測試 URL
  TEST_URLS: [
    'https://httpbin.org/ip',
    'https://api.ipify.org?format=json',
    'https://jsonip.com',
  ],
  
  // 國家代碼映射
  COUNTRIES: {
    US: '美國',
    CN: '中國',
    JP: '日本',
    KR: '韓國',
    TW: '台灣',
    HK: '香港',
    SG: '新加坡',
    GB: '英國',
    DE: '德國',
    FR: '法國',
    CA: '加拿大',
    AU: '澳洲',
    IN: '印度',
    BR: '巴西',
    RU: '俄羅斯',
    NL: '荷蘭',
    SE: '瑞典',
    NO: '挪威',
    FI: '芬蘭',
    DK: '丹麥',
  } as const,
} as const;

/**
 * UI 相關常數
 */
export const UI = {
  // 斷點
  BREAKPOINTS: {
    SM: 640,
    MD: 768,
    LG: 1024,
    XL: 1280,
    '2XL': 1536,
  },
  
  // 側邊欄寬度
  SIDEBAR: {
    WIDTH_EXPANDED: 240,
    WIDTH_COLLAPSED: 60,
  },
  
  // 活動欄寬度
  ACTIVITY_BAR: {
    WIDTH: 48,
  },
  
  // 狀態欄高度
  STATUS_BAR: {
    HEIGHT: 24,
  },
  
  // 標題欄高度
  TITLE_BAR: {
    HEIGHT: 32,
  },
  
  // 分頁大小選項
  PAGE_SIZES: [10, 25, 50, 100, 200],
  
  // 預設分頁大小
  DEFAULT_PAGE_SIZE: 25,
  
  // 動畫持續時間
  ANIMATION_DURATION: {
    FAST: 150,
    NORMAL: 200,
    SLOW: 300,
  },
  
  // Z-index 層級
  Z_INDEX: {
    DROPDOWN: 1000,
    STICKY: 1020,
    FIXED: 1030,
    MODAL_BACKDROP: 1040,
    MODAL: 1050,
    POPOVER: 1060,
    TOOLTIP: 1070,
    TOAST: 1080,
  },
} as const;

/**
 * 表格相關常數
 */
export const TABLE = {
  // 代理表格欄位
  PROXY_COLUMNS: [
    { key: 'ip', label: 'IP 地址', sortable: true, width: 120 },
    { key: 'port', label: '端口', sortable: true, width: 80 },
    { key: 'protocol', label: '協議', sortable: true, width: 80 },
    { key: 'country', label: '國家', sortable: true, width: 100 },
    { key: 'anonymity', label: '匿名等級', sortable: true, width: 100 },
    { key: 'speed', label: '速度', sortable: true, width: 80 },
    { key: 'uptime', label: '上線率', sortable: true, width: 80 },
    { key: 'lastChecked', label: '最後檢查', sortable: true, width: 140 },
    { key: 'status', label: '狀態', sortable: true, width: 80 },
    { key: 'actions', label: '操作', sortable: false, width: 120 },
  ],
  
  // 排序方向
  SORT_DIRECTIONS: ['asc', 'desc'] as const,
  
  // 預設排序
  DEFAULT_SORT: {
    column: 'lastChecked',
    direction: 'desc' as const,
  },
} as const;

/**
 * 顏色主題
 */
export const COLORS = {
  // 代理狀態顏色
  PROXY_STATUS: {
    ONLINE: '#22c55e',
    OFFLINE: '#ef4444',
    SLOW: '#f59e0b',
    UNKNOWN: '#6b7280',
  },
  
  // 協議顏色
  PROTOCOL: {
    HTTP: '#3b82f6',
    HTTPS: '#10b981',
    SOCKS4: '#8b5cf6',
    SOCKS5: '#f59e0b',
  },
  
  // 匿名等級顏色
  ANONYMITY: {
    ELITE: '#22c55e',
    ANONYMOUS: '#f59e0b',
    TRANSPARENT: '#ef4444',
  },
} as const;

/**
 * 正則表達式
 */
export const REGEX = {
  IP_V4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  IP_V6: /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/,
  PORT: /^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/,
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
} as const;

/**
 * 錯誤訊息
 */
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '網路連線錯誤，請檢查網路設定',
  SERVER_ERROR: '伺服器錯誤，請稍後再試',
  UNAUTHORIZED: '未授權，請重新登入',
  FORBIDDEN: '權限不足，無法執行此操作',
  NOT_FOUND: '請求的資源不存在',
  VALIDATION_ERROR: '輸入資料格式錯誤',
  TIMEOUT_ERROR: '請求超時，請稍後再試',
  UNKNOWN_ERROR: '發生未知錯誤，請稍後再試',
  
  // 代理相關錯誤
  PROXY_NOT_FOUND: '找不到指定的代理伺服器',
  PROXY_TEST_FAILED: '代理測試失敗',
  PROXY_INVALID_FORMAT: '代理格式錯誤',
  
  // 表單驗證錯誤
  REQUIRED_FIELD: '此欄位為必填',
  INVALID_IP: 'IP 地址格式錯誤',
  INVALID_PORT: '端口號必須在 1-65535 之間',
  INVALID_EMAIL: '電子郵件格式錯誤',
  INVALID_URL: 'URL 格式錯誤',
} as const;

/**
 * 成功訊息
 */
export const SUCCESS_MESSAGES = {
  PROXY_TESTED: '代理測試完成',
  PROXY_ADDED: '代理新增成功',
  PROXY_UPDATED: '代理更新成功',
  PROXY_DELETED: '代理刪除成功',
  SETTINGS_SAVED: '設定儲存成功',
  DATA_EXPORTED: '資料匯出成功',
  DATA_IMPORTED: '資料匯入成功',
} as const;

/**
 * 快捷鍵
 */
export const SHORTCUTS = {
  // 全域快捷鍵
  TOGGLE_SIDEBAR: 'Ctrl+B',
  TOGGLE_THEME: 'Ctrl+Shift+T',
  SEARCH: 'Ctrl+K',
  REFRESH: 'F5',
  HELP: 'F1',
  
  // 導航快捷鍵
  GO_TO_DASHBOARD: 'Ctrl+1',
  GO_TO_PROXIES: 'Ctrl+2',
  GO_TO_TASKS: 'Ctrl+3',
  GO_TO_DATA: 'Ctrl+4',
  GO_TO_SETTINGS: 'Ctrl+5',
  
  // 表格快捷鍵
  SELECT_ALL: 'Ctrl+A',
  DELETE_SELECTED: 'Delete',
  COPY_SELECTED: 'Ctrl+C',
  
  // 其他
  SAVE: 'Ctrl+S',
  UNDO: 'Ctrl+Z',
  REDO: 'Ctrl+Y',
} as const;

/**
 * 時間相關常數
 */
export const TIME = {
  // 刷新間隔（毫秒）
  REFRESH_INTERVALS: {
    FAST: 5000,    // 5 秒
    NORMAL: 30000, // 30 秒
    SLOW: 60000,   // 1 分鐘
  },
  
  // 快取時間（毫秒）
  CACHE_DURATION: {
    SHORT: 5 * 60 * 1000,     // 5 分鐘
    MEDIUM: 30 * 60 * 1000,   // 30 分鐘
    LONG: 60 * 60 * 1000,     // 1 小時
  },
  
  // 超時時間（毫秒）
  TIMEOUTS: {
    API_REQUEST: 30000,       // 30 秒
    PROXY_TEST: 10000,        // 10 秒
    FILE_UPLOAD: 60000,       // 1 分鐘
  },
} as const;

/**
 * 檔案相關常數
 */
export const FILE = {
  // 支援的檔案類型
  SUPPORTED_TYPES: {
    JSON: 'application/json',
    CSV: 'text/csv',
    TXT: 'text/plain',
    XML: 'application/xml',
  },
  
  // 檔案大小限制（位元組）
  SIZE_LIMITS: {
    SMALL: 1024 * 1024,       // 1 MB
    MEDIUM: 10 * 1024 * 1024, // 10 MB
    LARGE: 50 * 1024 * 1024,  // 50 MB
  },
  
  // 匯出格式
  EXPORT_FORMATS: ['json', 'csv', 'txt', 'xml'] as const,
} as const;

/**
 * 環境變數
 */
export const ENV = {
  NODE_ENV: import.meta.env.NODE_ENV || 'development',
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
  GA_TRACKING_ID: import.meta.env.VITE_GA_TRACKING_ID,
  VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
} as const;

/**
 * 功能標誌
 */
export const FEATURE_FLAGS = {
  ENABLE_ANALYTICS: ENV.NODE_ENV === 'production',
  ENABLE_ERROR_REPORTING: ENV.NODE_ENV === 'production',
  ENABLE_WEBSOCKET: true,
  ENABLE_DARK_MODE: true,
  ENABLE_KEYBOARD_SHORTCUTS: true,
  ENABLE_TOUR: true,
  ENABLE_EXPORT: true,
  ENABLE_IMPORT: true,
} as const;

/**
 * 預設值
 */
export const DEFAULTS = {
  THEME: 'dark' as const,
  LANGUAGE: 'zh-TW' as const,
  PAGE_SIZE: 25,
  REFRESH_INTERVAL: TIME.REFRESH_INTERVALS.NORMAL,
  SIDEBAR_COLLAPSED: false,
  
  // 代理預設值
  PROXY: {
    PROTOCOL: 'http' as const,
    ANONYMITY: 'anonymous' as const,
    TIMEOUT: 10000,
  },
  
  // 表格預設值
  TABLE: {
    SORT_COLUMN: 'lastChecked',
    SORT_DIRECTION: 'desc' as const,
    SHOW_COLUMNS: ['ip', 'port', 'protocol', 'country', 'status'],
  },
} as const;

/**
 * 類型定義
 */
export type ProxyProtocol = typeof PROXY.PROTOCOLS[number];
export type AnonymityLevel = typeof PROXY.ANONYMITY_LEVELS[number];
export type ProxyStatus = typeof PROXY.STATUS_TYPES[number];
export type SortDirection = typeof TABLE.SORT_DIRECTIONS[number];
export type ExportFormat = typeof FILE.EXPORT_FORMATS[number];
export type Theme = 'light' | 'dark' | 'auto';
export type Language = 'zh-TW' | 'en';