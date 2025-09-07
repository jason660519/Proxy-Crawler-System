/**
 * 下拉菜單組件 - VS Code 風格的下拉選單
 * 提供靈活的下拉菜單功能，支持多種觸發方式和自定義內容
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, shadows, transitions } from '../../styles/GlobalStyles';

// 下拉容器
const DropdownContainer = styled.div`
  position: relative;
  display: inline-block;
`;

// 觸發器
const DropdownTrigger = styled.div<{
  theme: 'light' | 'dark';
  disabled?: boolean;
}>`
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  opacity: ${props => props.disabled ? 0.6 : 1};
  transition: ${transitions.fast};
  
  &:hover {
    opacity: ${props => props.disabled ? 0.6 : 0.8};
  }
`;

// 下拉內容容器
const DropdownContent = styled.div<{
  theme: 'light' | 'dark';
  position: 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right';
  width?: string;
  maxHeight?: string;
  visible: boolean;
}>`
  position: absolute;
  z-index: 1000;
  min-width: 160px;
  max-width: 320px;
  width: ${props => props.width || 'auto'};
  max-height: ${props => props.maxHeight || '300px'};
  
  background-color: ${props => getThemeColors(props.theme).background.elevated};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.md};
  box-shadow: ${props => shadows[props.theme].dropdown};
  
  overflow-y: auto;
  
  opacity: ${props => props.visible ? 1 : 0};
  visibility: ${props => props.visible ? 'visible' : 'hidden'};
  transform: ${props => props.visible ? 'translateY(0)' : 'translateY(-8px)'};
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.position) {
      case 'bottom-left':
        return `
          top: 100%;
          left: 0;
          margin-top: ${spacing.xs};
        `;
      case 'bottom-right':
        return `
          top: 100%;
          right: 0;
          margin-top: ${spacing.xs};
        `;
      case 'top-left':
        return `
          bottom: 100%;
          left: 0;
          margin-bottom: ${spacing.xs};
        `;
      case 'top-right':
        return `
          bottom: 100%;
          right: 0;
          margin-bottom: ${spacing.xs};
        `;
      default:
        return `
          top: 100%;
          left: 0;
          margin-top: ${spacing.xs};
        `;
    }
  }}
  
  /* 自定義滾動條 */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: ${props => getThemeColors(props.theme).border.secondary};
    border-radius: ${borderRadius.full};
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background-color: ${props => getThemeColors(props.theme).border.primary};
  }
`;

// 下拉項目
const DropdownItem = styled.div<{
  theme: 'light' | 'dark';
  disabled?: boolean;
  danger?: boolean;
  selected?: boolean;
}>`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  padding: ${spacing.sm} ${spacing.md};
  
  font-size: 14px;
  color: ${props => {
    if (props.disabled) return getThemeColors(props.theme).text.disabled;
    if (props.danger) return getThemeColors(props.theme).status.error;
    return getThemeColors(props.theme).text.primary;
  }};
  
  background-color: ${props => {
    if (props.selected) return getThemeColors(props.theme).background.hover;
    return 'transparent';
  }};
  
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  transition: ${transitions.fast};
  
  &:hover {
    background-color: ${props => {
      if (props.disabled) return 'transparent';
      return getThemeColors(props.theme).background.hover;
    }};
  }
  
  &:active {
    background-color: ${props => {
      if (props.disabled) return 'transparent';
      return getThemeColors(props.theme).background.active;
    }};
  }
  
  &:first-child {
    border-top-left-radius: ${borderRadius.md};
    border-top-right-radius: ${borderRadius.md};
  }
  
  &:last-child {
    border-bottom-left-radius: ${borderRadius.md};
    border-bottom-right-radius: ${borderRadius.md};
  }
`;

// 下拉分隔線
const DropdownDivider = styled.div<{
  theme: 'light' | 'dark';
}>`
  height: 1px;
  margin: ${spacing.xs} 0;
  background-color: ${props => getThemeColors(props.theme).border.secondary};
