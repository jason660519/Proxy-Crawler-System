import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// 語言資源
import zhTW from './locales/zh-TW.json'
import enUS from './locales/en.json'

// 支援的語言列表
export const supportedLanguages = {
  'zh-TW': '繁體中文',
  'en-US': 'English',
} as const

export type SupportedLanguage = keyof typeof supportedLanguages

// 初始化 i18next
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    // 預設語言
    fallbackLng: 'zh-TW',
    
    // 支援的語言
    supportedLngs: Object.keys(supportedLanguages),
    
    // 語言資源
    resources: {
      'zh-TW': {
        translation: zhTW,
      },
      'en-US': {
        translation: enUS,
      },
    },
    
    // 語言檢測配置
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
    
    // 插值配置
    interpolation: {
      escapeValue: false, // React 已經處理 XSS
    },
    
    // 開發模式配置
    debug: import.meta.env.DEV,
    
    // 載入配置
    load: 'languageOnly',
    
    // 命名空間
    defaultNS: 'translation',
    
    // 鍵值分隔符
    keySeparator: '.',
    nsSeparator: ':',
    
    // 複數規則
    pluralSeparator: '_',
    
    // 上下文分隔符
    contextSeparator: '_',
    
    // 後備鍵
    saveMissing: import.meta.env.DEV,
    
    // 更新缺失鍵
    updateMissing: import.meta.env.DEV,
    
    // 返回物件
    returnObjects: true,
    
    // 返回空字串
    returnEmptyString: false,
    
    // 返回 null
    returnNull: false,
  })

export default i18n

// 語言切換工具函數
export const changeLanguage = (language: SupportedLanguage) => {
  return i18n.changeLanguage(language)
}

// 獲取當前語言
export const getCurrentLanguage = (): SupportedLanguage => {
  const currentLang = i18n.language
  return (currentLang in supportedLanguages 
    ? currentLang 
    : 'zh-TW') as SupportedLanguage
}

// 獲取語言顯示名稱
export const getLanguageDisplayName = (language: SupportedLanguage): string => {
  return supportedLanguages[language]
}

// 檢查是否為支援的語言
export const isSupportedLanguage = (language: string): language is SupportedLanguage => {
  return language in supportedLanguages
}