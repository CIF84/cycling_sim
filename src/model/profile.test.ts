import { it, expect } from "vitest";
import { energyProfile, inspectProfile } from "./profile";
import { routeFromTracks } from "./route";
import { simulate } from "./physics";
import { DEFAULT_INPUTS } from "./types";

const point = (meters: number, ele: number) => ({
  lat: meters / ((6371000 * Math.PI) / 180),
  lon: 0,
  ele,
});

// Independently chosen flat speed: solve power algebraically, then distance / speed
// and power × time give reference values without calling the production solver.
const density = 101325 / (287.05 * 288.15);
const flatPower =
  ((90 * 9.80665 * 0.005 + 0.5 * density * 0.35 * 10 ** 2) * 10) / 0.97;
const referenceInputs = {
  ...DEFAULT_INPUTS,
  riderKg: 75,
  bikeKg: 10,
  kitKg: 5,
  temperatureC: 15,
  altitudeM: 0,
  powerW: flatPower,
};

it("matches independent cumulative time and work at an interior point and both endpoints", () => {
  const route = routeFromTracks([[point(0, 100), point(1000, 100)]], "flat", 0);
  const ride = simulate(route, referenceInputs);
  const start = inspectProfile(route, ride, 0);
  expect(start.movingTimeS).toBe(0);
  expect(start.workKj).toBe(0);
  expect(start.remainingWorkKj).toBeCloseTo((flatPower * 100) / 1000, 5);
  const interior = inspectProfile(route, ride, 0.423);
  expect(interior.movingTimeS).toBeCloseTo(42.3, 5);
  expect(interior.workKj).toBeCloseTo((flatPower * 42.3) / 1000, 5);
  expect(interior.remainingWorkKj).toBeCloseTo((flatPower * 57.7) / 1000, 5);
  const end = inspectProfile(route, ride, 1);
  expect(end.movingTimeS).toBeCloseTo(100, 5);
  expect(end.workKj).toBeCloseTo((flatPower * 100) / 1000, 5);
  expect(end.remainingWorkKj).toBeCloseTo(0, 8);
});

it("does not double count work at a segment boundary or final short remainder", () => {
  const route = routeFromTracks(
    [[point(0, 100), point(101, 100)]],
    "remainder",
    0,
  );
  const ride = simulate(route, referenceInputs);
  for (const distance of [25, 50, 75, 100, 100.5, 101]) {
    const p = inspectProfile(route, ride, distance / route.distanceM);
    expect(p.movingTimeS).toBeCloseTo(distance / 10, 5);
    expect(p.workKj).toBeCloseTo((flatPower * distance) / 10000, 5);
  }
  expect(inspectProfile(route, ride, -1).workKj).toBe(0);
  expect(inspectProfile(route, ride, 2).workKj).toBeCloseTo(ride.workKj, 8);
});

it("advances time with zero work on a coasting descent", () => {
  const route = routeFromTracks([[point(0, 100), point(1000, 50)]], "coast", 0);
  const ride = simulate(route, {
    ...referenceInputs,
    powerW: 0,
    speedLimitKmh: 80,
  });
  const theta = Math.atan(0.05);
  const terminalSpeed = Math.sqrt(
    (2 * 90 * 9.80665 * (Math.sin(theta) - 0.005 * Math.cos(theta))) /
      (density * 0.35),
  );
  const totalSeconds = Math.hypot(1000, 50) / terminalSpeed;
  for (const fraction of [0, 0.25, 0.5, 0.75, 1]) {
    const p = inspectProfile(route, ride, fraction);
    expect(p.movingTimeS).toBeCloseTo(totalSeconds * fraction, 5);
    expect(p.workKj).toBe(0);
    expect(p.remainingWorkKj).toBe(0);
  }
  expect(
    energyProfile(route, ride)
      .flat()
      .every((p) => p.value === 0),
  ).toBe(true);
});

it("uses reduced crank power at a speed ceiling, not the rider's requested power", () => {
  const route = routeFromTracks(
    [[point(0, 100), point(1000, 100)]],
    "capped",
    0,
  );
  const ride = simulate(route, {
    ...referenceInputs,
    powerW: 500,
    speedLimitKmh: 15,
  });
  const speed = 15 / 3.6;
  const requiredPower =
    ((90 * 9.80665 * 0.005 + 0.5 * density * 0.35 * speed ** 2) * speed) / 0.97;
  const p = inspectProfile(route, ride, 0.5);
  expect(p.movingTimeS).toBeCloseTo(500 / speed, 6);
  expect(p.workKj).toBeCloseTo((requiredPower * 500) / speed / 1000, 6);
  expect(p.workKj).toBeLessThan((500 * p.movingTimeS) / 1000);
});

