import { createGlobalStyle } from 'styled-components';
import { createGlobalStyles } from './index';

/**
 * 全域樣式組件
 * 使用 styled-components 的 createGlobalStyle 創建全域樣式
 */
export const GlobalStyle = createGlobalStyle`
  ${({ theme }) => createGlobalStyles(theme)}
`;

export default GlobalStyle;