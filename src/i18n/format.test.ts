import { describe, expect, it } from "vitest";
import { cs, type MessageKey } from "./cs";
import {
  decimalText,
  formatNumber,
  formatElapsedTime,
  parseDecimal,
  selectLocale,
  translate,
} from "./format";
import { ModelError, message } from "../model/messages";
import { validateInputs } from "../model/physics";
import { DEFAULT_INPUTS } from "../model/types";

it.each([
  [0, "0 min"],
  [0.01, "<1 min"],
  [59, "<1 min"],
  [60, "1 min"],
  [90, "2 min"],
  [3599, "1 h 0 min"],
  [5160, "1 h 26 min"],
])(
  "formats chart progress at %s seconds without a false one-minute start",
  (seconds, expected) => {
    expect(formatElapsedTime("en", Number(seconds))).toBe(expected);
    expect(formatElapsedTime("cs", Number(seconds))).toBe(expected);
  },
);

describe("language selection", () => {
  it("uses explicit links, then saved choice, then the browser's primary language", () => {
    expect(selectLocale("cs", "en", ["en-GB"])).toBe("cs");
    expect(selectLocale("en", "cs", ["cs-CZ"])).toBe("en");
    expect(selectLocale(null, "en", ["cs-CZ"])).toBe("en");
    expect(selectLocale(null, null, ["cs-CZ", "en"])).toBe("cs");
    expect(selectLocale("unknown", "unknown", ["de-DE", "cs"])).toBe("en");
    expect(selectLocale(null, null, [])).toBe("en");
  });
});
describe("decimal input and display", () => {
  it.each([
    ["0,005", 0.005],
    ["2.105", 2.105],
    ["-17,5", -17.5],
    ["75,", 75],
    [" ,5 ", 0.5],
  ])("parses %s without changing units", (text, expected) => {
    expect(parseDecimal(String(text))).toBe(expected);
  });
  it.each([
    "",
    " ",
    "1,2.3",
    "1.000,5",
    "1,000,000",
    "1 234",
    "10kg",
    "Infinity",
    "NaN",
    "0x10",
    "1e2",
    "--1",
  ])("rejects ambiguous input %s", (text) => {
    expect(parseDecimal(text)).toBeNaN();
  });
  it("formats decimals and grouping for each locale, preserving editable precision", () => {
    expect(formatNumber("cs", 1234.5, 1)).toBe("1\u00a0234,5");
    expect(formatNumber("en", 1234.5, 1)).toBe("1,234.5");
    expect(decimalText("cs", 0.00345678)).toBe("0,00345678");
    expect(decimalText("en", 0.00345678)).toBe("0.00345678");
  });
});
describe("catalog and model messages", () => {
  it("preserves every placeholder in the complete Czech catalog", () => {
    const tokens = (s: string) =>
      [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const [key, translated] of Object.entries(cs)) {
      expect(translated.trim(), key).not.toBe("");
      expect(tokens(translated), key).toEqual(tokens(key));
      expect(translate("en", key as MessageKey)).toBe(key);
    }
  });
  it("localizes nested validation labels and bounds after worker-style serialization", () => {
    let error: ModelError | undefined;
    try {
      validateInputs({ ...DEFAULT_INPUTS, crr: NaN });
    } catch (e) {
      error = e as ModelError;
    }
    expect(error).toBeInstanceOf(ModelError);
    expect(error?.message).toBe(
      "Rolling resistance must be between 0.001 and 0.03.",
    );
    const detail = structuredClone(error!.detail);
    expect(translate("cs", detail.key, detail.values)).toBe(
      "Valivý odpor: zadejte hodnotu od 0,001 do 0,03.",
    );
    expect(translate("en", detail.key, detail.values)).toBe(error?.message);
  });
  it("formats comparison precision and warning parameters without touching model values", () => {
    const detail = message("Crr {before} → {after}", {
      before: { number: 0.005, digits: 4 },
      after: { number: 0.004, digits: 4 },
    });
    expect(translate("cs", detail.key, detail.values)).toBe(
      "Crr 0,0050 → 0,0040",
    );
    expect(
      translate(
        "cs",
        "{count} separate track sections; connecting travel is excluded.",
        { count: 3 },
      ),
    ).toContain("úseky záznamu: 3");
  });
});
