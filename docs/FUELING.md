# Local fuel and water plan

Published with owner approval through [PR #4](https://github.com/CIF84/cycling_sim/pull/4) on 20 November 2026. It supports planning for adults' recreational endurance rides, not medical nutrition treatment or an individually validated intake prescription. The plan is optional; opening it adds controls and chart markers without changing the ride simulation. No food catalog or grocery list is used.

## Three different quantities

- **Pedal work (kJ)** is actual modeled crank power multiplied by moving time. It remains the Energy chart's vertical axis.
- **Estimated expenditure (kcal)** retains the existing illustrative 18–25% gross-efficiency conversion, `work_kJ / (4.184 × efficiency)`. It describes pedaling only, omitting resting/coasting metabolism. It is especially uncertain at very low power and is not an intake target.
- **Planned carbohydrate intake (g and kcal)** is a separately chosen rate times moving hours, with an approximate food-energy equivalent of 4 kcal/g. This is ingested carbohydrate energy, not a prediction of absorption, oxidation or glycogen. Include carbohydrates in both food and drinks once; no energy-deficit or glycogen-depletion curve is inferred.

The whole-ride totals and cursor readouts keep these units and labels separate. Planned intake is not obtained by replacing estimated expenditure. Gearing does not change totals; power affects duration and therefore planned quantities, while a manual carbohydrate rate stays fixed.

## Evidence and practical choices

Sources checked 19 November 2026:

- [Australian Institute of Sport: sports drinks, use and carbohydrate guidelines](https://www.ausport.gov.au/ais/nutrition/supplements/group_a/sports-foods2/sports-drink/how-and-when-do-i-use-it): endurance guidance of 30–60 g/h for 1–2.5 h and up to 90 g/h for longer events; shorter high-intensity activity can benefit from smaller amounts. Higher intakes require appropriate carbohydrate mixtures and practiced tolerance. Duration alone does not establish personal need.
- [NATA position statement: Fluid Replacement for the Physically Active (2017)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5634236/): individual fluid planning, variation in sweat/fluid needs and the risks of excessive as well as inadequate drinking. The app does not estimate sweat from temperature, mass or mechanical work.
- [FDA carbohydrate information](https://www.accessdata.fda.gov/scripts/InteractiveNutritionFactsLabel/assets/InteractiveNFL_TotalCarbohydrate_October2021.pdf): conventional energy equivalent of 4 kcal/g for carbohydrate. The planner concerns digestible ride fuel, not total food energy or fibre/sugar-alcohol accounting.

**App choices, not validated physiological rules:** Auto starts at 0 g/h below one hour, 45 g/h at 1–2.5 h, and 60 g/h above 2.5 h. It does not prescribe fuel for a fully coasting model (zero pedaling time). Users can choose 0/30/45/60/75/90 g/h explicitly; above 60 g/h displays a practiced-strategy explanation. Zero planned intake or zero crank work must not be interpreted as zero body energy use. The automatic plan does not infer intensity from FTP or judge gut tolerance.

Food is spread across **20-minute windows** from the start, with a proportional final partial window. Markers lie at window midpoints, not exact eating deadlines. Window quantities sum to the whole-ride total before display rounding. Intake at the cursor is the linear hourly target by that moving time; it is not a record of meals eaten. Timing should be adapted to safe, comfortable opportunities. These windows are a practical reminder format, not an absorption model.

The model holds pedaling power constant. Climbing increases time and work per kilometre, not prescribed power per second. The selected climb therefore shows work per kilometre and the cumulative carbohydrate plan by its start, without an extra pre-climb dose or a claim about hunger peaks. Coasting reduces mechanical work; it does not remove elapsed time from a manually selected intake plan.

## Bottles and refill coverage

The example is two 750 ml bottles, an editable **500 ml/h planning rate**, and a 250 ml carried reserve. None is a personalized need estimate. Drinking rate accepts 100–2,000 ml/h as defensive software bounds, not a recommendation; bottle count must be a whole 1–6, size 100–2,000 ml, and reserve between zero and total capacity. These limits do not establish safety or suitability for any rider.

Each leg begins with full bottles, including at every manual water stop. For each leg:

```
planned fluid = chosen ml/h × modeled leg hours
remaining at next stop/finish = bottle capacity − planned fluid
reserve time = leg start time + (capacity − reserve) / chosen rate
empty time = leg start time + capacity / chosen rate
```

The app maps reserve and empty times back to distance using the actual section times. It flags any leg that consumes the chosen reserve and separately identifies a leg that exceeds capacity. A later refill cannot erase an earlier shortage. At a refill cursor, the bottles show the **post-refill** level; leg warnings still reflect the pre-refill journey. Refill amounts describe topping up, not extra capacity. Carrying a reserve is not an instruction to drink it all.

Stops are water-only, not food resupply points. Users add/remove them by distance or at the chart cursor. Maximum eight stops, strictly inside the route and at least 10 m apart. The app neither discovers nor verifies shops, drinking-water access, opening hours or safe stopping places. Track breaks omit connecting travel and trigger an additional planning warning. All totals/timing exclude stops, delays and unrecorded travel; extra supplies must account for those separately.

Bottle settings do not automatically alter rider/bike/kit mass. The user must include carried food/water in Kit & water. No dynamic reduction in mass as supplies are used is modeled.

## Architecture, lifecycle and limits

`src/model/fueling.ts` is a pure module; it consumes the existing validated route and simulation. Binary search maps time to route distance. It creates at most 72 food windows for a supported ride of up to 24 modeled moving hours, plus at most nine water legs. No simulation worker restart is needed to edit a plan or move the chart cursor. Plans beyond that duration are explicitly unavailable rather than silently truncated.

React state holds settings and stop distances in memory only. They are excluded from Remember my setup and all network requests. Refresh clears the plan; a new route, same-filename reimport, return to demo or smoothing change clears stops. Power/gearing edits preserve stop distance and recalculate arrival times/coverage. Changing language preserves state. Invalid planning inputs hide intake/coverage/markers while preserving the ride and emit an explicit unavailable-plan line in downloads.

The downloaded briefing includes expenditure, carbohydrate grams/kcal/rate, fluid totals, starting capacity, reserve, shortage warnings, refill locations/times, all food windows, assumptions and source URLs. No GPS coordinates are included. The route's existing warning messages remain in the briefing.

## Verification

Twenty independent model/format checks cover arithmetic, inverse time mapping, exact/partial intervals, reserve/empty boundaries, late-refill shortages, unsorted stops, invariance to crank work and gearing with fixed duration/manual intake, coasting defaults, validation and translated exports. Browser coverage exercises controls, plot/readout links, stops, downloads, new/same-name routes, smoothing, power edits, local-only operation, non-persistence, zero-work rides, both languages, accessibility and narrow layouts. See [VERIFICATION.md](VERIFICATION.md) for the final release results.
