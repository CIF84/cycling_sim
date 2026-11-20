import { useRef, useState } from "react";
import { useI18n } from "../i18n/context";
import { formatElapsedTime } from "../i18n/format";
import type { Ride, Route } from "../model/types";
import type {
  FuelPlan,
  FuelSettings,
  FuelError,
  RefillStop,
} from "../model/fueling";
import { NumberField } from "./NumberField";

export function FuelPlanner({
  route,
  ride,
  enabled,
  onEnable,
  settings,
  onSettings,
  stops,
  plan,
  error,
  onAddStop,
  onRemoveStop,
  onInspect,
}: {
  route: Route;
  ride: Ride;
  enabled: boolean;
  onEnable: (v: boolean) => void;
  settings: FuelSettings;
  onSettings: (s: FuelSettings) => void;
  stops: RefillStop[];
  plan: FuelPlan | null;
  error: FuelError;
  onAddStop: (distanceM: number) => boolean;
  onRemoveStop: (id: number) => void;
  onInspect: (distanceM: number) => void;
}) {
  const { t, number, locale } = useI18n();
  const [stopKm, setStopKm] = useState(NaN);
  const [stopError, setStopError] = useState(false);
  const addButton = useRef<HTMLButtonElement>(null);
  const elapsed = (seconds: number) => formatElapsedTime(locale, seconds);
  const update = <K extends keyof FuelSettings>(
    key: K,
    value: FuelSettings[K],
  ) => onSettings({ ...settings, [key]: value });
  const issues = plan?.legs.filter((l) => l.reserveAtM !== null) ?? [];
  return (
    <section
      className="card fuel-planner"
      id="fuel-plan"
      aria-labelledby="fuel-title"
    >
      <div className="card-heading fuel-heading">
        <div>
          <span className="step-label">{t("02 / HOW SHOULD I PREPARE?")}</span>
          <h3 id="fuel-title">{t("Fuel & water plan")}</h3>
        </div>
        <button
          type="button"
          className="fuel-toggle"
          aria-expanded={enabled}
          aria-controls={enabled ? "fuel-details" : undefined}
          onClick={() => onEnable(!enabled)}
        >
          {t(enabled ? "Hide plan" : "Build my plan")}
        </button>
      </div>
      <div className="fuel-content">
        {!enabled && (
          <p className="fuel-intro">
            {t(
              "See energy spent, plan carbohydrate intake and check how far your bottles cover. Add your own refill stops. Everything stays in this tab.",
            )}
          </p>
        )}
        <div className="fuel-totals" aria-label={t("Energy and supplies")}>
          <div>
            <span>{t("Estimated expenditure")}</span>
            <strong data-testid="fuel-expenditure">
              {number(Math.round(ride.kcalLow / 50) * 50)}–
              {number(Math.round(ride.kcalHigh / 50) * 50)} <small>kcal</small>
            </strong>
            <p>{t("During pedaling · 18–25% efficiency")}</p>
          </div>
          {enabled && plan && (
            <>
              <div>
                <span>{t("Planned carbohydrate intake")}</span>
                <strong data-testid="fuel-carbs">
                  {number(Math.round(plan.carbsG))} <small>g</small>
                </strong>
                <p data-testid="fuel-intake">
                  ≈ {number(Math.round(plan.intakeKcal / 10) * 10)} kcal ·{" "}
                  {number(plan.carbGph)} g/h
                </p>
              </div>
              <div>
                <span>{t("Planned fluid")}</span>
                <strong data-testid="fuel-fluid">
                  {number(plan.fluidMl / 1000, 1)} <small>l</small>
                </strong>
                <p>
                  {t("Start with {litres} l in your bottles", {
                    litres: number(plan.capacityMl / 1000, 1),
                  })}
                </p>
              </div>
            </>
          )}
        </div>
        {enabled && (
          <div id="fuel-details">
            <p className="fuel-distinction">
              {t(
                "Intake supports the ride; it does not replace every calorie spent. Carbohydrates include food and drinks. This is a plan, not a measurement of your needs or remaining body energy.",
              )}
            </p>
            {route.trackCount > 1 && (
              <p className="fuel-warning">
                {t(
                  "Track breaks omit travel. This plan cannot cover the missing sections; allow extra supplies.",
                )}
              </p>
            )}
            <div className="fuel-controls">
              <div className="field">
                <label htmlFor="fuel-carbs">{t("Carbohydrate target")}</label>
                <select
                  id="fuel-carbs"
                  value={settings.carbGph ?? "auto"}
                  onChange={(e) =>
                    update(
                      "carbGph",
                      e.target.value === "auto" ? null : Number(e.target.value),
                    )
                  }
                >
                  <option value="auto">
                    {t("Starting plan for this duration")}
                  </option>
                  {[0, 30, 45, 60, 75, 90].map((v) => (
                    <option key={v} value={v}>
                      {v} g/h
                    </option>
                  ))}
                </select>
                <small>
                  {t(
                    "Editable starting point: 0 g/h under 1 h, 45 g/h for 1–2.5 h, 60 g/h above 2.5 h. Use what you have practiced.",
                  )}
                </small>
              </div>
              <NumberField
                label={t("Planning drinking rate")}
                value={settings.drinkMlph}
                onChange={(v) => update("drinkMlph", v)}
                min={100}
                max={2000}
                unit="ml/h"
                help={t(
                  "500 ml/h is an example, not a sweat estimate. Adjust for your experience and conditions; do not force drinking to match it.",
                )}
              />
              <NumberField
                label={t("Number of bottles")}
                value={settings.bottles}
                onChange={(v) => update("bottles", v)}
                min={1}
                max={6}
                unit=""
              />
              <NumberField
                label={t("Volume per bottle")}
                value={settings.bottleMl}
                onChange={(v) => update("bottleMl", v)}
                min={100}
                max={2000}
                unit="ml"
              />
            </div>
            {error && (
              <p className="fuel-warning" role="alert">
                {t(
                  error === "duration"
                    ? "Planning supports up to 24 h of modeled moving time."
                    : error === "stops"
                      ? "Refill stops must be inside this route, at least 10 m apart, with no more than eight stops."
                      : "Check plan inputs: carbs 0–90 g/h, fluid 100–2,000 ml/h, 1–6 whole bottles of 100–2,000 ml, and a reserve no larger than capacity.",
                )}
              </p>
            )}
            {plan && (
              <>
                {plan.carbGph > 60 && (
                  <p className="fuel-warning">
                    {t(
                      "Above 60 g/h: use only a practiced strategy with suitable carbohydrate mixtures and gut tolerance. Longer duration does not automatically mean you need 90 g/h.",
                    )}
                  </p>
                )}
                {plan.carbGph === 0 && (
                  <p className="caption">
                    {t(
                      "No carbohydrate intake is planned. Short easy rides may not need an on-bike fuel schedule; longer or harder rides can. Zero modeled work does not mean zero body energy use.",
                    )}
                  </p>
                )}
                <div className="fuel-coverage" data-testid="fuel-coverage">
                  <h4>{t("Will my bottles cover the route?")}</h4>
                  <p>
                    {issues.length
                      ? t("Your plan needs attention before these points:")
                      : t(
                          "The modeled legs fit your bottle capacity, including the chosen reserve.",
                        )}
                  </p>
                  {issues.map((leg) => (
                    <p className="fuel-warning" key={leg.startM}>
                      <button
                        type="button"
                        onClick={() => onInspect(leg.reserveAtM!)}
                      >
                        {t("Reserve reached near {distance} km", {
                          distance: number(leg.reserveAtM! / 1000, 1),
                        })}
                      </button>
                      {" · "}
                      {leg.emptyAtM !== null
                        ? t(
                            "Bottles run out near {distance} km, before the next refill or finish.",
                            { distance: number(leg.emptyAtM / 1000, 1) },
                          )
                        : t(
                            "This leg uses part of your reserve. Refill earlier or carry more.",
                          )}
                    </p>
                  ))}
                  <p className="caption">
                    {t(
                      "Starts full; each marked stop refills all bottles. Coverage follows your chosen rate, not predicted thirst. Carrying more does not mean drinking it all.",
                    )}
                  </p>
                </div>
              </>
            )}
            <div className="fuel-stops">
              <h4>{t("Your water refill stops")}</h4>
              <p className="caption">
                {t(
                  "Add a known water stop by distance or at the chart cursor. Check access yourself. These are water refills, not food resupply points.",
                )}
              </p>
              <div className="fuel-add-stop">
                <NumberField
                  allowEmpty
                  label={t("Refill at distance")}
                  value={stopKm}
                  onChange={(v) => {
                    setStopKm(v);
                    setStopError(false);
                  }}
                  min={0}
                  max={route.distanceM / 1000}
                  unit="km"
                />
                <button
                  ref={addButton}
                  type="button"
                  onClick={() => {
                    const added = onAddStop(stopKm * 1000);
                    setStopError(!added);
                    if (added) setStopKm(NaN);
                  }}
                >
                  {t("Add refill stop")}
                </button>
              </div>
              {stopError && (
                <p className="fuel-warning" role="alert">
                  {t(
                    "Choose a point inside the route, at least 10 m from another stop. Maximum eight stops.",
                  )}
                </p>
              )}
              {stops.length === 0 && (
                <p className="caption">
                  {t(
                    "No refills planned. Bring enough for the whole modeled ride.",
                  )}
                </p>
              )}
              <ol className="fuel-stop-list">
                {[...stops]
                  .sort((a, b) => a.distanceM - b.distanceM)
                  .map((stop, i) => {
                    const planned = plan?.stops.find((s) => s.id === stop.id);
                    const leg = plan?.legs[i];
                    return (
                      <li key={stop.id}>
                        <button
                          type="button"
                          className="fuel-stop-inspect"
                          onClick={() => onInspect(stop.distanceM)}
                        >
                          {t("Refill {number}", { number: i + 1 })} ·{" "}
                          {number(stop.distanceM / 1000, 1)} km
                          {planned && (
                            <small>
                              {elapsed(planned.timeS)} ·{" "}
                              {t("Top up about {litres} l", {
                                litres: number((leg?.refillMl ?? 0) / 1000, 1),
                              })}
                            </small>
                          )}
                        </button>
                        <button
                          className="fuel-remove"
                          type="button"
                          aria-label={t("Remove refill {number}", {
                            number: i + 1,
                          })}
                          onClick={() => {
                            onRemoveStop(stop.id);
                            addButton.current?.focus();
                          }}
                        >
                          {t("Remove")}
                        </button>
                      </li>
                    );
                  })}
              </ol>
            </div>
            {plan && plan.windows.length > 0 && (
              <details className="fuel-timing">
                <summary>
                  {t("Fuel timing along the route")} <span>+</span>
                </summary>
                <p className="caption">
                  {t(
                    "Spread intake through each 20-minute window, starting early. Markers sit at window midpoints, not exact eating deadlines. Include carbs in drinks; choose safe, comfortable moments.",
                  )}
                </p>
                <div className="fuel-window-list">
                  {plan.windows.map((w, i) => (
                    <button
                      type="button"
                      key={w.startS}
                      onClick={() => onInspect(w.distanceM)}
                      aria-label={t("Inspect fuel window {number}", {
                        number: i + 1,
                      })}
                    >
                      <span>
                        {elapsed(w.startS)}–{elapsed(w.endS)}
                      </span>
                      <strong>≈ {number(Math.round(w.carbsG))} g</strong>
                      <small>~{number(w.distanceM / 1000, 1)} km</small>
                    </button>
                  ))}
                </div>
              </details>
            )}
            <details className="fuel-assumptions">
              <summary>
                {t("Reserve, guidance & assumptions")} <span>+</span>
              </summary>
              <NumberField
                label={t("Water reserve")}
                value={settings.reserveMl}
                onChange={(v) => update("reserveMl", v)}
                min={0}
                max={settings.bottles * settings.bottleMl}
                unit="ml"
                help={t(
                  "Extra carried capacity, not extra prescribed drinking. The 250 ml example is editable.",
                )}
              />
              <p>
                {t(
                  "AIS guidance for endurance exercise: 30–60 g/h over 1–2.5 h; up to 90 g/h for longer events with a practiced strategy. Shorter rides depend on intensity and prior eating. Our starting rates and 20-minute windows are planning choices.",
                )}
              </p>
              <p>
                {t(
                  "Fluid needs vary with the rider and conditions. This planner does not calculate sweat, sodium needs, absorption or glycogen. Expenditure omits coasting and resting metabolism. Plan extra for stops, delays and missing route sections.",
                )}
              </p>
              <p>
                {t(
                  "Plan quantities do not change bike mass automatically. Include carried water and food in Kit & water. Plans and stops stay in memory and clear on refresh; route changes clear stops.",
                )}
              </p>
              <p className="fuel-sources">
                <a
                  href="https://www.ausport.gov.au/ais/nutrition/supplements/group_a/sports-foods2/sports-drink/how-and-when-do-i-use-it"
                  target="_blank"
                  rel="noreferrer"
                >
                  {t("AIS carbohydrate guidance")}
                </a>
                <a
                  href="https://pmc.ncbi.nlm.nih.gov/articles/PMC5634236/"
                  target="_blank"
                  rel="noreferrer"
                >
                  {t("NATA fluid guidance")}
                </a>
              </p>
            </details>
          </div>
        )}
      </div>
    </section>
  );
}
