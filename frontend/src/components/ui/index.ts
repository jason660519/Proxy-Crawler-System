/**
 * UI 組件統一導出
 * 提供所有基礎UI組件的統一入口
 */

// 基礎組件
export { Button } from './Button';
export type { ButtonProps } from './Button';

export { Input } from './Input';
export type { InputProps } from './Input';

export { Card, CardHeader, CardContent, CardFooter } from './Card';
export type { CardProps, CardHeaderProps, CardContentProps, CardFooterProps } from './Card';

export { Modal } from './Modal';
export type { ModalProps } from './Modal';

export { default as Select } from './Select';
export type { SelectProps, SelectOption } from './Select';

export { TextArea } from './TextArea';
export type { TextAreaProps } from './TextArea';

export { Switch } from './Switch';
export type { SwitchProps } from './Switch';

export { Checkbox } from './Checkbox';
export type { CheckboxProps } from './Checkbox';

export { Tooltip } from './Tooltip';
export type { TooltipProps } from './Tooltip';

export { Badge } from './Badge';
export type { BadgeProps } from './Badge';

export { Spinner } from './Spinner';
export type { SpinnerProps } from './Spinner';

export { Progress } from './Progress';
export type { ProgressProps } from './Progress';

export { Icon } from './Icon';
export type { IconProps, IconName } from './Icon';

// 新增組件
export { DataTable } from './DataTable';
export type { DataTableProps, DataTableColumn } from './DataTable';

export { 
  StatusIndicator,
  SuccessStatus,
  WarningStatus,
  ErrorStatus,
  InfoStatus,
  PendingStatus,
  ActiveStatus
} from './StatusIndicator';
export type { StatusIndicatorProps, StatusType, StatusSize, StatusVariant } from './StatusIndicator';

// 重新導出預設組件
export { default as ButtonDefault } from './Button';
export { default as InputDefault } from './Input';
export { default as CardDefault } from './Card';