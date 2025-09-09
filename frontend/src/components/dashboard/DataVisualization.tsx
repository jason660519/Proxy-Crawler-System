/**
 * 數據可視化組件
 * 提供多種圖表類型和交互式數據展示功能
 */

import React, { useState, useMemo } from 'react';
import styled from 'styled-components';
import { Card } from '../ui/Card';
import { spacing, borderRadius } from '../../styles';

// ============= 類型定義 =============

interface DataVisualizationProps {
  className?: string;
  data?: ChartData[];
  chartType?: ChartType;
  title?: string;
  height?: number;
}

type ChartType = 'line' | 'bar' | 'pie' | 'area' | 'scatter' | 'heatmap';

interface ChartData {
  label: string;
  value: number;
  timestamp?: string;
  category?: string;
  color?: string;
}

interface ChartPoint {
  x: number;
  y: number;
  label: string;
  value: number;
}

// ============= 樣式定義 =============

const VisualizationContainer = styled(Card)`
  padding: ${spacing[6]};
  background: var(--color-background-card);
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.lg};
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing[4]};
`;

const Title = styled.h3`
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const ChartTypeSelector = styled.div`
  display: flex;
  gap: ${spacing[1]};
`;

const ChartTypeButton = styled.button<{ active?: boolean }>`
  padding: ${spacing[1]} ${spacing[2]};
  border: 1px solid var(--color-border-default);
  border-radius: ${borderRadius.sm};
  background: ${({ active }) => active ? 'var(--color-primary-500)' : 'var(--color-background-card)'};
  color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-text-secondary)'};
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-primary-500);
    color: ${({ active }) => active ? 'var(--color-white)' : 'var(--color-primary-500)'};
  }
`;

const ChartContainer = styled.div<{ height: number }>`
  position: relative;
  height: ${({ height }) => height}px;
  background: var(--color-background-subtle);
  border-radius: ${borderRadius.md};
  overflow: hidden;
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

const ChartBar = styled.rect<{ color?: string }>`
  fill: ${({ color }) => color || 'var(--color-primary-500)'};
  transition: all 0.2s ease;

  &:hover {
    opacity: 0.8;
    transform: scaleY(1.05);
  }
`;

const GridLine = styled.line`
  stroke: var(--color-border-light);
  stroke-width: 1;
  stroke-dasharray: 2,2;
`;

const AxisLabel = styled.text`
  fill: var(--color-text-secondary);
  font-size: 0.75rem;
  text-anchor: middle;
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
  box-shadow: 0 4px 12px var(--color-shadow-light);
  
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

const Legend = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: ${spacing[3]};
  margin-top: ${spacing[4]};
  padding-top: ${spacing[3]};
  border-top: 1px solid var(--color-border-light);
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing[1]};
  font-size: 0.875rem;
  color: var(--color-text-secondary);
`;

const LegendColor = styled.div<{ color: string }>`
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: ${({ color }) => color};
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-secondary);
  text-align: center;
  
  .empty-icon {
    font-size: 2rem;
    margin-bottom: ${spacing[2]};
  }
  
  .empty-message {
    font-size: 0.875rem;
  }
`;

// ============= 工具函數 =============

/**
 * 生成顏色調色板
 */
const generateColors = (count: number): string[] => {
  const colors = [
    'var(--color-primary-500)',
    'var(--color-secondary-500)',
    'var(--color-success-500)',
    'var(--color-warning-500)',
    'var(--color-error-500)',
    'var(--color-info-500)',
    '#8B5CF6', // 紫色
    '#F59E0B', // 橙色
    '#10B981', // 綠色
    '#EF4444', // 紅色
  ];
  
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  
  return result;
};

/**
 * 計算圖表點位置
 */
const calculatePoints = (data: ChartData[], width: number, height: number): ChartPoint[] => {
  if (!data.length) return [];
  
  const values = data.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueRange = maxValue - minValue || 1;
  
  return data.map((item, index) => ({
    x: (index / (data.length - 1)) * width,
    y: height - ((item.value - minValue) / valueRange) * height,
    label: item.label,
    value: item.value
  }));
};

