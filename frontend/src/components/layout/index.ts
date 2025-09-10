/**
 * Layout 組件統一導出
 * 提供所有佈局組件的統一入口
 */

// 佈局組件 - 使用預設導出
export { default as Header } from './Header';
export type { HeaderProps } from './Header';

export { default as ActivityBar } from './ActivityBar';
export type { ActivityBarProps } from './ActivityBar';

// 重新導出預設組件
export { default as HeaderDefault } from './Header';
export { default as ActivityBarDefault } from './ActivityBar';
export { default as Layout } from './Layout';