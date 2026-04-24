interface LocaleData {
  locale: string;
  messages: Record<string, string>;
}

let localeData: LocaleData = {
  locale: 'en',
  messages: {},
};

export const setLocaleData = (locale: string, messages: Record<string, string>) => {
  localeData = { locale, messages };
};

export const getLocaleData = (): LocaleData => localeData;
