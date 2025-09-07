/**
 * 表單組件 - VS Code 風格的表單控制組件
 * 提供表單驗證、字段管理、布局控制等功能
 */

import React, { useState, useCallback, useRef, useEffect, createContext, useContext } from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions } from '../../styles/GlobalStyles';

// 表單容器
const FormContainer = styled.form<{
  theme: 'light' | 'dark';
  layout: 'vertical' | 'horizontal' | 'inline';
  size: 'small' | 'medium' | 'large';
}>`
  display: flex;
  flex-direction: ${props => props.layout === 'inline' ? 'row' : 'column'};
  gap: ${props => {
    switch (props.size) {
      case 'small': return spacing.sm;
      case 'large': return spacing.xl;
      default: return spacing.lg;
    }
  }};
  
  ${props => props.layout === 'inline' && `
    flex-wrap: wrap;
    align-items: flex-start;
  `}
`;

// 表單項目容器
const FormItemContainer = styled.div<{
  theme: 'light' | 'dark';
  layout: 'vertical' | 'horizontal' | 'inline';
  size: 'small' | 'medium' | 'large';
  required?: boolean;
  error?: boolean;
  span?: number;
}>`
  display: flex;
  flex-direction: ${props => props.layout === 'horizontal' ? 'row' : 'column'};
  align-items: ${props => props.layout === 'horizontal' ? 'flex-start' : 'stretch'};
  gap: ${props => {
    switch (props.size) {
      case 'small': return spacing.xs;
      case 'large': return spacing.md;
      default: return spacing.sm;
    }
  }};
  
  ${props => props.layout === 'inline' && `
    flex: ${props.span ? `0 0 ${(props.span / 24) * 100}%` : '0 0 auto'};
    min-width: 200px;
  `}
  
  ${props => props.layout === 'horizontal' && `
    align-items: center;
  `}
`;

// 表單標籤
const FormLabel = styled.label<{
  theme: 'light' | 'dark';
  layout: 'vertical' | 'horizontal' | 'inline';
  size: 'small' | 'medium' | 'large';
  required?: boolean;
  width?: string | number;
}>`
  display: flex;
  align-items: center;
  color: ${props => getThemeColors(props.theme).text.primary};
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '12px';
      case 'large': return '16px';
      default: return '14px';
    }
  }};
  font-weight: 500;
  line-height: 1.4;
  
  ${props => props.layout === 'horizontal' && `
    flex: 0 0 ${props.width ? (typeof props.width === 'number' ? props.width + 'px' : props.width) : '120px'};
    text-align: right;
    padding-right: ${spacing.md};
  `}
  
  ${props => props.required && `
    &::before {
      content: '*';
      color: ${getThemeColors(props.theme).status.error};
      margin-right: 4px;
    }
  `}
`;

// 表單控制區域
const FormControl = styled.div<{
  theme: 'light' | 'dark';
  layout: 'vertical' | 'horizontal' | 'inline';
}>`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: ${spacing.xs};
`;

// 表單錯誤信息
const FormError = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  color: ${props => getThemeColors(props.theme).status.error};
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '11px';
      case 'large': return '14px';
      default: return '12px';
    }
  }};
  line-height: 1.4;
  margin-top: 2px;
`;

// 表單幫助文本
const FormHelp = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '11px';
      case 'large': return '14px';
      default: return '12px';
    }
  }};
  line-height: 1.4;
  margin-top: 2px;
`;

// 表單分組容器
const FormGroup = styled.fieldset<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large';
}>`
  border: 1px solid ${props => getThemeColors(props.theme).border.secondary};
  border-radius: ${borderRadius.md};
  padding: ${props => {
    switch (props.size) {
      case 'small': return spacing.md;
      case 'large': return spacing.xl;
      default: return spacing.lg;
    }
  }};
  margin: 0;
  
  legend {
    color: ${props => getThemeColors(props.theme).text.primary};
    font-weight: 600;
    font-size: ${props => {
      switch (props.size) {
        case 'small': return '13px';
        case 'large': return '17px';
        default: return '15px';
      }
    }};
    padding: 0 ${spacing.sm};
  }
`;

// 表單操作區域
const FormActions = styled.div<{
  theme: 'light' | 'dark';
  layout: 'vertical' | 'horizontal' | 'inline';
  align?: 'left' | 'center' | 'right';
}>`
  display: flex;
  gap: ${spacing.md};
  margin-top: ${spacing.lg};
  
  ${props => {
    switch (props.align) {
      case 'center': return 'justify-content: center;';
      case 'right': return 'justify-content: flex-end;';
      default: return 'justify-content: flex-start;';
    }
  }}
  
  ${props => props.layout === 'horizontal' && `
    margin-left: 120px;
  `}
`;

