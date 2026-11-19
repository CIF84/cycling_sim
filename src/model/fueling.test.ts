import { describe, expect, it } from "vitest";
import {
  buildFuelPlan,
  DEFAULT_FUEL_SETTINGS,
  distanceAtTime,
  fuelError,
  inspectFuelPlan,
  startingCarbs,
} from "./fueling";
import { inspectProfile } from "./profile";
import { fuelBrief } from "../i18n/fuelBrief";
import type { Ride, Route } from "./types";

// Independent fixture: first 10 km takes 30 min, next 10 km takes 90 min.
// Timing must follow the simulation, not a linear fraction of route length.
const route: Route = {
  name: "Reference",
  source: "gpx",
  distanceM: 20000,
  horizontalM: 20000,
  ascentM: 0,
  descentM: 0,
  rawAscentM: 0,
  pointCount: 3,
  trackCount: 1,
  warnings: [],
  smoothingM: 0,
  segments: [0, 10000].map((startM) => ({
    startM,
    horizontalM: 10000,
    deltaM: 0,
    elevationM: 100,
    track: 0,
  })),
  profile: [0, 10000, 20000].map((distanceM) => ({
    distanceM,
    elevationM: 100,
    track: 0,
  })),
};
const ride: Ride = {
  timeS: 7200,
  speedKmh: 10,
  workKj: 1440,
  kcalLow: 1376,
  kcalHigh: 1912,
  pedalingS: 7200,
  lowCadenceS: 0,
  cappedS: 0,
  segments: [1800, 5400].map((timeS, i) => ({
    startM: i * 10000,
    startTimeS: i === 0 ? 0 : 1800,
    startWorkKj: i === 0 ? 0 : 360,
    distanceM: 10000,
    gradePct: 0,
    speedKmh: 36000000 / timeS,
    timeS,
    powerW: 200,
    cadence: 85,
    ring: 34,
    cog: 20,
    capped: false,
  })),
};
const settings = {
  ...DEFAULT_FUEL_SETTINGS,
  carbGph: 60,
  drinkMlph: 600,
  bottles: 2,
  bottleMl: 500,
  reserveMl: 200,
};

