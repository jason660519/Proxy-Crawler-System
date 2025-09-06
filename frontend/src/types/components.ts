/**
 * 組件相關類型定義
 * 定義 React 組件的 Props 和狀態類型
 */

import type { ReactNode, CSSProperties, HTMLAttributes, ButtonHTMLAttributes, InputHTMLAttributes } from 'react';
import type {
  ProxyNode,
  Task,
  User,
  TableColumn,
  TableSort,
  TableFilter,
  TableSelection,
  FormField,
  FormError,
  NotificationType,
  ThemeMode
} from './index';

// ============================================================================
// 基礎組件類型
// ============================================================================

/**
 * 基礎組件 Props
 */
export interface BaseComponentProps {
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
  id?: string;
  'data-testid'?: string;
}

/**
 * 尺寸類型
 */
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * 變體類型
 */
export type Variant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';

/**
 * 位置類型
 */
export type Position = 'top' | 'bottom' | 'left' | 'right' | 'center';

/**
 * 對齊類型
 */
export type Alignment = 'start' | 'center' | 'end' | 'stretch';

// ============================================================================
// 按鈕組件類型
// ============================================================================

/**
 * 按鈕變體類型
 */
export type ButtonVariant = 
  | 'primary'
  | 'secondary'
  | 'outline'
  | 'ghost'
  | 'link'
  | 'danger';

/**
 * 按鈕 Props
 */
export interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'size'>, BaseComponentProps {
  variant?: ButtonVariant;
  size?: Size;
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  rounded?: boolean;
}

/**
 * 圖標按鈕 Props
 */
export interface IconButtonProps extends Omit<ButtonProps, 'children'> {
  icon: ReactNode;
  'aria-label': string;
  tooltip?: string;
}

/**
 * 按鈕組 Props
 */
export interface ButtonGroupProps extends BaseComponentProps {
  orientation?: 'horizontal' | 'vertical';
  size?: Size;
  variant?: ButtonVariant;
  spacing?: number;
  attached?: boolean;
}

// ============================================================================
// 輸入組件類型
// ============================================================================

/**
 * 輸入框 Props
 */
export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'>, BaseComponentProps {
  size?: Size;
  variant?: 'outline' | 'filled' | 'flushed' | 'unstyled';
  error?: boolean;
  errorMessage?: string;
  helperText?: string;
  label?: string;
  required?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  leftElement?: ReactNode;
  rightElement?: ReactNode;
}

/**
 * 文本區域 Props
 */
export interface TextareaProps extends BaseComponentProps {
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  rows?: number;
  cols?: number;
  resize?: 'none' | 'both' | 'horizontal' | 'vertical';
  error?: boolean;
  errorMessage?: string;
  helperText?: string;
  label?: string;
  onChange?: (value: string) => void;
  onBlur?: () => void;
  onFocus?: () => void;
}

/**
 * 選擇框選項
 */
export interface SelectOption {
  label: string;
  value: any;
  disabled?: boolean;
  group?: string;
  icon?: ReactNode;
  description?: string;
}

/**
 * 選擇框 Props
 */
export interface SelectProps extends BaseComponentProps {
  options: SelectOption[];
  value?: any;
  defaultValue?: any;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  multiple?: boolean;
  searchable?: boolean;
  clearable?: boolean;
  loading?: boolean;
  error?: boolean;
  errorMessage?: string;
  helperText?: string;
  label?: string;
  size?: Size;
  maxHeight?: number;
  onChange?: (value: any) => void;
  onSearch?: (query: string) => void;
  renderOption?: (option: SelectOption) => ReactNode;
  renderValue?: (value: any) => ReactNode;
}

/**
 * 複選框 Props
 */
export interface CheckboxProps extends BaseComponentProps {
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  required?: boolean;
  indeterminate?: boolean;
  size?: Size;
  label?: string;
  description?: string;
  error?: boolean;
  errorMessage?: string;
  onChange?: (checked: boolean) => void;
}

/**
 * 單選框 Props
 */
export interface RadioProps extends BaseComponentProps {
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  required?: boolean;
  size?: Size;
  label?: string;
  description?: string;
  value?: any;
  name?: string;
  error?: boolean;
  errorMessage?: string;
  onChange?: (value: any) => void;
}

/**
 * 單選框組 Props
 */
export interface RadioGroupProps extends BaseComponentProps {
  value?: any;
  defaultValue?: any;
  name?: string;
  disabled?: boolean;
  required?: boolean;
  orientation?: 'horizontal' | 'vertical';
  size?: Size;
  spacing?: number;
  label?: string;
  description?: string;
  error?: boolean;
  errorMessage?: string;
  onChange?: (value: any) => void;
}

