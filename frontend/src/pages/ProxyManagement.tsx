/**
 * 代理管理分頁組件
 * 
 * 提供完整的代理管理功能，包括：
 * - 代理列表檢視與篩選
 * - 代理新增、編輯、刪除
 * - 批量操作與測試
 * - 即時狀態監控
 * - 效能分析
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import type {
  ProxyNode,
  ProxyFilters,
  PaginationParams,
  SortConfig,
  ProxyStatus,
  ProxyProtocol
} from '../types';
import { PageLayout } from '../components/layout/PageLayout';
import { DataTable, type DataTableColumn } from '../components/ui/DataTable';
import { StatusIndicator, type StatusType } from '../components/ui/StatusIndicator';
import { Button, Input, Card, Modal, Select } from '../components/ui';
import { CsvImportModal } from '../components/proxy/CsvImportModal';
import { HealthCheckEngine } from '../components/proxy/HealthCheckEngine';
import { StatsDashboard } from '../components/proxy/StatsDashboard';
import { BatchOperations } from '../components/proxy/BatchOperations';
import { useProxyManagement } from '../hooks/useProxyManagement';
import { useNotification } from '../hooks/useNotification';
import { formatDateTime } from '../utils/formatters';
import { validateProxyUrl } from '../utils/validators';

// ============= 樣式定義 =============

const ProxyManagementContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  background: var(--color-background);
  min-height: 100vh;
`;

const FiltersSection = styled(Card)`
  padding: 20px;
  background: var(--color-surface);
  border-radius: 8px;
  box-shadow: var(--shadow-small);
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

const BulkActions = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
`;

const StatsCards = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled(Card)`
  padding: 20px;
  text-align: center;
  background: var(--color-background-secondary);
  border-radius: 8px;
  box-shadow: var(--shadow-small);
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-medium);
  }
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 8px;
`;

const StatLabel = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ProxyForm = styled.form`
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

interface ProxyFormData {
  url: string;
  type: 'http' | 'https' | 'socks4' | 'socks5';
  username?: string;
  password?: string;
  country?: string;
  tags: string[];
  maxConcurrent: number;
  timeout: number;
  enabled: boolean;
}

interface ProxyManagementProps {
  className?: string;
}

// ============= 主要組件 =============

export const ProxyManagement: React.FC<ProxyManagementProps> = ({ className }) => {
  // ============= 狀態管理 =============
  
  const {
    state,
    actions: {
      loadProxies,
      createProxy,
      updateProxy,
      deleteProxy,
      bulkOperation,
      testProxy
    }
  } = useProxyManagement();
  
  const { showNotification } = useNotification();
  
  const [filters, setFilters] = useState<ProxyFilters>({
    status: undefined,
    country: undefined,
    type: undefined,
    tags: [],
    search: '',
    healthScore: { min: 0, max: 100 }
  });
  
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    size: 20
  });
  
  const [sortConfig] = useState<SortConfig>({
    field: 'lastChecked',
    direction: 'desc'
  });
  
  const [selectedProxies, setSelectedProxies] = useState<string[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showHealthCheck, setShowHealthCheck] = useState(false);
  const [showStatsDashboard, setShowStatsDashboard] = useState(false);
  const [editingProxy, setEditingProxy] = useState<ProxyNode | null>(null);
  
  const [formData, setFormData] = useState<ProxyFormData>({
    url: '',
    type: 'http',
    username: '',
    password: '',
    country: '',
    tags: [],
    maxConcurrent: 10,
    timeout: 30000,
    enabled: true
  });
  
  // ============= 計算屬性 =============
  
  const stats = useMemo(() => {
    const proxies = state.proxies;
    const total = proxies.length;
    const active = proxies.filter(p => p.status === 'active').length;
    const healthy = proxies.filter(p => (p.healthScore || 0) >= 80).length;
    const avgResponseTime = proxies.reduce((sum, p) => sum + (p.responseTime || 0), 0) / total || 0;
    
    return {
      total,
      active,
      healthy,
      avgResponseTime: Math.round(avgResponseTime)
    };
  }, [state.proxies]);
  
  const filteredProxies = useMemo(() => {
    let filtered = state.proxies;
    
    // 狀態篩選
    if (filters.status) {
      filtered = filtered.filter(proxy => filters.status!.includes(proxy.status));
    }
    
    // 國家篩選
    if (filters.country) {
      filtered = filtered.filter(proxy => proxy.country === filters.country);
    }
    
    // 類型篩選
    if (filters.type) {
      filtered = filtered.filter(proxy => proxy.type === filters.type);
    }
    
    // 標籤篩選
    if (filters.tags && filters.tags.length > 0) {
      filtered = filtered.filter(proxy => 
        filters.tags!.some(tag => (proxy.tags || []).includes(tag))
      );
    }
    
    // 搜尋篩選
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(proxy => 
        (proxy.url || '').toLowerCase().includes(searchLower) ||
        proxy.country?.toLowerCase().includes(searchLower) ||
        (proxy.tags || []).some(tag => tag.toLowerCase().includes(searchLower))
      );
    }
    
    // 健康分數篩選
    if (filters.healthScore) {
      filtered = filtered.filter(proxy => 
        (proxy.healthScore || 0) >= filters.healthScore!.min &&
        (proxy.healthScore || 0) <= filters.healthScore!.max
      );
    }
    
    return filtered;
  }, [state.proxies, filters]);
  
  const tableColumns: DataTableColumn<ProxyNode>[] = useMemo(() => [
    {
      key: 'status',
      title: '狀態',
      sortable: true,
      render: (proxy: ProxyNode) => {
          const statusMap: Record<ProxyStatus, StatusType> = {
            'active': 'success',
            'inactive': 'error',
            'testing': 'warning',
            'error': 'error',
            'unknown': 'info'
          };
          return (
            <StatusIndicator 
               status={statusMap[proxy.status] || 'info'}
               size="small"
               text={proxy.status}
             />
          );
        }
    },
    {
      key: 'url',
      title: '代理地址',
      sortable: true,
      render: (proxy: ProxyNode) => (
        <div>
          <div style={{ fontWeight: 'medium' }}>{proxy.url}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            {(proxy.type || 'http').toUpperCase()} • {proxy.country || '未知'}
          </div>
        </div>
      )
    },
    {
      key: 'healthScore',
      title: '健康分數',
      sortable: true,
      render: (proxy: ProxyNode) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold', color: (proxy.healthScore || 0) >= 80 ? 'var(--success)' : (proxy.healthScore || 0) >= 50 ? 'var(--warning)' : 'var(--error)' }}>
            {proxy.healthScore || 0}%
          </div>
        </div>
      )
    },
    {
      key: 'responseTime',
      title: '回應時間',
      sortable: true,
      render: (proxy: ProxyNode) => (
        <div style={{ textAlign: 'center' }}>
          {proxy.responseTime ? `${proxy.responseTime}ms` : '-'}
        </div>
      )
    },
    {
      key: 'lastChecked',
      title: '最後檢查',
      sortable: true,
      render: (proxy: ProxyNode) => (
        <div style={{ fontSize: '0.875rem' }}>
          {proxy.lastChecked ? formatDateTime(proxy.lastChecked) : '從未檢查'}
        </div>
      )
    },
    {
      key: 'tags',
      title: '標籤',
      render: (proxy: ProxyNode) => (
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {(proxy.tags || []).map(tag => (
            <span 
              key={tag}
              style={{
                padding: '2px 8px',
                background: 'var(--primary-light)',
                color: 'var(--primary)',
                borderRadius: '12px',
                fontSize: '0.75rem'
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )
    },
    {
key: 'actions' as any,
      title: '操作',
      render: (proxy: ProxyNode) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleTestProxy(proxy.id)}
            disabled={state.loading}
          >
            測試
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleEditProxy(proxy)}
          >
            編輯
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleDeleteProxy(proxy.id)}
            disabled={state.loading}
          >
            刪除
          </Button>
        </div>
      )
    }
  ], [state.loading]);
  
  // ============= 事件處理 =============
  
  const handleLoadProxies = useCallback(async () => {
    try {
      await loadProxies({ filters, pagination, sort: sortConfig });
    } catch (error) {
      showNotification('載入代理列表失敗', 'error');
    }
  }, [filters, pagination, sortConfig, loadProxies, showNotification]);
  
  const handleFilterChange = useCallback((key: keyof ProxyFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一頁
  }, []);
  

  
  const handlePageChange = useCallback((page: number, size: number) => {
    setPagination({ page, size });
  }, []);
  
  const handleAddProxy = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 驗證表單
    if (!validateProxyUrl(formData.url)) {
      showNotification('代理地址格式不正確', 'error');
      return;
    }
    
    try {
      await createProxy(formData);
      setShowAddModal(false);
      setFormData({
        url: '',
        type: 'http',
        username: '',
        password: '',
        country: '',
        tags: [],
        maxConcurrent: 10,
        timeout: 30000,
        enabled: true
      });
      showNotification('代理新增成功', 'success');
      handleLoadProxies();
    } catch (error) {
      showNotification('代理新增失敗', 'error');
    }
  }, [formData, createProxy, showNotification, handleLoadProxies]);
  
  const handleEditProxy = useCallback((proxy: ProxyNode) => {
    setEditingProxy(proxy);
    setFormData({
      url: proxy.url || '',
      type: (proxy.type || 'http') as ProxyProtocol,
      username: proxy.username || '',
      password: proxy.password || '',
      country: proxy.country || '',
      tags: proxy.tags || [],
      maxConcurrent: proxy.maxConcurrent || 1,
      timeout: proxy.timeout || 5000,
      enabled: proxy.enabled ?? true
    });
    setShowAddModal(true);
  }, []);
  
  const handleUpdateProxy = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!editingProxy) return;
    
    try {
      await updateProxy(editingProxy.id, formData);
      setShowAddModal(false);
      setEditingProxy(null);
      showNotification('代理更新成功', 'success');
      handleLoadProxies();
    } catch (error) {
      showNotification('代理更新失敗', 'error');
    }
  }, [editingProxy, formData, updateProxy, showNotification, handleLoadProxies]);
  
  const handleDeleteProxy = useCallback(async (proxyId: string) => {
    if (!confirm('確定要刪除此代理嗎？')) return;
    
    try {
      await deleteProxy(proxyId);
      showNotification('代理刪除成功', 'success');
      handleLoadProxies();
    } catch (error) {
      showNotification('代理刪除失敗', 'error');
    }
  }, [deleteProxy, showNotification, handleLoadProxies]);
  
  const handleTestProxy = useCallback(async (proxyId: string) => {
    try {
      await testProxy(proxyId);
      showNotification('代理測試完成', 'success');
    } catch (error) {
      showNotification('代理測試失敗', 'error');
    }
  }, [testProxy, showNotification]);
  
  const handleBulkOperation = useCallback(async (operation: string) => {
    if (selectedProxies.length === 0) {
      showNotification('請選擇要操作的代理', 'warning');
      return;
    }
    
    try {
      const result = await bulkOperation(operation, selectedProxies);
      showNotification(`批量操作完成：成功 ${result.success}，失敗 ${result.failed}`, 'success');
      setSelectedProxies([]);
      handleLoadProxies();
    } catch (error) {
      showNotification('批量操作失敗', 'error');
    }
  }, [selectedProxies, bulkOperation, showNotification, handleLoadProxies]);

  const handleCsvImport = useCallback(async (proxies: any[]) => {
    try {
      const importPromises = proxies.map(proxy => {
        // 確保端口存在，如果沒有則使用默認端口
        const port = proxy.port || (proxy.protocol === 'https' ? 443 : proxy.protocol === 'socks4' || proxy.protocol === 'socks5' ? 1080 : 8080);
        const protocol = proxy.protocol || 'http';
        
        const proxyData = {
          url: `${protocol}://${proxy.ip}:${port}`,
          type: protocol as ProxyProtocol,
          username: proxy.username,
          password: proxy.password,
          country: proxy.country,
          tags: [],
          maxConcurrent: 10,
          timeout: 30000,
          enabled: true
        };
        return createProxy(proxyData);
      });
      
      await Promise.all(importPromises);
      handleLoadProxies();
      showNotification(`成功導入 ${proxies.length} 個代理`, 'success');
    } catch (error) {
      console.error('CSV導入錯誤:', error);
      showNotification('批量導入失敗', 'error');
      throw error;
    }
  }, [createProxy, handleLoadProxies, showNotification]);

  const handleHealthCheckComplete = useCallback((results: any[]) => {
    // 處理健康檢查完成後的邏輯
    const successCount = results.filter(r => r.status === 'success').length;
    const totalCount = results.length;
    showNotification(`健康檢查完成：${successCount}/${totalCount} 通過`, 'success');
    
    // 重新載入代理列表以更新健康狀態
    handleLoadProxies();
  }, [showNotification, handleLoadProxies]);

  // 批量操作處理函數
  const handleBatchTest = useCallback(async (proxyIds: string[]) => {
    try {
      // 調用批量測試 API
      console.log('批量測試代理:', proxyIds);
      // 這裡應該調用實際的 API
    } catch (error) {
      console.error('批量測試失敗:', error);
      throw error;
    }
  }, []);

  const handleBatchDelete = useCallback(async (proxyIds: string[]) => {
    try {
      // 調用批量刪除 API
      console.log('批量刪除代理:', proxyIds);
      // 這裡應該調用實際的 API
    } catch (error) {
      console.error('批量刪除失敗:', error);
      throw error;
    }
  }, []);

  const handleBatchUpdate = useCallback(async (proxyIds: string[], updates: any) => {
    try {
      // 調用批量更新 API
      console.log('批量更新代理:', proxyIds, updates);
      // 這裡應該調用實際的 API
    } catch (error) {
      console.error('批量更新失敗:', error);
      throw error;
    }
  }, []);

  const handleBatchExport = useCallback((proxyIds: string[]) => {
    // 導出選中的代理
    const selectedProxyData = filteredProxies.filter(p => proxyIds.includes(p.id));
    const csvContent = generateCSVContent(selectedProxyData);
    downloadCSV(csvContent, `proxies_export_${new Date().toISOString().split('T')[0]}.csv`);
  }, [filteredProxies]);

  // CSV 生成和下載輔助函數
  const generateCSVContent = useCallback((data: ProxyNode[]) => {
    const headers = ['ID', '代理地址', '端口', '類型', '國家', '狀態', '健康分數', '響應時間', '最後檢查時間'];
    const rows = data.map(proxy => [
      proxy.id,
      proxy.host,
      proxy.port,
      proxy.type || 'http',
      proxy.country || '',
      proxy.status,
      proxy.healthScore || 0,
      proxy.responseTime || 0,
      proxy.lastChecked ? new Date(proxy.lastChecked).toLocaleString() : ''
    ]);
    
    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    return csvContent;
  }, []);

  const downloadCSV = useCallback((content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);
  

  
  // ============= 生命週期 =============
  
  useEffect(() => {
    handleLoadProxies();
  }, [handleLoadProxies]);
  
  // ============= 渲染 =============
  
  return (
    <PageLayout
      title="代理管理"
      subtitle="管理和監控代理節點"
      loading={state.loading}
      error={state.error}
      className={className}
      toolbar={
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            variant="primary"
            onClick={() => setShowAddModal(true)}
            disabled={state.loading}
          >
            新增代理
          </Button>
          <Button
            variant="secondary"
            onClick={() => setShowImportModal(true)}
            disabled={state.loading}
          >
            導入 CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowHealthCheck(!showHealthCheck)}
            disabled={state.loading}
          >
            {showHealthCheck ? '隱藏' : '顯示'}健康檢查
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowStatsDashboard(!showStatsDashboard)}
            disabled={state.loading}
          >
            {showStatsDashboard ? '隱藏' : '顯示'}統計儀表盤
          </Button>
        </div>
      }
    >
      <ProxyManagementContainer>
        {/* 統計卡片 */}
        <StatsCards>
          <StatCard>
            <StatValue>{stats.total}</StatValue>
            <StatLabel>總代理數</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.active}</StatValue>
            <StatLabel>活躍代理</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.healthy}</StatValue>
            <StatLabel>健康代理</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.avgResponseTime}ms</StatValue>
            <StatLabel>平均回應時間</StatLabel>
          </StatCard>
        </StatsCards>
        
        {/* 統計儀表盤 */}
         {showStatsDashboard && (
           <StatsDashboard
             proxies={filteredProxies}
           />
         )}
         
         {/* 批量操作 */}
         <BatchOperations
           proxies={filteredProxies}
           selectedProxies={selectedProxies}
           onSelectionChange={setSelectedProxies}
           onBatchTest={handleBatchTest}
           onBatchDelete={handleBatchDelete}
           onBatchUpdate={handleBatchUpdate}
           onBatchExport={handleBatchExport}
         />
        
        {/* 健康檢查引擎 */}
        {showHealthCheck && (
          <HealthCheckEngine
            proxies={filteredProxies}
            onHealthCheckComplete={(results) => {
              // 更新代理健康狀態
              showNotification('健康檢查結果已更新', 'success');
              handleLoadProxies();
            }}
          />
        )}
        
        {/* 篩選區域 */}
        <FiltersSection>
          <FiltersGrid>
            <Input
              placeholder="搜尋代理地址、國家或標籤..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
            <Select
              placeholder="選擇狀態"
              value={filters.status || ''}
              onChange={(value) => handleFilterChange('status', value || undefined)}
              options={[
                { value: '', label: '全部狀態' },
                { value: 'active', label: '活躍' },
                { value: 'inactive', label: '非活躍' },
                { value: 'error', label: '錯誤' },
                { value: 'testing', label: '測試中' }
              ]}
            />
            <Select
              placeholder="選擇協議"
              value={filters.protocol?.[0] || ''}
              onChange={(value) => handleFilterChange('protocol', value ? [value as any] : undefined)}
              options={[
                { value: '', label: '全部協議' },
                { value: 'http', label: 'HTTP' },
                { value: 'https', label: 'HTTPS' },
                { value: 'socks4', label: 'SOCKS4' },
                { value: 'socks5', label: 'SOCKS5' }
              ]}
            />
            <Select
              placeholder="選擇國家"
              value={filters.country || ''}
              onChange={(value) => handleFilterChange('country', value || undefined)}
              options={[
                { value: '', label: '全部國家' },
                { value: 'US', label: '美國' },
                { value: 'CN', label: '中國' },
                { value: 'JP', label: '日本' },
                { value: 'KR', label: '韓國' },
                { value: 'SG', label: '新加坡' }
              ]}
            />
          </FiltersGrid>
        </FiltersSection>
        
        {/* 操作列 */}
        <ActionsBar>
          <BulkActions>
            <span>已選擇 {selectedProxies.length} 個代理</span>
            {selectedProxies.length > 0 && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkOperation('enable')}
                  disabled={state.loading}
                >
                  啟用
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkOperation('disable')}
                  disabled={state.loading}
                >
                  停用
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkOperation('test')}
                  disabled={state.loading}
                >
                  測試
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkOperation('delete')}
                  disabled={state.loading}
                >
                  刪除
                </Button>
              </>
            )}
          </BulkActions>
          
          <div style={{ display: 'flex', gap: '8px' }}>

            <Button
              variant="outline"
              onClick={handleLoadProxies}
              disabled={state.loading}
            >
              重新整理
            </Button>
          </div>
        </ActionsBar>
        
        {/* 代理列表 */}
        <DataTable
          dataSource={filteredProxies}
          columns={tableColumns}
          pagination={{
            current: pagination.page,
            pageSize: pagination.size,
            total: state.total,
            showSizeChanger: true,
            showQuickJumper: true,
            onChange: handlePageChange
          }}
          loading={state.loading}
          emptyText="沒有找到代理"
        />
        
        {/* 新增/編輯代理模態框 */}
        <Modal
          visible={showAddModal}
          onClose={() => {
            setShowAddModal(false);
            setEditingProxy(null);
          }}
          title={editingProxy ? '編輯代理' : '新增代理'}
        >
          <ProxyForm onSubmit={editingProxy ? handleUpdateProxy : handleAddProxy}>
            <FormRow>
              <Input
                label="代理地址"
                placeholder="http://proxy.example.com:8080"
                value={formData.url}
                onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                required
              />
              <div>
                <label>代理類型</label>
                <Select
                   value={formData.type}
                   onChange={(value) => setFormData(prev => ({ ...prev, type: value as any }))}
                   options={[
                     { value: 'http', label: 'HTTP' },
                     { value: 'https', label: 'HTTPS' },
                     { value: 'socks4', label: 'SOCKS4' },
                     { value: 'socks5', label: 'SOCKS5' }
                   ]}
                 />
              </div>
            </FormRow>
            
            <FormRow>
              <Input
                label="用戶名"
                placeholder="選填"
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
              />
              <Input
                label="密碼"
                type="password"
                placeholder="選填"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
              />
            </FormRow>
            
            <FormRow>
              <Input
                label="國家代碼"
                placeholder="如：US, CN, JP"
                value={formData.country}
                onChange={(e) => setFormData(prev => ({ ...prev, country: e.target.value }))}
              />
              <Input
                label="最大併發數"
                type="number"
                min="1"
                max="100"
                value={formData.maxConcurrent}
                onChange={(e) => setFormData(prev => ({ ...prev, maxConcurrent: parseInt(e.target.value) }))}
              />
            </FormRow>
            
            <FormRow>
              <Input
                label="超時時間 (毫秒)"
                type="number"
                min="1000"
                max="60000"
                value={formData.timeout}
                onChange={(e) => setFormData(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formData.enabled}
                  onChange={(e) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                />
                <label htmlFor="enabled">啟用代理</label>
              </div>
            </FormRow>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowAddModal(false);
                  setEditingProxy(null);
                }}
              >
                取消
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={state.loading}
              >
                {editingProxy ? '更新' : '新增'}
              </Button>
            </div>
          </ProxyForm>
        </Modal>
        
        {/* CSV 導入模態框 */}
        <CsvImportModal
          isOpen={showImportModal}
          onClose={() => setShowImportModal(false)}
          onImport={handleCsvImport}
        />
      </ProxyManagementContainer>
    </PageLayout>
  );
};

export default ProxyManagement;