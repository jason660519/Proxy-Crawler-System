import http, { etlHttp } from './http';

export interface HealthResponse {
  status: string;
  timestamp?: string;
  services?: Record<string, string>;
  service?: string;
}

export async function getMainHealth(): Promise<HealthResponse> {
  const { data } = await http.get<HealthResponse>('/health');
  return data;
}

export async function getEtlHealth(): Promise<HealthResponse> {
  // ETL 健康來自獨立服務（8001）
  const { data } = await etlHttp.get<HealthResponse>('/health');
  return data;
}


