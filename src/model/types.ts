import type { Message } from "./messages";
import type { MessageKey } from "../i18n/cs";
import { DEFAULT_GROUPSET } from "./gearing";
export interface Segment {
  horizontalM: number;
  deltaM: number;
  startM: number;
  elevationM: number;
  track: number;
}
export interface ProfilePoint {
  distanceM: number;
  elevationM: number;
  track: number;
}
export interface Route {
  name: string;
  source: "demo" | "gpx";
  segments: Segment[];
  profile: ProfilePoint[];
  distanceM: number;
  horizontalM: number;
  ascentM: number;
  descentM: number;
  rawAscentM: number;
  pointCount: number;
  trackCount: number;
  warnings: Message[];
  smoothingM: number;
}
export interface Inputs {
  riderKg: number;
  bikeKg: number;
  kitKg: number;
  powerW: number;
  cda: number;
  crr: number;
  windKmh: number;
  temperatureC: number;
  altitudeM: number;
  efficiency: number;
  speedLimitKmh: number;
  coastDescents: boolean;
  chainrings: number[];
  cogs: number[];
  wheelM: number;
  cadenceRpm: number;
}
export interface SegmentResult {
  startM: number;
  distanceM: number;
  gradePct: number;
  speedKmh: number;
  timeS: number;
  powerW: number;
  cadence: number | null;
  ring: number;
  cog: number;
  capped: boolean;
}
export interface Ride {
  timeS: number;
  speedKmh: number;
  workKj: number;
  kcalLow: number;
  kcalHigh: number;
  pedalingS: number;
  lowCadenceS: number;
  cappedS: number;
  segments: SegmentResult[];
}
export type Comparison = {
  key: string;
  title: MessageKey;
  detail: Message;
  changes: Partial<Inputs>;
} & (
  | { available: true; timeS: number; savedS: number }
  | { available: false; timeS: null; savedS: null; reason: MessageKey }
);
export const DEFAULT_INPUTS: Inputs = {
  riderKg: 75,
  bikeKg: 10,
  kitKg: 3,
  powerW: 180,
  cda: 0.35,
  crr: 0.005,
  windKmh: 0,
  temperatureC: 20,
  altitudeM: 200,
  efficiency: 0.97,
  speedLimitKmh: 50,
  coastDescents: true,
  chainrings: [...DEFAULT_GROUPSET.chainrings],
  cogs: [...DEFAULT_GROUPSET.cassette.cogs],
  wheelM: 2.105,
  cadenceRpm: 85,
};
