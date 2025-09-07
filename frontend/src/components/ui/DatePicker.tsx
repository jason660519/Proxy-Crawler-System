/**
 * 日期選擇器組件 - VS Code 風格的日期和時間選擇控制元件
 * 提供日期、時間和日期時間選擇功能，支持範圍選擇和自定義格式
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 日期選擇器容器
const DatePickerContainer = styled.div<{
  theme: 'light' | 'dark';
  disabled?: boolean;
  size: 'small' | 'medium' | 'large';
}>`
  position: relative;
  display: inline-block;
  width: 100%;
  opacity: ${props => props.disabled ? 0.6 : 1};
`;

// 日期輸入框
const DateInput = styled.input<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
  variant: 'default' | 'primary' | 'success' | 'warning' | 'error';
  hasError?: boolean;
}>`
  width: 100%;
  border: 1px solid ${props => {
    const colors = getThemeColors(props.theme);
    if (props.hasError) return colors.status.error;
    
    switch (props.variant) {
      case 'primary': return colors.accent.primary;
      case 'success': return colors.status.success;
      case 'warning': return colors.status.warning;
      case 'error': return colors.status.error;
      default: return colors.border.primary;
    }
  }};
  
  border-radius: ${borderRadius.sm};
  background-color: ${props => getThemeColors(props.theme).background.primary};
  color: ${props => getThemeColors(props.theme).text.primary};
  
  transition: ${transitions.fast};
  cursor: pointer;
  
  ${props => {
    switch (props.size) {
      case 'small':
        return `
          padding: ${spacing.xs} ${spacing.sm};
          font-size: 12px;
          height: 28px;
        `;
      case 'large':
        return `
          padding: ${spacing.md} ${spacing.lg};
          font-size: 16px;
          height: 44px;
        `;
      default:
        return `
          padding: ${spacing.sm} ${spacing.md};
          font-size: 14px;
          height: 36px;
        `;
    }
  }}
  
  &:hover {
    border-color: ${props => getThemeColors(props.theme).border.hover};
    background-color: ${props => getThemeColors(props.theme).background.hover};
  }
  
  &:focus {
    outline: none;
    border-color: ${props => getThemeColors(props.theme).accent.primary};
    box-shadow: 0 0 0 2px ${props => getThemeColors(props.theme).accent.primary}33;
  }
  
  &:disabled {
    cursor: not-allowed;
    background-color: ${props => getThemeColors(props.theme).background.disabled};
  }
  
  &::placeholder {
    color: ${props => getThemeColors(props.theme).text.placeholder};
  }
`;

// 日期選擇器彈出層
const DatePickerPopover = styled.div<{
  theme: 'light' | 'dark';
  visible: boolean;
  position: 'top' | 'bottom';
}>`
  position: absolute;
  ${props => props.position === 'top' ? 'bottom: 100%;' : 'top: 100%;'}
  left: 0;
  z-index: 1000;
  
  min-width: 280px;
  padding: ${spacing.md};
  margin-${props => props.position === 'top' ? 'bottom' : 'top'}: ${spacing.xs};
  
  background-color: ${props => getThemeColors(props.theme).background.elevated};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.md};
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  
  opacity: ${props => props.visible ? 1 : 0};
  visibility: ${props => props.visible ? 'visible' : 'hidden'};
  transform: ${props => props.visible ? 'translateY(0)' : `translateY(${props.position === 'top' ? '8px' : '-8px'})`};
  transition: ${transitions.medium};
`;

// 日曆標題
const CalendarHeader = styled.div<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.md};
  padding-bottom: ${spacing.sm};
  border-bottom: 1px solid ${props => getThemeColors(props.theme).border.secondary};
`;

// 月份年份顯示
const MonthYearDisplay = styled.div<{
  theme: 'light' | 'dark';
}>`
  font-size: 16px;
  font-weight: 600;
  color: ${props => getThemeColors(props.theme).text.primary};
`;

// 導航按鈕
const NavButton = styled.button<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  
  background: none;
  border: none;
  border-radius: ${borderRadius.sm};
  color: ${props => getThemeColors(props.theme).text.secondary};
  cursor: pointer;
  transition: ${transitions.fast};
  
  &:hover {
    background-color: ${props => getThemeColors(props.theme).background.hover};
    color: ${props => getThemeColors(props.theme).text.primary};
  }
  
  &:active {
    background-color: ${props => getThemeColors(props.theme).background.pressed};
  }
`;

// 星期標題行
const WeekHeader = styled.div`
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: ${spacing.xs};
`;

// 星期標題
const WeekDay = styled.div<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  
  font-size: 12px;
  font-weight: 500;
  color: ${props => getThemeColors(props.theme).text.secondary};
  text-align: center;
`;

// 日期網格
const DateGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
`;

// 日期單元格
const DateCell = styled.button<{
  theme: 'light' | 'dark';
  isToday?: boolean;
  isSelected?: boolean;
  isInRange?: boolean;
  isRangeStart?: boolean;
  isRangeEnd?: boolean;
  isOtherMonth?: boolean;
  disabled?: boolean;
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  
  background: none;
  border: none;
  border-radius: ${borderRadius.sm};
  font-size: 14px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  transition: ${transitions.fast};
  
  ${props => {
    const colors = getThemeColors(props.theme);
    
    if (props.disabled) {
      return `
        color: ${colors.text.disabled};
        opacity: 0.5;
      `;
    }
    
    if (props.isSelected || props.isRangeStart || props.isRangeEnd) {
      return `
        background-color: ${colors.accent.primary};
        color: ${colors.text.inverse};
      `;
    }
    
    if (props.isInRange) {
      return `
        background-color: ${colors.accent.primary}33;
        color: ${colors.text.primary};
      `;
    }
    
    if (props.isOtherMonth) {
      return `
        color: ${colors.text.disabled};
      `;
    }
    
    if (props.isToday) {
      return `
        color: ${colors.accent.primary};
        font-weight: 600;
        border: 1px solid ${colors.accent.primary};
      `;
    }
    
    return `
      color: ${colors.text.primary};
    `;
  }}
  
  &:hover {
    ${props => {
      if (props.disabled) return '';
      
      const colors = getThemeColors(props.theme);
      
      if (props.isSelected || props.isRangeStart || props.isRangeEnd) {
        return `background-color: ${colors.accent.hover};`;
      }
      
      return `
        background-color: ${colors.background.hover};
      `;
    }}
  }
`;

// 時間選擇器容器
const TimePickerContainer = styled.div<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  margin-top: ${spacing.md};
  padding-top: ${spacing.md};
  border-top: 1px solid ${props => getThemeColors(props.theme).border.secondary};
`;

// 時間輸入框
const TimeInput = styled.input<{
  theme: 'light' | 'dark';
}>`
  width: 60px;
  padding: ${spacing.xs} ${spacing.sm};
  
  background-color: ${props => getThemeColors(props.theme).background.primary};
  border: 1px solid ${props => getThemeColors(props.theme).border.primary};
  border-radius: ${borderRadius.sm};
  color: ${props => getThemeColors(props.theme).text.primary};
  
  font-size: 14px;
  text-align: center;
  transition: ${transitions.fast};
  
  &:focus {
    outline: none;
    border-color: ${props => getThemeColors(props.theme).accent.primary};
  }
`;

// 時間分隔符
const TimeSeparator = styled.span<{
  theme: 'light' | 'dark';
}>`
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-weight: 600;
`;

// 日期選擇器組件介面
export interface DatePickerProps {
  theme: 'light' | 'dark';
  value?: Date;
  defaultValue?: Date;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  placeholder?: string;
  format?: string;
  showTime?: boolean;
  minDate?: Date;
  maxDate?: Date;
  disabledDates?: Date[];
  onChange?: (date: Date | null) => void;
  className?: string;
}

/**
 * 日期選擇器組件
 * 用於日期和時間選擇
 */
