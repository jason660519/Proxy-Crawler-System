/**
 * Icon 組件
 * 將字符串圖標名稱映射到 lucide-react 圖標組件
 */

import React from 'react';
import {
  BarChart3,
  Settings,
  Activity,
  List,
  FileText,
  TrendingUp,
  RefreshCw,
  Search,
  Wifi,
  WifiOff,
  CheckCircle,

  XCircle,
  Clock,
  Server,
  Database,
  Globe,
  Shield,
  Eye,
  EyeOff,
  Download,
  Upload,
  Play,
  Pause,
  RotateCcw,
  Filter,
  SortAsc,
  MoreHorizontal,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Plus,
  Minus,
  X,

  Info,
  AlertTriangle,
  HelpCircle,
  Home,
  Users,
  Mail,
  Phone,
  Calendar,
  MapPin,
  Link,
  ExternalLink,
  Copy,
  Edit,
  Trash2,
  Save,
  Archive,
  Star,
  Heart,
  Bookmark,
  Share,
  MessageSquare,
  Bell,
  User,
  Lock,
  Unlock,
  LogIn,
  LogOut,
  Menu,
  Grid,
  Layout,
  Sun,
  Moon,
  Monitor,
  Power,
  Tag,
  Package,
  Box,
  Layers,
  Target,
  Flag,
  Shuffle,
  File,
  Folder
} from 'lucide-react';

// 圖標映射表
const iconMap = {
  // 導航和佈局
  dashboard: BarChart3,
  settings: Settings,
  home: Home,
  menu: Menu,
  grid: Grid,
  layout: Layout,
  
  // 代理相關
  proxy: Globe,
  proxies: Server,
  network: Wifi,
  shield: Shield,
  
  // 任務和處理
  tasks: List,
  task: CheckCircle,
  queue: Clock,
  processing: RefreshCw,
  
  // 日誌和監控
  logs: FileText,
  log: File,
  monitor: Activity,
  analytics: TrendingUp,
  
  // 系統和設置
  config: Settings,
  system: Server,
  database: Database,
  
  // 轉換工具
  convert: RefreshCw,
  transform: Shuffle,
  
  // 狀態指示
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  info: Info,
  pending: Clock,
  
  // 操作
  search: Search,
  filter: Filter,
  sort: SortAsc,
  edit: Edit,
  delete: Trash2,
  save: Save,
  copy: Copy,
  share: Share,
  download: Download,
  upload: Upload,
  
  // 播放控制
  play: Play,
  pause: Pause,
  refresh: RotateCcw,
  
  // 方向
  up: ChevronUp,
  down: ChevronDown,
  left: ChevronLeft,
  right: ChevronRight,
  
  // 添加/移除
  plus: Plus,
  add: Plus,
  minus: Minus,
  remove: Minus,
  close: X,
  
  // 用戶和認證
  user: User,
  users: Users,
  login: LogIn,
  logout: LogOut,
  lock: Lock,
  unlock: Unlock,
  
  // 通信
  mail: Mail,
  message: MessageSquare,
  phone: Phone,
  notification: Bell,
  
  // 文件和文件夾
  file: File,
  folder: Folder,
  archive: Archive,
  
  // 主題
  sun: Sun,
  moon: Moon,
  theme: Monitor,
  
  // 連接狀態
  connected: Wifi,
  disconnected: WifiOff,
  connecting: RefreshCw,
  
  // 其他常用
  star: Star,
  heart: Heart,
  bookmark: Bookmark,
  link: Link,
  external: ExternalLink,
  calendar: Calendar,
  clock: Clock,
  location: MapPin,
  target: Target,
  flag: Flag,
  tag: Tag,
  package: Package,
  box: Box,
  layers: Layers,
  eye: Eye,
  eyeOff: EyeOff,
  power: Power,
  help: HelpCircle,
  more: MoreHorizontal
} as const;

// 圖標名稱類型
export type IconName = keyof typeof iconMap;

// 圖標組件屬性
export interface IconProps {
  /** 圖標名稱 */
  name: IconName | string;
  /** 圖標大小 */
  size?: number | string;
  /** 圖標顏色 */
  color?: string;
  /** 自定義類名 */
  className?: string;
  /** 自定義樣式 */
  style?: React.CSSProperties;
  /** 點擊事件 */
  onClick?: () => void;
}

/**
 * Icon 組件
 * 根據名稱渲染對應的 lucide-react 圖標
 */
export const Icon: React.FC<IconProps> = ({
  name,
  size = 20,
  color = 'currentColor',
  className,
  style,
  onClick
}) => {
  // 獲取對應的圖標組件
  const IconComponent = iconMap[name as IconName];
  
  // 如果找不到對應的圖標，返回默認圖標或null
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in iconMap`);
    return <HelpCircle size={size} color={color} className={className} style={style} onClick={onClick} />;
  }
  
  return (
    <IconComponent
      size={size}
      color={color}
      className={className}
      style={style}
      onClick={onClick}
    />
  );
};

export default Icon;