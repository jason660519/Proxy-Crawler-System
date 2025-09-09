/**
 * Modal 組件
 * 提供彈出對話框功能
 */

import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Button } from './Button';
import { Card } from './Card';

export interface ModalProps {
  /** 是否顯示 Modal */
  visible?: boolean;
  /** 標題 */
  title?: React.ReactNode;
  /** 內容 */
  children?: React.ReactNode;
  /** 底部按鈕 */
  footer?: React.ReactNode;
  /** 是否可關閉 */
  closable?: boolean;
  /** 點擊遮罩是否關閉 */
  maskClosable?: boolean;
  /** 關閉回調 */
  onClose?: () => void;
  /** 確認回調 */
  onOk?: () => void;
  /** 取消回調 */
  onCancel?: () => void;
  /** 確認按鈕文字 */
  okText?: string;
  /** 取消按鈕文字 */
  cancelText?: string;
  /** 確認按鈕是否載入中 */
  confirmLoading?: boolean;
  /** 寬度 */
  width?: string | number;
  /** 高度 */
  height?: string | number;
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
}

export const Modal: React.FC<ModalProps> = ({
  visible = false,
  title,
  children,
  footer,
  closable = true,
  maskClosable = true,
  onClose,
  onOk,
  onCancel,
  okText = '確定',
  cancelText = '取消',
  confirmLoading = false,
  width = 520,
  height,
  className = '',
  style = {}
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // 處理 ESC 鍵關閉
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && visible && closable) {
        onClose?.();
      }
    };

    if (visible) {
      document.addEventListener('keydown', handleKeyDown);
      // 防止背景滾動
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [visible, closable, onClose]);

  // 處理點擊遮罩關閉
  const handleMaskClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && maskClosable && closable) {
      onClose?.();
    }
  };

  // 處理確認
  const handleOk = () => {
    onOk?.();
  };

  // 處理取消
  const handleCancel = () => {
    onCancel?.() || onClose?.();
  };

  // 預設底部
  const defaultFooter = (
    <div className="flex justify-end gap-2">
      <Button variant="outline" onClick={handleCancel}>
        {cancelText}
      </Button>
      <Button 
        onClick={handleOk} 
        loading={confirmLoading}
      >
        {okText}
      </Button>
    </div>
  );

  if (!visible) return null;

  const modalContent = (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${className}`}
      style={style}
    >
      {/* 遮罩 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleMaskClick}
      />
      
      {/* Modal 內容 */}
      <div
        ref={modalRef}
        className="relative z-10 w-full max-w-lg max-h-[90vh] overflow-hidden"
        style={{ width, height }}
      >
        <Card className="h-full flex flex-col">
          {/* 標題欄 */}
          {title && (
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {title}
              </h3>
              {closable && (
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          )}
          
          {/* 內容區域 */}
          <div className="flex-1 p-4 overflow-y-auto">
            {children}
          </div>
          
          {/* 底部按鈕 */}
          {(footer !== null) && (
            <div className="p-4 border-t">
              {footer || defaultFooter}
            </div>
          )}
        </Card>
      </div>
    </div>
  );

  // 使用 Portal 渲染到 body
  return createPortal(modalContent, document.body);
};

export default Modal;
