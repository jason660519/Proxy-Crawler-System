import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Switch } from '../components/ui/Switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/Select';
import { Textarea } from '../components/ui/Textarea';
import { Save, RefreshCw, Download, Upload, AlertTriangle } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

interface GeneralSettings {
  language: string;
  theme: string;
  autoRefresh: boolean;
  refreshInterval: number;
  notifications: boolean;
}

interface ProxySettings {
  maxConcurrent: number;
  timeout: number;
  retryAttempts: number;
  userAgent: string;
  customHeaders: string;
}

interface SecuritySettings {
  enableAuth: boolean;
  apiKey: string;
  allowedIPs: string;
  logLevel: string;
}

/**
 * 設置頁面組件
 * 管理應用程序的各種配置選項
 */
export const Settings: React.FC = () => {
  const { theme, setTheme } = useTheme();
  
  const [generalSettings, setGeneralSettings] = useState<GeneralSettings>({
    language: 'zh-TW',
    theme: theme,
    autoRefresh: true,
    refreshInterval: 30,
    notifications: true
  });
  
  const [proxySettings, setProxySettings] = useState<ProxySettings>({
    maxConcurrent: 10,
    timeout: 5000,
    retryAttempts: 3,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    customHeaders: '{}'
  });
  
  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>({
    enableAuth: false,
    apiKey: '',
    allowedIPs: '127.0.0.1,::1',
    logLevel: 'info'
  });
  
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const handleSaveSettings = () => {
    // 這裡應該調用API保存設置
    console.log('保存設置:', { generalSettings, proxySettings, securitySettings });
    setHasUnsavedChanges(false);
    // 顯示成功消息
  };

  const handleResetSettings = () => {
    // 重置為默認值
    setGeneralSettings({
      language: 'zh-TW',
      theme: 'system',
      autoRefresh: true,
      refreshInterval: 30,
      notifications: true
    });
    setProxySettings({
      maxConcurrent: 10,
      timeout: 5000,
      retryAttempts: 3,
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      customHeaders: '{}'
    });
    setSecuritySettings({
      enableAuth: false,
      apiKey: '',
      allowedIPs: '127.0.0.1,::1',
      logLevel: 'info'
    });
    setHasUnsavedChanges(true);
  };

  const handleExportSettings = () => {
    const settings = { generalSettings, proxySettings, securitySettings };
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'proxy-manager-settings.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImportSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const settings = JSON.parse(e.target?.result as string);
          if (settings.generalSettings) setGeneralSettings(settings.generalSettings);
          if (settings.proxySettings) setProxySettings(settings.proxySettings);
          if (settings.securitySettings) setSecuritySettings(settings.securitySettings);
          setHasUnsavedChanges(true);
        } catch (error) {
          console.error('導入設置失敗:', error);
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">設置</h1>
        <div className="flex items-center space-x-2">
          {hasUnsavedChanges && (
            <div className="flex items-center space-x-1 text-amber-600">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">有未保存的更改</span>
            </div>
          )}
          <Button variant="outline" onClick={handleResetSettings}>
            <RefreshCw className="h-4 w-4 mr-2" />
            重置
          </Button>
          <Button onClick={handleSaveSettings}>
            <Save className="h-4 w-4 mr-2" />
            保存設置
          </Button>
        </div>
      </div>
      
      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">一般設置</TabsTrigger>
          <TabsTrigger value="proxy">代理設置</TabsTrigger>
          <TabsTrigger value="security">安全設置</TabsTrigger>
          <TabsTrigger value="backup">備份與恢復</TabsTrigger>
        </TabsList>
        
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>界面設置</CardTitle>
              <CardDescription>自定義應用程序的外觀和行為</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="language">語言</Label>
                  <Select 
                    value={generalSettings.language}
                    onValueChange={(value) => {
                      setGeneralSettings(prev => ({ ...prev, language: value }));
                      setHasUnsavedChanges(true);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="zh-TW">繁體中文</SelectItem>
                      <SelectItem value="zh-CN">简体中文</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="ja">日本語</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="theme">主題</Label>
                  <Select 
                    value={generalSettings.theme}
                    onValueChange={(value) => {
                      setGeneralSettings(prev => ({ ...prev, theme: value }));
                      setTheme(value as 'light' | 'dark' | 'system');
                      setHasUnsavedChanges(true);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">淺色</SelectItem>
                      <SelectItem value="dark">深色</SelectItem>
                      <SelectItem value="system">跟隨系統</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>自動刷新</Label>
                    <p className="text-sm text-muted-foreground">自動刷新代理狀態</p>
                  </div>
                  <Switch 
                    checked={generalSettings.autoRefresh}
                    onCheckedChange={(checked) => {
                      setGeneralSettings(prev => ({ ...prev, autoRefresh: checked }));
                      setHasUnsavedChanges(true);
                    }}
                  />
                </div>
                
                {generalSettings.autoRefresh && (
                  <div className="space-y-2">
                    <Label htmlFor="refreshInterval">刷新間隔 (秒)</Label>
                    <Input
                      id="refreshInterval"
                      type="number"
                      min="5"
                      max="300"
                      value={generalSettings.refreshInterval}
                      onChange={(e) => {
                        setGeneralSettings(prev => ({ ...prev, refreshInterval: parseInt(e.target.value) }));
                        setHasUnsavedChanges(true);
                      }}
                    />
                  </div>
                )}
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>桌面通知</Label>
                    <p className="text-sm text-muted-foreground">啟用系統通知</p>
                  </div>
                  <Switch 
                    checked={generalSettings.notifications}
                    onCheckedChange={(checked) => {
                      setGeneralSettings(prev => ({ ...prev, notifications: checked }));
                      setHasUnsavedChanges(true);
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="proxy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>代理配置</CardTitle>
              <CardDescription>配置代理檢測和管理參數</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="maxConcurrent">最大併發數</Label>
                  <Input
                    id="maxConcurrent"
                    type="number"
                    min="1"
                    max="100"
                    value={proxySettings.maxConcurrent}
                    onChange={(e) => {
                      setProxySettings(prev => ({ ...prev, maxConcurrent: parseInt(e.target.value) }));
                      setHasUnsavedChanges(true);
                    }}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="timeout">超時時間 (毫秒)</Label>
                  <Input
                    id="timeout"
                    type="number"
                    min="1000"
                    max="30000"
                    value={proxySettings.timeout}
                    onChange={(e) => {
                      setProxySettings(prev => ({ ...prev, timeout: parseInt(e.target.value) }));
                      setHasUnsavedChanges(true);
                    }}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="retryAttempts">重試次數</Label>
                  <Input
                    id="retryAttempts"
                    type="number"
                    min="0"
                    max="10"
                    value={proxySettings.retryAttempts}
                    onChange={(e) => {
                      setProxySettings(prev => ({ ...prev, retryAttempts: parseInt(e.target.value) }));
                      setHasUnsavedChanges(true);
                    }}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="userAgent">User Agent</Label>
                <Input
                  id="userAgent"
                  value={proxySettings.userAgent}
                  onChange={(e) => {
                    setProxySettings(prev => ({ ...prev, userAgent: e.target.value }));
                    setHasUnsavedChanges(true);
                  }}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="customHeaders">自定義請求頭 (JSON)</Label>
                <Textarea
                  id="customHeaders"
                  placeholder='{"X-Custom-Header": "value"}'
                  value={proxySettings.customHeaders}
                  onChange={(e) => {
                    setProxySettings(prev => ({ ...prev, customHeaders: e.target.value }));
                    setHasUnsavedChanges(true);
                  }}
                  rows={4}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>安全設置</CardTitle>
              <CardDescription>配置API訪問和安全選項</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>啟用API認證</Label>
                  <p className="text-sm text-muted-foreground">要求API密鑰進行訪問</p>
                </div>
                <Switch 
                  checked={securitySettings.enableAuth}
                  onCheckedChange={(checked) => {
                    setSecuritySettings(prev => ({ ...prev, enableAuth: checked }));
                    setHasUnsavedChanges(true);
                  }}
                />
              </div>
              
              {securitySettings.enableAuth && (
                <div className="space-y-2">
                  <Label htmlFor="apiKey">API密鑰</Label>
                  <Input
                    id="apiKey"
                    type="password"
                    value={securitySettings.apiKey}
                    onChange={(e) => {
                      setSecuritySettings(prev => ({ ...prev, apiKey: e.target.value }));
                      setHasUnsavedChanges(true);
                    }}
                    placeholder="輸入API密鑰"
                  />
                </div>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="allowedIPs">允許的IP地址</Label>
                <Textarea
                  id="allowedIPs"
                  value={securitySettings.allowedIPs}
                  onChange={(e) => {
                    setSecuritySettings(prev => ({ ...prev, allowedIPs: e.target.value }));
                    setHasUnsavedChanges(true);
                  }}
                  placeholder="127.0.0.1,::1,192.168.1.0/24"
                  rows={3}
                />
                <p className="text-sm text-muted-foreground">
                  每行一個IP地址或CIDR範圍
                </p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="logLevel">日誌級別</Label>
                <Select 
                  value={securitySettings.logLevel}
                  onValueChange={(value) => {
                    setSecuritySettings(prev => ({ ...prev, logLevel: value }));
                    setHasUnsavedChanges(true);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="debug">Debug</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="warning">Warning</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="backup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>備份與恢復</CardTitle>
              <CardDescription>導出和導入應用程序設置</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-medium">導出設置</h3>
                  <p className="text-sm text-muted-foreground">將當前設置保存為JSON文件</p>
                </div>
                <Button onClick={handleExportSettings}>
                  <Download className="h-4 w-4 mr-2" />
                  導出
                </Button>
              </div>
              
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-medium">導入設置</h3>
                  <p className="text-sm text-muted-foreground">從JSON文件恢復設置</p>
                </div>
                <div>
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleImportSettings}
                    className="hidden"
                    id="import-settings"
                  />
                  <Button asChild>
                    <label htmlFor="import-settings" className="cursor-pointer">
                      <Upload className="h-4 w-4 mr-2" />
                      導入
                    </label>
                  </Button>
                </div>
              </div>
              
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-amber-800">注意事項</h4>
                    <p className="text-sm text-amber-700 mt-1">
                      導入設置將覆蓋當前配置。請確保備份文件來自可信來源，並在導入前備份當前設置。
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;