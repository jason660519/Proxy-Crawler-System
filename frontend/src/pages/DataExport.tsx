import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Switch } from '../components/ui/Switch';
import { Download, FileText, Database, Calendar, Filter } from 'lucide-react';

/**
 * 數據導出頁面組件
 * 提供代理數據的導出功能，支持多種格式和篩選條件
 */
export const DataExport: React.FC = () => {
  const [exportConfig, setExportConfig] = useState({
    format: 'json',
    includeInactive: false,
    minSpeed: '',
    maxSpeed: '',
    countries: '',
    protocols: 'all',
    dateRange: '7days'
  });

  const [exportHistory, setExportHistory] = useState([
    {
      id: 1,
      filename: 'proxies_2024-01-15_active.json',
      format: 'JSON',
      size: '2.3 MB',
      records: 1250,
      date: '2024-01-15 14:30:00',
      status: 'completed'
    },
    {
      id: 2,
      filename: 'proxies_2024-01-15_all.csv',
      format: 'CSV',
      size: '1.8 MB',
      records: 890,
      date: '2024-01-15 13:45:00',
      status: 'completed'
    },
    {
      id: 3,
      filename: 'proxies_2024-01-15_filtered.txt',
      format: 'TXT',
      size: '456 KB',
      records: 450,
      date: '2024-01-15 12:20:00',
      status: 'completed'
    }
  ]);

  const handleExport = () => {
    // 導出邏輯
    console.log('導出配置:', exportConfig);
  };

  const formatOptions = [
    { value: 'json', label: 'JSON' },
    { value: 'csv', label: 'CSV' },
    { value: 'txt', label: 'TXT (IP:Port)' },
    { value: 'xml', label: 'XML' }
  ];

  const protocolOptions = [
    { value: 'all', label: '全部協議' },
    { value: 'http', label: 'HTTP' },
    { value: 'https', label: 'HTTPS' },
    { value: 'socks4', label: 'SOCKS4' },
    { value: 'socks5', label: 'SOCKS5' }
  ];

  const dateRangeOptions = [
    { value: '1day', label: '最近1天' },
    { value: '7days', label: '最近7天' },
    { value: '30days', label: '最近30天' },
    { value: 'all', label: '全部時間' }
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">數據導出</h1>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 導出配置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Download className="mr-2 h-5 w-5" />
              導出設定
            </CardTitle>
            <CardDescription>配置代理數據的導出格式和篩選條件</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 導出格式 */}
            <div className="space-y-2">
              <Label htmlFor="format">導出格式</Label>
              <Select
                value={exportConfig.format}
                onValueChange={(value) => setExportConfig({...exportConfig, format: value})}
              >
                {formatOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            {/* 協議類型 */}
            <div className="space-y-2">
              <Label htmlFor="protocols">協議類型</Label>
              <Select
                value={exportConfig.protocols}
                onValueChange={(value) => setExportConfig({...exportConfig, protocols: value})}
              >
                {protocolOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            {/* 時間範圍 */}
            <div className="space-y-2">
              <Label htmlFor="dateRange">時間範圍</Label>
              <Select
                value={exportConfig.dateRange}
                onValueChange={(value) => setExportConfig({...exportConfig, dateRange: value})}
              >
                {dateRangeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            {/* 速度篩選 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="minSpeed">最小速度 (ms)</Label>
                <Input
                  id="minSpeed"
                  type="number"
                  placeholder="0"
                  value={exportConfig.minSpeed}
                  onChange={(e) => setExportConfig({...exportConfig, minSpeed: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxSpeed">最大速度 (ms)</Label>
                <Input
                  id="maxSpeed"
                  type="number"
                  placeholder="5000"
                  value={exportConfig.maxSpeed}
                  onChange={(e) => setExportConfig({...exportConfig, maxSpeed: e.target.value})}
                />
              </div>
            </div>

            {/* 國家篩選 */}
            <div className="space-y-2">
              <Label htmlFor="countries">國家篩選</Label>
              <Input
                id="countries"
                placeholder="例如: US,CN,JP (留空表示全部)"
                value={exportConfig.countries}
                onChange={(e) => setExportConfig({...exportConfig, countries: e.target.value})}
              />
            </div>

            {/* 包含非活躍代理 */}
            <div className="flex items-center space-x-2">
              <Switch
                id="includeInactive"
                checked={exportConfig.includeInactive}
                onCheckedChange={(checked) => setExportConfig({...exportConfig, includeInactive: checked})}
              />
              <Label htmlFor="includeInactive">包含非活躍代理</Label>
            </div>

            <Button onClick={handleExport} className="w-full">
              <Download className="mr-2 h-4 w-4" />
              開始導出
            </Button>
          </CardContent>
        </Card>

        {/* 導出歷史 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="mr-2 h-5 w-5" />
              導出歷史
            </CardTitle>
            <CardDescription>查看和下載之前的導出文件</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {exportHistory.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-8 w-8 text-blue-500" />
                    <div>
                      <p className="font-medium">{item.filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {item.format} • {item.size} • {item.records} 筆記錄
                      </p>
                      <p className="text-xs text-muted-foreground">{item.date}</p>
                    </div>
                  </div>
                  <Button size="sm" variant="outline">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 統計信息 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">可導出代理</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2,847</div>
            <p className="text-xs text-muted-foreground">
              包含所有狀態的代理
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍代理</CardTitle>
            <Filter className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,923</div>
            <p className="text-xs text-muted-foreground">
              通過最近檢測的代理
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日導出</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">
              今日導出文件數量
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};