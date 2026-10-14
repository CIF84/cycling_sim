import type { Inputs, Route, Ride, Comparison } from "./types";
export const G = 9.80665;
function range(value: number, min: number, max: number, name: string) {
  if (!Number.isFinite(value) || value < min || value > max)
    throw new Error(`${name} must be between ${min} and ${max}.`);
}
export function validateInputs(i: Inputs) {
  range(i.riderKg, 30, 200, "Rider weight");
  range(i.bikeKg, 3, 45, "Bike weight");
  range(i.kitKg, 0, 40, "Kit weight");
  range(i.powerW, 0, 700, "Sustainable power");
  range(i.cda, 0.15, 0.8, "Drag area");
  range(i.crr, 0.001, 0.03, "Rolling resistance");
  range(i.windKmh, -60, 60, "Wind");
  range(i.temperatureC, -15, 45, "Temperature");
  range(i.altitudeM, -400, 5000, "Air-density altitude");
  range(i.efficiency, 0.85, 1, "Drivetrain efficiency");
  range(i.speedLimitKmh, 15, 80, "Speed ceiling");
  range(i.wheelM, 1.5, 2.5, "Wheel circumference");
  range(i.cadenceRpm, 50, 110, "Preferred cadence");
  for (const [name, teeth] of [
    ["Chainrings", i.chainrings],
    ["Cassette", i.cogs],
  ] as const) {
    if (
      !teeth.length ||
      teeth.length > 16 ||
      new Set(teeth).size !== teeth.length ||
      teeth.some((t) => !Number.isInteger(t) || t < 9 || t > 65)
    )
      throw new Error(
        `${name}: enter distinct whole tooth counts from 9 to 65.`,
      );
  }
}
// Dry ideal gas + standard-atmosphere pressure approximation. Humidity/yaw omitted.
export function airDensity(temperatureC: number, altitudeM: number) {
  return (
    (101325 * Math.pow(1 - 2.25577e-5 * altitudeM, 5.25588)) /
    (287.05 * (temperatureC + 273.15))
  );
}
export interface Physics {
  massKg: number;
  gradePct: number;
  windKmh: number;
  cda: number;
  crr: number;
  density: number;
  efficiency: number;
}
export function resistanceN(speedMs: number, p: Physics) {
  const theta = Math.atan(p.gradePct / 100),
    relative = speedMs + p.windKmh / 3.6;
  return (
    p.massKg * G * (Math.sin(theta) + p.crr * Math.cos(theta)) +
    0.5 * p.density * p.cda * relative * Math.abs(relative)
  );
}
export function solveSpeed(powerW: number, p: Physics): number {
  range(powerW, 0, 700, "Power");
  range(p.massKg, 1, 300, "System mass");
  range(p.gradePct, -40, 40, "Grade");
  range(p.windKmh, -60, 60, "Wind");
  range(p.cda, 0.15, 0.8, "Drag area");
  range(p.crr, 0.001, 0.03, "Rolling resistance");
  range(p.density, 0.5, 1.6, "Air density");
  range(p.efficiency, 0.85, 1, "Efficiency");
  // At zero power solve net force, not v*force: v=0 is otherwise a spurious root.
  if (powerW === 0 && resistanceN(0, p) >= 0) return 0;
  const residual =
    powerW === 0
      ? (v: number) => resistanceN(v, p)
      : (v: number) => resistanceN(v, p) * v - powerW * p.efficiency;
  let low = 0,
    high = 16;
  while (residual(high) < 0 && high < 128) high *= 2;
  if (residual(high) < 0)
    throw new Error(
      "No speed equilibrium within solver bounds. Check route and conditions.",
    );
  for (let j = 0; j < 80; j++) {
    const mid = (low + high) / 2;
    if (residual(mid) < 0) low = mid;
    else high = mid;
    if (high - low < 1e-8) break;
  }
  return (low + high) / 2;
}
export function cadence(
  speedKmh: number,
  ring: number,
  cog: number,
  wheelM: number,
) {
  return ((speedKmh / 3.6) * 60) / ((wheelM * ring) / cog);
}
export function chooseGear(speedKmh: number, i: Inputs) {
  let best = { ring: i.chainrings[0], cog: i.cogs[0], cadence: 0 },
    error = Infinity;
  for (const ring of i.chainrings)
    for (const cog of i.cogs) {
      const rpm = cadence(speedKmh, ring, cog, i.wheelM);
      if (Math.abs(rpm - i.cadenceRpm) < error) {
        error = Math.abs(rpm - i.cadenceRpm);
        best = { ring, cog, cadence: rpm };
      }
    }
  return best;
}
export function simulate(route: Route, i: Inputs): Ride {
  validateInputs(i);
  if (!route.segments.length)
    throw new Error("The route has no rideable segments.");
  let timeS = 0,
    workKj = 0,
    pedalingS = 0,
    lowCadenceS = 0,
    cappedS = 0;
  const density = airDensity(i.temperatureC, i.altitudeM);
  const segments = route.segments.map((s) => {
    if (
      !Number.isFinite(s.horizontalM) ||
      s.horizontalM <= 0 ||
      !Number.isFinite(s.deltaM)
    )
      throw new Error("Invalid route segment.");
    const gradePct = (100 * s.deltaM) / s.horizontalM;
    const p = {
      massKg: i.riderKg + i.bikeKg + i.kitKg,
      gradePct,
      windKmh: i.windKmh,
      cda: i.cda,
      crr: i.crr,
      density,
      efficiency: i.efficiency,
    };
    let powerW = i.coastDescents && gradePct <= -3 ? 0 : i.powerW;
    const equilibrium = solveSpeed(powerW, p),
      speedMs = Math.min(equilibrium, i.speedLimitKmh / 3.6),
      capped = equilibrium > speedMs + 1e-6;
    if (speedMs <= 0)
      throw new Error(
        "This power cannot keep you moving on every section. Add sustainable power or choose a downhill-only route for coasting.",
      );
    // If braking at the ceiling, reduce pedaling to power actually needed there.
    if (capped)
      powerW = Math.min(
        powerW,
        Math.max(0, (resistanceN(speedMs, p) * speedMs) / i.efficiency),
      );
    const distanceM = Math.hypot(s.horizontalM, s.deltaM),
      t = distanceM / speedMs,
      gear = chooseGear(speedMs * 3.6, i);
    timeS += t;
    workKj += (powerW * t) / 1000;
    if (powerW > 1) {
      pedalingS += t;
      if (gear.cadence < 60) lowCadenceS += t;
    }
    if (capped) cappedS += t;
    return {
      startM: s.startM,
      distanceM,
      gradePct,
      speedKmh: speedMs * 3.6,
      timeS: t,
      powerW,
      cadence: powerW > 1 ? gear.cadence : null,
      ring: gear.ring,
      cog: gear.cog,
      capped,
    };
  });
  return {
    timeS,
    speedKmh: (route.distanceM / timeS) * 3.6,
    workKj,
    kcalLow: workKj / 4.184 / 0.25,
    kcalHigh: workKj / 4.184 / 0.18,
    pedalingS,
    lowCadenceS,
    cappedS,
    segments,
  };
}
export function compare(
  route: Route,
  i: Inputs,
  base = simulate(route, i),
): Comparison[] {
  const scenarios = [
    {
      key: "power",
      title: "10% more sustainable power",
      detail: `${Math.round(i.powerW)} → ${Math.round(i.powerW * 1.1)} W`,
      changes: { powerW: i.powerW * 1.1 },
    },
    {
      key: "weight",
      title: "2 kg less carried weight",
      detail: "System mass −2 kg · same watts",
      changes: i.kitKg >= 2 ? { kitKg: i.kitKg - 2 } : { bikeKg: i.bikeKg - 2 },
    },
    {
      key: "aero",
      title: "10% lower aerodynamic drag",
      detail: `CdA ${i.cda.toFixed(3)} → ${(i.cda * 0.9).toFixed(3)} m²`,
      changes: { cda: i.cda * 0.9 },
    },
    {
      key: "rolling",
      title: "20% lower rolling resistance",
      detail: `Crr ${i.crr.toFixed(4)} → ${(i.crr * 0.8).toFixed(4)}`,
      changes: { crr: i.crr * 0.8 },
    },
  ];
  return scenarios
    .filter((s) => {
      if (
        Object.entries(s.changes).every(
          ([key, value]) => i[key as keyof Inputs] === value,
        )
      )
        return false;
      try {
        validateInputs({ ...i, ...s.changes });
        return true;
      } catch {
        return false;
      }
    })
    .map((s) => {
      const r = simulate(route, { ...i, ...s.changes });
      return { ...s, timeS: r.timeS, savedS: base.timeS - r.timeS };
    })
    .sort((a, b) => b.savedS - a.savedS);
}
export function powerForTime(
  route: Route,
  i: Inputs,
  targetS: number,
  minW = 1,
  maxW = 700,
) {
  range(targetS, 0.01, 1e9, "Target time");
  range(minW, 1, 700, "Minimum power");
  range(maxW, minW, 700, "Maximum power");
  const fast = simulate(route, { ...i, powerW: maxW }).timeS,
    slow = simulate(route, { ...i, powerW: minW }).timeS;
  if (targetS < fast - 0.01 || targetS > slow + 0.01)
    return { reachable: false as const, fastestS: fast, slowestS: slow };
  let low = minW,
    high = maxW;
  for (let n = 0; n < 45; n++) {
    const mid = (low + high) / 2;
    if (simulate(route, { ...i, powerW: mid }).timeS > targetS) low = mid;
    else high = mid;
  }
  return { reachable: true as const, powerW: (low + high) / 2 };
}
