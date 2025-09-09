import React, { useState, useEffect } from 'react';
import { Typography } from '../components/ui/Typography';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Space } from '../components/ui/Space';
import { apiClient } from '../services/http';

interface ProxyInfo {
  ip: string;
  port: number;
  country_code: string;
  country_name: string;
  anonymity: string;
  google_support: boolean;
  https_support: boolean;
  last_checked: string;
  source_url?: string; // 添加來源URL
}

interface JobResult {
  job_id: string;
  status: string;
  result?: {
    files: Array<{
      format: string;
      path: string;
      size: number;
    }>;
  };
  urls: string[];
}

const UrlToParquetWizard: React.FC = () => {
  // 預設四個URL輸入框
  const [urls, setUrls] = useState<string[]>([
    'https://free-proxy-list.net/',
    'https://www.sslproxies.org/',
    'https://www.us-proxy.org/',
    'https://www.proxy-list.download/HTTP'
  ]);
  const [results, setResults] = useState<JobResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [proxyList, setProxyList] = useState<ProxyInfo[]>([]);
  const [markdownContents, setMarkdownContents] = useState<{[key: string]: string}>({});
  const [redirects, setRedirects] = useState<any[]>([]);
  const [showRedirectDialog, setShowRedirectDialog] = useState(false);

  // 解析 Markdown 中的代理表格
  const parseProxyTable = (markdown: string, sourceUrl?: string): ProxyInfo[] => {
    const lines = markdown.split('\n');
    const proxyList: ProxyInfo[] = [];
    
    // 找到表格開始位置 - 支援多種表格格式
    let tableStart = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('| IP Address | Port | Code | Country |') ||
          lines[i].includes('| IP | Port |') ||
          lines[i].includes('| IP Address | Port |')) {
        tableStart = i + 2; // 跳過標題行和分隔行
        break;
      }
    }
    
    if (tableStart === -1) return proxyList;
    
    // 解析表格行
    for (let i = tableStart; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line.startsWith('|') || line === '') break;
      
      const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell !== '');
      if (cells.length >= 6) { // 降低最小要求
        try {
          const proxy: ProxyInfo = {
            ip: cells[0],
            port: parseInt(cells[1]) || 0,
            country_code: cells[2] || '',
            country_name: cells[3] || '',
            anonymity: cells[4] || '',
            google_support: cells[5] === 'yes' || cells[5] === 'Yes',
            https_support: cells[6] === 'yes' || cells[6] === 'Yes',
            last_checked: cells[7] || '',
            source_url: sourceUrl
          };
          proxyList.push(proxy);
        } catch (e) {
          console.warn('解析代理行失敗:', line);
        }
      }
    }
    
    return proxyList;
  };

  // 添加URL輸入框
  const addUrl = () => {
    setUrls([...urls, '']);
  };

  // 移除URL輸入框
  const removeUrl = (index: number) => {
    if (urls.length > 1) {
      const newUrls = urls.filter((_, i) => i !== index);
      setUrls(newUrls);
    }
  };

  // 更新URL
  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const onSubmit = async () => {
    setLoading(true);
    setError(null);
    setResults([]);
    setProxyList([]);
    setMarkdownContents({});
    setRedirects([]);
    setShowRedirectDialog(false);
    
    // 過濾掉空的URL
    const validUrls = urls.filter(url => url.trim() !== '');
    if (validUrls.length === 0) {
      setError('請至少輸入一個有效的URL');
      setLoading(false);
      return;
    }
    
    try {
      const data = await apiClient.post<any>('/api/url2parquet/jobs', { 
        urls: validUrls, 
        output_formats: ['md', 'json', 'parquet'],
        timeout_seconds: 30
      });
      
      // 檢查是否為重定向響應
      if (data.status === 'redirected' && data.redirects) {
        setRedirects(data.redirects);
        setShowRedirectDialog(true);
        setLoading(false);
        return;
      }
      
      const jobResult: JobResult = {
        job_id: data.job_id,
        status: data.status,
        result: data.result,
        urls: validUrls
      };
      
      setResults([jobResult]);
      
      // 如果有文件資訊，嘗試獲取 Markdown 內容
      if (data.result && data.result.files) {
        const mdFile = data.result.files.find((file: any) => file.format === 'md');
        if (mdFile && data.job_id) {
          try {
            // 獲取 Markdown 文件內容
            const fileResponse = await apiClient.get(`/api/url2parquet/jobs/${data.job_id}/files/md`);
            setMarkdownContents({ [data.job_id]: fileResponse.content });
          } catch (e) {
            console.warn('無法獲取 Markdown 內容:', e);
            setMarkdownContents({ [data.job_id]: '無法獲取 Markdown 內容' });
          }
        }
      }
    } catch (e: any) {
      setError(e?.message || '轉換失敗');
    } finally {
      setLoading(false);
    }
  };

  // 處理重定向確認
  const handleRedirectConfirm = async () => {
    setLoading(true);
    setShowRedirectDialog(false);
    
    try {
      const redirectUrls = redirects.map(r => r.final_url);
      const data = await apiClient.post(`/api/url2parquet/jobs/${redirects[0].job_id || 'temp'}/confirm-redirect`, redirectUrls);
      
      const jobResult: JobResult = {
        job_id: data.job_id,
        status: data.status,
        result: data.result,
        urls: redirectUrls
      };
      
      setResults([jobResult]);
      
      // 如果有文件資訊，嘗試獲取 Markdown 內容
      if (data.result && data.result.files) {
        const mdFile = data.result.files.find((file: any) => file.format === 'md');
        if (mdFile && data.job_id) {
          try {
            const fileResponse = await apiClient.get(`/api/url2parquet/jobs/${data.job_id}/files/md`);
            setMarkdownContents({ [data.job_id]: fileResponse.content });
          } catch (e) {
            console.warn('無法獲取 Markdown 內容:', e);
            setMarkdownContents({ [data.job_id]: '無法獲取 Markdown 內容' });
          }
        }
      }
    } catch (e: any) {
      setError(e?.message || '重定向處理失敗');
    } finally {
      setLoading(false);
    }
  };

  // 導出功能
  const exportToCSV = () => {
    if (proxyList.length === 0) return;
    
    const headers = ['IP', 'Port', 'Country Code', 'Country Name', 'Anonymity', 'Google Support', 'HTTPS Support', 'Last Checked', 'Source URL'];
    const csvContent = [
      headers.join(','),
      ...proxyList.map(proxy => [
        proxy.ip,
        proxy.port,
        proxy.country_code,
        `"${proxy.country_name}"`,
        proxy.anonymity,
        proxy.google_support ? 'Yes' : 'No',
        proxy.https_support ? 'Yes' : 'No',
        proxy.last_checked,
        proxy.source_url || ''
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `proxy_list_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const exportToJSON = () => {
    if (proxyList.length === 0) return;
    
    const jsonContent = JSON.stringify(proxyList, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `proxy_list_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
  };

  const exportToTXT = () => {
    if (proxyList.length === 0) return;
    
    const txtContent = proxyList.map(proxy => `${proxy.ip}:${proxy.port}`).join('\n');
    const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `proxy_list_${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
  };

  // 下載原始文件
  const downloadOriginalFiles = async () => {
    if (results.length === 0) return;
    
    for (const result of results) {
      if (result.result && result.result.files) {
        for (const file of result.result.files) {
          try {
            const response = await apiClient.get(`/api/url2parquet/jobs/${result.job_id}/files/${file.format}`);
            const blob = new Blob([response.content], { type: 'text/plain;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `${file.format}_${result.job_id}.${file.format}`;
            link.click();
          } catch (e) {
            console.warn(`無法下載文件 ${file.format}:`, e);
          }
        }
      }
    }
  };

  // 當有 Markdown 內容時，解析代理列表
  useEffect(() => {
    const allProxies: ProxyInfo[] = [];
    
    Object.entries(markdownContents).forEach(([jobId, content]) => {
      if (content && content !== '無法獲取 Markdown 內容') {
        const result = results.find(r => r.job_id === jobId);
        const sourceUrl = result?.urls[0] || '';
        const parsed = parseProxyTable(content, sourceUrl);
        allProxies.push(...parsed);
      }
    });
    
    setProxyList(allProxies);
  }, [markdownContents, results]);

  return (
    <Space direction="vertical" size={16}>
      <Typography variant="h3">URL 轉換與代理擷取</Typography>
      
      {/* URL 輸入區域 */}
      <Card>
        <Space direction="vertical" size={12}>
          <Typography variant="h4">代理網站 URL 列表</Typography>
          <Typography color="textSecondary">
            輸入要爬取的代理網站URL，系統會自動轉換為Markdown、JSON、Parquet格式
          </Typography>
          
          {urls.map((url, index) => (
            <div key={index} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Input
                placeholder={`URL ${index + 1} (例如: https://free-proxy-list.net/)`}
            value={url}
                onChange={(e: any) => updateUrl(index, e.target.value)}
                style={{ flex: 1 }}
              />
              {urls.length > 1 && (
                <Button 
                  onClick={() => removeUrl(index)} 
                  size="small" 
                  variant="outline"
                  style={{ color: 'red' }}
                >
                  移除
                </Button>
              )}
            </div>
          ))}
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button onClick={addUrl} variant="outline" size="small">
              + 添加 URL
            </Button>
            <Button 
              onClick={onSubmit} 
              disabled={urls.every(url => url.trim() === '')} 
              loading={loading}
            >
              {loading ? '轉換中...' : `開始轉換 (${urls.filter(url => url.trim() !== '').length} 個URL)`}
            </Button>
          </div>
        </Space>
      </Card>

      {/* 錯誤顯示 */}
      {error && (
        <Card>
          <Typography color="error">{error}</Typography>
        </Card>
      )}

      {/* 重定向對話框 */}
      {showRedirectDialog && (
        <Card>
          <Space direction="vertical" size={16}>
            <Typography variant="h4" color="warning">檢測到URL重定向</Typography>
            <Typography>以下URL發生了重定向，是否繼續測試新的URL？</Typography>
            
            {redirects.map((redirect, index) => (
              <div key={index} style={{ border: '1px solid #e0e0e0', padding: '12px', borderRadius: '4px' }}>
                <Typography variant="h5">重定向 {index + 1}</Typography>
                <Space direction="vertical" size={8}>
                  <Typography><strong>原始URL:</strong> {redirect.original_url}</Typography>
                  <Typography><strong>重定向至:</strong> {redirect.final_url}</Typography>
                  <Typography color="textSecondary">{redirect.message}</Typography>
                </Space>
              </div>
            ))}
            
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button onClick={handleRedirectConfirm} loading={loading}>
                是，繼續測試重定向的URL
              </Button>
              <Button onClick={() => setShowRedirectDialog(false)} variant="outline">
                取消
              </Button>
            </div>
          </Space>
        </Card>
      )}

      {/* 轉換結果 */}
      {results.length > 0 && (
        <Card>
          <Typography variant="h4">轉換結果</Typography>
          <Space direction="vertical" size={12}>
            {results.map((result, index) => (
              <div key={result.job_id} style={{ border: '1px solid #e0e0e0', padding: '12px', borderRadius: '4px' }}>
                <Typography variant="h5">任務 {index + 1}</Typography>
                <Space direction="vertical" size={8}>
                  <Typography>任務 ID: {result.job_id}</Typography>
                  <Typography>狀態: {result.status}</Typography>
                  <Typography>處理的 URL: {result.urls.join(', ')}</Typography>
                  {result.result && result.result.files && (
                    <div>
                      <Typography>生成的文件:</Typography>
                      <ul>
                        {result.result.files.map((file: any, fileIndex: number) => (
                          <li key={fileIndex}>
                            {file.format.toUpperCase()}: {file.path} ({file.size} bytes)
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Space>
              </div>
            ))}
            
            {/* 下載按鈕 */}
            <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
              <Button onClick={downloadOriginalFiles} variant="outline">
                下載原始文件 (MD/JSON/Parquet)
              </Button>
              {proxyList.length > 0 && (
                <>
                  <Button onClick={exportToCSV} variant="outline">
                    下載代理列表 (CSV)
                  </Button>
                  <Button onClick={exportToJSON} variant="outline">
                    下載代理列表 (JSON)
                  </Button>
                  <Button onClick={exportToTXT} variant="outline">
                    下載代理列表 (TXT)
                  </Button>
                </>
              )}
            </div>
          </Space>
        </Card>
      )}

      {/* 代理列表展示 */}
      {proxyList.length > 0 && (
        <Card>
          <Space direction="vertical" size={16}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h4">擷取的代理列表 ({proxyList.length} 個)</Typography>
              <Space>
                <Button onClick={exportToCSV} size="small">導出 CSV</Button>
                <Button onClick={exportToJSON} size="small">導出 JSON</Button>
                <Button onClick={exportToTXT} size="small">導出 TXT</Button>
              </Space>
            </div>
            
            <div style={{ maxHeight: '400px', overflow: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f5f5f5' }}>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>IP 地址</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>端口</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>國家</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>匿名性</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>Google</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>HTTPS</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>最後檢查</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>來源</th>
                  </tr>
                </thead>
                <tbody>
                  {proxyList.map((proxy, index) => (
                    <tr key={index}>
                      <td style={{ padding: '8px', border: '1px solid #ddd', fontFamily: 'monospace' }}>
                        {proxy.ip}
                      </td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{proxy.port}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                        {proxy.country_code} - {proxy.country_name}
                      </td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{proxy.anonymity}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'center' }}>
                        {proxy.google_support ? '✅' : '❌'}
                      </td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'center' }}>
                        {proxy.https_support ? '✅' : '❌'}
                      </td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{proxy.last_checked}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', fontSize: '12px', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {proxy.source_url ? new URL(proxy.source_url).hostname : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Space>
        </Card>
      )}

      {/* 統計資訊 */}
      {proxyList.length > 0 && (
        <Card>
          <Typography variant="h4">統計資訊</Typography>
          <Space direction="vertical" size={8}>
            <Typography>總代理數: {proxyList.length}</Typography>
            <Typography>支援 HTTPS: {proxyList.filter(p => p.https_support).length}</Typography>
            <Typography>支援 Google: {proxyList.filter(p => p.google_support).length}</Typography>
            <Typography>Elite 代理: {proxyList.filter(p => p.anonymity.includes('elite')).length}</Typography>
            <Typography>匿名代理: {proxyList.filter(p => p.anonymity.includes('anonymous')).length}</Typography>
          </Space>
        </Card>
      )}
    </Space>
  );
};

export default UrlToParquetWizard;


