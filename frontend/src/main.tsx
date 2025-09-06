import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import App from './App.tsx'
import './styles/globals.css'
import './i18n/index.ts'

// 創建 React Query 客戶端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 分鐘
      cacheTime: 10 * 60 * 1000, // 10 分鐘
      retry: (failureCount, error) => {
        // 對於 4xx 錯誤不重試
        if (error instanceof Error && error.message.includes('4')) {
          return false
        }
        return failureCount < 3
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

// 移除載入指示器
const removeLoadingSpinner = () => {
  const root = document.getElementById('root')
  if (root) {
    root.classList.add('app-loaded')
  }
}

// 渲染應用程式
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        {/* 開發環境顯示 React Query DevTools */}
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)

// 應用程式載入完成後移除載入指示器
setTimeout(removeLoadingSpinner, 100)

// 開發環境的熱重載支援
if (import.meta.env.DEV) {
  // 啟用 React Fast Refresh
  if (import.meta.hot) {
    import.meta.hot.accept()
  }
}

// 全域錯誤處理
window.addEventListener('unhandledrejection', (event) => {
  console.error('未處理的 Promise 拒絕:', event.reason)
  // 在生產環境中，可以將錯誤發送到錯誤追蹤服務
})

window.addEventListener('error', (event) => {
  console.error('全域錯誤:', event.error)
  // 在生產環境中，可以將錯誤發送到錯誤追蹤服務
})