/**
 * 即時日誌檢視器組件
 * 顯示系統日誌，支援即時更新、篩選和搜尋功能
 */

import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { useLogs } from '../../hooks';
import { spacing, borderRadius } from '../../styles';
import type { LogEntry, LogLevel as LogLevelType } from '../../types';

// ============= 類型定義 =============

interface LogViewerProps {
  className?: string;
  maxItems?: number;
  autoScroll?: boolean;
}

interface LogItemProps {
  log: LogEntry;
}

interface LogLevelFilterProps {
  level: LogLevelType | 'all';
  active: boolean;
  count: number;
  onClick: () => void;
}

// ============= 樣式定義 =============

const LogViewerContainer = styled(Card)`
  padding: ${spacing[6]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.lg};
  min-height: 400px;
  display: flex;
  flex-direction: column;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[4]};
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

const Controls = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing[2]};
  margin-bottom: ${spacing[4]};
`;

const TopControls = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[2]};
`;

const SearchInput = styled(Input)`
  flex: 1;
  max-width: 300px;
`;

const LevelFilters = styled.div`
  display: flex;
  gap: ${spacing[1]};
  padding: ${spacing[1]};
  background: var(--color-background-secondary);
  border-radius: ${borderRadius.md};
`;

const LevelFilter = styled.button<{ active: boolean; level: LogLevelType | 'all' }>`
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
    color: ${({ active, level }) => {
      if (active) return 'var(--color-primary-500)';
      switch (level) {
        case 'error': return 'var(--color-status-error)';
        case 'warning': return 'var(--color-status-warning)';
        case 'info': return 'var(--color-primary-600)';
        case 'debug': return 'var(--color-neutral-600)';
        default: return 'var(--color-text-secondary)';
      }
    }};
    padding: 2px 6px;
    border-radius: ${borderRadius.full};
    font-size: 0.75rem;
    font-weight: 600;
    min-width: 18px;
    text-align: center;
  }
`;

const LogList = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-neutral-900);
  border-radius: ${borderRadius.md};
  overflow: hidden;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.4;
`;

const LogListContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: ${spacing[2]};
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--color-neutral-800);
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--color-neutral-600);
    border-radius: 4px;
    
    &:hover {
      background: var(--color-neutral-500);
    }
  }
`;

const LogItem = styled.div<{ level: LogLevelType }>`
  display: flex;
  align-items: flex-start;
  gap: ${spacing[2]};
  padding: ${spacing[1]} 0;
  border-bottom: 1px solid var(--color-neutral-800);
  
  &:last-child {
    border-bottom: none;
  }
  
  &:hover {
    background: var(--color-neutral-800-50);
  }
`;

const LogTimestamp = styled.span`
  color: var(--color-neutral-400);
  font-size: 0.75rem;
  white-space: nowrap;
  min-width: 80px;
`;

const LogLevelBadge = styled.span<{ level: LogLevelType }>`
  display: inline-block;
  width: 60px;
  text-align: center;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  
  ${({ level }) => {
    switch (level) {
      case 'error':
        return `color: var(--color-status-error);`;
      case 'warning':
        return `color: var(--color-status-warning);`;
      case 'info':
        return `color: var(--color-primary-400);`;
      case 'debug':
        return `color: var(--color-neutral-400);`;
      default:
        return `color: var(--color-neutral-300);`;
    }
  }}
`;

const LogMessage = styled.span`
  flex: 1;
  color: var(--color-neutral-100);
  word-break: break-word;
  
  .highlight {
    background: var(--color-status-warning);
    color: var(--color-neutral-900);
    padding: 0 2px;
    border-radius: 2px;
  }
`;

const LogSource = styled.span`
  color: var(--color-neutral-500);
  font-size: 0.75rem;
  white-space: nowrap;
  min-width: 100px;
  text-align: right;
`;

const LoadingState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-neutral-400);
  background: var(--color-neutral-900);
  border-radius: ${borderRadius.md};
`;

const ErrorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-status-error);
  background: var(--color-neutral-900);
  border-radius: ${borderRadius.md};
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
  color: var(--color-neutral-400);
  background: var(--color-neutral-900);
  border-radius: ${borderRadius.md};
  text-align: center;
  
  .empty-message {
    margin-top: ${spacing[2]};
    font-size: 0.875rem;
  }
`;

const StatusBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing[1]} ${spacing[2]};
  background: var(--color-neutral-800);
  border-top: 1px solid var(--color-neutral-700);
  font-size: 0.75rem;
  color: var(--color-neutral-400);
`;

// ============= 組件實作 =============

/**
 * 日誌等級篩選器組件
 */
const LevelFilterButton: React.FC<LogLevelFilterProps> = ({ level, active, count, onClick }) => {
  const getLevelLabel = (level: LogLevelType | 'all') => {
    switch (level) {
      case 'all': return '全部';
      case 'error': return '錯誤';
      case 'warning': return '警告';
      case 'info': return '資訊';
      case 'debug': return '除錯';
      default: return level;
    }
  };

  return (
    <LevelFilter active={active} level={level} onClick={onClick}>
      {getLevelLabel(level)}
      <span className="count">{count}</span>
    </LevelFilter>
  );
};

