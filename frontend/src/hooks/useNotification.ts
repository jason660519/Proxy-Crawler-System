/**
 * 通知系統 Hook
 * 
 * 提供統一的通知管理功能，包括：
 * - 顯示不同類型的通知
 * - 自動消失機制
 * - 通知歷史記錄
 * - 通知狀態管理
 */

import { useState, useCallback, useRef } from 'react';

// ============= 類型定義 =============

export interface NotificationItem {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  duration?: number;
  timestamp: Date;
  read: boolean;
}

export interface NotificationOptions {
  title?: string;
  duration?: number; // 毫秒，0 表示不自動消失
  persistent?: boolean; // 是否持久化
}

export interface UseNotificationReturn {
  notifications: NotificationItem[];
  showNotification: (message: string, type?: NotificationItem['type'], options?: NotificationOptions) => string;
  hideNotification: (id: string) => void;
  clearNotifications: () => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  unreadCount: number;
}

// ============= Hook 實現 =============

/**
 * 通知系統 Hook
 * 
 * @returns 通知系統的狀態和操作方法
 */
export function useNotification(): UseNotificationReturn {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const timeoutRefs = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const idCounter = useRef(0);

  /**
   * 顯示通知
   * 
   * @param message 通知訊息
   * @param type 通知類型
   * @param options 通知選項
   * @returns 通知 ID
   */
  const showNotification = useCallback((message: string, type: NotificationItem['type'] = 'info', options: NotificationOptions = {}): string => {
    const id = `notification-${++idCounter.current}`;
    const duration = options.duration ?? (type === 'error' ? 0 : 5000); // 錯誤通知預設不自動消失
    
    const notification: NotificationItem = {
      id,
      type,
      title: options.title,
      message,
      duration,
      timestamp: new Date(),
      read: false
    };

    setNotifications(prev => [notification, ...prev]);

    // 設置自動消失
    if (duration > 0) {
      const timeoutId = setTimeout(() => {
        hideNotification(id);
      }, duration);
      timeoutRefs.current.set(id, timeoutId);
    }

    return id;
  }, []);

  /**
   * 隱藏通知
   * 
   * @param id 通知 ID
   */
  const hideNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
    
    // 清除定時器
    const timeoutId = timeoutRefs.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutRefs.current.delete(id);
    }
  }, []);

  /**
   * 清除所有通知
   */
  const clearNotifications = useCallback(() => {
    // 清除所有定時器
    timeoutRefs.current.forEach(timeoutId => clearTimeout(timeoutId));
    timeoutRefs.current.clear();
    
    setNotifications([]);
  }, []);

  /**
   * 標記通知為已讀
   * 
   * @param id 通知 ID
   */
  const markAsRead = useCallback((id: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, read: true }
          : notification
      )
    );
  }, []);

  /**
   * 標記所有通知為已讀
   */
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
  }, []);

  // 計算未讀通知數量
  const unreadCount = notifications.filter(n => !n.read).length;

  return {
    notifications,
    showNotification,
    hideNotification,
    clearNotifications,
    markAsRead,
    markAllAsRead,
    unreadCount
  };
}

export default useNotification;