/**
 * 開關 Props
 */
export interface SwitchProps extends BaseComponentProps {
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  required?: boolean;
  size?: Size;
  label?: string;
  description?: string;
  error?: boolean;
  errorMessage?: string;
  onChange?: (checked: boolean) => void;
}

// ============================================================================
// 顯示組件類型
// ============================================================================

/**
 * 卡片 Props
 */
export interface CardProps extends BaseComponentProps {
  variant?: 'outline' | 'filled' | 'elevated';
  size?: Size;
  padding?: number | string;
  header?: ReactNode;
  footer?: ReactNode;
  hoverable?: boolean;
  clickable?: boolean;
  loading?: boolean;
  onClick?: () => void;
}

/**
 * 徽章 Props
 */
export interface BadgeProps extends BaseComponentProps {
  variant?: Variant;
  size?: Size;
  rounded?: boolean;
  dot?: boolean;
  count?: number;
  max?: number;
  showZero?: boolean;
  offset?: [number, number];
}

/**
 * 標籤 Props
 */
export interface TagProps extends BaseComponentProps {
  variant?: Variant;
  size?: Size;
  rounded?: boolean;
  closable?: boolean;
  icon?: ReactNode;
  onClose?: () => void;
}

/**
 * 頭像 Props
 */
export interface AvatarProps extends BaseComponentProps {
  src?: string;
  alt?: string;
  size?: Size | number;
  name?: string;
  fallback?: ReactNode;
  rounded?: boolean;
  border?: boolean;
  loading?: boolean;
  onClick?: () => void;
}

/**
 * 頭像組 Props
 */
export interface AvatarGroupProps extends BaseComponentProps {
  max?: number;
  size?: Size | number;
  spacing?: number;
  rounded?: boolean;
  border?: boolean;
}

/**
 * 進度條 Props
 */
export interface ProgressProps extends BaseComponentProps {
  value?: number;
  max?: number;
  size?: Size;
  variant?: 'linear' | 'circular';
  color?: string;
  striped?: boolean;
  animated?: boolean;
  label?: string;
  showValue?: boolean;
  indeterminate?: boolean;
}

/**
 * 骨架屏 Props
 */
export interface SkeletonProps extends BaseComponentProps {
  width?: number | string;
  height?: number | string;
  variant?: 'text' | 'rectangular' | 'circular';
  animation?: 'pulse' | 'wave' | false;
  lines?: number;
  loading?: boolean;
}

// ============================================================================
// 導航組件類型
// ============================================================================

/**
 * 導航項目
 */
export interface NavItem {
  key: string;
  label: string;
  icon?: ReactNode;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  badge?: number | string;
  children?: NavItem[];
}

/**
 * 導航 Props
 */
export interface NavProps extends BaseComponentProps {
  items: NavItem[];
  activeKey?: string;
  orientation?: 'horizontal' | 'vertical';
  variant?: 'tabs' | 'pills' | 'underline';
  size?: Size;
  onChange?: (key: string) => void;
}

/**
 * 麵包屑項目
 */
export interface BreadcrumbItem {
  key: string;
  label: string;
  href?: string;
  icon?: ReactNode;
  onClick?: () => void;
}

/**
 * 麵包屑 Props
 */
export interface BreadcrumbProps extends BaseComponentProps {
  items: BreadcrumbItem[];
  separator?: ReactNode;
  maxItems?: number;
}

/**
 * 分頁 Props
 */
export interface PaginationProps extends BaseComponentProps {
  current: number;
  total: number;
  pageSize?: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean | ((total: number, range: [number, number]) => ReactNode);
  size?: Size;
  simple?: boolean;
  disabled?: boolean;
  onChange?: (page: number, pageSize?: number) => void;
  onShowSizeChange?: (current: number, size: number) => void;
}

// ============================================================================
// 反饋組件類型
// ============================================================================

/**
 * 警告 Props
 */
export interface AlertProps extends BaseComponentProps {
  type?: NotificationType;
  title?: string;
  description?: string;
  closable?: boolean;
  showIcon?: boolean;
  icon?: ReactNode;
  action?: ReactNode;
  onClose?: () => void;
}

/**
 * 通知 Props
 */
export interface NotificationProps extends BaseComponentProps {
  type?: NotificationType;
  title: string;
  description?: string;
  duration?: number;
  closable?: boolean;
  showIcon?: boolean;
  icon?: ReactNode;
  action?: ReactNode;
  placement?: 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight';
  onClose?: () => void;
}

