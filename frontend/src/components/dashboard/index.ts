/**
 * 儀表板組件索引
 * 統一導出所有儀表板相關組件
 */

export { Dashboard } from './Dashboard';
export { OperationsDashboard } from './OperationsDashboard';
export { MetricsOverview } from './MetricsOverview';
export { HealthCard } from './HealthCard';
export { TrendChart } from './TrendChart';
export { TaskBoard } from './TaskBoard';
export { LogViewer } from './LogViewer';
export { Settings } from '../settings/Settings';

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