import { useEffect, useRef, useState } from "react";
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
import "./style.css";
const time = (s: number) => {
  const m = Math.max(1, Math.round(s / 60));
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${m % 60} min`;
};
const savings = (s: number) =>
  Math.abs(s) < 30
    ? "<1 min"
    : `${Math.max(1, Math.round(Math.abs(s) / 60))} min`;
function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit,
  help,
}: {
  label: string;
  value: number;
  onChange: (n: number) => void;
  min: number;
  max: number;
  step?: number;
  unit: string;
  help?: string;
}) {
  const id = label.toLowerCase().replace(/[^a-z]+/g, "-");
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="number-wrap">
        <input
          id={id}
          type="number"
          min={min}
          max={max}
          step={step}
          value={Number.isNaN(value) ? "" : value}
          onChange={(e) =>
            onChange(e.target.value === "" ? NaN : Number(e.target.value))
          }
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
        Comma-separated tooth counts. Applied when you leave this field.
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
  const [cassetteMode, setCassetteMode] = useState("road");
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
    [error, setError] = useState(""),
    [importError, setImportError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null),
    workId = useRef(0),
    importId = useRef(0);
  function update<K extends keyof Inputs>(key: K, value: Inputs[K]) {
    setInputs((i) => ({ ...i, [key]: value }));
  }
  useEffect(() => {
    setBusy(true);
    setError("");
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
        "The calculation could not start. Refresh the page and try again.",
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
    setImportError("");
    if (file.size > 10 * 1024 * 1024) {
      setImportError(
        "Please choose a GPX smaller than 10 MB. Your current route is unchanged.",
      );
      return;
    }
    if (!/\.gpx$/i.test(file.name)) {
      setImportError(
        "Please choose a .gpx file. Your current route is unchanged.",
      );
      return;
    }
    try {
      const xml = await file.text();
      if (currentImport !== importId.current) return;
      setSource({ xml, name: file.name });
    } catch {
      setImportError("This file could not be read. Please try again.");
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
    setImportError("");
    if (fileRef.current) fileRef.current.value = "";
  }
  function exportBrief() {
    if (!ride) return;
    const comparisonText = comparisons
      .map((c) =>
        c.available
          ? `${c.title}: ${savings(c.savedS)} ${c.savedS < -0.5 ? "slower" : c.savedS > 0.5 ? "saved" : "difference"}`
          : `${c.title}: unavailable. ${c.reason}`,
      )
      .join("\n");
    const text = `Bike Science Pro · Public beta\n${route.name}\n\n${(route.distanceM / 1000).toFixed(1)} km · ${Math.round(route.ascentM)} m ascent\nEstimated moving time: ${time(ride.timeS)}\nAverage speed: ${ride.speedKmh.toFixed(1)} km/h\nSustainable crank power: ${inputs.powerW} W\nSystem mass: ${inputs.riderKg + inputs.bikeKg + inputs.kitKg} kg\nCdA ${inputs.cda} m² · Crr ${inputs.crr}\nWind: ${inputs.windKmh} km/h (+ headwind) · ${inputs.temperatureC} °C · air-density altitude ${inputs.altitudeM} m\nSpeed ceiling: ${inputs.speedLimitKmh} km/h · coast below −3%: ${inputs.coastDescents}\nCrank work: ${Math.round(ride.workKj)} kJ\n\n${route.warnings.join("\n")}\n\nSteady-state planning estimate, not a finish-time promise. No stops, traffic, corners, acceleration, crosswind or fatigue model. Descent ceiling is a modelling assumption, not a recommended speed.\nComparisons change one variable at a time:\n${comparisonText}\n\nModel and sources: see Assumptions & limitations in the app. GPX processed locally; no coordinates in this briefing.\n`;
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "bike-science-briefing.txt";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <>
      <a className="skip" href="#briefing">
        Skip to ride briefing
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
        <span className="beta">PUBLIC BETA</span>
        <nav aria-label="Main">
          <a href="#briefing">Ride briefing</a>
          <a href="#comparisons">Compare changes</a>
          <a href="#model">
            The model <ArrowUpRight size={14} />
          </a>
        </nav>
        <span className="privacy">
          <ShieldCheck size={15} /> GPX stays on your device
        </span>
      </header>
      <main>
        <section className="hero">
          <div>
            <div className="eyebrow">
              <span /> LESS GUESSWORK. BETTER RIDES.
            </div>
            <h1>
              Know the ride.
              <br />
              <em>Ride with a plan.</em>
            </h1>
            <p>
              Understand the effort, prepare for the climbs, and see which
              changes matter on your route.
            </p>
            <div className="hero-links">
              <a href="#briefing" onClick={reset}>
                Explore the demo <ArrowDown size={15} />
              </a>
              <span>No sign-up. No upload.</span>
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
              <Mountain size={14} /> EVERY ROUTE HAS A STORY
            </div>
          </div>
        </section>
        <div className="workspace">
          <aside className="setup">
            <div className="setup-heading">
              <SlidersHorizontal size={18} />
              <h2>Your ride setup</h2>
            </div>
            <section className="route-input">
              <span className="field-label">01 / THE ROUTE</span>
              <div className="selected-route">
                <RouteIcon size={19} />
                <div>
                  <strong>
                    {source
                      ? source.name.replace(/\.gpx$/i, "")
                      : "The Sunday Loop"}
                  </strong>
                  <small>
                    {source
                      ? "Local GPX file"
                      : "38 km · rolling hills · synthetic demo"}
                  </small>
                </div>
              </div>
              <input
                className="sr-only"
                ref={fileRef}
                id="gpx-file"
                aria-label="Choose GPX file"
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
                <Upload size={16} /> Import your GPX <ChevronRight size={15} />
              </button>
              <p className="caption">
                Up to 10 MB / 100,000 points. Read locally, never uploaded.
              </p>
              {source && (
                <button className="text-button" onClick={reset}>
                  <RotateCcw size={13} /> Return to demo & clear GPX
                </button>
              )}
              {importError && (
                <p className="field-error" role="alert">
                  {importError}
                </p>
              )}
              {source && (
                <label className="field">
                  Elevation smoothing
                  <select
                    value={smoothingM}
                    onChange={(e) => setSmoothingM(Number(e.target.value))}
                  >
                    <option value={0}>Off · raw resampled elevation</option>
                    <option value={100}>100 m · balanced</option>
                    <option value={200}>200 m · noisy recordings</option>
                  </select>
                  <small>
                    Distance-based median filter. Smoothing can hide short
                    ramps.
                  </small>
                </label>
              )}
            </section>
            <section className="rider-input">
              <span className="field-label">02 / RIDER & BIKE</span>
              <div className="field-pair">
                <NumberField
                  label="Rider weight"
                  value={inputs.riderKg}
                  onChange={(v) => update("riderKg", v)}
                  min={30}
                  max={200}
                  unit="kg"
                />
                <NumberField
                  label="Bike weight"
                  value={inputs.bikeKg}
                  onChange={(v) => update("bikeKg", v)}
                  min={3}
                  max={45}
                  unit="kg"
                />
              </div>
              <NumberField
                label="Kit & water"
                value={inputs.kitKg}
                onChange={(v) => update("kitKg", v)}
                min={0}
                max={40}
                unit="kg"
              />
              <NumberField
                label="Sustainable power"
                value={inputs.powerW}
                onChange={(v) => update("powerW", v)}
                min={0}
                max={700}
                unit="W"
                help="Average pedaling power you can hold for this ride, measured at the cranks. Use less than FTP for a long endurance ride."
              />
              <div className="power-note">
                <Gauge size={15} />
                {Number.isFinite(inputs.powerW / inputs.riderKg)
                  ? (inputs.powerW / inputs.riderKg).toFixed(1)
                  : "—"}{" "}
                W/kg <span>· for context, not a fitness score</span>
              </div>
              <label className="field">
                Surface & tires
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
                  <option value={0.004}>Smooth road · fast tires</option>
                  <option value={0.005}>Typical paved road</option>
                  <option value={0.008}>Firm gravel</option>
                  <option value={0.012}>Rough gravel</option>
                  <option value="custom" disabled>
                    Custom · edit in Conditions
                  </option>
                </select>
                <small>
                  Approximate resistance presets, not tire measurements.
                </small>
              </label>
              <label className="field">
                Riding position
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
                  <option value={0.3}>Low on the drops · CdA 0.30</option>
                  <option value={0.35}>Relaxed road · CdA 0.35</option>
                  <option value={0.45}>Upright · CdA 0.45</option>
                  <option value="custom" disabled>
                    Custom · edit in Conditions
                  </option>
                </select>
                <small>
                  Drag area combines body position and air resistance.
                  Individual values vary widely.
                </small>
              </label>
            </section>
            <details className="advanced">
              <summary>
                <Wind size={16} /> Conditions & model <span>+</span>
              </summary>
              <div className="details-body">
                <NumberField
                  label="Along-route wind"
                  value={inputs.windKmh}
                  onChange={(v) => update("windKmh", v)}
                  min={-60}
                  max={60}
                  unit="km/h"
                  help="Positive = headwind, negative = tailwind. Applied to the entire route; not a weather forecast."
                />
                <div className="field-pair">
                  <NumberField
                    label="Temperature"
                    value={inputs.temperatureC}
                    onChange={(v) => update("temperatureC", v)}
                    min={-15}
                    max={45}
                    unit="°C"
                  />
                  <NumberField
                    label="Air-density altitude"
                    value={inputs.altitudeM}
                    onChange={(v) => update("altitudeM", v)}
                    min={-400}
                    max={5000}
                    unit="m"
                  />
                </div>
                <small>
                  Altitude and temperature estimate air density only, not heat
                  stress or physiological performance.
                </small>
                <NumberField
                  label="Aerodynamic drag (CdA)"
                  value={inputs.cda}
                  onChange={(v) => update("cda", v)}
                  min={0.15}
                  max={0.8}
                  step={0.01}
                  unit="m²"
                />
                <NumberField
                  label="Rolling resistance (Crr)"
                  value={inputs.crr}
                  onChange={(v) => update("crr", v)}
                  min={0.001}
                  max={0.03}
                  step={0.001}
                  unit=""
                />
                <NumberField
                  label="Speed ceiling"
                  value={inputs.speedLimitKmh}
                  onChange={(v) => update("speedLimitKmh", v)}
                  min={15}
                  max={80}
                  unit="km/h"
                  help="Braking assumption for the model. Not a safe-speed recommendation; corners are not modeled."
                />
                <label className="check-field">
                  <input
                    type="checkbox"
                    checked={inputs.coastDescents}
                    onChange={(e) => update("coastDescents", e.target.checked)}
                  />{" "}
                  Coast on descents of −3% or steeper
                </label>
                <NumberField
                  label="Drivetrain efficiency"
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
                <Bike size={16} /> Gearing & cadence <span>+</span>
              </summary>
              <div className="details-body">
                <label className="field">
                  Cassette preset
                  <select
                    value={cassetteMode}
                    onChange={(e) => {
                      setCassetteMode(e.target.value);
                      if (e.target.value === "road")
                        update(
                          "cogs",
                          [11, 12, 13, 14, 16, 18, 20, 22, 25, 28, 32],
                        );
                      else if (e.target.value === "wide")
                        update(
                          "cogs",
                          [10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 36],
                        );
                    }}
                  >
                    <option value="road">Shimano 105 11-speed · 11–32</option>
                    <option value="wide">SRAM XG-1270 · 10–36</option>
                    <option value="custom">Custom · edit cogs below</option>
                  </select>
                </label>
                <TeethField
                  label="Front chainrings"
                  value={inputs.chainrings}
                  onChange={(v) => update("chainrings", v)}
                />
                <TeethField
                  label="Cassette cogs"
                  value={inputs.cogs}
                  onChange={(v) => {
                    setCassetteMode("custom");
                    update("cogs", v);
                  }}
                />
                <NumberField
                  label="Wheel circumference"
                  value={inputs.wheelM}
                  onChange={(v) => update("wheelM", v)}
                  min={1.5}
                  max={2.5}
                  step={0.005}
                  unit="m"
                  help="2.105 m is an illustrative 700C road tire; measure one wheel revolution for your bike."
                />
                <NumberField
                  label="Preferred cadence"
                  value={inputs.cadenceRpm}
                  onChange={(v) => update("cadenceRpm", v)}
                  min={50}
                  max={110}
                  unit="rpm"
                />
                <small>
                  Virtual gear selection finds the nearest cadence.
                  Cross-chaining and derailleur compatibility are not checked.
                </small>
              </div>
            </details>
            <button
              className="reset-button"
              onClick={() => {
                setInputs({ ...DEFAULT_INPUTS });
                setCassetteMode("road");
              }}
            >
              <RotateCcw size={14} /> Reset ride inputs
            </button>
          </aside>
          <div className="results" id="briefing" aria-busy={busy}>
            <div className="section-heading">
              <div className="eyebrow">YOUR RIDE, EXPLAINED</div>
              <div className="result-title">
                <h2>
                  {source ? source.name.replace(/\.gpx$/i, "") : route.name}
                </h2>
                <span className="route-tag">
                  {source ? "LOCAL GPX" : "DEMO ROUTE"}
                </span>
                <button
                  className="export-button"
                  disabled={busy || !ride}
                  onClick={exportBrief}
                  aria-label="Download ride briefing"
                >
                  <Download size={17} />
                  <span>Save briefing</span>
                </button>
              </div>
              <p>
                {error || busy
                  ? "Choose a route and valid ride inputs to build your briefing."
                  : route.source === "demo"
                    ? "A rolling loop with one sustained climb and a few shorter rises."
                    : `${route.pointCount.toLocaleString()} source points · ${route.trackCount} track section${route.trackCount > 1 ? "s" : ""} · ${(route.horizontalM / 1000).toFixed(1)} km horizontal GPS distance.`}
              </p>
            </div>
            <div className="status" role="status" aria-live="polite">
              {busy ? (
                <>
                  <LoaderCircle size={15} className="spin" /> Calculating your
                  ride locally…
                </>
              ) : error ? (
                <>
                  <CircleAlert size={15} /> Check your route or inputs below
                </>
              ) : (
                <>
                  <Check size={14} /> Briefing updated · steady-state model
                </>
              )}
            </div>
            {error && (
              <div className="error-panel" role="alert">
                <CircleAlert size={22} />
                <div>
                  <h3>We can’t estimate this ride yet</h3>
                  <p>{error}</p>
                  <button
                    className="text-button"
                    onClick={() => {
                      reset();
                      setInputs({ ...DEFAULT_INPUTS });
                      setCassetteMode("road");
                    }}
                  >
                    Reset setup & try the demo
                  </button>
                </div>
              </div>
            )}
            {!error && ride && (
              <div
                className={busy ? "result-content updating" : "result-content"}
              >
                <section className="metrics" aria-label="Ride estimates">
                  <div className="metric main-metric">
                    <Clock3 size={18} />
                    <span>Estimated moving time</span>
                    <strong data-testid="moving-time">
                      {time(ride.timeS)}
                    </strong>
                    <small>Add your stops separately</small>
                  </div>
                  <div className="metric">
                    <RouteIcon size={18} />
                    <span>Route distance</span>
                    <strong>
                      {(route.distanceM / 1000).toFixed(1)}
                      <small> km</small>
                    </strong>
                    <small>Including slope distance</small>
                  </div>
                  <div className="metric">
                    <Mountain size={18} />
                    <span>Total climbing</span>
                    <strong>
                      {Math.round(route.ascentM)}
                      <small> m</small>
                    </strong>
                    <small>{Math.round(route.descentM)} m descending</small>
                  </div>
                  <div className="metric">
                    <Gauge size={18} />
                    <span>Average speed</span>
                    <strong>
                      {ride.speedKmh.toFixed(1)}
                      <small> km/h</small>
                    </strong>
                    <small>Distance ÷ moving time</small>
                  </div>
                </section>
                <section className="card profile-card">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        01 / HOW HARD IS THIS RIDE?
                      </span>
                      <h3>The shape of your ride</h3>
                    </div>
                    <span className="chart-legend">
                      <span /> Elevation
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
                          ? `The main climb starts at ${(worst.start / 1000).toFixed(1)} km.`
                          : "No sustained climb over 2% detected."}
                      </strong>
                      <p>
                        {worst
                          ? `Allow about ${time(worst.timeS)} for this ${(worst.distance / 1000).toFixed(1)} km section. Settle into a sustainable rhythm; the model holds ${inputs.powerW} W while pedaling.`
                          : "Distance, wind and your sustainable power will shape the effort. Short ramps may be hidden by smoothing."}
                      </p>
                    </div>
                  </div>
                </section>
                <details className="quality card">
                  <summary>
                    <ShieldCheck size={17} />
                    <strong>Route quality</strong>
                    <span
                      className={
                        route.warnings.length ? "quality-warning" : "quality-ok"
                      }
                    >
                      {route.warnings.length
                        ? `${route.warnings.length} notes to review`
                        : route.source === "demo"
                          ? "Synthetic demo"
                          : "No detected data issues"}{" "}
                      <ChevronRight size={14} />
                    </span>
                  </summary>
                  <div className="details-body">
                    <p>
                      {route.source === "demo"
                        ? "This profile is entirely fictional. It contains no personal locations or recorded activities."
                        : "Distance is preserved across connected points; separate tracks and gaps over 2 km are not joined. Elevation is resampled and smoothed, so ascent is an estimate."}
                    </p>
                    {route.warnings.map((w) => (
                      <p className="quality-note" key={w}>
                        <Info size={15} />
                        {w}
                      </p>
                    ))}
                    {route.source === "gpx" && (
                      <p>
                        Recorded ascent: {Math.round(route.rawAscentM)} m ·
                        modeled ascent: {Math.round(route.ascentM)} m. No issues
                        detected does not mean the file is accurate. Inspect
                        sparse tracks and elevation spikes before relying on the
                        briefing.
                      </p>
                    )}
                  </div>
                </details>
                <section className="card demanding">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        THE SECTIONS TO RESPECT
                      </span>
                      <h3>
                        {demanding.length
                          ? "Give these climbs some room"
                          : "A ride without sustained climbs"}
                      </h3>
                    </div>
                    <span className="muted">Ranked by moving time</span>
                  </div>
                  {demanding.length ? (
                    <div className="climb-list">
                      {demanding.map((g, n) => (
                        <div className="climb-row" key={g.start}>
                          <span className="climb-number">0{n + 1}</span>
                          <div className="climb-title">
                            <strong>
                              {(g.start / 1000).toFixed(1)}–
                              {(g.end / 1000).toFixed(1)} km
                            </strong>
                            <small>
                              {(g.distance / 1000).toFixed(1)} km · +
                              {Math.round(g.gain)} m
                            </small>
                          </div>
                          <div>
                            <strong>{g.maxGrade.toFixed(1)}%</strong>
                            <small>steepest segment</small>
                          </div>
                          <div>
                            <strong>{time(g.timeS)}</strong>
                            <small>at your ride power</small>
                          </div>
                          <div>
                            <strong>
                              {Number.isFinite(g.minCadence)
                                ? `${Math.round(g.minCadence)} rpm`
                                : "Coasting"}
                            </strong>
                            <small>lowest virtual cadence</small>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty">
                      No connected climbing section of at least 100 m exceeds
                      2%. Check for short ramps in the profile.
                    </p>
                  )}
                </section>
                <section id="prepare" className="prepare-section">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        02 / HOW SHOULD I PREPARE?
                      </span>
                      <h3>A few things to get right</h3>
                    </div>
                  </div>
                  <div className="prep-grid">
                    <article className="prep-card">
                      <span className="prep-icon">
                        <Bike size={22} />
                      </span>
                      <h4>
                        {ride.lowCadenceS > 60
                          ? "Consider an easier climbing gear"
                          : "Your gearing has room to work"}
                      </h4>
                      <p>
                        {ride.lowCadenceS > 60
                          ? `About ${time(ride.lowCadenceS)} of pedaling falls below 60 rpm even in the closest gear. A smaller chainring or larger rear cog can help cadence.`
                          : "The virtual gear selection stays above 60 rpm on most pedaled sections. Check the low gear before a longer climb."}
                      </p>
                      <div className="prep-foot">
                        Lowest ratio {Math.min(...inputs.chainrings)}/
                        {Math.max(...inputs.cogs)} ·{" "}
                        {cadence(
                          10,
                          Math.min(...inputs.chainrings),
                          Math.max(...inputs.cogs),
                          inputs.wheelM,
                        ).toFixed(0)}{" "}
                        rpm at 10 km/h
                      </div>
                    </article>
                    <article className="prep-card">
                      <span className="prep-icon">
                        <Gauge size={22} />
                      </span>
                      <h4>Budget effort, not just distance</h4>
                      <p>
                        {Math.round(ride.workKj).toLocaleString()} kJ of modeled
                        crank work. At an illustrative 18–25% gross efficiency,
                        that corresponds to roughly{" "}
                        {Math.round(ride.kcalLow / 50) * 50}–
                        {Math.round(ride.kcalHigh / 50) * 50} kcal during
                        pedaling.
                      </p>
                      <div className="prep-foot">
                        Energy expenditure ≠ suggested food intake
                      </div>
                    </article>
                    <article className="prep-card">
                      <span className="prep-icon">
                        <Clock3 size={22} />
                      </span>
                      <h4>Make a practical ride plan</h4>
                      <p>
                        Plan food, water and refill stops around{" "}
                        {time(ride.timeS)} of moving time. Bring familiar snacks
                        and check water access. Heat, sweat rate and gut
                        tolerance need your own experience.
                      </p>
                      <div className="prep-foot">
                        No personalized fuel or hydration prescription
                      </div>
                    </article>
                  </div>
                  <p className="section-note">
                    <Info size={14} /> Gearing changes cadence in this model,
                    not ride time. No fatigue or FTP-based sustainability
                    prediction is included.
                  </p>
                </section>
                <section id="comparisons" className="card comparisons">
                  <div className="card-heading">
                    <div>
                      <span className="step-label">
                        03 / WHAT WOULD MAKE THE BIGGEST DIFFERENCE?
                      </span>
                      <h3>Small changes. This route.</h3>
                    </div>
                    <span className="compare-baseline">
                      Baseline {time(ride.timeS)}
                    </span>
                  </div>
                  <p className="card-intro">
                    Each comparison changes one variable. All others, including
                    your absolute watts in the weight scenario, stay fixed.
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
                            <strong>{c.title}</strong>
                            <small>{c.detail}</small>
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
                                  ? "slower"
                                  : c.savedS > 0.5
                                    ? "saved"
                                    : "difference"}
                              </small>
                            </div>
                          </>
                        ) : (
                          <p className="comparison-note">
                            <strong>Unavailable.</strong> {c.reason}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                  {comparisons.length === 0 && (
                    <p>
                      No comparison scenarios are available at these input
                      limits.
                    </p>
                  )}
                  <div className="comparison-insight">
                    <FlaskConical size={20} />
                    <p>
                      {bestChange ? (
                        <>
                          <strong>{bestChange.title}</strong> ranks first for
                          modeled time savings here. A change can also slow this
                          ride, especially with tailwinds or coasting descents.
                          These are sensitivity examples, not guaranteed
                          equipment gains or training advice.
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
                    <Info size={14} /> About {time(ride.cappedS)} is limited by
                    your {inputs.speedLimitKmh} km/h speed ceiling. Descents are
                    especially uncertain without cornering and braking data.
                  </p>
                )}
              </div>
            )}
            {busy && !ride && !error && (
              <div className="loading-card">
                <LoaderCircle className="spin" size={26} />
                <h3>Building your ride briefing</h3>
                <p>Processing the route on your device.</p>
              </div>
            )}
            <section id="model" className="model-section">
              <div className="model-title">
                <FlaskConical size={21} />
                <div>
                  <span className="step-label">TRANSPARENT BY DESIGN</span>
                  <h3>A useful estimate, with honest limits.</h3>
                </div>
              </div>
              <p>
                We solve a steady-state force balance for each section: gravity,
                rolling resistance and signed aerodynamic drag. Moving time
                excludes stops, traffic, corners and acceleration. It is a
                planning estimate, not a finish-time promise.
              </p>
              <details>
                <summary>
                  Assumptions & limitations <span>+</span>
                </summary>
                <div className="model-copy">
                  <p>
                    <strong>Physics.</strong> Power at the cranks × drivetrain
                    efficiency = speed × total resistance. Gravity uses
                    sin(slope angle); rolling resistance uses cos(slope angle).
                    Air drag uses relative air speed × its absolute value,
                    allowing a strong tailwind to push forward. Zero-power
                    descents solve force equilibrium.
                  </p>
                  <p>
                    <strong>Pacing.</strong> Your sustainable watts stay
                    constant during pedaling. With coasting enabled, power
                    becomes zero at grades of −3% or steeper. That threshold and
                    the speed ceiling are practical assumptions, not a validated
                    pacing strategy. FTP is not automatically converted into
                    long-ride power.
                  </p>
                  <p>
                    <strong>Conditions.</strong> Wind is a constant along-route
                    component. There is no compass-direction, crosswind, yaw or
                    weather model. Air density uses dry air and
                    standard-atmosphere pressure at your selected altitude. CdA
                    and rolling resistance presets are illustrative and need
                    calibration for a specific rider, tire and surface.
                  </p>
                  <p>
                    <strong>Route data.</strong> GPS distance is horizontal;
                    model time uses slope distance. Missing elevations are
                    interpolated within each track, with endpoints held
                    constant. Files with an entirely unelevated section are
                    rejected. Separate tracks and gaps over 2 km exclude
                    connecting travel. Median smoothing on a 25 m grid preserves
                    track endpoints but can soften short hills. Distance plus
                    ascent alone is not enough to infer a route, so manual
                    terrain estimates are deferred.
                  </p>
                  <p>
                    <strong>Gearing.</strong> Cadence = wheel revolutions per
                    minute × rear teeth / front teeth. Virtual shifting selects
                    the nearest preferred cadence. It does not constrain power
                    or speed, check compatibility, or penalize cross-chaining.
                    Cadence below 60 rpm is a practical flag, not a
                    physiological threshold.
                  </p>
                  <p>
                    <strong>Energy.</strong> The displayed range converts
                    modeled crank work using an illustrative 18–25% gross
                    efficiency. It omits off-bike and coasting metabolism and is
                    particularly uncertain at very low power. It is not a
                    calorie intake target. Sweat, sodium and carbohydrate
                    prescriptions are deferred because they need individual
                    evidence.
                  </p>
                  <p>
                    <strong>Validation.</strong> Equations and numerical
                    behavior are checked against independent reference
                    calculations. This particular route-time implementation has
                    not been validated against outdoor rides. No confidence
                    interval is claimed. Use comparisons to explore assumptions
                    and check predictions against your own ride.
                  </p>
                  <p className="sources">
                    <strong>Model evidence:</strong>{" "}
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
                    </a>
                    . These sources support the model framework and variable
                    efficiency; they do not validate this app’s defaults.
                  </p>
                </div>
              </details>
              <details>
                <summary>
                  Privacy & beta scope <span>+</span>
                </summary>
                <div className="model-copy">
                  <p>
                    GPX files are read into memory on your device and processed
                    in a browser worker. No route uploads, analytics, cookies,
                    accounts or cloud route storage. Refresh or “Return to demo
                    & clear GPX” discards your imported route. Downloaded
                    briefings contain your chosen settings and route name, but
                    no coordinates. Cloudflare handles ordinary asset requests
                    and may retain standard infrastructure logs; GPX contents
                    are not sent to it.
                  </p>
                  <p>
                    The beta focuses on route briefing, preparation and
                    controlled comparisons. Live weather, Strava, accounts,
                    payments and an AI assistant are deferred. Unsupported
                    nutrition recommendations and target-time promises are
                    excluded.
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
        <span>Built for the ride ahead.</span>
        <span>Public beta · Model v0.1 · Local-first</span>
      </footer>
    </>
  );
}
