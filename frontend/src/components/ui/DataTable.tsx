/**
 * DataTable 組件
 * 統一的數據表格組件，支援排序、篩選、分頁等功能
 */

import React, { useState, useMemo } from 'react';
import styled from 'styled-components';
import { spacing, borderRadius } from '../../styles';
import type { BaseComponentProps } from '../../types';
import { Button } from './Button';
import { Input } from './Input';

// ============= 類型定義 =============

export interface DataTableColumn<T = any> {
  /** 欄位鍵值 */
  key: keyof T;
  /** 欄位標題 */
  title: string;
  /** 欄位寬度 */
  width?: string | number;
  /** 是否可排序 */
  sortable?: boolean;
  /** 是否可篩選 */
  filterable?: boolean;
  /** 自訂渲染函數 */
  render?: (value: any, record: T, index: number) => React.ReactNode;
  /** 對齊方式 */
  align?: 'left' | 'center' | 'right';
  /** 是否固定欄位 */
  fixed?: 'left' | 'right';
}

export interface DataTableProps<T = any> extends BaseComponentProps {
  /** 表格欄位配置 */
  columns: DataTableColumn<T>[];
  /** 表格數據 */
  dataSource: T[];
  /** 行鍵值字段 */
  rowKey?: keyof T | ((record: T) => string | number);
  /** 是否顯示載入狀態 */
  loading?: boolean;
  /** 空數據提示 */
  emptyText?: string;
  /** 是否顯示分頁 */
  pagination?: boolean | {
    current?: number;
    pageSize?: number;
    total?: number;
    showSizeChanger?: boolean;
    showQuickJumper?: boolean;
    onChange?: (page: number, pageSize: number) => void;
  };
  /** 行選擇配置 */
  rowSelection?: {
    type?: 'checkbox' | 'radio';
    selectedRowKeys?: (string | number)[];
    onChange?: (selectedRowKeys: (string | number)[], selectedRows: T[]) => void;
  };
  /** 行點擊事件 */
  onRowClick?: (record: T, index: number) => void;
  /** 表格大小 */
  size?: 'small' | 'middle' | 'large';
  /** 是否顯示邊框 */
  bordered?: boolean;
  /** 是否顯示斑馬紋 */
  striped?: boolean;
}

type SortOrder = 'asc' | 'desc' | null;

interface SortState {
  key: string;
  order: SortOrder;
}

// ============= 樣式定義 =============

const TableContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--color-background-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: ${borderRadius.lg};
  overflow: hidden;
`;

const TableHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing[4]};
  background-color: var(--color-background-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  gap: ${spacing[4]};
`;

const TableFilters = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[3]};
`;

const TableWrapper = styled.div`
  flex: 1;
  overflow: auto;
`;

const Table = styled.table<{ size: string; bordered: boolean; striped: boolean }>`
  width: 100%;
  border-collapse: collapse;
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '0.75rem';
      case 'large': return '0.875rem';
      default: return '0.8125rem';
    }
  }};
`;

const TableHead = styled.thead`
  background-color: var(--color-background-tertiary);
  position: sticky;
  top: 0;
  z-index: 1;
`;

const TableBody = styled.tbody``;

const TableRow = styled.tr<{ clickable: boolean; striped: boolean; index: number }>`
  ${props => props.striped && props.index % 2 === 1 && `
    background-color: var(--color-background-secondary);
  `}
  
  ${props => props.clickable && `
    cursor: pointer;
    
    &:hover {
      background-color: var(--color-background-hover);
    }
  `}
  
  transition: background-color 0.2s ease;
`;

const TableHeaderCell = styled.th<{ 
  align: string; 
  sortable: boolean; 
  width?: string | number;
  bordered: boolean;
}>`
  padding: ${spacing[3]} ${spacing[4]};
  text-align: ${props => props.align};
  font-weight: 600;
  color: var(--color-text-primary);
  background-color: var(--color-background-tertiary);
  border-bottom: 1px solid var(--color-border-primary);
  ${props => props.bordered && 'border-right: 1px solid var(--color-border-primary);'}
  ${props => props.width && `width: ${typeof props.width === 'number' ? props.width + 'px' : props.width};`}
  white-space: nowrap;
  
  ${props => props.sortable && `
    cursor: pointer;
    user-select: none;
    
    &:hover {
      background-color: var(--color-background-hover);
    }
  `}
`;

const TableCell = styled.td<{ 
  align: string; 
  bordered: boolean;
}>`
  padding: ${spacing[3]} ${spacing[4]};
  text-align: ${props => props.align};
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border-secondary);
  ${props => props.bordered && 'border-right: 1px solid var(--color-border-secondary);'}
  vertical-align: middle;
`;

const SortIcon = styled.span<{ order: SortOrder }>`
  margin-left: ${spacing[2]};
  font-size: 0.75rem;
  color: ${props => props.order ? 'var(--color-interactive-primary)' : 'var(--color-text-tertiary)'};
`;

const EmptyContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: ${spacing[8]};
  color: var(--color-text-tertiary);
  text-align: center;
`;

const EmptyIcon = styled.div`
  font-size: 3rem;
  margin-bottom: ${spacing[4]};
  opacity: 0.5;
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${spacing[8]};
  color: var(--color-text-secondary);
`;

const PaginationContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing[4]};
  background-color: var(--color-background-secondary);
  border-top: 1px solid var(--color-border-primary);
`;

const PaginationInfo = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const PaginationControls = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[2]};
`;

// ============= 組件實現 =============

/**
 * DataTable 組件
 * 提供統一的數據表格功能，支援排序、篩選、分頁等
 * 
 * @param props - DataTable 屬性
 * @returns React 組件
 */
