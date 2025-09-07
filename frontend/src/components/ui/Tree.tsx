/**
 * 樹形控件組件 - VS Code 風格的層次結構數據顯示組件
 * 提供樹形數據的展示、選擇、展開/收起等功能
 */

import React, { useState, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 樹形控件容器
const TreeContainer = styled.div<{
  theme: 'light' | 'dark';
}>`
  width: 100%;
  background-color: ${props => getThemeColors(props.theme).background.primary};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.md};
  overflow: hidden;
`;

// 樹節點容器
const TreeNodeContainer = styled.div<{
  theme: 'light' | 'dark';
  level: number;
  isSelected?: boolean;
  isHovered?: boolean;
  disabled?: boolean;
}>`
  display: flex;
  align-items: center;
  padding: ${spacing.xs} ${spacing.sm};
  padding-left: ${props => spacing.sm + (props.level * 20)}px;
  
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  transition: ${transitions.fast};
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    if (props.disabled) {
      return `
        color: ${colors.text.disabled};
        opacity: 0.6;
      `;
    }
    
    if (props.isSelected) {
      return `
        background-color: ${colors.accent.primary};
        color: ${colors.text.inverse};
      `;
    }
    
    if (props.isHovered) {
      return `
        background-color: ${colors.background.hover};
      `;
    }
    
    return `
      color: ${colors.text.primary};
    `;
  }}
  
  &:hover {
    ${props => {
      if (props.disabled) return '';
      
      const colors = getThemeColors(props.theme);
      
      if (props.isSelected) {
        return `background-color: ${colors.accent.hover};`;
      }
      
      return `
        background-color: ${colors.background.hover};
      `;
    }}
  }
`;

// 展開/收起按鈕
const ExpandButton = styled.button<{
  theme: 'light' | 'dark';
  expanded: boolean;
  hasChildren: boolean;
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: ${spacing.xs};
  
  background: none;
  border: none;
  color: ${props => getThemeColors(props.theme).text.secondary};
  cursor: ${props => props.hasChildren ? 'pointer' : 'default'};
  transition: ${transitions.fast};
  
  opacity: ${props => props.hasChildren ? 1 : 0};
  transform: ${props => props.expanded ? 'rotate(90deg)' : 'rotate(0deg)'};
  
  &:hover {
    color: ${props => props.hasChildren ? getThemeColors(props.theme).text.primary : 'inherit'};
  }
  
  &::before {
    content: '▶';
    font-size: 10px;
  }
`;

// 節點圖標
const NodeIcon = styled.span<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: ${spacing.xs};
  
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-size: 14px;
`;

// 節點標籤
const NodeLabel = styled.span<{
  theme: 'light' | 'dark';
}>`
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
  user-select: none;
`;

// 節點操作按鈕
const NodeActions = styled.div<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  gap: ${spacing.xs};
  margin-left: ${spacing.sm};
  opacity: 0;
  transition: ${transitions.fast};
  
  ${TreeNodeContainer}:hover & {
    opacity: 1;
  }
`;

// 操作按鈕
const ActionButton = styled.button<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  
  background: none;
  border: none;
  border-radius: ${borderRadius.sm};
  color: ${props => getThemeColors(props.theme).text.secondary};
  cursor: pointer;
  transition: ${transitions.fast};
  
  &:hover {
    background-color: ${props => getThemeColors(props.theme).background.hover};
    color: ${props => getThemeColors(props.theme).text.primary};
  }
`;

// 複選框
const Checkbox = styled.input<{
  theme: 'light' | 'dark';
}>`
  margin-right: ${spacing.xs};
  cursor: pointer;
  
  &:disabled {
    cursor: not-allowed;
  }
`;

// 拖拽指示器
const DragIndicator = styled.div<{
  theme: 'light' | 'dark';
  position: 'before' | 'after' | 'inside';
  visible: boolean;
}>`
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background-color: ${props => getThemeColors(props.theme).accent.primary};
  opacity: ${props => props.visible ? 1 : 0};
  transition: ${transitions.fast};
  
  ${props => {
    switch (props.position) {
      case 'before':
        return 'top: -1px;';
      case 'after':
        return 'bottom: -1px;';
      case 'inside':
        return `
          top: 0;
          bottom: 0;
          height: auto;
          background-color: ${getThemeColors(props.theme).accent.primary}33;
        `;
    }
  }}
`;

// 樹節點數據介面
export interface TreeNodeData {
  id: string;
  label: string;
  icon?: string;
  disabled?: boolean;
  children?: TreeNodeData[];
  data?: any;
}

// 樹形控件組件介面
export interface TreeProps {
  theme: 'light' | 'dark';
  data: TreeNodeData[];
  selectedKeys?: string[];
  expandedKeys?: string[];
  checkedKeys?: string[];
  defaultSelectedKeys?: string[];
  defaultExpandedKeys?: string[];
  defaultCheckedKeys?: string[];
  multiple?: boolean;
  checkable?: boolean;
  draggable?: boolean;
  showIcon?: boolean;
  showLine?: boolean;
  autoExpandParent?: boolean;
  disabled?: boolean;
  onSelect?: (selectedKeys: string[], info: { node: TreeNodeData; selected: boolean }) => void;
  onExpand?: (expandedKeys: string[], info: { node: TreeNodeData; expanded: boolean }) => void;
  onCheck?: (checkedKeys: string[], info: { node: TreeNodeData; checked: boolean }) => void;
  onDrop?: (info: { dragNode: TreeNodeData; dropNode: TreeNodeData; dropPosition: number }) => void;
  onRightClick?: (info: { node: TreeNodeData; event: React.MouseEvent }) => void;
  renderTitle?: (node: TreeNodeData) => React.ReactNode;
  className?: string;
}

/**
 * 樹節點組件
 */
interface TreeNodeProps {
  theme: 'light' | 'dark';
  node: TreeNodeData;
  level: number;
  isSelected: boolean;
  isExpanded: boolean;
  isChecked: boolean;
  checkable: boolean;
  draggable: boolean;
  showIcon: boolean;
  disabled: boolean;
  onSelect: (nodeId: string) => void;
  onExpand: (nodeId: string) => void;
  onCheck: (nodeId: string, checked: boolean) => void;
  onRightClick?: (node: TreeNodeData, event: React.MouseEvent) => void;
  renderTitle?: (node: TreeNodeData) => React.ReactNode;
}

const TreeNode: React.FC<TreeNodeProps> = ({
  theme,
  node,
  level,
  isSelected,
  isExpanded,
  isChecked,
  checkable,
  draggable,
  showIcon,
  disabled,
  onSelect,
  onExpand,
  onCheck,
  onRightClick,
  renderTitle
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragPosition, setDragPosition] = useState<'before' | 'after' | 'inside' | null>(null);
  
  const hasChildren = node.children && node.children.length > 0;
  const nodeDisabled = disabled || node.disabled;
  
  // 處理節點點擊
  const handleNodeClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (nodeDisabled) return;
    
    onSelect(node.id);
  }, [nodeDisabled, onSelect, node.id]);
  
  // 處理展開/收起
  const handleExpandClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!hasChildren || nodeDisabled) return;
    
    onExpand(node.id);
  }, [hasChildren, nodeDisabled, onExpand, node.id]);
  
  // 處理複選框變更
  const handleCheckChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    event.stopPropagation();
    
    if (nodeDisabled) return;
    
    onCheck(node.id, event.target.checked);
  }, [nodeDisabled, onCheck, node.id]);
  
  // 處理右鍵點擊
  const handleRightClick = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (nodeDisabled) return;
    
    onRightClick?.(node, event);
  }, [nodeDisabled, onRightClick, node]);
  
  // 處理拖拽開始
  const handleDragStart = useCallback((event: React.DragEvent) => {
    if (!draggable || nodeDisabled) {
      event.preventDefault();
      return;
    }
    
    setIsDragging(true);
    event.dataTransfer.setData('text/plain', node.id);
    event.dataTransfer.effectAllowed = 'move';
  }, [draggable, nodeDisabled, node.id]);
  
  // 處理拖拽結束
  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    setDragPosition(null);
  }, []);
  
  // 處理拖拽懸停
  const handleDragOver = useCallback((event: React.DragEvent) => {
    if (!draggable || nodeDisabled) return;
    
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    
    const rect = event.currentTarget.getBoundingClientRect();
    const y = event.clientY - rect.top;
    const height = rect.height;
    
    if (y < height * 0.25) {
      setDragPosition('before');
    } else if (y > height * 0.75) {
      setDragPosition('after');
    } else {
      setDragPosition('inside');
    }
  }, [draggable, nodeDisabled]);
  
  // 處理拖拽離開
  const handleDragLeave = useCallback(() => {
    setDragPosition(null);
  }, []);
  
  // 處理放置
  const handleDrop = useCallback((event: React.DragEvent) => {
    if (!draggable || nodeDisabled) return;
    
    event.preventDefault();
    event.stopPropagation();
    
    const dragNodeId = event.dataTransfer.getData('text/plain');
    if (dragNodeId === node.id) return;
    
    // 這裡應該觸發 onDrop 回調
    setDragPosition(null);
  }, [draggable, nodeDisabled, node.id]);
  
  return (
    <>
      <TreeNodeContainer
        theme={theme}
        level={level}
        isSelected={isSelected}
        isHovered={isHovered}
        disabled={nodeDisabled}
        onClick={handleNodeClick}
        onContextMenu={handleRightClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        draggable={draggable && !nodeDisabled}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          position: 'relative',
          opacity: isDragging ? 0.5 : 1
        }}
      >
        <DragIndicator
          theme={theme}
          position="before"
          visible={dragPosition === 'before'}
        />
        <DragIndicator
          theme={theme}
          position="inside"
          visible={dragPosition === 'inside'}
        />
        <DragIndicator
          theme={theme}
          position="after"
          visible={dragPosition === 'after'}
        />
        
        <ExpandButton
          theme={theme}
          expanded={isExpanded}
          hasChildren={hasChildren}
          onClick={handleExpandClick}
        />
        
        {checkable && (
          <Checkbox
            theme={theme}
            type="checkbox"
            checked={isChecked}
            disabled={nodeDisabled}
            onChange={handleCheckChange}
          />
        )}
        
        {showIcon && (
          <NodeIcon theme={theme}>
            {node.icon || (hasChildren ? '📁' : '📄')}
          </NodeIcon>
        )}
        
        <NodeLabel theme={theme}>
          {renderTitle ? renderTitle(node) : node.label}
        </NodeLabel>
        
        <NodeActions theme={theme}>
          <ActionButton theme={theme} title="編輯">
            ✏️
          </ActionButton>
          <ActionButton theme={theme} title="刪除">
            🗑️
          </ActionButton>
        </NodeActions>
      </TreeNodeContainer>
      
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map(child => (
            <TreeNode
              key={child.id}
              theme={theme}
              node={child}
              level={level + 1}
              isSelected={isSelected}
              isExpanded={isExpanded}
              isChecked={isChecked}
              checkable={checkable}
              draggable={draggable}
              showIcon={showIcon}
              disabled={disabled}
              onSelect={onSelect}
              onExpand={onExpand}
              onCheck={onCheck}
              onRightClick={onRightClick}
              renderTitle={renderTitle}
            />
          ))}
        </div>
      )}
    </>
  );
};

