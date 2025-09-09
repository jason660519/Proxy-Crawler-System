/**
 * 健康檢查引擎組件
 * 
 * 提供代理健康檢查功能，包括：
 * - 批量健康檢查
 * - 即時檢測狀態
 * - 檢測結果分析
 * - 效能監控
 * - 檢測歷史記錄
 */

import React, { useState, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import { Card, Button, Progress, Select, Input } from '../ui';
import { StatusIndicator } from '../ui/StatusIndicator';
import { useNotification } from '../../hooks/useNotification';
import { formatDateTime } from '../../utils/formatters';

// ============= 樣式定義 =============

const HealthCheckContainer = styled(Card)`
  padding: 24px;
  background: var(--color-surface);
  border-radius: 12px;
  box-shadow: var(--shadow-medium);
`;

const HeaderSection = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
`;

const Title = styled.h2`
  margin: 0;
  color: var(--color-text-primary);
  font-size: 1.5rem;
  font-weight: 600;
`;

const ControlsSection = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--color-background-secondary);
  border-radius: 8px;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled.div`
  padding: 16px;
  background: var(--color-background);
  border-radius: 8px;
  text-align: center;
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-small);
  }
`;

const StatValue = styled.div`
  font-size: 1.8rem;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 4px;
`;

const StatLabel = styled.div`
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ProgressSection = styled.div`
  margin-bottom: 24px;
`;

const ProgressHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`;

const ProgressLabel = styled.div`
  font-weight: 500;
  color: var(--color-text-primary);
`;

const ProgressStatus = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const ResultsSection = styled.div`
  margin-top: 24px;
`;

const ResultsTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  
  th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--color-border);
  }
  
  th {
    background: var(--color-background-secondary);
    font-weight: 600;
    color: var(--color-text-primary);
    position: sticky;
    top: 0;
  }
  
  td {
    color: var(--color-text-secondary);
  }
  
  tr:hover {
    background: var(--color-background-secondary);
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`;

const ResponseTimeIndicator = styled.div<{ responseTime: number }>`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  background: ${props => {
    if (props.responseTime < 1000) return 'var(--color-success-light)';
    if (props.responseTime < 3000) return 'var(--color-warning-light)';
    return 'var(--color-error-light)';
  }};
  color: ${props => {
    if (props.responseTime < 1000) return 'var(--color-success)';
    if (props.responseTime < 3000) return 'var(--color-warning)';
    return 'var(--color-error)';
  }};
`;

// ============= 類型定義 =============

interface HealthCheckResult {
  id: string;
  url: string;
  status: 'success' | 'failed' | 'timeout' | 'testing';
  responseTime?: number;
  errorMessage?: string;
  timestamp: Date;
  healthScore: number;
}

interface HealthCheckStats {
  total: number;
  tested: number;
  passed: number;
  failed: number;
  avgResponseTime: number;
  successRate: number;
}

interface HealthCheckEngineProps {
  proxies: any[];
  onHealthCheckComplete?: (results: HealthCheckResult[]) => void;
  className?: string;
}

// ============= 主要組件 =============

