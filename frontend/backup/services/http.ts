import axios from 'axios';

const baseURL = (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_BASE_URL) ||
  (window as any)?.__API_BASE_URL__ ||
  'http://localhost:8000';

const etlBaseURL = (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_ETL_BASE_URL) ||
  (window as any)?.__ETL_BASE_URL__ ||
  'http://localhost:8001';

export const http = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const etlHttp = axios.create({
  baseURL: etlBaseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

etlHttp.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

export default http;


