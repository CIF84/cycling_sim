import { it, expect } from "vitest";
import { inspectProfile } from "./profile";
import { routeFromTracks } from "./route";
import { simulate } from "./physics";
import { DEFAULT_INPUTS } from "./types";

const point = (meters: number, ele: number) => ({
  lat: meters / ((6371000 * Math.PI) / 180),
  lon: 0,
  ele,
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
