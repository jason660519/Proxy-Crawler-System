/**
 * CSV 導入模態框組件
 * 
 * 提供代理IP的CSV檔案導入功能，包括：
 * - 檔案上傳與驗證
 * - CSV 格式解析
 * - 資料預覽與確認
 * - 批量導入處理
 * - 錯誤處理與回饋
 */

import React, { useState, useCallback, useRef } from 'react';
import styled from 'styled-components';
import { Modal, Button, Card, Progress } from '../ui';
import { useNotification } from '../../hooks/useNotification';

// ============= 樣式定義 =============

const ImportContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
`;

const UploadArea = styled.div<{ isDragOver: boolean }>`
  border: 2px dashed ${props => props.isDragOver ? 'var(--color-primary)' : 'var(--color-border)'};
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  background: ${props => props.isDragOver ? 'var(--color-primary-light)' : 'var(--color-background-secondary)'};
  transition: all 0.3s ease;
  cursor: pointer;
  
  &:hover {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
  }
`;

const UploadIcon = styled.div`
  font-size: 3rem;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
`;

const UploadText = styled.div`
  font-size: 1.1rem;
  color: var(--color-text-primary);
  margin-bottom: 8px;
`;

const UploadHint = styled.div`
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const PreviewSection = styled(Card)`
  padding: 20px;
  background: var(--color-surface);
`;

const PreviewTitle = styled.h3`
  margin: 0 0 16px 0;
  color: var(--color-text-primary);
  font-size: 1.1rem;
`;

const PreviewTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  
  th, td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--color-border);
  }
  
  th {
    background: var(--color-background-secondary);
    font-weight: 600;
    color: var(--color-text-primary);
  }
  
  td {
    color: var(--color-text-secondary);
  }
  
  tr:hover {
    background: var(--color-background-secondary);
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
`;

const StatItem = styled.div`
  text-align: center;
  padding: 12px;
  background: var(--color-background-secondary);
  border-radius: 6px;
`;

const StatValue = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-primary);
`;

const StatLabel = styled.div`
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  margin-top: 4px;
`;

const ActionButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
`;

const HiddenFileInput = styled.input`
  display: none;
`;

// ============= 類型定義 =============

interface ParsedProxy {
  ip: string;
  port?: number;
  protocol?: 'http' | 'https' | 'socks4' | 'socks5';
  username?: string;
  password?: string;
  country?: string;
  isValid: boolean;
  error?: string;
}

interface ImportStats {
  total: number;
  valid: number;
  invalid: number;
  duplicates: number;
}

interface CsvImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (proxies: ParsedProxy[]) => Promise<void>;
}

// ============= 主要組件 =============

export const CsvImportModal: React.FC<CsvImportModalProps> = ({
  isOpen,
  onClose,
  onImport
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<ParsedProxy[]>([]);
  const [stats, setStats] = useState<ImportStats>({ total: 0, valid: 0, invalid: 0, duplicates: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showNotification } = useNotification();

  /**
   * 下載CSV範本檔案
   */
  const downloadTemplate = useCallback(() => {
    const templateData = [
      'ip_address,port,protocol,username,password,country,tags',
      '192.168.1.1,8080,http,,,US,premium',
      '10.0.0.1,1080,socks5,user,pass,CN,test',
      '172.16.0.1,3128,https,,,JP,'
    ].join('\n');
    
    const blob = new Blob([templateData], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'proxy_template.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('CSV範本已下載', 'success');
  }, [showNotification]);

  // ============= 檔案處理函數 =============

  /**
   * 驗證IP地址格式
   */
  const validateIP = useCallback((ip: string): boolean => {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip.trim());
  }, []);

  /**
   * 驗證連接埠號
   */
  const validatePort = useCallback((port: string | number): boolean => {
    const portNum = typeof port === 'string' ? parseInt(port) : port;
    return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
  }, []);

  /**
   * 驗證協議類型
   */
  const validateProtocol = useCallback((protocol: string): boolean => {
    const validProtocols = ['http', 'https', 'socks4', 'socks5'];
    return validProtocols.includes(protocol.toLowerCase());
  }, []);

  /**
   * 驗證國家代碼
   */
  const validateCountryCode = useCallback((country: string): boolean => {
    if (!country) return true; // 可選欄位
    // 簡化的 ISO 3166-1 alpha-2 驗證
    return /^[A-Z]{2}$/.test(country.toUpperCase());
  }, []);

  /**
   * 解析CSV檔案內容
   */
  const parseCSV = useCallback(async (file: File): Promise<ParsedProxy[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          const lines = text.split('\n').filter(line => line.trim());
          const parsed: ParsedProxy[] = [];
          const seenIPs = new Set<string>();
          let isFirstLine = true;
          
          lines.forEach((line) => {
            // 跳過標題行（如果存在）
            if (isFirstLine && line.toLowerCase().includes('ip_address')) {
              isFirstLine = false;
              return;
            }
            isFirstLine = false;
            
            const columns = line.split(',').map(col => col.trim().replace(/"/g, ''));
            const ip = columns[0];
            
            if (!ip) return;
            
            // 處理端口：如果沒有提供端口，根據協議設置默認端口
            let port: number | undefined;
            if (columns[1] && columns[1].trim() !== '') {
              port = parseInt(columns[1]);
            } else {
              // 根據協議設置默認端口
              const protocol = columns[2] && columns[2].trim() !== '' ? columns[2].toLowerCase() : 'http';
              switch (protocol) {
                case 'https':
                  port = 443;
                  break;
                case 'socks4':
                case 'socks5':
                  port = 1080;
                  break;
                default:
                  port = 8080; // HTTP 代理常用端口
              }
            }
            
            const proxy: ParsedProxy = {
              ip,
              port,
              protocol: (columns[2] as any) || 'http',
              username: columns[3] || undefined,
              password: columns[4] || undefined,
              country: columns[5] || undefined,
              isValid: false,
              error: undefined
            };
            
            const errors: string[] = [];
            
            // 驗證IP格式
            if (!validateIP(ip)) {
              errors.push('無效的IP地址格式');
            }
            
            // 檢查重複IP
            if (seenIPs.has(ip)) {
              errors.push('重複的IP地址');
            }
            
            // 驗證連接埠
            if (proxy.port && !validatePort(proxy.port)) {
              errors.push('連接埠必須在1-65535範圍內');
            }
            
            // 驗證協議
            if (proxy.protocol && !validateProtocol(proxy.protocol)) {
              errors.push('不支援的協議類型');
            }
            
            // 驗證國家代碼
            if (proxy.country && !validateCountryCode(proxy.country)) {
              errors.push('無效的國家代碼格式');
            }
            
            if (errors.length === 0) {
              proxy.isValid = true;
              seenIPs.add(ip);
            } else {
              proxy.error = errors.join(', ');
            }
            
            parsed.push(proxy);
          });
          
          resolve(parsed);
        } catch (error) {
          reject(new Error('CSV檔案解析失敗'));
        }
      };
      
      reader.onerror = () => reject(new Error('檔案讀取失敗'));
      reader.readAsText(file, 'UTF-8');
    });
  }, [validateIP, validatePort, validateProtocol, validateCountryCode]);

  /**
   * 計算統計資訊
   */
  const calculateStats = useCallback((data: ParsedProxy[]): ImportStats => {
    const total = data.length;
    const valid = data.filter(p => p.isValid).length;
    const invalid = data.filter(p => !p.isValid && p.error !== '重複的IP地址').length;
    const duplicates = data.filter(p => p.error === '重複的IP地址').length;
    
    return { total, valid, invalid, duplicates };
  }, []);

  // ============= 事件處理函數 =============

  /**
   * 處理檔案選擇
   */
  const handleFileSelect = useCallback(async (selectedFile: File) => {
    // 檔案格式驗證
    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      showNotification('請選擇CSV檔案', 'error');
      return;
    }
    
    // 檔案大小驗證（10MB限制）
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (selectedFile.size > maxSize) {
      showNotification('檔案大小不能超過10MB', 'error');
      return;
    }
    
    // 檔案內容類型驗證
    if (selectedFile.type && !selectedFile.type.includes('csv') && !selectedFile.type.includes('text')) {
      showNotification('檔案格式不正確，請選擇有效的CSV檔案', 'error');
      return;
    }
    
    setFile(selectedFile);
    setIsProcessing(true);
    setErrors([]);
    setImportProgress(10);
    
    try {
      setImportProgress(30);
      const parsed = await parseCSV(selectedFile);
      setImportProgress(70);
      
      setParsedData(parsed);
      const stats = calculateStats(parsed);
      setStats(stats);
      
      setImportProgress(100);
      
      // 檢查解析結果
      if (parsed.length === 0) {
        setErrors(['檔案中沒有找到有效的代理資料']);
      } else if (stats.valid === 0) {
        setErrors(['檔案中沒有找到有效的代理IP地址']);
      } else {
        // 顯示解析成功的通知
        showNotification(`成功解析 ${stats.total} 筆資料，其中 ${stats.valid} 筆有效`, 'success');
      }
      
      // 記錄數限制檢查（10,000筆）
      if (parsed.length > 10000) {
        setErrors(prev => [...prev, '檔案記錄數超過10,000筆限制，僅顯示前10,000筆']);
        setParsedData(parsed.slice(0, 10000));
        setStats(calculateStats(parsed.slice(0, 10000)));
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '檔案處理失敗';
      setErrors([errorMessage]);
      showNotification(errorMessage, 'error');
    } finally {
      setIsProcessing(false);
      setTimeout(() => setImportProgress(0), 1000);
    }
  }, [parseCSV, calculateStats, showNotification]);

  /**
   * 處理拖拽上傳
   */
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  /**
   * 處理檔案輸入變更
   */
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  /**
   * 處理導入確認
   */
  const handleImportConfirm = useCallback(async () => {
    const validProxies = parsedData.filter(p => p.isValid);
    
    if (validProxies.length === 0) {
      showNotification('沒有有效的代理可以導入', 'warning');
      return;
    }
    
    setIsProcessing(true);
    setImportProgress(0);
    
    try {
      await onImport(validProxies);
      showNotification(`成功導入 ${validProxies.length} 個代理`, 'success');
      handleClose();
    } catch (error) {
      showNotification('導入失敗', 'error');
    } finally {
      setIsProcessing(false);
      setImportProgress(0);
    }
  }, [parsedData, onImport, showNotification]);

  /**
   * 重置狀態並關閉模態框
   */
  const handleClose = useCallback(() => {
    setFile(null);
    setParsedData([]);
    setStats({ total: 0, valid: 0, invalid: 0, duplicates: 0 });
    setIsProcessing(false);
    setImportProgress(0);
    setErrors([]);
    setIsDragOver(false);
    onClose();
  }, [onClose]);

  // ============= 渲染 =============

  return (
    <Modal
      title="導入代理 CSV 檔案"
      width="800px"
      visible={isOpen}
      onClose={handleClose}
    >
      <ImportContainer>
        {/* 檔案上傳區域 */}
        {!file && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h4 style={{ margin: 0, color: 'var(--color-text-primary)' }}>上傳代理CSV檔案</h4>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                  支援標準CSV格式，包含IP地址、連接埠、協議等欄位
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={downloadTemplate}
                style={{ fontSize: '0.875rem' }}
              >
                📥 下載範本
              </Button>
            </div>
            
            <UploadArea
              isDragOver={isDragOver}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
            >
              <UploadIcon>📁</UploadIcon>
              <UploadText>點擊選擇檔案或拖拽到此處</UploadText>
              <UploadHint>
                支援 CSV 格式 • 檔案大小限制 10MB • 最多 10,000 筆記錄<br/>
                <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                  支援欄位：ip_address*, port*, protocol*, username, password, country, tags
                </span>
              </UploadHint>
              <HiddenFileInput
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileInputChange}
              />
            </UploadArea>
          </>
        )}

        {/* 錯誤訊息 */}
        {errors.length > 0 && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: 'var(--color-error-light, #fee)',
            border: '1px solid var(--color-error, #f00)',
            borderRadius: '6px',
            color: 'var(--color-error, #f00)'
          }}>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              {errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {/* 處理進度 */}
        {isProcessing && (
          <Progress percent={importProgress} />
        )}

        {/* 資料預覽 */}
        {file && parsedData.length > 0 && (
          <PreviewSection>
            <PreviewTitle>檔案預覽：{file.name}</PreviewTitle>
            
            {/* 統計資訊 */}
            <StatsGrid>
              <StatItem>
                <StatValue>{stats.total}</StatValue>
                <StatLabel>總計</StatLabel>
              </StatItem>
              <StatItem>
                <StatValue>{stats.valid}</StatValue>
                <StatLabel>有效</StatLabel>
              </StatItem>
              <StatItem>
                <StatValue>{stats.invalid}</StatValue>
                <StatLabel>無效</StatLabel>
              </StatItem>
              <StatItem>
                <StatValue>{stats.duplicates}</StatValue>
                <StatLabel>重複</StatLabel>
              </StatItem>
            </StatsGrid>

            {/* 資料表格 */}
            <PreviewTable>
              <thead>
                <tr>
                  <th>IP 地址</th>
                  <th>埠號</th>
                  <th>協議</th>
                  <th>國家</th>
                  <th>狀態</th>
                </tr>
              </thead>
              <tbody>
                {parsedData.slice(0, 10).map((proxy, index) => (
                  <tr key={index}>
                    <td>{proxy.ip}</td>
                    <td>{proxy.port || '-'}</td>
                    <td>{proxy.protocol || 'http'}</td>
                    <td>{proxy.country || '-'}</td>
                    <td>
                      {proxy.isValid ? (
                        <span style={{ color: 'var(--color-success)' }}>✓ 有效</span>
                      ) : (
                        <span style={{ color: 'var(--color-error)' }}>✗ {proxy.error}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </PreviewTable>
            
            {parsedData.length > 10 && (
              <div style={{ textAlign: 'center', marginTop: '12px', color: 'var(--color-text-secondary)' }}>
                顯示前 10 筆，共 {parsedData.length} 筆資料
              </div>
            )}
          </PreviewSection>
        )}

        {/* 操作按鈕 */}
        <ActionButtons>
          <Button variant="secondary" onClick={handleClose}>
            取消
          </Button>
          {file && (
            <Button
              variant="secondary"
              onClick={() => {
                setFile(null);
                setParsedData([]);
                setErrors([]);
              }}
            >
              重新選擇
            </Button>
          )}
          {stats.valid > 0 && (
            <Button
              variant="primary"
              onClick={handleImportConfirm}
              disabled={isProcessing}
            >
              導入 {stats.valid} 個有效代理
            </Button>
          )}
        </ActionButtons>
      </ImportContainer>
    </Modal>
  );
};

export default CsvImportModal;