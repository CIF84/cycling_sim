import type { Ride, Route } from "./types";
import { inspectProfile } from "./profile";

export interface FuelSettings {
  carbGph: number | null; // null: duration-based starting plan, not individualized need
  drinkMlph: number;
  bottles: number;
  bottleMl: number;
  reserveMl: number;
}
export const DEFAULT_FUEL_SETTINGS: FuelSettings = {
  carbGph: null,
  drinkMlph: 500,
  bottles: 2,
  bottleMl: 750,
  reserveMl: 250,
};
export interface RefillStop {
  id: number;
  distanceM: number;
}
export interface FuelWindow {
  startS: number;
  endS: number;
  timeS: number;
  distanceM: number;
  carbsG: number;
}
export interface WaterLeg {
  startM: number;
  endM: number;
  startS: number;
  endS: number;
  neededMl: number;
  remainingMl: number;
  refillMl: number;
  reserveAtM: number | null;
  emptyAtM: number | null;
}
export interface FuelPlan {
  carbGph: number;
  carbsG: number;
  intakeKcal: number;
  drinkMlph: number;
  fluidMl: number;
  capacityMl: number;
  reserveMl: number;
  windows: FuelWindow[];
  legs: WaterLeg[];
  stops: (RefillStop & { timeS: number })[];
}
export function startingCarbs(ride: Ride) {
  if (ride.pedalingS === 0 || ride.timeS < 3600) return 0;
  return ride.timeS <= 9000 ? 45 : 60;
}
// Inverse of the profile time inspector. At a track break, use the next track;
// no time or distance is invented for unrecorded connections.
export function distanceAtTime(ride: Ride, seconds: number) {
  const t = Math.max(0, Math.min(ride.timeS, seconds));
  let lo = 0,
    hi = ride.segments.length - 1;
  while (lo < hi) {
    const mid = Math.ceil((lo + hi) / 2);
    if (ride.segments[mid].startTimeS <= t) lo = mid;
    else hi = mid - 1;
  }
  const s = ride.segments[lo];
  return (
    s.startM +
    s.distanceM * Math.max(0, Math.min(1, (t - s.startTimeS) / s.timeS))
  );
}
export type FuelError = "settings" | "duration" | "stops" | null;
export function fuelError(
  route: Route,
  ride: Ride,
  s: FuelSettings,
  stops: RefillStop[],
): FuelError {
  if (!Number.isFinite(ride.timeS) || ride.timeS <= 0 || ride.timeS > 86400)
    return "duration";
  const valid = (n: number, min: number, max: number) =>
    Number.isFinite(n) && n >= min && n <= max;
  if (
    (s.carbGph !== null && !valid(s.carbGph, 0, 90)) ||
    !valid(s.drinkMlph, 100, 2000) ||
    !valid(s.bottles, 1, 6) ||
    !Number.isInteger(s.bottles) ||
    !valid(s.bottleMl, 100, 2000) ||
    !valid(s.reserveMl, 0, s.bottles * s.bottleMl)
  )
    return "settings";
  if (
    stops.length > 8 ||
    new Set(stops.map((s) => s.id)).size !== stops.length ||
    stops.some(
      (s) =>
        !Number.isFinite(s.distanceM) ||
        s.distanceM <= 0 ||
        s.distanceM >= route.distanceM,
    )
  )
    return "stops";
  const sorted = [...stops].sort((a, b) => a.distanceM - b.distanceM);
  if (
    sorted.some((s, i) => i > 0 && s.distanceM - sorted[i - 1].distanceM < 10)
  )
    return "stops";
  return null;
}
export function buildFuelPlan(
  route: Route,
  ride: Ride,
  settings: FuelSettings,
  stops: RefillStop[],
): FuelPlan {
  const error = fuelError(route, ride, settings, stops);
  if (error) throw new Error(error);
  const carbGph = settings.carbGph ?? startingCarbs(ride);
  const carbsG = (carbGph * ride.timeS) / 3600;
  const capacityMl = settings.bottles * settings.bottleMl;
  const sorted = [...stops]
    .sort((a, b) => a.distanceM - b.distanceM)
    .map((s) => ({
      ...s,
      timeS: inspectProfile(route, ride, s.distanceM / route.distanceM)
        .movingTimeS,
    }));
  const windows: FuelWindow[] = [];
  // 20-minute windows are a planning convenience, not an absorption model.
  if (carbGph > 0)
    for (let startS = 0; startS < ride.timeS - 1e-6; startS += 1200) {
      const endS = Math.min(ride.timeS, startS + 1200);
      const timeS = (startS + endS) / 2;
      windows.push({
        startS,
        endS,
        timeS,
        distanceM: distanceAtTime(ride, timeS),
        carbsG: (carbGph * (endS - startS)) / 3600,
      });
    }
  const boundaries = [
    { distanceM: 0, timeS: 0 },
    ...sorted,
    { distanceM: route.distanceM, timeS: ride.timeS },
  ];
  const legs = boundaries.slice(1).map((end, i): WaterLeg => {
    const start = boundaries[i];
    const neededMl = ((end.timeS - start.timeS) * settings.drinkMlph) / 3600;
    const remainingMl = capacityMl - neededMl;
    return {
      startM: start.distanceM,
      endM: end.distanceM,
      startS: start.timeS,
      endS: end.timeS,
      neededMl,
      remainingMl,
      refillMl: i < sorted.length ? Math.min(capacityMl, neededMl) : 0,
      reserveAtM:
        remainingMl < settings.reserveMl - 1e-6
          ? distanceAtTime(
              ride,
              start.timeS +
                ((capacityMl - settings.reserveMl) / settings.drinkMlph) * 3600,
            )
          : null,
      emptyAtM:
        remainingMl < -1e-6
          ? distanceAtTime(
              ride,
              start.timeS + (capacityMl / settings.drinkMlph) * 3600,
            )
          : null,
    };
  });
  return {
    carbGph,
    carbsG,
    intakeKcal: carbsG * 4,
    drinkMlph: settings.drinkMlph,
    fluidMl: (ride.timeS * settings.drinkMlph) / 3600,
    capacityMl,
    reserveMl: settings.reserveMl,
    windows,
    legs,
    stops: sorted,
  };
}
export function inspectFuelPlan(plan: FuelPlan, movingTimeS: number) {
  const last = plan.legs.at(-1)!;
  const t = Math.max(0, Math.min(last.endS, movingTimeS));
  // At a refill show bottles after the refill. Each leg still reports pre-refill shortage.
  const leg = plan.legs.find((l) => t < l.endS - 1e-6) ?? last;
  return {
    carbsG: (plan.carbGph * t) / 3600,
    waterMl: Math.max(
      0,
      plan.capacityMl - ((t - leg.startS) * plan.drinkMlph) / 3600,
    ),
    shortfallMl: Math.max(
      0,
      ((t - leg.startS) * plan.drinkMlph) / 3600 - plan.capacityMl,
    ),
  };
}