/**
 * 生成 SVG 路徑
 */
const generatePath = (points: ChartPoint[]): string => {
  if (!points.length) return '';
  
  return points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
    .join(' ');
};

/**
 * 生成區域填充路徑
 */
const generateAreaPath = (points: ChartPoint[], height: number): string => {
  if (!points.length) return '';
  
  const linePath = generatePath(points);
  const lastPoint = points[points.length - 1];
  const firstPoint = points[0];
  
  return `${linePath} L ${lastPoint.x} ${height} L ${firstPoint.x} ${height} Z`;
};

// ============= 組件實作 =============

/**
 * 線性圖表組件
 */
const LineChart: React.FC<{ data: ChartData[]; width: number; height: number; onHover: (point: ChartPoint | null, event?: React.MouseEvent) => void }> = ({ 
  data, width, height, onHover 
}) => {
  const points = useMemo(() => calculatePoints(data, width, height), [data, width, height]);
  const linePath = useMemo(() => generatePath(points), [points]);
  
  return (
    <g>
      {/* 網格線 */}
      {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
        <GridLine key={ratio} x1="0" y1={height * ratio} x2={width} y2={height * ratio} />
      ))}
      
      {/* 線條 */}
      <ChartLine d={linePath} />
      
      {/* 數據點 */}
      {points.map((point, index) => (
        <circle
          key={index}
          cx={point.x}
          cy={point.y}
          r="4"
          fill="var(--color-primary-500)"
          stroke="var(--color-white)"
          strokeWidth="2"
          style={{ cursor: 'pointer' }}
          onMouseEnter={(e) => onHover(point, e)}
          onMouseLeave={() => onHover(null)}
        />
      ))}
    </g>
  );
};

/**
 * 區域圖表組件
 */
const AreaChart: React.FC<{ data: ChartData[]; width: number; height: number; onHover: (point: ChartPoint | null, event?: React.MouseEvent) => void }> = ({ 
  data, width, height, onHover 
}) => {
  const points = useMemo(() => calculatePoints(data, width, height), [data, width, height]);
  const linePath = useMemo(() => generatePath(points), [points]);
  const areaPath = useMemo(() => generateAreaPath(points, height), [points, height]);
  
  return (
    <g>
      {/* 網格線 */}
      {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
        <GridLine key={ratio} x1="0" y1={height * ratio} x2={width} y2={height * ratio} />
      ))}
      
      {/* 區域填充 */}
      <ChartArea d={areaPath} />
      
      {/* 線條 */}
      <ChartLine d={linePath} />
      
      {/* 數據點 */}
      {points.map((point, index) => (
        <circle
          key={index}
          cx={point.x}
          cy={point.y}
          r="3"
          fill="var(--color-primary-500)"
          stroke="var(--color-white)"
          strokeWidth="1"
          style={{ cursor: 'pointer' }}
          onMouseEnter={(e) => onHover(point, e)}
          onMouseLeave={() => onHover(null)}
        />
      ))}
    </g>
  );
};

/**
 * 柱狀圖表組件
 */
const BarChart: React.FC<{ data: ChartData[]; width: number; height: number; onHover: (point: ChartPoint | null, event?: React.MouseEvent) => void }> = ({ 
  data, width, height, onHover 
}) => {
  const colors = useMemo(() => generateColors(data.length), [data.length]);
  const maxValue = useMemo(() => Math.max(...data.map(d => d.value)), [data]);
  const barWidth = width / data.length * 0.8;
  const barSpacing = width / data.length * 0.2;
  
  return (
    <g>
      {/* 網格線 */}
      {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
        <GridLine key={ratio} x1="0" y1={height * ratio} x2={width} y2={height * ratio} />
      ))}
      
      {/* 柱狀圖 */}
      {data.map((item, index) => {
        const barHeight = (item.value / maxValue) * height;
        const x = index * (barWidth + barSpacing) + barSpacing / 2;
        const y = height - barHeight;
        
        const point: ChartPoint = {
          x: x + barWidth / 2,
          y: y,
          label: item.label,
          value: item.value
        };
        
        return (
          <ChartBar
            key={index}
            x={x}
            y={y}
            width={barWidth}
            height={barHeight}
            color={item.color || colors[index]}
            style={{ cursor: 'pointer' }}
            onMouseEnter={(e) => onHover(point, e)}
            onMouseLeave={() => onHover(null)}
          />
        );
      })}
      
      {/* X軸標籤 */}
      {data.map((item, index) => {
        const x = index * (barWidth + barSpacing) + barSpacing / 2 + barWidth / 2;
        return (
          <AxisLabel key={index} x={x} y={height + 15}>
            {item.label}
          </AxisLabel>
        );
      })}
    </g>
  );
};

