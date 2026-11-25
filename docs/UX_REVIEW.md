# UX review · 20 November 2026

Baseline: production PR #4 (`b840250` documentation head), 156 unit checks and 62 desktop/mobile browser cases passing. This is a heuristic/task review of the existing app, not a user study. Scope: demo and GPX entry, setup, chart/climb inspection, food/water planning, comparison, export and error recovery in English/Czech.

## Findings and implementation

| Finding                                                                                                          | Impact                                                                                    | Implemented correction                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Food/water planning is absent from the main navigation; mobile has no section navigation.                        | New capability is easy to miss and requires a long scroll past setup.                     | Add a preparation link on desktop and compact sticky setup/ride/food/comparison shortcuts on small screens. Preserve native anchor navigation and keyboard focus. |
| Upload, hide plan, build plan and add water all use the same dark fill.                                          | Routine actions compete with the next useful step.                                        | Explicit primary, secondary and quiet action styles. Warm primary actions; blue water actions; subdued reset/remove/hide controls.                                |
| Save briefing is small and loses its visible label on phones; there is no export action after building the plan. | The main takeaway is hard to discover when it is most useful.                             | Keep labeled, touch-sized export controls and add a plan-inclusive download at the end of planning.                                                               |
| Nearly all surfaces and chart modes are green.                                                                   | Content types and chart modes look interchangeable.                                       | Neutral paper/ink foundation, green elevation, amber work/food, blue water. Retain labels, units, shapes and selected-state indicators so color is supplementary. |
| Save-setup preference precedes route and rider inputs; automatic recalculation is implicit.                      | First-time visitors see housekeeping before the task and may look for a calculate button. | Move the opt-in after setup fields and explain automatic updates near the setup heading.                                                                          |
| Disclosure plus signs remain unchanged when open; some controls have small targets and weak hover feedback.      | Controls do not consistently communicate state or affordance.                             | State-aware chevrons, visible focus/hover, larger input/button/slider targets and unchanged reduced-motion behavior.                                              |

## Verification plan

Keep the simulation, sources, storage contract and plan arithmetic unchanged. Check keyboard navigation and anchor focus, unavailable-result shortcuts, plan export, both languages, 320/390 px phones and desktop layouts. Run existing numerical/browser checks, accessibility checks and the production build. Inspect screenshots and the live app, then deploy only the separate preview and leave production for owner approval.

## Local results

- All 156 unit checks, strict TypeScript and the production build pass. All 68 desktop/mobile browser cases pass without retries (35.9 s), including six new cases for keyboard/anchor focus, unavailable results, plan export, invalid plans and responsive navigation.
- Both languages pass automated accessibility checks in the exercised states, including 320 px width. New primary/secondary actions, inputs and the chart slider have at least 44 px target height. The plan download stays unavailable for invalid plan inputs; the existing general briefing download still explains unavailable planning.
- Inspected desktop, 390 px phone and 320 px screenshots. Narrow metric labels and navigation icons retain alignment when text wraps. The local Czech navigation → build plan → timing chart flow was also checked manually.
- No new dependencies or external requests. The simulation worker remains `worker-Dx0otFHa.js`; the palette does not change equations, quantities, persistence or source assumptions.

## Hosted preview

All 68 browser cases pass on the separate preview without retries (46.9 s). All five public asset files match the tested build, and configured security headers are present. The live Czech preparation navigation, build-plan action and chart-timing shortcut were manually checked. Preview version `1cb9ff36-2a72-4861-bdee-f082751f7728` was deployed from `8a250f4` and is held in [draft PR #5](https://github.com/CIF84/cycling_sim/pull/5) for owner review. Production deployment history still shows the approved PR #4 version `e398b6db-22e8-489c-82c8-4127610d5c7a`.

## Review limits and next evidence

This review improves discoverability and interaction consistency; it does not establish that new riders understand every model assumption. Watch a few independent riders import a route, adjust power, inspect a climb, make a plan and download it. Pay particular attention to expenditure versus intake and whether manual refills are understood as known stops. Actual Safari/phone review remains useful beyond Chromium device emulation. No accounts, analytics or remote route storage were added for this work.

## Owner review: compact introduction · 25 November 2026

The owner found that the desktop headline and decorative landscape displaced useful ride information. Remove the landscape entirely, preserve “Every route has a story” as the introductory text, use a smaller headline without a forced line break and move the demo action beside the copy on desktop. Tighten header/intro spacing while retaining readable controls and the existing app layout. Check both languages on desktop and phones, then update only PR #5 and preview.

Implemented the compact introduction in both languages. The landscape and its unused styles are removed; “Každá trasa má svůj příběh” remains above the Czech headline. The headline is 28 px on desktop and 26 px on phones, with natural wrapping. The demo action sits beside the copy on desktop and below it on phones. Controls and ride content retain their existing sizes.

All 156 unit checks, strict TypeScript and the production build pass. All 68 local desktop/mobile browser cases pass without retries (34.0 s). Inspected the live Czech desktop and desktop/phone screenshots: the 1440 × 1000 overview now includes the elevation graph and its slider. This is a presentation-only change; the simulation worker bundle remains unchanged.
