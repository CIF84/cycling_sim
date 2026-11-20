import { useEffect, useId, useRef, useState } from "react";
import { useI18n } from "../i18n/context";
import { decimalText, parseDecimal } from "../i18n/format";
export function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  unit,
  help,
  allowEmpty = false,
}: {
  label: string;
  value: number;
  onChange: (n: number) => void;
  min: number;
  max: number;
  unit: string;
  help?: string;
  allowEmpty?: boolean;
}) {
  const id = useId();
  const { locale } = useI18n();
  const [text, setText] = useState(() => decimalText(locale, value));
  const previousLocale = useRef(locale);
  useEffect(() => {
    const changed = previousLocale.current !== locale;
    setText((current) =>
      (changed && Number.isFinite(value)) ||
      !Object.is(parseDecimal(current), value)
        ? decimalText(locale, value)
        : current,
    );
    previousLocale.current = locale;
  }, [value, locale]);
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="number-wrap">
        <input
          id={id}
          type="text"
          inputMode={min < 0 ? "text" : "decimal"}
          value={text}
          aria-invalid={
            allowEmpty && text === ""
              ? false
              : !Number.isFinite(value) || value < min || value > max
          }
          onChange={(e) => {
            setText(e.target.value);
            onChange(parseDecimal(e.target.value));
          }}
          aria-describedby={help ? `${id}-help` : undefined}
        />
        <span>{unit}</span>
      </div>
      {help && <small id={`${id}-help`}>{help}</small>}
    </div>
  );
}
