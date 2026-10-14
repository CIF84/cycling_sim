# Public beta verification · updated 15 October 2026

## Final result

React/Vite beta implemented in this checkout, with source review on the `codex/bike-science-pro-beta` branch. GPX parsing and simulation run locally in a browser worker, independently from the UI. The Python prototype and original README remain available as historical material. Cloudflare publication is limited to the separate preview Worker. No production-domain publication or Spořilov change was made.

The fictional demo is 38.0 km, 400 m climbing and 400 m descending. Default inputs yield about **1 h 26 min**, **26.6 km/h**, and **880 kJ** crank work. These are model outputs, not validated ride observations. Raising sustainable power from 180 to 220 W changes the demo to about **1 h 17 min**. Gearing-only changes leave time unchanged.

## Baseline and numerical checks

- System Python baseline could not import the historical tests because pandas/gpxpy were absent. Those tests use pytest-style functions; `unittest` discovery was only a dependency/import check, not proof of baseline correctness.
- The legacy pure solver was extracted with Python AST and executed independently of its pandas import. It reproduced **0.36 km/h** at 0 W, −5%, 90 kg, and also at zero-power flat riding in −30 km/h tailwind.
- **49 TypeScript numerical/GPX/profile tests pass** (`pnpm test`). Representative flat/climbing/descending/windy calculations match an independently written Newton reference, using algebraic slope geometry rather than production force or solver functions. Flat 36 km/h recovers a hand-computed 266.4999226804124 W at 90 kg, density 1.225, CdA .35, Crr .005 and efficiency .97.
- Zero-power −5% descent matches its closed-form terminal speed (about 49 km/h); flat/uphill zero-power sections explicitly fail route completion. Strong-tailwind coasting matches its separate analytical solution.
- Checks include invalid inputs, exact slope geometry, air-density trends, speed ceilings and reduced work under braking, route totals, time-weighted cadence flags, gearing invariance, independent one-field scenarios, negative weight savings on a descent, unchanged zero-power scenario omission, and inverse reachability including a 30% climb.
- GPX checks cover independent great-circle distance, sparse-point distance preservation, final remainders, net elevation, route points/namespaces, track separation, duplicates, partial/no elevation, malicious DTD/malformed XML, excluded jumps, spike rejection, smoothing and demo integrity.

## Browser and accessibility checks

