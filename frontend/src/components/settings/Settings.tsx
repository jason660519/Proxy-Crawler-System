/**
 * 系統設定頁
 * 放置主題調試器與其他開發者選項
 */

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { ThemeDebugger } from '../debug/ThemeDebugger';
import { useTheme } from '../../hooks';

const Container = styled.div`
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
`;

const Section = styled.section`
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid var(--color-border-primary);
  border-radius: 8px;
  background: var(--color-background-elevated);
`;

const Title = styled.h2`
  margin: 0 0 12px 0;
  font-size: 1.25rem;
  color: var(--color-text-primary);
`;

const Row = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Toggle = styled.input.attrs({ type: 'checkbox' })``;

export const Settings: React.FC = () => {
  const { theme, isDark } = useTheme();
  const [showThemeDebugger, setShowThemeDebugger] = useState<boolean>(false);

  useEffect(() => {
    try {
      const saved = window.sessionStorage.getItem('js-theme-debugger') === '1';
      setShowThemeDebugger(Boolean(saved));
    } catch {}
  }, []);

  useEffect(() => {
    try {
      if (showThemeDebugger) {
        window.sessionStorage.setItem('js-theme-debugger', '1');
      } else {
        window.sessionStorage.removeItem('js-theme-debugger');
      }
    } catch {}
  }, [showThemeDebugger]);

  return (
    <Container>
      <Section>
        <Title>開發者選項</Title>
        <Row>
          <Toggle
            checked={showThemeDebugger}
            onChange={(e) => setShowThemeDebugger(e.target.checked)}
          />
          <span>顯示主題調試器（僅開發模式）</span>
        </Row>
      </Section>

      {showThemeDebugger && (
        <Section>
          <Title>主題調試器</Title>
          <ThemeDebugger theme={theme} isDark={isDark} isVisible inline />
        </Section>
      )}
    </Container>
  );
};

export default Settings;


