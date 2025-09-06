import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 條件式類名合併工具函數
 * 結合 clsx 和 tailwind-merge 的功能
 * 
 * @param inputs 類名輸入值（可以是字串、物件、陣列等）
 * @returns 合併後的類名字串
 * 
 * @example
 * ```tsx
 * // 基本使用
 * cn('px-2 py-1', 'text-sm') // 'px-2 py-1 text-sm'
 * 
 * // 條件式類名
 * cn('base-class', {
 *   'active-class': isActive,
 *   'disabled-class': isDisabled
 * })
 * 
 * // Tailwind 類名衝突解決
 * cn('px-2 py-1', 'px-4') // 'py-1 px-4' (px-2 被 px-4 覆蓋)
 * 
 * // 複雜條件
 * cn(
 *   'btn',
 *   variant === 'primary' && 'btn-primary',
 *   variant === 'secondary' && 'btn-secondary',
 *   size === 'lg' && 'btn-lg',
 *   disabled && 'btn-disabled'
 * )
 * ```
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * 條件式類名工具函數集合
 */
export const classNames = {
  /**
   * 根據條件返回類名
   * @param condition 條件
   * @param trueClass 條件為真時的類名
   * @param falseClass 條件為假時的類名
   */
  conditional: (condition: boolean, trueClass: string, falseClass?: string): string => {
    return condition ? trueClass : (falseClass || '');
  },

  /**
   * 根據變體返回對應的類名
   * @param variant 變體值
   * @param variants 變體映射物件
   * @param defaultClass 預設類名
   */
  variant: <T extends string>(
    variant: T,
    variants: Record<T, string>,
    defaultClass?: string
  ): string => {
    return variants[variant] || defaultClass || '';
  },

  /**
   * 根據大小返回對應的類名
   * @param size 大小值
   * @param sizes 大小映射物件
   */
  size: <T extends string>(size: T, sizes: Record<T, string>): string => {
    return sizes[size] || '';
  },

  /**
   * 根據狀態返回對應的類名
   * @param state 狀態值
   * @param states 狀態映射物件
   */
  state: <T extends string>(state: T, states: Record<T, string>): string => {
    return states[state] || '';
  },

  /**
   * 組合多個類名映射
   * @param mappings 類名映射陣列
   */
  combine: (...mappings: (string | undefined | null | false)[]): string => {
    return cn(...mappings.filter(Boolean));
  },
};

/**
 * 常用的 VS Code 風格類名組合
 */
export const vscodeClasses = {
  // 背景色
  bg: {
    primary: 'bg-vscode-bg',
    secondary: 'bg-vscode-panel-bg',
    sidebar: 'bg-vscode-sidebar-bg',
    activitybar: 'bg-vscode-activitybar-bg',
    editor: 'bg-vscode-editor-bg',
    statusbar: 'bg-vscode-statusbar-bg',
    hover: 'hover:bg-vscode-list-hover-bg',
    active: 'bg-vscode-list-active-bg',
  },

  // 文字色
  text: {
    primary: 'text-vscode-foreground',
    secondary: 'text-vscode-foreground/70',
    muted: 'text-vscode-foreground/50',
    inverse: 'text-vscode-bg',
  },

  // 邊框
  border: {
    default: 'border-vscode-border',
    panel: 'border-vscode-panel-border',
    input: 'border-vscode-input-border',
  },

  // 按鈕
  button: {
    primary: 'bg-vscode-button-bg hover:bg-vscode-button-hover-bg text-white',
    secondary: 'bg-vscode-panel-bg hover:bg-vscode-list-hover-bg text-vscode-foreground border border-vscode-border',
    ghost: 'hover:bg-vscode-list-hover-bg text-vscode-foreground',
    outline: 'border border-vscode-button-bg text-vscode-button-bg hover:bg-vscode-button-bg hover:text-white',
  },

  // 輸入框
  input: {
    default: 'bg-vscode-input-bg border-vscode-input-border text-vscode-foreground placeholder-vscode-foreground/50',
    focus: 'focus:ring-2 focus:ring-vscode-button-bg focus:border-vscode-button-bg',
    error: 'border-proxy-offline focus:ring-proxy-offline',
    success: 'border-proxy-online focus:ring-proxy-online',
  },

  // 卡片
  card: {
    default: 'bg-vscode-panel-bg border border-vscode-border rounded-lg',
    hover: 'hover:bg-vscode-list-hover-bg transition-colors',
    active: 'bg-vscode-list-active-bg',
  },

  // 標籤頁
  tab: {
    active: 'bg-vscode-tab-active-bg text-vscode-foreground border-b-2 border-vscode-button-bg',
    inactive: 'bg-vscode-tab-inactive-bg text-vscode-foreground/70 hover:text-vscode-foreground',
  },

  // 滾動條
  scrollbar: {
    default: 'scrollbar-thin scrollbar-track-vscode-panel-bg scrollbar-thumb-vscode-border hover:scrollbar-thumb-vscode-foreground/30',
  },
};

