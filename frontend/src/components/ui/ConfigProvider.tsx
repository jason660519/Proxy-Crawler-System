/**
 * ConfigProvider 組件
 * 提供全域配置和主題上下文
 */

import React, { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { ThemeProvider } from 'styled-components';
import { lightTheme } from '../../styles';
import type { Theme } from '../../styles';

// ============= 類型定義 =============

export interface ConfigContextValue {
  theme: Theme;
  locale: string;
  direction: 'ltr' | 'rtl';
}

export interface ConfigProviderProps {
  children: ReactNode;
  theme?: Partial<ConfigContextValue['theme']>;
  locale?: string;
  direction?: 'ltr' | 'rtl';
}

// ============= 上下文 =============

const ConfigContext = createContext<ConfigContextValue | undefined>(undefined);

// ============= Hook =============

/**
 * 使用配置上下文的 Hook
 * 
 * @returns 配置上下文值
 */
export const useConfig = (): ConfigContextValue => {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};

// ============= 主要組件 =============

/**
 * ConfigProvider 組件
 * 提供全域配置和主題
 * 
 * @param props - ConfigProvider 屬性
 * @returns ConfigProvider 組件
 */
export const ConfigProvider: React.FC<ConfigProviderProps> = ({
  children,
  theme = {},
  locale = 'zh-TW',
  direction = 'ltr',
}) => {
  const configValue: ConfigContextValue = {
    theme: {
      ...lightTheme,
      ...theme,
    },
    locale,
    direction,
  };

  return (
    <ConfigContext.Provider value={configValue}>
      <ThemeProvider theme={configValue.theme}>
        <div dir={direction}>
          {children}
        </div>
      </ThemeProvider>
    </ConfigContext.Provider>
  );
};

export default ConfigProvider;