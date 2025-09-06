import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Play, Pause, Square, Clock, Calendar, Settings } from 'lucide-react';

/**
 * 任務調度頁面組件
 * 管理和監控爬蟲任務的調度和執行狀態
 */
export const TaskScheduling: React.FC = () => {
  const [tasks, setTasks] = useState([
    {
      id: 1,
      name: '代理池更新任務',
      status: 'running',
      schedule: '每小時',
      lastRun: '2024-01-15 14:30:00',
      nextRun: '2024-01-15 15:30:00',
      success: 95
    },
    {
      id: 2,
      name: '代理質量檢測',
      status: 'scheduled',
      schedule: '每30分鐘',
      lastRun: '2024-01-15 14:00:00',
      nextRun: '2024-01-15 14:30:00',
      success: 88
    },
    {
      id: 3,
      name: '失效代理清理',
      status: 'paused',
      schedule: '每日 02:00',
      lastRun: '2024-01-15 02:00:00',
      nextRun: '2024-01-16 02:00:00',
      success: 100
    }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'scheduled': return 'bg-blue-500';
      case 'paused': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running': return '執行中';
      case 'scheduled': return '已排程';
      case 'paused': return '已暫停';
      case 'error': return '錯誤';
      default: return '未知';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">任務調度</h1>
        <Button>
          <Settings className="mr-2 h-4 w-4" />
          調度設定
        </Button>
      </div>

      {/* 統計概覽 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總任務數</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
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
            <CardTitle className="text-sm font-medium">已排程任務</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.filter(t => t.status === 'scheduled').length}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均成功率</CardTitle>
            <Badge className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(tasks.reduce((acc, t) => acc + t.success, 0) / tasks.length)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 任務列表 */}
      <Card>
        <CardHeader>
          <CardTitle>任務列表</CardTitle>
          <CardDescription>管理和監控所有調度任務</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tasks.map((task) => (
              <div key={task.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(task.status)}`} />
                  <div>
                    <h3 className="font-medium">{task.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      調度: {task.schedule} | 成功率: {task.success}%
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right text-sm">
                    <p>上次執行: {task.lastRun}</p>
                    <p>下次執行: {task.nextRun}</p>
                  </div>
                  
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