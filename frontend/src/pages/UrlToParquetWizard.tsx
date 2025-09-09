import React, { useState } from 'react';
import { Typography } from '../components/ui/Typography';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Space } from '../components/ui/Space';
import { apiClient } from '../services/http';

const UrlToParquetWizard: React.FC = () => {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiClient.post<any>('/api/url2parquet/jobs', { url, options: { output_formats: ['parquet','json','md'] } });
      setResult(data);
    } catch (e: any) {
      setError(e?.message || '轉換失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space direction="vertical" size={16}>
      <Typography variant="h3">URL 轉換</Typography>
      <Card>
        <Space direction="vertical" size={12}>
          <Input
            placeholder="輸入一個 URL"
            value={url}
            onChange={(e: any) => setUrl(e.target.value)}
          />
          <Button onClick={onSubmit} disabled={!url} loading={loading}>開始轉換</Button>
        </Space>
      </Card>
      {error && (
        <Typography color="error">{error}</Typography>
      )}
      {result && (
        <Card>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(result, null, 2)}</pre>
        </Card>
      )}
    </Space>
  );
};

export default UrlToParquetWizard;


