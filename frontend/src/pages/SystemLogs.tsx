/**
 * 系統日誌管理分頁組件
 * 
 * 提供完整的日誌管理功能，包括：
 * - 日誌列表檢視與篩選
 * - 即時日誌流
 * - 日誌搜尋與分析
 * - 日誌導出與下載
 * - 日誌統計與視覺化
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import styled from 'styled-components';
import {
  type LogEntry,
  type LogFilters,
  type LogLevel,
  type PaginationParams,
} from '../types';
import { PageLayout } from '../components/layout/PageLayout';
import { DataTable } from '../components/ui/DataTable';
import { StatusIndicator } from '../components/ui/StatusIndicator';
import { Button, Input, Card, Modal, Select, Switch } from '../components/ui';
import { useSystemLogs } from '../hooks/useSystemLogs';
import { useNotification } from '../hooks/useNotification';
import { useWebSocket } from '../hooks/useWebSocket';
import { formatDateTime, formatFileSize } from '../utils/formatters';
import { downloadFile } from '../utils/download';

// ============= 樣式定義 =============

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  background: ${props => props.theme.colors.background};
  min-height: 100vh;
`;

const FiltersSection = styled(Card)`
  padding: 20px;
  background: ${props => props.theme.colors.background.primary};
  border-radius: 8px;
  box-shadow: ${props => props.theme.shadows.small};
`;

const FiltersGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
`;

const ActionsBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
`;

const StatsCards = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled(Card)`
  padding: 16px;
  text-align: center;
  background: ${props => props.theme.colors.background.primary};
  border-radius: 8px;
  box-shadow: ${props => props.theme.shadows.small};
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: ${props => props.theme.shadows.medium};
  }
`;

const StatValue = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: ${props => props.theme.colors.text.primary};
  margin-bottom: 4px;
`;

const StatLabel = styled.div`
  font-size: 0.75rem;
  color: ${props => props.theme.colors.text.secondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const LiveLogSection = styled(Card)`
  padding: 20px;
  background: ${props => props.theme.colors.background.primary};
  border-radius: 8px;
  box-shadow: ${props => props.theme.shadows.small};
  margin-bottom: 24px;
`;

const LiveLogHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h3 {
    margin: 0;
    color: ${props => props.theme.colors.text};
    font-size: 1.125rem;
  }
`;

const LiveLogContainer = styled.div`
  background: ${props => props.theme.colors.background.secondary};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
  height: 300px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  padding: 12px;
`;

const LogEntryStyled = styled.div<{ level: LogLevel }>`
  padding: 4px 0;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  color: ${props => {
    switch (props.level) {
      case 'error': return props.theme.colors.status.error;
      case 'warning': return props.theme.colors.status.warning;
      case 'info': return props.theme.colors.status.info;
      case 'debug': return props.theme.colors.text.secondary;
      default: return props.theme.colors.text;
    }
  }};
  
  &:last-child {
    border-bottom: none;
  }
  
  .timestamp {
    color: ${props => props.theme.colors.text.secondary};
    margin-right: 8px;
  }
  
  .level {
    font-weight: bold;
    margin-right: 8px;
    text-transform: uppercase;
  }
  
  .message {
    word-break: break-word;
  }
`;

const LogDetails = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
  
  .log-message {
    font-weight: 500;
    color: ${props => props.theme.colors.text};
    word-break: break-word;
  }
  
  .log-meta {
    font-size: 0.75rem;
    color: ${props => props.theme.colors.text.secondary};
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  
  .log-source {
    background: ${props => props.theme.colors.background.secondary};
    padding: 2px 6px;
    border-radius: 3px;
    font-family: monospace;
  }
`;

const LevelBadge = styled.span<{ level: LogLevel }>`
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  background: ${props => {
    switch (props.level) {
      case 'error': return props.theme.colors.background.secondary;
      case 'warning': return props.theme.colors.background.secondary;
      case 'info': return props.theme.colors.background.secondary;
      case 'debug': return props.theme.colors.background.secondary;
      default: return props.theme.colors.background.secondary;
    }
  }};
  color: ${props => {
    switch (props.level) {
      case 'error': return props.theme.colors.status.error;
      case 'warning': return props.theme.colors.status.warning;
      case 'info': return props.theme.colors.status.info;
      case 'debug': return props.theme.colors.text.secondary;
      default: return props.theme.colors.text.secondary;
    }
  }};
`;

const ExportForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
`;

// ============= 介面定義 =============

interface SystemLogsProps {
  className?: string;
}

interface LiveLogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source?: string;
}

// ============= 主要組件 =============

export const SystemLogs: React.FC<SystemLogsProps> = ({ className }) => {
  // ============= 狀態管理 =============
  
  const {
    state,
    actions: {
      loadLogs,
      searchLogs,
      exportLogs
    }
  } = useSystemLogs();
  
  const { showNotification } = useNotification();
  
  const [filters, setFilters] = useState<LogFilters>({
    level: undefined,
    category: undefined,
    source: undefined,
    search: '',
    dateRange: undefined
  });
  
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    size: 50
  });
  

  
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportRequest, setExportRequest] = useState({
    format: 'json' as 'json' | 'csv' | 'txt',
    filters: {},
    includeMetadata: true,
    compression: false
  });
  
  const [liveLogsEnabled, setLiveLogsEnabled] = useState(false);
  const [liveLogs, setLiveLogs] = useState<LiveLogEntry[]>([]);
  const [statistics, setStatistics] = useState<any | null>(null);
  
  const liveLogContainerRef = useRef<HTMLDivElement>(null);
  const maxLiveLogEntries = 100;
  
  // WebSocket 連接用於即時日誌
  const { 
    isConnected: wsConnected, 
    connect: wsConnect, 
    disconnect: wsDisconnect,
    lastMessage
  } = useWebSocket('ws://localhost:8000/ws/logs');
  
  // 處理 WebSocket 訊息
   useEffect(() => {
     if (lastMessage && lastMessage.type === 'log_entry') {
       const newEntry: LiveLogEntry = {
         id: lastMessage.data.id,
         timestamp: lastMessage.data.timestamp,
         level: lastMessage.data.level,
         message: lastMessage.data.message,
         source: lastMessage.data.source
       };
       
       setLiveLogs(prev => {
         const updated = [newEntry, ...prev];
         return updated.slice(0, maxLiveLogEntries);
       });
       
       // 自動滾動到最新日誌
       if (liveLogContainerRef.current) {
         liveLogContainerRef.current.scrollTop = 0;
       }
     }
   }, [lastMessage]);
  
  // 處理 WebSocket 連接錯誤
  useEffect(() => {
    if (!wsConnected && liveLogsEnabled) {
      showNotification('即時日誌連接失敗', 'error');
    }
  }, [wsConnected, liveLogsEnabled, showNotification]);
  
  // ============= 計算屬性 =============
  
  const filteredLogs = useMemo(() => {
    let filtered = state.logs;
    
    // 等級篩選
    if (filters.level) {
      filtered = filtered.filter(log => filters.level?.includes(log.level));
    }
    
    // 分類篩選
    if (filters.category) {
      filtered = filtered.filter(log => log.category === filters.category);
    }
    
    // 來源篩選
    if (filters.source) {
      filtered = filtered.filter(log => filters.source?.includes(log.source));
    }
    
    // 搜尋篩選
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchLower) ||
        log.source?.toLowerCase().includes(searchLower) ||
        log.details?.toLowerCase().includes(searchLower)
      );
    }
    
    // 日期範圍篩選
    if (filters.dateRange) {
      const [start, end] = filters.dateRange;
      filtered = filtered.filter(log => {
        const logDate = new Date(log.timestamp);
        return logDate >= new Date(start) && logDate <= new Date(end);
      });
    }
    
    return filtered;
  }, [state.logs, filters]);
  
  const tableColumns = useMemo(() => [
    {
      key: 'level' as keyof LogEntry,
      title: '等級',
      sortable: true,
      width: '80px',
      render: (log: LogEntry) => (
        <LevelBadge level={log.level}>
          {log.level}
        </LevelBadge>
      )
    },
    {
      key: 'timestamp' as keyof LogEntry,
      title: '時間',
      sortable: true,
      width: '160px',
      render: (log: LogEntry) => (
        <div style={{ fontSize: '0.875rem' }}>
          {formatDateTime(log.timestamp)}
        </div>
      )
    },
    {
      key: 'message' as keyof LogEntry,
      title: '日誌內容',
      sortable: true,
      render: (log: LogEntry) => (
        <LogDetails>
          <div className="log-message">{log.message}</div>
          <div className="log-meta">
            {log.source && (
              <span className="log-source">{log.source}</span>
            )}
            {log.category && (
              <span>分類: {log.category}</span>
            )}
            {log.userId && (
              <span>用戶: {log.userId}</span>
            )}
            {log.requestId && (
              <span>請求: {log.requestId}</span>
            )}
          </div>
        </LogDetails>
      )
    },
    {
      key: 'actions' as keyof LogEntry,
      title: '操作',
      width: '100px',
      render: (log: LogEntry) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleViewLogDetails(log)}
          >
            詳情
          </Button>
        </div>
      )
    }
  ], []);
  
  // ============= 事件處理 =============
  
  const handleLoadLogs = useCallback(async () => {
    try {
      await loadLogs({ filters, pagination });
    } catch (error) {
      showNotification('載入日誌失敗', 'error');
    }
  }, [filters, pagination, loadLogs, showNotification]);
  
  const handleFilterChange = useCallback((key: keyof LogFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一頁
  }, []);
  

  

  
  const handleSearch = useCallback(async (searchTerm: string) => {
    try {
      await searchLogs({ query: searchTerm, filters, pagination });
    } catch (error) {
      showNotification('搜尋日誌失敗', 'error');
    }
  }, [filters, searchLogs, showNotification]);
  
  const handleExport = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await exportLogs({
        ...exportRequest,
        filters: filters
      });
      
      // 下載檔案
      await downloadFile(result.downloadUrl, result.filename);
      
      setShowExportModal(false);
      showNotification(`日誌導出成功：${result.filename}`, 'success');
    } catch (error) {
      showNotification('日誌導出失敗', 'error');
    }
  }, [exportRequest, filters, exportLogs, showNotification]);
  
  const handleViewLogDetails = useCallback((log: LogEntry) => {
    // 顯示日誌詳情模態框
    // 這裡可以實現一個詳細的日誌檢視器
    console.log('查看日誌詳情:', log);
  }, []);
  
  const handleToggleLiveLogs = useCallback((enabled: boolean) => {
    setLiveLogsEnabled(enabled);
    
    if (enabled) {
      wsConnect();
    } else {
      wsDisconnect();
      setLiveLogs([]);
    }
  }, [wsConnect, wsDisconnect]);
  
  const handleClearLiveLogs = useCallback(() => {
    setLiveLogs([]);
  }, []);
  
  const loadStatistics = useCallback(async () => {
    try {
      // TODO: 實現統計數據獲取
      const stats = null;
      setStatistics(stats);
    } catch (error) {
      console.error('載入統計資料失敗:', error);
    }
  }, [filters]);
  
  // ============= 生命週期 =============
  
  useEffect(() => {
    handleLoadLogs();
  }, [handleLoadLogs]);
  
  useEffect(() => {
    loadStatistics();
  }, [loadStatistics]);
  
  // ============= 渲染 =============
  
  return (
    <PageLayout
      title="系統日誌"
      subtitle="檢視和管理系統運行日誌"
      loading={state.loading}
      error={state.error}
      className={className}
      toolbar={
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            variant="outline"
            onClick={() => setShowExportModal(true)}
            disabled={state.loading}
          >
            導出日誌
          </Button>
          <Button
            variant="outline"
            onClick={handleLoadLogs}
            disabled={state.loading}
          >
            重新整理
          </Button>
        </div>
      }
    >
      <LogsContainer>
        {/* 統計卡片 */}
        {statistics && (
          <StatsCards>
            <StatCard>
              <StatValue>{statistics.totalLogs}</StatValue>
              <StatLabel>總日誌數</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{statistics.errorCount}</StatValue>
              <StatLabel>錯誤</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{statistics.warningCount}</StatValue>
              <StatLabel>警告</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{statistics.infoCount}</StatValue>
              <StatLabel>資訊</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{statistics.debugCount}</StatValue>
              <StatLabel>除錯</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{formatFileSize(statistics.totalSize)}</StatValue>
              <StatLabel>總大小</StatLabel>
            </StatCard>
          </StatsCards>
        )}
        
        {/* 即時日誌區域 */}
        <LiveLogSection>
          <LiveLogHeader>
            <h3>即時日誌流</h3>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Switch
                  checked={liveLogsEnabled}
                  onChange={handleToggleLiveLogs}
                />
                <span>啟用即時日誌</span>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={handleClearLiveLogs}
                disabled={!liveLogsEnabled || liveLogs.length === 0}
              >
                清空
              </Button>
              <StatusIndicator
                status={wsConnected ? 'success' : 'error'}
                size="small"
              />
            </div>
          </LiveLogHeader>
          
          <LiveLogContainer ref={liveLogContainerRef}>
            {liveLogs.length === 0 ? (
              <div style={{ 
                textAlign: 'center', 
                color: 'var(--text-secondary)', 
                padding: '40px',
                fontStyle: 'italic'
              }}>
                {liveLogsEnabled ? '等待日誌...' : '請啟用即時日誌以查看實時更新'}
              </div>
            ) : (
              liveLogs.map(entry => (
                <LogEntryStyled key={entry.id} level={entry.level}>
                  <span className="timestamp">
                    {formatDateTime(entry.timestamp)}
                  </span>
                  <span className="level">
                    [{entry.level}]
                  </span>
                  {entry.source && (
                    <span className="source">
                      {entry.source}:
                    </span>
                  )}
                  <span className="message">
                    {entry.message}
                  </span>
                </LogEntryStyled>
              ))
            )}
          </LiveLogContainer>
        </LiveLogSection>
        
        {/* 篩選區域 */}
        <FiltersSection>
          <FiltersGrid>
            <Input
              placeholder="搜尋日誌內容、來源或詳情..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSearch(e.currentTarget.value);
                }
              }}
            />
            <Select
              placeholder="選擇等級"
              value={filters.level || ''}
              onChange={(value) => handleFilterChange('level', value || undefined)}
              options={[
                { value: '', label: '全部等級' },
                { value: 'error', label: '錯誤' },
                { value: 'warning', label: '警告' },
                { value: 'info', label: '資訊' },
                { value: 'debug', label: '除錯' }
              ]}
            />
            <Select
              placeholder="選擇分類"
              value={filters.category || ''}
              onChange={(value) => handleFilterChange('category', value || undefined)}
              options={[
                { value: '', label: '全部分類' },
                { value: 'crawler', label: '爬蟲' },
                { value: 'proxy', label: '代理' },
                { value: 'task', label: '任務' },
                { value: 'system', label: '系統' },
                { value: 'api', label: 'API' },
                { value: 'auth', label: '認證' }
              ]}
            />
            <Select
              placeholder="選擇來源"
              value={filters.source || ''}
              onChange={(value) => handleFilterChange('source', value || undefined)}
              options={[
                { value: '', label: '全部來源' },
                { value: 'crawler_engine', label: '爬蟲引擎' },
                { value: 'proxy_manager', label: '代理管理器' },
                { value: 'task_scheduler', label: '任務排程器' },
                { value: 'api_server', label: 'API 伺服器' },
                { value: 'web_interface', label: 'Web 介面' }
              ]}
            />
          </FiltersGrid>
        </FiltersSection>
        
        {/* 操作列 */}
        <ActionsBar>
          <div>
            找到 {filteredLogs.length} 條日誌
          </div>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              variant="outline"
              onClick={() => handleSearch(filters.search || '')}
              disabled={state.loading}
            >
              搜尋
            </Button>
          </div>
        </ActionsBar>
        
        {/* 日誌列表 */}
        <DataTable
            dataSource={filteredLogs}
          columns={tableColumns}
          pagination={{
            current: pagination.page,
            pageSize: pagination.size,
            total: state.logs.length,
            showSizeChanger: true,
            showQuickJumper: true,
            onChange: (page: number, pageSize: number) => {
              setPagination(prev => ({ ...prev, page, size: pageSize }));
            }
          }}

          loading={state.loading}

          
        />
        
        {/* 導出日誌模態框 */}
        <Modal
          visible={showExportModal}
          onClose={() => setShowExportModal(false)}
          title="導出日誌"
        >
          <ExportForm onSubmit={handleExport}>
            <FormRow>
              <Select
                value={exportRequest.format}
                onChange={(value) => setExportRequest((prev: any) => ({ ...prev, format: value as any }))}
                options={[
                  { value: 'json', label: 'JSON' },
                  { value: 'csv', label: 'CSV' },
                  { value: 'txt', label: 'TXT' }
                ]}
                placeholder="選擇導出格式"
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  id="includeMetadata"
                  checked={exportRequest.includeMetadata}
                  onChange={(e) => setExportRequest((prev: any) => ({ 
                    ...prev, 
                    includeMetadata: e.target.checked 
                  }))}
                />
                <label htmlFor="includeMetadata">包含元數據</label>
              </div>
            </FormRow>
            
            <FormRow>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  id="compression"
                  checked={exportRequest.compression}
                  onChange={(e) => setExportRequest((prev: any) => ({ 
                    ...prev, 
                    compression: e.target.checked 
                  }))}
                />
                <label htmlFor="compression">壓縮檔案</label>
              </div>
            </FormRow>
            
            <div style={{ 
              padding: '12px', 
              background: 'var(--background-secondary)', 
              borderRadius: '4px',
              fontSize: '0.875rem',
              color: 'var(--text-secondary)'
            }}>
              將導出當前篩選條件下的所有日誌。大量日誌可能需要較長時間處理。
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowExportModal(false)}
              >
                取消
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={state.loading}
              >
                導出
              </Button>
            </div>
          </ExportForm>
        </Modal>
      </LogsContainer>
    </PageLayout>
  );
};

export default SystemLogs;