export const DatePicker: React.FC<DatePickerProps> = ({
  theme,
  value: controlledValue,
  defaultValue,
  disabled = false,
  size = 'medium',
  variant = 'default',
  placeholder = '選擇日期',
  format = 'YYYY-MM-DD',
  showTime = false,
  minDate,
  maxDate,
  disabledDates = [],
  onChange,
  className
}) => {
  const [internalValue, setInternalValue] = useState<Date | null>(defaultValue || null);
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [inputValue, setInputValue] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  
  // 判斷是否為受控組件
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;
  
  // 格式化日期
  const formatDate = useCallback((date: Date | null) => {
    if (!date) return '';
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    let formatted = format
      .replace('YYYY', year.toString())
      .replace('MM', month)
      .replace('DD', day);
    
    if (showTime) {
      formatted += ` ${hours}:${minutes}`;
    }
    
    return formatted;
  }, [format, showTime]);
  
  // 解析日期字符串
  const parseDate = useCallback((dateString: string): Date | null => {
    if (!dateString) return null;
    
    try {
      const date = new Date(dateString);
      return isNaN(date.getTime()) ? null : date;
    } catch {
      return null;
    }
  }, []);
  
  // 更新輸入框值
  useEffect(() => {
    setInputValue(formatDate(value));
  }, [value, formatDate]);
  
  // 處理日期變更
  const handleDateChange = useCallback((newDate: Date | null) => {
    if (!isControlled) {
      setInternalValue(newDate);
    }
    
    onChange?.(newDate);
  }, [isControlled, onChange]);
  
  // 處理輸入框變更
  const handleInputChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setInputValue(newValue);
    
    const parsedDate = parseDate(newValue);
    if (parsedDate) {
      handleDateChange(parsedDate);
    }
  }, [parseDate, handleDateChange]);
  
  // 處理輸入框點擊
  const handleInputClick = useCallback(() => {
    if (!disabled) {
      setIsOpen(true);
    }
  }, [disabled]);
  
  // 處理日期選擇
  const handleDateSelect = useCallback((date: Date) => {
    const newDate = new Date(date);
    
    if (value && showTime) {
      newDate.setHours(value.getHours());
      newDate.setMinutes(value.getMinutes());
    }
    
    handleDateChange(newDate);
    
    if (!showTime) {
      setIsOpen(false);
    }
  }, [value, showTime, handleDateChange]);
  
  // 處理時間變更
  const handleTimeChange = useCallback((hours: number, minutes: number) => {
    if (!value) return;
    
    const newDate = new Date(value);
    newDate.setHours(hours);
    newDate.setMinutes(minutes);
    
    handleDateChange(newDate);
  }, [value, handleDateChange]);
  
  // 生成日曆日期
  const generateCalendarDates = useCallback(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const dates: Date[] = [];
    const current = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    
    return dates;
  }, [currentMonth]);
  
  // 檢查日期是否被禁用
  const isDateDisabled = useCallback((date: Date) => {
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    
    return disabledDates.some(disabledDate => 
      date.toDateString() === disabledDate.toDateString()
    );
  }, [minDate, maxDate, disabledDates]);
  
  // 處理外部點擊
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);
  
  const calendarDates = generateCalendarDates();
  const today = new Date();
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
  
  return (
    <DatePickerContainer
      ref={containerRef}
      theme={theme}
      disabled={disabled}
      size={size}
      className={className}
    >
      <DateInput
        theme={theme}
        size={size}
        variant={variant}
        value={inputValue}
        placeholder={placeholder}
        disabled={disabled}
        onChange={handleInputChange}
        onClick={handleInputClick}
        readOnly
      />
      
      <DatePickerPopover
        theme={theme}
        visible={isOpen}
        position="bottom"
      >
        <CalendarHeader theme={theme}>
          <NavButton
            theme={theme}
            onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
          >
            ‹
          </NavButton>
          
          <MonthYearDisplay theme={theme}>
            {currentMonth.getFullYear()}年 {currentMonth.getMonth() + 1}月
          </MonthYearDisplay>
          
          <NavButton
            theme={theme}
            onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
          >
            ›
          </NavButton>
        </CalendarHeader>
        
        <WeekHeader>
          {weekDays.map(day => (
            <WeekDay key={day} theme={theme}>
              {day}
            </WeekDay>
          ))}
        </WeekHeader>
        
        <DateGrid>
          {calendarDates.map((date, index) => {
            const isToday = date.toDateString() === today.toDateString();
            const isSelected = value && date.toDateString() === value.toDateString();
            const isOtherMonth = date.getMonth() !== currentMonth.getMonth();
            const disabled = isDateDisabled(date);
            
            return (
              <DateCell
                key={index}
                theme={theme}
                isToday={isToday}
                isSelected={isSelected}
                isOtherMonth={isOtherMonth}
                disabled={disabled}
                onClick={() => !disabled && handleDateSelect(date)}
              >
                {date.getDate()}
              </DateCell>
            );
          })}
        </DateGrid>
        
        {showTime && value && (
          <TimePickerContainer theme={theme}>
            <TimeInput
              theme={theme}
              type="number"
              min="0"
              max="23"
              value={value.getHours()}
              onChange={(e) => handleTimeChange(parseInt(e.target.value) || 0, value.getMinutes())}
            />
            <TimeSeparator theme={theme}>:</TimeSeparator>
            <TimeInput
              theme={theme}
              type="number"
              min="0"
              max="59"
              value={value.getMinutes()}
              onChange={(e) => handleTimeChange(value.getHours(), parseInt(e.target.value) || 0)}
            />
          </TimePickerContainer>
        )}
      </DatePickerPopover>
    </DatePickerContainer>
  );
};

