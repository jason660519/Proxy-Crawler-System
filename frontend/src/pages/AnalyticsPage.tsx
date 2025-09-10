import React from 'react';
import styled from 'styled-components';
import { OperationsDashboard, MetricsOverview } from '../components/dashboard';
import { Typography, Space } from '../components/ui';
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
 * 分析內容容器樣式
 */
const AnalyticsContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

/**
 * 數據分析頁面組件
 * 提供深入的爬蟲數據和性能分析
 */
const AnalyticsPage: React.FC = () => {
  // 設置頁面標題
  React.useEffect(() => {
    document.title = '數據分析 - Proxy Crawler System';
  }, []);

  return (
    <>
      <SEOHead 
        title="數據分析 - Proxy Crawler System"
        description="深入的爬蟲數據和性能分析，提供操作概覽和性能指標"
      />
      <PageContainer>
        <PageHeader>
          <Title level={2} style={{ margin: 0 }}>
            📈 數據分析
          </Title>
        </PageHeader>
      
      <AnalyticsContent>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 操作儀表板 */}
          <div>
            <Title level={3} style={{ marginBottom: '1rem' }}>
              操作概覽
            </Title>
            <OperationsDashboard />
          </div>
          
          {/* 指標概覽 */}
          <div>
            <Title level={3} style={{ marginBottom: '1rem' }}>
              性能指標
            </Title>
            <MetricsOverview />
          </div>
        </Space>
      </AnalyticsContent>
    </PageContainer>
    </>
  );
};

export default AnalyticsPage;