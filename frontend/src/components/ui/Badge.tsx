/**
 * Badge 組件
 * 提供徽章功能
 */

import React from 'react';

export interface BadgeProps {
  /** 徽章內容 */
  count?: number | string;
  /** 是否顯示零值 */
  showZero?: boolean;
  /** 最大顯示數字 */
  overflowCount?: number;
  /** 是否顯示小紅點 */
  dot?: boolean;
  /** 徽章狀態 */
  status?: 'default' | 'success' | 'processing' | 'error' | 'warning';
  /** 文字 */
  text?: string;
  /** 子元素 */
  children?: React.ReactNode;
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({
  count,
  showZero = false,
  overflowCount = 99,
  dot = false,
  status,
  text,
  children,
  className = '',
  style = {}
}) => {
  // 計算顯示的數字
  const getDisplayCount = () => {
    if (dot) return null;
    if (typeof count === 'number') {
      if (count === 0 && !showZero) return null;
      return count > overflowCount ? `${overflowCount}+` : count.toString();
    }
    return count;
  };

  const displayCount = getDisplayCount();
  const hasContent = displayCount !== null || dot || text;

  // 狀態顏色
  const getStatusColor = () => {
    switch (status) {
      case 'success': return 'bg-green-500';
      case 'processing': return 'bg-blue-500';
      case 'error': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      default: return 'bg-red-500';
    }
  };

  if (!children) {
    // 沒有子元素時，只顯示徽章
    return (
      <span
        className={`inline-flex items-center justify-center min-w-4 h-4 px-1 text-xs font-medium text-white rounded-full ${getStatusColor()} ${className}`}
        style={style}
      >
        {displayCount}
      </span>
    );
  }

  return (
    <span className={`relative inline-block ${className}`} style={style}>
      {children}
      {hasContent && (
        <span
          className={`absolute -top-1 -right-1 inline-flex items-center justify-center min-w-4 h-4 px-1 text-xs font-medium text-white rounded-full ${getStatusColor()}`}
        >
          {displayCount}
        </span>
      )}
      {text && (
        <span className="ml-1 text-sm text-gray-600 dark:text-gray-400">
          {text}
        </span>
      )}
    </span>
  );
};

export default Badge;