// 日期範圍選擇器組件介面
export interface DateRangePickerProps {
  theme: 'light' | 'dark';
  value?: [Date | null, Date | null];
  defaultValue?: [Date | null, Date | null];
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  placeholder?: [string, string];
  format?: string;
  showTime?: boolean;
  minDate?: Date;
  maxDate?: Date;
  disabledDates?: Date[];
  onChange?: (dates: [Date | null, Date | null]) => void;
  className?: string;
}

/**
 * 日期範圍選擇器組件
 * 用於選擇日期範圍
 */
export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  theme,
  value: controlledValue,
  defaultValue = [null, null],
  disabled = false,
  size = 'medium',
  variant = 'default',
  placeholder = ['開始日期', '結束日期'],
  format = 'YYYY-MM-DD',
  showTime = false,
  minDate,
  maxDate,
  disabledDates = [],
  onChange,
  className
}) => {
  const [internalValue, setInternalValue] = useState<[Date | null, Date | null]>(defaultValue);
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [hoverDate, setHoverDate] = useState<Date | null>(null);
  const [selectingIndex, setSelectingIndex] = useState<0 | 1>(0);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // 判斷是否為受控組件
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;
  
  // 格式化日期
  const formatDate = useCallback((date: Date | null) => {
    if (!date) return '';
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    let formatted = format
      .replace('YYYY', year.toString())
      .replace('MM', month)
      .replace('DD', day);
    
    if (showTime) {
      formatted += ` ${hours}:${minutes}`;
    }
    
    return formatted;
  }, [format, showTime]);
  
  // 處理日期範圍變更
  const handleRangeChange = useCallback((newRange: [Date | null, Date | null]) => {
    if (!isControlled) {
      setInternalValue(newRange);
    }
    
    onChange?.(newRange);
  }, [isControlled, onChange]);
  
  // 處理日期選擇
  const handleDateSelect = useCallback((date: Date) => {
    const newRange: [Date | null, Date | null] = [...value];
    
    if (selectingIndex === 0 || !value[0] || (value[0] && value[1])) {
      // 選擇開始日期
      newRange[0] = date;
      newRange[1] = null;
      setSelectingIndex(1);
    } else {
      // 選擇結束日期
      if (date >= value[0]) {
        newRange[1] = date;
      } else {
        newRange[0] = date;
        newRange[1] = value[0];
      }
      setSelectingIndex(0);
      
      if (!showTime) {
        setIsOpen(false);
      }
    }
    
    handleRangeChange(newRange);
  }, [value, selectingIndex, showTime, handleRangeChange]);
  
  // 檢查日期是否在範圍內
  const isDateInRange = useCallback((date: Date) => {
    if (!value[0] || !value[1]) {
      if (value[0] && hoverDate && selectingIndex === 1) {
        const start = value[0] <= hoverDate ? value[0] : hoverDate;
        const end = value[0] <= hoverDate ? hoverDate : value[0];
        return date >= start && date <= end;
      }
      return false;
    }
    
    return date >= value[0] && date <= value[1];
  }, [value, hoverDate, selectingIndex]);
  
  // 檢查日期是否為範圍起點或終點
  const isRangeStart = useCallback((date: Date) => {
    return value[0] && date.toDateString() === value[0].toDateString();
  }, [value]);
  
  const isRangeEnd = useCallback((date: Date) => {
    return value[1] && date.toDateString() === value[1].toDateString();
  }, [value]);
  
  // 生成日曆日期
  const generateCalendarDates = useCallback(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const dates: Date[] = [];
    const current = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    
    return dates;
  }, [currentMonth]);
  
  // 檢查日期是否被禁用
  const isDateDisabled = useCallback((date: Date) => {
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    
    return disabledDates.some(disabledDate => 
      date.toDateString() === disabledDate.toDateString()
    );
  }, [minDate, maxDate, disabledDates]);
  
  const calendarDates = generateCalendarDates();
  const today = new Date();
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
  
  return (
    <DatePickerContainer
      ref={containerRef}
      theme={theme}
      disabled={disabled}
      size={size}
      className={className}
    >
      <div style={{ display: 'flex', gap: spacing.sm }}>
        <DateInput
          theme={theme}
          size={size}
          variant={variant}
          value={formatDate(value[0])}
          placeholder={placeholder[0]}
          disabled={disabled}
          onClick={() => !disabled && setIsOpen(true)}
          readOnly
        />
        <DateInput
          theme={theme}
          size={size}
          variant={variant}
          value={formatDate(value[1])}
          placeholder={placeholder[1]}
          disabled={disabled}
          onClick={() => !disabled && setIsOpen(true)}
          readOnly
        />
      </div>
      
      <DatePickerPopover
        theme={theme}
        visible={isOpen}
        position="bottom"
      >
        <CalendarHeader theme={theme}>
          <NavButton
            theme={theme}
            onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
          >
            ‹
          </NavButton>
          
          <MonthYearDisplay theme={theme}>
            {currentMonth.getFullYear()}年 {currentMonth.getMonth() + 1}月
          </MonthYearDisplay>
          
          <NavButton
            theme={theme}
            onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
          >
            ›
          </NavButton>
        </CalendarHeader>
        
        <WeekHeader>
          {weekDays.map(day => (
            <WeekDay key={day} theme={theme}>
              {day}
            </WeekDay>
          ))}
        </WeekHeader>
        
        <DateGrid>
          {calendarDates.map((date, index) => {
            const isToday = date.toDateString() === today.toDateString();
            const isSelected = isRangeStart(date) || isRangeEnd(date);
            const isInRange = isDateInRange(date);
            const isOtherMonth = date.getMonth() !== currentMonth.getMonth();
            const disabled = isDateDisabled(date);
            
            return (
              <DateCell
                key={index}
                theme={theme}
                isToday={isToday}
                isSelected={isSelected}
                isInRange={isInRange}
                isRangeStart={isRangeStart(date)}
                isRangeEnd={isRangeEnd(date)}
                isOtherMonth={isOtherMonth}
                disabled={disabled}
                onClick={() => !disabled && handleDateSelect(date)}
                onMouseEnter={() => setHoverDate(date)}
                onMouseLeave={() => setHoverDate(null)}
              >
                {date.getDate()}
              </DateCell>
            );
          })}
        </DateGrid>
      </DatePickerPopover>
    </DatePickerContainer>
  );
};

export default DatePicker;