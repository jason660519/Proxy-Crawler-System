import React from 'react';
import { Loader2, RefreshCw, Circle } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * 載入動畫的類型
 */
export type SpinnerType = 'default' | 'dots' | 'pulse' | 'bounce' | 'ring' | 'bars';

/**
 * 載入動畫的大小
 */
export type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * LoadingSpinner 組件的 Props
 */
interface LoadingSpinnerProps {
  /** 動畫類型 */
  type?: SpinnerType;
  /** 大小 */
  size?: SpinnerSize;
  /** 自定義類名 */
  className?: string;
  /** 載入文字 */
  text?: string;
  /** 是否顯示文字 */
  showText?: boolean;
  /** 文字位置 */
  textPosition?: 'bottom' | 'right';
  /** 顏色主題 */
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  /** 是否全屏顯示 */
  fullScreen?: boolean;
  /** 背景遮罩透明度 */
  overlayOpacity?: number;
}

/**
 * 大小對應的CSS類名映射
 */
const sizeClasses: Record<SpinnerSize, string> = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

/**
 * 文字大小對應的CSS類名映射
 */
const textSizeClasses: Record<SpinnerSize, string> = {
  xs: 'text-xs',
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl',
};

/**
 * 顏色變體對應的CSS類名映射
 */
const variantClasses: Record<string, string> = {
  primary: 'text-vscode-button-bg',
  secondary: 'text-vscode-foreground/70',
  success: 'text-proxy-online',
  warning: 'text-proxy-slow',
  error: 'text-proxy-offline',
};

/**
 * 預設載入動畫組件（旋轉圓圈）
 */
const DefaultSpinner: React.FC<{ className: string }> = ({ className }) => (
  <Loader2 className={cn('animate-spin', className)} />
);

/**
 * 點狀載入動畫
 */
const DotsSpinner: React.FC<{ className: string }> = ({ className }) => (
  <div className={cn('flex space-x-1', className)}>
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        className="w-2 h-2 bg-current rounded-full animate-bounce"
        style={{
          animationDelay: `${i * 0.1}s`,
          animationDuration: '0.6s',
        }}
      />
    ))}
  </div>
);

/**
 * 脈衝載入動畫
 */
const PulseSpinner: React.FC<{ className: string }> = ({ className }) => (
  <div className={cn('relative', className)}>
    <div className="w-full h-full bg-current rounded-full animate-ping opacity-75" />
    <div className="absolute inset-0 w-full h-full bg-current rounded-full animate-pulse" />
  </div>
);

/**
 * 彈跳載入動畫
 */
const BounceSpinner: React.FC<{ className: string }> = ({ className }) => (
  <div className={cn('flex space-x-1', className)}>
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        className="w-3 h-3 bg-current rounded-full animate-bounce"
        style={{
          animationDelay: `${i * 0.15}s`,
        }}
      />
    ))}
  </div>
);

/**
 * 環形載入動畫
 */
const RingSpinner: React.FC<{ className: string }> = ({ className }) => (
  <div className={cn('relative', className)}>
    <div className="absolute inset-0 border-2 border-current border-opacity-20 rounded-full" />
    <div className="absolute inset-0 border-2 border-transparent border-t-current rounded-full animate-spin" />
  </div>
);

/**
 * 條狀載入動畫
 */
const BarsSpinner: React.FC<{ className: string }> = ({ className }) => (
  <div className={cn('flex space-x-1 items-end', className)}>
    {[0, 1, 2, 3].map((i) => (
      <div
        key={i}
        className="w-1 bg-current animate-pulse"
        style={{
          height: `${20 + (i % 2) * 10}px`,
          animationDelay: `${i * 0.1}s`,
          animationDuration: '1s',
        }}
      />
    ))}
  </div>
);

/**
 * 載入動畫組件映射
 */
const spinnerComponents: Record<SpinnerType, React.FC<{ className: string }>> = {
  default: DefaultSpinner,
  dots: DotsSpinner,
  pulse: PulseSpinner,
  bounce: BounceSpinner,
  ring: RingSpinner,
  bars: BarsSpinner,
};

/**
 * 載入動畫組件
 * 提供多種載入動畫效果和自定義選項
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  type = 'default',
  size = 'md',
  className,
  text,
  showText = false,
  textPosition = 'bottom',
  variant = 'primary',
  fullScreen = false,
  overlayOpacity = 0.5,
}) => {
  const SpinnerComponent = spinnerComponents[type];
  const sizeClass = sizeClasses[size];
  const textSizeClass = textSizeClasses[size];
  const variantClass = variantClasses[variant];

  // 載入動畫元素
  const spinnerElement = (
    <SpinnerComponent
      className={cn(
        sizeClass,
        variantClass,
        className
      )}
    />
  );

  // 文字元素
  const textElement = (showText || text) && (
    <span className={cn(
      textSizeClass,
      variantClass,
      'font-medium',
      textPosition === 'right' ? 'ml-2' : 'mt-2'
    )}>
      {text || '載入中...'}
    </span>
  );

  // 載入內容容器
  const loadingContent = (
    <div className={cn(
      'flex items-center justify-center',
      textPosition === 'bottom' ? 'flex-col' : 'flex-row',
      !fullScreen && 'inline-flex'
    )}>
      {spinnerElement}
      {textElement}
    </div>
  );

  // 如果是全屏模式
  if (fullScreen) {
    return (
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{
          backgroundColor: `rgba(0, 0, 0, ${overlayOpacity})`,
        }}
      >
        <div className="bg-vscode-panel-bg border border-vscode-border rounded-lg p-6 shadow-lg">
          {loadingContent}
        </div>
      </div>
    );
  }

  return loadingContent;
};

/**
 * 載入覆蓋層組件
 * 在現有內容上顯示載入動畫
 */