// 表單按鈕
const FormButton = styled.button<{
  theme: 'light' | 'dark';
  variant: 'primary' | 'secondary' | 'danger' | 'ghost';
  size: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.xs};
  
  padding: ${props => {
    switch (props.size) {
      case 'small': return `${spacing.xs} ${spacing.sm}`;
      case 'large': return `${spacing.md} ${spacing.xl}`;
      default: return `${spacing.sm} ${spacing.lg}`;
    }
  }};
  
  background-color: ${props => {
    const colors = getThemeColors(props.theme);
    if (props.disabled || props.loading) return colors.background.disabled;
    
    switch (props.variant) {
      case 'primary': return colors.accent.primary;
      case 'danger': return colors.status.error;
      case 'ghost': return 'transparent';
      default: return colors.background.secondary;
    }
  }};
  
  border: 1px solid ${props => {
    const colors = getThemeColors(props.theme);
    if (props.disabled || props.loading) return colors.border.disabled;
    
    switch (props.variant) {
      case 'primary': return colors.accent.primary;
      case 'danger': return colors.status.error;
      case 'ghost': return colors.border.primary;
      default: return colors.border.primary;
    }
  }};
  
  border-radius: ${borderRadius.sm};
  
  color: ${props => {
    const colors = getThemeColors(props.theme);
    if (props.disabled || props.loading) return colors.text.disabled;
    
    switch (props.variant) {
      case 'primary': return colors.text.inverse;
      case 'danger': return colors.text.inverse;
      default: return colors.text.primary;
    }
  }};
  
  font-size: ${props => {
    switch (props.size) {
      case 'small': return '12px';
      case 'large': return '16px';
      default: return '14px';
    }
  }};
  
  font-weight: 500;
  cursor: ${props => (props.disabled || props.loading) ? 'not-allowed' : 'pointer'};
  transition: ${transitions.fast};
  
  &:hover {
    ${props => !(props.disabled || props.loading) && `
      background-color: ${(() => {
        const colors = getThemeColors(props.theme);
        switch (props.variant) {
          case 'primary': return colors.accent.hover;
          case 'danger': return colors.status.errorHover;
          case 'ghost': return colors.background.hover;
          default: return colors.background.hover;
        }
      })()};
    `}
  }
  
  &:focus {
    outline: 2px solid ${props => getThemeColors(props.theme).accent.primary};
    outline-offset: 2px;
  }
