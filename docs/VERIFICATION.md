# Public beta verification · updated 19 November 2026

## Final result

The owner approved [PR #3](https://github.com/CIF84/cycling_sim/pull/3) on 19 November 2026. Its chart-linked climbs are merged into `main` and published to production as version `000bf4d7-8d28-41ce-bc5c-f4f482decdff`. The dated entries below retain preview and earlier release history.

The owner approved PR #2 on 19 November 2026. Its Elevation / Energy chart, GPX remainder correction and opt-in remembered setup are merged into `main` and published to production as version `cca515d5-bfb5-40f6-929c-9acfedff1f87`. The dated entries below retain the earlier preview/launch history.

React/Vite beta is merged into `main` through PR #1 and published after owner approval on 16 October 2026. GPX parsing and simulation run locally in a browser worker, independently from the UI. The Python prototype and original README remain available as historical material. [Production](https://bike-science-pro.roman-christov.workers.dev) and [preview](https://bike-science-pro-preview.roman-christov.workers.dev) use separate Cloudflare Workers. No custom domain or Spořilov change was made.

The fictional demo is 38.0 km, 400 m climbing and 400 m descending. Default inputs yield about **1 h 26 min**, **26.6 km/h**, and **880 kJ** crank work. These are model outputs, not validated ride observations. Raising sustainable power from 180 to 220 W changes the demo to about **1 h 17 min**. Gearing-only changes leave time unchanged.

## Baseline and numerical checks

- System Python baseline could not import the historical tests because pandas/gpxpy were absent. Those tests use pytest-style functions; `unittest` discovery was only a dependency/import check, not proof of baseline correctness.
- The legacy pure solver was extracted with Python AST and executed independently of its pandas import. It reproduced **0.36 km/h** at 0 W, −5%, 90 kg, and also at zero-power flat riding in −30 km/h tailwind.
- **136 TypeScript unit checks pass** (`pnpm test`): 64 numerical/GPX/profile/climb, 29 localization/formatting, 31 groupset and 12 storage checks. Representative flat/climbing/descending/windy calculations match an independently written Newton reference, using algebraic slope geometry rather than production force or solver functions. Flat 36 km/h recovers a hand-computed 266.4999226804124 W at 90 kg, density 1.225, CdA .35, Crr .005 and efficiency .97.
- Zero-power −5% descent matches its closed-form terminal speed (about 49 km/h); flat/uphill zero-power sections explicitly fail route completion. Strong-tailwind coasting matches its separate analytical solution.
- Checks include invalid inputs, exact slope geometry, air-density trends, speed ceilings and reduced work under braking, route totals, time-weighted cadence flags, gearing invariance, independent one-field scenarios, negative weight savings on a descent, unchanged zero-power scenario omission, and inverse reachability including a 30% climb.
- GPX checks cover independent great-circle distance, sparse-point distance preservation, final remainders, net elevation, route points/namespaces, track separation, duplicates, partial/no elevation, malicious DTD/malformed XML, excluded jumps, spike rejection, smoothing and demo integrity.

## Browser and accessibility checks

**50 browser cases pass** across desktop Chrome (1440×1000) and mobile Chrome emulating iPhone 13 (390×844), against the local build, [preview](https://bike-science-pro-preview.roman-christov.workers.dev) and [production](https://bike-science-pro.roman-christov.workers.dev). The latest production run on 19 November passed without retries in 30.1 seconds. Earlier localization checks also passed in Cloudflare’s local Workers runtime. Tested interactions:

- Immediate demo and moving time; sustainable watts and gravel surface changes.
- Front chainring edits change cadence while preserving ride time; wind changes route time.
- Input reset, keyboard profile slider, briefing file download, comparison updates and no page-level horizontal overflow.
- Shared Elevation / Energy cursor and moving time, zero-work coasting and English/Czech accessible chart controls. Climb selection/highlighting, section time/work/cadence, input updates, clear/focus behavior and same-filename route replacement.
- Local setup opt-in, refresh, valid/invalid edits, preset/custom gearing, reset/removal, two-tab forgetting, blocked storage, and exclusion of GPX data and visit conditions.
- Synthetic GPX import with 50 m ascent, quality disclosure, smoothing toggle, missing elevations, malformed files, stationary zero-power estimate, invalid mass and recovery to the demo.
- A 20,000-point synthetic import with rapid power changes; latest inputs win and superseded worker results do not replace them. The test completed in under a second on this machine; no general phone performance guarantee is made.
- No non-GET upload requests and no outbound requests beyond the app origin during the exercised flow.
- Axe WCAG 2 A/AA and 2.1 AA audit: **zero detected violations** with advanced condition/gearing inputs open, on both viewport sizes. Faint secondary text and a missing file-picker label found during testing were corrected. This is an automated audit, not full accessibility certification.

The local app was also opened and inspected in the Codex browser at desktop and phone sizes. An in-app file-chooser automation failure prevented that particular manual import attempt; imports were successfully exercised in the independent production-browser test suite. Screenshots from automated browser runs were inspected; the phone chart was revised to use the available width rather than shrink a desktop plot. Only Chromium has automated coverage; real iOS Safari/Android devices have not been validated.

## Build and hosting verification

- TypeScript strict check and production Vite build pass (`pnpm build`). Main JS about 318 kB (104 kB gzip), separate GPX/model worker about 74 kB, CSS about 23 kB (6 kB gzip). All runtime assets are local.
- Preview Worker `--dry-run` accepts static assets with no server bindings. Actual local workerd serves security headers and supports the client-side worker/download/import flows.
- Compatibility date adjusted from 2026-10-14 to **2026-10-13**, the newest date supported by the installed pinned runtime. This avoids a local startup failure.
- Production CSP blocks outbound app connections. No analytics, external fonts or GPX uploads. `sample_routes/my_ride.gpx`, Python files, tests and docs are absent from `dist`.
- Owner completed Cloudflare OAuth and the separate `bike-science-pro-preview` Worker was deployed on 14 October 2026. The review fixes were deployed on 15 October 2026 as version `26c908f8-f974-4412-bcaa-146a8cf788e8`. Those initial releases deployed only the preview; the production launch is recorded below.
- Hosted HTTPS response is 200 with CSP, no-framing, no-referrer, nosniff and restricted permissions headers. All 5 served public assets match the local build byte for byte. Cloudflare also adds its infrastructure network-error reporting headers; the application has no analytics or route uploads.
- On 14 October, the first test run immediately after the initial deployment hit Cloudflare's initial propagation: one document request and two asset requests returned 404. Six tests passed. After propagation, a full rerun passed **all 8 tests in 9.9 seconds**, with no test retries or application changes. The deployed app was also opened in the Codex browser for review.

## PR #1 review follow-up · 15 October 2026

- Fixed three reproduced defects: asymmetric endpoint smoothing could reject a valid descent or invent steep ramps; an immobile comparison could discard a valid baseline; the profile could report the next section’s grade too early or combine data across a track break. See [review findings and corrections](PR_REVIEW.md).
- Nine added numerical/profile regressions cover constant positive/negative slopes, a 1 m final interval, two smoothing widths, unavailable tailwind comparisons, profile interpolation and track boundaries. The seven smoothing/comparison regressions failed against the original implementation; the profile regression was also reproduced against the original hosted preview on both browser sizes.
- All **49 numerical/GPX/profile checks**, strict TypeScript, and production build pass. All **14 browser checks** pass in local Cloudflare Workers (8.2 s) and the updated hosted preview (13.3 s), with no retries. New browser cases exercise corrected descent import, exact profile grade, unavailable-comparison display/download, and no-gain comparisons. Comparison bar geometry is also checked.
- Desktop/mobile screenshots of the new unavailable state were inspected, and the updated live demo was opened in the Codex browser. The existing Axe audit still reports zero detected violations.
- `pnpm audit --prod` reports no known runtime dependency vulnerabilities at review time. Deployed asset hashes and HTTPS/security headers were verified again.
- PR #1 remains open and unmerged; no production deployment was performed.

## Czech localization · 16 October 2026

- Added a complete English/Czech website catalog, including model explanations, assumptions, privacy text, chart accessibility, preparation/comparison results, GPX warnings, validation errors and downloaded briefings. The selector preserves route, inputs and results. Explicit language links override the saved choice; browser language is the initial fallback.
- Czech decimal commas and point input are accepted without changing numerical units. Ambiguous/invalid values are rejected. Structured worker messages can be translated after calculation, so changing language does not restart computation. No equations, GPX processing or comparison scenarios changed.
- Only the selected language is saved locally; routes/settings remain in memory. Imported filenames are never translated. No translation API or additional network service was added.
- All **71 unit checks** pass: 49 existing model/GPX/profile checks and 22 localization cases. Strict TypeScript, production build, formatting and diff checks pass.
- All **22 browser checks** pass in local Cloudflare Workers (9.5 s) and the hosted preview (15.4 s), without retries. They exercise Czech browser defaults, explicit/saved preference, unavailable storage, comma input, live warning/error translation, unchanged worker count on language switches, GPX-name preservation, downloads and both viewport sizes. English regression coverage remains intact.
- Both languages pass the automated accessibility audit with advanced inputs open; the Czech model/privacy explanations are also expanded for the audit. No horizontal page overflow was detected. Desktop and mobile screenshots were inspected, and the live Czech preview was opened in the app browser. Independent native-language review remains with the owner.
- Preview version **`7b3412ef-44a7-438b-83bf-6af239e412cb`** is deployed only to `bike-science-pro-preview`. All five public asset hashes match the local build (following the canonical redirect from `/index.html`); HTTPS/security headers are verified. PR #1 remains unmerged and production remains unpublished.

See [localization details and review notes](LOCALIZATION.md).

## Czech label/layout follow-up · 16 October 2026

Shortened the altitude input label to “Nadmořská výška”, retaining the explanation below. Paired fields now align their input boxes even if a label wraps at narrow widths. Browser inspection confirmed equal input top positions at 1440, 1024, 390 and 320 px. Production build and all four hosted English/Czech desktop/mobile form/accessibility checks pass. Preview version: `477353a0-f428-46e5-81be-f392651de2c7`. No calculation change or production publication.

## Groupset presets · 16 October 2026

- Added 25 curated Shimano/SRAM road and gravel configurations, setting both chainrings and every cassette cog. Specifications and generation/derailleur compatibility were checked only against official manufacturer sources. Each preset exposes source links; the complete dated record is in [GROUPSETS.md](GROUPSETS.md).
- Current Tiagra R4000 is 2×11; SRAM RED/Force/Rival XPLR E1 are 1×13, while Apex XPLR remains 1×12 in these examples. GRX 10–45/10–51 presets use the appropriate GS/SGS configurations. These are representative setups, not every possible factory or aftermarket combination.
- Default changed intentionally from 50/34 with 11-speed 11–32 to Shimano 105 50/34 with 12-speed 11–34. Cadence insights can change; power, mass, moving time, work and comparison results do not. An independent wheel-speed/cadence calculation and simulation checks verify that separation.
- All **102 unit checks**, strict TypeScript and production build pass. All **26 browser checks** pass against the local production build (12.5 s) and hosted preview (19.0 s), without retries. The four new groupset cases also passed locally after the final source-panel spacing refinement.
- Browser cases cover both manual tooth fields, invalid-list recovery, reset, language switching without losing the preset, official reference links, exported actual gearing, unchanged ride estimates and comparisons, and no overflow at 320 px. Axe detects zero violations with source details expanded. Desktop/mobile layouts were visually inspected.
- Preview version **`4e381995-5515-4717-824a-6d9a2c9d9b8f`** serves the verified build. All five public asset hashes and HTTPS/security headers pass. The GPX/model worker bundle is unchanged. PR #1 remains unmerged; production remains unpublished.

## Production launch · 16 October 2026

- The owner approved merge and publication. PR #1 merged at 13:22 UTC as **`d01d1470fb4765979a3fd0bb81cf7cb72b40a3ad`**. The deployed app, dependencies and hosting configuration exactly match the reviewed beta commit `7a2440e`.
- Re-ran all **102 unit checks**, strict TypeScript and the production build before release. Published to **`bike-science-pro`**, version **`64b18568-b3d0-47a0-a292-4c5ed8bedfe1`**.
- All **26 production desktop/mobile browser checks pass in 18.8 seconds**, without retries: demo, GPX imports, errors, comparisons, localization, groupset/manual editing, downloads and accessibility. The production demo was also opened and visually inspected in the app browser.
- Production returns HTTPS 200 with the configured CSP, no-framing, no-referrer, nosniff and restricted permissions headers. All five served public assets match the local build byte for byte.
- The preview remains available independently. No custom domain, production backend, GPX upload service or Spořilov change was introduced. Documentation updates after the launch do not change the deployed assets.

## Elevation / Energy preview · 16 October 2026

- Added an Elevation / Energy selector with one shared cursor and slider. Both views show estimated moving time from the start; Energy shows accumulated pedal work and work remaining in kJ. Switching views/languages retains position and does not start a new simulation worker. No fueling recommendations or new metabolic estimates were added.
- Six model checks cover independently calculated flat-route time/work, partial sections, exact boundaries, a short remainder, coasting, reduced power at a speed ceiling, track breaks, monotonic accumulation and agreement with briefing totals. Seven formatting cases cover zero/sub-minute progress and rounding.
- The new coasting browser case exposed a pre-existing GPX roundoff defect: a nominal 1,000 m track could gain a final interval of roughly `1e-13 m`, with zero elevation change, falsely blocking zero-power riding. Three regressions failed on the previous implementation. The grid now folds sub-micrometre remainders into the preceding interval while retaining exact endpoint distance/elevation. Real short intervals remain preserved.
- All **118 unit checks**, strict TypeScript, production build, formatting and diff checks pass. All **32 local desktop/mobile browser cases** pass (14.9 s). On the hosted preview, 31 initially passed and one navigation failed with `ERR_NETWORK_IO_SUSPENDED` before the app loaded. Both desktop/mobile larger-route cases passed on rerun, including the added Energy endpoint check. No app change or redeployment was required for that transient navigation failure.
- Browser coverage includes keyboard/pointer inspection, switching at the same distance, updated power, translated accessible slider values, zero-work rides with advancing time, separate tracks, 20,000-point imports, both languages, 320 px layouts and zero detected Axe violations. Desktop and mobile views were visually inspected. Existing demo, import, error, comparison, download and groupset coverage remains intact.
- Preview version **`f20e7de0-59c8-47f4-bb9d-a3e9581ccf22`** serves the verified build. HTTPS/security headers and all five public asset bytes match locally. Production was checked and still serves its approved launch assets. This branch remains unmerged pending owner review.

## Remembered setup · 19 November 2026

- Added opt-in local rider/bike/power/model preferences, including presets and custom tooth lists. GPX content, filenames and route data are never persisted; wind, temperature and altitude reset for every visit. The first simulation uses validated restored inputs.
- Valid edits save automatically. Invalid edits retain the last good setup; corrupt/incompatible saved records fall back to defaults with a message. Turning saving off keeps current inputs, removes only the setup key, and stops other open tabs from saving it again. Reset saves defaults only while opted in.
- Storage access/quota/removal failures are handled without breaking simulation. Even if deletion fails, opting out stops future writes and offers removal retry with an explanation. Language remains independent. No model equations, dependencies, backend or account system changed.
- **130 unit checks**, strict TypeScript, production build, formatting and diff checks pass. **42 desktop/mobile browser cases pass** against the final local build (23.9 s), without retries. Coverage includes opt-in/refresh, presets/custom gears, invalid edits, reset, route/condition exclusion, two-tab removal, blocked storage, Czech/English, accessibility and 320/820 px layouts. Saved-state desktop/mobile screenshots were inspected.
- All **42 hosted desktop/mobile browser cases pass** without retries (29.7 s). The hosted Czech setup was manually checked through save, refresh, restored values and removal; test inputs were cleared. Published asset bytes and security headers match the tested build.
- Preview version **`a3928998-5ad1-4a2c-8e44-4d1c2c07589b`** was deployed from `e37f544` after renewing Cloudflare authorization in the owner's signed-in Safari session. Production deployment history was checked before and after and remains on **`64b18568-b3d0-47a0-a292-4c5ed8bedfe1`**. PR #2 remains draft and unmerged. See [the local storage contract and review steps](LOCAL_SETUP.md).

## Production update · 19 November 2026

- Owner approved merging and publishing PR #2. Merge commit **`a44e3df157119b4a0febc094fe7f7be531b002dc`** has exactly the reviewed tree from `cb93776`.
- Re-ran all **130 unit checks**, strict TypeScript and the production build before publication. Deployed only **`bike-science-pro`**, version **`cca515d5-bfb5-40f6-929c-9acfedff1f87`**.
- All **42 production desktop/mobile browser checks pass** without retries (28.2 s). Coverage includes the new Energy and local setup features plus demo, import, error, comparison, groupset, localization, download and accessibility regressions. The live Czech demo was also opened to confirm both controls and its completed briefing.
- All five production asset bytes and configured security headers match the tested build. Preview deployment history confirms it remains independently on `a3928998-5ad1-4a2c-8e44-4d1c2c07589b`. No custom domain, backend, GPX upload or Spořilov change.
- Production and preview use separate browser storage; preferences saved on preview do not automatically appear on production. Release documentation changes after deployment do not alter the published application.

## Chart-linked climb preview · 19 November 2026

- Demanding-section cards now select a shaded interval in both chart views and move the shared cursor to its start. The whole route stays available. A clear action removes the selection. The summary shows section moving time, actual crank work and lowest modeled pedaling cadence, in English or Czech.
- Extracted the existing climb grouping into a pure model module without changing its thresholds. Stable geometry IDs preserve the selected climb when power changes re-rank the cards. Route replacement, smoothing, reset and errors clear selection; changing chart view, language, power or gearing keeps valid selection.
- Six added model checks cover independent constant-grade time/work/cadence calculations, reduced work at a speed ceiling, tailwind coasting, track breaks, minimum length, ranking, stable IDs and mixed pedaling/coasting cadence. All **136 unit checks**, strict TypeScript and the production build pass. No simulation equations or worker bundle changed.
- All **50 local desktop/mobile browser cases pass** without retries (24.5 s). Eight new cases cover keyboard/touch selection, shared views/slider, recalculated summaries, gearing-only invariance, clearing/focus, invalid-input recovery, smoothing and same-filename GPX replacement. Czech/English and 320 px layouts are covered; Axe reports zero detected violations with a climb selected. Desktop and phone screenshots were visually inspected.

- All **50 hosted desktop/mobile cases pass** without retries (33.1 s). The hosted Czech climb selection and Energy switch were manually inspected; desktop/mobile screenshots cover both views. All five public assets match the tested build byte for byte, and configured security headers are present.
- Preview version **`8e4248ed-0c6e-42dc-8d56-df817470d775`** was deployed from `acd4134`. Production history remains on **`cca515d5-bfb5-40f6-929c-9acfedff1f87`**. This update is held in draft PR #3 for owner review; no production deployment was performed.

## Climb-card production release · 19 November 2026

- Owner approved merge and publication of PR #3. Merge commit **`4fd758615f67d6f33766c8c5ca7a987a0d491cad`** has exactly the reviewed tree from `23eb58d`.
- Re-ran all **136 unit checks**, strict TypeScript and production build before publication. Deployed only **`bike-science-pro`**, version **`000bf4d7-8d28-41ce-bc5c-f4f482decdff`**.
- All **50 production desktop/mobile browser checks pass** without retries (30.1 s), including climb interactions and prior demo, GPX, comparison, localization, groupset, storage, download and accessibility coverage. The live Czech climb summary and Energy highlight were also inspected manually.
- All five production assets match the tested build byte for byte; configured security headers are present. Preview remains independently on `8e4248ed-0c6e-42dc-8d56-df817470d775`. No custom domain, backend or Spořilov change.
- Release documentation commits after publication do not alter the deployed assets.

## Remaining limitations

No known failing local checks remain. This is published as an owner-approved **planning-estimate public beta**, with assumptions visible. Route-time accuracy has not been validated on real outdoor rides. GPS elevation/sparse recordings, unknown CdA/Crr, steady-state transitions, braking/turns, stops, constant wind and fatigue can produce material errors. No claimed confidence interval or physiological sustainability predictor exists.

Fuel/sweat/sodium prescriptions, manual routes inferred from totals, accounts, cloud route storage, integrations and AI were deferred for reliability and launch focus. Opt-in browser setup preferences are separate from route storage. A bounded inverse-power utility is numerically checked but not shown publicly because mathematical reachability does not prove a rider can sustain the required power.

The initial beta, PR #2 and PR #3 owner reviews, merges and production publications are complete. Production uses its dedicated `workers.dev` address; a custom domain remains optional and has not been selected. Recommended next evidence: compare several rides with measured sustainable power and good elevation data; record model residuals rather than tuning against one ride. Expand to actual Safari/phone testing before claiming broad browser support.
