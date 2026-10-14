import { useEffect, useRef, useState } from "react";
import type { Route, Ride } from "../model/types";
import { inspectProfile } from "../model/profile";
export function Profile({ route, ride }: { route: Route; ride: Ride }) {
  const container = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(900);
  useEffect(() => {
    const observer = new ResizeObserver((entries) =>
      setWidth(Math.max(340, Math.min(900, entries[0].contentRect.width))),
    );
    if (container.current) observer.observe(container.current);
    return () => observer.disconnect();
  }, []);
  const [fraction, setFraction] = useState(0.32);
  const point = inspectProfile(route, ride, fraction);
  const { segment } = point;
  const elevations = route.profile.map((p) => p.elevationM),
    min = Math.floor(Math.min(...elevations) / 50) * 50,
    max = Math.max(min + 100, Math.ceil(Math.max(...elevations) / 50) * 50);
  const x = (d: number) => 52 + (d / route.distanceM) * (width - 80),
    y = (e: number) => 200 - ((e - min) / (max - min)) * 155;
  const groups = Array.from({ length: route.trackCount }, (_, track) =>
    route.profile.filter((p) => p.track === track),
  );
  return (
    <div className="profile" ref={container}>
      <div className="chart-readout">
        <span>
          <strong>{(point.distanceM / 1000).toFixed(1)} km</strong> into the
          ride
        </span>
        <span>
          {Math.round(point.elevationM)} m <i>·</i>{" "}
          {segment.gradePct.toFixed(1)}% grade <i>·</i>{" "}
          {Math.round(segment.speedKmh)} km/h
        </span>
      </div>
      <svg
        viewBox={`0 0 ${width} 240`}
        role="img"
        aria-label={`Elevation profile. From ${Math.round(Math.min(...elevations))} to ${Math.round(Math.max(...elevations))} metres. Use the slider below to inspect sections.`}
        onPointerMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          setFraction(
            Math.max(
              0,
              Math.min(
                1,
                (((e.clientX - r.left) / r.width) * width - 52) / (width - 80),
              ),
            ),
          );
        }}
      >
        <defs>
          <linearGradient id="profile-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#acc789" stopOpacity=".7" />
            <stop offset="1" stopColor="#acc789" stopOpacity=".06" />
          </linearGradient>
        </defs>
        {[0, 0.5, 1].map((t) => (
          <g key={t}>
            <line
              x1="52"
              x2={width - 28}
              y1={200 - t * 155}
              y2={200 - t * 155}
              stroke="#e2e7de"
              strokeDasharray="4 5"
            />
            <text x="40" y={204 - t * 155} textAnchor="end">
              {Math.round(min + t * (max - min))} m
            </text>
          </g>
        ))}
        {groups.map((pts, n) => {
          const sampled = pts.filter(
            (_, j) =>
              j % Math.max(1, Math.floor(pts.length / 700)) === 0 ||
              j === pts.length - 1,
          );
          const line = sampled
            .map((p) => `${x(p.distanceM)},${y(p.elevationM)}`)
            .join(" ");
          return (
            <g key={n}>
              <polygon
                points={`${x(pts[0].distanceM)},200 ${line} ${x(pts.at(-1)!.distanceM)},200`}
                fill="url(#profile-fill)"
              />
              <polyline
                points={line}
                fill="none"
                stroke="#476b45"
                strokeWidth="2.5"
                strokeLinejoin="round"
              />
            </g>
          );
        })}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <text key={t} x={x(t * route.distanceM)} y="225" textAnchor="middle">
            {Math.round((t * route.distanceM) / 1000)} km
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
          cy={y(point.elevationM)}
          r="5"
          fill="#183e36"
          stroke="white"
          strokeWidth="2"
        />
      </svg>
      <label className="sr-only" htmlFor="profile-position">
        Inspect route distance
      </label>
      <input
        id="profile-position"
        aria-valuetext={`${(point.distanceM / 1000).toFixed(1)} km, ${Math.round(point.elevationM)} metres`}
        type="range"
        min="0"
        max="1000"
        value={fraction * 1000}
        onChange={(e) => setFraction(Number(e.target.value) / 1000)}
      />
      <p className="caption">
        Move across the profile or use the slider.{" "}
        {route.source === "demo"
          ? "Fictional terrain, built for exploring the model."
          : `Elevation sampled every 25 m; ${route.smoothingM} m median smoothing. Track breaks are not connected.`}
      </p>
    </div>
  );
}