`;

// 驗證規則介面
export interface ValidationRule {
  required?: boolean;
  pattern?: RegExp;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  validator?: (value: any) => string | null;
  message?: string;
}

// 表單字段介面
export interface FormField {
  name: string;
  value: any;
  error?: string;
  touched?: boolean;
  rules?: ValidationRule[];
}

// 表單狀態介面
export interface FormState {
  values: Record<string, any>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isValid: boolean;
  isSubmitting: boolean;
}

// 表單上下文
interface FormContextType {
  formState: FormState;
  updateField: (name: string, value: any) => void;
  validateField: (name: string) => void;
  setFieldTouched: (name: string, touched: boolean) => void;
  theme: 'light' | 'dark';
  layout: 'vertical' | 'horizontal' | 'inline';
  size: 'small' | 'medium' | 'large';
  disabled?: boolean;
}

const FormContext = createContext<FormContextType | null>(null);

// 使用表單上下文的 Hook
export const useFormContext = () => {
  const context = useContext(FormContext);
  if (!context) {
    throw new Error('useFormContext must be used within a Form component');
  }
  return context;
};

// 表單項目組件介面
export interface FormItemProps {
  name: string;
  label?: string;
  required?: boolean;
  rules?: ValidationRule[];
  help?: string;
  span?: number;
  labelWidth?: string | number;
  children: React.ReactNode;
  className?: string;
}

/**
 * 表單項目組件
 * 用於包裝表單控件並提供標籤、驗證等功能
 */
export const FormItem: React.FC<FormItemProps> = ({
  name,
  label,
  required,
  rules = [],
  help,
  span,
  labelWidth,
  children,
  className
}) => {
  const { formState, theme, layout, size } = useFormContext();
  
  const error = formState.errors[name];
  const hasError = !!error;
  
  return (
    <FormItemContainer
      theme={theme}
      layout={layout}
      size={size}
      required={required}
      error={hasError}
      span={span}
      className={className}
    >
      {label && (
        <FormLabel
          theme={theme}
          layout={layout}
          size={size}
          required={required}
          width={labelWidth}
        >
          {label}
        </FormLabel>
      )}
      
      <FormControl theme={theme} layout={layout}>
        {children}
        
        {hasError && (
          <FormError theme={theme} size={size}>
            {error}
          </FormError>
        )}
        
        {!hasError && help && (
          <FormHelp theme={theme} size={size}>
            {help}
          </FormHelp>
        )}
      </FormControl>
    </FormItemContainer>
  );
};

// 表單組件介面
export interface FormProps {
  theme: 'light' | 'dark';
  layout?: 'vertical' | 'horizontal' | 'inline';
  size?: 'small' | 'medium' | 'large';
  initialValues?: Record<string, any>;
  disabled?: boolean;
  onSubmit?: (values: Record<string, any>) => void | Promise<void>;
  onValuesChange?: (changedValues: Record<string, any>, allValues: Record<string, any>) => void;
  validateTrigger?: 'onChange' | 'onBlur' | 'onSubmit';
  children: React.ReactNode;
  className?: string;
}

/**
 * 表單組件
 * 提供表單狀態管理、驗證和提交功能
 */
export const Form: React.FC<FormProps> = ({
  theme,
  layout = 'vertical',
  size = 'medium',
  initialValues = {},
  disabled = false,
  onSubmit,
  onValuesChange,
  validateTrigger = 'onChange',
  children,
  className
}) => {
  const [formState, setFormState] = useState<FormState>({
    values: { ...initialValues },
    errors: {},
    touched: {},
    isValid: true,
    isSubmitting: false
  });
  
  const rulesRef = useRef<Record<string, ValidationRule[]>>({});
  
  // 驗證單個字段
  const validateField = useCallback((name: string, value: any = formState.values[name]) => {
    const rules = rulesRef.current[name] || [];
    
    for (const rule of rules) {
      // 必填驗證
      if (rule.required && (!value || (typeof value === 'string' && !value.trim()))) {
        return rule.message || `${name} 是必填項目`;
      }
      
      // 跳過空值的其他驗證
      if (!value && typeof value !== 'number') continue;
      
      // 正則驗證
      if (rule.pattern && !rule.pattern.test(String(value))) {
        return rule.message || `${name} 格式不正確`;
      }
      
      // 最小值驗證
      if (rule.min !== undefined && Number(value) < rule.min) {
        return rule.message || `${name} 不能小於 ${rule.min}`;
      }
      
      // 最大值驗證
      if (rule.max !== undefined && Number(value) > rule.max) {
        return rule.message || `${name} 不能大於 ${rule.max}`;
      }
      
      // 最小長度驗證
      if (rule.minLength !== undefined && String(value).length < rule.minLength) {
        return rule.message || `${name} 長度不能少於 ${rule.minLength} 個字符`;
      }
      
      // 最大長度驗證
      if (rule.maxLength !== undefined && String(value).length > rule.maxLength) {
        return rule.message || `${name} 長度不能超過 ${rule.maxLength} 個字符`;
      }
      
      // 自定義驗證
      if (rule.validator) {
        const error = rule.validator(value);
        if (error) return error;
      }
    }
    
    return null;
  }, [formState.values]);
  
  // 更新字段值
  const updateField = useCallback((name: string, value: any) => {
    setFormState(prev => {
      const newValues = { ...prev.values, [name]: value };
      const newErrors = { ...prev.errors };
      
      // 驗證字段
      if (validateTrigger === 'onChange' || prev.touched[name]) {
        const error = validateField(name, value);
        if (error) {
          newErrors[name] = error;
        } else {
          delete newErrors[name];
        }
      }
      
      const newState = {
        ...prev,
        values: newValues,
        errors: newErrors,
        isValid: Object.keys(newErrors).length === 0
      };
      
      // 觸發值變化回調
      onValuesChange?.({ [name]: value }, newValues);
      
      return newState;
    });
  }, [validateField, validateTrigger, onValuesChange]);
  
  // 設置字段為已觸摸
  const setFieldTouched = useCallback((name: string, touched: boolean) => {
    setFormState(prev => {
      const newTouched = { ...prev.touched, [name]: touched };
      const newErrors = { ...prev.errors };
      
      // 如果是失焦驗證且字段被觸摸，進行驗證
      if (validateTrigger === 'onBlur' && touched) {
        const error = validateField(name);
        if (error) {
          newErrors[name] = error;
        } else {
          delete newErrors[name];
        }
      }
      
      return {
        ...prev,
        touched: newTouched,
        errors: newErrors,
        isValid: Object.keys(newErrors).length === 0
      };
    });
  }, [validateField, validateTrigger]);
  
  // 驗證所有字段
  const validateAllFields = useCallback(() => {
    const errors: Record<string, string> = {};
    
    Object.keys(rulesRef.current).forEach(name => {
      const error = validateField(name);
      if (error) {
        errors[name] = error;
      }
    });
    
    setFormState(prev => ({
      ...prev,
      errors,
      isValid: Object.keys(errors).length === 0
    }));
    
    return Object.keys(errors).length === 0;
  }, [validateField]);
  
  // 處理表單提交
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (disabled || formState.isSubmitting) return;
    
    setFormState(prev => ({ ...prev, isSubmitting: true }));
    
    try {
      // 驗證所有字段
      const isValid = validateTrigger === 'onSubmit' ? validateAllFields() : formState.isValid;
      
      if (isValid && onSubmit) {
        await onSubmit(formState.values);
      }
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setFormState(prev => ({ ...prev, isSubmitting: false }));
    }
  }, [disabled, formState.isSubmitting, formState.isValid, formState.values, validateTrigger, validateAllFields, onSubmit]);
  
  // 註冊字段規則
  const registerField = useCallback((name: string, rules: ValidationRule[]) => {
    rulesRef.current[name] = rules;
  }, []);
  
  // 提供給子組件的上下文值
  const contextValue: FormContextType = {
    formState,
    updateField,
    validateField: (name: string) => {
      const error = validateField(name);
      setFormState(prev => {
        const newErrors = { ...prev.errors };
        if (error) {
          newErrors[name] = error;
        } else {
          delete newErrors[name];
        }
        return {
          ...prev,
          errors: newErrors,
          isValid: Object.keys(newErrors).length === 0
        };
      });
    },
    setFieldTouched,
    theme,
    layout,
    size,
    disabled
  };
  
  // 註冊字段規則
  useEffect(() => {
    const registerRules = (element: React.ReactElement) => {
      if (element.type === FormItem) {
        const { name, rules = [] } = element.props;
        if (name) {
          registerField(name, rules);
        }
      }
      
      if (element.props?.children) {
        React.Children.forEach(element.props.children, child => {
          if (React.isValidElement(child)) {
            registerRules(child);
          }
        });
      }
    };
    
    React.Children.forEach(children, child => {
      if (React.isValidElement(child)) {
        registerRules(child);
      }
    });
  }, [children, registerField]);
  
  return (
    <FormContext.Provider value={contextValue}>
      <FormContainer
        theme={theme}
        layout={layout}
        size={size}
        onSubmit={handleSubmit}
        className={className}
      >
        {children}
      </FormContainer>
    </FormContext.Provider>
  );
};

// 表單分組組件介面
export interface FormGroupProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * 表單分組組件
 * 用於將相關的表單項目分組顯示
 */
export const FormGroup: React.FC<FormGroupProps> = ({
  title,
  children,
  className
}) => {
  const { theme, size } = useFormContext();
  
  return (
    <FormGroup theme={theme} size={size} className={className}>
      <legend>{title}</legend>
      {children}
    </FormGroup>
  );
};

// 表單操作組件介面
export interface FormActionsProps {
  align?: 'left' | 'center' | 'right';
  children: React.ReactNode;
  className?: string;
}

/**
 * 表單操作組件
 * 用於放置表單提交、重置等操作按鈕
 */
export const FormActions: React.FC<FormActionsProps> = ({
  align = 'left',
  children,
  className
}) => {
  const { theme, layout } = useFormContext();
  
  return (
    <FormActions theme={theme} layout={layout} align={align} className={className}>
      {children}
    </FormActions>
  );
};

// 表單按鈕組件介面
export interface FormButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  type?: 'button' | 'submit' | 'reset';
  loading?: boolean;
  disabled?: boolean;
  onClick?: (e: React.MouseEvent) => void;
  children: React.ReactNode;
  className?: string;
}

/**
 * 表單按鈕組件
 * 用於表單操作的按鈕
 */
export const FormButton: React.FC<FormButtonProps> = ({
  variant = 'secondary',
  type = 'button',
  loading = false,
  disabled = false,
  onClick,
  children,
  className
}) => {
  const { theme, size, formState } = useFormContext();
  
  const isDisabled = disabled || (type === 'submit' && formState.isSubmitting);
  const isLoading = loading || (type === 'submit' && formState.isSubmitting);
  
  return (
    <FormButton
      theme={theme}
      variant={variant}
      size={size}
      type={type}
      loading={isLoading}
      disabled={isDisabled}
      onClick={onClick}
      className={className}
    >
      {isLoading && (
        <span style={{ 
          display: 'inline-block',
          width: '14px',
          height: '14px',
          border: '2px solid currentColor',
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
      )}
      {children}
    </FormButton>
  );
};

export default Form;