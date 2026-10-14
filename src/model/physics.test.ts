import { describe, it, expect } from "vitest";
import {
  solveSpeed,
  resistanceN,
  simulate,
  compare,
  powerForTime,
  cadence,
  airDensity,
  validateInputs,
} from "./physics";
import { DEFAULT_INPUTS } from "./types";
import { demoRoute } from "./route";
const p = {
  massKg: 90,
  gradePct: 0,
  windKmh: 0,
  cda: 0.35,
  crr: 0.005,
  density: 1.225,
  efficiency: 0.97,
};
// Independent Newton reference, with slope geometry computed algebraically rather
// than calling production force/solver functions. Start above terminal speed.
function reference(power: number, grade: number, wind: number) {
  const g = grade / 100,
    c = (90 * 9.80665 * (g + 0.005)) / Math.sqrt(1 + g * g),
    a = 0.5 * 1.225 * 0.35,
    w = wind / 3.6;
  let v = 50;
  for (let j = 0; j < 100; j++) {
    const u = v + w,
      f = c + a * u * Math.abs(u),
      r = power === 0 ? f : v * f - 0.97 * power,
      derivative =
        power === 0 ? 2 * a * Math.abs(u) : f + v * 2 * a * Math.abs(u);
    v -= r / derivative;
  }
  return v;
}
describe("force balance and bounds", () => {
  it("recovers 36 km/h from an independently calculated flat 266.499922 W", () => {
    expect(solveSpeed(266.4999226804124, p)).toBeCloseTo(10, 7);
  });
  it.each([
    [250, 0, 0],
    [250, 5, 0],
    [250, 12, 0],
    [180, -5, 0],
    [250, 0, 20],
    [180, 3, -30],
    [250, 0, -60],
    [0.1, -12, 60],
  ])(
    "matches Newton reference for %s W, %s%%, wind %s",
    (power, grade, wind) => {
      expect(
        solveSpeed(power, { ...p, gradePct: grade, windKmh: wind }),
      ).toBeCloseTo(reference(power, grade, wind), 6);
    },
  );
  it("coasts down −5% at analytical terminal speed, not 0.36 km/h", () => {
    const expected = Math.sqrt(
      (90 * 9.80665 * (0.05 - 0.005)) /
        Math.sqrt(1 + 0.05 ** 2) /
        (0.5 * 1.225 * 0.35),
    );
    const actual = solveSpeed(0, { ...p, gradePct: -5 });
    expect(actual).toBeCloseTo(expected, 7);
    expect(actual * 3.6).toBeGreaterThan(48);
    expect(actual * 3.6).toBeLessThan(50);
  });
  it("returns stationary on flat/uphill with zero power", () => {
    expect(solveSpeed(0, p)).toBe(0);
    expect(solveSpeed(0, { ...p, gradePct: 5 })).toBe(0);
  });
  it("strong tailwind can propel a coasting rider below wind speed", () => {
    const v = solveSpeed(0, { ...p, windKmh: -30 });
    const expected =
      30 / 3.6 - Math.sqrt((90 * 9.80665 * 0.005) / (0.5 * 1.225 * 0.35));
    expect(v).toBeCloseTo(expected, 7);
    expect(resistanceN(1, { ...p, windKmh: -30 })).toBeLessThan(0);
  });
  it("more power increases speed; headwind reduces speed", () => {
    expect(solveSpeed(280, p)).toBeGreaterThan(solveSpeed(180, p));
    expect(solveSpeed(250, { ...p, windKmh: 20 })).toBeLessThan(
      solveSpeed(250, p),
    );
  });
  it("uses temperature/altitude only for dry-air density", () => {
    expect(airDensity(15, 0)).toBeCloseTo(1.225, 3);
    expect(airDensity(30, 0)).toBeLessThan(airDensity(10, 0));
    expect(airDensity(20, 2000)).toBeLessThan(airDensity(20, 0));
  });
  it.each([NaN, Infinity, -1, 701])("rejects invalid power %s", (power) =>
    expect(() => solveSpeed(power, p)).toThrow(),
  );
  it("rejects unrealistic grades and invalid gearing", () => {
    expect(() => solveSpeed(250, { ...p, gradePct: 50 })).toThrow();
    expect(() =>
      validateInputs({ ...DEFAULT_INPUTS, cogs: [11, 11] }),
    ).toThrow();
    expect(() => validateInputs({ ...DEFAULT_INPUTS, wheelM: 0 })).toThrow();
  });
});
describe("route, gearing and comparisons", () => {
  const route = demoRoute();
  it("aggregates time/work and distance rather than averaging segment speeds", () => {
    const r = simulate(route, DEFAULT_INPUTS);
    expect(r.timeS).toBeCloseTo(
      r.segments.reduce((n, s) => n + s.timeS, 0),
      9,
    );
    expect(r.workKj).toBeCloseTo(
      r.segments.reduce((n, s) => n + (s.powerW * s.timeS) / 1000, 0),
      9,
    );
    expect(r.speedKmh).toBeCloseTo((route.distanceM / r.timeS) * 3.6, 9);
    expect(r.timeS).toBeGreaterThan(5000);
    expect(r.timeS).toBeLessThan(5300);
  });
  it("coasting uses zero work and no cadence; speed ceiling reports braking", () => {
    const r = simulate(route, DEFAULT_INPUTS);
    expect(r.segments.some((s) => s.powerW === 0 && s.cadence === null)).toBe(
      true,
    );
    expect(r.cappedS).toBeGreaterThan(0);
    expect(r.segments.every((s) => s.speedKmh <= 50 + 0.00001)).toBe(true);
  });
  it("flags an immobile route rather than manufacturing a tiny speed", () =>
    expect(() => simulate(route, { ...DEFAULT_INPUTS, powerW: 0 })).toThrow(
      /keep you moving/,
    ));
  it("gearing changes cadence without changing speed/time", () => {
    const a = simulate(route, DEFAULT_INPUTS),
      b = simulate(route, {
        ...DEFAULT_INPUTS,
        chainrings: [50],
        cogs: [11, 13, 15],
      });
    expect(a.timeS).toBe(b.timeS);
    expect(b.lowCadenceS).toBeGreaterThan(a.lowCadenceS);
    expect(cadence(20, 40, 20, 2)).toBeCloseTo(83.333333, 5);
  });
  it("each comparison changes exactly one field and never mutates the baseline", () => {
    const before = JSON.stringify(DEFAULT_INPUTS),
      cs = compare(route, DEFAULT_INPUTS);
    expect(cs).toHaveLength(4);
    for (const c of cs) {
      expect(Object.keys(c.changes)).toHaveLength(1);
      if (c.key === "weight") expect(c.changes.powerW).toBeUndefined();
      expect(c.timeS).toBe(
        simulate(route, { ...DEFAULT_INPUTS, ...c.changes }).timeS,
      );
    }
    expect(JSON.stringify(DEFAULT_INPUTS)).toBe(before);
  });
  it("supports negative savings when lighter mass slows a coasting descent", () => {
    const down = {
      ...route,
      segments: [
        {
          horizontalM: 1000,
          deltaM: -100,
          startM: 0,
          elevationM: 500,
          track: 0,
        },
      ],
      distanceM: Math.hypot(1000, 100),
    };
    const cs = compare(down, { ...DEFAULT_INPUTS, speedLimitKmh: 80 });
    expect(cs.find((c) => c.key === "weight")!.savedS).toBeLessThan(0);
  });
  it("does not throw when a scenario would cross allowed bounds", () =>
    expect(
      compare(route, { ...DEFAULT_INPUTS, powerW: 700, cda: 0.15, crr: 0.001 }),
    ).toHaveLength(1));
  it("inverse finds a known target and rejects times outside its bracket", () => {
    const i = { ...DEFAULT_INPUTS, coastDescents: false },
      target = simulate(route, { ...i, powerW: 230 }).timeS;
    const found = powerForTime(route, i, target);
    expect(found.reachable).toBe(true);
    if (found.reachable) expect(found.powerW).toBeCloseTo(230, 5);
    expect(powerForTime(route, i, 1).reachable).toBe(false);
    expect(powerForTime(route, i, 1e8).reachable).toBe(false);
  });
});

it("inverse brackets a very steep route without an artificial slow-speed cutoff", () => {
  const route = {
    ...demoRoute(),
    segments: [
      { horizontalM: 1000, deltaM: 300, startM: 0, elevationM: 100, track: 0 },
    ],
    distanceM: Math.hypot(1000, 300),
  };
  const target = simulate(route, { ...DEFAULT_INPUTS, powerW: 230 }).timeS;
  const found = powerForTime(route, DEFAULT_INPUTS, target);
  expect(found.reachable).toBe(true);
  if (found.reachable) expect(found.powerW).toBeCloseTo(230, 5);
});
it("coasting-only route omits the unchanged zero-power scenario", () => {
  const route = {
    ...demoRoute(),
    segments: [
      { horizontalM: 1000, deltaM: -100, startM: 0, elevationM: 500, track: 0 },
    ],
    distanceM: Math.hypot(1000, 100),
  };
  expect(
    compare(route, { ...DEFAULT_INPUTS, powerW: 0, speedLimitKmh: 80 }).some(
      (c) => c.key === "power",
    ),
  ).toBe(false);
});
