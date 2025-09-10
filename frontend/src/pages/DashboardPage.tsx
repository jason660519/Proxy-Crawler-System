import React from 'react';
import styled from 'styled-components';
import { Dashboard } from '../components/dashboard';
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
 * 儀表板頁面組件
 * 顯示系統整體狀態和關鍵指標
 */
const DashboardPage: React.FC = () => {
  // 設置頁面標題
  React.useEffect(() => {
    document.title = '儀表板 - Proxy Crawler System';
  }, []);

  return (
    <>
      <SEOHead 
        title="儀表板 - Proxy Crawler System"
        description="系統儀表板 - 查看代理爬蟲系統的整體狀態和關鍵指標"
      />
      <PageContainer>
        <PageHeader>
          <Title level={2} style={{ margin: 0 }}>
            📊 系統儀表板
          </Title>
        </PageHeader>
        <Dashboard />
      </PageContainer>
    </>
  );
};

export default DashboardPage;