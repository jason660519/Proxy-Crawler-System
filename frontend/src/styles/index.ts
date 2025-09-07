/**
 * 全域樣式配置
 * 包含主題變數、顏色系統、間距、字體等設計系統
 */

import { css } from 'styled-components';

// ============= 顏色系統 =============

export const colors = {
  // 主色調
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  
  // 次要色調
  secondary: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },
  
  // 狀態顏色
  success: {
    50: '#ecfdf5',
    100: '#d1fae5',
    200: '#a7f3d0',
    300: '#6ee7b7',
    400: '#34d399',
    500: '#10b981',
    600: '#059669',
    700: '#047857',
    800: '#065f46',
    900: '#064e3b',
  },
  
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },
  
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },
  
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  
  // 灰階
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  
  // 特殊顏色
  white: '#ffffff',
  black: '#000000',
  transparent: 'transparent',
};

// ============= 主題配置 =============

export const lightTheme = {
  name: 'light',
  colors: {
    // 背景色
    background: {
      primary: colors.white,
      secondary: colors.gray[50],
      tertiary: colors.gray[100],
      elevated: colors.white,
    },
    
    // 文字顏色
    text: {
      primary: colors.gray[900],
      secondary: colors.gray[600],
      tertiary: colors.gray[400],
      inverse: colors.white,
      disabled: colors.gray[300],
    },
    
    // 邊框顏色
    border: {
      primary: colors.gray[200],
      secondary: colors.gray[100],
      focus: colors.primary[500],
      error: colors.error[500],
    },
    
    // 狀態顏色
    status: {
      success: colors.success[500],
      warning: colors.warning[500],
      error: colors.error[500],
      info: colors.info[500],
    },
    
    // 互動顏色
    interactive: {
      primary: colors.primary[500],
      primaryHover: colors.primary[600],
      primaryActive: colors.primary[700],
      secondary: colors.gray[100],
      secondaryHover: colors.gray[200],
      secondaryActive: colors.gray[300],
    },
    
    // 陰影
    shadow: {
      light: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      medium: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      heavy: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    },
  },
  spacing: [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160, 192, 224, 256],
  borderRadius: {
    small: '0.25rem',
    medium: '0.5rem',
    large: '1rem',
    full: '9999px',
  },
  shadows: {
    small: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    medium: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    large: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    focus: '0 0 0 3px rgba(59, 130, 246, 0.1)',
  },
  typography: {
    fontFamily: {
      primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      mono: 'SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
};

export const darkTheme = {
  name: 'dark',
  colors: {
    // 背景色
    background: {
      primary: colors.gray[900],
      secondary: colors.gray[800],
      tertiary: colors.gray[700],
      elevated: colors.gray[800],
    },
    
    // 文字顏色
    text: {
      primary: colors.gray[100],
      secondary: colors.gray[300],
      tertiary: colors.gray[500],
      inverse: colors.gray[900],
      disabled: colors.gray[600],
    },
    
    // 邊框顏色
    border: {
      primary: colors.gray[700],
      secondary: colors.gray[800],
      focus: colors.primary[400],
      error: colors.error[400],
    },
    
    // 狀態顏色
    status: {
      success: colors.success[400],
      warning: colors.warning[400],
      error: colors.error[400],
      info: colors.info[400],
    },
    
    // 互動顏色
    interactive: {
      primary: colors.primary[500],
      primaryHover: colors.primary[400],
      primaryActive: colors.primary[300],
      secondary: colors.gray[700],
      secondaryHover: colors.gray[600],
      secondaryActive: colors.gray[500],
    },
    
    // 陰影
    shadow: {
      light: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
      medium: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
      heavy: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
    },
  },
  spacing: [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160, 192, 224, 256],
  borderRadius: {
    small: '0.25rem',
    medium: '0.5rem',
    large: '1rem',
    full: '9999px',
  },
  shadows: {
    small: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    medium: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
    large: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
    focus: '0 0 0 3px rgba(59, 130, 246, 0.2)',
  },
  typography: {
    fontFamily: {
      primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      mono: 'SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
       tight: 1.25,
       normal: 1.5,
       relaxed: 1.75,
     },
   },
 };

// ============= 間距系統 =============

export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
  32: '8rem',     // 128px
  40: '10rem',    // 160px
  48: '12rem',    // 192px
  56: '14rem',    // 224px
  64: '16rem',    // 256px
};

// ============= 字體系統 =============

export const typography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
    mono: ['JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', 'monospace'],
  },
  
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
    '6xl': '3.75rem', // 60px
  },
  
  fontWeight: {
    thin: 100,
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },
  
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
};

