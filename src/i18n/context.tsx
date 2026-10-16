import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Message } from "../model/messages";
import type { MessageKey } from "./cs";
import {
  LANGUAGE_KEY,
  formatNumber,
  selectLocale,
  translate,
  type Locale,
} from "./format";
function initialLocale(): Locale {
  let saved: string | null = null;
  try {
    saved = localStorage.getItem(LANGUAGE_KEY);
  } catch {
    /* Private browsing may disable storage. */
  }
  return selectLocale(
    new URL(location.href).searchParams.get("lang"),
    saved,
    navigator.languages,
  );
}
const I18nContext = createContext<ReturnType<typeof useLanguage> | null>(null);
function useLanguage() {
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const t = (key: MessageKey, values?: Message["values"]) =>
    translate(locale, key, values);
  const number = (value: number, digits?: number) =>
    formatNumber(locale, value, digits);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.title = `Bike Science Pro · ${translate(locale, "Ride with a plan")}`;
    document
      .querySelector('meta[name="description"]')
      ?.setAttribute(
        "content",
        translate(
          locale,
          "Plan your ride with local GPX analysis, cycling physics, gearing insights and controlled comparisons.",
        ),
      );
    try {
      localStorage.setItem(LANGUAGE_KEY, locale);
    } catch {
      /* Language still works for this visit. */
    }
  }, [locale]);
  const changeLocale = (next: Locale) => {
    const url = new URL(location.href);
    url.searchParams.set("lang", next);
    history.replaceState(null, "", url);
    setLocale(next);
  };
  return {
    locale,
    setLocale: changeLocale,
    t,
    number,
    formatMessage: (m: Message) => t(m.key, m.values),
    time: (s: number) => {
      const m = Math.max(1, Math.round(s / 60));
      return m < 60
        ? `${number(m)} min`
        : `${number(Math.floor(m / 60))} h ${number(m % 60)} min`;
    },
    savings: (s: number) =>
      Math.abs(s) < 30
        ? "<1 min"
        : `${number(Math.max(1, Math.round(Math.abs(s) / 60)))} min`,
  };
}
export function I18nProvider({ children }: { children: ReactNode }) {
  return (
    <I18nContext.Provider value={useLanguage()}>
      {children}
    </I18nContext.Provider>
  );
}
export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("I18nProvider is required");
  return context;
}