it("carries accumulated work across track breaks without charging for the missing connection", () => {
  const route = routeFromTracks(
    [
      [point(0, 100), point(100, 100)],
      [point(10000, 500), point(10100, 500)],
    ],
    "tracks",
    0,
  );
  const ride = simulate(route, referenceInputs);
  const boundary = route.segments.find((s) => s.track === 1)!.startM;
  const p = inspectProfile(route, ride, boundary / route.distanceM);
  expect(p.movingTimeS).toBeCloseTo(10, 5);
  expect(p.workKj).toBeCloseTo((flatPower * 10) / 1000, 5);
  const groups = energyProfile(route, ride);
  expect(groups).toHaveLength(2);
  expect(groups[0].at(-1)).toEqual(groups[1][0]);
  expect(groups[1].at(-1)!.value).toBeCloseTo((flatPower * 20) / 1000, 5);
  expect(inspectProfile(route, ride, 1).movingTimeS).toBeCloseTo(20, 5);
});

it("starts at zero, stays monotonic and finishes at the briefing totals on mixed terrain", () => {
  const route = routeFromTracks(
    [[point(0, 100), point(200, 110), point(400, 100), point(625, 100)]],
    "mixed",
    0,
  );
  const ride = simulate(route, referenceInputs);
  const points = energyProfile(route, ride).flat();
  expect(points[0]).toEqual({ distanceM: 0, value: 0 });
  expect(points.at(-1)!.value).toBeCloseTo(ride.workKj, 8);
  expect(points.at(-1)!.distanceM).toBeCloseTo(route.distanceM, 8);
  for (let index = 1; index < points.length; index++) {
    expect(points[index].value).toBeGreaterThanOrEqual(points[index - 1].value);
  }
  const coast = ride.segments.find((s) => s.powerW === 0)!;
  const before = inspectProfile(route, ride, coast.startM / route.distanceM);
  const after = inspectProfile(
    route,
    ride,
    (coast.startM + coast.distanceM * 0.8) / route.distanceM,
  );
  expect(after.workKj).toBeCloseTo(before.workKj, 8);
  expect(after.movingTimeS).toBeGreaterThan(before.movingTimeS);
  expect(inspectProfile(route, ride, 1).movingTimeS).toBeCloseTo(ride.timeS, 8);
});

it("interpolates elevation and reads grade from the containing section", () => {
  const route = routeFromTracks(
    [[point(0, 100), point(100, 100), point(220, 112)]],
    "profile",
    0,
  );
  const ride = simulate(route, DEFAULT_INPUTS);
  const beforeClimb = inspectProfile(route, ride, 88 / route.distanceM);
  expect(beforeClimb.distanceM).toBe(88);
  expect(beforeClimb.elevationM).toBeCloseTo(100);
  expect(beforeClimb.segment.gradePct).toBeCloseTo(0);
  const onClimb = inspectProfile(
    route,
    ride,
    (100 + Math.hypot(50, 5)) / route.distanceM,
  );
  expect(onClimb.elevationM).toBeCloseTo(105);
  expect(onClimb.segment.gradePct).toBeCloseTo(10);
  expect(inspectProfile(route, ride, 0).elevationM).toBe(100);
  expect(inspectProfile(route, ride, 1).elevationM).toBeCloseTo(112);
});

it("keeps elevation and grade on the same track at a break", () => {
  const route = routeFromTracks(
    [
      [point(0, 100), point(100, 100)],
      [point(10000, 500), point(10100, 490)],
    ],
    "break",
    0,
  );
  const ride = simulate(route, DEFAULT_INPUTS);
  const boundary = route.segments.find((s) => s.track === 1)!.startM;
  const inspected = inspectProfile(route, ride, boundary / route.distanceM);
  expect(inspected.elevationM).toBeCloseTo(500);
  expect(inspected.segment.gradePct).toBeCloseTo(-10);
  expect(
    inspectProfile(route, ride, (boundary - 1) / route.distanceM).elevationM,
  ).toBe(100);
});