export const DataTable = <T extends Record<string, any>>({
  columns,
  dataSource,
  rowKey = 'id',
  loading = false,
  emptyText = '暫無數據',
  pagination = false,
  rowSelection,
  onRowClick,
  size = 'middle',
  bordered = false,
  striped = true,
  className,
  ...rest
}: DataTableProps<T>) => {
  const [sortState, setSortState] = useState<SortState>({ key: '', order: null });
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  // 獲取行鍵值
  const getRowKey = (record: T, index: number): string | number => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey] || index;
  };

  // 處理排序
  const handleSort = (key: string) => {
    setSortState(prev => {
      if (prev.key === key) {
        const nextOrder = prev.order === 'asc' ? 'desc' : prev.order === 'desc' ? null : 'asc';
        return { key: nextOrder ? key : '', order: nextOrder };
      }
      return { key, order: 'asc' };
    });
  };

  // 處理篩選
  const handleFilter = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  // 處理數據排序和篩選
  const processedData = useMemo(() => {
    let result = [...dataSource];

    // 應用篩選
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        result = result.filter(item => 
          String(item[key]).toLowerCase().includes(value.toLowerCase())
        );
      }
    });

    // 應用排序
    if (sortState.key && sortState.order) {
      result.sort((a, b) => {
        const aVal = a[sortState.key];
        const bVal = b[sortState.key];
        
        if (aVal < bVal) return sortState.order === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortState.order === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [dataSource, filters, sortState]);

  // 分頁數據
  const paginatedData = useMemo(() => {
    if (!pagination) return processedData;
    
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return processedData.slice(start, end);
  }, [processedData, pagination, currentPage, pageSize]);

  // 渲染表格標題
  const renderTableHeader = () => (
    <TableHead>
      <TableRow clickable={false} striped={false} index={0}>
        {rowSelection && (
          <TableHeaderCell align="center" sortable={false} bordered={bordered}>
            {/* 全選框 */}
          </TableHeaderCell>
        )}
        {columns.map((column) => (
          <TableHeaderCell
            key={String(column.key)}
            align={column.align || 'left'}
            sortable={column.sortable || false}
            width={column.width}
            bordered={bordered}
            onClick={column.sortable ? () => handleSort(String(column.key)) : undefined}
          >
            {column.title}
            {column.sortable && (
              <SortIcon order={sortState.key === String(column.key) ? sortState.order : null}>
                {sortState.key === String(column.key) && sortState.order === 'asc' ? '↑' :
                 sortState.key === String(column.key) && sortState.order === 'desc' ? '↓' : '↕'}
              </SortIcon>
            )}
          </TableHeaderCell>
        ))}
      </TableRow>
    </TableHead>
  );

  // 渲染表格內容
  const renderTableBody = () => {
    if (loading) {
      return (
        <tbody>
          <tr>
            <td colSpan={columns.length + (rowSelection ? 1 : 0)}>
              <LoadingContainer>
                載入中...
              </LoadingContainer>
            </td>
          </tr>
        </tbody>
      );
    }

    if (paginatedData.length === 0) {
      return (
        <tbody>
          <tr>
            <td colSpan={columns.length + (rowSelection ? 1 : 0)}>
              <EmptyContainer>
                <EmptyIcon>📋</EmptyIcon>
                {emptyText}
              </EmptyContainer>
            </td>
          </tr>
        </tbody>
      );
    }

    return (
      <TableBody>
        {paginatedData.map((record, index) => (
          <TableRow
            key={getRowKey(record, index)}
            clickable={!!onRowClick}
            striped={striped}
            index={index}
            onClick={() => onRowClick?.(record, index)}
          >
            {rowSelection && (
              <TableCell align="center" bordered={bordered}>
                {/* 選擇框 */}
              </TableCell>
            )}
            {columns.map((column) => (
              <TableCell
                key={String(column.key)}
                align={column.align || 'left'}
                bordered={bordered}
              >
                {column.render 
                  ? column.render(record[column.key], record, index)
                  : String(record[column.key] || '')
                }
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    );
  };

  // 渲染篩選器
  const renderFilters = () => {
    const filterableColumns = columns.filter(col => col.filterable);
    if (filterableColumns.length === 0) return null;

    return (
      <TableFilters>
        {filterableColumns.map((column) => (
          <Input
            key={String(column.key)}
            placeholder={`篩選 ${column.title}`}
            value={filters[String(column.key)] || ''}
            onChange={(e) => handleFilter(String(column.key), e.target.value)}
            size="sm"
          />
        ))}
      </TableFilters>
    );
  };

  // 渲染分頁
  const renderPagination = () => {
    if (!pagination) return null;

    const total = processedData.length;
    const totalPages = Math.ceil(total / pageSize);
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, total);

    return (
      <PaginationContainer>
        <PaginationInfo>
          顯示 {start}-{end} 項，共 {total} 項
        </PaginationInfo>
        <PaginationControls>
          <Button
            size="sm"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
          >
            上一頁
          </Button>
          <span>{currentPage} / {totalPages}</span>
          <Button
            size="sm"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
          >
            下一頁
          </Button>
        </PaginationControls>
      </PaginationContainer>
    );
  };

  return (
    <TableContainer className={className} {...rest}>
      {/* 表格工具欄 */}
      <TableHeader>
        <div>數據表格</div>
        {renderFilters()}
      </TableHeader>

      {/* 表格主體 */}
      <TableWrapper>
        <Table size={size} bordered={bordered} striped={striped}>
          {renderTableHeader()}
          {renderTableBody()}
        </Table>
      </TableWrapper>

      {/* 分頁 */}
      {renderPagination()}
    </TableContainer>
  );
};

export default DataTable;