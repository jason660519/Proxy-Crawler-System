/**
 * 模態對話框組件 - VS Code 風格的彈出對話框
 * 提供各種尺寸和類型的模態框
 */

import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';
import { IconButton } from './Button';

// 模態背景遮罩
const ModalOverlay = styled.div<{ theme: 'light' | 'dark'; open?: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: ${props => getThemeColors(props.theme).overlay.background};
  backdrop-filter: blur(2px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${spacing.lg};
  
  opacity: ${props => props.open ? 1 : 0};
  visibility: ${props => props.open ? 'visible' : 'hidden'};
  transition: all ${transitions.normal} ease;
`;

// 模態容器
const ModalContainer = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large' | 'fullscreen';
  open?: boolean;
}>`
  background-color: ${props => getThemeColors(props.theme).modal.background};
  border: 1px solid ${props => getThemeColors(props.theme).modal.border};
  border-radius: ${borderRadius.md};
  box-shadow: 0 8px 32px ${props => getThemeColors(props.theme).shadow.modal};
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - ${spacing.xl});
  overflow: hidden;
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          width: 400px;
          max-width: 90vw;
        `;
      case 'large':
        return `
          width: 800px;
          max-width: 95vw;
        `;
      case 'fullscreen':
        return `
          width: 95vw;
          height: 95vh;
          max-width: none;
          max-height: none;
        `;
      default:
        return `
          width: 600px;
          max-width: 90vw;
        `;
    }
  }}
  
  transform: ${props => props.open ? 'scale(1) translateY(0)' : 'scale(0.95) translateY(-20px)'};
  transition: all ${transitions.normal} ease;
`;

// 模態標題欄
const ModalHeader = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing.lg};
  border-bottom: 1px solid ${props => getThemeColors(props.theme).border.primary};
  background-color: ${props => getThemeColors(props.theme).modal.headerBackground};
  flex-shrink: 0;
`;

// 模態標題
const ModalTitle = styled.h2<{ theme: 'light' | 'dark' }>`
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: ${props => getThemeColors(props.theme).text.primary};
  flex: 1;
`;

// 模態內容區域
const ModalContent = styled.div<{ theme: 'light' | 'dark' }>`
  flex: 1;
  padding: ${spacing.lg};
  overflow-y: auto;
  color: ${props => getThemeColors(props.theme).text.primary};
  
  /* 自定義滾動條 */
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: ${props => getThemeColors(props.theme).scrollbar.track};
  }
  
  &::-webkit-scrollbar-thumb {
    background: ${props => getThemeColors(props.theme).scrollbar.thumb};
    border-radius: 4px;
    
    &:hover {
      background: ${props => getThemeColors(props.theme).scrollbar.thumbHover};
    }
  }
`;

// 模態底部操作欄
const ModalFooter = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: ${spacing.sm};
  padding: ${spacing.lg};
  border-top: 1px solid ${props => getThemeColors(props.theme).border.primary};
  background-color: ${props => getThemeColors(props.theme).modal.footerBackground};
  flex-shrink: 0;
`;

// 關閉按鈕容器
const CloseButtonContainer = styled.div`
  display: flex;
  align-items: center;
`;

// 模態組件介面
export interface ModalProps {
  theme: 'light' | 'dark';
  open: boolean;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  title?: string;
  closable?: boolean;
  maskClosable?: boolean;
  keyboard?: boolean;
  className?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  onClose?: () => void;
  onAfterOpen?: () => void;
  onAfterClose?: () => void;
}

/**
 * 模態對話框組件
 * 提供統一的彈出對話框樣式
 */
export const Modal: React.FC<ModalProps> = ({
  theme,
  open,
  size = 'medium',
  title,
  closable = true,
  maskClosable = true,
  keyboard = true,
  className,
  children,
  footer,
  onClose,
  onAfterOpen,
  onAfterClose
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);
  
  // 處理鍵盤事件
  useEffect(() => {
    if (!keyboard) return;
    
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open && closable) {
        onClose?.();
      }
    };
    
    if (open) {
      document.addEventListener('keydown', handleKeyDown);
    }
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, keyboard, closable, onClose]);
  
  // 處理焦點管理
  useEffect(() => {
    if (open) {
      // 保存當前焦點元素
      previousActiveElement.current = document.activeElement as HTMLElement;
      
      // 將焦點移到模態框
      setTimeout(() => {
        modalRef.current?.focus();
        onAfterOpen?.();
      }, 100);
      
      // 禁止背景滾動
      document.body.style.overflow = 'hidden';
    } else {
      // 恢復焦點
      if (previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
      
      // 恢復背景滾動
      document.body.style.overflow = '';
      
      // 延遲執行關閉後回調
      setTimeout(() => {
        onAfterClose?.();
      }, 300);
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [open, onAfterOpen, onAfterClose]);
  
  // 處理遮罩點擊
  const handleOverlayClick = (event: React.MouseEvent) => {
    if (event.target === event.currentTarget && maskClosable && closable) {
      onClose?.();
    }
  };
  
  // 處理關閉按鈕點擊
  const handleCloseClick = () => {
    if (closable) {
      onClose?.();
    }
  };
  
  // 阻止模態內容點擊事件冒泡
  const handleContentClick = (event: React.MouseEvent) => {
    event.stopPropagation();
  };
  
  // 如果不是打開狀態且沒有動畫，不渲染
  if (!open) {
    return null;
  }
  
  const modalContent = (
    <ModalOverlay
      theme={theme}
      open={open}
      onClick={handleOverlayClick}
    >
      <ModalContainer
        ref={modalRef}
        theme={theme}
        size={size}
        open={open}
        className={className}
        onClick={handleContentClick}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
      >
        {(title || closable) && (
          <ModalHeader theme={theme}>
            {title && (
              <ModalTitle theme={theme} id="modal-title">
                {title}
              </ModalTitle>
            )}
            
            {closable && (
              <CloseButtonContainer>
                <IconButton
                  theme={theme}
                  variant="ghost"
                  size="small"
                  icon={
                    <svg viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 7.293l2.146-2.147a.5.5 0 01.708.708L8.707 8l2.147 2.146a.5.5 0 01-.708.708L8 8.707l-2.146 2.147a.5.5 0 01-.708-.708L7.293 8 5.146 5.854a.5.5 0 01.708-.708L8 7.293z" />
                    </svg>
                  }
                  onClick={handleCloseClick}
                  title="關閉"
                />
              </CloseButtonContainer>
            )}
          </ModalHeader>
        )}
        
        <ModalContent theme={theme}>
          {children}
        </ModalContent>
        
        {footer && (
          <ModalFooter theme={theme}>
            {footer}
          </ModalFooter>
        )}
      </ModalContainer>
    </ModalOverlay>
  );
  
  // 使用 Portal 渲染到 body
  return createPortal(modalContent, document.body);
};

export default Modal;