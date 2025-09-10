import React from 'react';
import styled from 'styled-components';
import { Card, Typography, Button, Space } from '../components/ui';
import { useNavigate } from 'react-router-dom';
import { SEOHead } from '../components/seo';

const { Title, Paragraph } = Typography;

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
 * 開發中卡片樣式
 */
const DevelopmentCard = styled(Card)`
  text-align: center;
  padding: 3rem;
  max-width: 600px;
  margin: 2rem auto;
`;

/**
 * 圖標樣式
 */
const Icon = styled.div`
  font-size: 4rem;
  margin-bottom: 1.5rem;
`;

/**
 * 代理管理頁面組件
 * 用於管理和監控代理伺服器（開發中）
 */
const ProxiesPage: React.FC = () => {
  const navigate = useNavigate();

  // 設置頁面標題
  React.useEffect(() => {
    document.title = '代理管理 - Proxy Crawler System';
  }, []);

  /**
   * 返回儀表板
   */
  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  /**
   * 返回首頁
   */
  const handleBackToHome = () => {
    navigate('/');
  };

  return (
    <>
      <SEOHead 
        title="代理管理 - Proxy Crawler System"
        description="代理伺服器管理和監控功能，包括代理池管理、性能分析、故障轉移等功能。"
        keywords="代理管理,代理伺服器,代理池,性能監控,故障轉移"
      />
      <PageContainer>
        <PageHeader>
          <Title level={2} style={{ margin: 0 }}>
            🌐 代理管理
          </Title>
        </PageHeader>
      
      <DevelopmentCard>
        <Icon>🚧</Icon>
        <Title level={3} style={{ marginBottom: '1rem' }}>
          功能開發中
        </Title>
        <Paragraph style={{ fontSize: '1.1rem', color: '#7f8c8d', marginBottom: '2rem' }}>
          代理管理功能正在積極開發中，即將為您提供：
        </Paragraph>
        
        <div style={{ textAlign: 'left', marginBottom: '2rem' }}>
          <ul style={{ fontSize: '1rem', color: '#5a6c7d' }}>
            <li>代理伺服器狀態監控</li>
            <li>代理池管理和配置</li>
            <li>代理性能分析</li>
            <li>自動故障轉移</li>
            <li>代理使用統計</li>
          </ul>
        </div>
        
        <Space size="large">
          <Button type="primary" onClick={handleBackToDashboard}>
            返回儀表板
          </Button>
          <Button onClick={handleBackToHome}>
            返回首頁
          </Button>
        </Space>
      </DevelopmentCard>
    </PageContainer>
    </>
  );
};

export default ProxiesPage;