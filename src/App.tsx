import { useI18n } from "./i18n/context";
import { decimalText, isLocale, parseDecimal } from "./i18n/format";
import { message, type Message } from "./model/messages";
import { useEffect, useId, useRef, useState } from "react";
import {
  Bike,
  ArrowUpRight,
  Upload,
  ShieldCheck,
  Mountain,
  Clock3,
  Gauge,
  ChevronRight,
  SlidersHorizontal,
  Wind,
  Check,
  RotateCcw,
  Download,
  Info,
  ArrowDown,
  FlaskConical,
  CircleAlert,
  LoaderCircle,
  Route as RouteIcon,
} from "lucide-react";
import {
  DEFAULT_INPUTS,
  type Inputs,
  type Route,
  type Ride,
  type Comparison,
} from "./model/types";
import { demoRoute } from "./model/route";
import { cadence } from "./model/physics";
import { Profile } from "./components/Profile";
import { GroupsetSelect } from "./components/GroupsetSelect";
import { DEFAULT_GROUPSET_ID, applyGroupset, sameTeeth } from "./model/gearing";
import "./style.css";
function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  unit,
  help,
}: {
  label: string;
  value: number;
  onChange: (n: number) => void;
  min: number;
  max: number;
  unit: string;
  help?: string;
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
          aria-invalid={!Number.isFinite(value) || value < min || value > max}
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
function TeethField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number[];
  onChange: (v: number[]) => void;
}) {
  const { t } = useI18n();
  const [text, setText] = useState(value.join(", "));
  useEffect(() => setText(value.join(", ")), [value]);
  return (
    <div className="field">
      <label>
        {label}
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={() =>
            onChange(
              text
                .split(",")
                .map((t) => (t.trim() === "" ? NaN : Number(t.trim()))),
            )
          }
          onKeyDown={(e) => {
            if (e.key === "Enter") e.currentTarget.blur();
          }}
        />
      </label>
      <small>
        {" "}
        {t(
          "Comma-separated tooth counts. Applied when you leave this field.",
        )}{" "}
      </small>
    </div>
  );
}
function climbs(route: Route, ride: Ride) {
  const groups: {
    start: number;
    end: number;
    gain: number;
    timeS: number;
    distance: number;
    maxGrade: number;
    minCadence: number;
    track: number;
  }[] = [];
  ride.segments.forEach((s, n) => {
    if (s.gradePct < 2) return;
    const prev = groups.at(-1),
      track = route.segments[n].track;
    if (prev && Math.abs(prev.end - s.startM) < 0.1 && prev.track === track) {
      prev.end += s.distanceM;
      prev.distance += s.distanceM;
      prev.gain += route.segments[n].deltaM;
      prev.timeS += s.timeS;
      prev.maxGrade = Math.max(prev.maxGrade, s.gradePct);
      prev.minCadence = Math.min(prev.minCadence, s.cadence ?? Infinity);
    } else
      groups.push({
        start: s.startM,
        end: s.startM + s.distanceM,
        gain: route.segments[n].deltaM,
        timeS: s.timeS,
        distance: s.distanceM,
        maxGrade: s.gradePct,
        minCadence: s.cadence ?? Infinity,
        track,
      });
  });
  return groups
    .filter((g) => g.distance >= 100)
    .sort((a, b) => b.timeS - a.timeS)
    .slice(0, 3);
}
export default function App() {
  const { locale, setLocale, t, number, formatMessage, time, savings } =
    useI18n();
  const [groupsetId, setGroupsetId] = useState(DEFAULT_GROUPSET_ID);
  const [inputs, setInputs] = useState<Inputs>({ ...DEFAULT_INPUTS });
  const [source, setSource] = useState<{ xml: string; name: string } | null>(
      null,
    ),
    [smoothingM, setSmoothingM] = useState(100);
  const [route, setRoute] = useState<Route>(demoRoute),
    [result, setResult] = useState<{
      ride: Ride;
      comparisons: Comparison[];
    } | null>(null);
  const [busy, setBusy] = useState(true),
    [error, setError] = useState<Message | null>(null),
    [importError, setImportError] = useState<Message | null>(null);
  const fileRef = useRef<HTMLInputElement>(null),
    workId = useRef(0),
    importId = useRef(0);
  function update<K extends keyof Inputs>(key: K, value: Inputs[K]) {
    setInputs((i) => ({ ...i, [key]: value }));
  }
  useEffect(() => {
    setBusy(true);
    setError(null);
    const id = ++workId.current;
    const worker = new Worker(new URL("./model/worker.ts", import.meta.url), {
      type: "module",
    });
    worker.onmessage = (e) => {
      if (e.data.id !== id) return;
      setBusy(false);
      if (e.data.error) {
        setError(e.data.error);
        setResult(null);
      } else {
        setRoute(e.data.route);
        setResult({ ride: e.data.ride, comparisons: e.data.comparisons });
      }
      worker.terminate();
    };
    worker.onerror = () => {
      setBusy(false);
      setError(
        message(
          "The calculation could not start. Refresh the page and try again.",
        ),
      );
      setResult(null);
      worker.terminate();
    };
    worker.postMessage({
      id,
      inputs,
      ...(source ? { xml: source.xml, name: source.name, smoothingM } : {}),
    });
    return () => worker.terminate();
  }, [inputs, source, smoothingM]);
  async function importFile(file?: File) {
    if (!file) return;
    const currentImport = ++importId.current;
    setImportError(null);
    if (file.size > 10 * 1024 * 1024) {
      setImportError(
        message(
          "Please choose a GPX smaller than 10 MB. Your current route is unchanged.",
        ),
      );
      return;
    }
    if (!/\.gpx$/i.test(file.name)) {
      setImportError(
        message("Please choose a .gpx file. Your current route is unchanged."),
      );
      return;
    }
    try {
      const xml = await file.text();
      if (currentImport !== importId.current) return;
      setSource({ xml, name: file.name });
    } catch {
      setImportError(message("This file could not be read. Please try again."));
    }
  }
  const ride = result?.ride,
    demanding = ride ? climbs(route, ride) : [],
    worst = demanding[0];
  const comparisons = result?.comparisons ?? [];
  const availableComparisons = comparisons.filter((c) => c.available);
  const bestChange = availableComparisons.find((c) => c.savedS > 0.5);
  const largestDifference = Math.max(
    1,
    ...availableComparisons.map((c) => Math.abs(c.savedS)),
  );
  function reset() {
    ++importId.current;
    if (source) {
      setRoute(demoRoute());
      setResult(null);
    }
    setSource(null);
    setImportError(null);
    if (fileRef.current) fileRef.current.value = "";
  }
  const routeName = route.source === "demo" ? t("The Sunday Loop") : route.name;
  function exportBrief() {
    if (!ride) return;
    const comparisonText = comparisons
      .map(
        (c) =>
          `${t(c.title)}: ${
            c.available
              ? `${savings(c.savedS)} ${t(c.savedS < -0.5 ? "slower" : c.savedS > 0.5 ? "saved" : "difference")}`
              : `${t("Unavailable.")} ${t(c.reason)}`
          }`,
      )
      .join("\n");
    const text = [
      `Bike Science Pro · ${t("Public beta")}`,
      routeName,
      "",
      t("{distance} km · {ascent} m ascent", {
        distance: number(route.distanceM / 1000, 1),
        ascent: Math.round(route.ascentM),
      }),
      `${t("Estimated moving time")}: ${time(ride.timeS)}`,
      `${t("Average speed")}: ${number(ride.speedKmh, 1)} km/h`,
      `${t("Sustainable crank power")}: ${number(inputs.powerW)} W`,
      `${t("System mass")}: ${number(inputs.riderKg + inputs.bikeKg + inputs.kitKg)} kg`,
      `CdA ${number(inputs.cda)} m² · Crr ${number(inputs.crr)}`,
      `${t("Front chainrings")}: ${inputs.chainrings.join(", ")}`,
      `${t("Cassette cogs")}: ${inputs.cogs.join(", ")}`,
      t(
        "Wind: {wind} km/h (+ headwind) · {temperature} °C · air-density altitude {altitude} m",
        {
          wind: inputs.windKmh,
          temperature: inputs.temperatureC,
          altitude: inputs.altitudeM,
        },
      ),
      t("Speed ceiling: {speed} km/h · coast below −3%: {coast}", {
        speed: inputs.speedLimitKmh,
        coast: t(inputs.coastDescents ? "true" : "false"),
      }),
      `${t("Crank work")}: ${number(Math.round(ride.workKj))} kJ`,
      "",
      ...route.warnings.map(formatMessage),
      "",
      t(
        "Steady-state planning estimate, not a finish-time promise. No stops, traffic, corners, acceleration, crosswind or fatigue model. Descent ceiling is a modelling assumption, not a recommended speed.",
      ),
      t("Comparisons change one variable at a time:"),
      comparisonText,
      "",
      t(
        "Model and sources: see Assumptions & limitations in the app. GPX processed locally; no coordinates in this briefing.",
      ),
      "",
    ].join("\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download =
      locale === "cs"
        ? "bike-science-prehled.txt"
        : "bike-science-briefing.txt";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <>
      <a className="skip" href="#briefing">
        {" "}
        {t("Skip to ride briefing")}{" "}
      </a>
      <header className="header">
        <a href="#" className="brand">
          <span className="brand-icon">
            <Bike size={25} />
          </span>
          <span>
            Bike Science <strong>Pro</strong>
          </span>
        </a>
        <span className="beta">{t("PUBLIC BETA")}</span>
        <nav aria-label={t("Main")}>
          <a href="#briefing">{t("Ride briefing")}</a>
          <a href="#comparisons">{t("Compare changes")}</a>
          <a href="#model">
            {" "}
            {t("The model")} <ArrowUpRight size={14} />
          </a>
        </nav>
        <div className="language-switch">
          <label htmlFor="language" className="sr-only">
            {t("Language")}
          </label>
          <select
            id="language"
            value={locale}
            onChange={(e) => {
              if (isLocale(e.target.value)) setLocale(e.target.value);
            }}
          >
            <option value="en" lang="en">
              English
            </option>
            <option value="cs" lang="cs">
              Čeština
            </option>
          </select>
        </div>
        <span className="privacy">
          <ShieldCheck size={15} /> {t("GPX stays on your device")}{" "}
        </span>
      </header>
      <main>
        <section className="hero">
          <div>
            <div className="eyebrow">
              <span /> {t("LESS GUESSWORK. BETTER RIDES.")}{" "}
            </div>
            <h1>
              {" "}
              {t("Know the ride.")} <br />
              <em>{t("Ride with a plan.")}</em>
            </h1>
            <p>
              {" "}
              {t(
                "Understand the effort, prepare for the climbs, and see which changes matter on your route.",
              )}{" "}
            </p>
            <div className="hero-links">
              <a href="#briefing" onClick={reset}>
                {" "}
                {t("Explore the demo")} <ArrowDown size={15} />
              </a>
              <span>{t("No sign-up. No upload.")}</span>
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <svg viewBox="0 0 520 230">
              <path
                d="M0 150 120 95 175 125 280 15 355 100 430 65 520 125V230H0Z"
                fill="#dae4ce"
              />
              <path
                d="M0 180 105 145 190 160 295 75 340 130 420 115 520 170V230H0Z"
                fill="#a9bd97"
              />
              <path
                d="M0 213 95 175 180 194 275 155 335 180 430 158 520 207V230H0Z"
                fill="#597557"
              />
              <path
                d="M0 220C100 212 135 185 205 198S312 228 352 209 397 172 460 186 492 201 520 200"
                fill="none"
                stroke="#e5f0ab"
                strokeWidth="3"
                strokeDasharray="5 6"
              />
              <circle cx="352" cy="209" r="6" fill="#e5f0ab" />
            </svg>
            <div className="art-label">
              <Mountain size={14} /> {t("EVERY ROUTE HAS A STORY")}{" "}
            </div>
          </div>
        </section>
        <div className="workspace">
          <aside className="setup">
            <div className="setup-heading">
              <SlidersHorizontal size={18} />
              <h2>{t("Your ride setup")}</h2>
            </div>
            <section className="route-input">
              <span className="field-label">{t("01 / THE ROUTE")}</span>
              <div className="selected-route">
                <RouteIcon size={19} />
                <div>
                  <strong>
                    {source
                      ? source.name.replace(/\.gpx$/i, "")
                      : t("The Sunday Loop")}
                  </strong>
                  <small>
                    {source
                      ? t("Local GPX file")
                      : t("38 km · rolling hills · synthetic demo")}
                  </small>
                </div>
              </div>
              <input
                className="sr-only"
                ref={fileRef}
                id="gpx-file"
                aria-label={t("Choose GPX file")}
                type="file"
                accept=".gpx,application/gpx+xml"
                onChange={(e) => {
                  void importFile(e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
              <button
                className="upload-button"
                onClick={() => fileRef.current?.click()}
              >
                <Upload size={16} /> {t("Import your GPX")}{" "}
                <ChevronRight size={15} />
              </button>
              <p className="caption">
                {" "}
                {t(
                  "Up to 10 MB / 100,000 points. Read locally, never uploaded.",
                )}{" "}
              </p>
              {source && (
                <button className="text-button" onClick={reset}>
                  <RotateCcw size={13} /> {t("Return to demo & clear GPX")}{" "}
                </button>
              )}
              {importError && (
                <p className="field-error" role="alert">
                  {formatMessage(importError)}
                </p>
              )}
              {source && (
                <label className="field">
                  {" "}
                  {t("Elevation smoothing")}{" "}
                  <select
                    value={smoothingM}
                    onChange={(e) => setSmoothingM(Number(e.target.value))}
                  >
                    <option value={0}>
                      {t("Off · raw resampled elevation")}
                    </option>
                    <option value={100}>{t("100 m · balanced")}</option>
                    <option value={200}>{t("200 m · noisy recordings")}</option>
                  </select>
                  <small>
                    {" "}
                    {t(
                      "Distance-based median filter. Smoothing can hide short ramps.",
                    )}{" "}
                  </small>
                </label>
              )}
            </section>
            <section className="rider-input">
              <span className="field-label">{t("02 / RIDER & BIKE")}</span>
              <div className="field-pair">
                <NumberField
                  label={t("Rider weight")}
                  value={inputs.riderKg}
                  onChange={(v) => update("riderKg", v)}
                  min={30}
                  max={200}
                  unit="kg"
                />
                <NumberField
                  label={t("Bike weight")}
                  value={inputs.bikeKg}
                  onChange={(v) => update("bikeKg", v)}
                  min={3}
                  max={45}
                  unit="kg"
                />
              </div>
              <NumberField
                label={t("Kit & water")}
                value={inputs.kitKg}
                onChange={(v) => update("kitKg", v)}
                min={0}
                max={40}
                unit="kg"
              />
              <NumberField
                label={t("Sustainable power")}
                value={inputs.powerW}
                onChange={(v) => update("powerW", v)}
                min={0}
                max={700}
                unit="W"
                help={t(
                  "Average pedaling power you can hold for this ride, measured at the cranks. Use less than FTP for a long endurance ride.",
                )}
              />
              <div className="power-note">
                <Gauge size={15} />
                {Number.isFinite(inputs.powerW / inputs.riderKg)
                  ? number(inputs.powerW / inputs.riderKg, 1)
                  : "—"}{" "}
                W/kg <span>{t("· for context, not a fitness score")}</span>
              </div>
              <label className="field">
                {" "}
                {t("Surface & tires")}{" "}
                <select
                  value={
                    [0.004, 0.005, 0.008, 0.012].includes(inputs.crr)
                      ? inputs.crr
                      : "custom"
                  }
                  onChange={(e) => {
                    if (e.target.value !== "custom")
                      update("crr", Number(e.target.value));
                  }}
                >
                  <option value={0.004}>{t("Smooth road · fast tires")}</option>
                  <option value={0.005}>{t("Typical paved road")}</option>
                  <option value={0.008}>{t("Firm gravel")}</option>
                  <option value={0.012}>{t("Rough gravel")}</option>
                  <option value="custom" disabled>
                    {" "}
                    {t("Custom · edit in Conditions")}{" "}
                  </option>
                </select>
                <small>
                  {" "}
                  {t(
                    "Approximate resistance presets, not tire measurements.",
                  )}{" "}
                </small>
              </label>
              <label className="field">
                {" "}
                {t("Riding position")}{" "}
                <select
                  value={
                    [0.3, 0.35, 0.45].includes(inputs.cda)
                      ? inputs.cda
                      : "custom"
                  }
                  onChange={(e) => {
                    if (e.target.value !== "custom")
                      update("cda", Number(e.target.value));
                  }}
                >
                  <option value={0.3}>
                    {t("Low on the drops · CdA 0.30")}
                  </option>
                  <option value={0.35}>{t("Relaxed road · CdA 0.35")}</option>
                  <option value={0.45}>{t("Upright · CdA 0.45")}</option>
                  <option value="custom" disabled>
                    {" "}
                    {t("Custom · edit in Conditions")}{" "}
                  </option>
                </select>
                <small>
                  {" "}
                  {t(
                    "Drag area combines body position and air resistance. Individual values vary widely.",
                  )}{" "}
                </small>
              </label>
            </section>
            <details className="advanced">
              <summary>
                <Wind size={16} /> {t("Conditions & model")} <span>+</span>
              </summary>
              <div className="details-body">
                <NumberField
                  label={t("Along-route wind")}
                  value={inputs.windKmh}
                  onChange={(v) => update("windKmh", v)}
                  min={-60}
                  max={60}
                  unit="km/h"
                  help={t(
                    "Positive = headwind, negative = tailwind. Applied to the entire route; not a weather forecast.",
                  )}
                />
                <div className="field-pair">
                  <NumberField
                    label={t("Temperature")}
                    value={inputs.temperatureC}
                    onChange={(v) => update("temperatureC", v)}
                    min={-15}
                    max={45}
                    unit="°C"
                  />
                  <NumberField
                    label={t("Air-density altitude")}
                    value={inputs.altitudeM}
                    onChange={(v) => update("altitudeM", v)}
                    min={-400}
                    max={5000}
                    unit="m"
                  />
                </div>
                <small>
                  {" "}
                  {t(
                    "Altitude and temperature estimate air density only, not heat stress or physiological performance.",
                  )}{" "}
                </small>
                <NumberField
                  label={t("Aerodynamic drag (CdA)")}
                  value={inputs.cda}
                  onChange={(v) => update("cda", v)}
                  min={0.15}
                  max={0.8}
                  unit="m²"
                />
                <NumberField
                  label={t("Rolling resistance (Crr)")}
                  value={inputs.crr}
                  onChange={(v) => update("crr", v)}
                  min={0.001}
                  max={0.03}
                  unit=""
                />
                <NumberField
                  label={t("Speed ceiling")}
                  value={inputs.speedLimitKmh}
                  onChange={(v) => update("speedLimitKmh", v)}
                  min={15}
                  max={80}
                  unit="km/h"
                  help={t(
                    "Braking assumption for the model. Not a safe-speed recommendation; corners are not modeled.",
                  )}
                />
                <label className="check-field">
                  <input
                    type="checkbox"
                    checked={inputs.coastDescents}
                    onChange={(e) => update("coastDescents", e.target.checked)}
                  />{" "}
                  {t("Coast on descents of −3% or steeper")}{" "}
                </label>
                <NumberField
                  label={t("Drivetrain efficiency")}
                  value={inputs.efficiency * 100}
                  onChange={(v) => update("efficiency", v / 100)}
                  min={85}
                  max={100}
                  unit="%"
                />
              </div>
            </details>
            <details className="advanced">
              <summary>
                <Bike size={16} /> {t("Gearing & cadence")} <span>+</span>
              </summary>
              <div className="details-body">
                <GroupsetSelect
                  value={groupsetId}
                  onChange={(preset) => {
                    setGroupsetId(preset?.id ?? "custom");
                    if (preset)
                      setInputs((current) => applyGroupset(current, preset));
                  }}
                />
                <TeethField
                  label={t("Front chainrings")}
                  value={inputs.chainrings}
                  onChange={(v) => {
                    if (!sameTeeth(v, inputs.chainrings))
                      setGroupsetId("custom");
                    update("chainrings", v);
                  }}
                />
                <TeethField
                  label={t("Cassette cogs")}
                  value={inputs.cogs}
                  onChange={(v) => {
                    if (!sameTeeth(v, inputs.cogs)) setGroupsetId("custom");
                    update("cogs", v);
                  }}
                />
                <NumberField
                  label={t("Wheel circumference")}
                  value={inputs.wheelM}
                  onChange={(v) => update("wheelM", v)}
                  min={1.5}
                  max={2.5}
                  unit="m"
                  help={t(
                    "2.105 m is an illustrative 700C road tire; measure one wheel revolution for your bike.",
                  )}
                />
                <NumberField
                  label={t("Preferred cadence")}
                  value={inputs.cadenceRpm}
                  onChange={(v) => update("cadenceRpm", v)}
                  min={50}
                  max={110}
                  unit={t("rpm")}
                />
                <small>
                  {" "}
                  {t(
                    "Virtual gear selection finds the nearest cadence. Cross-chaining and derailleur compatibility are not checked.",
                  )}{" "}
                </small>
              </div>
            </details>
            <button
              className="reset-button"
              onClick={() => {
                setInputs({ ...DEFAULT_INPUTS });
                setGroupsetId(DEFAULT_GROUPSET_ID);
              }}
            >
              <RotateCcw size={14} /> {t("Reset ride inputs")}{" "}
            </button>
          </aside>
          <div className="results" id="briefing" aria-busy={busy}>
            <div className="section-heading">
              <div className="eyebrow">{t("YOUR RIDE, EXPLAINED")}</div>
              <div className="result-title">
                <h2>
                  {source ? source.name.replace(/\.gpx$/i, "") : routeName}
                </h2>
                <span className="route-tag">
                  {source ? t("LOCAL GPX") : t("DEMO ROUTE")}
                </span>
                <button
                  className="export-button"
                  disabled={busy || !ride}
                  onClick={exportBrief}
                  aria-label={t("Download ride briefing")}
                >
                  <Download size={17} />
                  <span>{t("Save briefing")}</span>
                </button>
              </div>
              <p>
                {error || busy
                  ? t(
                      "Choose a route and valid ride inputs to build your briefing.",
                    )
                  : route.source === "demo"
                    ? t(
                        "A rolling loop with one sustained climb and a few shorter rises.",
                      )
                    : t(
                        "Source points: {points} · track sections: {sections} · {distance} km horizontal GPS distance.",
                        {
                          points: route.pointCount,
                          sections: route.trackCount,
                          distance: number(route.horizontalM / 1000, 1),
                        },
                      )}
              </p>
            </div>
            <div className="status" role="status" aria-live="polite">
              {busy ? (
                <>
                  <LoaderCircle size={15} className="spin" />{" "}
                  {t("Calculating your ride locally…")}{" "}
                </>
              ) : error ? (
                <>
                  <CircleAlert size={15} />{" "}
                  {t("Check your route or inputs below")}{" "}
                </>
              ) : (
                <>
                  <Check size={14} />{" "}
                  {t("Briefing updated · steady-state model")}{" "}
                </>
              )}
            </div>
            {error && (
              <div className="error-panel" role="alert">
                <CircleAlert size={22} />
                <div>
                  <h3>{t("We can’t estimate this ride yet")}</h3>
                  <p>{formatMessage(error)}</p>
                  <button
                    className="text-button"
                    onClick={() => {
                      reset();
                      setInputs({ ...DEFAULT_INPUTS });
                      setGroupsetId(DEFAULT_GROUPSET_ID);
                    }}
                  >
                    {" "}
                    {t("Reset setup & try the demo")}{" "}
                  </button>
                </div>
              </div>
            )}
            {!error && ride && (
              <div
                className={busy ? "result-content updating" : "result-content"}
              >
                <section className="metrics" aria-label={t("Ride estimates")}>
                  <div className="metric main-metric">
                    <Clock3 size={18} />
                    <span>{t("Estimated moving time")}</span>
                    <strong data-testid="moving-time">
                      {time(ride.timeS)}
                    </strong>
                    <small>{t("Add your stops separately")}</small>
                  </div>
                  <div className="metric">
                    <RouteIcon size={18} />
                    <span>{t("Route distance")}</span>
                    <strong>
                      {number(route.distanceM / 1000, 1)}
                      <small> km</small>
                    </strong>
                    <small>{t("Including slope distance")}</small>
                  </div>
                  <div className="metric">
                    <Mountain size={18} />
                    <span>{t("Total climbing")}</span>
                    <strong>
                      {number(Math.round(route.ascentM))}
                      <small> m</small>
                    </strong>
                    <small>
                      {t("{metres} m descending", {
                        metres: Math.round(route.descentM),
                      })}
                    </small>
                  </div>
                  <div className="metric">
                    <Gauge size={18} />
                    <span>{t("Average speed")}</span>
                    <strong>
                      {number(ride.speedKmh, 1)}
                      <small> km/h</small>
                    </strong>
                    <small>{t("Distance ÷ moving time")}</small>
                  </div>
                </section>
                <section className="card profile-card">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        {" "}
                        {t("01 / HOW HARD IS THIS RIDE?")}{" "}
                      </span>
                      <h3>{t("The shape of your ride")}</h3>
                    </div>
                    <span className="chart-legend">
                      <span /> {t("Elevation")}{" "}
                    </span>
                  </div>
                  <Profile
                    key={route.name + route.smoothingM}
                    route={route}
                    ride={ride}
                  />
                  <div className="ride-takeaway">
                    <Mountain size={20} />
                    <div>
                      <strong>
                        {worst
                          ? t("The main climb starts at {distance} km.", {
                              distance: number(worst.start / 1000, 1),
                            })
                          : t("No sustained climb over 2% detected.")}
                      </strong>
                      <p>
                        {worst
                          ? t(
                              "Allow about {time} for this {distance} km section. Settle into a sustainable rhythm; the model holds {power} W while pedaling.",
                              {
                                time: time(worst.timeS),
                                distance: number(worst.distance / 1000, 1),
                                power: inputs.powerW,
                              },
                            )
                          : t(
                              "Distance, wind and your sustainable power will shape the effort. Short ramps may be hidden by smoothing.",
                            )}
                      </p>
                    </div>
                  </div>
                </section>
                <details className="quality card">
                  <summary>
                    <ShieldCheck size={17} />
                    <strong>{t("Route quality")}</strong>
                    <span
                      className={
                        route.warnings.length ? "quality-warning" : "quality-ok"
                      }
                    >
                      {route.warnings.length
                        ? t("Notes to review: {count}", {
                            count: route.warnings.length,
                          })
                        : route.source === "demo"
                          ? t("Synthetic demo")
                          : t("No detected data issues")}{" "}
                      <ChevronRight size={14} />
                    </span>
                  </summary>
                  <div className="details-body">
                    <p>
                      {route.source === "demo"
                        ? t(
                            "This profile is entirely fictional. It contains no personal locations or recorded activities.",
                          )
                        : t(
                            "Distance is preserved across connected points; separate tracks and gaps over 2 km are not joined. Elevation is resampled and smoothed, so ascent is an estimate.",
                          )}
                    </p>
                    {route.warnings.map((w, n) => (
                      <p className="quality-note" key={n}>
                        <Info size={15} />
                        {formatMessage(w)}
                      </p>
                    ))}
                    {route.source === "gpx" && (
                      <p>
                        {t(
                          "Recorded ascent: {raw} m · modeled ascent: {modeled} m. No issues detected does not mean the file is accurate. Inspect sparse tracks and elevation spikes before relying on the briefing.",
                          {
                            raw: Math.round(route.rawAscentM),
                            modeled: Math.round(route.ascentM),
                          },
                        )}
                      </p>
                    )}
                  </div>
                </details>
                <section className="card demanding">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        {" "}
                        {t("THE SECTIONS TO RESPECT")}{" "}
                      </span>
                      <h3>
                        {demanding.length
                          ? t("Give these climbs some room")
                          : t("A ride without sustained climbs")}
                      </h3>
                    </div>
                    <span className="muted">{t("Ranked by moving time")}</span>
                  </div>
                  {demanding.length ? (
                    <div className="climb-list">
                      {demanding.map((g, n) => (
                        <div className="climb-row" key={g.start}>
                          <span className="climb-number">0{n + 1}</span>
                          <div className="climb-title">
                            <strong>
                              {number(g.start / 1000, 1)}–
                              {number(g.end / 1000, 1)} km
                            </strong>
                            <small>
                              {number(g.distance / 1000, 1)} km · +
                              {number(Math.round(g.gain))} m
                            </small>
                          </div>
                          <div>
                            <strong>{number(g.maxGrade, 1)}%</strong>
                            <small>{t("steepest segment")}</small>
                          </div>
                          <div>
                            <strong>{time(g.timeS)}</strong>
                            <small>{t("at your ride power")}</small>
                          </div>
                          <div>
                            <strong>
                              {Number.isFinite(g.minCadence)
                                ? `${number(Math.round(g.minCadence))} ${t("rpm")}`
                                : t("Coasting")}
                            </strong>
                            <small>{t("lowest virtual cadence")}</small>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty">
                      {" "}
                      {t(
                        "No connected climbing section of at least 100 m exceeds 2%. Check for short ramps in the profile.",
                      )}{" "}
                    </p>
                  )}
                </section>
                <section id="prepare" className="prepare-section">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        {" "}
                        {t("02 / HOW SHOULD I PREPARE?")}{" "}
                      </span>
                      <h3>{t("A few things to get right")}</h3>
                    </div>
                  </div>
                  <div className="prep-grid">
                    <article className="prep-card">
                      <span className="prep-icon">
                        <Bike size={22} />
                      </span>
                      <h4>
                        {ride.lowCadenceS > 60
                          ? t("Consider an easier climbing gear")
                          : t("Your gearing has room to work")}
                      </h4>
                      <p>
                        {ride.lowCadenceS > 60
                          ? t(
                              "About {time} of pedaling falls below 60 rpm even in the closest gear. A smaller chainring or larger rear cog can help cadence.",
                              { time: time(ride.lowCadenceS) },
                            )
                          : t(
                              "The virtual gear selection stays above 60 rpm on most pedaled sections. Check the low gear before a longer climb.",
                            )}
                      </p>
                      <div className="prep-foot">
                        {t(
                          "Lowest ratio {ring}/{cog} · {cadence} rpm at 10 km/h",
                          {
                            ring: Math.min(...inputs.chainrings),
                            cog: Math.max(...inputs.cogs),
                            cadence: number(
                              cadence(
                                10,
                                Math.min(...inputs.chainrings),
                                Math.max(...inputs.cogs),
                                inputs.wheelM,
                              ),
                              0,
                            ),
                          },
                        )}
                      </div>
                    </article>
                    <article className="prep-card">
                      <span className="prep-icon">
                        <Gauge size={22} />
                      </span>
                      <h4>{t("Budget effort, not just distance")}</h4>
                      <p>
                        {t(
                          "{work} kJ of modeled crank work. At an illustrative 18–25% gross efficiency, that corresponds to roughly {low}–{high} kcal during pedaling.",
                          {
                            work: Math.round(ride.workKj),
                            low: Math.round(ride.kcalLow / 50) * 50,
                            high: Math.round(ride.kcalHigh / 50) * 50,
                          },
                        )}
                      </p>
                      <div className="prep-foot">
                        {" "}
                        {t("Energy expenditure ≠ suggested food intake")}{" "}
                      </div>
                    </article>
                    <article className="prep-card">
                      <span className="prep-icon">
                        <Clock3 size={22} />
                      </span>
                      <h4>{t("Make a practical ride plan")}</h4>
                      <p>
                        {t(
                          "Plan food, water and refill stops around {time} of moving time. Bring familiar snacks and check water access. Heat, sweat rate and gut tolerance need your own experience.",
                          { time: time(ride.timeS) },
                        )}
                      </p>
                      <div className="prep-foot">
                        {" "}
                        {t(
                          "No personalized fuel or hydration prescription",
                        )}{" "}
                      </div>
                    </article>
                  </div>
                  <p className="section-note">
                    <Info size={14} />{" "}
                    {t(
                      "Gearing changes cadence in this model, not ride time. No fatigue or FTP-based sustainability prediction is included.",
                    )}{" "}
                  </p>
                </section>
                <section id="comparisons" className="card comparisons">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        {" "}
                        {t("03 / WHAT WOULD MAKE THE BIGGEST DIFFERENCE?")}{" "}
                      </span>
                      <h3>{t("Small changes. This route.")}</h3>
                    </div>
                    <span className="compare-baseline">
                      {" "}
                      {t("Baseline")} {time(ride.timeS)}
                    </span>
                  </div>
                  <p className="card-intro">
                    {" "}
                    {t(
                      "Each comparison changes one variable. All others, including your absolute watts in the weight scenario, stay fixed.",
                    )}{" "}
                  </p>
                  <div className="comparison-list">
                    {comparisons.map((c) => (
                      <div
                        className={
                          c.available
                            ? "comparison-row"
                            : "comparison-row unavailable"
                        }
                        key={c.key}
                      >
                        <div className="comparison-label">
                          <span
                            className={`comparison-icon ${c.key === bestChange?.key ? "best" : ""}`}
                          >
                            {c.key === bestChange?.key ? (
                              <ArrowUpRight size={18} />
                            ) : (
                              <FlaskConical size={17} />
                            )}
                          </span>
                          <div>
                            <strong>{t(c.title)}</strong>
                            <small>{formatMessage(c.detail)}</small>
                          </div>
                        </div>
                        {c.available ? (
                          <>
                            <div className="saving-bar" aria-hidden="true">
                              <span
                                style={{
                                  width: `${Math.abs(c.savedS) <= 0.5 ? 0 : Math.max(2, (Math.abs(c.savedS) / largestDifference) * 100)}%`,
                                }}
                              />
                            </div>
                            <div
                              className={
                                c.savedS < -0.5 ? "saving slower" : "saving"
                              }
                            >
                              <strong>{savings(c.savedS)}</strong>
                              <small>
                                {c.savedS < -0.5
                                  ? t("slower")
                                  : c.savedS > 0.5
                                    ? t("saved")
                                    : t("difference")}
                              </small>
                            </div>
                          </>
                        ) : (
                          <p className="comparison-note">
                            <strong>{t("Unavailable.")}</strong> {t(c.reason)}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                  {comparisons.length === 0 && (
                    <p>
                      {" "}
                      {t(
                        "No comparison scenarios are available at these input limits.",
                      )}{" "}
                    </p>
                  )}
                  <div className="comparison-insight">
                    <FlaskConical size={20} />
                    <p>
                      {bestChange ? (
                        <>
                          <strong>{t(bestChange.title)}</strong>{" "}
                          {t(
                            "ranks first for modeled time savings here. A change can also slow this ride, especially with tailwinds or coasting descents. These are sensitivity examples, not guaranteed equipment gains or training advice.",
                          )}{" "}
                        </>
                      ) : comparisons.length ? (
                        "None of these changes saves modeled time under these conditions. A speed ceiling, coasting or assisting wind can change the outcome."
                      ) : (
                        "Try the default ride inputs to explore comparisons."
                      )}
                    </p>
                  </div>
                </section>
                {ride.cappedS > 0 && (
                  <p className="section-note">
                    <Info size={14} />{" "}
                    {t(
                      "About {time} is limited by your {speed} km/h speed ceiling. Descents are especially uncertain without cornering and braking data.",
                      { time: time(ride.cappedS), speed: inputs.speedLimitKmh },
                    )}
                  </p>
                )}
              </div>
            )}
            {busy && !ride && !error && (
              <div className="loading-card">
                <LoaderCircle className="spin" size={26} />
                <h3>{t("Building your ride briefing")}</h3>
                <p>{t("Processing the route on your device.")}</p>
              </div>
            )}
            <section id="model" className="model-section">
              <div className="model-title">
                <FlaskConical size={21} />
                <div>
                  <span className="step-label">
                    {t("TRANSPARENT BY DESIGN")}
                  </span>
                  <h3>{t("A useful estimate, with honest limits.")}</h3>
                </div>
              </div>
              <p>
                {" "}
                {t(
                  "We solve a steady-state force balance for each section: gravity, rolling resistance and signed aerodynamic drag. Moving time excludes stops, traffic, corners and acceleration. It is a planning estimate, not a finish-time promise.",
                )}{" "}
              </p>
              <details>
                <summary>
                  {" "}
                  {t("Assumptions & limitations")} <span>+</span>
                </summary>
                <div className="model-copy">
                  <p>
                    <strong>{t("Physics.")}</strong>{" "}
                    {t(
                      "Power at the cranks × drivetrain efficiency = speed × total resistance. Gravity uses sin(slope angle); rolling resistance uses cos(slope angle). Air drag uses relative air speed × its absolute value, allowing a strong tailwind to push forward. Zero-power descents solve force equilibrium.",
                    )}{" "}
                  </p>
                  <p>
                    <strong>{t("Pacing.")}</strong>{" "}
                    {t(
                      "Your sustainable watts stay constant during pedaling. With coasting enabled, power becomes zero at grades of −3% or steeper. That threshold and the speed ceiling are practical assumptions, not a validated pacing strategy. FTP is not automatically converted into long-ride power.",
                    )}{" "}
                  </p>
                  <p>
                    <strong>{t("Conditions.")}</strong>{" "}
                    {t(
                      "Wind is a constant along-route component. There is no compass-direction, crosswind, yaw or weather model. Air density uses dry air and standard-atmosphere pressure at your selected altitude. CdA and rolling resistance presets are illustrative and need calibration for a specific rider, tire and surface.",
                    )}{" "}
                  </p>
                  <p>
                    <strong>{t("Route data.")}</strong>{" "}
                    {t(
                      "GPS distance is horizontal; model time uses slope distance. Missing elevations are interpolated within each track, with endpoints held constant. Files with an entirely unelevated section are rejected. Separate tracks and gaps over 2 km exclude connecting travel. Median smoothing on a 25 m grid preserves track endpoints but can soften short hills. Distance plus ascent alone is not enough to infer a route, so manual terrain estimates are deferred.",
                    )}{" "}
                  </p>
                  <p>
                    <strong>{t("Gearing.")}</strong>{" "}
                    {t(
                      "Cadence = wheel revolutions per minute × rear teeth / front teeth. Virtual shifting selects the nearest preferred cadence. It does not constrain power or speed, check compatibility, or penalize cross-chaining. Cadence below 60 rpm is a practical flag, not a physiological threshold.",
                    )}{" "}
                  </p>
                  <p>
                    <strong>{t("Energy.")}</strong>{" "}
                    {t(
                      "The displayed range converts modeled crank work using an illustrative 18–25% gross efficiency. It omits off-bike and coasting metabolism and is particularly uncertain at very low power. It is not a calorie intake target. Sweat, sodium and carbohydrate prescriptions are deferred because they need individual evidence.",
                    )}{" "}
                  </p>
                  <p>
                    <strong>{t("Validation.")}</strong>{" "}
                    {t(
                      "Equations and numerical behavior are checked against independent reference calculations. This particular route-time implementation has not been validated against outdoor rides. No confidence interval is claimed. Use comparisons to explore assumptions and check predictions against your own ride.",
                    )}{" "}
                  </p>
                  <p className="sources">
                    <strong>{t("Model evidence:")}</strong>{" "}
                    <a
                      href="https://pubmed.ncbi.nlm.nih.gov/28121252/"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Martin et al. (1998)
                    </a>{" "}
                    ·{" "}
                    <a
                      href="https://arxiv.org/abs/2005.04229"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Danek et al. (2020)
                    </a>{" "}
                    ·{" "}
                    <a
                      href="https://pubmed.ncbi.nlm.nih.gov/8933490/"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Nickleberry & Brooks (1996)
                    </a>{" "}
                    {t(
                      ". These sources support the model framework and variable efficiency; they do not validate this app’s defaults.",
                    )}{" "}
                  </p>
                </div>
              </details>
              <details>
                <summary>
                  {" "}
                  {t("Privacy & beta scope")} <span>+</span>
                </summary>
                <div className="model-copy">
                  <p>
                    {" "}
                    {t(
                      "GPX files are read into memory on your device and processed in a browser worker. No route uploads, analytics, cookies, accounts or cloud route storage. Refresh or “Return to demo & clear GPX” discards your imported route. Downloaded briefings contain your chosen settings and route name, but no coordinates. Cloudflare handles ordinary asset requests and may retain standard infrastructure logs; GPX contents are not sent to it.",
                    )}{" "}
                  </p>
                  <p>
                    {t(
                      "Only your language preference is saved in this browser; your route and ride settings are not stored.",
                    )}
                  </p>
                  <p>
                    {" "}
                    {t(
                      "The beta focuses on route briefing, preparation and controlled comparisons. Live weather, Strava, accounts, payments and an AI assistant are deferred. Unsupported nutrition recommendations and target-time promises are excluded.",
                    )}{" "}
                  </p>
                </div>
              </details>
            </section>
          </div>
        </div>
      </main>
      <footer>
        <a className="brand" href="#">
          <Bike size={21} /> Bike Science <strong>Pro</strong>
        </a>
        <span>{t("Built for the ride ahead.")}</span>
        <span>{t("Public beta · Model v0.1 · Local-first")}</span>
      </footer>
    </>
  );
}
