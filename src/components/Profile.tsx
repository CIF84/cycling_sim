import { useI18n } from "../i18n/context";
import { formatElapsedTime } from "../i18n/format";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { Route, Ride } from "../model/types";
import { energyProfile, inspectProfile } from "../model/profile";

export function Profile({ route, ride }: { route: Route; ride: Ride }) {
  const { t, number, locale } = useI18n();
  const container = useRef<HTMLDivElement>(null);
  const id = useId();
  const [width, setWidth] = useState(900);
  const [view, setView] = useState<"elevation" | "energy">("elevation");
  const [fraction, setFraction] = useState(0.32);
  useEffect(() => {
    const observer = new ResizeObserver((entries) =>
      setWidth(Math.max(280, Math.min(900, entries[0].contentRect.width))),
    );
    if (container.current) observer.observe(container.current);
    return () => observer.disconnect();
  }, []);

  const point = inspectProfile(route, ride, fraction);
  const elapsed = formatElapsedTime(locale, point.movingTimeS);
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