/**
 * 代理狀態相關的類名
 */
export const proxyClasses = {
  status: {
    online: 'text-proxy-online bg-proxy-online/10 border-proxy-online/20',
    offline: 'text-proxy-offline bg-proxy-offline/10 border-proxy-offline/20',
    slow: 'text-proxy-slow bg-proxy-slow/10 border-proxy-slow/20',
    unknown: 'text-vscode-foreground/50 bg-vscode-foreground/5 border-vscode-foreground/10',
  },

  speed: {
    fast: 'text-proxy-online',
    medium: 'text-proxy-slow',
    slow: 'text-proxy-offline',
  },

  anonymity: {
    elite: 'text-proxy-online',
    anonymous: 'text-proxy-slow',
    transparent: 'text-proxy-offline',
  },
};

/**
 * 響應式設計相關的類名工具
 */
export const responsiveClasses = {
  /**
   * 根據斷點隱藏/顯示元素
   */
  visibility: {
    mobileOnly: 'block md:hidden',
    tabletOnly: 'hidden md:block lg:hidden',
    desktopOnly: 'hidden lg:block',
    mobileAndTablet: 'block lg:hidden',
    tabletAndDesktop: 'hidden md:block',
  },

  /**
   * 響應式網格
   */
  grid: {
    responsive: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
    autoFit: 'grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))]',
    autoFill: 'grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))]',
  },

  /**
   * 響應式間距
   */
  spacing: {
    padding: 'p-4 md:p-6 lg:p-8',
    margin: 'm-4 md:m-6 lg:m-8',
    gap: 'gap-4 md:gap-6 lg:gap-8',
  },

  /**
   * 響應式文字大小
   */
  text: {
    heading: 'text-xl md:text-2xl lg:text-3xl',
    subheading: 'text-lg md:text-xl lg:text-2xl',
    body: 'text-sm md:text-base lg:text-lg',
  },
};

/**
 * 動畫相關的類名
 */
export const animationClasses = {
  transition: {
    default: 'transition-all duration-200 ease-in-out',
    fast: 'transition-all duration-150 ease-in-out',
    slow: 'transition-all duration-300 ease-in-out',
    colors: 'transition-colors duration-200 ease-in-out',
    transform: 'transition-transform duration-200 ease-in-out',
  },

  hover: {
    scale: 'hover:scale-105 transition-transform duration-200',
    lift: 'hover:-translate-y-1 hover:shadow-lg transition-all duration-200',
    glow: 'hover:shadow-lg hover:shadow-vscode-button-bg/25 transition-shadow duration-200',
  },

  focus: {
    ring: 'focus:outline-none focus:ring-2 focus:ring-vscode-button-bg focus:ring-offset-2',
    glow: 'focus:outline-none focus:shadow-lg focus:shadow-vscode-button-bg/25',
  },

  loading: {
    spin: 'animate-spin',
    pulse: 'animate-pulse',
    bounce: 'animate-bounce',
    ping: 'animate-ping',
  },
};

/**
 * 工具類名組合函數
 */
export const utils = {
  /**
   * 建立按鈕類名
   */
  button: ({
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    className,
  }: {
    variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    className?: string;
  } = {}) => {
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    return cn(
      'inline-flex items-center justify-center font-medium rounded transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-vscode-button-bg focus:ring-offset-2',
      sizeClasses[size],
      vscodeClasses.button[variant],
      {
        'opacity-50 cursor-not-allowed': disabled || loading,
        'cursor-wait': loading,
      },
      className
    );
  },

  /**
   * 建立輸入框類名
   */
  input: ({
    variant = 'default',
    size = 'md',
    error = false,
    className,
  }: {
    variant?: 'default' | 'error' | 'success';
    size?: 'sm' | 'md' | 'lg';
    error?: boolean;
    className?: string;
  } = {}) => {
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-4 py-3 text-lg',
    };

    const variantClasses = {
      default: vscodeClasses.input.default,
      error: vscodeClasses.input.error,
      success: vscodeClasses.input.success,
    };

    return cn(
      'w-full rounded border transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      sizeClasses[size],
      error ? variantClasses.error : variantClasses[variant],
      vscodeClasses.input.focus,
      className
    );
  },

  /**
   * 建立卡片類名
   */
  card: ({
    variant = 'default',
    hover = false,
    active = false,
    className,
  }: {
    variant?: 'default' | 'elevated';
    hover?: boolean;
    active?: boolean;
    className?: string;
  } = {}) => {
    return cn(
      vscodeClasses.card.default,
      {
        'shadow-lg': variant === 'elevated',
        [vscodeClasses.card.hover]: hover,
        [vscodeClasses.card.active]: active,
      },
      className
    );
  },
};