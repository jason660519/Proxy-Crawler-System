/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // VS Code 風格色彩系統
        vscode: {
          // 深色主題 (預設)
          dark: {
            bg: '#1e1e1e',
            'bg-secondary': '#252526',
            'bg-tertiary': '#2d2d30',
            sidebar: '#333333',
            'sidebar-hover': '#2a2d2e',
            panel: '#252526',
            border: '#3e3e42',
            text: '#cccccc',
            'text-secondary': '#969696',
            'text-muted': '#6a6a6a',
            accent: '#007acc',
            'accent-hover': '#1177bb',
            success: '#4ec9b0',
            warning: '#ffcc02',
            error: '#f44747',
            info: '#75beff'
          },
          // 淺色主題
          light: {
            bg: '#ffffff',
            'bg-secondary': '#f8f8f8',
            'bg-tertiary': '#f0f0f0',
            sidebar: '#f3f3f3',
            'sidebar-hover': '#e8e8e8',
            panel: '#f8f8f8',
            border: '#e5e5e5',
            text: '#333333',
            'text-secondary': '#666666',
            'text-muted': '#999999',
            accent: '#0066cc',
            'accent-hover': '#005bb5',
            success: '#00aa44',
            warning: '#ff9900',
            error: '#e51400',
            info: '#0099ff'
          }
        },
        // 代理狀態色彩
        proxy: {
          online: '#4ade80',
          offline: '#ef4444',
          testing: '#f59e0b',
          unknown: '#6b7280',
          premium: '#8b5cf6',
          free: '#06b6d4'
        }
      },
      fontFamily: {
        'mono': ['Consolas', 'Monaco', 'Courier New', 'monospace'],
        'sans': ['Segoe UI', 'Tahoma', 'Geneva', 'Verdana', 'sans-serif']
      },
      fontSize: {
        'xs': '0.75rem',
        'sm': '0.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem'
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem'
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounceSubtle 1s ease-in-out infinite'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-2px)' }
        }
      },
      boxShadow: {
        'vscode': '0 2px 8px rgba(0, 0, 0, 0.15)',
        'vscode-hover': '0 4px 12px rgba(0, 0, 0, 0.2)'
      },
      borderRadius: {
        'vscode': '3px'
      }
    },
  },
  plugins: [
    // 自定義工具類
    function({ addUtilities }) {
      const newUtilities = {
        '.scrollbar-thin': {
          'scrollbar-width': 'thin',
          'scrollbar-color': '#6b7280 transparent'
        },
        '.scrollbar-webkit': {
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px'
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent'
          },
          '&::-webkit-scrollbar-thumb': {
            'background-color': '#6b7280',
            'border-radius': '4px',
            border: '2px solid transparent',
            'background-clip': 'content-box'
          },
          '&::-webkit-scrollbar-thumb:hover': {
            'background-color': '#4b5563'
          }
        },
        '.text-shadow': {
          'text-shadow': '0 1px 2px rgba(0, 0, 0, 0.1)'
        }
      }
      addUtilities(newUtilities)
    }
  ],
}