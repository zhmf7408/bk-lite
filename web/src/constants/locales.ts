import enUS from 'antd/lib/locale/en_US';
import zhCN from 'antd/lib/locale/zh_CN';

export const locales = {
  'en': enUS,
  'zh-Hans': zhCN,
  'zh-CN': zhCN,
  'zh': zhCN,
};

export type LocaleKey = keyof typeof locales;
