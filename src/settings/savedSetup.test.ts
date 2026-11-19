import { describe, expect, it } from "vitest";
import { DEFAULT_INPUTS } from "../model/types";
import {
  DEFAULT_GROUPSET_ID,
  GROUPSET_PRESETS,
  applyGroupset,
} from "../model/gearing";
import { forgetSetup, loadSetup, saveSetup, SETUP_KEY } from "./savedSetup";

function storage() {
  const data = new Map<string, string>();
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value);
    },
    removeItem: (key: string) => {
      data.delete(key);
    },
  };
}

describe("local setup boundary", () => {
  it("starts without consent and only writes the explicit preference allowlist", () => {
    const s = storage();
    expect(loadSetup(s)).toEqual({ status: "off" });
    const inputs = {
      ...DEFAULT_INPUTS,
      riderKg: 81.5,
      powerW: 220,
      windKmh: 12,
      temperatureC: 30,
      altitudeM: 1200,
      xml: "private GPX",
      name: "home.gpx",
      route: { lat: 50, lon: 14 },
    };
    expect(saveSetup(inputs, DEFAULT_GROUPSET_ID, s)).toBe("saved");
    const encoded = JSON.parse(s.getItem(SETUP_KEY)!);
    expect(Object.keys(encoded.inputs).sort()).toEqual(
      [
        "riderKg",
        "bikeKg",
        "kitKg",
        "powerW",
        "cda",
        "crr",
        "efficiency",
        "speedLimitKmh",
        "wheelM",
        "cadenceRpm",
        "coastDescents",
        "chainrings",
        "cogs",
      ].sort(),
    );
    expect(s.getItem(SETUP_KEY)).not.toMatch(
      /private|home|xml|route|wind|temperature|altitude/,
    );
    const loaded = loadSetup(s);
    expect(loaded.setup?.inputs).toEqual({
      ...DEFAULT_INPUTS,
      riderKg: 81.5,
      powerW: 220,
    });
    expect(loaded.setup?.groupsetId).toBe(DEFAULT_GROUPSET_ID);
  });

  it("round-trips each catalog preset and preserves custom gears", () => {
    const s = storage();
    for (const preset of GROUPSET_PRESETS) {
      const inputs = applyGroupset(DEFAULT_INPUTS, preset);
      expect(saveSetup(inputs, preset.id, s)).toBe("saved");
      expect(loadSetup(s).setup).toEqual({ inputs, groupsetId: preset.id });
    }
    const inputs = {
      ...DEFAULT_INPUTS,
      chainrings: [30, 46],
      cogs: [11, 13, 17, 24, 36],
    };
    saveSetup(inputs, "custom", s);
    expect(loadSetup(s).setup).toEqual({ inputs, groupsetId: "custom" });
    expect(loadSetup(s).setup?.inputs.chainrings).not.toBe(inputs.chainrings);
  });

  it("does not label mismatched or retired gearing as a manufacturer preset", () => {
    const s = storage();
    saveSetup({ ...DEFAULT_INPUTS, chainrings: [40] }, DEFAULT_GROUPSET_ID, s);
    expect(loadSetup(s).setup?.groupsetId).toBe("custom");
    saveSetup(DEFAULT_INPUTS, "retired-preset", s);
    expect(loadSetup(s).setup?.groupsetId).toBe("custom");
  });

  it.each(["{broken", "null", "[]", '{"version":99}', "x".repeat(16_385)])(
    "rejects unreadable or incompatible saved data (%#)",
    (raw) => {
      const s = storage();
      s.setItem(SETUP_KEY, raw);
      expect(loadSetup(s)).toEqual({ status: "invalid" });
    },
  );

  it("validates every saved field and keeps the previous good snapshot during invalid edits", () => {
    const s = storage();
    saveSetup(DEFAULT_INPUTS, DEFAULT_GROUPSET_ID, s);
    const good = s.getItem(SETUP_KEY)!;
    for (const patch of [
      { riderKg: 29 },
      { riderKg: "80" },
      { bikeKg: null },
      { kitKg: -1 },
      { powerW: NaN },
      { cda: Infinity },
      { crr: 0 },
      { efficiency: 0.1 },
      { speedLimitKmh: 900 },
      { wheelM: 0 },
      { cadenceRpm: 150 },
      { coastDescents: "false" },
      { chainrings: [] },
      { cogs: [11, 11] },
      { cogs: [10.5] },
      { cogs: "11, 12" },
      { cogs: Array(17).fill(11) },
    ]) {
      const invalid = { ...DEFAULT_INPUTS, ...patch } as typeof DEFAULT_INPUTS;
      expect(saveSetup(invalid, DEFAULT_GROUPSET_ID, s)).toBe("invalid");
      expect(s.getItem(SETUP_KEY)).toBe(good);
      s.setItem(
        SETUP_KEY,
        JSON.stringify({ ...JSON.parse(good), inputs: invalid }),
      );
      expect(loadSetup(s)).toEqual({ status: "invalid" });
      s.setItem(SETUP_KEY, good);
    }
  });

  it("ignores injected visit conditions and does not mutate defaults", () => {
    const s = storage();
    saveSetup(DEFAULT_INPUTS, DEFAULT_GROUPSET_ID, s);
    const value = JSON.parse(s.getItem(SETUP_KEY)!);
    value.inputs.windKmh = 60;
    value.inputs.temperatureC = 45;
    value.inputs.altitudeM = 5000;
    s.setItem(SETUP_KEY, JSON.stringify(value));
    const loaded = loadSetup(s).setup!;
    expect(loaded.inputs).toEqual(DEFAULT_INPUTS);
    loaded.inputs.cogs.push(65);
    expect(DEFAULT_INPUTS.cogs).not.toContain(65);
  });

  it("forgets only the setup, leaving language and other site data intact", () => {
    const s = storage();
    s.setItem("bike-science-language", "cs");
    saveSetup(DEFAULT_INPUTS, DEFAULT_GROUPSET_ID, s);
    expect(forgetSetup(s)).toBe(true);
    expect(loadSetup(s)).toEqual({ status: "off" });
    expect(s.getItem("bike-science-language")).toBe("cs");
  });

  it("reports read, quota and removal failures without crashing", () => {
    const fail = () => {
      throw new Error("storage blocked");
    };
    const blocked = { getItem: fail, setItem: fail, removeItem: fail };
    expect(loadSetup(blocked)).toEqual({ status: "unavailable" });
    expect(saveSetup(DEFAULT_INPUTS, DEFAULT_GROUPSET_ID, blocked)).toBe(
      "unavailable",
    );
    expect(forgetSetup(blocked)).toBe(false);
  });
});
