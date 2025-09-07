/**
 * 表格組件 - VS Code 風格的數據表格
 * 支援排序、篩選、分頁、虛擬滾動等功能
 */

import React, { useState, useMemo, useCallback } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 表格容器
const TableContainer = styled.div<{ theme: 'light' | 'dark' }>`
  background-color: ${props => getThemeColors(props.theme).background.secondary};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.md};
  overflow: hidden;
  position: relative;
`;

// 表格包裝器（支援水平滾動）
const TableWrapper = styled.div`
  overflow-x: auto;
  overflow-y: hidden;
  max-height: 600px;
`;

// 表格主體
const StyledTable = styled.table<{ theme: 'light' | 'dark' }>`
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  
  th, td {
    text-align: left;
    padding: ${spacing.sm} ${spacing.md};
    border-bottom: 1px solid ${props => getThemeColors(props.theme).border.secondary};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  th {
    background-color: ${props => getThemeColors(props.theme).background.tertiary};
    color: ${props => getThemeColors(props.theme).text.primary};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: sticky;
    top: 0;
    z-index: 10;
    
    &:first-child {
      border-top-left-radius: ${borderRadius.md};
    }
    
    &:last-child {
      border-top-right-radius: ${borderRadius.md};
    }
  }
  
  td {
    color: ${props => getThemeColors(props.theme).text.secondary};
    transition: background-color ${transitions.fast} ease;
  }
  
  tbody tr {
    &:hover {
      background-color: ${props => getThemeColors(props.theme).interactive.hover};
    }
    
    &:last-child td {
      border-bottom: none;
    }
    
    &.selected {
      background-color: ${props => getThemeColors(props.theme).interactive.selected};
    }
  }
`;

// 可排序的表頭
const SortableHeader = styled.th<{ 
  theme: 'light' | 'dark';
  sortable?: boolean;
  sortDirection?: 'asc' | 'desc' | null;
}>`
  ${props => props.sortable && `
    cursor: pointer;
    user-select: none;
    position: relative;
    
    &:hover {
      background-color: ${getThemeColors(props.theme).interactive.hover};
    }
    
    &::after {
      content: '';
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      width: 0;
      height: 0;
      border-left: 4px solid transparent;
      border-right: 4px solid transparent;
      opacity: ${props.sortDirection ? '1' : '0.3'};
      
      ${props.sortDirection === 'asc' ? `
        border-bottom: 6px solid ${getThemeColors(props.theme).text.secondary};
      ` : props.sortDirection === 'desc' ? `
        border-top: 6px solid ${getThemeColors(props.theme).text.secondary};
      ` : `
        border-bottom: 6px solid ${getThemeColors(props.theme).text.disabled};
      `}
    }
  `}
`;

// 表格工具列
const TableToolbar = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing.md} ${spacing.lg};
  background-color: ${props => getThemeColors(props.theme).background.tertiary};
  border-bottom: 1px solid ${props => getThemeColors(props.theme).border.secondary};
  gap: ${spacing.md};
`;

// 搜尋輸入框
const SearchInput = styled.input<{ theme: 'light' | 'dark' }>`
  padding: ${spacing.xs} ${spacing.sm};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.sm};
  background-color: ${props => getThemeColors(props.theme).background.primary};
  color: ${props => getThemeColors(props.theme).text.primary};
  font-size: 12px;
  min-width: 200px;
  
  &::placeholder {
    color: ${props => getThemeColors(props.theme).text.disabled};
  }
  
  &:focus {
    outline: 1px solid ${props => getThemeColors(props.theme).border.focus};
    outline-offset: -1px;
  }
`;

// 分頁控制器
const PaginationContainer = styled.div<{ theme: 'light' | 'dark' }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing.md} ${spacing.lg};
  background-color: ${props => getThemeColors(props.theme).background.tertiary};
  border-top: 1px solid ${props => getThemeColors(props.theme).border.secondary};
  font-size: 12px;
  color: ${props => getThemeColors(props.theme).text.secondary};
`;

const PaginationControls = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
`;

const PaginationButton = styled.button<{ theme: 'light' | 'dark'; active?: boolean }>`
  padding: ${spacing.xs} ${spacing.sm};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.sm};
  background-color: ${props => props.active 
    ? getThemeColors(props.theme).interactive.primary
    : getThemeColors(props.theme).background.primary
  };
  color: ${props => props.active 
    ? getThemeColors(props.theme).interactive.primaryForeground
    : getThemeColors(props.theme).text.secondary
  };
  font-size: 11px;
  min-width: 32px;
  transition: all ${transitions.fast} ease;
  
  &:hover:not(:disabled) {
    background-color: ${props => props.active 
      ? getThemeColors(props.theme).interactive.primaryHover
      : getThemeColors(props.theme).interactive.hover
    };
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// 狀態單元格
const StatusCell = styled.td<{ 
  theme: 'light' | 'dark';
  status: 'success' | 'warning' | 'error' | 'info' | 'inactive';
}>`
  color: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'success': return colors.status.success;
      case 'warning': return colors.status.warning;
      case 'error': return colors.status.error;
      case 'info': return colors.status.info;
      default: return colors.text.disabled;
    }
  }} !important;
  font-weight: 500;
  
  &::before {
    content: '●';
    margin-right: ${spacing.xs};
  }
`;

// 動作單元格
const ActionCell = styled.td`
  width: 120px;
  text-align: right;
  
  button {
    margin-left: ${spacing.xs};
    padding: 2px 6px;
    font-size: 10px;
    border-radius: ${borderRadius.sm};
  }
`;

// 表格列定義介面
export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex: keyof T;
  width?: string | number;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
}