/**
 * 模態框 Props
 */
export interface ModalProps extends BaseComponentProps {
  open?: boolean;
  title?: ReactNode;
  size?: Size | 'full';
  centered?: boolean;
  closable?: boolean;
  maskClosable?: boolean;
  keyboard?: boolean;
  footer?: ReactNode;
  confirmLoading?: boolean;
  destroyOnClose?: boolean;
  zIndex?: number;
  onOk?: () => void | Promise<void>;
  onCancel?: () => void;
  afterClose?: () => void;
}

/**
 * 抽屜 Props
 */
export interface DrawerProps extends BaseComponentProps {
  open?: boolean;
  title?: ReactNode;
  placement?: 'top' | 'right' | 'bottom' | 'left';
  size?: Size | number;
  closable?: boolean;
  maskClosable?: boolean;
  keyboard?: boolean;
  footer?: ReactNode;
  destroyOnClose?: boolean;
  zIndex?: number;
  onClose?: () => void;
  afterClose?: () => void;
}

/**
 * 工具提示 Props
 */
export interface TooltipProps extends BaseComponentProps {
  title: ReactNode;
  placement?: Position;
  trigger?: 'hover' | 'focus' | 'click' | 'contextMenu';
  visible?: boolean;
  defaultVisible?: boolean;
  delay?: number;
  mouseEnterDelay?: number;
  mouseLeaveDelay?: number;
  overlayClassName?: string;
  overlayStyle?: CSSProperties;
  onVisibleChange?: (visible: boolean) => void;
}

/**
 * 氣泡確認 Props
 */
export interface PopconfirmProps extends TooltipProps {
  title: ReactNode;
  description?: ReactNode;
  okText?: string;
  cancelText?: string;
  okType?: ButtonVariant;
  icon?: ReactNode;
  disabled?: boolean;
  onConfirm?: () => void | Promise<void>;
  onCancel?: () => void;
}

// ============================================================================
// 表格組件類型
// ============================================================================

/**
 * 表格 Props
 */
export interface TableProps<T = any> extends BaseComponentProps {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  size?: Size;
  bordered?: boolean;
  striped?: boolean;
  hoverable?: boolean;
  sticky?: boolean;
  virtual?: boolean;
  rowKey?: keyof T | ((record: T) => string);
  rowSelection?: TableSelection<T>;
  expandable?: {
    expandedRowKeys?: string[];
    defaultExpandedRowKeys?: string[];
    expandedRowRender?: (record: T, index: number) => ReactNode;
    onExpand?: (expanded: boolean, record: T) => void;
    onExpandedRowsChange?: (expandedKeys: string[]) => void;
  };
  pagination?: false | PaginationProps;
  scroll?: {
    x?: number | string;
    y?: number | string;
  };
  sortable?: boolean;
  filterable?: boolean;
  resizable?: boolean;
  onRow?: (record: T, index: number) => HTMLAttributes<HTMLTableRowElement>;
  onHeaderRow?: (columns: TableColumn<T>[], index: number) => HTMLAttributes<HTMLTableRowElement>;
  onSort?: (sort: TableSort) => void;
  onFilter?: (filters: TableFilter[]) => void;
  onResize?: (width: number, column: TableColumn<T>) => void;
}

// ============================================================================
// 表單組件類型
// ============================================================================

/**
 * 表單 Props
 */
export interface FormProps extends BaseComponentProps {
  fields: FormField[];
  values?: Record<string, any>;
  errors?: FormError[];
  loading?: boolean;
  disabled?: boolean;
  layout?: 'horizontal' | 'vertical' | 'inline';
  labelWidth?: number | string;
  size?: Size;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  onSubmit?: (values: Record<string, any>) => void | Promise<void>;
  onChange?: (values: Record<string, any>) => void;
  onValidate?: (errors: FormError[]) => void;
}

/**
 * 表單項目 Props
 */
export interface FormItemProps extends BaseComponentProps {
  field: FormField;
  value?: any;
  error?: FormError;
  disabled?: boolean;
  layout?: 'horizontal' | 'vertical';
  labelWidth?: number | string;
  size?: Size;
  onChange?: (value: any) => void;
  onBlur?: () => void;
  onFocus?: () => void;
}

// ============================================================================
// 佈局組件類型
// ============================================================================

/**
 * 容器 Props
 */
export interface ContainerProps extends BaseComponentProps {
  maxWidth?: Size | number | string;
  centered?: boolean;
  fluid?: boolean;
  padding?: number | string;
}

