import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
`;

const Frame = styled.iframe`
  width: 100%;
  height: 420px;
  border: 1px solid var(--color-border-primary);
  border-radius: 8px;
  background: var(--color-background-card);
`;

const getEnv = (key: string, defVal: string) => (import.meta as any).env?.[key] || defVal;

export const OperationsDashboard: React.FC = () => {
  const grafana = getEnv('VITE_GRAFANA_URL', 'http://localhost:3001');
  // Public panels require Grafana to allow embedding or be accessible via viewer auth.
  const overviewUrl = `${grafana}/d-solo/_proxy_overview/proxy-system-overview?orgId=1&panelId=1`;
  const validationUrl = `${grafana}/d-solo/_proxy_validation/proxy-validation-overview?orgId=1&panelId=1`;

  return (
    <Container>
      <Frame src={overviewUrl} title="Proxy System Overview" />
      <Frame src={validationUrl} title="Proxy Validation Overview" />
    </Container>
  );
};


