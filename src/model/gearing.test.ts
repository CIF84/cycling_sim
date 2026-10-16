import { describe, expect, it } from "vitest";
import {
  GROUPSET_PRESETS,
  DEFAULT_GROUPSET,
  DEFAULT_GROUPSET_ID,
  applyGroupset,
  sameTeeth,
} from "./gearing";
import { DEFAULT_INPUTS } from "./types";
import { cadence, compare, simulate, validateInputs } from "./physics";
import { demoRoute } from "./route";

const preset = (id: string) => GROUPSET_PRESETS.find((p) => p.id === id)!;

describe("manufacturer-backed groupset catalog", () => {
  it("has unique IDs and an explicit current 105 default", () => {
    expect(new Set(GROUPSET_PRESETS.map((p) => p.id)).size).toBe(
      GROUPSET_PRESETS.length,
    );
    expect(DEFAULT_GROUPSET.id).toBe(DEFAULT_GROUPSET_ID);
    expect(DEFAULT_INPUTS.chainrings).toEqual([34, 50]);
    expect(DEFAULT_INPUTS.cogs).toEqual([
      11, 12, 13, 14, 15, 17, 19, 21, 24, 27, 30, 34,
    ]);
  });

  it.each(GROUPSET_PRESETS)(
    "$id has valid actual gears and official references",
    (p) => {
      expect(() =>
        validateInputs(applyGroupset(DEFAULT_INPUTS, p)),
      ).not.toThrow();
      for (const teeth of [p.chainrings, p.cassette.cogs]) {
        expect(new Set(teeth).size).toBe(teeth.length);
        expect(
          teeth.every(
            (n, i) =>
              Number.isInteger(n) &&
              n >= 9 &&
              n <= 65 &&
              (i === 0 || teeth[i - 1] < n),
          ),
        ).toBe(true);
      }
      expect([8, 9, 10, 11, 12, 13]).toContain(p.cassette.cogs.length);
      for (const part of [p.crank, p.cassette, p.derailleur]) {
        expect(part.model).not.toBe("");
        const url = new URL(part.url);
        expect(url.protocol).toBe("https:");
        expect([
          "bike.shimano.com",
          "si.shimano.com",
          "productinfo.shimano.com",
          "www.sram.com",
        ]).toContain(url.hostname);
      }
    },
  );

  // Independent manufacturer transcription guards against substituting a
  // same-range cassette with a different speed count or intermediate steps.
  it("distinguishes 11-speed Tiagra from 12-speed road and 13-speed XPLR", () => {
    expect(preset("shimano-tiagra-r4000").cassette.cogs).toEqual([
      11, 13, 15, 17, 19, 21, 23, 25, 28, 32, 36,
    ]);
    expect(preset("sram-rival-axs-e1").cassette.cogs).toEqual([
      10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 36,
    ]);
    for (const id of [
      "sram-red-xplr-e1",
      "sram-force-xplr-e1",
      "sram-rival-xplr-e1",
    ]) {
      expect(preset(id).cassette.cogs).toEqual([
        10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 46,
      ]);
      expect(preset(id).chainrings).toHaveLength(1);
    }
    expect(preset("sram-apex-xplr").cassette.cogs).toEqual([
      11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 44,
    ]);
  });

  it("keeps GRX 45/51-tooth cassette steps and cage choices distinct", () => {
    const close = preset("shimano-grx-rx820-1x45"),
      wide = preset("shimano-grx-rx820-1x51");
    expect(close.cassette.cogs).toEqual([
      10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 40, 45,
    ]);
    expect(close.derailleur.model).toBe("RD-RX822-GS");
    expect(wide.cassette.cogs).toEqual([
      10, 12, 14, 16, 18, 21, 24, 28, 33, 39, 45, 51,
    ]);
    expect(wide.derailleur.model).toBe("RD-RX822-SGS");
  });
});

describe("preset application", () => {
  it("changes both gear lists, preserves all other settings and does not share catalog arrays", () => {
    const before = {
      ...DEFAULT_INPUTS,
      powerW: 231,
      bikeKg: 8.7,
      wheelM: 2.23,
      efficiency: 0.94,
    };
    const p = preset("sram-rival-xplr-e1");
    const after = applyGroupset(before, p);
    expect(after).toEqual({
      ...before,
      chainrings: [40],
      cogs: [...p.cassette.cogs],
    });
    after.chainrings[0] = 44;
    after.cogs.push(50);
    expect(p.chainrings).toEqual([40]);
    expect(p.cassette.cogs).toHaveLength(13);
    expect(before.chainrings).toEqual([34, 50]);
  });

  it("changes climb cadence by the gear ratio without changing time, work or comparisons", () => {
    const road = applyGroupset(
      { ...DEFAULT_INPUTS, powerW: 100 },
      preset("shimano-dura-ace-r9200"),
    );
    const gravel = applyGroupset(
      { ...DEFAULT_INPUTS, powerW: 100 },
      preset("shimano-grx-rx820-1x51"),
    );
    const route = demoRoute();
    const a = simulate(route, road),
      b = simulate(route, gravel);
    expect(a.timeS).toBe(b.timeS);
    expect(a.workKj).toBe(b.workKj);
    expect(a.lowCadenceS).toBeGreaterThan(b.lowCadenceS);
    expect(compare(route, road)).toEqual(compare(route, gravel));
    // At 10 km/h: wheel rpm = (10,000 / 60) / circumference.
    const wheelRpm = 10000 / 60 / road.wheelM;
    expect(cadence(10, 36, 30, road.wheelM)).toBeCloseTo(
      (wheelRpm * 30) / 36,
      10,
    );
    expect(cadence(10, 40, 51, gravel.wheelM)).toBeCloseTo(
      (wheelRpm * 51) / 40,
      10,
    );
  });

  it("treats reordered tooth counts as unchanged but detects edits and invalid lists", () => {
    expect(sameTeeth([50, 34], [34, 50])).toBe(true);
    expect(sameTeeth([34, 50], [34, 52])).toBe(false);
    expect(sameTeeth([34, 34], [34, 50])).toBe(false);
    expect(sameTeeth([NaN], [40])).toBe(false);
    expect(sameTeeth([11, 12], [11, 12, 13])).toBe(false);
  });
});
