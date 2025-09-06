import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

/**
 * 錯誤邊界組件的 Props 介面
 */
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  resetOnPropsChange?: boolean;
  resetKeys?: Array<string | number>;
}

/**
 * 錯誤邊界組件的 State 介面
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  eventId: string | null;
}

/**
 * 錯誤詳情組件的 Props
 */
interface ErrorDetailsProps {
  error: Error;
  errorInfo: ErrorInfo;
  onToggle: () => void;
  isExpanded: boolean;
}

/**
 * 錯誤詳情組件
 * 顯示詳細的錯誤資訊和堆疊追蹤
 */
const ErrorDetails: React.FC<ErrorDetailsProps> = ({ error, errorInfo, onToggle, isExpanded }) => {
  const copyToClipboard = async () => {
    const errorText = `
錯誤訊息: ${error.message}
錯誤名稱: ${error.name}
錯誤堆疊:
${error.stack}

組件堆疊:
${errorInfo.componentStack}

時間: ${new Date().toISOString()}
用戶代理: ${navigator.userAgent}
    `.trim();

    try {
      await navigator.clipboard.writeText(errorText);
      // TODO: 顯示複製成功的提示
    } catch (err) {
      console.error('複製到剪貼板失敗:', err);
    }
  };

  return (
    <div className="mt-6 border border-vscode-border rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 bg-vscode-panel-bg hover:bg-vscode-list-hover-bg 
                   text-left text-sm font-medium text-vscode-foreground 
                   flex items-center justify-between transition-colors"
      >
        <span className="flex items-center gap-2">
          <Bug className="w-4 h-4" />
          錯誤詳情
        </span>
        <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      
      {isExpanded && (
        <div className="p-4 bg-vscode-editor-bg border-t border-vscode-border">
          <div className="space-y-4">
            {/* 錯誤訊息 */}
            <div>
              <h4 className="text-sm font-semibold text-vscode-foreground mb-2">錯誤訊息</h4>
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm font-mono">
                {error.message}
              </div>
            </div>
            
            {/* 錯誤類型 */}
            <div>
              <h4 className="text-sm font-semibold text-vscode-foreground mb-2">錯誤類型</h4>
              <div className="p-2 bg-vscode-input-bg border border-vscode-input-border rounded text-sm font-mono">
                {error.name}
              </div>
            </div>
            
            {/* 堆疊追蹤 */}
            {error.stack && (
              <div>
                <h4 className="text-sm font-semibold text-vscode-foreground mb-2">堆疊追蹤</h4>
                <pre className="p-3 bg-vscode-input-bg border border-vscode-input-border rounded 
                               text-xs font-mono text-vscode-foreground overflow-x-auto max-h-40 overflow-y-auto">
                  {error.stack}
                </pre>
              </div>
            )}
            
            {/* 組件堆疊 */}
            {errorInfo.componentStack && (
              <div>
                <h4 className="text-sm font-semibold text-vscode-foreground mb-2">組件堆疊</h4>
                <pre className="p-3 bg-vscode-input-bg border border-vscode-input-border rounded 
                               text-xs font-mono text-vscode-foreground overflow-x-auto max-h-40 overflow-y-auto">
                  {errorInfo.componentStack}
                </pre>
              </div>
            )}
            
            {/* 操作按鈕 */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={copyToClipboard}
                className="px-3 py-1.5 bg-vscode-button-bg hover:bg-vscode-button-hover-bg 
                         text-white text-xs rounded transition-colors"
              >
                複製錯誤資訊
              </button>
              <button
                onClick={() => {
                  console.error('錯誤詳情:', { error, errorInfo });
                }}
                className="px-3 py-1.5 bg-gray-600 hover:bg-gray-700 
                         text-white text-xs rounded transition-colors"
              >
                輸出到控制台
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * 錯誤邊界組件
 * 捕獲並處理 React 組件樹中的 JavaScript 錯誤
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null,
    };
  }

  /**
   * 靜態方法：從錯誤中派生狀態
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * 組件捕獲錯誤時調用
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 更新狀態
    this.setState({
      error,
      errorInfo,
      eventId: this.generateEventId(),
    });

    // 調用外部錯誤處理函數
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 記錄錯誤到控制台
    console.error('ErrorBoundary 捕獲到錯誤:', error);
    console.error('錯誤資訊:', errorInfo);

    // 發送錯誤到監控服務（如果配置了的話）
    this.reportError(error, errorInfo);
  }

  /**
   * 組件更新時檢查是否需要重置錯誤狀態
   */
  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    // 如果之前有錯誤且現在需要重置
    if (hasError && prevProps.resetKeys !== resetKeys) {
      if (resetKeys) {
        const hasResetKeyChanged = resetKeys.some(
          (key, index) => prevProps.resetKeys?.[index] !== key
        );
        if (hasResetKeyChanged) {
          this.resetErrorBoundary();
        }
      }
    }

    // 如果 props 變化且設置了重置標誌
    if (hasError && resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetErrorBoundary();
    }
  }

  /**
   * 生成唯一的事件 ID
   */
  private generateEventId(): string {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 報告錯誤到監控服務
   */
  private reportError(error: Error, errorInfo: ErrorInfo) {
    // 這裡可以整合錯誤監控服務，如 Sentry、LogRocket 等
    // 例如：Sentry.captureException(error, { contexts: { react: errorInfo } });
    
    // 暫時只記錄到本地存儲
    try {
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        eventId: this.state.eventId,
      };
      
      const existingReports = JSON.parse(
        localStorage.getItem('proxy-manager-error-reports') || '[]'
      );
      
      existingReports.push(errorReport);
      
      // 只保留最近的 10 個錯誤報告
      if (existingReports.length > 10) {
        existingReports.splice(0, existingReports.length - 10);
      }
      
      localStorage.setItem('proxy-manager-error-reports', JSON.stringify(existingReports));
    } catch (storageError) {
      console.error('無法保存錯誤報告到本地存儲:', storageError);
    }
  }

  /**
   * 重置錯誤邊界狀態
   */
  private resetErrorBoundary = () => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
    
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null,
    });
  };

  /**
   * 延遲重置錯誤邊界
   */
  private delayedReset = () => {
    this.resetTimeoutId = window.setTimeout(() => {
      this.resetErrorBoundary();
    }, 100);
  };

  /**
   * 重新載入頁面
   */
  private reloadPage = () => {
    window.location.reload();
  };

  /**
   * 導航到首頁
   */
  private goHome = () => {
    window.location.href = '/';
  };

  render() {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback, showDetails = true } = this.props;

    if (hasError && error) {
      // 如果提供了自定義的 fallback，使用它
      if (fallback) {
        return fallback;
      }

      // 預設的錯誤 UI
      return (
        <ErrorFallback
          error={error}
          errorInfo={errorInfo}
          onReset={this.resetErrorBoundary}
          onReload={this.reloadPage}
          onGoHome={this.goHome}
          showDetails={showDetails}
        />
      );
    }

    return children;
  }
}

