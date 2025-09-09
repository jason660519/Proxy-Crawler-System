/**
 * Header 組件
 * 應用程式頂部導航欄，包含搜尋、快速動作和通知功能
 */

import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { Input } from '../ui';
import { useGlobalSearch, useTheme } from '../../hooks';
import { spacing, borderRadius, shadows, zIndex } from '../../styles';
import type { ProxyNode } from '../../types';

// ============= 類型定義 =============

export interface HeaderProps {
  /** 是否顯示搜尋欄 */
  showSearch?: boolean;
  /** 是否顯示快速動作 */
  showQuickActions?: boolean;
  /** 是否顯示通知 */
  showNotifications?: boolean;
  /** 自定義快速動作 */
  customActions?: React.ReactNode;
  /** 搜尋回調 */
  onSearch?: (query: string) => void;
  /** 通知點擊回調 */
  onNotificationClick?: () => void;
  /** 主題切換（若提供則覆蓋內部 hook）*/
  onToggleTheme?: () => void;
  /** 當前主題（若提供則覆蓋內部 hook）*/
  themeName?: 'light' | 'dark';
}

interface NotificationItem {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

// ============= 樣式定義 =============

const HeaderContainer = styled.header`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing[3]} ${spacing[6]};
  background-color: var(--color-background-primary);
  border-bottom: 1px solid var(--color-border-primary);
  box-shadow: ${shadows.sm};
  position: sticky;
  top: 0;
  z-index: ${zIndex.header};
  min-height: 64px;
`;

const LeftSection = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[4]};
  flex: 1;
  min-width: 0;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[2]};
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  white-space: nowrap;
`;

const LogoIcon = styled.div`
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--color-interactive-primary), var(--color-interactive-primaryHover));
  border-radius: ${borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 1rem;
`;

const SearchSection = styled.div`
  flex: 1;
  max-width: 500px;
  margin: 0 ${spacing[4]};
  position: relative;
`;

const SearchResults = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: var(--color-background-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: ${borderRadius.md};
  box-shadow: ${shadows.lg};
  max-height: 400px;
  overflow-y: auto;
  z-index: ${zIndex.dropdown};
  margin-top: ${spacing[1]};
`;

const SearchResultItem = styled.div`
  padding: ${spacing[3]};
  border-bottom: 1px solid var(--color-border-primary);
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: var(--color-background-secondary);
  }
  
  &:last-child {
    border-bottom: none;
  }
`;

const SearchResultTitle = styled.div`
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: ${spacing[1]};
`;

const SearchResultDescription = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const RightSection = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[3]};
`;



const NotificationButton = styled.button<{ hasUnread: boolean }>`
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background-color: transparent;
  border-radius: ${borderRadius.md};
  cursor: pointer;
  transition: background-color 0.2s ease;
  color: var(--color-text-primary);
  
  &:hover {
    background-color: var(--color-background-secondary);
  }
  
  ${props => props.hasUnread && `
    &::after {
      content: '';
      position: absolute;
      top: 8px;
      right: 8px;
      width: 8px;
      height: 8px;
      background-color: var(--color-status-error);
      border-radius: 50%;
    }
  `}
`;

const ThemeToggle = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background-color: transparent;
  border-radius: ${borderRadius.md};
  cursor: pointer;
  transition: background-color 0.2s ease;
  color: var(--color-text-primary);
  
  &:hover {
    background-color: var(--color-background-secondary);
  }
`;

// ============= 組件實作 =============

export const Header: React.FC<HeaderProps> = ({
  showSearch = true,
  showNotifications = true,
  onSearch,
  onNotificationClick,
  onToggleTheme,
  themeName,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchResults, setShowSearchResults] = useState(false);
  const { results: searchResults, search: performSearch } = useGlobalSearch();
  // 若父層提供主題控制則優先使用，以避免多個 useTheme 實例不同步
  const { theme, toggleTheme } = useTheme();
  const effectiveTheme = themeName ?? theme;
  const effectiveToggle = onToggleTheme ?? toggleTheme;

  // 模擬通知數據
  const [notifications] = useState<NotificationItem[]>([
    {
      id: '1',
      type: 'warning',
      title: '代理連線異常',
      message: '檢測到 5 個代理節點連線不穩定',
      timestamp: new Date(),
      read: false,
    },
    {
      id: '2',
      type: 'success',
      title: '任務完成',
      message: '爬蟲任務 #1234 已成功完成',
      timestamp: new Date(Date.now() - 300000),
      read: true,
    },
  ]);

  const hasUnreadNotifications = notifications.some(n => !n.read);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    
    if (value.trim()) {
      performSearch(value);
      setShowSearchResults(true);
    } else {
      setShowSearchResults(false);
    }
    
    onSearch?.(value);
  }, [performSearch, onSearch]);

  const handleSearchResultClick = useCallback((proxy: ProxyNode) => {
    setSearchQuery('');
    setShowSearchResults(false);
    // 這裡可以添加導航邏輯
    console.log('Navigate to proxy:', proxy);
  }, []);



  return (
    <HeaderContainer>
      <LeftSection>
        <Logo>
          <LogoIcon>JS</LogoIcon>
          JasonSpider
        </Logo>
        
        {showSearch && (
          <SearchSection>
            <Input
              placeholder="搜尋代理、任務、日誌..."
              value={searchQuery}
              onChange={handleSearchChange}
              leftIcon={
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              }
            />
            
            {showSearchResults && searchResults && (
              <SearchResults>
                {/* 顯示代理結果 */}
                {searchResults.proxies?.map((proxy) => (
                  <SearchResultItem
                    key={proxy.id}
                    onClick={() => handleSearchResultClick(proxy)}
                  >
                    <SearchResultTitle>{proxy.ip}:{proxy.port}</SearchResultTitle>
                    <SearchResultDescription>{proxy.country} - {proxy.anonymity}</SearchResultDescription>
                  </SearchResultItem>
                ))}
              </SearchResults>
            )}
          </SearchSection>
        )}
      </LeftSection>
      
      <RightSection>
        {/* 已移除重新整理與設定兩個按鈕，以避免右上角重複與無作用項 */}
        <ThemeToggle onClick={effectiveToggle} title="切換主題" aria-label="切換主題">
          {effectiveTheme === 'dark' ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </ThemeToggle>
        
        {showNotifications && (
          <NotificationButton
            hasUnread={hasUnreadNotifications}
            onClick={onNotificationClick}
            title="通知"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </NotificationButton>
        )}
      </RightSection>
    </HeaderContainer>
  );
};

export default Header;