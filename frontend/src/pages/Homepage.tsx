import React from 'react';
import styled from 'styled-components';
import { Card, Typography, Button, Space } from '../components/ui';
import { useNavigate } from 'react-router-dom';
import { SEOHead } from '../components/seo';

const { Title, Paragraph } = Typography;

/**
 * 首頁容器樣式
 */
const HomepageContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`;

/**
 * 歡迎卡片樣式
 */
const WelcomeCard = styled(Card)`
  max-width: 800px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  padding: 3rem;
`;

/**
 * 功能網格樣式
 */
const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
`;

/**
 * 功能卡片樣式
 */
const FeatureCard = styled(Card)`
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
  }
`;

/**
 * 功能圖標樣式
 */
const FeatureIcon = styled.div`
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: ${props => props.theme.colors.primary};
`;

/**
 * 首頁組件
 * 提供應用概覽和快速導航功能
 */
const Homepage: React.FC = () => {
  const navigate = useNavigate();

  /**
   * 功能列表配置
   */
  const features = [
    {
      title: '儀表板',
      description: '查看系統整體狀態和關鍵指標',
      icon: '📊',
      path: '/dashboard'
    },
    {
      title: '代理管理',
      description: '管理和監控代理伺服器',
      icon: '🌐',
      path: '/proxies'
    },
    {
      title: '任務佇列',
      description: '查看和管理爬蟲任務',
      icon: '📋',
      path: '/tasks'
    },
    {
      title: '系統日誌',
      description: '查看系統運行日誌',
      icon: '📝',
      path: '/logs'
    },
    {
      title: '數據分析',
      description: '深入分析爬蟲數據和性能',
      icon: '📈',
      path: '/analytics'
    },
    {
      title: '系統設定',
      description: '配置系統參數和偏好設定',
      icon: '⚙️',
      path: '/settings'
    }
  ];

  /**
   * 處理功能卡片點擊事件
   * @param path - 目標路由路徑
   */
  const handleFeatureClick = (path: string) => {
    navigate(path);
  };

  return (
    <>
      <SEOHead 
        title="Proxy Crawler System - 代理爬蟲管理系統"
        description="強大的網路爬蟲和代理管理平台，提供完整的數據收集、處理和分析解決方案"
        keywords="代理爬蟲,網路爬蟲,數據收集,代理管理,數據分析"
      />
      <HomepageContainer>
      <WelcomeCard>
        <Title level={1} style={{ marginBottom: '1rem', color: '#2c3e50' }}>
          🕷️ Proxy Crawler System
        </Title>
        <Paragraph style={{ fontSize: '1.2rem', color: '#7f8c8d', marginBottom: '2rem' }}>
          歡迎使用代理爬蟲管理系統！這是一個強大的網路爬蟲和代理管理平台，
          提供完整的數據收集、處理和分析解決方案。
        </Paragraph>
        
        <Space size="large">
          <Button 
            type="primary" 
            size="large"
            onClick={() => navigate('/dashboard')}
          >
            開始使用
          </Button>
          <Button 
            size="large"
            onClick={() => navigate('/analytics')}
          >
            查看分析
          </Button>
        </Space>

        <FeatureGrid>
          {features.map((feature, index) => (
            <FeatureCard 
              key={index}
              onClick={() => handleFeatureClick(feature.path)}
            >
              <FeatureIcon>{feature.icon}</FeatureIcon>
              <Title level={4} style={{ marginBottom: '0.5rem' }}>
                {feature.title}
              </Title>
              <Paragraph style={{ color: '#7f8c8d', margin: 0 }}>
                {feature.description}
              </Paragraph>
            </FeatureCard>
          ))}
        </FeatureGrid>
      </WelcomeCard>
    </HomepageContainer>
    </>
  );
};

export default Homepage;