`;

// 下拉標題
const DropdownHeader = styled.div<{
  theme: 'light' | 'dark';
}>`
  padding: ${spacing.sm} ${spacing.md};
  font-size: 12px;
  font-weight: 600;
  color: ${props => getThemeColors(props.theme).text.secondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid ${props => getThemeColors(props.theme).border.secondary};
  margin-bottom: ${spacing.xs};
`;

// 下拉項目圖標
const DropdownItemIcon = styled.span<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
`;

// 下拉項目文字
const DropdownItemText = styled.span`
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

// 下拉項目快捷鍵
const DropdownItemShortcut = styled.span<{
  theme: 'light' | 'dark';
}>`
  font-size: 12px;
  color: ${props => getThemeColors(props.theme).text.tertiary};
  margin-left: auto;
  flex-shrink: 0;
`;

// 下拉項目介面
export interface DropdownItemData {
  key: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  shortcut?: string;
  disabled?: boolean;
  danger?: boolean;
  selected?: boolean;
  onClick?: () => void;
}

// 下拉組件介面
export interface DropdownProps {
  theme: 'light' | 'dark';
  trigger: React.ReactNode;
  children?: React.ReactNode;
  items?: DropdownItemData[];
  position?: 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right';
  width?: string;
  maxHeight?: string;
  disabled?: boolean;
  closeOnItemClick?: boolean;
  closeOnOutsideClick?: boolean;
  onVisibleChange?: (visible: boolean) => void;
  className?: string;
}

/**
 * 下拉菜單組件
 * 提供靈活的下拉菜單功能
 */
export const Dropdown: React.FC<DropdownProps> = ({
  theme,
  trigger,
  children,
  items,
  position = 'bottom-left',
  width,
  maxHeight,
  disabled = false,
  closeOnItemClick = true,
  closeOnOutsideClick = true,
  onVisibleChange,
  className
}) => {
  const [visible, setVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  
  // 切換顯示狀態
  const toggleVisible = useCallback(() => {
    if (disabled) return;
    
    const newVisible = !visible;
    setVisible(newVisible);
    onVisibleChange?.(newVisible);
  }, [visible, disabled, onVisibleChange]);
  
  // 隱藏下拉菜單
  const hideDropdown = useCallback(() => {
    setVisible(false);
    onVisibleChange?.(false);
  }, [onVisibleChange]);
  
  // 處理項目點擊
  const handleItemClick = useCallback((item: DropdownItemData) => {
    if (item.disabled) return;
    
    item.onClick?.();
    
    if (closeOnItemClick) {
      hideDropdown();
    }
  }, [closeOnItemClick, hideDropdown]);
  
  // 處理外部點擊
  useEffect(() => {
    if (!closeOnOutsideClick || !visible) return;
    
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        hideDropdown();
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [visible, closeOnOutsideClick, hideDropdown]);
  
  // 處理鍵盤事件
  useEffect(() => {
    if (!visible) return;
    
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        hideDropdown();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [visible, hideDropdown]);
  
  // 渲染下拉內容
  const renderContent = () => {
    if (children) {
      return children;
    }
    
    if (items && items.length > 0) {
      return items.map((item, index) => {
        if (item.key === 'divider') {
          return <DropdownDivider key={index} theme={theme} />;
        }
        
        if (item.key === 'header') {
          return (
            <DropdownHeader key={index} theme={theme}>
              {item.label}
            </DropdownHeader>
          );
        }
        
        return (
          <DropdownItem
            key={item.key}
            theme={theme}
            disabled={item.disabled}
            danger={item.danger}
            selected={item.selected}
            onClick={() => handleItemClick(item)}
          >
            {item.icon && (
              <DropdownItemIcon theme={theme}>
                {item.icon}
              </DropdownItemIcon>
            )}
            
            <DropdownItemText>
              {item.label}
            </DropdownItemText>
            
            {item.shortcut && (
              <DropdownItemShortcut theme={theme}>
                {item.shortcut}
              </DropdownItemShortcut>
            )}
          </DropdownItem>
        );
      });
    }
    
    return null;
  };
  
  return (
    <DropdownContainer ref={containerRef} className={className}>
      <DropdownTrigger
        theme={theme}
        disabled={disabled}
        onClick={toggleVisible}
      >
        {trigger}
      </DropdownTrigger>
      
      <DropdownContent
        ref={contentRef}
        theme={theme}
        position={position}
        width={width}
        maxHeight={maxHeight}
        visible={visible}
      >
        {renderContent()}
      </DropdownContent>
    </DropdownContainer>
  );
};

// 下拉項目組件
export const DropdownItemComponent: React.FC<{
  theme: 'light' | 'dark';
  icon?: React.ReactNode;
  children: React.ReactNode;
  shortcut?: string;
  disabled?: boolean;
  danger?: boolean;
  selected?: boolean;
  onClick?: () => void;
}> = ({
  theme,
  icon,
  children,
  shortcut,
  disabled,
  danger,
  selected,
  onClick
}) => {
  return (
    <DropdownItem
      theme={theme}
      disabled={disabled}
      danger={danger}
      selected={selected}
      onClick={onClick}
    >
      {icon && (
        <DropdownItemIcon theme={theme}>
          {icon}
        </DropdownItemIcon>
      )}
      
      <DropdownItemText>
        {children}
      </DropdownItemText>
      
      {shortcut && (
        <DropdownItemShortcut theme={theme}>
          {shortcut}
        </DropdownItemShortcut>
      )}
    </DropdownItem>
  );
};

// 下拉分隔線組件
export const DropdownDividerComponent: React.FC<{
  theme: 'light' | 'dark';
}> = ({ theme }) => {
  return <DropdownDivider theme={theme} />;
};

// 下拉標題組件
export const DropdownHeaderComponent: React.FC<{
  theme: 'light' | 'dark';
  children: React.ReactNode;
}> = ({ theme, children }) => {
  return (
    <DropdownHeader theme={theme}>
      {children}
    </DropdownHeader>
  );
};

export default Dropdown;