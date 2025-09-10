import React from 'react';
import { Helmet } from 'react-helmet-async';

/**
 * SEO Head 組件的 Props 接口
 */
export interface SEOHeadProps {
  /** 頁面標題 */
  title: string;
  /** 頁面描述 */
  description?: string;
  /** 關鍵字 */
  keywords?: string;
  /** 頁面類型 */
  type?: 'website' | 'article';
  /** 頁面 URL */
  url?: string;
  /** 頁面圖片 */
  image?: string;
  /** 是否為首頁 */
  isHomepage?: boolean;
}

/**
 * SEO Head 組件
 * 用於管理頁面的 meta 標籤和 SEO 優化
 */
const SEOHead: React.FC<SEOHeadProps> = ({
  title,
  description = 'Proxy Crawler System - 強大的網路爬蟲和代理管理平台，提供完整的數據收集、處理和分析解決方案。',
  keywords = 'proxy, crawler, 爬蟲, 代理, 數據收集, 網路爬蟲, 代理管理',
  type = 'website',
  url,
  image,
  isHomepage = false
}) => {
  // 構建完整標題
  const fullTitle = isHomepage ? title : `${title} - Proxy Crawler System`;
  
  // 當前頁面 URL
  const currentUrl = url || (typeof window !== 'undefined' ? window.location.href : '');
  
  // 默認圖片
  const defaultImage = '/favicon.ico';
  const ogImage = image || defaultImage;

  return (
    <Helmet>
      {/* 基本 meta 標籤 */}
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="author" content="Proxy Crawler System" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      
      {/* Open Graph 標籤 */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={type} />
      <meta property="og:url" content={currentUrl} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:site_name" content="Proxy Crawler System" />
      
      {/* Twitter Card 標籤 */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
      
      {/* 其他 SEO 標籤 */}
      <meta name="robots" content="index, follow" />
      <meta name="language" content="zh-TW" />
      <meta httpEquiv="Content-Language" content="zh-TW" />
      
      {/* 結構化數據 */}
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "WebApplication",
          "name": "Proxy Crawler System",
          "description": description,
          "url": currentUrl,
          "applicationCategory": "BusinessApplication",
          "operatingSystem": "Web Browser",
          "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
          }
        })}
      </script>
    </Helmet>
  );
};

export default SEOHead;