import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Progress } from '../components/ui/Progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { Play, Pause, RotateCcw, Settings, TrendingUp, AlertTriangle } from 'lucide-react';

interface PoolStats {
  total: number;
  active: number;
  failed: number;
  pending: number;
  successRate: number;
}

interface PoolConfig {
  maxSize: number;
  minHealthy: number;
  checkInterval: number;
  rotationEnabled: boolean;
}

/**
 * 代理池頁面組件
 * 管理代理池的配置、監控和控制
 */
export const ProxyPool: React.FC = () => {
  const [poolStats, setPoolStats] = useState<PoolStats>({
    total: 150,
    active: 120,
    failed: 15,
    pending: 15,
    successRate: 85.2
  });
  
  const [poolConfig, setPoolConfig] = useState<PoolConfig>({
    maxSize: 200,
    minHealthy: 50,
    checkInterval: 300,
    rotationEnabled: true
  });
  
  const [isRunning, setIsRunning] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // 模擬實時更新
  useEffect(() => {
    const interval = setInterval(() => {
      setPoolStats(prev => ({
        ...prev,
        active: Math.max(50, prev.active + Math.floor(Math.random() * 10 - 5)),
        failed: Math.max(0, prev.failed + Math.floor(Math.random() * 4 - 2)),
        successRate: Math.max(70, Math.min(95, prev.successRate + Math.random() * 2 - 1))
      }));
      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleTogglePool = () => {
    setIsRunning(!isRunning);
  };

  const handleResetPool = () => {
    setPoolStats({
      total: 150,
      active: 120,
      failed: 15,
      pending: 15,
      successRate: 85.2
    });
  };

  const getHealthStatus = () => {
    if (poolStats.successRate >= 80) return { status: '健康', color: 'text-green-600', bg: 'bg-green-100' };
    if (poolStats.successRate >= 60) return { status: '警告', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { status: '危險', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const health = getHealthStatus();

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">代理池管理</h1>
        <div className="flex items-center space-x-2">
          <Button
            variant={isRunning ? "destructive" : "default"}
            onClick={handleTogglePool}
          >
            {isRunning ? (
              <>
                <Pause className="h-4 w-4 mr-2" />
                暫停池
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                啟動池
              </>
            )}
          </Button>
          <Button variant="outline" onClick={handleResetPool}>
            <RotateCcw className="h-4 w-4 mr-2" />
            重置
          </Button>
        </div>
      </div>
      
      {/* 狀態概覽 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">池狀態</CardTitle>
            <div className={`h-3 w-3 rounded-full ${isRunning ? 'bg-green-500' : 'bg-red-500'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isRunning ? '運行中' : '已停止'}</div>
            <p className="text-xs text-muted-foreground">
              最後更新: {lastUpdate.toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍代理</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{poolStats.active}</div>
            <p className="text-xs text-muted-foreground">
              總計 {poolStats.total} 個代理
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">成功率</CardTitle>
            <div className={`px-2 py-1 rounded-full text-xs ${health.bg} ${health.color}`}>
              {health.status}
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{poolStats.successRate.toFixed(1)}%</div>
            <Progress value={poolStats.successRate} className="mt-2" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">失敗代理</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{poolStats.failed}</div>
            <p className="text-xs text-muted-foreground">
              待處理 {poolStats.pending} 個
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* 詳細配置和監控 */}
      <Tabs defaultValue="monitor" className="space-y-4">
        <TabsList>
          <TabsTrigger value="monitor">監控</TabsTrigger>
          <TabsTrigger value="config">配置</TabsTrigger>
          <TabsTrigger value="logs">日誌</TabsTrigger>
        </TabsList>
        
        <TabsContent value="monitor" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>代理分佈</CardTitle>
                <CardDescription>按狀態分類的代理數量</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">活躍</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full" 
                          style={{ width: `${(poolStats.active / poolStats.total) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{poolStats.active}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">失敗</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-red-500 h-2 rounded-full" 
                          style={{ width: `${(poolStats.failed / poolStats.total) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{poolStats.failed}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">待處理</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-yellow-500 h-2 rounded-full" 
                          style={{ width: `${(poolStats.pending / poolStats.total) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{poolStats.pending}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>性能指標</CardTitle>
                <CardDescription>實時性能監控</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>平均響應時間</span>
                      <span>245ms</span>
                    </div>
                    <Progress value={75} />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>併發連接數</span>
                      <span>89/100</span>
                    </div>
                    <Progress value={89} />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>帶寬使用率</span>
                      <span>67%</span>
                    </div>
                    <Progress value={67} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="config" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>池配置</CardTitle>
              <CardDescription>調整代理池的運行參數</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">最大池大小</label>
                  <input 
                    type="number" 
                    value={poolConfig.maxSize}
                    onChange={(e) => setPoolConfig(prev => ({ ...prev, maxSize: parseInt(e.target.value) }))}
                    className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">最小健康代理數</label>
                  <input 
                    type="number" 
                    value={poolConfig.minHealthy}
                    onChange={(e) => setPoolConfig(prev => ({ ...prev, minHealthy: parseInt(e.target.value) }))}
                    className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">檢查間隔 (秒)</label>
                  <input 
                    type="number" 
                    value={poolConfig.checkInterval}
                    onChange={(e) => setPoolConfig(prev => ({ ...prev, checkInterval: parseInt(e.target.value) }))}
                    className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <input 
                    type="checkbox" 
                    checked={poolConfig.rotationEnabled}
                    onChange={(e) => setPoolConfig(prev => ({ ...prev, rotationEnabled: e.target.checked }))}
                    className="rounded"
                  />
                  <label className="text-sm font-medium">啟用代理輪換</label>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline">重置</Button>
                <Button>保存配置</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>系統日誌</CardTitle>
              <CardDescription>代理池運行日誌</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                <div className="text-sm font-mono p-2 bg-gray-50 rounded">
                  <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
                  <span className="text-green-600 ml-2">INFO</span>
                  <span className="ml-2">代理池健康檢查完成，120個代理正常運行</span>
                </div>
                <div className="text-sm font-mono p-2 bg-gray-50 rounded">
                  <span className="text-gray-500">[{new Date(Date.now() - 60000).toLocaleTimeString()}]</span>
                  <span className="text-yellow-600 ml-2">WARN</span>
                  <span className="ml-2">代理 192.168.1.100:8080 響應時間過長 (&gt;500ms)</span>
                </div>
                <div className="text-sm font-mono p-2 bg-gray-50 rounded">
                  <span className="text-gray-500">[{new Date(Date.now() - 120000).toLocaleTimeString()}]</span>
                  <span className="text-red-600 ml-2">ERROR</span>
                  <span className="ml-2">代理 10.0.0.50:3128 連接失敗，已從池中移除</span>
                </div>
                <div className="text-sm font-mono p-2 bg-gray-50 rounded">
                  <span className="text-gray-500">[{new Date(Date.now() - 180000).toLocaleTimeString()}]</span>
                  <span className="text-green-600 ml-2">INFO</span>
                  <span className="ml-2">新增代理 172.16.0.25:1080 到池中</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ProxyPool;