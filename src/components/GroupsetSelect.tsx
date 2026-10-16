import { useId } from "react";
import { ArrowUpRight } from "lucide-react";
import { useI18n } from "../i18n/context";
import type { MessageKey } from "../i18n/cs";
import {
  GEARING_CHECKED_ON,
  GROUPSET_PRESETS,
  type GroupsetCategory,
  type GroupsetPreset,
} from "../model/gearing";

const categories: { id: GroupsetCategory; label: MessageKey }[] = [
  { id: "shimano-road", label: "Shimano · Road" },
  { id: "shimano-gravel", label: "Shimano · Gravel" },
  { id: "shimano-cues", label: "Shimano · Road & gravel" },
  { id: "sram-road", label: "SRAM · Road" },
  { id: "sram-gravel", label: "SRAM · Gravel" },
];

export function GroupsetSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (preset: GroupsetPreset | null) => void;
}) {
  const { t, locale } = useI18n();
  const id = useId();
  const preset = GROUPSET_PRESETS.find((p) => p.id === value);
  return (
    <div className="groupset-picker">
      <label className="field" htmlFor={id}>
        {t("Groupset preset")}
      </label>
      <select
        id={id}
        value={value}
        aria-describedby={`${id}-help`}
        onChange={(e) =>
          onChange(
            GROUPSET_PRESETS.find((p) => p.id === e.target.value) ?? null,
          )
        }
      >
        {categories.map((category) => (
          <optgroup key={category.id} label={t(category.label)}>
            {GROUPSET_PRESETS.filter((p) => p.category === category.id).map(
              (p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ),
            )}
          </optgroup>
        ))}
        <option value="custom">{t("Custom gearing")}</option>
      </select>
      <small id={`${id}-help`}>
        {t(
          "Example setups, not every available combination. Check the gearing fitted to your bike, or edit it below.",
        )}
      </small>
      {preset && (
        <div className="gearing-preset" data-testid="gearing-preset">
          <div className="gearing-preset-heading">
            <strong>{preset.name}</strong>
            <span>
              {preset.chainrings.length}×{preset.cassette.cogs.length}
            </span>
          </div>
          <dl>
            <div>
              <dt>{t("Front chainrings")}</dt>
              <dd>
                {[...preset.chainrings].reverse().join(" / ")}{" "}
                <span>{t("teeth")}</span>
              </dd>
            </div>
            <div>
              <dt>{t("Cassette")}</dt>
              <dd>
                {preset.cassette.cogs[0]}–{preset.cassette.cogs.at(-1)}{" "}
                <span>{t("teeth")}</span>
              </dd>
            </div>
          </dl>
          <p>
            {t("{front} front × {rear} rear gears", {
              front: preset.chainrings.length,
              rear: preset.cassette.cogs.length,
            })}
          </p>
          <details className="gearing-sources">
            <summary>{t("Manufacturer specifications")}</summary>
            <ul>
              {[preset.crank, preset.cassette, preset.derailleur].map(
                (part) => (
                  <li key={part.model}>
                    <a href={part.url} target="_blank" rel="noreferrer">
                      {part.model}
                      <ArrowUpRight size={12} aria-hidden="true" />
                    </a>
                  </li>
                ),
              )}
            </ul>
            <small>
              {t(
                "Checked {date}. Presets describe gearing only; they do not check fit on your bike.",
                {
                  date: new Intl.DateTimeFormat(locale, {
                    day: "numeric",
                    month: "numeric",
                    year: "numeric",
                    timeZone: "UTC",
                  }).format(new Date(`${GEARING_CHECKED_ON}T00:00:00Z`)),
                },
              )}
            </small>
          </details>
        </div>
      )}
      <small className="gearing-model-note">
        {t(
          "Gearing changes cadence in this model. Power, weight and estimated ride time stay the same.",
        )}
      </small>
    </div>
  );
}
