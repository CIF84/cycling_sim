import { cs, type MessageKey } from "./cs";
import type { Message } from "../model/messages";
export type Locale = "en" | "cs";
export const LANGUAGE_KEY = "bike-science-language";
export const isLocale = (value: unknown): value is Locale =>
  value === "en" || value === "cs";
export function selectLocale(
  query: string | null,
  saved: string | null,
  languages: readonly string[],
): Locale {
  if (isLocale(query)) return query;
  if (isLocale(saved)) return saved;
  return languages[0]?.toLowerCase().split("-")[0] === "cs" ? "cs" : "en";
}
export function formatNumber(locale: Locale, n: number, digits?: number) {
  return new Intl.NumberFormat(locale === "cs" ? "cs-CZ" : "en-GB", {
    maximumFractionDigits: digits ?? 4,
    ...(digits === undefined ? {} : { minimumFractionDigits: digits }),
  }).format(n);
}
export function translate(
  locale: Locale,
  key: MessageKey,
  values?: Message["values"],
): string {
  return (locale === "cs" ? cs[key] : key).replace(
    /\{(\w+)\}/g,
    (_, token: string) => {
      const value = values?.[token];
      if (typeof value === "number") return formatNumber(locale, value);
      if (typeof value === "object")
        return "key" in value
          ? translate(locale, value.key, value.values)
          : formatNumber(locale, value.number, value.digits);
      return value ?? `{${token}}`;
    },
  );
}
// Decimal comma and decimal point are both accepted. Mixed separators, exponents
// and partial garbage must never silently turn into a plausible ride input.
export function parseDecimal(text: string): number {
  const value = text.trim();
  if (!/^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(value)) return NaN;
  return Number(value.replace(",", "."));
}
export const decimalText = (locale: Locale, n: number) =>
  Number.isFinite(n) ? String(n).replace(".", locale === "cs" ? "," : ".") : "";