/**
 * 網格 Props
 */
export interface GridProps extends BaseComponentProps {
  container?: boolean;
  item?: boolean;
  spacing?: number;
  columns?: number;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
  direction?: 'row' | 'column';
  justify?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly';
  align?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
  wrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
}

/**
 * 堆疊 Props
 */
export interface StackProps extends BaseComponentProps {
  direction?: 'row' | 'column';
  spacing?: number;
  align?: Alignment;
  justify?: 'start' | 'center' | 'end' | 'space-between' | 'space-around' | 'space-evenly';
  wrap?: boolean;
  divider?: ReactNode;
}

/**
 * 分隔器 Props
 */
export interface DividerProps extends BaseComponentProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'dotted';
  thickness?: number;
  spacing?: number;
  color?: string;
  label?: ReactNode;
  labelPosition?: 'left' | 'center' | 'right';
}

// ============================================================================
// 專案特定組件類型
// ============================================================================

/**
 * 代理卡片 Props
 */
export interface ProxyCardProps extends BaseComponentProps {
  proxy: ProxyNode;
  selected?: boolean;
  actions?: ReactNode;
  onSelect?: (proxy: ProxyNode) => void;
  onTest?: (proxy: ProxyNode) => void;
  onEdit?: (proxy: ProxyNode) => void;
  onDelete?: (proxy: ProxyNode) => void;
}

/**
 * 代理列表 Props
 */
export interface ProxyListProps extends BaseComponentProps {
  proxies: ProxyNode[];
  loading?: boolean;
  selection?: TableSelection<ProxyNode>;
  onRefresh?: () => void;
  onTest?: (proxies: ProxyNode[]) => void;
  onExport?: (proxies: ProxyNode[]) => void;
  onDelete?: (proxies: ProxyNode[]) => void;
}

/**
 * 任務卡片 Props
 */
export interface TaskCardProps extends BaseComponentProps {
  task: Task;
  actions?: ReactNode;
  onStart?: (task: Task) => void;
  onStop?: (task: Task) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (task: Task) => void;
  onViewLogs?: (task: Task) => void;
}

/**
 * 任務列表 Props
 */
export interface TaskListProps extends BaseComponentProps {
  tasks: Task[];
  loading?: boolean;
  onRefresh?: () => void;
  onCreate?: () => void;
}

/**
 * 狀態指示器 Props
 */
export interface StatusIndicatorProps extends BaseComponentProps {
  status: 'online' | 'offline' | 'unknown' | 'running' | 'stopped' | 'error';
  size?: Size;
  showText?: boolean;
  text?: string;
  animated?: boolean;
}

/**
 * 統計卡片 Props
 */
export interface StatCardProps extends BaseComponentProps {
  title: string;
  value: number | string;
  unit?: string;
  change?: number;
  changeType?: 'increase' | 'decrease';
  icon?: ReactNode;
  color?: string;
  loading?: boolean;
  onClick?: () => void;
}

/**
 * 圖表 Props
 */
export interface ChartProps extends BaseComponentProps {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area';
  data: any;
  options?: any;
  width?: number | string;
  height?: number | string;
  loading?: boolean;
  error?: string;
  onDataPointClick?: (point: any) => void;
}

/**
 * 搜索框 Props
 */
export interface SearchBoxProps extends BaseComponentProps {
  value?: string;
  placeholder?: string;
  size?: Size;
  loading?: boolean;
  clearable?: boolean;
  suggestions?: string[];
  onSearch?: (query: string) => void;
  onChange?: (value: string) => void;
  onClear?: () => void;
  onSuggestionSelect?: (suggestion: string) => void;
}

/**
 * 篩選器 Props
 */
export interface FilterProps extends BaseComponentProps {
  filters: {
    key: string;
    label: string;
    type: 'text' | 'select' | 'date' | 'range';
    options?: SelectOption[];
    value?: any;
  }[];
  values?: Record<string, any>;
  onFilter?: (filters: Record<string, any>) => void;
  onReset?: () => void;
}

/**
 * 主題切換器 Props
 */
export interface ThemeSwitcherProps extends BaseComponentProps {
  theme?: ThemeMode;
  size?: Size;
  showLabel?: boolean;
  onChange?: (theme: ThemeMode) => void;
}

/**
 * 語言切換器 Props
 */
export interface LanguageSwitcherProps extends BaseComponentProps {
  language?: string;
  languages: {
    code: string;
    name: string;
    flag?: string;
  }[];
  size?: Size;
  showFlag?: boolean;
  onChange?: (language: string) => void;
}