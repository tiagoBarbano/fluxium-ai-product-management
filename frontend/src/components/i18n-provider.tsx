"use client";

import { createContext, useContext, useMemo, useState } from "react";
import type { Locale } from "@/lib/i18n";
import { messages } from "@/lib/i18n";

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, values?: Record<string, string | number>) => string;
};

export const I18nContext = createContext<I18nContextValue>({
  locale: "pt-BR",
  setLocale: () => undefined,
  t: (key) => messages["pt-BR"][key] ?? key,
});

export function useI18n() {
  return useContext(I18nContext);
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("pt-BR");

  const value = useMemo<I18nContextValue>(() => ({
    locale,
    setLocale: (nextLocale) => {
      setLocaleState(nextLocale);
      window.localStorage.setItem("fluxium_locale", nextLocale);
    },
    t: (key, values) => {
      const template = messages[locale][key] ?? messages["pt-BR"][key] ?? key;
      return Object.entries(values ?? {}).reduce(
        (result, [name, replacement]) => result.replace(`{${name}}`, String(replacement)),
        template,
      );
    },
  }), [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
