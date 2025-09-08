/**
 * 任務佇列板組件
 * 顯示任務列表，支援狀態篩選、排序和基本操作
 */

import React, { useState, useMemo } from 'react';
import styled from 'styled-components';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { useTasks } from '../../hooks';
import { spacing, borderRadius } from '../../styles';
import type { Task, TaskStatus as TaskStatusType } from '../../types';

// ============= 類型定義 =============

type TaskStatus = TaskStatusType;

interface TaskBoardProps {
  className?: string;
  maxItems?: number;
}

interface TaskItemProps {
  task: Task;
  onStatusChange?: (taskId: string, status: TaskStatus) => void;
}

interface StatusFilterProps {
  status: TaskStatus | 'all';
  active: boolean;
  count: number;
  onClick: () => void;
}

// ============= 樣式定義 =============

const TaskBoardContainer = styled(Card)`
  padding: ${spacing[6]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.lg};
  min-height: 400px;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[6]};
`;

const Title = styled.h3`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const Actions = styled.div`
  display: flex;
  gap: ${spacing[2]};
`;

const FilterTabs = styled.div`
  display: flex;
  gap: ${spacing[1]};
  margin-bottom: ${spacing[4]};
  padding: ${spacing[1]};
  background: var(--color-background-secondary);
  border-radius: ${borderRadius.md};
`;

const StatusFilter = styled.button<{ active: boolean }>`
  display: flex;
  align-items: center;
  gap: ${spacing[1]};
  padding: ${spacing[1]} ${spacing[2]};
  border: none;
  border-radius: ${borderRadius.sm};
  background: ${({ active }) => active ? 'var(--color-primary-500)' : 'transparent'};
  color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-text-secondary)'};
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ active }) => active ? 'var(--color-primary-600)' : 'var(--color-background-hover)'};
  }

  .count {
    background: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-neutral-200)'};
    color: ${({ active }) => active ? 'var(--color-primary-500)' : 'var(--color-text-secondary)'};
    padding: 2px 6px;
    border-radius: ${borderRadius.full};
    font-size: 0.75rem;
    font-weight: 600;
    min-width: 18px;
    text-align: center;
  }
`;

const TaskList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing[2]};
  max-height: 300px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--color-background-secondary);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--color-neutral-300);
    border-radius: 3px;
    
    &:hover {
      background: var(--color-neutral-400);
    }
  }
`;

const TaskItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing[4]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-light);
  border-radius: ${borderRadius.md};
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-border-hover);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const TaskInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const TaskName = styled.div`
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: ${spacing[1]};
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const TaskMeta = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[4]};
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const TaskStatusBadge = styled.span<{ status: TaskStatus }>`
  display: inline-flex;
  align-items: center;
  gap: ${spacing[1]};
  padding: ${spacing[1]} ${spacing[2]};
  border-radius: ${borderRadius.full};
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  
  ${({ status }) => {
    switch (status) {
      case 'pending':
        return `
          background: var(--color-neutral-100);
          color: var(--color-neutral-600);
        `;
      case 'running':
        return `
          background: var(--color-primary-100);
          color: var(--color-primary-700);
        `;
      case 'completed':
        return `
          background: var(--color-status-success-light);
          color: var(--color-status-success);
        `;
      case 'failed':
        return `
          background: var(--color-status-error-light);
          color: var(--color-status-error);
        `;
      case 'cancelled':
        return `
          background: var(--color-status-warning-light);
          color: var(--color-status-warning);
        `;
      default:
        return `
          background: var(--color-neutral-100);
          color: var(--color-neutral-600);
        `;
    }
  }}

  &::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }
`;

const TaskActions = styled.div`
  display: flex;
  gap: ${spacing[1]};
  margin-left: ${spacing[4]};
`;

const ActionButton = styled.button`
  padding: ${spacing[1]};
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.sm};
  background: var(--color-background-card);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: var(--color-primary-500);
    color: var(--color-primary-500);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const LoadingState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-secondary);
`;

const ErrorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-status-error);
  text-align: center;
  
  .error-message {
    margin-top: ${spacing[2]};
    font-size: 0.875rem;
  }
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-secondary);
  text-align: center;
  
  .empty-message {
    margin-top: ${spacing[2]};
    font-size: 0.875rem;
  }
`;

// ============= 組件實作 =============

/**
 * 狀態篩選器組件
 */
const StatusFilterButton: React.FC<StatusFilterProps> = ({ status, active, count, onClick }) => {
  const getStatusLabel = (status: TaskStatus | 'all') => {
    switch (status) {
      case 'all': return '全部';
      case 'pending': return '等待中';
      case 'running': return '執行中';
      case 'completed': return '已完成';
      case 'failed': return '失敗';
      case 'cancelled': return '已取消';
      default: return status;
    }
  };

  return (
    <StatusFilter active={active} onClick={onClick}>
      {getStatusLabel(status)}
      <span className="count">{count}</span>
    </StatusFilter>
  );
};

