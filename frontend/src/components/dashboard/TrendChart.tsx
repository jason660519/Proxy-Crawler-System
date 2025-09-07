/**
 * 趨勢圖組件
 * 顯示系統性能趨勢，包括成功率、響應時間等指標的時間序列圖表
 */

import React, { useMemo, useState } from 'react';
import styled from 'styled-components';
import { Card } from '../ui/Card';
import { useTrendData } from '../../hooks';
import { spacing, borderRadius } from '../../styles';
import type { TrendDataPoint } from '../../types';

// ============= 類型定義 =============

interface TrendChartProps {
  className?: string;
  metric?: 'successRate' | 'validationCount' | 'averageLatency';
  timeRange?: '1h' | '6h' | '24h' | '7d';
}

// 圖表數據點類型
interface ChartPoint {
  x: number;
  y: number;
  timestamp: string;
  value: number;
}

// ============= 樣式定義 =============

const TrendChartContainer = styled(Card)`
  padding: ${spacing[6]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.lg};
  min-height: 300px;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[6]};
`;

const Title = styled.h3`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const Controls = styled.div`
  display: flex;
  gap: ${spacing[2]};
`;

const TimeRangeButton = styled.button<{ active?: boolean }>`
  padding: ${spacing[1]} ${spacing[2]};
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.md};
  background: ${({ active }) => active ? 'var(--color-primary-500)' : 'var(--color-background-card)'};
  color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-text-secondary)'};
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-primary-500);
    color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-primary-500)'};
  }
`;

const ChartContainer = styled.div`
  position: relative;
  height: 200px;
  margin: ${spacing[4]} 0;
`;

const SVGChart = styled.svg`
  width: 100%;
  height: 100%;
  overflow: visible;
`;

const ChartLine = styled.path`
  fill: none;
  stroke: var(--color-primary-500);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
`;

const ChartArea = styled.path`
  fill: var(--color-primary-500-alpha-20);
  stroke: none;
`;

const GridLine = styled.line`
  stroke: var(--color-border-light);
  stroke-width: 1;
  stroke-dasharray: 2,2;
`;



const Tooltip = styled.div<{ x: number; y: number; visible: boolean }>`
  position: absolute;
  left: ${({ x }) => x}px;
  top: ${({ y }) => y}px;
  background: var(--color-background-tooltip);
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.md};
  padding: ${spacing[2]};
  font-size: 0.875rem;
  color: var(--color-text-primary);
  pointer-events: none;
  opacity: ${({ visible }) => visible ? 1 : 0};
  transition: opacity 0.2s ease;
  z-index: 1000;
  
  &::before {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: var(--color-border-default);
  }
`;

const LoadingState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-secondary);
`;

const ErrorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-status-error);
  text-align: center;
  
  .error-message {
    margin-top: ${spacing[2]};
    font-size: 0.875rem;
  }
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-secondary);
  text-align: center;
  
  .empty-message {
    margin-top: ${spacing[2]};
    font-size: 0.875rem;
  }
