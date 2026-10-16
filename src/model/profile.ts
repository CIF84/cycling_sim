import type { Route, Ride } from "./types";

// Inspect the section containing this distance, not the nearest section start.
// At a track break, choose the following section without interpolating the gap.
export function inspectProfile(route: Route, ride: Ride, fraction: number) {
  const distanceM = Math.max(0, Math.min(1, fraction)) * route.distanceM;
  let low = 0,
    high = ride.segments.length - 1;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    if (ride.segments[mid].startM <= distanceM) low = mid;
    else high = mid - 1;
  }
  const segment = ride.segments[low],
    terrain = route.segments[low];
  const progress = Math.max(
    0,
    Math.min(1, (distanceM - segment.startM) / segment.distanceM),
  );
  const workKj =
    segment.startWorkKj + (segment.powerW * segment.timeS * progress) / 1000;
  return {
    distanceM,
    elevationM: terrain.elevationM + progress * terrain.deltaM,
    movingTimeS: segment.startTimeS + segment.timeS * progress,
    workKj,
    remainingWorkKj: Math.max(0, ride.workKj - workKj),
    segment,
  };
}

// Keep track boundaries separate even though connecting travel is excluded.
// Points are accumulated crank work, not metabolic energy or required intake.
export function energyProfile(route: Route, ride: Ride) {
  const groups: { distanceM: number; value: number }[][] = [];
  ride.segments.forEach((segment, index) => {
    const track = route.segments[index].track;
    const points = (groups[track] ??= []);
    points.push({ distanceM: segment.startM, value: segment.startWorkKj });
    if (
      index === ride.segments.length - 1 ||
      route.segments[index + 1].track !== track
    ) {
      points.push({
        distanceM: segment.startM + segment.distanceM,
        value: segment.startWorkKj + (segment.powerW * segment.timeS) / 1000,
      });
    }
  });
  return groups;
}
