import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/Select';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Clock, Globe, Zap, Shield } from 'lucide-react';

interface QualityMetrics {
  totalProxies: number;
  workingProxies: number;
  averageSpeed: number;
  averageUptime: number;
  anonymityLevels: {
    transparent: number;
    anonymous: number;
    elite: number;
  };
  geographicDistribution: {
    country: string;
    count: number;
  }[];
  speedDistribution: {
    range: string;
    count: number;
  }[];
  uptimeHistory: {
    date: string;
    uptime: number;
  }[];
}

interface ProxyQuality {
  id: string;
  host: string;
  port: number;
  country: string;
  speed: number;
  uptime: number;
  anonymity: 'transparent' | 'anonymous' | 'elite';
  lastChecked: string;
  qualityScore: number;
}

/**
 * 質量分析頁面組件
 * 提供代理質量的深度分析和可視化
 */
export const QualityAnalysis: React.FC = () => {
  const [metrics, setMetrics] = useState<QualityMetrics | null>(null);
  const [topProxies, setTopProxies] = useState<ProxyQuality[]>([]);
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQualityMetrics();
  }, [timeRange]);

  const fetchQualityMetrics = async () => {
    setLoading(true);
    try {
      // 模擬API調用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockMetrics: QualityMetrics = {
        totalProxies: 1250,
        workingProxies: 892,
        averageSpeed: 1.2,
        averageUptime: 94.5,
        anonymityLevels: {
          transparent: 156,
          anonymous: 445,
          elite: 291
        },
        geographicDistribution: [
          { country: '美國', count: 234 },
          { country: '德國', count: 189 },
          { country: '英國', count: 156 },
          { country: '法國', count: 134 },
          { country: '日本', count: 98 },
          { country: '其他', count: 81 }
        ],
        speedDistribution: [
          { range: '< 0.5s', count: 123 },
          { range: '0.5-1s', count: 267 },
          { range: '1-2s', count: 334 },
          { range: '2-5s', count: 145 },
          { range: '&gt; 5s', count: 23 }
        ],
        uptimeHistory: [
          { date: '2024-01-01', uptime: 92.3 },
          { date: '2024-01-02', uptime: 94.1 },
          { date: '2024-01-03', uptime: 91.8 },
          { date: '2024-01-04', uptime: 95.2 },
          { date: '2024-01-05', uptime: 93.7 },
          { date: '2024-01-06', uptime: 96.1 },
          { date: '2024-01-07', uptime: 94.5 }
        ]
      };
      
      const mockTopProxies: ProxyQuality[] = [
        {
          id: '1',
          host: '192.168.1.100',
          port: 8080,
          country: '美國',
          speed: 0.3,
          uptime: 99.2,
          anonymity: 'elite',
          lastChecked: '2024-01-07T10:30:00Z',
          qualityScore: 98.5
        },
        {
          id: '2',
          host: '10.0.0.50',
          port: 3128,
          country: '德國',
          speed: 0.4,
          uptime: 98.7,
          anonymity: 'elite',
          lastChecked: '2024-01-07T10:25:00Z',
          qualityScore: 97.8
        },
        {
          id: '3',
          host: '172.16.0.25',
          port: 8888,
          country: '英國',
          speed: 0.5,
          uptime: 97.9,
          anonymity: 'anonymous',
          lastChecked: '2024-01-07T10:20:00Z',
          qualityScore: 96.2
        }
      ];
      
      setMetrics(mockMetrics);
      setTopProxies(mockTopProxies);
    } catch (error) {
      console.error('獲取質量指標失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAnonymityColor = (level: string) => {
    switch (level) {
      case 'elite': return 'bg-green-500';
      case 'anonymous': return 'bg-yellow-500';
      case 'transparent': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getAnonymityIcon = (level: string) => {
    switch (level) {
      case 'elite': return <Shield className="h-4 w-4" />;
      case 'anonymous': return <CheckCircle className="h-4 w-4" />;
      case 'transparent': return <AlertTriangle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">無法載入質量分析數據</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">質量分析</h1>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">過去1天</SelectItem>
              <SelectItem value="7d">過去7天</SelectItem>
              <SelectItem value="30d">過去30天</SelectItem>
              <SelectItem value="90d">過去90天</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchQualityMetrics}>刷新數據</Button>
        </div>
      </div>
      
      {/* 概覽指標 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總代理數</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalProxies.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              可用: {metrics.workingProxies} ({((metrics.workingProxies / metrics.totalProxies) * 100).toFixed(1)}%)
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均速度</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.averageSpeed}s</div>
            <p className="text-xs text-green-600 flex items-center">
              <TrendingUp className="h-3 w-3 mr-1" />
              比上週快 12%
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均正常運行時間</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.averageUptime}%</div>
            <Progress value={metrics.averageUptime} className="mt-2" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">精英代理</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.anonymityLevels.elite}</div>
            <p className="text-xs text-muted-foreground">
              佔總數 {((metrics.anonymityLevels.elite / metrics.workingProxies) * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>
      
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概覽</TabsTrigger>
          <TabsTrigger value="performance">性能分析</TabsTrigger>
          <TabsTrigger value="geographic">地理分佈</TabsTrigger>
          <TabsTrigger value="top-proxies">頂級代理</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>匿名性分佈</CardTitle>
                <CardDescription>按匿名性級別分類的代理數量</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: '精英', value: metrics.anonymityLevels.elite, color: '#10B981' },
                        { name: '匿名', value: metrics.anonymityLevels.anonymous, color: '#F59E0B' },
                        { name: '透明', value: metrics.anonymityLevels.transparent, color: '#EF4444' }
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {[
                        { name: '精英', value: metrics.anonymityLevels.elite, color: '#10B981' },
                        { name: '匿名', value: metrics.anonymityLevels.anonymous, color: '#F59E0B' },
                        { name: '透明', value: metrics.anonymityLevels.transparent, color: '#EF4444' }
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>正常運行時間趨勢</CardTitle>
                <CardDescription>過去7天的平均正常運行時間</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metrics.uptimeHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[85, 100]} />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="uptime" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      dot={{ fill: '#8884d8' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>速度分佈</CardTitle>
              <CardDescription>代理響應時間分佈情況</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={metrics.speedDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="geographic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>地理分佈</CardTitle>
              <CardDescription>按國家/地區分類的代理數量</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={metrics.geographicDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="country" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="top-proxies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>頂級代理</CardTitle>
              <CardDescription>質量評分最高的代理服務器</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topProxies.map((proxy, index) => (
                  <div key={proxy.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-primary text-primary-foreground rounded-full text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium">{proxy.host}:{proxy.port}</div>
                        <div className="text-sm text-muted-foreground">{proxy.country}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <div className="text-sm font-medium">{proxy.speed}s</div>
                        <div className="text-xs text-muted-foreground">速度</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-sm font-medium">{proxy.uptime}%</div>
                        <div className="text-xs text-muted-foreground">正常運行時間</div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Badge 
                          variant="secondary" 
                          className={`${getAnonymityColor(proxy.anonymity)} text-white`}
                        >
                          {getAnonymityIcon(proxy.anonymity)}
                          <span className="ml-1 capitalize">{proxy.anonymity}</span>
                        </Badge>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-600">{proxy.qualityScore}</div>
                        <div className="text-xs text-muted-foreground">質量評分</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default QualityAnalysis;