`;

// ============= 組件實作 =============

/**
 * 趨勢圖組件
 */
export const TrendChart: React.FC<TrendChartProps> = ({
  className,
  metric = 'successRate',
  timeRange = '24h'
}) => {
  const { trendData, loading, error } = useTrendData(timeRange);
  const [hoveredPoint, setHoveredPoint] = useState<ChartPoint | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // 處理圖表數據
  const chartData: ChartPoint[] = useMemo(() => {
    if (!trendData) return [];
    
    let dataPoints: TrendDataPoint[] = [];
    switch (metric) {
      case 'successRate':
        dataPoints = trendData.successRate || [];
        break;
      case 'validationCount':
        dataPoints = trendData.validationCount || [];
        break;
      case 'averageLatency':
        dataPoints = trendData.averageLatency || [];
        break;
      default:
        dataPoints = trendData.successRate || [];
    }
    
    if (!dataPoints.length) return [];

    return dataPoints.map((item, index) => {
      return {
        x: (index / (dataPoints.length - 1)) * 100,
        y: item.value,
        timestamp: item.timestamp,
        value: item.value
      };
    });
  }, [trendData, metric]);

  // 計算 Y 軸範圍
  const yRange = useMemo(() => {
    if (!chartData.length) return { min: 0, max: 100 };
    
    const values = chartData.map((d: ChartPoint) => d.y);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.1;
    
    return {
      min: Math.max(0, min - padding),
      max: max + padding
    };
  }, [chartData]);

  // 生成 SVG 路徑
  const linePath = useMemo(() => {
    if (!chartData.length) return '';
    
    return chartData
      .map((point: ChartPoint, index: number) => {
        const x = point.x;
        const y = 100 - ((point.y - yRange.min) / (yRange.max - yRange.min)) * 100;
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  }, [chartData, yRange]);

  // 生成區域填充路徑
  const areaPath = useMemo(() => {
    if (!chartData.length) return '';
    
    const line = chartData
      .map((point: ChartPoint, index: number) => {
        const x = point.x;
        const y = 100 - ((point.y - yRange.min) / (yRange.max - yRange.min)) * 100;
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
    
    const lastPoint = chartData[chartData.length - 1];
    const firstPoint = chartData[0];
    
    return `${line} L ${lastPoint.x} 100 L ${firstPoint.x} 100 Z`;
  }, [chartData, yRange]);

  // 處理滑鼠懸停
  const handleMouseMove = (event: React.MouseEvent<SVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    
    // 找到最近的數據點
    const closestPoint = chartData.reduce((closest: ChartPoint, point: ChartPoint) => {
      return Math.abs(point.x - x) < Math.abs(closest.x - x) ? point : closest;
    }, chartData[0]);
    
    if (closestPoint) {
      setHoveredPoint(closestPoint);
      setTooltipPos({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top - 60
      });
    }
  };

  const handleMouseLeave = () => {
    setHoveredPoint(null);
  };

  // 獲取指標標題
  const getMetricTitle = () => {
    switch (metric) {
      case 'successRate': return '成功率趨勢';
      case 'validationCount': return '驗證次數趨勢';
      case 'averageLatency': return '平均延遲趨勢';
      default: return '趨勢圖';
    }
  };

  // 格式化數值
  const formatValue = (value: number) => {
    switch (metric) {
      case 'successRate': return `${value.toFixed(1)}%`;
      case 'validationCount': return value.toString();
      case 'averageLatency': return `${value.toFixed(0)}ms`;
      default: return value.toString();
    }
  };

  return (
    <TrendChartContainer className={className}>
      <Header>
        <Title>{getMetricTitle()}</Title>
        <Controls>
          {(['1h', '6h', '24h', '7d'] as const).map((range) => (
            <TimeRangeButton
              key={range}
              active={timeRange === range}
              onClick={() => {/* TODO: 實現時間範圍切換 */}}
            >
              {range}
            </TimeRangeButton>
          ))}
        </Controls>
      </Header>

      <ChartContainer>
        {loading && (
          <LoadingState>
            載入趨勢數據中...
          </LoadingState>
        )}

        {error && (
          <ErrorState>
            <div>📈</div>
            <div className="error-message">
              無法載入趨勢數據：{error.message}
            </div>
          </ErrorState>
        )}

        {!loading && !error && !chartData.length && (
          <EmptyState>
            <div>📊</div>
            <div className="empty-message">
              暫無趨勢數據
            </div>
          </EmptyState>
        )}

        {!loading && !error && chartData.length > 0 && (
          <>
            <SVGChart
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              {/* 網格線 */}
              {[0, 25, 50, 75, 100].map(y => (
                <GridLine key={y} x1="0" y1={y} x2="100" y2={y} />
              ))}
              
              {/* 區域填充 */}
              <ChartArea d={areaPath} />
              
              {/* 趨勢線 */}
              <ChartLine d={linePath} />
              
              {/* 數據點 */}
              {chartData.map((point: ChartPoint, index: number) => {
                const y = 100 - ((point.y - yRange.min) / (yRange.max - yRange.min)) * 100;
                return (
                  <circle
                    key={index}
                    cx={point.x}
                    cy={y}
                    r="2"
                    fill="var(--color-primary-500)"
                    stroke="var(--color-white)"
                    strokeWidth="1"
                  />
                );
              })}
            </SVGChart>

            {/* 工具提示 */}
            <Tooltip
              x={tooltipPos.x}
              y={tooltipPos.y}
              visible={!!hoveredPoint}
            >
              {hoveredPoint && (
                <div>
                  <div>{formatValue(hoveredPoint.value)}</div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                    {new Date(hoveredPoint.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              )}
            </Tooltip>
          </>
        )}
      </ChartContainer>
    </TrendChartContainer>
  );
};

// 導出類型
export type { TrendChartProps, ChartPoint as ChartDataPoint };
export type ChartMetric = 'successRate' | 'validationCount' | 'averageLatency';

export default TrendChart;