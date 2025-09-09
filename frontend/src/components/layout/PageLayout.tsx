/**
 * PageLayout 組件
 * 統一的頁面佈局組件，為所有分頁提供一致的佈局結構
 */

import React from 'react';
import styled from 'styled-components';
import { spacing, borderRadius } from '../../styles';
import type { BaseComponentProps } from '../../types';

// ============= 類型定義 =============

export interface PageLayoutProps extends BaseComponentProps {
  /** 頁面標題 */
  title: string;
  /** 頁面副標題 */
  subtitle?: string;
  /** 頁面描述 */
  description?: string;
  /** 頁面動作按鈕 */
  actions?: React.ReactNode;
  /** 頁面工具欄 */
  toolbar?: React.ReactNode;
  /** 頁面內容 */
  children: React.ReactNode;
  /** 是否顯示載入狀態 */
  loading?: boolean;
  /** 錯誤訊息 */
  error?: string;
  /** 是否全寬度（無邊距） */
  fullWidth?: boolean;
  /** 自訂頁面容器樣式 */
  containerStyle?: React.CSSProperties;
}

// ============= 樣式定義 =============

const PageContainer = styled.div<{ fullWidth: boolean }>`
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: ${props => props.fullWidth ? '0' : `${spacing[6]} ${spacing[8]}`};
  background-color: var(--color-background-primary);
  overflow: hidden;
`;

const PageHeader = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: ${spacing[6]};
  gap: ${spacing[4]};
  flex-shrink: 0;
`;

const PageHeaderContent = styled.div`
  flex: 1;
  min-width: 0;
`;

const PageTitle = styled.h1`
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 ${spacing[2]} 0;
  line-height: 1.2;
`;

const PageSubtitle = styled.h2`
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin: 0 0 ${spacing[2]} 0;
  line-height: 1.4;
`;

const PageDescription = styled.p`
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0;
  line-height: 1.5;
  max-width: 600px;
`;

const PageActions = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[3]};
  flex-shrink: 0;
`;

const PageToolbar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing[4]};
  background-color: var(--color-background-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: ${borderRadius.lg};
  margin-bottom: ${spacing[4]};
  gap: ${spacing[4]};
  flex-wrap: wrap;
`;

const PageContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--color-background-primary);
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--color-text-secondary);
`;

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: ${spacing[8]};
  text-align: center;
`;

const ErrorIcon = styled.div`
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: var(--color-status-error-background);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: ${spacing[4]};
  color: var(--color-status-error);
  font-size: 1.5rem;
`;

const ErrorTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 ${spacing[2]} 0;
`;

const ErrorMessage = styled.p`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
  max-width: 400px;
  line-height: 1.5;
`;

const LoadingSpinner = styled.div`
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border-primary);
  border-top: 3px solid var(--color-interactive-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: ${spacing[3]};

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// ============= 組件實現 =============

/**
 * PageLayout 組件
 * 提供統一的頁面佈局結構，包含標題、工具欄、內容區域等
 * 
 * @param props - PageLayout 屬性
 * @returns React 組件
 */
export const PageLayout: React.FC<PageLayoutProps> = ({
  title,
  subtitle,
  description,
  actions,
  toolbar,
  children,
  loading = false,
  error,
  fullWidth = false,
  containerStyle,
  className,
  ...rest
}) => {
  // 渲染載入狀態
  const renderLoading = () => (
    <LoadingContainer>
      <LoadingSpinner />
      載入中...
    </LoadingContainer>
  );

  // 渲染錯誤狀態
  const renderError = () => (
    <ErrorContainer>
      <ErrorIcon>
        ⚠️
      </ErrorIcon>
      <ErrorTitle>載入失敗</ErrorTitle>
      <ErrorMessage>{error}</ErrorMessage>
    </ErrorContainer>
  );

  // 渲染頁面內容
  const renderContent = () => {
    if (loading) {
      return renderLoading();
    }

    if (error) {
      return renderError();
    }

    return (
      <PageContent>
        {children}
      </PageContent>
    );
  };

  return (
    <PageContainer 
      fullWidth={fullWidth} 
      className={className}
      style={containerStyle}
      {...rest}
    >
      {/* 頁面標題區域 */}
      <PageHeader>
        <PageHeaderContent>
          <PageTitle>{title}</PageTitle>
          {subtitle && <PageSubtitle>{subtitle}</PageSubtitle>}
          {description && <PageDescription>{description}</PageDescription>}
        </PageHeaderContent>
        {actions && (
          <PageActions>
            {actions}
          </PageActions>
        )}
      </PageHeader>

      {/* 頁面工具欄 */}
      {toolbar && (
        <PageToolbar>
          {toolbar}
        </PageToolbar>
      )}

      {/* 頁面內容 */}
      {renderContent()}
    </PageContainer>
  );
};

export default PageLayout;