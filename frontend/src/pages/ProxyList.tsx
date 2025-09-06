import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Search, Filter, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react';
import { ProxyNode } from '../types';

/**
 * 代理列表頁面組件
 * 顯示所有代理服務器的詳細列表，支持搜索、過濾和狀態管理
 */
export const ProxyList: React.FC = () => {
  const [proxies, setProxies] = useState<ProxyNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // 模擬數據加載
  useEffect(() => {
    const mockProxies: ProxyNode[] = [
      {
        id: '1',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'http',
        country: 'US',
        anonymity: 'high',
        speed: 245,
        uptime: 98.5,
        lastChecked: new Date().toISOString(),
        isActive: true
      },
      {
        id: '2',
        host: '10.0.0.50',
        port: 3128,
        protocol: 'https',
        country: 'JP',
        anonymity: 'medium',
        speed: 180,
        uptime: 95.2,
        lastChecked: new Date().toISOString(),
        isActive: true
      },
      {
        id: '3',
        host: '172.16.0.25',
        port: 1080,
        protocol: 'socks5',
        country: 'DE',
        anonymity: 'high',
        speed: 320,
        uptime: 89.7,
        lastChecked: new Date().toISOString(),
        isActive: false
      }
    ];
    
    setTimeout(() => {
      setProxies(mockProxies);
      setLoading(false);
    }, 1000);
  }, []);

  // 過濾代理列表
  const filteredProxies = proxies.filter(proxy => {
    const matchesSearch = proxy.host.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         proxy.country.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || 
                         (filterStatus === 'active' && proxy.isActive) ||
                         (filterStatus === 'inactive' && !proxy.isActive);
    return matchesSearch && matchesFilter;
  });

  const getStatusIcon = (isActive: boolean) => {
    return isActive ? 
      <CheckCircle className="h-4 w-4 text-green-500" /> : 
      <XCircle className="h-4 w-4 text-red-500" />;
  };

  const getAnonymityBadge = (anonymity: string) => {
    const variants = {
      high: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-red-100 text-red-800'
    };
    return (
      <Badge className={variants[anonymity as keyof typeof variants] || variants.low}>
        {anonymity}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>載入代理列表中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">代理列表</h1>
        <Button>
          <RefreshCw className="h-4 w-4 mr-2" />
          重新整理
        </Button>
      </div>
      
      {/* 搜索和過濾器 */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索代理..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">所有狀態</option>
          <option value="active">活躍</option>
          <option value="inactive">非活躍</option>
        </select>
      </div>
      
      {/* 代理列表 */}
      <Card>
        <CardHeader>
          <CardTitle>代理服務器 ({filteredProxies.length})</CardTitle>
          <CardDescription>
            管理和監控您的代理服務器
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredProxies.map((proxy) => (
              <div key={proxy.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                <div className="flex items-center space-x-4">
                  {getStatusIcon(proxy.isActive)}
                  <div>
                    <div className="font-medium">{proxy.host}:{proxy.port}</div>
                    <div className="text-sm text-muted-foreground">
                      {proxy.protocol.toUpperCase()} • {proxy.country}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  {getAnonymityBadge(proxy.anonymity)}
                  
                  <div className="text-right">
                    <div className="text-sm font-medium">{proxy.speed}ms</div>
                    <div className="text-xs text-muted-foreground">響應時間</div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm font-medium">{proxy.uptime}%</div>
                    <div className="text-xs text-muted-foreground">正常運行時間</div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      {new Date(proxy.lastChecked).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            
            {filteredProxies.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                未找到符合條件的代理服務器
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProxyList;