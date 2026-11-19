import type { Route, Ride } from "./types";

export interface Climb {
  id: string;
  start: number;
  end: number;
  gain: number;
  timeS: number;
  workKj: number;
  distance: number;
  maxGrade: number;
  minCadence: number | null;
  track: number;
}

// Existing briefing definition: contiguous >=2% sections, at least 100 m long.
// Never bridge track breaks. Rank by time, using a geometry ID rather than rank
// so changing power/gearing does not select a different climb.
export function findClimbs(route: Route, ride: Ride): Climb[] {
  const groups: Climb[] = [];
  ride.segments.forEach((s, index) => {
    if (s.gradePct < 2) return;
    const terrain = route.segments[index];
    const previous = groups.at(-1);
    const workKj = (s.powerW * s.timeS) / 1000;
    if (
      previous &&
      Math.abs(previous.end - s.startM) < 0.1 &&
      previous.track === terrain.track
    ) {
      previous.end = s.startM + s.distanceM;
      previous.distance += s.distanceM;
      previous.gain += terrain.deltaM;
      previous.timeS += s.timeS;
      previous.workKj += workKj;
      previous.maxGrade = Math.max(previous.maxGrade, s.gradePct);
      if (s.cadence !== null)
        previous.minCadence = Math.min(
          previous.minCadence ?? Infinity,
          s.cadence,
        );
    } else {
      groups.push({
        id: `${terrain.track}:${index}`,
        start: s.startM,
        end: s.startM + s.distanceM,
        gain: terrain.deltaM,
        timeS: s.timeS,
        workKj,
        distance: s.distanceM,
        maxGrade: s.gradePct,
        minCadence: s.cadence,
        track: terrain.track,
      });
    }
  });
  return groups
    .filter((g) => g.distance >= 100)
    .sort((a, b) => b.timeS - a.timeS)
    .slice(0, 3);
}
