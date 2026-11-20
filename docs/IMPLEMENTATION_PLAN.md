# Public beta implementation plan

Baseline (14 October 2026): Python/Streamlit prototype, no frontend or hosting configuration; existing pytest-style tests cannot run with system Python because pandas/gpxpy are absent. Source audit confirms unsigned aerodynamic force, 0.1 m/s coasting floor, force clamp, omitted segment boundaries, joined track breaks, FTP-like W/kg coupled to rider mass, invented grade pacing and unsupported sweat assumptions. Historical source remains in place, explicitly outside the beta runtime.

1. Implement an independent, typed browser model: signed wind, exact slope geometry, bracketed equilibrium solver, zero-power coasting, validation, one-variable comparisons and checked inverse bounds.
2. Parse GPX locally, separate tracks, interpolate partial elevations with warnings, require elevation for every usable track, preserve distance and segment endpoint elevation, apply distance-based smoothing and expose its effect. Ship synthetic demo only.
3. Build a responsive ride briefing, editable assumptions, gearing, profile, demanding sections, preparation guidance and ranked comparisons. Worker processing keeps parsing/simulation off the UI thread.
4. Add independent numerical and GPX regression checks. Exercise actual browser interactions at desktop/mobile; build production assets and verify Cloudflare configuration.
5. Document model evidence, intentional historical differences, privacy, deployment and beta limitations. Deploy an isolated preview only if existing access permits; no production-domain publication.

Launch scope: no accounts/storage/weather/Strava/payments/AI. No physiological difficulty score or sweat/sodium prescription. No manual route from distance+ascent (terrain distribution is unknown). No public inverse-time UI until physiological feasibility can be explained; the numerical utility validates bounded reachability.

## Groupset presets — 16 October 2026

Baseline: two cassette-only presets; chainring edits could leave the named cassette preset selected. All 71 unit checks and 22 browser checks passed for the preceding localization release.

1. Check current Shimano/SRAM road and gravel generations, exact chainring combinations, every cassette cog and compatible derailleur configurations against manufacturer sources only. Record dated references and distinguish curated examples from universal factory specifications.
2. Store the catalog independently of UI/localization. Apply chainrings and cassette together, preserve manual editing, and make a manual change to either field select Custom. Keep all other simulation inputs unchanged.
3. Provide English/Czech controls, readable gearing summaries and manufacturer links. Verify catalog integrity, cadence/time behavior, preset/custom/reset interactions, accessibility and mobile layout.
4. Build, update documentation, deploy and verify only the separate preview, then push the update to the existing unmerged PR.

## Elevation / Energy chart — 16 October 2026

Baseline: production is the approved `d01d147` application, documented by `27c64e2`; 102 unit checks and 26 production browser checks passed. The chart currently exposes elevation, grade and speed with one distance slider. Work and moving time are already calculated per section.

1. Carry cumulative moving time and crank work through the independent model, using actual modeled power (including coasting and speed-cap reductions). Check partial sections, endpoints, track breaks and zero-work rides against independent calculations.
2. Reuse the existing chart for Elevation / Energy views, preserving one cursor and adding moving time to both. Explain pedal work in kJ; defer fueling recommendations and new calorie estimates. Localize controls and accessibility text.
3. Exercise switching, keyboard/pointer input, changed inputs, large/short routes, coasting, Czech/English and narrow screens. Build and verify the preview, keeping production unchanged pending owner review.

## Chart-linked climbs — 19 November 2026

Baseline: PR #2 is published on production; 130 unit checks and 42 production browser cases pass. Climb cards are static, and the chart inspects one point at a time.

1. Extract the existing climb grouping into a pure model module, adding actual pedal work and stable geometry IDs. Preserve thresholds and track breaks; independently verify totals, ranking and cadence/coasting cases.
2. Make climb cards accessible selection buttons. Highlight the section in both chart views, retain whole-route inspection, expose climb time/work/lowest cadence, and provide clear selection. Keep selection through power/gearing/language/view changes; clear it for new routes and smoothing.
3. Verify keyboard/touch, numeric updates, clearing, GPX replacement (including identical filenames), boundaries, both languages and narrow layouts. Deploy only the separate preview; production requires a later owner decision.

Completed: 136 unit checks, strict TypeScript, production build and all 50 desktop/mobile cases pass locally and on the hosted preview. Climb selection was also checked manually in the Czech preview. The owner subsequently approved PR #3, which is merged and published to production. All 50 production browser cases pass; see the deployment and verification records.

## Local fuel and water plan — 19 November 2026

Baseline: approved PR #3 production, 136 unit checks and 50 production browser cases passing. Food/water preparation is explanatory only.

1. Keep expenditure, mechanical work and carbohydrate intake distinct. Use AIS duration guidance with editable targets; fluid rate is an explicit planning assumption, never inferred from watts or temperature. Document primary sources and practical timing choices.
2. Add pure local planning calculations for intake totals, 20-minute fuel windows, distance/time mapping and bottle coverage between manual full-refill stops. No food catalog, glycogen prediction, weather service or persistence of routes/stops.
3. Connect optional planning markers/readouts to both chart views, preserve climb inspection, add accessible English/Czech controls and include the plan in the downloaded briefing.
4. Verify independent arithmetic, boundaries, coasting, invalid inputs, track breaks, update/reset behavior, desktop/mobile accessibility and local-only operation. Deploy and verify preview; leave production unchanged.

Completed: 156 unit checks, strict TypeScript, production build and all 62 desktop/mobile browser cases pass locally and on the hosted preview. The live Czech plan/refill/chart flow was also inspected manually. Preview version `4260a839-3b02-4b8e-81e9-0baf4dfeeeeb` was reviewed by the owner, who approved [PR #4](https://github.com/CIF84/cycling_sim/pull/4) for merge and publication on 20 November 2026. Production version `e398b6db-22e8-489c-82c8-4127610d5c7a` passes all 62 browser cases; see the deployment and verification records.