/**
 * 樹形控件組件
 * 用於顯示層次結構數據
 */
export const Tree: React.FC<TreeProps> = ({
  theme,
  data,
  selectedKeys: controlledSelectedKeys,
  expandedKeys: controlledExpandedKeys,
  checkedKeys: controlledCheckedKeys,
  defaultSelectedKeys = [],
  defaultExpandedKeys = [],
  defaultCheckedKeys = [],
  multiple = false,
  checkable = false,
  draggable = false,
  showIcon = true,
  showLine = false,
  autoExpandParent = true,
  disabled = false,
  onSelect,
  onExpand,
  onCheck,
  onDrop,
  onRightClick,
  renderTitle,
  className
}) => {
  // 內部狀態
  const [internalSelectedKeys, setInternalSelectedKeys] = useState<string[]>(defaultSelectedKeys);
  const [internalExpandedKeys, setInternalExpandedKeys] = useState<string[]>(defaultExpandedKeys);
  const [internalCheckedKeys, setInternalCheckedKeys] = useState<string[]>(defaultCheckedKeys);
  
  // 判斷是否為受控組件
  const isSelectedControlled = controlledSelectedKeys !== undefined;
  const isExpandedControlled = controlledExpandedKeys !== undefined;
  const isCheckedControlled = controlledCheckedKeys !== undefined;
  
  const selectedKeys = isSelectedControlled ? controlledSelectedKeys : internalSelectedKeys;
  const expandedKeys = isExpandedControlled ? controlledExpandedKeys : internalExpandedKeys;
  const checkedKeys = isCheckedControlled ? controlledCheckedKeys : internalCheckedKeys;
  
  // 獲取所有節點的映射
  const nodeMap = useMemo(() => {
    const map = new Map<string, TreeNodeData>();
    
    const traverse = (nodes: TreeNodeData[]) => {
      nodes.forEach(node => {
        map.set(node.id, node);
        if (node.children) {
          traverse(node.children);
        }
      });
    };
    
    traverse(data);
    return map;
  }, [data]);
  
  // 處理節點選擇
  const handleSelect = useCallback((nodeId: string) => {
    const node = nodeMap.get(nodeId);
    if (!node) return;
    
    let newSelectedKeys: string[];
    
    if (multiple) {
      const isSelected = selectedKeys.includes(nodeId);
      if (isSelected) {
        newSelectedKeys = selectedKeys.filter(key => key !== nodeId);
      } else {
        newSelectedKeys = [...selectedKeys, nodeId];
      }
    } else {
      newSelectedKeys = selectedKeys.includes(nodeId) ? [] : [nodeId];
    }
    
    if (!isSelectedControlled) {
      setInternalSelectedKeys(newSelectedKeys);
    }
    
    onSelect?.(newSelectedKeys, {
      node,
      selected: newSelectedKeys.includes(nodeId)
    });
  }, [nodeMap, selectedKeys, multiple, isSelectedControlled, onSelect]);
  
  // 處理節點展開/收起
  const handleExpand = useCallback((nodeId: string) => {
    const node = nodeMap.get(nodeId);
    if (!node) return;
    
    const isExpanded = expandedKeys.includes(nodeId);
    let newExpandedKeys: string[];
    
    if (isExpanded) {
      newExpandedKeys = expandedKeys.filter(key => key !== nodeId);
    } else {
      newExpandedKeys = [...expandedKeys, nodeId];
    }
    
    if (!isExpandedControlled) {
      setInternalExpandedKeys(newExpandedKeys);
    }
    
    onExpand?.(newExpandedKeys, {
      node,
      expanded: !isExpanded
    });
  }, [nodeMap, expandedKeys, isExpandedControlled, onExpand]);
  
  // 處理節點勾選
  const handleCheck = useCallback((nodeId: string, checked: boolean) => {
    const node = nodeMap.get(nodeId);
    if (!node) return;
    
    let newCheckedKeys: string[];
    
    if (checked) {
      newCheckedKeys = [...checkedKeys, nodeId];
    } else {
      newCheckedKeys = checkedKeys.filter(key => key !== nodeId);
    }
    
    if (!isCheckedControlled) {
      setInternalCheckedKeys(newCheckedKeys);
    }
    
    onCheck?.(newCheckedKeys, {
      node,
      checked
    });
  }, [nodeMap, checkedKeys, isCheckedControlled, onCheck]);
  
  // 渲染樹節點
  const renderTreeNodes = useCallback((nodes: TreeNodeData[], level: number = 0) => {
    return nodes.map(node => (
      <TreeNode
        key={node.id}
        theme={theme}
        node={node}
        level={level}
        isSelected={selectedKeys.includes(node.id)}
        isExpanded={expandedKeys.includes(node.id)}
        isChecked={checkedKeys.includes(node.id)}
        checkable={checkable}
        draggable={draggable}
        showIcon={showIcon}
        disabled={disabled}
        onSelect={handleSelect}
        onExpand={handleExpand}
        onCheck={handleCheck}
        onRightClick={onRightClick}
        renderTitle={renderTitle}
      />
    ));
  }, [theme, selectedKeys, expandedKeys, checkedKeys, checkable, draggable, showIcon, disabled, handleSelect, handleExpand, handleCheck, onRightClick, renderTitle]);
  
  return (
    <TreeContainer theme={theme} className={className}>
      {renderTreeNodes(data)}
    </TreeContainer>
  );
};

