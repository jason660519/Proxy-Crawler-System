import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Switch } from '../components/ui/Switch';
import { Select } from '../components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { Badge } from '../components/ui/Badge';
import { Settings, Database, Globe, Shield, Bell, Server, HardDrive, Wifi } from 'lucide-react';

/**
 * 系統設置頁面組件
 * 提供系統配置、數據庫設置、網路配置等功能
 */
export const SystemSettings: React.FC = () => {
  const [generalSettings, setGeneralSettings] = useState({
    systemName: 'Proxy Manager System',
    timezone: 'Asia/Taipei',
    language: 'zh-TW',
    autoBackup: true,
    maintenanceMode: false,
    debugMode: false
  });

  const [databaseSettings, setDatabaseSettings] = useState({
    host: 'localhost',
    port: '5432',
    database: 'proxy_manager',
    username: 'postgres',
    maxConnections: '20',
    connectionTimeout: '30',
    autoVacuum: true
  });

  const [networkSettings, setNetworkSettings] = useState({
    apiPort: '8000',
    webPort: '3000',
    maxRequestsPerMinute: '1000',
    enableCors: true,
    allowedOrigins: 'http://localhost:3000',
    enableHttps: false,
    proxyTimeout: '30'
  });

  const [notificationSettings, setNotificationSettings] = useState({
    emailEnabled: true,
    webhookEnabled: false,
    slackEnabled: false,
    emailHost: 'smtp.gmail.com',
    emailPort: '587',
    emailUsername: '',
    webhookUrl: ''
  });

  const [systemStatus] = useState({
    uptime: '7天 14小時 32分鐘',
    cpuUsage: '23%',
    memoryUsage: '45%',
    diskUsage: '67%',
    networkStatus: 'online',
    databaseStatus: 'connected',
    lastBackup: '2024-01-15 02:00:00'
  });

  const handleSaveGeneral = () => {
    console.log('保存一般設置:', generalSettings);
  };

  const handleSaveDatabase = () => {
    console.log('保存數據庫設置:', databaseSettings);
  };

  const handleSaveNetwork = () => {
    console.log('保存網路設置:', networkSettings);
  };

  const handleSaveNotifications = () => {
    console.log('保存通知設置:', notificationSettings);
  };

  const handleTestConnection = () => {
    console.log('測試數據庫連接');
  };

  const handleBackupNow = () => {
    console.log('立即備份');
  };

  const getStatusBadge = (status: string) => {
    const statusMap: { [key: string]: { variant: string; text: string } } = {
      online: { variant: 'success', text: '在線' },
      connected: { variant: 'success', text: '已連接' },
      offline: { variant: 'destructive', text: '離線' },
      disconnected: { variant: 'destructive', text: '未連接' }
    };
    
    const statusInfo = statusMap[status] || { variant: 'secondary', text: status };
    return <Badge variant={statusInfo.variant as any}>{statusInfo.text}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">系統設置</h1>
      </div>

      {/* 系統狀態概覽 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">系統運行時間</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemStatus.uptime}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU 使用率</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemStatus.cpuUsage}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">記憶體使用率</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemStatus.memoryUsage}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">網路狀態</CardTitle>
            <Wifi className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {getStatusBadge(systemStatus.networkStatus)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="general">一般設置</TabsTrigger>
          <TabsTrigger value="database">數據庫</TabsTrigger>
          <TabsTrigger value="network">網路</TabsTrigger>
          <TabsTrigger value="notifications">通知</TabsTrigger>
        </TabsList>

        {/* 一般設置標籤 */}
        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="mr-2 h-5 w-5" />
                一般設置
              </CardTitle>
              <CardDescription>配置系統的基本設置和行為</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="systemName">系統名稱</Label>
                <Input
                  id="systemName"
                  value={generalSettings.systemName}
                  onChange={(e) => setGeneralSettings({...generalSettings, systemName: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="timezone">時區</Label>
                <Select
                  value={generalSettings.timezone}
                  onValueChange={(value) => setGeneralSettings({...generalSettings, timezone: value})}
                >
                  <option value="Asia/Taipei">Asia/Taipei (UTC+8)</option>
                  <option value="UTC">UTC (UTC+0)</option>
                  <option value="America/New_York">America/New_York (UTC-5)</option>
                  <option value="Europe/London">Europe/London (UTC+0)</option>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="language">語言</Label>
                <Select
                  value={generalSettings.language}
                  onValueChange={(value) => setGeneralSettings({...generalSettings, language: value})}
                >
                  <option value="zh-TW">繁體中文</option>
                  <option value="zh-CN">简体中文</option>
                  <option value="en-US">English</option>
                  <option value="ja-JP">日本語</option>
                </Select>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="autoBackup"
                  checked={generalSettings.autoBackup}
                  onCheckedChange={(checked) => setGeneralSettings({...generalSettings, autoBackup: checked})}
                />
                <Label htmlFor="autoBackup">自動備份</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="maintenanceMode"
                  checked={generalSettings.maintenanceMode}
                  onCheckedChange={(checked) => setGeneralSettings({...generalSettings, maintenanceMode: checked})}
                />
                <Label htmlFor="maintenanceMode">維護模式</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="debugMode"
                  checked={generalSettings.debugMode}
                  onCheckedChange={(checked) => setGeneralSettings({...generalSettings, debugMode: checked})}
                />
                <Label htmlFor="debugMode">調試模式</Label>
              </div>

              <div className="flex space-x-2">
                <Button onClick={handleSaveGeneral}>保存設置</Button>
                <Button onClick={handleBackupNow} variant="outline">
                  立即備份
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 數據庫設置標籤 */}
        <TabsContent value="database" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="mr-2 h-5 w-5" />
                數據庫設置
              </CardTitle>
              <CardDescription>配置數據庫連接和性能參數</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="dbHost">主機地址</Label>
                  <Input
                    id="dbHost"
                    value={databaseSettings.host}
                    onChange={(e) => setDatabaseSettings({...databaseSettings, host: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dbPort">端口</Label>
                  <Input
                    id="dbPort"
                    value={databaseSettings.port}
                    onChange={(e) => setDatabaseSettings({...databaseSettings, port: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="dbName">數據庫名稱</Label>
                <Input
                  id="dbName"
                  value={databaseSettings.database}
                  onChange={(e) => setDatabaseSettings({...databaseSettings, database: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="dbUsername">用戶名</Label>
                <Input
                  id="dbUsername"
                  value={databaseSettings.username}
                  onChange={(e) => setDatabaseSettings({...databaseSettings, username: e.target.value})}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="maxConnections">最大連接數</Label>
                  <Input
                    id="maxConnections"
                    type="number"
                    value={databaseSettings.maxConnections}
                    onChange={(e) => setDatabaseSettings({...databaseSettings, maxConnections: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="connectionTimeout">連接超時 (秒)</Label>
                  <Input
                    id="connectionTimeout"
                    type="number"
                    value={databaseSettings.connectionTimeout}
                    onChange={(e) => setDatabaseSettings({...databaseSettings, connectionTimeout: e.target.value})}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="autoVacuum"
                  checked={databaseSettings.autoVacuum}
                  onCheckedChange={(checked) => setDatabaseSettings({...databaseSettings, autoVacuum: checked})}
                />
                <Label htmlFor="autoVacuum">自動清理</Label>
              </div>

              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium">數據庫狀態</p>
                  <p className="text-sm text-muted-foreground">最後備份: {systemStatus.lastBackup}</p>
                </div>
                {getStatusBadge(systemStatus.databaseStatus)}
              </div>

              <div className="flex space-x-2">
                <Button onClick={handleSaveDatabase}>保存設置</Button>
                <Button onClick={handleTestConnection} variant="outline">
                  測試連接
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 網路設置標籤 */}
        <TabsContent value="network" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Globe className="mr-2 h-5 w-5" />
                網路設置
              </CardTitle>
              <CardDescription>配置API和Web服務的網路參數</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="apiPort">API 端口</Label>
                  <Input
                    id="apiPort"
                    value={networkSettings.apiPort}
                    onChange={(e) => setNetworkSettings({...networkSettings, apiPort: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="webPort">Web 端口</Label>
                  <Input
                    id="webPort"
                    value={networkSettings.webPort}
                    onChange={(e) => setNetworkSettings({...networkSettings, webPort: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="maxRequests">每分鐘最大請求數</Label>
                <Input
                  id="maxRequests"
                  type="number"
                  value={networkSettings.maxRequestsPerMinute}
                  onChange={(e) => setNetworkSettings({...networkSettings, maxRequestsPerMinute: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="allowedOrigins">允許的來源</Label>
                <Input
                  id="allowedOrigins"
                  value={networkSettings.allowedOrigins}
                  onChange={(e) => setNetworkSettings({...networkSettings, allowedOrigins: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="proxyTimeout">代理超時 (秒)</Label>
                <Input
                  id="proxyTimeout"
                  type="number"
                  value={networkSettings.proxyTimeout}
                  onChange={(e) => setNetworkSettings({...networkSettings, proxyTimeout: e.target.value})}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="enableCors"
                  checked={networkSettings.enableCors}
                  onCheckedChange={(checked) => setNetworkSettings({...networkSettings, enableCors: checked})}
                />
                <Label htmlFor="enableCors">啟用 CORS</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="enableHttps"
                  checked={networkSettings.enableHttps}
                  onCheckedChange={(checked) => setNetworkSettings({...networkSettings, enableHttps: checked})}
                />
                <Label htmlFor="enableHttps">啟用 HTTPS</Label>
              </div>

              <Button onClick={handleSaveNetwork}>保存設置</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 通知設置標籤 */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="mr-2 h-5 w-5" />
                通知設置
              </CardTitle>
              <CardDescription>配置系統通知和警報</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="emailEnabled"
                  checked={notificationSettings.emailEnabled}
                  onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, emailEnabled: checked})}
                />
                <Label htmlFor="emailEnabled">啟用電子郵件通知</Label>
              </div>

              {notificationSettings.emailEnabled && (
                <div className="space-y-4 pl-6 border-l-2 border-muted">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="emailHost">SMTP 主機</Label>
                      <Input
                        id="emailHost"
                        value={notificationSettings.emailHost}
                        onChange={(e) => setNotificationSettings({...notificationSettings, emailHost: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="emailPort">SMTP 端口</Label>
                      <Input
                        id="emailPort"
                        value={notificationSettings.emailPort}
                        onChange={(e) => setNotificationSettings({...notificationSettings, emailPort: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="emailUsername">SMTP 用戶名</Label>
                    <Input
                      id="emailUsername"
                      value={notificationSettings.emailUsername}
                      onChange={(e) => setNotificationSettings({...notificationSettings, emailUsername: e.target.value})}
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Switch
                  id="webhookEnabled"
                  checked={notificationSettings.webhookEnabled}
                  onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, webhookEnabled: checked})}
                />
                <Label htmlFor="webhookEnabled">啟用 Webhook 通知</Label>
              </div>

              {notificationSettings.webhookEnabled && (
                <div className="space-y-2 pl-6 border-l-2 border-muted">
                  <Label htmlFor="webhookUrl">Webhook URL</Label>
                  <Input
                    id="webhookUrl"
                    value={notificationSettings.webhookUrl}
                    onChange={(e) => setNotificationSettings({...notificationSettings, webhookUrl: e.target.value})}
                  />
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Switch
                  id="slackEnabled"
                  checked={notificationSettings.slackEnabled}
                  onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, slackEnabled: checked})}
                />
                <Label htmlFor="slackEnabled">啟用 Slack 通知</Label>
              </div>

              <Button onClick={handleSaveNotifications}>保存設置</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};