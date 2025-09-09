import React, { useState, useEffect } from 'react';
import { Typography } from '../components/ui/Typography';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Space } from '../components/ui/Space';
import { apiClient } from '../services/http';
import http from '../services/http';
import * as url2parquetApi from '../api/url2parquetApi';

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
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [pendingJobId, setPendingJobId] = useState<string | null>(null);
  const [urlStatusMap, setUrlStatusMap] = useState<Record<string, 'pending' | 'redirected' | 'completed' | 'failed'>>({});
  const [localMdFiles, setLocalMdFiles] = useState<Array<{ filename: string; size: number; modified: number }>>([]);
  const [localMdLoading, setLocalMdLoading] = useState(false);

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
      // 使用新的 API 封裝，確保 output_formats 正確傳遞
      const data = await url2parquetApi.createJob({
        urls: validUrls,
        output_formats: ['md', 'json', 'parquet', 'csv'], // 明確包含所有格式
        timeout_seconds: 60,
        engine: 'smart',
        obey_robots_txt: true,
        max_concurrency: 4
      });
      
      // 檢查是否為重定向響應
      if (url2parquetApi.isRedirectResponse(data)) {
        setPendingJobId(data.job_id);
        // 標記原始 URL 為 redirected
        const next: Record<string, any> = { ...urlStatusMap };
        (data.redirects as any[]).forEach(r => {
          next[r.original_url] = 'redirected';
        });
        setUrlStatusMap(next);
        setRedirects(data.redirects || []);
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
      // 啟動檔案清單輪詢（避免後端尚未立即寫入 files）
      startPollingFiles(jobResult.job_id);
      setPendingJobId(jobResult.job_id);
      // 標記第一個 URL 完成（後端目前回傳第一筆成功結果）
      if (validUrls[0]) {
        setUrlStatusMap(prev => ({ ...prev, [validUrls[0]]: 'completed' }));
      }
      
      // 嘗試立即獲取 Markdown（若已有 files）
      tryFetchMarkdownIfReady(data.job_id, data.result?.files || []);
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
      const jobId = pendingJobId || '';
      
      // 使用新的 API 封裝
      const data = await url2parquetApi.confirmRedirect(jobId, redirectUrls);
      
      const jobResult: JobResult = {
        job_id: data.job_id,
        status: data.status,
        result: data.result,
        urls: redirectUrls
      };
      
      setResults([jobResult]);
      // 重定向確認後同樣輪詢檔案清單
      startPollingFiles(jobResult.job_id);
      setPendingJobId(jobResult.job_id);
      // 標記重定向後第一個 URL 為完成
      if (redirectUrls[0]) {
        setUrlStatusMap(prev => ({ ...prev, [redirectUrls[0]]: 'completed' }));
      }
      
      tryFetchMarkdownIfReady(data.job_id, data.result?.files || []);
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
        try {
          // 使用新的 API 封裝批量下載
          await url2parquetApi.downloadAllFiles(result.job_id, result.result.files);
        } catch (e) {
          console.warn(`批量下載文件失敗:`, e);
        }
      }
    }
  };

  // 本地 Markdown 上傳解析
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const handleUploadLocalMd = () => fileInputRef.current?.click();
  const onLocalMdSelected: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const localId = `local_${Date.now()}`;
      setMarkdownContents(prev => ({ ...prev, [localId]: text }));
      const parsed = parseProxyTable(text, undefined);
      if (parsed.length > 0) {
        setProxyList(prev => [...prev, ...parsed]);
      }
    } catch (err) {
      console.warn('讀取本地 Markdown 失敗', err);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // 從後端列出 outputs 內的 Markdown 檔案
  const fetchLocalMdList = async () => {
    setLocalMdLoading(true);
    try {
      const data = await url2parquetApi.getLocalMarkdownFiles('data/url2parquet', 50);
      setLocalMdFiles(data.files);
    } catch (err) {
      console.warn('列出本地 Markdown 失敗', err);
      setLocalMdFiles([]);
    } finally {
      setLocalMdLoading(false);
    }
  };

  const loadLocalMdContent = async (filename: string) => {
    try {
      const data = await url2parquetApi.getLocalMarkdownContent(filename, 'data/url2parquet');
      const localId = `local_${Date.now()}`;
      setMarkdownContents(prev => ({ ...prev, [localId]: data.content }));
    } catch (err) {
      console.warn('讀取本地 Markdown 內容失敗', err);
    }
  };

  // 針對單一檔案提供立即下載按鈕
  const handleDownloadSingle = async (jobId: string, format: string) => {
    try {
      await url2parquetApi.downloadFile(jobId, format, `${format}_${jobId}.${format}`);
    } catch (e) {
      console.warn(`無法下載文件 ${format}:`, e);
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

  // ====== 輪詢與刷新邏輯 ======
  const updateResultFiles = (jobId: string, files: Array<{ format: string; path: string; size: number }>) => {
    if (!files || files.length === 0) return;
    setResults(prev => prev.map(r => r.job_id === jobId ? { ...r, result: { ...(r.result || {}), files } } as any : r));
    // 有了 files 後自動嘗試載入 Markdown
    tryFetchMarkdownIfReady(jobId, files);
  };

  const tryFetchMarkdownIfReady = async (jobId: string, files: Array<{ format: string }>) => {
    const hasMd = Array.isArray(files) && files.some(f => f.format === 'md');
    if (!hasMd || !jobId) return;
    if (markdownContents[jobId]) return; // 已載入過
    try {
      const fileResponse = await url2parquetApi.getFileContent(jobId, 'md');
      setMarkdownContents(prev => ({ ...prev, [jobId]: fileResponse.content }));
    } catch (e) {
      console.warn('無法獲取 Markdown 內容:', e);
      setMarkdownContents(prev => ({ ...prev, [jobId]: '無法獲取 Markdown 內容' }));
    }
  };

  const fetchJobFilesOnce = async (jobId: string) => {
    try {
      // 使用新的 API 封裝
      const { files } = await url2parquetApi.getJobFiles(jobId);
      if (files && files.length > 0) {
        updateResultFiles(jobId, files);
        return true;
      }

      // 回退查詢任務狀態
      const job = await url2parquetApi.getJob(jobId);
      const jobFiles = job?.result?.files || [];
      if (jobFiles && jobFiles.length > 0) {
        updateResultFiles(jobId, jobFiles);
        return true;
      }
    } catch (e) {
      console.warn('刷新檔案清單失敗:', e);
    }
    return false;
  };

  const startPollingFiles = async (jobId: string) => {
    if (!jobId || isPolling) return;
    setIsPolling(true);
    
    try {
      // 使用新的 API 封裝的輪詢工具
      await url2parquetApi.pollJobFilesUntilReady(
        jobId,
        (files) => {
          updateResultFiles(jobId, files);
        },
        {
          interval: 2000,
          timeout: 60000,
          maxAttempts: 30
        }
      );
    } catch (error) {
      console.warn('輪詢文件失敗:', error);
    } finally {
      setIsPolling(false);
    }
  };

  return (
    <>
    <Space direction="vertical" size={16}>
      <Typography variant="h3">URL 轉換與代理擷取</Typography>
      
      {/* URL 輸入區域 */}
      <Card>
        <Space direction="vertical" size={12}>
          <Typography variant="h4">代理網站 URL 列表</Typography>
          <Typography color="secondary">
            輸入要爬取的代理網站URL，系統會自動轉換為Markdown、JSON、Parquet格式
          </Typography>
          {/* 簡易 URL 狀態列 */}
          {urls.some(u => urlStatusMap[u]) && (
            <div style={{ fontSize: 12, color: '#666' }}>
              {urls.map(u => (
                <div key={u}>
                  <strong>{u}</strong>：{urlStatusMap[u] === 'completed' ? '完成' : urlStatusMap[u] === 'redirected' ? '已重定向，等待確認' : urlStatusMap[u] === 'failed' ? '失敗' : '待處理'}
                </div>
              ))}
            </div>
          )}
          
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
                  size="sm" 
                  variant="outline"
                  style={{ color: 'red' }}
                >
                  移除
                </Button>
              )}
            </div>
          ))}
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button onClick={addUrl} variant="outline" size="sm">
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
                  <Typography color="secondary">{redirect.message}</Typography>
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
                  {result.result && result.result.files && result.result.files.length > 0 ? (
                    <div>
                      <Typography>生成的文件:</Typography>
                      <ul>
                        {result.result.files.map((file: any, fileIndex: number) => (
                          <li key={fileIndex} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span>{file.format.toUpperCase()}: {file.path} ({file.size} bytes)</span>
                            <Button size="sm" variant="outline" onClick={() => handleDownloadSingle(result.job_id, file.format)}>
                              下載
                            </Button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <div>
                      <Typography color="secondary">尚未生成檔案清單，可能仍在處理或寫入中。</Typography>
                      <Space>
                        <Button size="sm" variant="outline" onClick={() => fetchJobFilesOnce(result.job_id)} disabled={loading}>
                          刷新檔案清單
                        </Button>
                        {!isPolling && (
                          <Button size="sm" onClick={() => startPollingFiles(result.job_id)}>
                            啟動自動刷新
                          </Button>
                        )}
                        {isPolling && (
                          <Typography color="secondary">自動刷新中...</Typography>
                        )}
                      </Space>
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
              <Button onClick={handleUploadLocalMd} variant="outline">
                上傳本地 Markdown 並解析
              </Button>
              <Button onClick={fetchLocalMdList} variant="outline" loading={localMdLoading}>
                載入本地 outputs 清單
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

      {/* 本地 outputs 檔案清單 */}
      {localMdFiles.length > 0 && (
        <Card>
          <Space direction="vertical" size={12}>
            <Typography variant="h4">本地 Markdown 檔案（outputs）</Typography>
            <ul>
              {localMdFiles.map((f, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontFamily: 'monospace' }}>{f.filename}</span>
                  <span style={{ color: '#888', fontSize: 12 }}>({Math.round(f.size / 1024)} KB)</span>
                  <Button size="sm" variant="outline" onClick={() => loadLocalMdContent(f.filename)}>
                    載入並解析
                  </Button>
                </li>
              ))}
            </ul>
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
                <Button onClick={exportToCSV} size="sm">導出 CSV</Button>
                <Button onClick={exportToJSON} size="sm">導出 JSON</Button>
                <Button onClick={exportToTXT} size="sm">導出 TXT</Button>
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
    <input ref={fileInputRef} type="file" accept=".md,text/markdown" style={{ display: 'none' }} onChange={onLocalMdSelected} />
  </>
  );
};

export default UrlToParquetWizard;


