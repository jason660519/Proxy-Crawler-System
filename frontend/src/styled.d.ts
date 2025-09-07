import 'styled-components';
import type { Theme } from './styles';

declare module 'styled-components' {
  export interface DefaultTheme {
    name: string;
    colors: {
      background: {
        primary: string;
        secondary: string;
        tertiary: string;
        elevated: string;
      };
      text: {
        primary: string;
        secondary: string;
        tertiary: string;
        inverse: string;
        disabled: string;
      };
      border: {
        primary: string;
        secondary: string;
        focus: string;
      };
      status: {
        success: string;
        warning: string;
        error: string;
        info: string;
      };
      interactive: {
        primary: string;
        primaryHover: string;
        primaryActive: string;
        secondary: string;
        secondaryHover: string;
        secondaryActive: string;
      };
      shadow: {
        light: string;
        medium: string;
        heavy: string;
      };
    };
    spacing: number[];
    borderRadius: {
      small: string;
      medium: string;
      large: string;
      full: string;
    };
    shadows: {
      small: string;
      medium: string;
      large: string;
      focus: string;
    };
    typography: {
      fontFamily: {
        primary: string;
        mono: string;
      };
      fontSize: {
        xs: string;
        sm: string;
        base: string;
        lg: string;
        xl: string;
        '2xl': string;
        '3xl': string;
      };
      fontWeight: {
        normal: number;
        medium: number;
        semibold: number;
        bold: number;
      };
      lineHeight: {
        tight: number;
        normal: number;
        relaxed: number;
      };
    };
  }
}