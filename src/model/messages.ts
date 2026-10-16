import type { MessageKey } from "../i18n/cs";
export type MessageValue =
  string | number | Message | { number: number; digits: number };
export interface Message {
  key: MessageKey;
  values?: Record<string, MessageValue>;
}
export const message = (
  key: MessageKey,
  values?: Message["values"],
): Message => ({ key, values });
// Keep Error.message useful to callers outside the UI, including numerical tests.
export function englishMessage(m: Message): string {
  return m.key.replace(/\{(\w+)\}/g, (_, key: string) => {
    const value = m.values?.[key];
    if (typeof value === "object")
      return "key" in value
        ? englishMessage(value)
        : value.number.toFixed(value.digits);
    return String(value ?? `{${key}}`);
  });
}
export class ModelError extends Error {
  readonly detail: Message;
  constructor(key: MessageKey, values?: Message["values"]) {
    const detail = message(key, values);
    super(englishMessage(detail));
    this.detail = detail;
  }
}
