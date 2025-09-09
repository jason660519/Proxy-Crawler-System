/**
 * 任務佇列管理分頁組件
 * 
 * 提供完整的任務管理功能，包括：
 * - 任務列表檢視與篩選
 * - 任務建立、編輯、刪除
 * - 任務執行控制與監控
 * - 批量操作與排程
 * - 即時狀態更新
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import type { 
  Task,
  CrawlTask, 
  TaskFilters, 
  PaginationParams,
  TaskPriority,
  TaskStatus
} from '../types';
import { PageLayout } from '../components/layout/PageLayout';
import { DataTable } from '../components/ui/DataTable';
import type { DataTableColumn } from '../components/ui/DataTable';
import { StatusIndicator } from '../components/ui/StatusIndicator';
import { Button, Input, Card, Modal, Select, TextArea } from '../components/ui';
import { useTaskQueue } from '../hooks/useTaskQueue';
import { useNotification } from '../hooks/useNotification';
import { formatDateTime, formatDuration } from '../utils/formatters';
import { validateUrl } from '../utils/validators';

// ============= 樣式定義 =============

const TaskQueueContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  background: ${props => props.theme.colors.background};
  min-height: 100vh;
`;

const FiltersSection = styled(Card)`
  padding: 20px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
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
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled(Card)`
  padding: 20px;
  text-align: center;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: #3b82f6;
  margin-bottom: 8px;
`;

const StatLabel = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const TaskForm = styled.form`
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

const FormSection = styled.div`
  margin-bottom: 20px;
  
  h4 {
    margin-bottom: 12px;
    color: ${props => props.theme.colors.text};
    font-size: 1rem;
    font-weight: 600;
  }
`;

const ProgressBar = styled.div<{ progress: number }>`
  width: 100%;
  height: 8px;
  background: #f9fafb;
  border-radius: 4px;
  overflow: hidden;
  
  &::after {
    content: '';
    display: block;
    width: ${props => props.progress}%;
    height: 100%;
    background: #3b82f6;
    transition: width 0.3s ease;
  }
`;

const TaskDetails = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  
  .task-url {
    font-weight: 500;
    color: ${props => props.theme.colors.text};
  }
  
  .task-meta {
    font-size: 0.75rem;
    color: #6b7280;
    display: flex;
    gap: 12px;
  }
`;

const PriorityBadge = styled.span<{ priority: TaskPriority }>`
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  background: ${props => {
    switch (props.priority) {
      case 'high': return '#fef2f2';
      case 'medium': return '#fffbeb';
      case 'low': return '#eff6ff';
      default: return '#f9fafb';
    }
  }};
  color: ${props => {
    switch (props.priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#6b7280';
    }
  }};
`;

// ============= 介面定義 =============

interface TaskFormData {
  url: string;
  name: string;
  description?: string;
  priority: TaskPriority;
  maxRetries: number;
  timeout: number;
  proxyIds: string[];
  headers: Record<string, string>;
  cookies: Record<string, string>;
  scheduledAt?: Date;
  recurring: boolean;
  recurringPattern?: string;
  enabled: boolean;
}

interface TaskQueueProps {
  className?: string;
}

// ============= 主要組件 =============

export const TaskQueue: React.FC<TaskQueueProps> = ({ className }) => {
  // ============= 狀態管理 =============
  
  const {
    state,
    actions: {
      loadTasks,
      createTask,
      updateTask,
      deleteTask,
      executeTaskOperation,
      bulkOperation,
      setSelectedTasks,

    }
  } = useTaskQueue();
  
  const { showNotification } = useNotification();
  
  const [filters, setFilters] = useState<TaskFilters>({
    status: undefined,
    type: undefined,
    priority: undefined,
    search: '',
    dateRange: undefined
  });
  
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    size: 20
  });
  

  
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingTask, setEditingTask] = useState<CrawlTask | null>(null);
  
  const [formData, setFormData] = useState<TaskFormData>({
    url: '',
    name: '',
    description: '',
    priority: 'medium',
    maxRetries: 3,
    timeout: 30000,
    proxyIds: [],
    headers: {},
    cookies: {},
    scheduledAt: undefined,
    recurring: false,
    recurringPattern: '',
    enabled: true
  });
  
  // ============= 計算屬性 =============
  
  const stats = useMemo(() => {
    const tasks = state.tasks;
    const total = tasks.length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    const running = tasks.filter(t => t.status === 'running').length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const failed = tasks.filter(t => t.status === 'failed').length;
    const successRate = total > 0 ? (completed / (completed + failed)) * 100 : 0;
    
    return {
      total,
      pending,
      running,
      completed,
      failed,
      successRate: Math.round(successRate)
    };
  }, [state.tasks]);
  
  const filteredTasks = useMemo(() => {
    let filtered = state.tasks;
    
    // 狀態篩選
    if (filters.status && Array.isArray(filters.status) && filters.status.length > 0) {
      filtered = filtered.filter(task => (filters.status as TaskStatus[]).includes(task.status));
    }
    
    // 優先級篩選
    if (filters.priority && Array.isArray(filters.priority) && filters.priority.length > 0) {
      filtered = filtered.filter(task => (filters.priority as TaskPriority[]).includes(task.priority));
    }
    
    // 類型篩選
    if (filters.type && filters.type.length > 0) {
      filtered = filtered.filter(task => 
        filters.type!.includes(task.type)
      );
    }
    
    // 搜尋篩選
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(task => 
        task.name.toLowerCase().includes(searchLower) ||
        (task as CrawlTask).url?.toLowerCase().includes(searchLower) ||
        (task as CrawlTask).description?.toLowerCase().includes(searchLower)
      );
    }
    
    // 日期範圍篩選
    if (filters.dateRange && filters.dateRange.length === 2) {
      const [start, end] = filters.dateRange;
      filtered = filtered.filter(task => {
        const taskDate = new Date(task.createdAt);
        return taskDate >= new Date(start) && taskDate <= new Date(end);
      });
    }
    
    return filtered;
  }, [state.tasks, filters]);
  
  const tableColumns: DataTableColumn<Task>[] = useMemo(() => [
    {
      key: 'status' as keyof Task,
      title: '狀態',
      sortable: true,
      render: (_, task: Task) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <StatusIndicator 
            status={task.status as any} 
            size={"small" as any}
            
          />
          {task.status === 'running' && (
            <ProgressBar progress={task.progress || 0} />
          )}
        </div>
      )
    },
    {
      key: 'name' as keyof Task,
      title: '任務資訊',
      sortable: true,
      render: (_, task: Task) => (
        <TaskDetails>
          <div className="task-url">{task.name}</div>
          <div className="task-meta">
            <span>URL: {(task as CrawlTask).url}</span>
            <PriorityBadge priority={task.priority}>
              {task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
            </PriorityBadge>
          </div>
        </TaskDetails>
      )
    },
    {
      key: 'progress' as keyof Task,
      title: '進度',
      sortable: true,
      render: (_, task: Task) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold' }}>{task.progress || 0}%</div>
        </div>
      )
    },
    {
      key: 'duration' as keyof Task,
      title: '執行時間',
      sortable: true,
      render: (_, task: Task) => (
        <div style={{ fontSize: '0.875rem' }}>
          {task.startTime && task.endTime ? (
            formatDuration(new Date(task.endTime).getTime() - new Date(task.startTime).getTime())
          ) : task.startTime ? (
            formatDuration(Date.now() - new Date(task.startTime).getTime())
          ) : task.duration ? (
            formatDuration(task.duration)
          ) : '-'}
        </div>
      )
    },
    {
      key: 'createdAt' as keyof Task,
      title: '建立時間',
      sortable: true,
      render: (_, task: Task) => (
        <div style={{ fontSize: '0.875rem' }}>
          {formatDateTime(task.createdAt)}
        </div>
      )
    },
    {
      key: 'type' as keyof Task,
      title: '任務類型',
      sortable: true,
      render: (_, task: Task) => (
        <div style={{ fontSize: '0.875rem' }}>
          {task.type}
        </div>
      )
    },
    {
      key: 'id' as keyof Task,
      title: '操作',
      render: (_, task: Task) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          {task.status === 'pending' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleExecuteTask(task.id)}
              disabled={state.loading}
            >
              執行
            </Button>
          )}
          {task.status === 'running' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handlePauseTask(task.id)}
              disabled={state.loading}
            >
              暫停
            </Button>
          )}
          {task.status === 'paused' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleResumeTask(task.id)}
              disabled={state.loading}
            >
              繼續
            </Button>
          )}
          {(task.status === 'running' || task.status === 'paused') && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleCancelTask(task.id)}
              disabled={state.loading}
            >
              取消
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleEditTask(task as CrawlTask)}
          >
            編輯
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleDeleteTask(task.id)}
            disabled={state.loading || task.status === 'running'}
          >
            刪除
          </Button>
        </div>
      )
    }
  ], [state.loading]);
  
  // ============= 事件處理 =============
  
  const handleLoadTasks = useCallback(async () => {
    try {
      await loadTasks({ filters, pagination });
    } catch (error) {
      showNotification('載入任務列表失敗', 'error');
    }
  }, [filters, pagination, loadTasks, showNotification]);
  
  const handleFilterChange = useCallback((key: keyof TaskFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一頁
  }, []);
  

  

  
  const handleAddTask = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 驗證表單
    if (!validateUrl(formData.url)) {
      showNotification('URL 格式不正確', 'error');
      return;
    }
    
    if (!formData.name.trim()) {
      showNotification('任務名稱不能為空', 'error');
      return;
    }
    
    try {
      await createTask(formData);
      setShowAddModal(false);
      resetForm();
      showNotification('任務建立成功', 'success');
      handleLoadTasks();
    } catch (error) {
      showNotification('任務建立失敗', 'error');
    }
  }, [formData, createTask, showNotification, handleLoadTasks]);
  
  const resetForm = useCallback(() => {
    setFormData({
      url: '',
      name: '',
      description: '',
      priority: 'medium',
      maxRetries: 3,
      timeout: 30000,
      proxyIds: [],
      headers: {},
      cookies: {},
      scheduledAt: undefined,
      recurring: false,
      recurringPattern: '',
      enabled: true
    });
  }, []);
  
  const handleEditTask = useCallback((task: CrawlTask) => {
    setEditingTask(task);
    setFormData({
      url: task.url,
      name: task.name,
      description: task.description || '',
      priority: task.priority,
      maxRetries: task.maxRetries,
      timeout: task.timeout,
      proxyIds: task.proxyIds,
      headers: task.headers || {},
      cookies: task.cookies || {},
      scheduledAt: task.scheduledAt ? new Date(task.scheduledAt) : undefined,
      recurring: task.recurring || false,
      recurringPattern: task.recurringPattern || '',
      enabled: task.enabled
    });
    setShowAddModal(true);
  }, []);
  
  const handleUpdateTask = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!editingTask) return;
    
    try {
      await updateTask(editingTask.id, formData);
      setShowAddModal(false);
      setEditingTask(null);
      showNotification('任務更新成功', 'success');
      handleLoadTasks();
    } catch (error) {
      showNotification('任務更新失敗', 'error');
    }
  }, [editingTask, formData, updateTask, showNotification, handleLoadTasks]);
  
  const handleDeleteTask = useCallback(async (taskId: string) => {
    if (!confirm('確定要刪除此任務嗎？')) return;
    
    try {
      await deleteTask(taskId);
      showNotification('任務刪除成功', 'success');
      handleLoadTasks();
    } catch (error) {
      showNotification('任務刪除失敗', 'error');
    }
  }, [deleteTask, showNotification, handleLoadTasks]);
  
  const handleExecuteTask = useCallback(async (taskId: string) => {
    try {
      await executeTaskOperation(taskId, 'start');
      showNotification('任務已開始執行', 'success');
      handleLoadTasks();
    } catch (error) {
      showNotification('任務執行失敗', 'error');
    }
  }, [executeTaskOperation, showNotification, handleLoadTasks]);
  
  const handlePauseTask = useCallback(async (taskId: string) => {
    try {
      await executeTaskOperation(taskId, 'pause');
      showNotification('任務已暫停', 'success');
      handleLoadTasks();
    } catch (error) {
      showNotification('任務暫停失敗', 'error');
    }
  }, [executeTaskOperation, showNotification, handleLoadTasks]);
  
  const handleResumeTask = useCallback(async (taskId: string) => {
    try {
      await executeTaskOperation(taskId, 'resume');
      showNotification('任務已繼續', 'success');
      handleLoadTasks();
    } catch (error) {
      showNotification('任務繼續失敗', 'error');
    }
  }, [executeTaskOperation, showNotification, handleLoadTasks]);
  
  const handleCancelTask = useCallback(async (taskId: string) => {
    if (!confirm('確定要取消此任務嗎？')) return;
    
    try {
      await executeTaskOperation(taskId, 'stop');
      showNotification('任務已取消', 'success');
      handleLoadTasks();
    } catch (error) {
      showNotification('任務取消失敗', 'error');
    }
  }, [executeTaskOperation, showNotification, handleLoadTasks]);
  
  const handleBulkOperation = useCallback(async (operation: string) => {
    if (state.selectedTasks.length === 0) {
      showNotification('請選擇要操作的任務', 'warning');
      return;
    }
    
    try {
      const result = await bulkOperation(operation, state.selectedTasks);
      showNotification(`批量操作完成：成功 ${result.success}，失敗 ${result.failed}`, 'success');
      setSelectedTasks([]);
      handleLoadTasks();
    } catch (error) {
      showNotification('批量操作失敗', 'error');
    }
  }, [state.selectedTasks, bulkOperation, showNotification, handleLoadTasks]);
  
  // ============= 生命週期 =============
  
  useEffect(() => {
    handleLoadTasks();
  }, [handleLoadTasks]);
  
  // ============= 渲染 =============
  
  return (
    <PageLayout
      title="任務佇列"
      subtitle="管理和監控爬蟲任務"
      loading={state.loading}
      error={state.error}
      className={className}
      toolbar={
        <Button
          variant="primary"
          onClick={() => setShowAddModal(true)}
          disabled={state.loading}
        >
          建立任務
        </Button>
      }
    >
      <TaskQueueContainer>
        {/* 統計卡片 */}
        <StatsCards>
          <StatCard>
            <StatValue>{stats.total}</StatValue>
            <StatLabel>總任務數</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.pending}</StatValue>
            <StatLabel>等待中</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.running}</StatValue>
            <StatLabel>執行中</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.completed}</StatValue>
            <StatLabel>已完成</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.failed}</StatValue>
            <StatLabel>失敗</StatLabel>
          </StatCard>
          <StatCard>
            <StatValue>{stats.successRate}%</StatValue>
            <StatLabel>成功率</StatLabel>
          </StatCard>
        </StatsCards>
        
        {/* 篩選區域 */}
        <FiltersSection>
          <FiltersGrid>
            <Input
              placeholder="搜尋任務名稱、URL 或描述..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
            <Select
              placeholder="選擇狀態"
              value={filters.status || ''}
              onChange={(value) => handleFilterChange('status', value || undefined)}
              options={[
                { value: '', label: '全部狀態' },
                { value: 'pending', label: '等待中' },
                { value: 'running', label: '執行中' },
                { value: 'paused', label: '已暫停' },
                { value: 'completed', label: '已完成' },
                { value: 'failed', label: '失敗' },
                { value: 'cancelled', label: '已取消' }
              ]}
            />
            <Select
              placeholder="選擇優先級"
              value={filters.priority || ''}
              onChange={(value) => handleFilterChange('priority', value || undefined)}
              options={[
                { value: '', label: '全部優先級' },
                { value: 'high', label: '高優先級' },
                { value: 'medium', label: '中優先級' },
                { value: 'low', label: '低優先級' }
              ]}
            />
          </FiltersGrid>
        </FiltersSection>
        
        {/* 操作列 */}
        <ActionsBar>
          <BulkActions>
            <span>已選擇 {state.selectedTasks.length} 個任務</span>
                {state.selectedTasks.length > 0 && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkOperation('execute')}
                  disabled={state.loading}
                >
                  執行
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkOperation('pause')}
                  disabled={state.loading}
                >
                  暫停
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkOperation('cancel')}
                  disabled={state.loading}
                >
                  取消
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
              onClick={handleLoadTasks}
              disabled={state.loading}
            >
              重新整理
            </Button>
          </div>
        </ActionsBar>
        
        {/* 任務列表 */}
        <DataTable
            columns={tableColumns}
            dataSource={filteredTasks}
            pagination={{
              current: pagination.page,
              pageSize: pagination.size,
              total: state.tasks.length,
              showSizeChanger: true,
              showQuickJumper: true,
              onChange: (page: number, pageSize: number) => {
                setPagination(prev => ({ ...prev, page, size: pageSize }));
              }
            }}
            loading={state.loading}
            rowSelection={{
              type: 'checkbox',
              selectedRowKeys: state.selectedTasks,
              onChange: (selectedRowKeys: (string | number)[]) => {
                setSelectedTasks(selectedRowKeys as string[]);
              }
            }}
          />
        
        {/* 建立/編輯任務模態框 */}
        <Modal
            visible={showAddModal}
            onClose={() => {
              setShowAddModal(false);
              setEditingTask(null);
              resetForm();
            }}
            title={editingTask ? '編輯任務' : '建立任務'}
            width="large"
          >
          <TaskForm onSubmit={editingTask ? handleUpdateTask : handleAddTask}>
            <FormSection>
              <h4>基本資訊</h4>
              <FormRow>
                <Input
                  label="任務名稱"
                  placeholder="輸入任務名稱"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  
                />
                <Input
                  label="目標 URL"
                  placeholder="https://example.com"
                  value={formData.url}
                  onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                  
                />
              </FormRow>
              
              <div>
                <label>任務描述</label>
                <TextArea
                   placeholder="選填：描述此任務的目的和內容"
                   value={formData.description}
                   onChange={(value) => setFormData(prev => ({ ...prev, description: value }))}
                   
                 />
              </div>
            </FormSection>
            
            <FormSection>
              <h4>執行設定</h4>
              <FormRow>
                <div>
                  <label>優先級 *</label>
                  <Select
                    value={formData.priority}
                    onChange={(value) => setFormData(prev => ({ ...prev, priority: value as TaskPriority }))}
                    options={[
                      { value: 'high', label: '高優先級' },
                      { value: 'medium', label: '中優先級' },
                      { value: 'low', label: '低優先級' }
                    ]}
                    
                  />
                </div>
                <Input
                  label="最大重試次數"
                  type="number"
                  min="0"
                  max="10"
                  value={formData.maxRetries}
                  onChange={(e) => setFormData(prev => ({ ...prev, maxRetries: parseInt(e.target.value) }))}
                />
              </FormRow>
              
              <FormRow>
                <Input
                  label="超時時間 (毫秒)"
                  type="number"
                  min="1000"
                  max="300000"
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
                  <label htmlFor="enabled">啟用任務</label>
                </div>
              </FormRow>
            </FormSection>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowAddModal(false);
                  setEditingTask(null);
                  resetForm();
                }}
              >
                取消
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={state.loading}
              >
                {editingTask ? '更新' : '建立'}
              </Button>
            </div>
          </TaskForm>
        </Modal>
      </TaskQueueContainer>
    </PageLayout>
  );
};

export default TaskQueue;