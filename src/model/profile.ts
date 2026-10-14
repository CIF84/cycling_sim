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
  return {
    distanceM,
    elevationM: terrain.elevationM + progress * terrain.deltaM,
    segment,
  };
}