/**
 * 主要數據可視化組件
 */
export const DataVisualization: React.FC<DataVisualizationProps> = ({
  className,
  data = [],
  chartType: initialChartType = 'line',
  title = '數據可視化',
  height = 300
}) => {
  const [chartType, setChartType] = useState<ChartType>(initialChartType);
  const [hoveredPoint, setHoveredPoint] = useState<ChartPoint | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  
  // 處理滑鼠懸停
  const handleHover = (point: ChartPoint | null, event?: React.MouseEvent) => {
    setHoveredPoint(point);
    if (point && event) {
      const rect = event.currentTarget.getBoundingClientRect();
      setTooltipPos({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top - 60
      });
    }
  };
  
  // 圖表尺寸
  const chartWidth = 400;
  const chartHeight = height - 60; // 預留空間給軸標籤
  
  // 圖表類型選項
  const chartTypes: { type: ChartType; icon: string; label: string }[] = [
    { type: 'line', icon: '📈', label: '線圖' },
    { type: 'area', icon: '📊', label: '區域圖' },
    { type: 'bar', icon: '📊', label: '柱狀圖' },
  ];
  
  // 渲染圖表
  const renderChart = () => {
    if (!data.length) {
      return (
        <EmptyState>
          <div className="empty-icon">📊</div>
          <div className="empty-message">暫無數據</div>
        </EmptyState>
      );
    }
    
    const commonProps = {
      data,
      width: chartWidth,
      height: chartHeight,
      onHover: handleHover
    };
    
    return (
      <SVGChart viewBox={`0 0 ${chartWidth} ${height}`} preserveAspectRatio="xMidYMid meet">
        {chartType === 'line' && <LineChart {...commonProps} />}
        {chartType === 'area' && <AreaChart {...commonProps} />}
        {chartType === 'bar' && <BarChart {...commonProps} />}
      </SVGChart>
    );
  };
  
  return (
    <VisualizationContainer className={className}>
      <Header>
        <Title>{title}</Title>
        <ChartTypeSelector>
          {chartTypes.map(({ type, icon, label }) => (
            <ChartTypeButton
              key={type}
              active={chartType === type}
              onClick={() => setChartType(type)}
              title={label}
            >
              {icon}
            </ChartTypeButton>
          ))}
        </ChartTypeSelector>
      </Header>
      
      <ChartContainer height={height}>
        {renderChart()}
        
        {/* 工具提示 */}
        <Tooltip
          x={tooltipPos.x}
          y={tooltipPos.y}
          visible={!!hoveredPoint}
        >
          {hoveredPoint && (
            <div>
              <div style={{ fontWeight: 600 }}>{hoveredPoint.label}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                數值: {hoveredPoint.value}
              </div>
            </div>
          )}
        </Tooltip>
      </ChartContainer>
      
      {/* 圖例 */}
      {data.length > 0 && chartType === 'bar' && (
        <Legend>
          {data.map((item, index) => {
            const colors = generateColors(data.length);
            return (
              <LegendItem key={index}>
                <LegendColor color={item.color || colors[index]} />
                <span>{item.label}</span>
              </LegendItem>
            );
          })}
        </Legend>
      )}
    </VisualizationContainer>
  );
};

export default DataVisualization;