// 表格組件介面
export interface TableProps<T = any> {
  theme: 'light' | 'dark';
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    showSizeChanger?: boolean;
    showQuickJumper?: boolean;
  };
  searchable?: boolean;
  searchPlaceholder?: string;
  selectedRowKeys?: string[];
  rowKey?: string | ((record: T) => string);
  onSearch?: (value: string) => void;
  onSort?: (column: string, direction: 'asc' | 'desc' | null) => void;
  onPageChange?: (page: number, pageSize: number) => void;
  onRowSelect?: (selectedKeys: string[], selectedRows: T[]) => void;
  className?: string;
}

/**
 * 表格組件
 * 提供完整的數據表格功能
 */
export const Table = <T extends Record<string, any>>({
  theme,
  columns,
  data,
  loading = false,
  pagination,
  searchable = false,
  searchPlaceholder = '搜尋...',
  selectedRowKeys = [],
  rowKey = 'id',
  onSearch,
  onSort,
  onPageChange,
  onRowSelect,
  className
}: TableProps<T>) => {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null);
  const [searchValue, setSearchValue] = useState('');
  
  // 處理排序
  const handleSort = useCallback((column: string) => {
    let newDirection: 'asc' | 'desc' | null = 'asc';
    
    if (sortColumn === column) {
      if (sortDirection === 'asc') {
        newDirection = 'desc';
      } else if (sortDirection === 'desc') {
        newDirection = null;
      }
    }
    
    setSortColumn(newDirection ? column : null);
    setSortDirection(newDirection);
    onSort?.(column, newDirection);
  }, [sortColumn, sortDirection, onSort]);
  
  // 處理搜尋
  const handleSearch = useCallback((value: string) => {
    setSearchValue(value);
    onSearch?.(value);
  }, [onSearch]);
  
  // 獲取行鍵值
  const getRowKey = useCallback((record: T, index: number): string => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey] || index.toString();
  }, [rowKey]);
  
  // 渲染分頁控制器
  const renderPagination = () => {
    if (!pagination) return null;
    
    const { current, pageSize, total } = pagination;
    const totalPages = Math.ceil(total / pageSize);
    const startItem = (current - 1) * pageSize + 1;
    const endItem = Math.min(current * pageSize, total);
    
    return (
      <PaginationContainer theme={theme}>
        <div>
          顯示 {startItem}-{endItem} 項，共 {total} 項
        </div>
        
        <PaginationControls>
          <PaginationButton
            theme={theme}
            disabled={current <= 1}
            onClick={() => onPageChange?.(current - 1, pageSize)}
          >
            上一頁
          </PaginationButton>
          
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            const page = current <= 3 ? i + 1 : current - 2 + i;
            if (page > totalPages) return null;
            
            return (
              <PaginationButton
                key={page}
                theme={theme}
                active={page === current}
                onClick={() => onPageChange?.(page, pageSize)}
              >
                {page}
              </PaginationButton>
            );
          })}
          
          <PaginationButton
            theme={theme}
            disabled={current >= totalPages}
            onClick={() => onPageChange?.(current + 1, pageSize)}
          >
            下一頁
          </PaginationButton>
        </PaginationControls>
      </PaginationContainer>
    );
  };
  
  return (
    <TableContainer theme={theme} className={className}>
      {searchable && (
        <TableToolbar theme={theme}>
          <SearchInput
            theme={theme}
            type="text"
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => handleSearch(e.target.value)}
          />
          <div>
            {selectedRowKeys.length > 0 && (
              <span>已選擇 {selectedRowKeys.length} 項</span>
            )}
          </div>
        </TableToolbar>
      )}
      
      <TableWrapper>
        <StyledTable theme={theme}>
          <thead>
            <tr>
              {columns.map((column) => (
                <SortableHeader
                  key={column.key}
                  theme={theme}
                  sortable={column.sortable}
                  sortDirection={sortColumn === column.key ? sortDirection : null}
                  style={{ 
                    width: column.width,
                    textAlign: column.align || 'left'
                  }}
                  onClick={column.sortable ? () => handleSort(column.key) : undefined}
                >
                  {column.title}
                </SortableHeader>
              ))}
            </tr>
          </thead>
          
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: spacing.xl }}>
                  載入中...
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: spacing.xl }}>
                  暫無資料
                </td>
              </tr>
            ) : (
              data.map((record, index) => {
                const key = getRowKey(record, index);
                const isSelected = selectedRowKeys.includes(key);
                
                return (
                  <tr
                    key={key}
                    className={isSelected ? 'selected' : ''}
                  >
                    {columns.map((column) => {
                      const value = record[column.dataIndex];
                      const cellContent = column.render 
                        ? column.render(value, record, index)
                        : value;
                      
                      return (
                        <td
                          key={column.key}
                          style={{ textAlign: column.align || 'left' }}
                        >
                          {cellContent}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </StyledTable>
      </TableWrapper>
      
      {renderPagination()}
    </TableContainer>
  );
};

// 導出相關組件
export { StatusCell, ActionCell };
export default Table;