/**
 * Layout 組件統一導出
 * 提供所有佈局組件的統一入口
 */

// 佈局組件
export { Header } from './Header';
export type { HeaderProps } from './Header';

export { ActivityBar } from './ActivityBar';
export type { ActivityBarProps } from './ActivityBar';

export { PageLayout } from './PageLayout';
export type { PageLayoutProps } from './PageLayout';

// 重新導出預設組件
export { default as HeaderDefault } from './Header';
export { default as ActivityBarDefault } from './ActivityBar';