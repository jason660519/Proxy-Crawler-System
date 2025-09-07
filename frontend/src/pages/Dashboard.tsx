/**
 * 首頁儀表板組件
 * 顯示系統概覽、代理狀態、ETL監控等關鍵資訊
 */

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius } from '../styles/GlobalStyles';
import { Card, StatusIndicator, CardStats, StatItem } from '../components/UI/Card';
import { Button, IconButton } from '../components/UI/Button';
import { Table, StatusCell, ActionCell } from '../components/UI/Table';
import type { ProxyNode, ETLTask, SystemMetrics } from '../types/index';

// 儀表板容器
const DashboardContainer = styled.div<{ theme: 'light' | 'dark' }>`
  padding: ${spacing.lg};
  background-color: ${props => getThemeColors(props.theme).background.primary};
  min-height: 100%;
  overflow-y: auto;
`;

// 頁面標題
const PageHeader = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.xl};
  
  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: ${props => getThemeColors(props.theme).text.primary};
  }
  
  .actions {
    display: flex;
    gap: ${spacing.sm};
  }
`;

// 統計卡片網格
const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: ${spacing.lg};
  margin-bottom: ${spacing.xl};
`;

// 內容網格
const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: ${spacing.lg};
  margin-bottom: ${spacing.xl};
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

// 圖表容器
const ChartContainer = styled.div<{ theme: 'light' | 'dark' }>`
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.md};
  padding: ${spacing.lg};
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${props => getThemeColors(props.theme).text.secondary};
`;

// 活動列表
const ActivityList = styled.div<{ theme: 'light' | 'dark' }>`
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.md};
  padding: ${spacing.lg};
  max-height: 400px;
  overflow-y: auto;
`;

const ActivityItem = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  padding: ${spacing.sm} 0;
  border-bottom: 1px solid ${props => getThemeColors(props.theme).border.secondary};
  
  &:last-child {
    border-bottom: none;
  }
  
  .time {
    font-size: 11px;
    color: ${props => getThemeColors(props.theme).text.disabled};
    min-width: 60px;
  }
  
  .content {
    flex: 1;
    font-size: 12px;
    color: ${props => getThemeColors(props.theme).text.secondary};
  }