export const HealthCheckEngine: React.FC<HealthCheckEngineProps> = ({
  proxies,
  onHealthCheckComplete,
  className
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<HealthCheckResult[]>([]);
  const [selectedProxies] = useState<string[]>([]);
  const [testUrl, setTestUrl] = useState('https://httpbin.org/ip');
  const [timeout, setTimeout] = useState(10000);
  const [concurrency, setConcurrency] = useState(5);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  
  const { showNotification } = useNotification();

  // ============= 計算屬性 =============

  const stats: HealthCheckStats = useMemo(() => {
    const total = results.length;
    const tested = results.filter(r => r.status !== 'testing').length;
    const passed = results.filter(r => r.status === 'success').length;
    const failed = results.filter(r => r.status === 'failed' || r.status === 'timeout').length;
    const avgResponseTime = results
      .filter(r => r.responseTime)
      .reduce((sum, r) => sum + (r.responseTime || 0), 0) / (passed || 1);
    const successRate = total > 0 ? (passed / tested) * 100 : 0;

    return {
      total,
      tested,
      passed,
      failed,
      avgResponseTime: Math.round(avgResponseTime),
      successRate: Math.round(successRate * 100) / 100
    };
  }, [results]);

  const filteredResults = useMemo(() => {
    if (filterStatus === 'all') return results;
    return results.filter(result => result.status === filterStatus);
  }, [results, filterStatus]);

  // ============= 健康檢查函數 =============

  /**
   * 測試單個代理的健康狀態
   */
  const testSingleProxy = useCallback(async (proxy: any): Promise<HealthCheckResult> => {
    const startTime = Date.now();
    const result: HealthCheckResult = {
      id: proxy.id,
      url: proxy.url,
      status: 'testing',
      timestamp: new Date(),
      healthScore: 0
    };

    try {
      // 模擬 API 調用
      const response = await fetch('/api/proxy/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          proxyUrl: proxy.url,
          testUrl,
          timeout
        })
      });

      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        await response.json();
        result.status = 'success';
        result.responseTime = responseTime;
        result.healthScore = calculateHealthScore(responseTime, true);
      } else {
        result.status = 'failed';
        result.errorMessage = `HTTP ${response.status}`;
        result.healthScore = 0;
      }
    } catch (error) {
      const responseTime = Date.now() - startTime;
      result.status = responseTime >= timeout ? 'timeout' : 'failed';
      result.errorMessage = error instanceof Error ? error.message : '未知錯誤';
      result.healthScore = 0;
    }

    return result;
  }, [testUrl, timeout]);

  /**
   * 計算健康分數
   */
  const calculateHealthScore = useCallback((responseTime: number, success: boolean): number => {
    if (!success) return 0;
    
    // 基於響應時間計算分數 (0-100)
    if (responseTime < 500) return 100;
    if (responseTime < 1000) return 90;
    if (responseTime < 2000) return 80;
    if (responseTime < 3000) return 70;
    if (responseTime < 5000) return 60;
    return 50;
  }, []);

  /**
   * 開始批量健康檢查
   */
  const startHealthCheck = useCallback(async () => {
    const proxiesToTest = selectedProxies.length > 0 
      ? proxies.filter(p => selectedProxies.includes(p.id))
      : proxies;

    if (proxiesToTest.length === 0) {
      showNotification('請選擇要檢測的代理', 'warning');
      return;
    }

    setIsRunning(true);
    setProgress(0);
    setResults([]);

    try {
      const totalProxies = proxiesToTest.length;
      let completedCount = 0;
      const newResults: HealthCheckResult[] = [];

      // 並發控制
      const chunks = [];
      for (let i = 0; i < proxiesToTest.length; i += concurrency) {
        chunks.push(proxiesToTest.slice(i, i + concurrency));
      }

      for (const chunk of chunks) {
        const chunkPromises = chunk.map(async (proxy) => {
          const result = await testSingleProxy(proxy);
          completedCount++;
          setProgress((completedCount / totalProxies) * 100);
          return result;
        });

        const chunkResults = await Promise.all(chunkPromises);
        newResults.push(...chunkResults);
        setResults([...newResults]);
      }

      onHealthCheckComplete?.(newResults);
      showNotification(`健康檢查完成：${newResults.filter(r => r.status === 'success').length}/${totalProxies} 通過`, 'success');
    } catch (error) {
      showNotification('健康檢查過程中發生錯誤', 'error');
    } finally {
      setIsRunning(false);
    }
  }, [proxies, selectedProxies, concurrency, testSingleProxy, onHealthCheckComplete, showNotification]);

  /**
   * 停止健康檢查
   */
  const stopHealthCheck = useCallback(() => {
    setIsRunning(false);
    showNotification('健康檢查已停止', 'info');
  }, [showNotification]);

  /**
   * 清除檢查結果
   */
  const clearResults = useCallback(() => {
    setResults([]);
    setProgress(0);
  }, []);

  // ============= 渲染 =============

  return (
    <HealthCheckContainer className={className}>
      <HeaderSection>
        <Title>健康檢查引擎</Title>
        <ActionButtons>
          <Button
            variant="primary"
            onClick={startHealthCheck}
            disabled={isRunning || proxies.length === 0}
          >
            {isRunning ? '檢查中...' : '開始檢查'}
          </Button>
          {isRunning && (
            <Button
              variant="outline"
              onClick={stopHealthCheck}
            >
              停止檢查
            </Button>
          )}
          <Button
            variant="outline"
            onClick={clearResults}
            disabled={isRunning || results.length === 0}
          >
            清除結果
          </Button>
        </ActionButtons>
      </HeaderSection>

      {/* 控制面板 */}
      <ControlsSection>
        <div>
          <label>測試 URL</label>
          <Input
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
            placeholder="輸入測試 URL"
            disabled={isRunning}
          />
        </div>
        <div>
          <label>超時時間 (毫秒)</label>
          <Input
            type="number"
            value={timeout}
            onChange={(e) => setTimeout(Number(e.target.value))}
            min="1000"
            max="60000"
            disabled={isRunning}
          />
        </div>
        <div>
          <label>並發數</label>
          <Input
            type="number"
            value={concurrency}
            onChange={(e) => setConcurrency(Number(e.target.value))}
            min="1"
            max="20"
            disabled={isRunning}
          />
        </div>
        <div>
          <label>結果篩選</label>
          <Select
            value={filterStatus}
            onChange={(value) => setFilterStatus(value as string)}
            options={[
              { value: 'all', label: '全部結果' },
              { value: 'success', label: '成功' },
              { value: 'failed', label: '失敗' },
              { value: 'timeout', label: '超時' }
            ]}
          />
        </div>
      </ControlsSection>

      {/* 統計資訊 */}
      <StatsGrid>
        <StatCard>
          <StatValue>{stats.total}</StatValue>
          <StatLabel>總代理數</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{stats.tested}</StatValue>
          <StatLabel>已檢測</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{stats.passed}</StatValue>
          <StatLabel>通過</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{stats.failed}</StatValue>
          <StatLabel>失敗</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{stats.avgResponseTime}ms</StatValue>
          <StatLabel>平均響應時間</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{stats.successRate}%</StatValue>
          <StatLabel>成功率</StatLabel>
        </StatCard>
      </StatsGrid>

      {/* 進度條 */}
      {isRunning && (
        <ProgressSection>
          <ProgressHeader>
            <ProgressLabel>檢查進度</ProgressLabel>
            <ProgressStatus>{Math.round(progress)}% 完成</ProgressStatus>
          </ProgressHeader>
          <Progress percent={progress} />
        </ProgressSection>
      )}

      {/* 檢查結果 */}
      {results.length > 0 && (
        <ResultsSection>
          <h3>檢查結果 ({filteredResults.length})</h3>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <ResultsTable>
              <thead>
                <tr>
                  <th>代理地址</th>
                  <th>狀態</th>
                  <th>響應時間</th>
                  <th>健康分數</th>
                  <th>錯誤訊息</th>
                  <th>檢測時間</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.map((result) => (
                  <tr key={result.id}>
                    <td>{result.url}</td>
                    <td>
                      <StatusIndicator
                        status={
                          result.status === 'success' ? 'success' :
                          result.status === 'timeout' ? 'warning' : 'error'
                        }
                        text={result.status}
                        size="small"
                      />
                    </td>
                    <td>
                      {result.responseTime ? (
                        <ResponseTimeIndicator responseTime={result.responseTime}>
                          {result.responseTime}ms
                        </ResponseTimeIndicator>
                      ) : '-'}
                    </td>
                    <td>
                      <div style={{ 
                        color: result.healthScore >= 80 ? 'var(--color-success)' :
                               result.healthScore >= 60 ? 'var(--color-warning)' : 'var(--color-error)'
                      }}>
                        {result.healthScore}/100
                      </div>
                    </td>
                    <td>
                      {result.errorMessage ? (
                        <span style={{ color: 'var(--color-error)', fontSize: '0.75rem' }}>
                          {result.errorMessage}
                        </span>
                      ) : '-'}
                    </td>
                    <td>{formatDateTime(result.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </ResultsTable>
          </div>
        </ResultsSection>
      )}
    </HealthCheckContainer>
  );
};

export default HealthCheckEngine;