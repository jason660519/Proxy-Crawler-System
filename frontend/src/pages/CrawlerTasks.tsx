import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { Play, Pause, Square, Download, Eye, Settings } from 'lucide-react';

/**
 * 爬蟲任務頁面組件
 * 管理和監控具體的爬蟲任務執行情況
 */
export const CrawlerTasks: React.FC = () => {
  const [tasks, setTasks] = useState([
    {
      id: 1,
      name: 'Free Proxy List 爬取',
      url: 'https://free-proxy-list.net/',
      status: 'running',
      progress: 75,
      collected: 1250,
      target: 2000,
      startTime: '2024-01-15 14:30:00',
      duration: '00:15:30',
      errors: 2
    },
    {
      id: 2,
      name: 'ProxyNova 爬取',
      url: 'https://www.proxynova.com/',
      status: 'completed',
      progress: 100,
      collected: 890,
      target: 1000,
      startTime: '2024-01-15 13:45:00',
      duration: '00:22:15',
      errors: 0
    },
    {
      id: 3,
      name: 'HideMyAss 爬取',
      url: 'https://www.hidemyass.com/',
      status: 'paused',
      progress: 45,
      collected: 450,
      target: 1500,
      startTime: '2024-01-15 14:00:00',
      duration: '00:08:20',
      errors: 5
    },
    {
      id: 4,
      name: 'ProxyList 爬取',
      url: 'https://www.proxy-list.download/',
      status: 'error',
      progress: 20,
      collected: 120,
      target: 800,
      startTime: '2024-01-15 14:20:00',
      duration: '00:03:45',
      errors: 15
    }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'completed': return 'bg-blue-500';
      case 'paused': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running': return '執行中';
      case 'completed': return '已完成';
      case 'paused': return '已暫停';
      case 'error': return '錯誤';
      default: return '未知';
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-600';
      case 'completed': return 'bg-blue-600';
      case 'paused': return 'bg-yellow-600';
      case 'error': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">爬蟲任務</h1>
        <Button>
          <Settings className="mr-2 h-4 w-4" />
          任務設定
        </Button>
      </div>

      {/* 統計概覽 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總任務數</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tasks.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">執行中任務</CardTitle>
            <Play className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.filter(t => t.status === 'running').length}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">已收集代理</CardTitle>
            <Download className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.reduce((acc, t) => acc + t.collected, 0)}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總錯誤數</CardTitle>
            <Square className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.reduce((acc, t) => acc + t.errors, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 任務列表 */}
      <Card>
        <CardHeader>
          <CardTitle>任務列表</CardTitle>
          <CardDescription>監控所有爬蟲任務的執行狀態和進度</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {tasks.map((task) => (
              <div key={task.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(task.status)}`} />
                    <div>
                      <h3 className="font-medium">{task.name}</h3>
                      <p className="text-sm text-muted-foreground">{task.url}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <Badge variant={task.status === 'running' ? 'default' : 'secondary'}>
                      {getStatusText(task.status)}
                    </Badge>
                    
                    <div className="flex space-x-2">
                      {task.status === 'running' ? (
                        <Button size="sm" variant="outline">
                          <Pause className="h-4 w-4" />
                        </Button>
                      ) : (
                        <Button size="sm" variant="outline">
                          <Play className="h-4 w-4" />
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        <Square className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>進度: {task.collected}/{task.target}</span>
                    <span>{task.progress}%</span>
                  </div>
                  <Progress value={task.progress} className="h-2" />
                </div>
                
                <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">開始時間:</span>
                    <p>{task.startTime}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">執行時間:</span>
                    <p>{task.duration}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">錯誤數:</span>
                    <p className={task.errors > 0 ? 'text-red-600' : 'text-green-600'}>
                      {task.errors}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};