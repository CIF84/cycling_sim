import { GROUPSET_PRESETS, sameTeeth } from "../model/gearing";
import { validateInputs } from "../model/physics";
import { DEFAULT_INPUTS, type Inputs } from "../model/types";

export const SETUP_KEY = "bike-science-setup";
const VERSION = 1;

// Explicit allowlist: never serialize route data, filenames or visit conditions.
const numericKeys = [
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
] as const;

export interface SavedSetup {
  inputs: Inputs;
  groupsetId: string;
}
export type LoadResult =
  | { status: "saved"; setup: SavedSetup }
  | { status: "off" | "invalid" | "unavailable"; setup?: never };
export type SaveResult = "saved" | "invalid" | "unavailable";
type SetupStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validatedSetup(
  value: unknown,
  groupsetId: unknown,
): SavedSetup | null {
  if (!record(value) || typeof groupsetId !== "string") return null;
  const inputs = { ...DEFAULT_INPUTS };
  for (const key of numericKeys) {
    if (typeof value[key] !== "number" || !Number.isFinite(value[key]))
      return null;
    inputs[key] = value[key];
  }
  if (typeof value.coastDescents !== "boolean") return null;
  inputs.coastDescents = value.coastDescents;
  for (const key of ["chainrings", "cogs"] as const) {
    const teeth = value[key];
    if (
      !Array.isArray(teeth) ||
      teeth.length > 16 ||
      !teeth.every((n) => typeof n === "number")
    )
      return null;
    inputs[key] = [...teeth];
  }
  try {
    validateInputs(inputs);
  } catch {
    return null;
  }
  const preset = GROUPSET_PRESETS.find((p) => p.id === groupsetId);
  return {
    inputs,
    groupsetId:
      preset &&
      sameTeeth(inputs.chainrings, preset.chainrings) &&
      sameTeeth(inputs.cogs, preset.cassette.cogs)
        ? preset.id
        : "custom",
  };
}

// Access localStorage inside the try: even obtaining it may throw in a browser.
export function loadSetup(storage?: SetupStorage): LoadResult {
  try {
    const raw = (storage ?? localStorage).getItem(SETUP_KEY);
    if (raw === null) return { status: "off" };
    if (raw.length > 16_384) return { status: "invalid" };
    let value: unknown;
    try {
      value = JSON.parse(raw);
    } catch {
      return { status: "invalid" };
    }
    if (!record(value) || value.version !== VERSION)
      return { status: "invalid" };
    const setup = validatedSetup(value.inputs, value.groupsetId);
    return setup ? { status: "saved", setup } : { status: "invalid" };
  } catch {
    return { status: "unavailable" };
  }
}

export function saveSetup(
  inputs: Inputs,
  groupsetId: string,
  storage?: SetupStorage,
): SaveResult {
  const setup = validatedSetup(inputs, groupsetId);
  if (!setup) return "invalid";
  const preferences = {
    ...Object.fromEntries(numericKeys.map((key) => [key, setup.inputs[key]])),
    coastDescents: setup.inputs.coastDescents,
    chainrings: setup.inputs.chainrings,
    cogs: setup.inputs.cogs,
  };
  try {
    (storage ?? localStorage).setItem(
      SETUP_KEY,
      JSON.stringify({
        version: VERSION,
        inputs: preferences,
        groupsetId: setup.groupsetId,
      }),
    );
    return "saved";
  } catch {
    return "unavailable";
  }
}

export function forgetSetup(storage?: SetupStorage): boolean {
  try {
    (storage ?? localStorage).removeItem(SETUP_KEY);
    return true;
  } catch {
    return false;
  }
}
