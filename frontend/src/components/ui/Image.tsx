/**
 * Image 組件
 * 提供統一的圖片顯示和載入狀態處理
 */

import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { colors, borderRadius } from '../../styles';

// ============= 類型定義 =============

export interface ImageProps {
  src: string;
  alt: string;
  width?: string | number;
  height?: string | number;
  fit?: 'cover' | 'contain' | 'fill' | 'scale-down' | 'none';
  placeholder?: string;
  fallback?: string;
  loading?: 'lazy' | 'eager';
  className?: string;
  style?: React.CSSProperties;
  onLoad?: () => void;
  onError?: () => void;
}

// ============= 樣式組件 =============

const ImageContainer = styled.div<{ width?: string | number; height?: string | number }>`
  position: relative;
  display: inline-block;
  overflow: hidden;
  border-radius: ${borderRadius.md};
  background-color: ${colors.secondary[100]};
  
  ${({ width }) => width && `width: ${typeof width === 'number' ? `${width}px` : width};`}
  ${({ height }) => height && `height: ${typeof height === 'number' ? `${height}px` : height};`}
`;

const StyledImage = styled.img<{ fit?: string }>`
  width: 100%;
  height: 100%;
  object-fit: ${({ fit }) => fit || 'cover'};
  transition: opacity 0.3s ease;
  
  &.loading {
    opacity: 0;
  }
  
  &.loaded {
    opacity: 1;
  }
  
  &.error {
    opacity: 0;
  }
`;

const PlaceholderContainer = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: ${colors.secondary[100]};
  color: ${colors.secondary[500]};
  font-size: 14px;
  transition: opacity 0.3s ease;
  
  &.hidden {
    opacity: 0;
    pointer-events: none;
  }
`;

const LoadingSpinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid ${colors.secondary[300]};
  border-top: 2px solid ${colors.primary[500]};
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// ============= 主要組件 =============

/**
 * Image 組件
 * 
 * @param props - Image 屬性
 * @returns Image 組件
 */
export const Image: React.FC<ImageProps> = ({
  src,
  alt,
  width,
  height,
  fit = 'cover',
  placeholder,
  fallback,
  loading = 'lazy',
  className,
  style,
  onLoad,
  onError,
  ...props
}) => {
  const [imageState, setImageState] = useState<'loading' | 'loaded' | 'error'>('loading');
  const [currentSrc, setCurrentSrc] = useState(src);

  const handleLoad = useCallback(() => {
    setImageState('loaded');
    onLoad?.();
  }, [onLoad]);

  const handleError = useCallback(() => {
    if (fallback && currentSrc !== fallback) {
      setCurrentSrc(fallback);
      setImageState('loading');
    } else {
      setImageState('error');
      onError?.();
    }
  }, [fallback, currentSrc, onError]);

  return (
    <ImageContainer
      width={width}
      height={height}
      className={className}
      style={style}
    >
      <StyledImage
        src={currentSrc}
        alt={alt}
        fit={fit}
        loading={loading}
        className={imageState}
        onLoad={handleLoad}
        onError={handleError}
        {...props}
      />
      
      <PlaceholderContainer className={imageState === 'loaded' ? 'hidden' : ''}>
        {imageState === 'loading' ? (
          placeholder ? (
            <span>{placeholder}</span>
          ) : (
            <LoadingSpinner />
          )
        ) : imageState === 'error' ? (
          <span>載入失敗</span>
        ) : null}
      </PlaceholderContainer>
    </ImageContainer>
  );
};

export default Image;