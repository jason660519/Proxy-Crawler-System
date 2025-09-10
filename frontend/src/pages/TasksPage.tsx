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
 * 任務佇列頁面組件
 * 用於查看和管理爬蟲任務（開發中）
 */
const TasksPage: React.FC = () => {
  const navigate = useNavigate();

  // 設置頁面標題
  React.useEffect(() => {
    document.title = '任務佇列 - Proxy Crawler System';
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
        title="任務佇列 - Proxy Crawler System"
        description="查看和管理爬蟲任務佇列，監控任務狀態，設定任務優先級，分析任務性能。"
        keywords="任務佇列,爬蟲任務,任務管理,任務監控,Proxy Crawler"
      />
      <PageContainer>
        <PageHeader>
          <Title level={2} style={{ margin: 0 }}>
            📋 任務佇列
          </Title>
        </PageHeader>
      
      <DevelopmentCard>
        <Icon>🚧</Icon>
        <Title level={3} style={{ marginBottom: '1rem' }}>
          功能開發中
        </Title>
        <Paragraph style={{ fontSize: '1.1rem', color: '#7f8c8d', marginBottom: '2rem' }}>
          任務佇列管理功能正在積極開發中，即將為您提供：
        </Paragraph>
        
        <div style={{ textAlign: 'left', marginBottom: '2rem' }}>
          <ul style={{ fontSize: '1rem', color: '#5a6c7d' }}>
            <li>爬蟲任務狀態監控</li>
            <li>任務佇列管理</li>
            <li>任務優先級設定</li>
            <li>任務執行歷史</li>
            <li>任務性能分析</li>
            <li>批量任務操作</li>
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

export default TasksPage;