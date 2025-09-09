/**
 * Progress 組件
 * 提供進度條功能
 */

import React from 'react';

export interface ProgressProps {
  /** 進度百分比 (0-100) */
  percent?: number;
  /** 是否顯示百分比文字 */
  showInfo?: boolean;
  /** 進度條狀態 */
  status?: 'normal' | 'success' | 'exception' | 'active';
  /** 進度條大小 */
  size?: 'default' | 'small';
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

export const Progress: React.FC<ProgressProps> = ({
  percent = 0,
  showInfo = true,
  status = 'normal',
  size = 'default',
  className = '',
  style = {}
}) => {
  const height = size === 'small' ? 'h-1' : 'h-2';
  
  const getStatusColor = () => {
    switch (status) {
      case 'success': return 'bg-green-500';
      case 'exception': return 'bg-red-500';
      case 'active': return 'bg-blue-500 animate-pulse';
      default: return 'bg-blue-500';
    }
  };

  const clampedPercent = Math.min(Math.max(percent, 0), 100);

  return (
    <div className={`w-full ${className}`} style={style}>
      <div className={`w-full bg-gray-200 rounded-full ${height}`}>
        <div
          className={`${height} rounded-full transition-all duration-300 ${getStatusColor()}`}
          style={{ width: `${clampedPercent}%` }}
        />
      </div>
      {showInfo && (
        <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {clampedPercent}%
        </div>
      )}
    </div>
  );
};

export default Progress;
