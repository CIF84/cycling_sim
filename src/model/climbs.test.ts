import { expect, it } from "vitest";
import { findClimbs } from "./climbs";
import { routeFromTracks } from "./route";
import { simulate } from "./physics";
import { DEFAULT_INPUTS } from "./types";

const point = (m: number, ele: number) => ({
  lat: m / ((6371000 * Math.PI) / 180),
  lon: 0,
  ele,
});
const inputs = {
  ...DEFAULT_INPUTS,
  riderKg: 75,
  bikeKg: 10,
  kitKg: 5,
  altitudeM: 0,
  temperatureC: 15,
  wheelM: 2,
  chainrings: [34],
  cogs: [34],
  speedLimitKmh: 80,
};
const density = 101325 / (287.05 * 288.15);
// Independent reference at a chosen wheel speed; no production force/solver calls.
const powerAt = (grade: number, speed: number) => {
  const angle = Math.atan(grade);
  return (
    ((90 * 9.80665 * (Math.sin(angle) + 0.005 * Math.cos(angle)) +
      0.5 * density * 0.35 * speed ** 2) *
      speed) /
    0.97
  );
};

it("sums a complete climb against independent time, work and fixed-gear cadence", () => {
  const route = routeFromTracks([[point(0, 100), point(1000, 150)]], "hill", 0);
  const powerW = powerAt(0.05, 5);
  const ride = simulate(route, { ...inputs, powerW });
  const [climb] = findClimbs(route, ride);
  expect(climb.start).toBe(0);
  expect(climb.end).toBeCloseTo(Math.hypot(1000, 50), 6);
  expect(climb.gain).toBeCloseTo(50, 8);
  expect(climb.timeS).toBeCloseTo(Math.hypot(1000, 50) / 5, 5);
  expect(climb.workKj).toBeCloseTo((powerW * Math.hypot(1000, 50)) / 5000, 5);
  expect(climb.minCadence).toBeCloseTo(150, 5);
});

it("counts reduced pedal work at a speed ceiling, not the requested power", () => {
  const route = routeFromTracks([[point(0, 0), point(1000, 30)]], "capped", 0);
  const [climb] = findClimbs(
    route,
    simulate(route, { ...inputs, powerW: 700, speedLimitKmh: 15 }),
  );
  const time = Math.hypot(1000, 30) / (15 / 3.6);
  expect(climb.timeS).toBeCloseTo(time, 6);
  expect(climb.workKj).toBeCloseTo((powerAt(0.03, 15 / 3.6) * time) / 1000, 5);
  expect(climb.workKj).toBeLessThan((700 * time) / 1000);
});

it("reports no pedaling cadence and zero work on a wind-propelled climb", () => {
  const route = routeFromTracks([[point(0, 0), point(1000, 30)]], "wind", 0);
  const [climb] = findClimbs(
    route,
    simulate(route, { ...inputs, powerW: 0, windKmh: -60 }),
  );
  expect(climb.timeS).toBeGreaterThan(0);
  expect(climb.workKj).toBe(0);
  expect(climb.minCadence).toBeNull();
});

it("does not join adjacent climb distances across a track break", () => {
  const route = routeFromTracks(
    [
      [point(0, 0), point(300, 15)],
      [point(10000, 400), point(10400, 420)],
    ],
    "tracks",
    0,
  );
  const ride = simulate(route, inputs);
  const climbs = findClimbs(route, ride);
  expect(climbs).toHaveLength(2);
  expect(new Set(climbs.map((c) => c.track)).size).toBe(2);
  expect(climbs.map((c) => Math.round(c.gain)).sort()).toEqual([15, 20]);
  expect(climbs.reduce((sum, c) => sum + c.workKj, 0)).toBeCloseTo(
    ride.workKj,
    8,
  );
});

it("excludes short ramps and flat/downhill sections and ranks only the three longest-time climbs", () => {
  const route = routeFromTracks(
    [
      [point(0, 0), point(50, 5)],
      [point(1000, 0), point(1200, 10)],
      [point(2000, 0), point(2300, 15)],
      [point(3000, 0), point(3400, 20)],
      [point(4000, 0), point(4500, 25)],
      [point(5000, 0), point(5500, 0), point(6000, -25)],
    ],
    "ranking",
    0,
  );
  const ride = simulate(route, inputs);
  const climbs = findClimbs(route, ride);
  expect(climbs.map((c) => c.track)).toEqual([4, 3, 2]);
  expect(climbs[0].timeS).toBeGreaterThan(climbs[1].timeS);
  const altered = {
    ...ride,
    segments: ride.segments.map((s, i) => ({
      ...s,
      timeS: route.segments[i].track === 2 ? s.timeS * 10 : s.timeS,
    })),
  };
  const reranked = findClimbs(route, altered);
  expect(reranked[0].track).toBe(2);
  expect(reranked[0].id).toBe(climbs[2].id);
});

it("does not bridge a flat section and ignores coasting when taking the minimum cadence", () => {
  const route = routeFromTracks(
    [[point(0, 0), point(250, 12.5), point(500, 12.5), point(750, 25)]],
    "split",
    0,
  );
  const ride = simulate(route, inputs);
  const altered = {
    ...ride,
    segments: ride.segments.map((s, i) => ({
      ...s,
      cadence: i % 2 ? 72 : null,
      powerW: i % 2 ? 200 : 0,
    })),
  };
  const climbs = findClimbs(route, altered);
  expect(climbs).toHaveLength(2);
  expect(climbs.every((c) => c.minCadence === 72)).toBe(true);
  expect(climbs.every((c) => c.workKj > 0)).toBe(true);
  climbs.sort((a, b) => a.start - b.start);
  expect(climbs[0].end).toBeLessThan(climbs[1].start);
});