describe("local fuel and water planning", () => {
  it("uses independently calculated hours, carbohydrate energy and volumes", () => {
    const plan = buildFuelPlan(route, ride, settings, []);
    expect(plan.carbsG).toBe(120);
    expect(plan.intakeKcal).toBe(480);
    expect(plan.fluidMl).toBe(1200);
    expect(plan.capacityMl).toBe(1000);
    expect(plan.legs[0].remainingMl).toBe(-200);
    expect(plan.windows).toHaveLength(6);
    expect(plan.windows.reduce((n, w) => n + w.carbsG, 0)).toBe(120);
    expect(plan.windows.every((w) => w.carbsG === 20)).toBe(true);
  });
  it("maps time to route distance using each segment, with exact boundaries and clamps", () => {
    expect(distanceAtTime(ride, 900)).toBe(5000);
    expect(distanceAtTime(ride, 1800)).toBe(10000);
    expect(distanceAtTime(ride, 3600)).toBeCloseTo(13333.3333333);
    expect(distanceAtTime(ride, -100)).toBe(0);
    expect(distanceAtTime(ride, 9000)).toBe(20000);
    for (const seconds of [0, 900, 1800, 2400, 7199, 7200])
      expect(
        inspectProfile(route, ride, distanceAtTime(ride, seconds) / 20000)
          .movingTimeS,
      ).toBeCloseTo(seconds, 8);
  });
  it("identifies reserve and empty points before a late refill; later filling never hides earlier shortage", () => {
    const plan = buildFuelPlan(route, ride, settings, [
      { id: 1, distanceM: 19500 },
    ]);
    expect(plan.legs[0].reserveAtM).toBeCloseTo(15555.5555556);
    expect(plan.legs[0].emptyAtM).toBeCloseTo(17777.7777778);
    expect(plan.legs[1].emptyAtM).toBeNull();
    const atStop = inspectFuelPlan(plan, plan.stops[0].timeS);
    expect(atStop.waterMl).toBe(1000);
    expect(inspectFuelPlan(plan, 6000).shortfallMl).toBeCloseTo(0);
    expect(inspectFuelPlan(plan, 6600).shortfallMl).toBeCloseTo(100);
  });
  it("sorts stops without mutating them and checks each full-bottle leg separately", () => {
    const stops = [
      { id: 2, distanceM: 16000 },
      { id: 1, distanceM: 10000 },
    ];
    const plan = buildFuelPlan(route, ride, settings, stops);
    expect(stops[0].id).toBe(2);
    expect(plan.stops.map((s) => s.id)).toEqual([1, 2]);
    expect(plan.legs.map((l) => l.neededMl)).toEqual([300, 540, 360]);
    expect(plan.legs.map((l) => l.refillMl)).toEqual([300, 540, 0]);
    expect(plan.legs.every((l) => l.reserveAtM === null)).toBe(true);
    expect(inspectFuelPlan(plan, 1800).waterMl).toBe(1000);
    expect(inspectFuelPlan(plan, 7200).waterMl).toBe(640);
    expect(inspectFuelPlan(plan, 7200).carbsG).toBe(120);
  });
  it("allows exact reserve coverage and exact empty-at-finish without claiming a shortfall", () => {
    const reserve = buildFuelPlan(
      route,
      ride,
      { ...settings, drinkMlph: 400 },
      [],
    );
    expect(reserve.legs[0].reserveAtM).toBeNull();
    const empty = buildFuelPlan(
      route,
      ride,
      { ...settings, drinkMlph: 500, reserveMl: 0 },
      [],
    );
    expect(empty.legs[0].emptyAtM).toBeNull();
    expect(inspectFuelPlan(empty, 7200).waterMl).toBe(0);
  });
  it("keeps intake independent from modeled work and ignores gear changes", () => {
    const baseline = buildFuelPlan(route, ride, settings, []);
    const coasting = {
      ...ride,
      workKj: 0,
      kcalLow: 0,
      kcalHigh: 0,
      pedalingS: 0,
      segments: ride.segments.map((s) => ({ ...s, powerW: 0, cadence: null })),
    };
    expect(startingCarbs(coasting)).toBe(0);
    expect(buildFuelPlan(route, coasting, settings, [])).toEqual(baseline);
    expect(
      buildFuelPlan(
        route,
        {
          ...ride,
          segments: ride.segments.map((s) => ({ ...s, ring: 50, cadence: 60 })),
        },
        settings,
        [],
      ),
    ).toEqual(baseline);
  });
  it("uses explicit starting plans for duration, retains user choices and supports zero intake", () => {
    expect(startingCarbs({ ...ride, timeS: 3599 })).toBe(0);
    expect(startingCarbs({ ...ride, timeS: 3600 })).toBe(45);
    expect(startingCarbs({ ...ride, timeS: 9000 })).toBe(45);
    expect(startingCarbs({ ...ride, timeS: 9001 })).toBe(60);
    const zero = buildFuelPlan(route, ride, { ...settings, carbGph: 0 }, []);
    expect(zero.windows).toEqual([]);
    expect(zero.intakeKcal).toBe(0);
  });
  it("includes partial final fuel windows without counting an extra full dose", () => {
    const short = {
      ...ride,
      timeS: 7500,
      segments: [{ ...ride.segments[0], distanceM: 20000, timeS: 7500 }],
    };
    const plan = buildFuelPlan(route, short, settings, []);
    expect(plan.windows.at(-1)?.carbsG).toBe(5);
    expect(plan.windows.at(-1)?.timeS).toBe(7350);
    expect(plan.windows.reduce((n, w) => n + w.carbsG, 0)).toBe(125);
  });
  it("does not invent time across track breaks and never mutates route or ride", () => {
    const separated = {
      ...route,
      trackCount: 2,
      segments: route.segments.map((s, i) => ({ ...s, track: i })),
    };
    const before = JSON.stringify({ separated, ride });
    expect(
      buildFuelPlan(separated, ride, settings, [{ id: 1, distanceM: 10000 }])
        .stops[0].timeS,
    ).toBe(1800);
    expect(JSON.stringify({ separated, ride })).toBe(before);
  });
  it.each([
    { carbGph: NaN },
    { carbGph: 91 },
    { carbGph: -1 },
    { drinkMlph: 0 },
    { drinkMlph: Infinity },
    { bottles: 1.5 },
    { bottles: 0 },
    { bottleMl: 99 },
    { reserveMl: 1001 },
  ])("rejects invalid settings %j without plausible totals", (change) => {
    expect(fuelError(route, ride, { ...settings, ...change }, [])).toBe(
      "settings",
    );
    expect(() =>
      buildFuelPlan(route, ride, { ...settings, ...change }, []),
    ).toThrow();
  });
  it("rejects invalid and duplicate stops, too many stops and unsupported duration", () => {
    for (const stops of [
      [{ id: 1, distanceM: 0 }],
      [{ id: 1, distanceM: 20000 }],
      [{ id: 1, distanceM: NaN }],
      [
        { id: 1, distanceM: 100 },
        { id: 2, distanceM: 105 },
      ],
      [
        { id: 1, distanceM: 100 },
        { id: 1, distanceM: 1000 },
      ],
      Array.from({ length: 9 }, (_, id) => ({
        id,
        distanceM: 1000 * (id + 1),
      })),
    ])
      expect(fuelError(route, ride, settings, stops)).toBe("stops");
    expect(fuelError(route, { ...ride, timeS: 86401 }, settings, [])).toBe(
      "duration",
    );
    const day = {
      ...ride,
      timeS: 86400,
      segments: [{ ...ride.segments[0], timeS: 86400, distanceM: 20000 }],
    };
    expect(buildFuelPlan(route, day, settings, []).windows).toHaveLength(72);
  });
  it("exports the same plan with both units, warnings, stops, timing and localized assumptions", () => {
    const plan = buildFuelPlan(route, ride, settings, [
      { id: 1, distanceM: 19500 },
    ]);
    const en = fuelBrief("en", ride, plan, true).join("\n");
    expect(en).toContain("120 g (≈ 480 kcal)");
    expect(en).toContain("Bottles run out near 17.8 km");
    expect(en).toContain("Refill 1: 19.5 km");
    expect(en).toContain("0 min–20 min: ≈ 20 g");
    expect(en).toContain("coasting and resting metabolism");
    const cs = fuelBrief("cs", ride, plan, true).join("\n");
    expect(cs).toContain("Doplnění 1: 19,5 km");
    expect(cs).not.toContain("{");
    expect(fuelBrief("en", ride, plan, false)).toEqual([]);
    expect(fuelBrief("en", ride, null, true).join(" ")).toContain("invalid");
  });
});