/**
 * 任務項目組件
 */
const TaskItemComponent: React.FC<TaskItemProps> = ({ task, onStatusChange }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusLabel = (status: TaskStatus) => {
    switch (status) {
      case 'pending': return '等待中';
      case 'running': return '執行中';
      case 'completed': return '已完成';
      case 'failed': return '失敗';
      case 'cancelled': return '已取消';
      default: return status;
    }
  };

  const canCancel = task.status === 'pending' || task.status === 'running';
  const canRetry = task.status === 'failed';

  return (
    <TaskItem>
      <TaskInfo>
        <TaskName>{task.name}</TaskName>
        <TaskMeta>
          <TaskStatusBadge status={task.status}>
            {getStatusLabel(task.status)}
          </TaskStatusBadge>
          <span>建立於 {formatDate(task.createdAt)}</span>
          {task.progress !== undefined && (
            <span>{Math.round(task.progress * 100)}%</span>
          )}
        </TaskMeta>
      </TaskInfo>
      
      <TaskActions>
        {canCancel && (
          <ActionButton
            onClick={() => onStatusChange?.(task.id, 'cancelled')}
            title="取消任務"
          >
            ⏹️
          </ActionButton>
        )}
        
        {canRetry && (
          <ActionButton
            onClick={() => onStatusChange?.(task.id, 'pending')}
            title="重試任務"
          >
            🔄
          </ActionButton>
        )}
        
        <ActionButton title="查看詳情">
          👁️
        </ActionButton>
      </TaskActions>
    </TaskItem>
  );
};

/**
 * 任務佇列板組件
 */
export const TaskBoard: React.FC<TaskBoardProps> = ({ className, maxItems = 10 }) => {
  const { tasks, loading, error, refresh } = useTasks({ size: maxItems });
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');

  // 計算各狀態的任務數量
  const statusCounts = useMemo((): Record<string, number> => {
    if (!tasks?.data) return {};
    
    const counts = (tasks.data || []).reduce((acc: Record<string, number>, task: Task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {} as Record<TaskStatus, number>);
    
    return {
      all: (tasks.data || []).length,
      ...counts
    };
  }, [tasks]);

  // 篩選任務
  const filteredTasks = useMemo(() => {
    if (!tasks?.data) return [];
    
    if (statusFilter === 'all') {
      return tasks.data;
    }
    
    return tasks.data.filter((task: Task) => task.status === statusFilter);
  }, [tasks, statusFilter]);

  // 處理狀態變更
  const handleStatusChange = async (taskId: string, status: TaskStatus) => {
    try {
      // 這裡應該調用 API 更新任務狀態
      console.log(`更新任務 ${taskId} 狀態為 ${status}`);
      // await api.updateTaskStatus(taskId, status);
      await refresh();
    } catch (error) {
      console.error('更新任務狀態失敗:', error);
    }
  };

  return (
    <TaskBoardContainer className={className}>
      <Header>
        <Title>任務佇列</Title>
        <Actions>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refresh()}
            disabled={loading}
          >
            🔄 重新整理
          </Button>
        </Actions>
      </Header>

      {/* 狀態篩選器 */}
      <FilterTabs>
        {(['all', 'pending', 'running', 'completed', 'failed', 'cancelled'] as const).map((status) => (
          <StatusFilterButton
            key={status}
            status={status}
            active={statusFilter === status}
            count={statusCounts[status] || 0}
            onClick={() => setStatusFilter(status)}
          />
        ))}
      </FilterTabs>

      {/* 任務列表 */}
      {loading && (
        <LoadingState>
          載入任務列表中...
        </LoadingState>
      )}

      {error && (
        <ErrorState>
          <div>⚠️</div>
          <div className="error-message">
            無法載入任務列表：{error.message}
          </div>
        </ErrorState>
      )}

      {!loading && !error && !filteredTasks.length && (
        <EmptyState>
          <div>📋</div>
          <div className="empty-message">
            {statusFilter === 'all' ? '暫無任務' : `暫無${statusFilter}狀態的任務`}
          </div>
        </EmptyState>
      )}

      {!loading && !error && filteredTasks.length > 0 && (
        <TaskList>
          {filteredTasks.map((task: Task) => (
            <TaskItemComponent
              key={task.id}
              task={task}
              onStatusChange={handleStatusChange}
            />
          ))}
        </TaskList>
      )}
    </TaskBoardContainer>
  );
};

// 導出類型
export type { TaskBoardProps, TaskItemProps };

export default TaskBoard;