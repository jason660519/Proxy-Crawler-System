/**
 * 儀表板組件索引
 * 統一導出所有儀表板相關組件
 */

export { default as Dashboard } from './Dashboard';
export { default as OperationsDashboard } from './OperationsDashboard';
export { default as MetricsOverview } from './MetricsOverview';
export { default as HealthCard } from './HealthCard';
export { default as TrendChart } from './TrendChart';
export { default as TaskBoard } from './TaskBoard';
export { default as LogViewer } from './LogViewer';
// Settings 組件應該從 settings 目錄單獨導入

// 類型導出
export type { 
  HealthCardProps,
  HealthMetric 
} from './HealthCard';

export type {
  TrendChartProps,
  ChartDataPoint,
  ChartMetric
} from './TrendChart';

export type {
  TaskBoardProps,
  TaskItemProps
} from './TaskBoard';

export type {
  LogViewerProps
} from './LogViewer';