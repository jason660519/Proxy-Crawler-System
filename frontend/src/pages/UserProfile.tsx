import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Avatar } from '../components/ui/Avatar';
import { Badge } from '../components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { User, Mail, Shield, Key, Bell, Activity, Calendar, Settings } from 'lucide-react';

/**
 * 用戶個人資料頁面組件
 * 提供用戶資料管理、安全設置和活動記錄功能
 */
export const UserProfile: React.FC = () => {
  const [userInfo, setUserInfo] = useState({
    username: 'admin',
    email: 'admin@proxymanager.com',
    fullName: '系統管理員',
    role: 'Administrator',
    avatar: '',
    lastLogin: '2024-01-15 14:30:00',
    createdAt: '2023-06-01 10:00:00'
  });

  const [securitySettings, setSecuritySettings] = useState({
    twoFactorEnabled: false,
    emailNotifications: true,
    loginAlerts: true,
    sessionTimeout: '30'
  });

  const [activityLog] = useState([
    {
      id: 1,
      action: '登入系統',
      timestamp: '2024-01-15 14:30:00',
      ip: '192.168.1.100',
      status: 'success'
    },
    {
      id: 2,
      action: '修改代理池設定',
      timestamp: '2024-01-15 13:45:00',
      ip: '192.168.1.100',
      status: 'success'
    },
    {
      id: 3,
      action: '導出代理數據',
      timestamp: '2024-01-15 12:20:00',
      ip: '192.168.1.100',
      status: 'success'
    },
    {
      id: 4,
      action: '嘗試登入失敗',
      timestamp: '2024-01-14 23:15:00',
      ip: '203.0.113.45',
      status: 'failed'
    }
  ]);

  const handleSaveProfile = () => {
    console.log('保存用戶資料:', userInfo);
  };

  const handleSaveSecurity = () => {
    console.log('保存安全設置:', securitySettings);
  };

  const getStatusBadge = (status: string) => {
    return status === 'success' ? (
      <Badge variant="success">成功</Badge>
    ) : (
      <Badge variant="destructive">失敗</Badge>
    );
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">用戶資料</h1>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="profile">個人資料</TabsTrigger>
          <TabsTrigger value="security">安全設置</TabsTrigger>
          <TabsTrigger value="activity">活動記錄</TabsTrigger>
        </TabsList>

        {/* 個人資料標籤 */}
        <TabsContent value="profile" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* 基本資料 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <User className="mr-2 h-5 w-5" />
                  基本資料
                </CardTitle>
                <CardDescription>管理您的個人基本資訊</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-4">
                  <Avatar className="h-20 w-20">
                    <div className="flex h-full w-full items-center justify-center bg-muted">
                      <User className="h-10 w-10" />
                    </div>
                  </Avatar>
                  <Button variant="outline">更換頭像</Button>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="fullName">姓名</Label>
                  <Input
                    id="fullName"
                    value={userInfo.fullName}
                    onChange={(e) => setUserInfo({...userInfo, fullName: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username">用戶名</Label>
                  <Input
                    id="username"
                    value={userInfo.username}
                    onChange={(e) => setUserInfo({...userInfo, username: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">電子郵件</Label>
                  <Input
                    id="email"
                    type="email"
                    value={userInfo.email}
                    onChange={(e) => setUserInfo({...userInfo, email: e.target.value})}
                  />
                </div>

                <Button onClick={handleSaveProfile} className="w-full">
                  保存變更
                </Button>
              </CardContent>
            </Card>

            {/* 帳戶資訊 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="mr-2 h-5 w-5" />
                  帳戶資訊
                </CardTitle>
                <CardDescription>查看您的帳戶狀態和權限</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">角色權限</span>
                  <Badge variant="default">{userInfo.role}</Badge>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">帳戶狀態</span>
                  <Badge variant="success">正常</Badge>
                </div>

                <div className="space-y-2">
                  <Label>最後登入時間</Label>
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{userInfo.lastLogin}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>帳戶創建時間</Label>
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{userInfo.createdAt}</span>
                  </div>
                </div>

                <Button variant="outline" className="w-full">
                  <Key className="mr-2 h-4 w-4" />
                  修改密碼
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 安全設置標籤 */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="mr-2 h-5 w-5" />
                安全設置
              </CardTitle>
              <CardDescription>管理您的帳戶安全選項</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>雙重驗證</Label>
                  <p className="text-sm text-muted-foreground">為您的帳戶添加額外的安全層</p>
                </div>
                <Button variant={securitySettings.twoFactorEnabled ? "default" : "outline"}>
                  {securitySettings.twoFactorEnabled ? '已啟用' : '啟用'}
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>電子郵件通知</Label>
                  <p className="text-sm text-muted-foreground">接收重要的帳戶活動通知</p>
                </div>
                <Button variant={securitySettings.emailNotifications ? "default" : "outline"}>
                  {securitySettings.emailNotifications ? '已啟用' : '啟用'}
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>登入警報</Label>
                  <p className="text-sm text-muted-foreground">當有新設備登入時發送警報</p>
                </div>
                <Button variant={securitySettings.loginAlerts ? "default" : "outline"}>
                  {securitySettings.loginAlerts ? '已啟用' : '啟用'}
                </Button>
              </div>

              <div className="space-y-2">
                <Label htmlFor="sessionTimeout">會話超時 (分鐘)</Label>
                <Input
                  id="sessionTimeout"
                  type="number"
                  value={securitySettings.sessionTimeout}
                  onChange={(e) => setSecuritySettings({...securitySettings, sessionTimeout: e.target.value})}
                />
              </div>

              <Button onClick={handleSaveSecurity} className="w-full">
                保存安全設置
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 活動記錄標籤 */}
        <TabsContent value="activity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="mr-2 h-5 w-5" />
                活動記錄
              </CardTitle>
              <CardDescription>查看您的帳戶活動歷史</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activityLog.map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Activity className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="font-medium">{activity.action}</p>
                        <p className="text-sm text-muted-foreground">
                          {activity.timestamp} • IP: {activity.ip}
                        </p>
                      </div>
                    </div>
                    {getStatusBadge(activity.status)}
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