/**
 * 錯誤回退組件的 Props
 */
interface ErrorFallbackProps {
  error: Error;
  errorInfo: ErrorInfo | null;
  onReset: () => void;
  onReload: () => void;
  onGoHome: () => void;
  showDetails: boolean;
}

/**
 * 錯誤回退組件
 * 顯示友好的錯誤頁面
 */
const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  onReset,
  onReload,
  onGoHome,
  showDetails,
}) => {
  const [detailsExpanded, setDetailsExpanded] = React.useState(false);

  return (
    <div className="min-h-screen bg-vscode-bg flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="bg-vscode-panel-bg border border-vscode-border rounded-lg p-8 shadow-lg">
          {/* 錯誤圖示和標題 */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/10 
                          border border-red-500/20 rounded-full mb-4">
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
            <h1 className="text-2xl font-bold text-vscode-foreground mb-2">
              糟糕！出現了一個錯誤
            </h1>
            <p className="text-vscode-foreground/70">
              應用程式遇到了意外的問題。我們已經記錄了這個錯誤，並會盡快修復。
            </p>
          </div>

          {/* 錯誤訊息 */}
          <div className="mb-6">
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 font-mono text-sm">
                {error.message || '未知錯誤'}
              </p>
            </div>
          </div>

          {/* 操作按鈕 */}
          <div className="flex flex-wrap gap-3 justify-center mb-6">
            <button
              onClick={onReset}
              className="inline-flex items-center gap-2 px-4 py-2 bg-vscode-button-bg 
                       hover:bg-vscode-button-hover-bg text-white rounded transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              重試
            </button>
            
            <button
              onClick={onReload}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-600 
                       hover:bg-gray-700 text-white rounded transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              重新載入頁面
            </button>
            
            <button
              onClick={onGoHome}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 
                       hover:bg-green-700 text-white rounded transition-colors"
            >
              <Home className="w-4 h-4" />
              回到首頁
            </button>
          </div>

          {/* 錯誤詳情 */}
          {showDetails && errorInfo && (
            <ErrorDetails
              error={error}
              errorInfo={errorInfo}
              onToggle={() => setDetailsExpanded(!detailsExpanded)}
              isExpanded={detailsExpanded}
            />
          )}

          {/* 幫助資訊 */}
          <div className="mt-6 pt-6 border-t border-vscode-border text-center">
            <p className="text-sm text-vscode-foreground/50">
              如果問題持續發生，請聯繫技術支援或查看
              <a 
                href="/help" 
                className="text-vscode-button-bg hover:underline ml-1"
              >
                幫助文檔
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 高階組件：為組件添加錯誤邊界
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

/**
 * Hook：在函數組件中使用錯誤邊界
 */
export function useErrorHandler() {
  return React.useCallback((error: Error, errorInfo?: ErrorInfo) => {
    // 拋出錯誤，讓最近的錯誤邊界捕獲
    throw error;
  }, []);
}