**14 browser tests pass** across desktop Chrome (1440×1000) and mobile Chrome emulating iPhone 13 (390×844). The full suite passed against both the **production build served by Cloudflare’s local Workers runtime** and the [deployed preview](https://bike-science-pro-preview.roman-christov.workers.dev), not only the Vite dev server. Tested interactions:

- Immediate demo and moving time; sustainable watts and gravel surface changes.
- Front chainring edits change cadence while preserving ride time; wind changes route time.
- Input reset, keyboard profile slider, briefing file download, comparison updates and no page-level horizontal overflow.
- Synthetic GPX import with 50 m ascent, quality disclosure, smoothing toggle, missing elevations, malformed files, stationary zero-power estimate, invalid mass and recovery to the demo.
- A 20,000-point synthetic import with rapid power changes; latest inputs win and superseded worker results do not replace them. The test completed in under a second on this machine; no general phone performance guarantee is made.
- No non-GET upload requests and no outbound requests beyond the app origin during the exercised flow.
- Axe WCAG 2 A/AA and 2.1 AA audit: **zero detected violations** with advanced condition/gearing inputs open, on both viewport sizes. Faint secondary text and a missing file-picker label found during testing were corrected. This is an automated audit, not full accessibility certification.

The local app was also opened and inspected in the Codex browser at desktop and phone sizes. An in-app file-chooser automation failure prevented that particular manual import attempt; imports were successfully exercised in the independent production-browser test suite. Screenshots from automated browser runs were inspected; the phone chart was revised to use the available width rather than shrink a desktop plot. Only Chromium has automated coverage; real iOS Safari/Android devices have not been validated.

## Build and hosting verification

- TypeScript strict check and production Vite build pass (`pnpm build`). Main JS about 261 kB (83 kB gzip), separate GPX/model worker about 73 kB, CSS about 19 kB (5 kB gzip). All runtime assets are local.
- Preview Worker `--dry-run` accepts static assets with no server bindings. Actual local workerd serves security headers and supports the client-side worker/download/import flows.
- Compatibility date adjusted from 2026-10-14 to **2026-10-13**, the newest date supported by the installed pinned runtime. This avoids a local startup failure.
- Production CSP blocks outbound app connections. No analytics, external fonts or GPX uploads. `sample_routes/my_ride.gpx`, Python files, tests and docs are absent from `dist`.
- Owner completed Cloudflare OAuth and the separate `bike-science-pro-preview` Worker was deployed on 14 October 2026. The review fixes were deployed on 15 October 2026 as version `26c908f8-f974-4412-bcaa-146a8cf788e8`. No production Worker/custom domain was deployed or changed.
- Hosted HTTPS response is 200 with CSP, no-framing, no-referrer, nosniff and restricted permissions headers. All 5 served public assets match the local build byte for byte. Cloudflare also adds its infrastructure network-error reporting headers; the application has no analytics or route uploads.
- On 14 October, the first test run immediately after the initial deployment hit Cloudflare's initial propagation: one document request and two asset requests returned 404. Six tests passed. After propagation, a full rerun passed **all 8 tests in 9.9 seconds**, with no test retries or application changes. The deployed app was also opened in the Codex browser for review.

## PR #1 review follow-up · 15 October 2026

- Fixed three reproduced defects: asymmetric endpoint smoothing could reject a valid descent or invent steep ramps; an immobile comparison could discard a valid baseline; the profile could report the next section’s grade too early or combine data across a track break. See [review findings and corrections](PR_REVIEW.md).
- Nine added numerical/profile regressions cover constant positive/negative slopes, a 1 m final interval, two smoothing widths, unavailable tailwind comparisons, profile interpolation and track boundaries. The seven smoothing/comparison regressions failed against the original implementation; the profile regression was also reproduced against the original hosted preview on both browser sizes.
- All **49 numerical/GPX/profile checks**, strict TypeScript, and production build pass. All **14 browser checks** pass in local Cloudflare Workers (8.2 s) and the updated hosted preview (13.3 s), with no retries. New browser cases exercise corrected descent import, exact profile grade, unavailable-comparison display/download, and no-gain comparisons. Comparison bar geometry is also checked.
- Desktop/mobile screenshots of the new unavailable state were inspected, and the updated live demo was opened in the Codex browser. The existing Axe audit still reports zero detected violations.
- `pnpm audit --prod` reports no known runtime dependency vulnerabilities at review time. Deployed asset hashes and HTTPS/security headers were verified again.
- PR #1 remains open and unmerged; no production deployment was performed.

## Remaining limitations and launch decision

No known failing local checks remain. This is ready for owner review as a **planning-estimate public beta**, with assumptions visible. Route-time accuracy has not been validated on real outdoor rides. GPS elevation/sparse recordings, unknown CdA/Crr, steady-state transitions, braking/turns, stops, constant wind and fatigue can produce material errors. No claimed confidence interval or physiological sustainability predictor exists.

Fuel/sweat/sodium prescriptions, manual routes inferred from totals, accounts, storage, integrations and AI were deferred for reliability and launch focus. A bounded inverse-power utility is numerically checked but not shown publicly because mathematical reachability does not prove a rider can sustain the required power.

Remaining release gate: owner review of the hosted preview and production domain. Cloudflare authentication and preview deployment are complete. No production domain is selected or connected automatically. Recommended next evidence: compare several rides with measured sustainable power and good elevation data; record model residuals rather than tuning against one ride. Expand to actual Safari/phone testing before claiming broad browser support.
