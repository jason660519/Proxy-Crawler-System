import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { getSystemMetrics, getTrendData } from '../../services/api';

const Container = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
`;

const Card = styled.div`
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
`;

const Title = styled.div`
  font-size: 14px;
  color: #666;
`;

const Value = styled.div`
  margin-top: 6px;
  font-size: 24px;
  font-weight: 700;
`;

export const MetricsOverview: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const summary = await getSystemMetrics();
        if (!mounted) return;
        setMetrics(summary);
      } catch (e: any) {
        setError(e?.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  if (loading) return <div>Loading metrics...</div>;
  if (error) return <div style={{ color: '#d00' }}>{error}</div>;

  return (
    <Container>
      <Card>
        <Title>Total Proxies</Title>
        <Value>{metrics?.totalProxies ?? 0}</Value>
      </Card>
      <Card>
        <Title>Active Proxies</Title>
        <Value>{metrics?.activeProxies ?? 0}</Value>
      </Card>
      <Card>
        <Title>Success Rate</Title>
        <Value>{(metrics?.successRate ?? 0).toFixed(1)}%</Value>
      </Card>
      <Card>
        <Title>Avg Latency</Title>
        <Value>{Math.round(metrics?.averageResponseTime ?? 0)} ms</Value>
      </Card>
    </Container>
  );
};

export default MetricsOverview;