`;

// 儀表板組件介面
export interface DashboardProps {
  theme: 'light' | 'dark';
}

/**
 * 儀表板組件
 * 系統首頁，顯示關鍵指標和狀態
 */
export const Dashboard: React.FC<DashboardProps> = ({ theme }) => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [recentProxies, setRecentProxies] = useState<ProxyNode[]>([]);
  const [recentTasks, setRecentTasks] = useState<ETLTask[]>([]);
  const [loading, setLoading] = useState(true);

  // 模擬數據載入
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      
      // 模擬 API 調用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 模擬系統指標
      setMetrics({
        totalProxies: 1247,
        activeProxies: 892,
        successRate: 87.3,
        avgResponseTime: 245,
        totalTasks: 156,
        runningTasks: 8,
        completedTasks: 142,
        failedTasks: 6
      });
      
      // 模擬最近代理數據
      setRecentProxies([
        {
          id: '1',
          ip: '192.168.1.100',
          port: 8080,
          protocol: 'http',
          country: 'US',
          anonymity: 'high',
          speed: 245,
          uptime: 98.5,
          lastChecked: new Date(),
          status: 'active'
        },
        {
          id: '2',
          ip: '10.0.0.50',
          port: 3128,
          protocol: 'https',
          country: 'JP',
          anonymity: 'medium',
          speed: 189,
          uptime: 95.2,
          lastChecked: new Date(),
          status: 'active'
        },
        {
          id: '3',
          ip: '172.16.0.25',
          port: 8888,
          protocol: 'socks5',
          country: 'DE',
          anonymity: 'high',
          speed: 312,
          uptime: 89.7,
          lastChecked: new Date(),
          status: 'inactive'
        }
      ]);
      
      // 模擬最近任務數據
      setRecentTasks([
        {
          id: 'task-1',
          name: 'Free Proxy List 爬取',
          status: 'running',
          progress: 65,
          startTime: new Date(Date.now() - 300000),
          estimatedEndTime: new Date(Date.now() + 200000),
          source: 'free-proxy-list.net',
          proxiesFound: 234
        },
        {
          id: 'task-2',
          name: 'Proxy 驗證任務',
          status: 'completed',
          progress: 100,
          startTime: new Date(Date.now() - 600000),
          endTime: new Date(Date.now() - 60000),
          source: 'validation',
          proxiesFound: 156
        }
      ]);
      
      setLoading(false);
    };
    
    loadData();
  }, []);

  // 代理表格列定義
  const proxyColumns = [
    {
      key: 'ip',
      title: 'IP 地址',
      dataIndex: 'ip' as keyof ProxyNode,
      width: '140px'
    },
    {
      key: 'port',
      title: '端口',
      dataIndex: 'port' as keyof ProxyNode,
      width: '80px'
    },
    {
      key: 'protocol',
      title: '協議',
      dataIndex: 'protocol' as keyof ProxyNode,
      width: '80px',
      render: (value: string) => value.toUpperCase()
    },
    {
      key: 'country',
      title: '國家',
      dataIndex: 'country' as keyof ProxyNode,
      width: '80px'
    },
    {
      key: 'speed',
      title: '速度 (ms)',
      dataIndex: 'speed' as keyof ProxyNode,
      width: '100px'
    },
    {
      key: 'status',
      title: '狀態',
      dataIndex: 'status' as keyof ProxyNode,
      width: '100px',
      render: (value: string) => (
        <StatusCell 
          theme={theme} 
          status={value === 'active' ? 'success' : 'inactive'}
        >
          {value === 'active' ? '活躍' : '離線'}
        </StatusCell>
      )
    }
  ];

  // 任務表格列定義
  const taskColumns = [
    {
      key: 'name',
      title: '任務名稱',
      dataIndex: 'name' as keyof ETLTask,
      width: '200px'
    },
    {
      key: 'status',
      title: '狀態',
      dataIndex: 'status' as keyof ETLTask,
      width: '100px',
      render: (value: string) => {
        const statusMap = {
          'running': { status: 'info' as const, text: '執行中' },
          'completed': { status: 'success' as const, text: '已完成' },
          'failed': { status: 'error' as const, text: '失敗' },
          'pending': { status: 'warning' as const, text: '等待中' }
        };
        const { status, text } = statusMap[value as keyof typeof statusMap] || { status: 'inactive' as const, text: value };
        
        return (
          <StatusCell theme={theme} status={status}>
            {text}
          </StatusCell>
        );
      }
    },
    {
      key: 'progress',
      title: '進度',
      dataIndex: 'progress' as keyof ETLTask,
      width: '100px',
      render: (value: number) => `${value}%`
    },
    {
      key: 'proxiesFound',
      title: '發現代理',
      dataIndex: 'proxiesFound' as keyof ETLTask,
      width: '100px'
    }
  ];

  return (
    <DashboardContainer theme={theme}>
      {/* 頁面標題 */}
      <PageHeader theme={theme}>
        <h1>系統儀表板</h1>
        <div className="actions">
          <Button theme={theme} variant="outline" size="small">
            重新整理
          </Button>
          <Button theme={theme} variant="primary" size="small">
            新增任務
          </Button>
        </div>
      </PageHeader>

      {/* 統計卡片 */}
      <StatsGrid>
        <Card theme={theme} title="代理節點" variant="elevated">
          <CardStats theme={theme}>
            <StatItem theme={theme}>
              <span className="stat-value">{metrics?.totalProxies || 0}</span>
              <span className="stat-label">總計</span>
            </StatItem>
            <StatItem theme={theme}>
              <span className="stat-value">{metrics?.activeProxies || 0}</span>
              <span className="stat-label">活躍</span>
            </StatItem>
            <StatItem theme={theme}>
              <span className="stat-value">{metrics?.successRate || 0}%</span>
              <span className="stat-label">成功率</span>
            </StatItem>
          </CardStats>
        </Card>

        <Card theme={theme} title="ETL 任務" variant="elevated">
          <CardStats theme={theme}>
            <StatItem theme={theme}>
              <span className="stat-value">{metrics?.totalTasks || 0}</span>
              <span className="stat-label">總計</span>
            </StatItem>
            <StatItem theme={theme}>
              <span className="stat-value">{metrics?.runningTasks || 0}</span>
              <span className="stat-label">執行中</span>
            </StatItem>
            <StatItem theme={theme}>
              <span className="stat-value">{metrics?.completedTasks || 0}</span>
              <span className="stat-label">已完成</span>
            </StatItem>
          </CardStats>
        </Card>

        <Card theme={theme} title="系統性能" variant="elevated">
          <CardStats theme={theme}>
            <StatItem theme={theme}>
              <span className="stat-value">{metrics?.avgResponseTime || 0}</span>
              <span className="stat-label">平均響應 (ms)</span>
            </StatItem>
            <StatItem theme={theme}>
              <span className="stat-value">98.5</span>
              <span className="stat-label">系統可用性 (%)</span>
            </StatItem>
          </CardStats>
        </Card>
      </StatsGrid>

      {/* 主要內容區域 */}
      <ContentGrid>
        <div>
          {/* 最近代理節點 */}
          <Card theme={theme} title="最近代理節點" variant="outlined">
            <Table
              theme={theme}
              columns={proxyColumns}
              data={recentProxies}
              loading={loading}
              pagination={{
                current: 1,
                pageSize: 5,
                total: recentProxies.length
              }}
            />
          </Card>
        </div>

        <div>
          {/* 系統活動 */}
          <Card theme={theme} title="系統活動" variant="outlined">
            <ActivityList theme={theme}>
              <ActivityItem theme={theme}>
                <div className="time">10:30</div>
                <StatusIndicator theme={theme} status="success" size="small">
                  新增代理節點
                </StatusIndicator>
                <div className="content">發現 25 個新的代理節點</div>
              </ActivityItem>
              
              <ActivityItem theme={theme}>
                <div className="time">10:15</div>
                <StatusIndicator theme={theme} status="info" size="small">
                  任務完成
                </StatusIndicator>
                <div className="content">Free Proxy List 爬取任務完成</div>
              </ActivityItem>
              
              <ActivityItem theme={theme}>
                <div className="time">09:45</div>
                <StatusIndicator theme={theme} status="warning" size="small">
                  代理失效
                </StatusIndicator>
                <div className="content">12 個代理節點響應超時</div>
              </ActivityItem>
              
              <ActivityItem theme={theme}>
                <div className="time">09:30</div>
                <StatusIndicator theme={theme} status="success" size="small">
                  系統啟動
                </StatusIndicator>
                <div className="content">代理管理系統已啟動</div>
              </ActivityItem>
            </ActivityList>
          </Card>
        </div>
      </ContentGrid>

      {/* 最近任務 */}
      <Card theme={theme} title="最近 ETL 任務" variant="outlined">
        <Table
          theme={theme}
          columns={taskColumns}
          data={recentTasks}
          loading={loading}
          searchable
          searchPlaceholder="搜尋任務..."
        />
      </Card>
    </DashboardContainer>
  );
};

export default Dashboard;