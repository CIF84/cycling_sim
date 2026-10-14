# Public beta implementation plan

Baseline (14 October 2026): Python/Streamlit prototype, no frontend or hosting configuration; existing pytest-style tests cannot run with system Python because pandas/gpxpy are absent. Source audit confirms unsigned aerodynamic force, 0.1 m/s coasting floor, force clamp, omitted segment boundaries, joined track breaks, FTP-like W/kg coupled to rider mass, invented grade pacing and unsupported sweat assumptions. Historical source remains in place, explicitly outside the beta runtime.

1. Implement an independent, typed browser model: signed wind, exact slope geometry, bracketed equilibrium solver, zero-power coasting, validation, one-variable comparisons and checked inverse bounds.
2. Parse GPX locally, separate tracks, interpolate partial elevations with warnings, require elevation for every usable track, preserve distance and segment endpoint elevation, apply distance-based smoothing and expose its effect. Ship synthetic demo only.
3. Build a responsive ride briefing, editable assumptions, gearing, profile, demanding sections, preparation guidance and ranked comparisons. Worker processing keeps parsing/simulation off the UI thread.
4. Add independent numerical and GPX regression checks. Exercise actual browser interactions at desktop/mobile; build production assets and verify Cloudflare configuration.
5. Document model evidence, intentional historical differences, privacy, deployment and beta limitations. Deploy an isolated preview only if existing access permits; no production-domain publication.

Launch scope: no accounts/storage/weather/Strava/payments/AI. No physiological difficulty score or sweat/sodium prescription. No manual route from distance+ascent (terrain distribution is unknown). No public inverse-time UI until physiological feasibility can be explained; the numerical utility validates bounded reachability.
