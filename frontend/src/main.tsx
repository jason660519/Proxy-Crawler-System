/**
 * 應用程式入口文件
 * React 應用程式的啟動點
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// 確保根元素存在
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found. Make sure you have a div with id="root" in your HTML.');
}

// 創建 React 根節點並渲染應用程式
const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);