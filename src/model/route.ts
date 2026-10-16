import { ModelError, message, type Message } from "./messages";
import { XMLParser, XMLValidator } from "fast-xml-parser";
import type { Route, Segment, ProfilePoint } from "./types";
interface Point {
  lat: number;
  lon: number;
  ele: number | null;
}
const array = <T>(v: T | T[] | undefined): T[] =>
  v === undefined ? [] : Array.isArray(v) ? v : [v];
export function haversine(a: Point, b: Point) {
  const rad = Math.PI / 180,
    dlat = (b.lat - a.lat) * rad,
    dlon = (b.lon - a.lon) * rad;
  const h =
    Math.sin(dlat / 2) ** 2 +
    Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dlon / 2) ** 2;
  return 6371000 * 2 * Math.asin(Math.sqrt(Math.min(1, h)));
}
export function routeFromTracks(
  tracks: Point[][],
  name: string,
  smoothingM = 100,
): Route {
  if (!Number.isFinite(smoothingM) || smoothingM < 0 || smoothingM > 500)
    throw new ModelError("Invalid smoothing distance.");
  const segments: Segment[] = [],
    profile: ProfilePoint[] = [],
    warnings: Message[] = [];
  let distanceM = 0,
    horizontalM = 0,
    ascentM = 0,
    descentM = 0,
    rawAscentM = 0,
    duplicates = 0,
    missing = 0,
    gaps = 0,
    sparse = 0,
    trackCount = 0;
  const pointCount = tracks.reduce((n, t) => n + t.length, 0);
  if (pointCount > 100000)
    throw new ModelError(
      "This GPX has over 100,000 points. Export a simplified track and try again.",
    );
  // Split large jumps rather than fabricate terrain across missing recordings.
  const parts: Point[][] = [];
  for (const track of tracks) {
    let part: Point[] = [];
    for (const p of track) {
      if (
        !Number.isFinite(p.lat) ||
        !Number.isFinite(p.lon) ||
        Math.abs(p.lat) > 90 ||
        Math.abs(p.lon) > 180 ||
        (p.ele !== null &&
          (!Number.isFinite(p.ele) || p.ele < -500 || p.ele > 9000))
      )
        throw new ModelError("GPX contains invalid coordinates or elevations.");
      if (part.length) {
        const d = haversine(part[part.length - 1], p);
        if (d < 0.05) {
          duplicates++;
          continue;
        }
        if (d > 250 && d <= 2000) sparse++;
        if (d > 2000) {
          parts.push(part);
          part = [];
          gaps++;
        }
      }
      part.push({ ...p });
    }
    parts.push(part);
  }
  if (parts.length > 100)
    throw new ModelError(
      "This GPX has more than 100 separate sections. Export a single ride or simplify track breaks.",
    );
  for (const track of parts) {
    if (track.length < 2) continue;
    const xs = [0];
    for (let n = 1; n < track.length; n++)
      xs.push(xs[n - 1] + haversine(track[n - 1], track[n]));
    const length = xs.at(-1)!;
    if (length < 1) continue;
    if (horizontalM + length > 1500000)
      throw new ModelError(
        "Routes over 1,500 km are not supported. Split this file into individual rides.",
      );
    const known = track
      .map((p, n) => (p.ele === null ? -1 : n))
      .filter((n) => n >= 0);
    if (!known.length)
      throw new ModelError(
        "A track has no elevation data. Export GPX with elevations; we cannot infer climbing from coordinates alone.",
      );
    let k = 0;
    for (let n = 0; n < track.length; n++) {
      if (track[n].ele !== null) continue;
      missing++;
      while (k < known.length - 1 && known[k + 1] < n) k++;
      const a = known[k],
        b = known[Math.min(k + 1, known.length - 1)];
      track[n].ele =
        n < a
          ? track[a].ele
          : n > b
            ? track[b].ele
            : track[a].ele! +
              ((track[b].ele! - track[a].ele!) * (xs[n] - xs[a])) /
                (xs[b] - xs[a] || 1);
    }
    for (let n = 1; n < track.length; n++)
      rawAscentM += Math.max(0, track[n].ele! - track[n - 1].ele!);
    let idx = 0;
    const interpolate = (x: number) => {
      while (idx < xs.length - 2 && xs[idx + 1] < x) idx++;
      const t = (x - xs[idx]) / (xs[idx + 1] - xs[idx]);
      return track[idx].ele! + (track[idx + 1].ele! - track[idx].ele!) * t;
    };
    // Uniform distance grid, exact final endpoint, no dropped remainder. Median
    // filtering acts in metres instead of an arbitrary count of GPS points.
    const grid: { x: number; e: number }[] = [];
    for (let x = 0; x < length; x += 25) grid.push({ x, e: interpolate(x) });
    grid.push({ x: length, e: interpolate(length) });
    const smooth = grid.map((p, n) => {
      if (n === 0 || n === grid.length - 1 || smoothingM === 0) return p.e;
      // Shrink symmetrically at boundaries. Clipping one side biases the
      // median, inventing ramps at endpoints (especially a short remainder).
      const r = Math.min(Math.ceil(smoothingM / 50), n, grid.length - 1 - n),
        values = grid
          .slice(n - r, n + r + 1)
          .map((q) => q.e)
          .sort((a, b) => a - b);
      return values[Math.floor(values.length / 2)];
    });
    const trackId = trackCount++;
    profile.push({ distanceM, elevationM: smooth[0], track: trackId });
    for (let n = 1; n < grid.length; n++) {
      const dx = grid[n].x - grid[n - 1].x,
        de = smooth[n] - smooth[n - 1];
      if (Math.abs(de / dx) > 0.4)
        throw new ModelError(
          "Elevation implies a grade over 40%. Check the GPX elevation spikes or use a corrected export.",
        );
      segments.push({
        horizontalM: dx,
        deltaM: de,
        startM: distanceM,
        elevationM: smooth[n - 1],
        track: trackId,
      });
      distanceM += Math.hypot(dx, de);
      horizontalM += dx;
      ascentM += Math.max(0, de);
      descentM += Math.max(0, -de);
      profile.push({ distanceM, elevationM: smooth[n], track: trackId });
    }
  }
  if (!segments.length || distanceM < 100)
    throw new ModelError(
      "The GPX needs at least 100 m of connected route points.",
    );
  if (duplicates)
    warnings.push(
      message("{count} duplicate or near-identical points removed.", {
        count: duplicates,
      }),
    );
  if (missing)
    warnings.push(
      message(
        "{count} missing elevations filled within their own track; leading/trailing values held constant. Climbing is less certain.",
        { count: missing },
      ),
    );
  if (sparse)
    warnings.push(
      message(
        "{count} point intervals exceed 250 m; short climbs and turns may be missing.",
        { count: sparse },
      ),
    );
  if (gaps)
    warnings.push(
      message(
        "{count} gaps over 2 km excluded. Missing parts are not included in time or distance.",
        { count: gaps },
      ),
    );
  if (trackCount > 1)
    warnings.push(
      message(
        "{count} separate track sections; connecting travel is excluded.",
        { count: trackCount },
      ),
    );
  if (rawAscentM - ascentM > Math.max(30, rawAscentM * 0.15))
    warnings.push(
      message(
        "Elevation processing reduced recorded ascent from {raw} to {modeled} m. Inspect the profile; short climbs may be softened.",
        { raw: Math.round(rawAscentM), modeled: Math.round(ascentM) },
      ),
    );
  return {
    name,
    source: "gpx",
    segments,
    profile,
    distanceM,
    horizontalM,
    ascentM,
    descentM,
    rawAscentM,
    pointCount,
    trackCount,
    warnings,
    smoothingM,
  };
}
export function parseGPX(
  xml: string,
  name = "Imported route",
  smoothingM = 100,
): Route {
  if (new TextEncoder().encode(xml).length > 10 * 1024 * 1024)
    throw new ModelError("Please choose a GPX smaller than 10 MB.");
  if (/<!DOCTYPE|<!ENTITY/i.test(xml))
    throw new ModelError(
      "GPX documents with external entities or DTDs are not supported.",
    );
  if (XMLValidator.validate(xml) !== true)
    throw new ModelError(
      "This file is not valid GPX XML. Try exporting the route again.",
    );
  const root = new XMLParser({
    ignoreAttributes: false,
    removeNSPrefix: true,
    parseTagValue: false,
    processEntities: false,
  }).parse(xml).gpx;
  if (!root) throw new ModelError("This file is not a GPX document.");
  const read = (p: Record<string, unknown>): Point => ({
    lat: String(p["@_lat"] ?? "").trim() === "" ? NaN : Number(p["@_lat"]),
    lon: String(p["@_lon"] ?? "").trim() === "" ? NaN : Number(p["@_lon"]),
    ele:
      p.ele === undefined || String(p.ele).trim() === "" ? null : Number(p.ele),
  });
  const tracks: Point[][] = [];
  for (const trk of array(root.trk))
    for (const seg of array(trk.trkseg))
      tracks.push(array(seg.trkpt).map(read));
  if (!tracks.length)
    for (const rte of array(root.rte)) tracks.push(array(rte.rtept).map(read));
  if (!tracks.length)
    throw new ModelError(
      "No track or route points found. Waypoints alone do not define a ride.",
    );
  return routeFromTracks(tracks, name.replace(/\.gpx$/i, ""), smoothingM);
}
// Fictional profile; no personal GPX or real location is bundled.
export function demoRoute(): Route {
  const anchors = [
    [0, 180],
    [5000, 205],
    [8000, 190],
    [12000, 390],
    [14500, 420],
    [18000, 205],
    [22500, 255],
    [27000, 210],
    [30000, 305],
    [34000, 190],
    [38000, 180],
  ];
  const segments: Segment[] = [],
    profile: ProfilePoint[] = [{ distanceM: 0, elevationM: 180, track: 0 }];
  let distanceM = 0,
    ascentM = 0,
    descentM = 0;
  for (let j = 1; j < anchors.length; j++)
    for (let x = anchors[j - 1][0]; x < anchors[j][0]; x += 100) {
      const dx = Math.min(100, anchors[j][0] - x),
        grade =
          (anchors[j][1] - anchors[j - 1][1]) /
          (anchors[j][0] - anchors[j - 1][0]),
        e = anchors[j - 1][1] + (x - anchors[j - 1][0]) * grade,
        de = grade * dx;
      segments.push({
        horizontalM: dx,
        deltaM: de,
        startM: distanceM,
        elevationM: e,
        track: 0,
      });
      distanceM += Math.hypot(dx, de);
      ascentM += Math.max(0, de);
      descentM += Math.max(0, -de);
      profile.push({ distanceM, elevationM: e + de, track: 0 });
    }
  return {
    name: "The Sunday Loop",
    source: "demo",
    segments,
    profile,
    distanceM,
    horizontalM: 38000,
    ascentM,
    descentM,
    rawAscentM: ascentM,
    pointCount: profile.length,
    trackCount: 1,
    warnings: [],
    smoothingM: 0,
  };
}