// ============= 邊框半徑 =============

export const borderRadius = {
  none: '0',
  sm: '0.125rem',   // 2px
  base: '0.25rem',  // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  '3xl': '1.5rem',  // 24px
  full: '9999px',
};

// ============= Z-Index 層級 =============

export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  header: 50,
  sidebar: 40,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
};

// ============= 斷點系統 =============

export const breakpoints = {
  xs: '0px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// ============= 媒體查詢 =============

export const media = {
  xs: `@media (min-width: ${breakpoints.xs})`,
  sm: `@media (min-width: ${breakpoints.sm})`,
  md: `@media (min-width: ${breakpoints.md})`,
  lg: `@media (min-width: ${breakpoints.lg})`,
  xl: `@media (min-width: ${breakpoints.xl})`,
  '2xl': `@media (min-width: ${breakpoints['2xl']})`,
};

// ============= 動畫 =============

export const animations = {
  duration: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms',
  },
  
  easing: {
    linear: 'linear',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  
  keyframes: {
    fadeIn: css`
      from { opacity: 0; }
      to { opacity: 1; }
    `,
    
    fadeOut: css`
      from { opacity: 1; }
      to { opacity: 0; }
    `,
    
    slideInUp: css`
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    `,
    
    slideInDown: css`
      from {
        opacity: 0;
        transform: translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    `,
    
    spin: css`
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    `,
    
    pulse: css`
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    `,
  },
};



// ============= 全域樣式 =============

export const createGlobalStyles = (theme: typeof lightTheme) => css`
  :root {
    /* 背景色變數 */
    --color-background-primary: ${theme.colors.background.primary};
    --color-background-primary-80: ${theme.name === 'light' ? 'rgba(255, 255, 255, 0.8)' : 'rgba(15, 23, 42, 0.8)'};
    --color-background-secondary: ${theme.colors.background.secondary};
    --color-background-tertiary: ${theme.colors.background.tertiary};
    --color-background-elevated: ${theme.colors.background.elevated};
    --color-background-card: ${theme.colors.background.elevated};
    --color-background-hover: ${theme.colors.background.secondary};
    --color-background-disabled: ${theme.colors.background.secondary};
    --color-background-tooltip: ${theme.colors.background.tertiary};
    
    /* 文字顏色變數 */
    --color-text-primary: ${theme.colors.text.primary};
    --color-text-secondary: ${theme.colors.text.secondary};
    --color-text-tertiary: ${theme.colors.text.tertiary};
    --color-text-inverse: ${theme.colors.text.inverse};
    --color-text-disabled: ${theme.colors.text.disabled};
    
    /* 邊框顏色變數 */
    --color-border-primary: ${theme.colors.border.primary};
    --color-border-secondary: ${theme.colors.border.secondary};
    --color-border-focus: ${theme.colors.border.focus};
    --color-border-error: ${theme.colors.border.error};
    --color-border-default: ${theme.colors.border.primary};
    --color-border-light: ${theme.colors.border.secondary};
    --color-border-hover: ${theme.colors.border.focus};
    
    /* 狀態顏色變數 */
    --color-status-success: ${theme.colors.status.success};
    --color-status-success-bg: ${theme.name === 'light' ? '#dcfce7' : '#14532d'};
    --color-status-success-light: ${theme.name === 'light' ? '#f0fdf4' : '#166534'};
    --color-status-warning: ${theme.colors.status.warning};
    --color-status-warning-bg: ${theme.name === 'light' ? '#fef3c7' : '#92400e'};
    --color-status-warning-light: ${theme.name === 'light' ? '#fffbeb' : '#a16207'};
    --color-status-error: ${theme.colors.status.error};
    --color-status-error-bg: ${theme.name === 'light' ? '#fef2f2' : '#7f1d1d'};
    --color-status-error-light: ${theme.name === 'light' ? '#fef7f7' : '#991b1b'};
    --color-status-info: ${theme.colors.status.info};
    --color-status-info-bg: ${theme.name === 'light' ? '#eff6ff' : '#1e3a8a'};
    --color-status-info-light: ${theme.name === 'light' ? '#f0f9ff' : '#1e40af'};
    
    /* 互動顏色變數 */
    --color-interactive-primary: ${theme.colors.interactive.primary};
    --color-interactive-primaryHover: ${theme.colors.interactive.primaryHover};
    --color-interactive-primaryActive: ${theme.colors.interactive.primaryActive};
    --color-interactive-secondary: ${theme.colors.interactive.secondary};
    --color-interactive-secondaryHover: ${theme.colors.interactive.secondaryHover};
    --color-interactive-secondaryActive: ${theme.colors.interactive.secondaryActive};
    
    /* Primary 色系變數 */
    --color-primary-50: ${colors.primary[50]};
    --color-primary-100: ${colors.primary[100]};
    --color-primary-200: ${colors.primary[200]};
    --color-primary-300: ${colors.primary[300]};
    --color-primary-400: ${colors.primary[400]};
    --color-primary-500: ${colors.primary[500]};
    --color-primary-600: ${colors.primary[600]};
    --color-primary-700: ${colors.primary[700]};
    --color-primary-800: ${colors.primary[800]};
    --color-primary-900: ${colors.primary[900]};
    --color-primary-500-alpha-20: ${theme.name === 'light' ? 'rgba(96, 165, 250, 0.2)' : 'rgba(96, 165, 250, 0.2)'};
    
    /* Neutral/Gray 色系變數 */
    --color-neutral-50: ${colors.gray[50]};
    --color-neutral-100: ${colors.gray[100]};
    --color-neutral-200: ${colors.gray[200]};
    --color-neutral-300: ${colors.gray[300]};
    --color-neutral-400: ${colors.gray[400]};
    --color-neutral-500: ${colors.gray[500]};
    --color-neutral-600: ${colors.gray[600]};
    --color-neutral-700: ${colors.gray[700]};
    --color-neutral-800: ${colors.gray[800]};
    --color-neutral-900: ${colors.gray[900]};
    --color-neutral-800-50: ${theme.name === 'light' ? 'rgba(64, 64, 64, 0.05)' : 'rgba(64, 64, 64, 0.5)'};
    
    /* 其他顏色變數 */
    --color-white: #ffffff;
    --color-black: #000000;
  }
  
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  
  html {
    font-size: 16px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  
  body {
    font-family: ${theme.typography.fontFamily.primary};
    font-weight: ${theme.typography.fontWeight.normal};
    background-color: var(--color-background-primary);
    color: var(--color-text-primary);
    transition: background-color 0.3s ease,
                color 0.3s ease;
  }
  
  #root {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  /* 滾動條樣式 */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  ::-webkit-scrollbar-track {
    background: var(--color-background-secondary);
  }
  
  ::-webkit-scrollbar-thumb {
    background: var(--color-border-primary);
    border-radius: ${theme.borderRadius.full};
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: var(--color-text-tertiary);
  }
  
  /* 選取文字樣式 */
  ::selection {
    background-color: var(--color-interactive-primary);
    color: var(--color-text-inverse);
  }
  
  /* 焦點樣式 */
  :focus {
    outline: 2px solid var(--color-border-focus);
    outline-offset: 2px;
  }
  
  :focus:not(:focus-visible) {
    outline: none;
  }
  
  /* 連結樣式 */
  a {
    color: var(--color-interactive-primary);
    text-decoration: none;
    transition: color 0.15s ease;
  }
  
  a:hover {
    color: var(--color-interactive-primaryHover);
  }
  
  /* 按鈕重置 */
  button {
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    font: inherit;
    color: inherit;
    cursor: pointer;
  }
  
  /* 輸入框重置 */
  input, textarea, select {
    font: inherit;
    color: inherit;
  }
  
  /* 圖片樣式 */
  img {
    max-width: 100%;
    height: auto;
  }
  
  /* 表格樣式 */
  table {
    border-collapse: collapse;
    width: 100%;
  }
  
  /* 無障礙輔助 */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
`;

// ============= CSS 變數生成 =============

export function generateCSSVariables(theme: typeof lightTheme): string {
  const variables: string[] = [];
  
  function addVariables(obj: any, prefix: string = '') {
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'object' && value !== null) {
        addVariables(value, `${prefix}${key}-`);
      } else {
        variables.push(`--color-${prefix}${key}: ${value};`);
      }
    }
  }
  
  addVariables(theme.colors);
  
  return `:root {
  ${variables.join('\n  ')}
}`;
}

// ============= 主題類型定義 =============

export type Theme = typeof lightTheme;
export type ThemeName = 'light' | 'dark';

// ============= 陰影系統 =============

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  none: 'none',
};

// ============= 匯出設計系統 =============

export const designSystem = {
  colors,
  lightTheme,
  darkTheme,
  spacing,
  typography,
  borderRadius,
  shadows,
  zIndex,
  breakpoints,
  media,
  animations,
  createGlobalStyles,
  generateCSSVariables,
};

export default designSystem;