/**
 * 日誌項目組件
 */
const LogItemComponent: React.FC<LogItemProps & { searchTerm?: string }> = ({ log, searchTerm }) => {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-TW', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const highlightText = (text: string, term: string) => {
    if (!term) return text;
    
    const regex = new RegExp(`(${term})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <span key={index} className="highlight">{part}</span>
      ) : (
        part
      )
    );
  };

  return (
    <LogItem level={log.level}>
      <LogTimestamp>{formatTime(log.timestamp)}</LogTimestamp>
      <LogLevelBadge level={log.level}>{log.level}</LogLevelBadge>
      <LogMessage>
        {highlightText(log.message, searchTerm || '')}
      </LogMessage>
      {log.source && (
        <LogSource>{log.source}</LogSource>
      )}
    </LogItem>
  );
};

/**
 * 即時日誌檢視器組件
 */
export const LogViewer: React.FC<LogViewerProps> = ({ 
  className, 
  maxItems = 100,
  autoScroll = true 
}) => {
  const { logs, loading, error, refresh } = useLogs({ limit: maxItems });
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState<LogLevelType | 'all'>('all');
  const [isAutoScroll, setIsAutoScroll] = useState(autoScroll);
  const logListRef = useRef<HTMLDivElement>(null);

  // 自動滾動到底部
  useEffect(() => {
    if (isAutoScroll && logListRef.current) {
      logListRef.current.scrollTop = logListRef.current.scrollHeight;
    }
  }, [logs, isAutoScroll]);

  // 計算各等級的日誌數量
  const levelCounts = React.useMemo(() => {
    if (!logs) return { all: 0 } as Record<LogLevelType | 'all', number>;
    
    const counts = logs.reduce((acc, log) => {
      acc[log.level] = (acc[log.level] || 0) + 1;
      return acc;
    }, {} as Record<LogLevelType, number>);
    
    return {
      all: logs.length,
      ...counts
    } as Record<LogLevelType | 'all', number>;
  }, [logs]);

  // 篩選日誌
  const filteredLogs = React.useMemo(() => {
    if (!logs) return [];
    
    let filtered = logs;
    
    // 等級篩選
    if (levelFilter !== 'all') {
      filtered = filtered.filter(log => log.level === levelFilter);
    }
    
    // 搜尋篩選
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(term) ||
        log.source?.toLowerCase().includes(term)
      );
    }
    
    return filtered;
  }, [logs, levelFilter, searchTerm]);

  // 清除日誌
  const handleClear = () => {
    // 這裡應該調用 API 清除日誌
    console.log('清除日誌');
  };

  // 下載日誌
  const handleDownload = () => {
    if (!filteredLogs.length) return;
    
    const logText = filteredLogs
      .map(log => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.source ? `[${log.source}] ` : ''}${log.message}`)
      .join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <LogViewerContainer className={className}>
      <Header>
        <Title>即時日誌</Title>
        <Actions>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsAutoScroll(!isAutoScroll)}
          >
            {isAutoScroll ? '🔒' : '🔓'} 自動滾動
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
            disabled={!filteredLogs.length}
          >
            💾 下載
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleClear}
          >
            🗑️ 清除
          </Button>
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

      <Controls>
        <TopControls>
          <SearchInput
            placeholder="搜尋日誌內容..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </TopControls>
        
        <LevelFilters>
          {(['all', 'error', 'warning', 'info', 'debug'] as const).map((level) => (
            <LevelFilterButton
              key={level}
              level={level}
              active={levelFilter === level}
              count={levelCounts[level] || 0}
              onClick={() => setLevelFilter(level)}
            />
          ))}
        </LevelFilters>
      </Controls>

      <LogList>
        {loading && (
          <LoadingState>
            載入日誌中...
          </LoadingState>
        )}

        {error && (
          <ErrorState>
            <div>⚠️</div>
            <div className="error-message">
              無法載入日誌：{error.message}
            </div>
          </ErrorState>
        )}

        {!loading && !error && !filteredLogs.length && (
          <EmptyState>
            <div>📝</div>
            <div className="empty-message">
              {searchTerm || levelFilter !== 'all' ? '沒有符合條件的日誌' : '暫無日誌'}
            </div>
          </EmptyState>
        )}

        {!loading && !error && filteredLogs.length > 0 && (
          <>
            <LogListContent ref={logListRef}>
              {filteredLogs.map((log, index) => (
                <LogItemComponent
                  key={`${log.timestamp}-${index}`}
                  log={log}
                  searchTerm={searchTerm}
                />
              ))}
            </LogListContent>
            
            <StatusBar>
              <span>
                顯示 {filteredLogs.length} 條日誌
                {searchTerm && ` (搜尋: "${searchTerm}")`}
                {levelFilter !== 'all' && ` (等級: ${levelFilter})`}
              </span>
              <span>
                最後更新: {logs && logs.length > 0 ? new Date(logs[logs.length - 1].timestamp).toLocaleTimeString() : '--'}
              </span>
            </StatusBar>
          </>
        )}
      </LogList>
    </LogViewerContainer>
  );
};

// 導出類型
export type { LogViewerProps };

export default LogViewer;