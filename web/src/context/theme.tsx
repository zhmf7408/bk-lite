'use client';

import { createContext, useContext, useState, ReactNode, useEffect, useMemo } from 'react';
import { ConfigProvider } from 'antd';
import dayjs from 'dayjs';
import { ThemeConfig } from 'antd/es/config-provider/context';
import { lightTheme, darkTheme } from '@/constants/theme';
import { useTranslation } from '@/utils/i18n';
import { locales, LocaleKey } from '@/constants/locales';
import { dayjsLocales } from '@/constants/dayjsLocales';
import { useLocale } from '@/context/locale';
import { normalizeLocale } from '@/utils/userPreferences';

const ThemeContext = createContext<{
  theme: ThemeConfig;
  themeName: string;
  setTheme: (isDark: boolean) => void;
    } | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState(lightTheme);
  const [themeName, setThemeName] = useState<string>('light');
  const { locale } = useLocale();

  const normalizedLocale = normalizeLocale(locale);
  const antdLocale = useMemo(() => locales[normalizedLocale as LocaleKey] || locales.en, [normalizedLocale]);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setThemeName(savedTheme);
    if (savedTheme === 'dark') {
      setTheme(darkTheme);
      document.documentElement.classList.add('dark');
    } else {
      setTheme(lightTheme);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  useEffect(() => {
    dayjs.locale(dayjsLocales[normalizedLocale as LocaleKey] || dayjsLocales.en);
  }, [normalizedLocale]);

  const changeTheme = (isDark: boolean) => {
    const newTheme = isDark ? darkTheme : lightTheme;
    setTheme(newTheme);
    const name = isDark ? 'dark' : 'light';
    setThemeName(name);
    localStorage.setItem('theme', name);
    document.documentElement.classList.toggle('dark', isDark);
  };

  return (
    <ThemeContext.Provider value={{ theme, themeName, setTheme: changeTheme }}>
      <ConfigProvider theme={theme} locale={antdLocale}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const { t } = useTranslation();
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error(t('common.useThemeError'));
  }
  return context;
};
