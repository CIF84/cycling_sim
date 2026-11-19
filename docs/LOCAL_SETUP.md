# Remember my setup

Published to production on 19 November 2026 after owner approval and the merge of [PR #2](https://github.com/CIF84/cycling_sim/pull/2).

## Behavior

- Off by default. Enabling saves current valid preferences and subsequent valid changes automatically.
- On the next visit, restore saved preferences before the first simulation. The demo route and default wind (0 km/h), temperature (20 °C) and air-density altitude (200 m) are used. The interface reminds riders to review power and conditions.
- Turning off removes only the setup record and stops future saves; current inputs, imported route and language stay intact. A removal event also disables saving in other open tabs so they cannot recreate a forgotten setup on the next edit.
- Reset ride inputs resets the current values and, while remembering is enabled, replaces the saved setup with defaults. Return to demo only clears the imported route.
- Invalid edits do not replace the last valid record. Unreadable data or an unsupported schema version is ignored and explained, without silently claiming a successful restore. Enabling the option replaces it with valid current settings.
- Storage access, quota and deletion errors are handled. Turning off stops future writes even if deletion fails, displays an honest warning that the prior setup may return next visit, and provides a retry action. The ride calculator remains usable.
- Different tabs retain their in-progress input values. When saving is enabled in multiple tabs, the last valid edit wins. Forgetting is propagated, but edits do not unexpectedly replace inputs in another open tab.

## Storage contract

`src/settings/savedSetup.ts` uses a single versioned localStorage key, `bike-science-setup`. The language key, `bike-science-language`, remains independent. No account, cookie, server API, telemetry, network storage or dependency was added.

Schema version 1 contains `groupsetId` and an explicit allowlist of inputs:

- `riderKg`, `bikeKg`, `kitKg`, `powerW`
- `cda`, `crr`, `efficiency`, `speedLimitKmh`, `coastDescents`
- `chainrings`, `cogs`, `wheelM`, `cadenceRpm`

All numbers and tooth lists use the existing model bounds, plus strict type checks. Arrays are copied. Preset IDs are checked against the current catalog and actual saved tooth counts; missing/retired/mismatched presets display Custom while preserving valid gears. New incompatible schemas must add an explicit migration or retain the current explained fallback.

There is deliberately no storage of GPX text, coordinates, names, route segments, results, chart state, smoothing, wind, temperature or altitude. Unknown fields are never copied to live inputs or written back. The persisted record is not a simulation cache.

localStorage belongs to the browser profile and origin. The separate preview Worker cannot read production preferences and vice versa. Browser clearing, private-session behavior, or storage eviction can remove preferences; this is convenience storage, not a backup or cross-device sync service.

## Review

1. Change weights, watts and gearing with remembering off. Reload: defaults return.
2. Enable remembering and set different weights, watts, a groupset or custom tooth lists. Reload: these return and the control remains enabled.
3. Import the synthetic GPX and change wind/temperature/altitude. Reload: demo and default conditions return; preferences still restore.
4. Leave a numeric value empty or enter invalid gearing. Reload: the last valid saved setup returns.
5. Turn remembering off. Current values stay, but reload returns defaults. Language survives.
6. Repeat in English and Czech, at desktop and phone widths. Preview and production preferences should remain separate.

Automated unit checks cover the storage boundary, validation, all catalog presets, custom gear lists, invalid/future records, failure handling and isolated removal. Browser checks cover opt-in, reload, update/reset, GPX/condition exclusion, invalid edits, two-tab forgetting, translated accessible controls, blocked storage and narrow layouts. No physics equations changed.
