import { it, expect } from "vitest";
import { parseGPX, routeFromTracks, haversine, demoRoute } from "./route";
const pt = (lat: number, ele: number | null) => ({ lat, lon: 0, ele });
const xml = (body: string) =>
  `<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">${body}</gpx>`;
const track = (elev = true) =>
  `<trk><trkseg><trkpt lat="0" lon="0">${elev ? "<ele>100</ele>" : ""}</trkpt><trkpt lat="0.01" lon="0">${elev ? "<ele>150</ele>" : ""}</trkpt></trkseg></trk>`;
it("haversine independent equatorial one-degree arc", () =>
  expect(haversine(pt(0, 0), pt(1, 0))).toBeCloseTo(111194.92664456, 5));
it("sparse points preserve every distance interval, final partial segment, and net elevation", () => {
  const r = parseGPX(xml(track()), "sparse.gpx");
  expect(r.horizontalM).toBeCloseTo(1111.9492664456, 6);
  expect(r.segments.reduce((n, s) => n + s.horizontalM, 0)).toBeCloseTo(
    r.horizontalM,
    8,
  );
  expect(r.segments.at(-1)!.horizontalM).toBeLessThan(25);
  expect(r.ascentM).toBeCloseTo(50, 8);
  expect(r.segments.reduce((n, s) => n + s.deltaM, 0)).toBeCloseTo(50, 8);
  expect(r.profile.at(-1)!.elevationM).toBe(150);
  expect(r.warnings.join()).toMatch(/250 m/);
});
it("supports route points and prefixed GPX", () => {
  expect(
    parseGPX(
      xml(
        '<rte><rtept lat="0" lon="0"><ele>20</ele></rtept><rtept lat="0.01" lon="0"><ele>20</ele></rtept></rte>',
      ),
    ).ascentM,
  ).toBe(0);
  expect(
    parseGPX(
      xml(track()).replace(/gpx/g, "ns:gpx").replace("xmlns=", "xmlns:ns="),
    ).ascentM,
  ).toBeCloseTo(50);
});
it("does not join separate tracks or their elevations", () => {
  const r = routeFromTracks(
    [
      [pt(0, 100), pt(0.001, 110)],
      [pt(1, 500), pt(1.001, 490)],
    ],
    "break",
  );
  expect(r.trackCount).toBe(2);
  expect(r.horizontalM).toBeCloseTo(222.389853, 5);
  expect(r.ascentM).toBeCloseTo(10);
  expect(r.descentM).toBeCloseTo(10);
  expect(r.warnings.join()).toMatch(/connecting travel/);
});
it("duplicates do not alter distance or fabricate vertical climbing", () => {
  const r = routeFromTracks(
    [[pt(0, 0), pt(0, 1000), pt(0.01, 10)]],
    "duplicates",
  );
  expect(r.horizontalM).toBeCloseTo(1111.949266, 5);
  expect(r.ascentM).toBeCloseTo(10);
  expect(r.warnings.join()).toMatch(/duplicate/);
});
it("partial missing elevations interpolate within the track; endpoints held constant", () => {
  const r = routeFromTracks(
    [
      [
        pt(0, null),
        pt(0.001, 10),
        pt(0.002, null),
        pt(0.003, 30),
        pt(0.004, null),
      ],
    ],
    "missing",
    0,
  );
  expect(r.profile[0].elevationM).toBe(10);
  expect(r.profile.at(-1)!.elevationM).toBe(30);
  expect(r.ascentM).toBeCloseTo(20);
  expect(r.warnings.join()).toMatch(/3 missing/);
});
it("rejects entirely missing elevations, malformed XML, waypoints and hostile DTD", () => {
  expect(() => parseGPX(xml(track(false)))).toThrow(/no elevation/);
  expect(() => parseGPX("<gpx><broken>")).toThrow(/valid GPX XML/);
  expect(() => parseGPX(xml('<wpt lat="0" lon="0"/>'))).toThrow(/No track/);
  expect(() => parseGPX("<!DOCTYPE gpx><gpx/>")).toThrow(/DTD/);
});
it("splits huge GPS jumps and explicitly excludes their distance", () => {
  const r = routeFromTracks(
    [[pt(0, 0), pt(0.002, 10), pt(1, 10), pt(1.002, 0)]],
    "gap",
  );
  expect(r.horizontalM).toBeCloseTo(444.7797066, 5);
  expect(r.trackCount).toBe(2);
  expect(r.warnings.join()).toMatch(/gaps over 2 km/);
});
it("rejects invalid coordinates and excessive grade", () => {
  expect(() => routeFromTracks([[pt(NaN, 0), pt(0.01, 0)]], "bad")).toThrow(
    /invalid/,
  );
  expect(() => routeFromTracks([[pt(0, 0), pt(0.001, 100)]], "spike")).toThrow(
    /40%/,
  );
});
it("smoothing reduces noise while preserving endpoints and distance", () => {
  const pts = Array.from({ length: 41 }, (_, n) =>
    pt(n * 0.000225, 100 + (n === 20 ? 8 : 0)),
  );
  const raw = routeFromTracks([pts], "noise", 0),
    smoothed = routeFromTracks([pts], "noise", 100);
  expect(smoothed.horizontalM).toBe(raw.horizontalM);
  expect(smoothed.ascentM).toBeLessThan(raw.ascentM);
  expect(smoothed.profile[0].elevationM).toBe(100);
  expect(smoothed.profile.at(-1)!.elevationM).toBe(100);
});
it("demo is synthetic and closes at same elevation with balanced ascent/descent", () => {
  const r = demoRoute();
  expect(r.source).toBe("demo");
  expect(r.ascentM).toBeCloseTo(400, 7);
  expect(r.descentM).toBeCloseTo(400, 7);
  expect(r.horizontalM).toBe(38000);
  expect(r.profile[0].elevationM).toBe(r.profile.at(-1)!.elevationM);
});