// 目錄樹組件介面
export interface DirectoryTreeProps extends Omit<TreeProps, 'showIcon'> {
  showFile?: boolean;
  fileIcon?: string;
  folderIcon?: string;
  expandedFolderIcon?: string;
}

/**
 * 目錄樹組件
 * 專門用於顯示文件和文件夾結構
 */
export const DirectoryTree: React.FC<DirectoryTreeProps> = ({
  showFile = true,
  fileIcon = '📄',
  folderIcon = '📁',
  expandedFolderIcon = '📂',
  ...props
}) => {
  // 自定義渲染標題
  const renderTitle = useCallback((node: TreeNodeData) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = props.expandedKeys?.includes(node.id) || props.defaultExpandedKeys?.includes(node.id);
    
    let icon = fileIcon;
    if (hasChildren) {
      icon = isExpanded ? expandedFolderIcon : folderIcon;
    }
    
    return (
      <span style={{ display: 'flex', alignItems: 'center' }}>
        <span style={{ marginRight: spacing.xs }}>{icon}</span>
        {node.label}
      </span>
    );
  }, [props.expandedKeys, props.defaultExpandedKeys, fileIcon, folderIcon, expandedFolderIcon]);
  
  return (
    <Tree
      {...props}
      showIcon={false}
      renderTitle={renderTitle}
    />
  );
};

export default Tree;