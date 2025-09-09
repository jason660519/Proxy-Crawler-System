/**
 * 批量操作組件
 * 
 * 提供代理批量操作功能，包括：
 * - 批量選擇和取消選擇
 * - 批量健康檢查
 * - 批量刪除
 * - 批量啟用/禁用
 * - 批量更新配置
 * - 批量導出
 */

import React, { useState, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import { Button, Select, Modal, Input, Checkbox } from '../ui';
import type { ProxyNode } from '../../types';
import { useNotification } from '../../hooks/useNotification';

// ============= 樣式定義 =============

const BatchContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: var(--color-surface);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  margin-bottom: 20px;
`;

const BatchHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
`;

const BatchTitle = styled.h3`
  margin: 0;
  color: var(--color-text-primary);
  font-size: 1.1rem;
  font-weight: 600;
`;

const SelectedCount = styled.div`
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  background: var(--color-primary-light);
  padding: 4px 12px;
  border-radius: 16px;
  font-weight: 500;
`;

const BatchActions = styled.div`
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
`;

const SelectionControls = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
  margin-right: 16px;
  padding-right: 16px;
  border-right: 1px solid var(--color-border);
`;

const ActionButton = styled(Button)<{ variant?: 'primary' | 'danger' | 'warning' | 'success' }>`
  ${props => {
    switch (props.variant) {
      case 'danger':
        return `
          background: var(--color-error);
          color: white;
          &:hover {
            background: var(--color-error-dark);
          }
        `;
      case 'warning':
        return `
          background: var(--color-warning);
          color: white;
          &:hover {
            background: var(--color-warning-dark);
          }
        `;
      case 'success':
        return `
          background: var(--color-success);
          color: white;
          &:hover {
            background: var(--color-success-dark);
          }
        `;
      default:
        return '';
    }
  }}
`;

const ProgressContainer = styled.div`
  margin-top: 16px;
  padding: 16px;
  background: var(--color-background-secondary);
  border-radius: 8px;
  border: 1px solid var(--color-border);
`;

const ProgressHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`;

const ProgressTitle = styled.div`
  font-weight: 600;
  color: var(--color-text-primary);
`;

const ProgressStats = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
`;

const ProgressFill = styled.div<{ percentage: number }>`
  height: 100%;
  width: ${props => props.percentage}%;
  background: var(--color-primary);
  transition: width 0.3s ease;
`;

const ProgressDetails = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
`;

const FilterSection = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  background: var(--color-background-secondary);
  border-radius: 8px;
  margin-bottom: 16px;
`;

const FilterLabel = styled.label`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

// ============= 類型定義 =============

interface BatchProgress {
  total: number;
  completed: number;
  failed: number;
  current?: string;
  isRunning: boolean;
}

interface BatchOperationsProps {
  proxies: ProxyNode[];
  selectedProxies: string[];
  onSelectionChange: (selected: string[]) => void;
  onBatchTest: (proxyIds: string[]) => Promise<void>;
  onBatchDelete: (proxyIds: string[]) => Promise<void>;
  onBatchUpdate: (proxyIds: string[], updates: Partial<ProxyNode>) => Promise<void>;
  onBatchExport: (proxyIds: string[]) => void;
  className?: string;
}

// ============= 主要組件 =============

export const BatchOperations: React.FC<BatchOperationsProps> = ({
  proxies,
  selectedProxies,
  onSelectionChange,
  onBatchTest,
  onBatchDelete,
  onBatchUpdate,
  onBatchExport,
  className
}) => {
  const [progress, setProgress] = useState<BatchProgress | null>(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateConfig, setUpdateConfig] = useState({
    timeout: '',
    maxRetries: '',
    enabled: true
  });
  const [filterCriteria, setFilterCriteria] = useState({
    status: 'all',
    healthScore: 'all',
    country: 'all'
  });
  
  const { showNotification } = useNotification();

  // ============= 計算屬性 =============

  const selectedCount = selectedProxies.length;
  const totalCount = proxies.length;
  const isAllSelected = selectedCount === totalCount && totalCount > 0;
  const isPartialSelected = selectedCount > 0 && selectedCount < totalCount;

  // 獲取可用的篩選選項
  const availableCountries = useMemo(() => {
    const countries = new Set(proxies.map(p => p.country).filter(Boolean));
    return Array.from(countries).sort();
  }, [proxies]);

  const availableStatuses = useMemo(() => {
    const statuses = new Set(proxies.map(p => p.status));
    return Array.from(statuses).sort();
  }, [proxies]);

  // ============= 選擇控制 =============

  const handleSelectAll = useCallback(() => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(proxies.map(p => p.id));
    }
  }, [isAllSelected, proxies, onSelectionChange]);

  const handleSelectByFilter = useCallback(() => {
    const filtered = proxies.filter(proxy => {
      if (filterCriteria.status !== 'all' && proxy.status !== filterCriteria.status) {
        return false;
      }
      if (filterCriteria.healthScore !== 'all') {
        const score = proxy.healthScore || 0;
        switch (filterCriteria.healthScore) {
          case 'high':
            return score >= 80;
          case 'medium':
            return score >= 50 && score < 80;
          case 'low':
            return score < 50;
          default:
            return true;
        }
      }
      if (filterCriteria.country !== 'all' && proxy.country !== filterCriteria.country) {
        return false;
      }
      return true;
    });
    
    onSelectionChange(filtered.map(p => p.id));
    showNotification(`已選擇 ${filtered.length} 個符合條件的代理`, 'success');
  }, [filterCriteria, proxies, onSelectionChange, showNotification]);

  // ============= 批量操作 =============

  const handleBatchTest = useCallback(async () => {
    if (selectedCount === 0) {
      showNotification('請先選擇要測試的代理', 'warning');
      return;
    }

    setProgress({
      total: selectedCount,
      completed: 0,
      failed: 0,
      isRunning: true
    });

    try {
      await onBatchTest(selectedProxies);
      showNotification(`批量測試完成，共測試 ${selectedCount} 個代理`, 'success');
    } catch (error) {
      showNotification('批量測試失敗', 'error');
    } finally {
      setProgress(null);
    }
  }, [selectedCount, selectedProxies, onBatchTest, showNotification]);

  const handleBatchDelete = useCallback(async () => {
    if (selectedCount === 0) {
      showNotification('請先選擇要刪除的代理', 'warning');
      return;
    }

    if (!confirm(`確定要刪除選中的 ${selectedCount} 個代理嗎？此操作無法撤銷。`)) {
      return;
    }

    setProgress({
      total: selectedCount,
      completed: 0,
      failed: 0,
      isRunning: true
    });

    try {
      await onBatchDelete(selectedProxies);
      onSelectionChange([]); // 清空選擇
      showNotification(`成功刪除 ${selectedCount} 個代理`, 'success');
    } catch (error) {
      showNotification('批量刪除失敗', 'error');
    } finally {
      setProgress(null);
    }
  }, [selectedCount, selectedProxies, onBatchDelete, onSelectionChange, showNotification]);

  const handleBatchUpdate = useCallback(async () => {
    if (selectedCount === 0) {
      showNotification('請先選擇要更新的代理', 'warning');
      return;
    }

    const updates: Partial<ProxyNode> = {};
    if (updateConfig.timeout) {
      updates.timeout = parseInt(updateConfig.timeout);
    }
    // maxRetries 屬性在 ProxyNode 類型中不存在，暫時移除
    // if (updateConfig.maxRetries) {
    //   updates.maxRetries = parseInt(updateConfig.maxRetries);
    // }
    updates.enabled = updateConfig.enabled;

    setProgress({
      total: selectedCount,
      completed: 0,
      failed: 0,
      isRunning: true
    });

    try {
      await onBatchUpdate(selectedProxies, updates);
      setShowUpdateModal(false);
      showNotification(`成功更新 ${selectedCount} 個代理`, 'success');
    } catch (error) {
      showNotification('批量更新失敗', 'error');
    } finally {
      setProgress(null);
    }
  }, [selectedCount, selectedProxies, updateConfig, onBatchUpdate, showNotification]);

  const handleBatchExport = useCallback(() => {
    if (selectedCount === 0) {
      showNotification('請先選擇要導出的代理', 'warning');
      return;
    }

    onBatchExport(selectedProxies);
    showNotification(`正在導出 ${selectedCount} 個代理...`, 'info');
  }, [selectedCount, selectedProxies, onBatchExport, showNotification]);

  // ============= 渲染 =============

  if (totalCount === 0) {
    return null;
  }

  return (
    <BatchContainer className={className}>
      <BatchHeader>
        <BatchTitle>批量操作</BatchTitle>
        <SelectedCount>
          已選擇 {selectedCount} / {totalCount} 個代理
        </SelectedCount>
      </BatchHeader>

      {/* 篩選條件 */}
      <FilterSection>
        <FilterLabel>快速選擇：</FilterLabel>
        <Select
          value={filterCriteria.status}
          onChange={(value) => setFilterCriteria(prev => ({ ...prev, status: value as string }))}
          options={[
            { value: 'all', label: '所有狀態' },
            ...availableStatuses.map(status => ({ value: status, label: status }))
          ]}
          size="small"
        />
        <Select
          value={filterCriteria.healthScore}
          onChange={(value) => setFilterCriteria(prev => ({ ...prev, healthScore: value as string }))}
          options={[
            { value: 'all', label: '所有健康度' },
            { value: 'high', label: '高 (≥80)' },
            { value: 'medium', label: '中 (50-79)' },
            { value: 'low', label: '低 (<50)' }
          ]}
          size="small"
        />
        <Select
          value={filterCriteria.country}
          onChange={(value) => setFilterCriteria(prev => ({ ...prev, country: value as string }))}
          options={[
            { value: 'all', label: '所有國家' },
            ...availableCountries.filter((country): country is string => Boolean(country)).map(country => ({ value: country, label: country }))
          ]}
          size="small"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={handleSelectByFilter}
        >
          按條件選擇
        </Button>
      </FilterSection>

      {/* 操作按鈕 */}
      <BatchActions>
        <SelectionControls>
          <Checkbox
            checked={isAllSelected}
            indeterminate={isPartialSelected}
            onChange={handleSelectAll}
          >
            全選
          </Checkbox>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onSelectionChange([])}
            disabled={selectedCount === 0}
          >
            清空選擇
          </Button>
        </SelectionControls>

        <ActionButton
          variant="primary"
          size="sm"
          onClick={handleBatchTest}
          disabled={selectedCount === 0 || progress?.isRunning}
        >
          🔍 批量測試
        </ActionButton>

        <ActionButton
          variant="success"
          size="sm"
          onClick={() => setShowUpdateModal(true)}
          disabled={selectedCount === 0 || progress?.isRunning}
        >
          ⚙️ 批量更新
        </ActionButton>

        <ActionButton
          variant="warning"
          size="sm"
          onClick={handleBatchExport}
          disabled={selectedCount === 0}
        >
          📤 導出選中
        </ActionButton>

        <ActionButton
          variant="danger"
          size="sm"
          onClick={handleBatchDelete}
          disabled={selectedCount === 0 || progress?.isRunning}
        >
          🗑️ 批量刪除
        </ActionButton>
      </BatchActions>

      {/* 進度顯示 */}
      {progress && (
        <ProgressContainer>
          <ProgressHeader>
            <ProgressTitle>操作進度</ProgressTitle>
            <ProgressStats>
              {progress.completed} / {progress.total} 完成
              {progress.failed > 0 && ` (${progress.failed} 失敗)`}
            </ProgressStats>
          </ProgressHeader>
          <ProgressBar>
            <ProgressFill percentage={(progress.completed / progress.total) * 100} />
          </ProgressBar>
          <ProgressDetails>
            <span>已完成：{progress.completed}</span>
            <span>失敗：{progress.failed}</span>
            <span>剩餘：{progress.total - progress.completed}</span>
          </ProgressDetails>
          {progress.current && (
            <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              正在處理：{progress.current}
            </div>
          )}
        </ProgressContainer>
      )}

      {/* 批量更新模態框 */}
      <Modal
        visible={showUpdateModal}
        onClose={() => setShowUpdateModal(false)}
        title="批量更新配置"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              超時時間 (毫秒)
            </label>
            <Input
              type="number"
              value={updateConfig.timeout}
              onChange={(e) => setUpdateConfig(prev => ({ ...prev, timeout: e.target.value }))}
              placeholder="例如：5000"
            />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              最大重試次數
            </label>
            <Input
              type="number"
              value={updateConfig.maxRetries}
              onChange={(e) => setUpdateConfig(prev => ({ ...prev, maxRetries: e.target.value }))}
              placeholder="例如：3"
            />
          </div>
          
          <div>
            <Checkbox
              checked={updateConfig.enabled}
              onChange={(checked) => setUpdateConfig(prev => ({ ...prev, enabled: checked }))}
            >
              啟用代理
            </Checkbox>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px' }}>
            <Button
              variant="outline"
              onClick={() => setShowUpdateModal(false)}
            >
              取消
            </Button>
            <Button
              variant="primary"
              onClick={handleBatchUpdate}
              disabled={progress?.isRunning}
            >
              確認更新 ({selectedCount} 個代理)
            </Button>
          </div>
        </div>
      </Modal>
    </BatchContainer>
  );
};

export default BatchOperations;