import React from 'react';
import styled from 'styled-components';
import Settings from '../components/settings/Settings';
import { Typography } from '../components/ui';
import { SEOHead } from '../components/seo';

const { Title } = Typography;

/**
 * 頁面容器樣式
 */
const PageContainer = styled.div`
  padding: 2rem;
  min-height: 100vh;
  background-color: ${props => props.theme.colors.background};
`;

/**
 * 頁面標題樣式
 */
const PageHeader = styled.div`
  margin-bottom: 2rem;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  padding-bottom: 1rem;
`;

/**
 * 系統設定頁面組件
 * 提供系統配置和偏好設定功能
 */
const SettingsPage: React.FC = () => {
  // 設置頁面標題
  React.useEffect(() => {
    document.title = '系統設定 - Proxy Crawler System';
  }, []);

  return (
    <>
      <SEOHead 
        title="系統設定 - Proxy Crawler System"
        description="系統配置和偏好設定功能"
      />
      <PageContainer>
        <PageHeader>
          <Title level={2} style={{ margin: 0 }}>
            ⚙️ 系統設定
          </Title>
        </PageHeader>
        <Settings />
      </PageContainer>
    </>
  );
};

export default SettingsPage;