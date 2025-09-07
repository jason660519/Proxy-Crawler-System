import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Search, Filter, RefreshCw, CheckCircle, XCircle, Clock, Wifi } from 'lucide-react';
import { useProxies, useRefreshProxies } from '../hooks/useProxies';
import type { ProxyNode } from '../utils/api';

/**
 * 代理列表頁面組件
 * 顯示所有代理服務器的詳細列表，支持搜索、過濾和狀態管理
 */
export const ProxyList: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const limit = 20; // 每頁顯示數量

  // 使用自定義 Hook 獲取代理數據
  const { data, isLoading, error, refetch } = useProxies({
    page: currentPage,
    limit,
    search: searchTerm,
    status: filterStatus === 'all' ? undefined : (filterStatus as 'online' | 'offline')
  });

  // 刷新代理數據
  const { mutate: refreshProxies, isPending: isRefreshing } = useRefreshProxies();

  // 處理刷新按鈕點擊
  const handleRefresh = () => {
    refreshProxies();
  };

  // 處理分頁變更
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // 狀態圖示
  const getStatusIcon = (isOnline: boolean) => {
    return isOnline ? 
      <CheckCircle className="h-4 w-4 text-green-500" /> : 
      <XCircle className="h-4 w-4 text-red-500" />;
  };

  // 匿名等級徽章
  const getAnonymityBadge = (anonymity: string) => {
    const variants: Record<string, string> = {
      elite: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
      anonymous: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100',
      transparent: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
    };
    
    return (
      <Badge className={variants[anonymity] || variants.transparent}>
        {anonymity === 'elite' ? '高匿名' : anonymity === 'anonymous' ? '匿名' : '透明'}
      </Badge>
    );
  };

  // 協議徽章
  const getProtocolBadge = (protocol: string) => {
    const variants: Record<string, string> = {
      http: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100',
      https: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100',
      socks4: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100',
      socks5: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-100'
    };
    
    return (
      <Badge className={variants[protocol] || variants.http}>
        {protocol.toUpperCase()}
      </Badge>
    );
  };

  // 載入狀態
  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>載入代理列表中...</span>
        </div>
      </div>
    );
  }

  // 錯誤狀態
  if (error) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center text-red-500">
          <p>載入數據時發生錯誤</p>
          <p className="text-sm mt-2">請檢查網路連線或稍後再試</p>
          <Button className="mt-4" onClick={() => refetch()}>
            重新嘗試
          </Button>
        </div>
      </div>
    );
  }

  // 計算分頁信息
  const totalPages = data?.pagination?.totalPages || 1;
  const totalItems = data?.pagination?.total || 0;
  const proxies = data?.data || [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">代理列表</h1>
        <Button onClick={handleRefresh} disabled={isRefreshing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? '刷新中...' : '重新整理'}
        </Button>
      </div>
      
      {/* 搜索和過濾器 */}
      <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4">
        <div className="relative flex-1 max-w-sm w-full">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索代理 IP、國家..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1); // 重置到第一頁
            }}
            className="pl-10"
          />
        </div>
        
        <select
          value={filterStatus}
          onChange={(e) => {
            setFilterStatus(e.target.value);
            setCurrentPage(1); // 重置到第一頁
          }}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600"
        >
          <option value="all">所有狀態</option>
          <option value="online">在線</option>
          <option value="offline">離線</option>
        </select>
      </div>
      
      {/* 代理列表 */}
      <Card>
        <CardHeader>
          <CardTitle>代理服務器 ({totalItems})</CardTitle>
          <CardDescription>
            管理和監控您的代理服務器
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {proxies.map((proxy) => (
              <div key={proxy.id} className="flex flex-col md:flex-row md:items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <div className="flex items-center space-x-4 mb-2 md:mb-0">
                  {getStatusIcon(proxy.isOnline)}
                  <div>
                    <div className="font-medium">{proxy.ip}:{proxy.port}</div>
                    <div className="text-sm text-muted-foreground flex flex-wrap items-center gap-2">
                      <span>{proxy.country || '未知'}</span>
                      <span>•</span>
                      <span>{proxy.city || '未知城市'}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex flex-wrap items-center gap-2">
                    {getProtocolBadge(proxy.protocol)}
                    {getAnonymityBadge(proxy.anonymity)}
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm font-medium">{proxy.speed ? `${proxy.speed}ms` : 'N/A'}</div>
                    <div className="text-xs text-muted-foreground">響應時間</div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm font-medium">{proxy.uptime ? `${proxy.uptime}%` : 'N/A'}</div>
                    <div className="text-xs text-muted-foreground">正常運行時間</div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      {proxy.lastChecked ? new Date(proxy.lastChecked).toLocaleTimeString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            
            {proxies.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <Wifi className="h-12 w-12 mx-auto mb-4 text-muted-foreground/20" />
                <p>未找到符合條件的代理服務器</p>
                <p className="text-sm mt-2">嘗試調整搜索條件或刷新數據</p>
              </div>
            )}
          </div>
          
          {/* 分頁控製 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 border-t pt-4">
              <div className="text-sm text-muted-foreground">
                顯示第 {(currentPage - 1) * limit + 1} 到 {Math.min(currentPage * limit, totalItems)} 項，共 {totalItems} 項
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  上一頁
                </Button>
                
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    // 計算要顯示的頁碼
                    let startPage = Math.max(1, currentPage - 2);
                    let endPage = Math.min(totalPages, startPage + 4);
                    
                    if (endPage - startPage < 4) {
                      startPage = Math.max(1, endPage - 4);
                    }
                    
                    const page = startPage + i;
                    
                    return (
                      <Button
                        key={page}
                        variant={page === currentPage ? "default" : "outline"}
                        size="sm"
                        onClick={() => handlePageChange(page)}
                        className={page === currentPage ? "bg-blue-500 text-white" : ""}
                      >
                        {page}
                      </Button>
                    );
                  })}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  下一頁
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ProxyList;