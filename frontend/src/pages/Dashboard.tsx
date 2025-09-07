import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Activity, Server, Users, Zap, Globe, TrendingUp } from 'lucide-react';
import { useProxyStats } from '../hooks/useProxies';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell
} from 'recharts';

/**
 * 儀表板頁面組件
 * 顯示代理服務器的總體統計信息和狀態概覽
 */
export const Dashboard: React.FC = () => {
  const { data: stats, isLoading, error } = useProxyStats();
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [countryData, setCountryData] = useState<any[]>([]);

  // 模擬性能數據（實際應該從 API 獲取）
  useEffect(() => {
    const mockPerformanceData = [
      { date: '01/01', successRate: 92, avgLatency: 280, proxies: 1200 },
      { date: '02/01', successRate: 94, avgLatency: 265, proxies: 1250 },
      { date: '03/01', successRate: 95, avgLatency: 250, proxies: 1300 },
      { date: '04/01', successRate: 93, avgLatency: 270, proxies: 1280 },
      { date: '05/01', successRate: 96, avgLatency: 240, proxies: 1350 },
      { date: '06/01', successRate: 97, avgLatency: 230, proxies: 1400 },
      { date: '07/01', successRate: 98, avgLatency: 220, proxies: 1420 },
    ];
    
    const mockCountryData = [
      { name: '美國', value: 456 },
      { name: '德國', value: 321 },
      { name: '日本', value: 289 },
      { name: '法國', value: 156 },
      { name: '英國', value: 123 },
    ];
    
    setPerformanceData(mockPerformanceData);
    setCountryData(mockCountryData);
  }, []);

  // 顏色配置
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span>載入儀表板數據中...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center text-red-500">
          <p>載入數據時發生錯誤</p>
          <p className="text-sm mt-2">請檢查網路連線或稍後再試</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">儀表板</h1>
      </div>
      
      {/* 統計卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總代理數</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 1234}</div>
            <p className="text-xs text-muted-foreground">
              +20.1% 較上月
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍代理</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.online || 892}</div>
            <p className="text-xs text-muted-foreground">
              +12.5% 較上月
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均響應時間</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.averageSpeed ? `${Math.round(stats.averageSpeed)}ms` : '245ms'}</div>
            <p className="text-xs text-muted-foreground">
              -5.2% 較上月
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">成功率</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.averageUptime ? `${stats.averageUptime.toFixed(1)}%` : '98.2%'}</div>
            <p className="text-xs text-muted-foreground">
              +0.8% 較上月
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* 圖表區域 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>代理使用趨勢</CardTitle>
            <CardDescription>
              過去7天的代理使用情況
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={performanceData}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="successRate"
                    name="成功率 (%)"
                    stroke="#8884d8"
                    activeDot={{ r: 8 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="avgLatency"
                    name="平均延遲 (ms)"
                    stroke="#82ca9d"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>地理分佈</CardTitle>
            <CardDescription>
              代理服務器的地理位置分佈
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={countryData}
                    cx="50%"
                    cy="50%"
                    labelLine={true}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {countryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* 額外統計卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">按協議分佈</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={Object.entries(stats?.byProtocol || {
                    http: 456,
                    https: 321,
                    socks4: 289,
                    socks5: 168
                  }).map(([name, value]) => ({ name, value }))}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>按國家分佈</CardTitle>
            <CardDescription>
              各國代理服務器數量
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={Object.entries(stats?.byCountry || {
                    '美國': 456,
                    '德國': 321,
                    '日本': 289,
                    '法國': 156,
                    '英國': 123,
                    '加拿大': 98,
                    '澳大利亞': 87
                  }).map(([name, value]) => ({ name, value }))}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 50,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;