interface LoadingOverlayProps extends LoadingSpinnerProps {
  /** 是否顯示覆蓋層 */
  show: boolean;
  /** 子組件 */
  children: React.ReactNode;
  /** 覆蓋層背景色 */
  overlayColor?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  show,
  children,
  overlayColor = 'bg-vscode-bg/80',
  overlayOpacity = 0.8,
  ...spinnerProps
}) => {
  return (
    <div className="relative">
      {children}
      {show && (
        <div className={cn(
          'absolute inset-0 flex items-center justify-center z-10',
          overlayColor
        )}>
          <LoadingSpinner {...spinnerProps} />
        </div>
      )}
    </div>
  );
};

/**
 * 載入按鈕組件
 * 帶有載入狀態的按鈕
 */
interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** 是否處於載入狀態 */
  loading?: boolean;
  /** 載入文字 */
  loadingText?: string;
  /** 載入動畫類型 */
  spinnerType?: SpinnerType;
  /** 載入動畫大小 */
  spinnerSize?: SpinnerSize;
  /** 按鈕變體 */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  /** 按鈕大小 */
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  loading = false,
  loadingText,
  spinnerType = 'default',
  spinnerSize = 'sm',
  variant = 'primary',
  size = 'md',
  children,
  disabled,
  className,
  ...props
}) => {
  const buttonSizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const buttonVariantClasses = {
    primary: 'bg-vscode-button-bg hover:bg-vscode-button-hover-bg text-white',
    secondary: 'bg-vscode-panel-bg hover:bg-vscode-list-hover-bg text-vscode-foreground border border-vscode-border',
    outline: 'border border-vscode-button-bg text-vscode-button-bg hover:bg-vscode-button-bg hover:text-white',
    ghost: 'text-vscode-button-bg hover:bg-vscode-button-bg/10',
  };

  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center font-medium rounded transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-vscode-button-bg focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        buttonSizeClasses[size],
        buttonVariantClasses[variant],
        className
      )}
    >
      {loading && (
        <LoadingSpinner
          type={spinnerType}
          size={spinnerSize}
          variant="secondary"
          className="mr-2"
        />
      )}
      {loading ? (loadingText || '載入中...') : children}
    </button>
  );
};

/**
 * 載入卡片組件
 * 顯示載入狀態的卡片容器
 */
interface LoadingCardProps {
  /** 是否處於載入狀態 */
  loading: boolean;
  /** 載入文字 */
  loadingText?: string;
  /** 載入動畫類型 */
  spinnerType?: SpinnerType;
  /** 子組件 */
  children: React.ReactNode;
  /** 自定義類名 */
  className?: string;
  /** 最小高度 */
  minHeight?: string;
}

export const LoadingCard: React.FC<LoadingCardProps> = ({
  loading,
  loadingText = '載入中...',
  spinnerType = 'default',
  children,
  className,
  minHeight = '200px',
}) => {
  if (loading) {
    return (
      <div 
        className={cn(
          'flex items-center justify-center bg-vscode-panel-bg border border-vscode-border rounded-lg',
          className
        )}
        style={{ minHeight }}
      >
        <LoadingSpinner
          type={spinnerType}
          size="lg"
          text={loadingText}
          showText
          textPosition="bottom"
        />
      </div>
    );
  }

  return (
    <div className={cn('bg-vscode-panel-bg border border-vscode-border rounded-lg', className)}>
      {children}
    </div>
  );
};

/**
 * 骨架載入組件
 * 顯示內容載入時的骨架屏
 */
interface SkeletonProps {
  /** 寬度 */
  width?: string | number;
  /** 高度 */
  height?: string | number;
  /** 是否為圓形 */
  circle?: boolean;
  /** 自定義類名 */
  className?: string;
  /** 動畫類型 */
  animation?: 'pulse' | 'wave' | 'none';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height = '1rem',
  circle = false,
  className,
  animation = 'pulse',
}) => {
  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-wave',
    none: '',
  };

  return (
    <div
      className={cn(
        'bg-vscode-list-hover-bg',
        circle ? 'rounded-full' : 'rounded',
        animationClasses[animation],
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  );
};

/**
 * 文字骨架組件
 */
interface TextSkeletonProps {
  /** 行數 */
  lines?: number;
  /** 最後一行的寬度百分比 */
  lastLineWidth?: number;
  /** 行間距 */
  lineHeight?: string;
  /** 自定義類名 */
  className?: string;
}

export const TextSkeleton: React.FC<TextSkeletonProps> = ({
  lines = 3,
  lastLineWidth = 60,
  lineHeight = '1rem',
  className,
}) => {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }, (_, index) => (
        <Skeleton
          key={index}
          height={lineHeight}
          width={index === lines - 1 ? `${lastLineWidth}%` : '100%'}
        />
      ))}
    </div>
  );
};