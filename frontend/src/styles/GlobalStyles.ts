/**
 * 全域樣式定義 - VS Code 風格主題
 * 提供一致的設計語言和視覺體驗
 */

import styled, { createGlobalStyle } from 'styled-components';

// VS Code 風格色彩系統
export const colors = {
  // 深色主題 (預設)
  dark: {
    // 背景色
    background: {
      primary: '#1e1e1e',      // 主要背景
      secondary: '#252526',    // 次要背景
      tertiary: '#2d2d30',     // 第三層背景
      elevated: '#3c3c3c',     // 浮起元素背景
      overlay: 'rgba(0, 0, 0, 0.6)' // 遮罩背景
    },
    
    // 文字色
    text: {
      primary: '#cccccc',      // 主要文字
      secondary: '#969696',    // 次要文字
      disabled: '#656565',     // 禁用文字
      inverse: '#1e1e1e',      // 反色文字
      accent: '#007acc'        // 強調文字
    },
    
    // 邊框色
    border: {
      primary: '#3c3c3c',      // 主要邊框
      secondary: '#464647',    // 次要邊框
      focus: '#007acc',        // 焦點邊框
      error: '#f14c4c',        // 錯誤邊框
      success: '#89d185'       // 成功邊框
    },
    
    // 狀態色
    status: {
      success: '#89d185',      // 成功
      warning: '#ffcc02',      // 警告
      error: '#f14c4c',        // 錯誤
      info: '#75beff',         // 資訊
      active: '#007acc',       // 活躍
      inactive: '#656565'      // 非活躍
    },
    
    // 互動色
    interactive: {
      hover: '#2a2d2e',        // 懸停
      active: '#094771',       // 按下
      selected: '#094771',     // 選中
      focus: 'rgba(0, 122, 204, 0.4)' // 焦點
    },
    
    // Activity Bar 色彩
    activityBar: {
      background: '#333333',
      foreground: '#ffffff',
      inactiveForeground: '#ffffff66',
      border: '#333333'
    },
    
    // Side Panel 色彩
    sidePanel: {
      background: '#252526',
      foreground: '#cccccc',
      border: '#3c3c3c'
    },
    
    // Header 色彩
    header: {
      background: '#2d2d30',
      foreground: '#cccccc',
      border: '#3c3c3c'
    },
    
    // Status Bar 色彩
    statusBar: {
      background: '#007acc',
      foreground: '#ffffff',
      border: '#007acc'
    }
  },
  
  // 淺色主題
  light: {
    background: {
      primary: '#ffffff',
      secondary: '#f3f3f3',
      tertiary: '#e8e8e8',
      elevated: '#ffffff',
      overlay: 'rgba(0, 0, 0, 0.4)'
    },
    
    text: {
      primary: '#333333',
      secondary: '#666666',
      disabled: '#999999',
      inverse: '#ffffff',
      accent: '#0066cc'
    },
    
    border: {
      primary: '#e8e8e8',
      secondary: '#d4d4d4',
      focus: '#0066cc',
      error: '#e51400',
      success: '#388a34'
    },
    
    status: {
      success: '#388a34',
      warning: '#bf8803',
      error: '#e51400',
      info: '#0066cc',
      active: '#0066cc',
      inactive: '#999999'
    },
    
    interactive: {
      hover: '#f0f0f0',
      active: '#e0e0e0',
      selected: '#e0e0e0',
      focus: 'rgba(0, 102, 204, 0.4)'
    },
    
    activityBar: {
      background: '#2c2c2c',
      foreground: '#ffffff',
      inactiveForeground: '#ffffff66',
      border: '#2c2c2c'
    },
    
    sidePanel: {
      background: '#f3f3f3',
      foreground: '#333333',
      border: '#e8e8e8'
    },
    
    header: {
      background: '#e8e8e8',
      foreground: '#333333',
      border: '#d4d4d4'
    },
    
    statusBar: {
      background: '#0066cc',
      foreground: '#ffffff',
      border: '#0066cc'
    }
  }
};

// 字體設定
export const fonts = {
  primary: "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
  mono: "'Consolas', 'Monaco', 'Courier New', monospace",
  sizes: {
    xs: '11px',
    sm: '12px',
    md: '13px',
    lg: '14px',
    xl: '16px',
    xxl: '18px'
  },
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  }
};

// 間距系統
export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '20px',
  xxl: '24px',
  xxxl: '32px'
};

// 陰影效果
export const shadows = {
  sm: '0 1px 3px rgba(0, 0, 0, 0.12)',
  md: '0 4px 6px rgba(0, 0, 0, 0.15)',
  lg: '0 8px 15px rgba(0, 0, 0, 0.2)',
  xl: '0 12px 24px rgba(0, 0, 0, 0.25)'
};

// 邊框圓角
export const borderRadius = {
  sm: '2px',
  md: '4px',
  lg: '6px',
  xl: '8px'
};

// 動畫時間
export const transitions = {
  fast: '150ms',
  normal: '250ms',
  slow: '350ms'
};

// Z-index 層級
export const zIndex = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modal: 1040,
  popover: 1050,
  tooltip: 1060
};

// 全域樣式
export const GlobalStyles = createGlobalStyle<{ theme: 'light' | 'dark' }>`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  html {
    font-size: 13px;
    line-height: 1.4;
  }
  
  body {
    font-family: ${fonts.primary};
    font-size: ${fonts.sizes.md};
    font-weight: ${fonts.weights.normal};
    background-color: ${props => colors[props.theme].background.primary};
    color: ${props => colors[props.theme].text.primary};
    overflow: hidden;
    user-select: none;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  
  #root {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  /* 滾動條樣式 */
  ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }
  
  ::-webkit-scrollbar-track {
    background: ${props => colors[props.theme].background.secondary};
  }
  
  ::-webkit-scrollbar-thumb {
    background: ${props => colors[props.theme].border.secondary};
    border-radius: 5px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: ${props => colors[props.theme].text.secondary};
  }
  
  /* 選取文字樣式 */
  ::selection {
    background: ${props => colors[props.theme].interactive.selected};
    color: ${props => colors[props.theme].text.inverse};
  }
  
  /* 焦點樣式 */
  :focus {
    outline: 1px solid ${props => colors[props.theme].border.focus};
    outline-offset: -1px;
  }
  
  /* 按鈕重置 */
  button {
    border: none;
    background: none;
    cursor: pointer;
    font-family: inherit;
    font-size: inherit;
  }
  
  /* 輸入框重置 */
  input, textarea, select {
    border: none;
    background: none;
    font-family: inherit;
    font-size: inherit;
    color: inherit;
  }
  
  /* 連結重置 */
  a {
    color: inherit;
    text-decoration: none;
  }
  
  /* 列表重置 */
  ul, ol {
    list-style: none;
  }
  
  /* 表格重置 */
  table {
    border-collapse: collapse;
    border-spacing: 0;
  }
  
  /* 圖片重置 */
  img {
    max-width: 100%;
    height: auto;
  }
`;

// 主題提供者介面
export interface ThemeProviderProps {
  theme: 'light' | 'dark';
  children: React.ReactNode;
}

// 取得當前主題色彩
export const getThemeColors = (theme: 'light' | 'dark') => colors[theme];