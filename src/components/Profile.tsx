import { useI18n } from "../i18n/context";
import { formatElapsedTime } from "../i18n/format";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { Route, Ride } from "../model/types";
import { energyProfile, inspectProfile } from "../model/profile";
import { inspectFuelPlan, type FuelPlan } from "../model/fueling";
import type { Climb } from "../model/climbs";

export function Profile({
  route,
  ride,
  selectedClimb,
  climbNumber,
  onClearClimb,
  fraction,
  onFractionChange: setFraction,
  plan,
  onAddRefill,
}: {
  fraction: number;
  onFractionChange: (fraction: number) => void;
  plan: FuelPlan | null;
  onAddRefill: (distanceM: number) => boolean;
  route: Route;
  ride: Ride;
  selectedClimb: Climb | null;
  climbNumber: number;
  onClearClimb: () => void;
}) {
  const { t, number, locale } = useI18n();
  const container = useRef<HTMLDivElement>(null);
  const id = useId();
  const [width, setWidth] = useState(900);
  const [view, setView] = useState<"elevation" | "energy">("elevation");
  const [refillError, setRefillError] = useState(false);
  useEffect(() => setRefillError(false), [fraction]);
  useEffect(() => {
    if (selectedClimb) setFraction(selectedClimb.start / route.distanceM);
  }, [selectedClimb?.id, selectedClimb?.start, route.distanceM]);
  useEffect(() => {
    const observer = new ResizeObserver((entries) =>
      setWidth(Math.max(280, Math.min(900, entries[0].contentRect.width))),
    );
    if (container.current) observer.observe(container.current);
    return () => observer.disconnect();
  }, []);

  const point = inspectProfile(route, ride, fraction);
  const elapsed = formatElapsedTime(locale, point.movingTimeS);
  const planned = plan ? inspectFuelPlan(plan, point.movingTimeS) : null;
  const fuelWindow = plan?.windows.find(
    (w) => point.movingTimeS >= w.startS && point.movingTimeS < w.endS,
  );
  const energy = view === "energy";
  const series = useMemo(() => {
    const elevation = Array.from({ length: route.trackCount }, (_, track) =>
      route.profile
        .filter((p) => p.track === track)
        .map((p) => ({
          distanceM: p.distanceM,
          value: p.elevationM,
        })),
    );
    return { elevation, energy: energyProfile(route, ride) };
  }, [route, ride]);
  const bounds = useMemo(() => {
    let low = Infinity,
      high = -Infinity;
    for (const p of route.profile) {
      low = Math.min(low, p.elevationM);
      high = Math.max(high, p.elevationM);
    }
    return { low, high };
  }, [route]);
  const energyStep = 10 ** Math.floor(Math.log10(Math.max(1, ride.workKj)));
  const min = energy ? 0 : Math.floor(bounds.low / 50) * 50;
  const max = energy
    ? Math.ceil(Math.max(1, ride.workKj) / energyStep) * energyStep
    : Math.max(min + 100, Math.ceil(bounds.high / 50) * 50);
  const ticks = [0, 0.5, 1].map((fraction) => ({
    fraction,
    label:
      number(
        min + fraction * (max - min),
        (min + fraction * (max - min)) % 1 ? 1 : 0,
      ) + (energy ? "" : " m"),
  }));
  const left = Math.max(52, ...ticks.map((tick) => tick.label.length * 7 + 12));
  const x = (distance: number) =>
    left + (distance / route.distanceM) * (width - left - 28);
  const y = (value: number) => 200 - ((value - min) / (max - min)) * 155;
  const paths = useMemo(
    () =>
      series[view].map((points) => {
        // Render at bounded resolution; exact inspection always uses the full model.
        const stride = Math.max(1, Math.ceil(points.length / 700));
        const sampled = points.filter(
          (_, index) => index % stride === 0 || index === points.length - 1,
        );
        return {
          line: sampled.map((p) => x(p.distanceM) + "," + y(p.value)).join(" "),
          start: x(points[0].distanceM),
          end: x(points.at(-1)!.distanceM),
        };
      }),
    [series, view, width, left, min, max],
  );

  return (
    <>
      <div className="card-heading profile-heading">
        <div>
          <span className="step-label">{t("01 / HOW HARD IS THIS RIDE?")}</span>
          <h3>{t("The shape of your ride")}</h3>
        </div>
        <div className="chart-switch" role="group" aria-label={t("Chart view")}>
          <button
            type="button"
            aria-pressed={!energy}
            onClick={() => setView("elevation")}
          >
            {t("Elevation")}
          </button>
          <button
            type="button"
            aria-pressed={energy}
            onClick={() => setView("energy")}
          >
            {t("Energy")}
          </button>
        </div>
      </div>
      <div className="profile" ref={container}>
        {selectedClimb && (
          <div
            className="climb-selection"
            data-testid="climb-selection"
            aria-live="polite"
          >
            <div className="climb-selection-heading">
              <div>
                <strong>
                  {t("Climb {number}", { number: climbNumber })} ·{" "}
                  {number(selectedClimb.start / 1000, 1)}–
                  {number(selectedClimb.end / 1000, 1)} km
                </strong>
                <span>
                  {number(selectedClimb.distance / 1000, 1)} km · +
                  {number(Math.round(selectedClimb.gain))} m
                </span>
              </div>
              <button
                type="button"
                className="clear-climb"
                onClick={onClearClimb}
              >
                {t("Clear selection")}
              </button>
            </div>
            <dl className="climb-selection-stats">
              <div>
                <dt>{t("Climb moving time")}</dt>
                <dd data-testid="climb-time">
                  {formatElapsedTime(locale, selectedClimb.timeS)}
                </dd>
              </div>
              <div>
                <dt>{t("Climb pedal work")}</dt>
                <dd data-testid="climb-work">
                  {number(Math.round(selectedClimb.workKj))} kJ
                </dd>
              </div>
              <div>
                <dt>{t("Lowest modeled cadence")}</dt>
                <dd data-testid="climb-cadence">
                  {selectedClimb.minCadence === null
                    ? t("Coasting")
                    : `${number(Math.round(selectedClimb.minCadence))} ${t("rpm")}`}
                </dd>
              </div>
            </dl>
            {plan && (
              <p className="climb-fuel-context">
                {t(
                  "Work concentration: {work} kJ/km. Planned intake by this climb’s start: {grams} g from the ride’s start. Keep intake spread over time.",
                  {
                    work: Math.round(
                      selectedClimb.workKj / (selectedClimb.distance / 1000),
                    ),
                    grams: Math.round(
                      (plan.carbGph *
                        inspectProfile(
                          route,
                          ride,
                          selectedClimb.start / route.distanceM,
                        ).movingTimeS) /
                        3600,
                    ),
                  },
                )}
              </p>
            )}
            <p>
              {t(
                "Climb totals at your current settings. Cadence uses the closest available gear while pedaling; work is not a food intake target.",
              )}
            </p>
          </div>
        )}
        <div className="chart-readout">
          <div className="chart-position">
            <span>
              <strong data-testid="profile-distance">
                {number(point.distanceM / 1000, 1)} km
              </strong>{" "}
              {t("into the ride")}
            </span>
            <span>
              <strong data-testid="profile-time">{elapsed}</strong>{" "}
              {t("moving time so far")}
            </span>
          </div>
          <div
            className={
              energy ? "chart-values chart-energy-values" : "chart-values"
            }
          >
            {energy ? (
              <>
                <span>
                  <strong data-testid="profile-work">
                    {number(Math.round(point.workKj))} kJ
                  </strong>{" "}
                  {t("work so far")}
                </span>
                <span>
                  <strong data-testid="profile-work-remaining">
                    {number(Math.round(point.remainingWorkKj))} kJ
                  </strong>{" "}
                  {t("work remaining")}
                </span>
              </>
            ) : (
              <span>
                {number(Math.round(point.elevationM))} m <i>·</i>{" "}
                {number(point.segment.gradePct, 1)}
                {t("% grade")} <i>·</i>{" "}
                {number(Math.round(point.segment.speedKmh))} km/h
              </span>
            )}
          </div>
        </div>
        {energy && (
          <p className="chart-axis-label">{t("Cumulative pedal work (kJ)")}</p>
        )}
        <svg
          viewBox={"0 0 " + width + " 240"}
          role="img"
          aria-label={
            energy
              ? t(
                  "Cumulative pedal work. From zero to {work} kJ over the ride. Use the slider below to inspect progress.",
                  { work: Math.round(ride.workKj) },
                )
              : t(
                  "Elevation profile. From {min} to {max} metres. Use the slider below to inspect sections.",
                  {
                    min: Math.round(bounds.low),
                    max: Math.round(bounds.high),
                  },
                )
          }
          onPointerMove={(e) => {
            // Touch scrolling should not move the cursor accidentally; use the slider on phones.
            if (e.pointerType !== "mouse") return;
            const rect = e.currentTarget.getBoundingClientRect();
            setFraction(
              Math.max(
                0,
                Math.min(
                  1,
                  (((e.clientX - rect.left) / rect.width) * width - left) /
                    (width - left - 28),
                ),
              ),
            );
          }}
        >
          <defs>
            <linearGradient id={id + "-fill"} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#acc789" stopOpacity=".7" />
              <stop offset="1" stopColor="#acc789" stopOpacity=".06" />
            </linearGradient>
          </defs>
          {ticks.map((tick) => (
            <g key={tick.fraction}>
              <line
                x1={left}
                x2={width - 28}
                y1={200 - tick.fraction * 155}
                y2={200 - tick.fraction * 155}
                stroke="#e2e7de"
                strokeDasharray="4 5"
              />
              <text
                x={left - 12}
                y={204 - tick.fraction * 155}
                textAnchor="end"
              >
                {tick.label}
              </text>
            </g>
          ))}
          {paths.map((path, index) => (
            <g key={index}>
              <polygon
                points={
                  path.start + ",200 " + path.line + " " + path.end + ",200"
                }
                fill={"url(#" + id + "-fill)"}
              />
              <polyline
                points={path.line}
                fill="none"
                stroke="#476b45"
                strokeWidth="2.5"
                strokeLinejoin="round"
              />
            </g>
          ))}
          {selectedClimb && (
            <g
              data-testid="climb-highlight"
              aria-hidden="true"
              pointerEvents="none"
            >
              <rect
                x={x(selectedClimb.start)}
                y="35"
                width={Math.max(
                  0,
                  x(selectedClimb.end) - x(selectedClimb.start),
                )}
                height="165"
                fill="#b6ce72"
                fillOpacity=".3"
              />
              {[selectedClimb.start, selectedClimb.end].map((distance) => (
                <line
                  key={distance}
                  x1={x(distance)}
                  x2={x(distance)}
                  y1="35"
                  y2="200"
                  stroke="#617d32"
                  strokeWidth="1.5"
                  strokeDasharray="5 3"
                />
              ))}
            </g>
          )}
          {plan && (
            <g aria-hidden="true" data-testid="plan-markers">
              {plan.windows.map((w, i) => (
                <g
                  key={w.startS}
                  onClick={() => setFraction(w.distanceM / route.distanceM)}
                >
                  <circle cx={x(w.distanceM)} cy="22" r="5" fill="#9a5417" />
                  <title>{t("Fuel window {number}", { number: i + 1 })}</title>
                </g>
              ))}
              {plan.stops.map((stop, i) => (
                <g
                  key={stop.id}
                  onClick={() => setFraction(stop.distanceM / route.distanceM)}
                >
                  <line
                    x1={x(stop.distanceM)}
                    x2={x(stop.distanceM)}
                    y1="34"
                    y2="200"
                    stroke="#286b86"
                    strokeDasharray="2 5"
                  />
                  <path
                    d={`M ${x(stop.distanceM)} 27 l 6 7 l -6 7 l -6 -7 Z`}
                    fill="#286b86"
                  />
                  <title>{t("Refill {number}", { number: i + 1 })}</title>
                </g>
              ))}
            </g>
          )}
          {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
            <text
              key={tick}
              x={x(tick * route.distanceM)}
              y="225"
              textAnchor="middle"
            >
              {number(
                (tick * route.distanceM) / 1000,
                route.distanceM < 4000 ? 1 : 0,
              )}{" "}
              km
            </text>
          ))}
          <line
            x1={x(point.distanceM)}
            x2={x(point.distanceM)}
            y1="35"
            y2="200"
            stroke="#183e36"
            strokeDasharray="3 4"
          />
          <circle
            cx={x(point.distanceM)}
            cy={y(energy ? point.workKj : point.elevationM)}
            r="5"
            fill="#183e36"
            stroke="white"
            strokeWidth="2"
          />
        </svg>
        <label className="sr-only" htmlFor={id + "-position"}>
          {t("Inspect route distance")}
        </label>
        <input
          id={id + "-position"}
          aria-describedby={id + "-caption"}
          aria-valuetext={
            energy
              ? t(
                  "{distance} km, {time} moving time, {work} kJ of pedal work",
                  {
                    distance: number(point.distanceM / 1000, 1),
                    time: elapsed,
                    work: Math.round(point.workKj),
                  },
                )
              : t("{distance} km, {time} moving time, {elevation} metres", {
                  distance: number(point.distanceM / 1000, 1),
                  time: elapsed,
                  elevation: Math.round(point.elevationM),
                })
          }
          type="range"
          min="0"
          max="1000"
          value={fraction * 1000}
          onChange={(e) => setFraction(Number(e.target.value) / 1000)}
        />
        <p className="caption" id={id + "-caption"}>
          {t("Move across the profile or use the slider.")}{" "}
          {route.trackCount > 1
            ? t(
                "Moving time excludes stops and travel between separate tracks.",
              )
            : t("Moving time excludes stops.")}
        </p>
        {plan && planned && (
          <div className="profile-plan" data-testid="profile-plan">
            <div className="plan-legend">
              <span>
                <i className="fuel-dot" />
                {t("Fuel windows")}
              </span>
              <span>
                <i className="water-diamond" />
                {t("Water refills")}
              </span>
              <a href="#fuel-plan">{t("Edit plan")}</a>
            </div>
            <div className="profile-plan-stats">
              <span>
                {t("Expenditure to here")}
                <strong>
                  {number(Math.round(point.workKj / (4.184 * 0.25) / 10) * 10)}–
                  {number(Math.round(point.workKj / (4.184 * 0.18) / 10) * 10)}{" "}
                  kcal
                </strong>
              </span>
              <span>
                {t("Carb target by here")}
                <strong data-testid="profile-carbs">
                  {number(Math.round(planned.carbsG))} g · ≈{" "}
                  {number(Math.round((planned.carbsG * 4) / 10) * 10)} kcal
                </strong>
              </span>
              <span>
                {t("Water in bottles")}
                <strong data-testid="profile-water">
                  {number(planned.waterMl / 1000, 1)} l
                </strong>
              </span>
            </div>
            {planned.shortfallMl > 0 && (
              <p className="fuel-warning">
                {t(
                  "This point is beyond your planned bottle coverage. Add an earlier refill or more capacity.",
                )}
              </p>
            )}
            {fuelWindow && (
              <p className="caption">
                {t(
                  "Current fuel window: {start}–{end} · spread about {grams} g through this interval.",
                  {
                    start: formatElapsedTime(locale, fuelWindow.startS),
                    end: formatElapsedTime(locale, fuelWindow.endS),
                    grams: Math.round(fuelWindow.carbsG),
                  },
                )}
              </p>
            )}
            <p className="caption">
              {t(
                "Climbs concentrate work per kilometre. The model holds pedaling power steady, so a steeper Energy curve is not a power spike or a cue to eat a large dose. Keep intake spread over time.",
              )}
            </p>
            <button
              type="button"
              className="chart-refill"
              onClick={() => setRefillError(!onAddRefill(point.distanceM))}
            >
              {t("Add water refill here")}
            </button>
            {refillError && (
              <p className="fuel-warning" role="alert">
                {t(
                  "Choose a point inside the route, at least 10 m from another stop. Maximum eight stops.",
                )}
              </p>
            )}
            <p className="caption">
              {t(
                "At a refill, bottles show the level after filling. All timing uses moving time; allow extra for stops and delays.",
              )}
            </p>
          </div>
        )}
        {energy ? (
          <p className="caption energy-explanation">
            {t(
              "Energy delivered through the pedals, accumulated from the start. The curve stays flat while coasting; your body still uses energy. This is not a food intake target.",
            )}
          </p>
        ) : (
          <p className="caption">
            {route.source === "demo"
              ? t("Fictional terrain, built for exploring the model.")
              : t(
                  "Elevation sampled every 25 m; {smoothing} m median smoothing. Track breaks are not connected.",
                  { smoothing: route.smoothingM },
                )}
          </p>
        )}
      </div>
    </>
  );
}
