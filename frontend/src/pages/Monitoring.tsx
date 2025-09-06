import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { Select } from '../components/ui/Select';
import { Activity, AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown, Server, Database, Wifi, Clock } from 'lucide-react';

/**
 * 系統監控頁面組件
 * 提供實時系統狀態監控、性能指標和警報管理
 */
export const Monitoring: React.FC = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const [systemMetrics] = useState({
    cpu: { current: 23, trend: 'up', status: 'normal' },
    memory: { current: 45, trend: 'stable', status: 'normal' },
    disk: { current: 67, trend: 'up', status: 'warning' },
    network: { current: 12, trend: 'down', status: 'normal' }
  });

  const [serviceStatus] = useState([
    { name: 'API 服務', status: 'running', uptime: '7天 14小時', port: '8000' },
    { name: 'Web 服務', status: 'running', uptime: '7天 14小時', port: '3000' },
    { name: 'PostgreSQL', status: 'running', uptime: '15天 8小時', port: '5432' },
    { name: 'Redis 緩存', status: 'running', uptime: '15天 8小時', port: '6379' },
    { name: '代理檢測器', status: 'running', uptime: '2天 6小時', port: '-' },
    { name: '爬蟲調度器', status: 'stopped', uptime: '-', port: '-' }
  ]);

  const [alerts] = useState([
    {
      id: 1,
      level: 'warning',
      message: '磁盤使用率超過 60%',
      timestamp: '2024-01-15 14:30:00',
      source: 'System Monitor',
      resolved: false
    },
    {
      id: 2,
      level: 'info',
      message: '代理池已更新，新增 150 個代理',
      timestamp: '2024-01-15 13:45:00',
      source: 'Proxy Crawler',
      resolved: true
    },
    {
      id: 3,
      level: 'error',
      message: '爬蟲調度器連接失敗',
      timestamp: '2024-01-15 12:20:00',
      source: 'Task Scheduler',
      resolved: false
    },
    {
      id: 4,
      level: 'success',
      message: '數據庫備份完成',
      timestamp: '2024-01-15 02:00:00',
      source: 'Database',
      resolved: true
    }
  ]);

  const [performanceData] = useState({
    proxyRequests: {
      total: 15420,
      successful: 13876,
      failed: 1544,
      successRate: 90.0
    },
    crawlerStats: {
      sitesMonitored: 12,
      proxiesFound: 2847,
      validProxies: 1923,
      validationRate: 67.5
    },
    responseTime: {
      average: 245,
      p95: 890,
      p99: 1250
    }
  });

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        setLastUpdate(new Date());
      }, 30000); // 每30秒更新一次

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusBadge = (status: string) => {
    const statusMap: { [key: string]: { variant: string; text: string; icon: React.ReactNode } } = {
      running: { variant: 'success', text: '運行中', icon: <CheckCircle className="h-3 w-3" /> },
      stopped: { variant: 'destructive', text: '已停止', icon: <XCircle className="h-3 w-3" /> },
      warning: { variant: 'warning', text: '警告', icon: <AlertTriangle className="h-3 w-3" /> },
      error: { variant: 'destructive', text: '錯誤', icon: <XCircle className="h-3 w-3" /> }
    };
    
    const statusInfo = statusMap[status] || { variant: 'secondary', text: status, icon: null };
    return (
      <Badge variant={statusInfo.variant as any} className="flex items-center gap-1">
        {statusInfo.icon}
        {statusInfo.text}
      </Badge>
    );
  };

  const getAlertBadge = (level: string) => {
    const levelMap: { [key: string]: { variant: string; text: string } } = {
      error: { variant: 'destructive', text: '錯誤' },
      warning: { variant: 'warning', text: '警告' },
      info: { variant: 'default', text: '資訊' },
      success: { variant: 'success', text: '成功' }
    };
    
    const levelInfo = levelMap[level] || { variant: 'secondary', text: level };
    return <Badge variant={levelInfo.variant as any}>{levelInfo.text}</Badge>;
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-green-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getMetricColor = (value: number, type: string) => {
    if (type === 'network') return 'text-blue-600';
    if (value < 50) return 'text-green-600';
    if (value < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">系統監控</h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              最後更新: {lastUpdate.toLocaleTimeString()}
            </span>
          </div>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <option value="1h">最近 1 小時</option>
            <option value="6h">最近 6 小時</option>
            <option value="24h">最近 24 小時</option>
            <option value="7d">最近 7 天</option>
          </Select>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '自動刷新' : '手動刷新'}
          </Button>
        </div>
      </div>

      {/* 系統指標概覽 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU 使用率</CardTitle>
            <div className="flex items-center space-x-1">
              {getTrendIcon(systemMetrics.cpu.trend)}
              <Server className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getMetricColor(systemMetrics.cpu.current, 'cpu')}`}>
              {systemMetrics.cpu.current}%
            </div>
            <p className="text-xs text-muted-foreground">
              狀態正常
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">記憶體使用率</CardTitle>
            <div className="flex items-center space-x-1">
              {getTrendIcon(systemMetrics.memory.trend)}
              <Database className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getMetricColor(systemMetrics.memory.current, 'memory')}`}>
              {systemMetrics.memory.current}%
            </div>
            <p className="text-xs text-muted-foreground">
              狀態正常
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">磁盤使用率</CardTitle>
            <div className="flex items-center space-x-1">
              {getTrendIcon(systemMetrics.disk.trend)}
              <Server className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getMetricColor(systemMetrics.disk.current, 'disk')}`}>
              {systemMetrics.disk.current}%
            </div>
            <p className="text-xs text-muted-foreground">
              需要注意
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">網路流量</CardTitle>
            <div className="flex items-center space-x-1">
              {getTrendIcon(systemMetrics.network.trend)}
              <Wifi className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getMetricColor(systemMetrics.network.current, 'network')}`}>
              {systemMetrics.network.current} MB/s
            </div>
            <p className="text-xs text-muted-foreground">
              流量正常
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="services" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="services">服務狀態</TabsTrigger>
          <TabsTrigger value="performance">性能指標</TabsTrigger>
          <TabsTrigger value="alerts">警報中心</TabsTrigger>
          <TabsTrigger value="logs">系統日誌</TabsTrigger>
        </TabsList>

        {/* 服務狀態標籤 */}
        <TabsContent value="services" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Server className="mr-2 h-5 w-5" />
                服務狀態
              </CardTitle>
              <CardDescription>監控所有系統服務的運行狀態</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {serviceStatus.map((service, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Server className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="font-medium">{service.name}</p>
                        <p className="text-sm text-muted-foreground">
                          運行時間: {service.uptime}
                          {service.port !== '-' && ` • 端口: ${service.port}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(service.status)}
                      <Button size="sm" variant="outline">
                        {service.status === 'running' ? '重啟' : '啟動'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 性能指標標籤 */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>代理請求統計</CardTitle>
                <CardDescription>代理服務的請求處理情況</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">總請求數</span>
                  <span className="text-2xl font-bold">{performanceData.proxyRequests.total.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">成功請求</span>
                  <span className="text-lg font-semibold text-green-600">{performanceData.proxyRequests.successful.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">失敗請求</span>
                  <span className="text-lg font-semibold text-red-600">{performanceData.proxyRequests.failed.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">成功率</span>
                  <span className="text-lg font-semibold">{performanceData.proxyRequests.successRate}%</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>爬蟲統計</CardTitle>
                <CardDescription>代理爬蟲的工作情況</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">監控網站</span>
                  <span className="text-2xl font-bold">{performanceData.crawlerStats.sitesMonitored}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">發現代理</span>
                  <span className="text-lg font-semibold">{performanceData.crawlerStats.proxiesFound.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">有效代理</span>
                  <span className="text-lg font-semibold text-green-600">{performanceData.crawlerStats.validProxies.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">有效率</span>
                  <span className="text-lg font-semibold">{performanceData.crawlerStats.validationRate}%</span>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>響應時間統計</CardTitle>
                <CardDescription>系統響應時間分析</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-sm font-medium text-muted-foreground">平均響應時間</p>
                    <p className="text-2xl font-bold">{performanceData.responseTime.average}ms</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-muted-foreground">95% 響應時間</p>
                    <p className="text-2xl font-bold">{performanceData.responseTime.p95}ms</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-muted-foreground">99% 響應時間</p>
                    <p className="text-2xl font-bold">{performanceData.responseTime.p99}ms</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 警報中心標籤 */}
        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertTriangle className="mr-2 h-5 w-5" />
                警報中心
              </CardTitle>
              <CardDescription>查看和管理系統警報</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <div key={alert.id} className={`flex items-center justify-between p-3 border rounded-lg ${
                    alert.resolved ? 'opacity-60' : ''
                  }`}>
                    <div className="flex items-center space-x-3">
                      <AlertTriangle className={`h-5 w-5 ${
                        alert.level === 'error' ? 'text-red-500' :
                        alert.level === 'warning' ? 'text-yellow-500' :
                        alert.level === 'success' ? 'text-green-500' : 'text-blue-500'
                      }`} />
                      <div>
                        <p className="font-medium">{alert.message}</p>
                        <p className="text-sm text-muted-foreground">
                          {alert.source} • {alert.timestamp}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getAlertBadge(alert.level)}
                      {!alert.resolved && (
                        <Button size="sm" variant="outline">
                          標記已解決
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 系統日誌標籤 */}
        <TabsContent value="logs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="mr-2 h-5 w-5" />
                系統日誌
              </CardTitle>
              <CardDescription>查看詳細的系統運行日誌</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-96 overflow-y-auto">
                <div>[2024-01-15 14:30:15] INFO: API server started on port 8000</div>
                <div>[2024-01-15 14:30:16] INFO: Database connection established</div>
                <div>[2024-01-15 14:30:17] INFO: Proxy pool initialized with 1923 active proxies</div>
                <div>[2024-01-15 14:30:18] INFO: Crawler scheduler started</div>
                <div>[2024-01-15 14:31:00] INFO: Proxy validation completed: 1850/1923 valid</div>
                <div>[2024-01-15 14:31:30] WARN: Disk usage exceeded 60% threshold</div>
                <div>[2024-01-15 14:32:00] INFO: New proxy batch added: 25 proxies from free-proxy-list.net</div>
                <div>[2024-01-15 14:32:15] ERROR: Failed to connect to crawler scheduler</div>
                <div>[2024-01-15 14:32:30] INFO: Automatic retry scheduled for crawler scheduler</div>
                <div>[2024-01-15 14:33:00] INFO: Memory usage: 45% (normal)</div>
                <div>[2024-01-15 14:33:15] INFO: CPU usage: 23% (normal)</div>
                <div>[2024-01-15 14:33:30] INFO: Network traffic: 12 MB/s</div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};