/**
 * 主題調試組件
 * 用於調試主題切換問題，顯示當前主題狀態和 CSS 變數值
 */

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

const DebugPanel = styled.div`
  position: fixed;
  bottom: 10px;
  right: 10px;
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-primary);
  border-radius: 8px;
  padding: 16px;
  font-size: 12px;
  /* 低於 Header（zIndex.header = 50），避免覆蓋右上角主題切換 */
  z-index: 10;
  max-width: 300px;
  box-shadow: var(--color-shadow-medium);
  transition: all 0.3s ease;
`;

const DebugHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-secondary);
`;

const DebugTitle = styled.h3`
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
`;

const ToggleButton = styled.button`
  background: var(--color-interactive-secondary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: var(--color-interactive-secondaryHover);
  }
`;

const DebugItem = styled.div`
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const DebugLabel = styled.span`
  font-weight: 600;
  color: var(--color-text-primary);
  display: inline-block;
  min-width: 120px;
`;

const DebugValue = styled.span`
  color: var(--color-text-secondary);
  margin-left: 8px;
  word-break: break-all;
`;

const ColorPreview = styled.div<{ color: string }>`
  display: inline-block;
  width: 12px;
  height: 12px;
  background-color: ${props => props.color};
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  margin-left: 4px;
  vertical-align: middle;
`;

const CollapsibleSection = styled.div<{ isOpen: boolean }>`
  max-height: ${props => props.isOpen ? '200px' : '0'};
  overflow: hidden;
  transition: max-height 0.3s ease;
  margin-top: 8px;
`;

interface ThemeDebuggerProps {
  theme: 'light' | 'dark';
  isDark: boolean;
  isVisible?: boolean;
  /** 若在頁面內嵌顯示，使用 relative 流式佈局，不固定在角落 */
  inline?: boolean;
}

export const ThemeDebugger: React.FC<ThemeDebuggerProps> = ({ 
  theme, 
  isDark, 
  isVisible = false,
  inline = false,
}) => {
  // 如果不是開發模式，強制不顯示，避免干擾使用者
  if (!import.meta.env.DEV) {
    isVisible = false;
  }
  const [cssVars, setCssVars] = useState<Record<string, string>>({});
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (!isVisible) return;
    
    const root = document.documentElement;
    const computedStyle = getComputedStyle(root);
    
    const vars = {
      '--color-background-primary': computedStyle.getPropertyValue('--color-background-primary'),
      '--color-text-primary': computedStyle.getPropertyValue('--color-text-primary'),
      '--color-border-primary': computedStyle.getPropertyValue('--color-border-primary'),
      '--color-interactive-primary': computedStyle.getPropertyValue('--color-interactive-primary'),
      '--color-primary-500': computedStyle.getPropertyValue('--color-primary-500'),
      '--color-primary-600': computedStyle.getPropertyValue('--color-primary-600'),
      '--color-neutral-400': computedStyle.getPropertyValue('--color-neutral-400'),
      '--color-neutral-600': computedStyle.getPropertyValue('--color-neutral-600'),
    };
    
    setCssVars(vars);
  }, [theme, isVisible]);

  if (!isVisible) return null;

  return (
    <DebugPanel style={inline ? { position: 'relative', bottom: 'auto', right: 'auto' } : undefined}>
      <DebugHeader>
        <DebugTitle>主題調試器</DebugTitle>
        <ToggleButton onClick={() => setIsExpanded(!isExpanded)}>
          {isExpanded ? '收起' : '展開'}
        </ToggleButton>
      </DebugHeader>
      
      <DebugItem>
        <DebugLabel>當前主題:</DebugLabel>
        <DebugValue>{theme}</DebugValue>
      </DebugItem>
      
      <DebugItem>
        <DebugLabel>是否深色:</DebugLabel>
        <DebugValue>{isDark ? '是' : '否'}</DebugValue>
      </DebugItem>
      
      <DebugItem>
        <DebugLabel>data-theme:</DebugLabel>
        <DebugValue>{document.documentElement.getAttribute('data-theme')}</DebugValue>
      </DebugItem>
      
      <DebugItem>
        <DebugLabel>localStorage:</DebugLabel>
        <DebugValue>{localStorage.getItem('theme') || '未設置'}</DebugValue>
      </DebugItem>
      
      <CollapsibleSection isOpen={isExpanded}>
        {Object.entries(cssVars).map(([key, value]) => (
          <DebugItem key={key}>
            <DebugLabel>{key}:</DebugLabel>
            <DebugValue>
              {value || '未定義'}
              {value && <ColorPreview color={value} />}
            </DebugValue>
          </DebugItem>
        ))}
      </CollapsibleSection>
    </DebugPanel>
  );
};

export default ThemeDebugger;
