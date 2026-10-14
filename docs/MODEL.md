# Model v0.1 · assumptions and evidence

## What is verified

The force-balance framework is supported by published cycling models. Numerical tests check our equations and solver independently of historical outputs. **This particular app has not been validated against outdoor rides.** A model framework’s experimental validation does not transfer automatically to this implementation, its defaults or GPX forecasts.

For speed `v` in m/s, crank power `P` in W, total mass `m` in kg, grade `q = rise / horizontal distance`, and `theta = atan(q)`:

```
Fgravity = m × 9.80665 × sin(theta)
Frolling = Crr × m × 9.80665 × cos(theta)
u = v + wind_kmh / 3.6  (+ headwind, − tailwind)
Faero = 0.5 × rho × CdA × u × abs(u)
P × drivetrain_efficiency = v × (Fgravity + Frolling + Faero)
```

For positive power, bracket the positive equilibrium from 0 to 16 m/s, expanding to at most 128 m/s. Bisection stops below 1e−8 m/s bracket width or after 80 iterations. At zero power, solve **net force = 0** on descents or assisting wind; if net force at rest opposes forward travel, return zero. This avoids the spurious `v=0` root of zero-power balance. No minimum force or invented crawling speed is applied. An immobile section fails the route estimate with an actionable message.

The resistance force is increasing with forward speed. For positive power, the physically relevant equilibrium lies on the positive-force branch, where resisting power increases monotonically. For coasting, the unique force crossing determines terminal speed. This permits bisection even when resisting power is negative below terminal speed.

Inputs must be finite and within documented UI bounds. Grades beyond ±40% are rejected. These are defensive beta limits, not cycling feasibility thresholds. Wheel speed is along the slope; grade uses horizontal distance and moving time uses `hypot(horizontal, rise)`. Route average speed is total modeled distance / total moving time, not an arithmetic mean of section speeds.

At a speed ceiling we assume braking/reduced pedaling. Effective crank power is reduced to the nonnegative power needed at that speed (never greater than input power). If gravity/wind already propels the rider, effective crank power is zero. No cadence is reported while coasting. Mechanical energy sums **actual modeled crank power × section time**, excluding braking losses supplied by gravity.

## Sources and their scope

- [Martin, Milliken, Cobb, McFadden & Coggan (1998), Validation of a Mathematical Model for Road Cycling Power](https://pubmed.ncbi.nlm.nih.gov/28121252/): experimentally evaluated power-demand framework; includes effects omitted here, so its reported error is not this app’s accuracy.
- [Danek, Slawinski & Stanoev (2020), On modelling bicycle power-meter measurements](https://arxiv.org/abs/2005.04229), equation 2 and sign discussion on pp. 4–5: gravity, rolling resistance, drivetrain losses and correct signed tailwind drag. We set acceleration to zero and omit wheel rotational aerodynamic terms.
- [NASA Glenn, Drag Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/): dynamic pressure and drag area relation; drag direction opposes relative airflow.
- [NASA Glenn, Earth Atmosphere Model](https://www.grc.nasa.gov/www/k-12/airplane/atmosmet.html): standard-atmosphere/ideal-gas framework. We use `pressure = 101325 × (1 − 2.25577e−5 × altitude)^5.25588` Pa and `rho = pressure / [287.05 × (temperature + 273.15)]`. Pressure comes from a standard atmosphere, while temperature is entered independently. Dry air, constant altitude for the whole ride, no local pressure/humidity measurement. This is a practical density approximation.
- [Nickleberry & Brooks (1996)](https://pubmed.ncbi.nlm.nih.gov/8933490/) reports gross efficiency varying by workload/cadence, with lab values extending below the displayed illustrative range. The **18–25% range is a planning assumption**, not a personalized metabolic estimate or a confidence interval. The app converts crank kJ into kcal with `work_kJ / (4.184 × efficiency)`; resting/coasting metabolic costs are omitted. Do not infer carbohydrate oxidation, food intake, sweat or sodium replacement from mechanical work alone.
- [Shimano CS-R7000 manufacturer parts document](https://si.shimano.com/en/pdfs/ev/CS-R7000-4330/EV-CS-R7000-4330.pdf): actual 11–32, 11-speed teeth **11,12,13,14,16,18,20,22,25,28,32**.
- [SRAM XG-1270 manufacturer service specifications](https://www.sram.com/en/service/models/cs-xg-1270-e1): actual 10–36, 12-speed teeth **10,11,12,13,15,17,19,21,24,28,32,36**.

Sources checked 14 October 2026. No equipment purchase or personalized medical/nutrition recommendation is made.

## Practical approximations, not validated defaults

- 180 W, 75 kg rider, 10 kg bike and 3 kg kit are approachable demo values. **Sustainable power is not FTP.** User selects watts appropriate for expected duration. No fatigue, physiological threshold, training load or pacing optimization model exists.
- Power stays constant when pedaling; optionally coast at grade ≤−3%. This replaces the prototype’s unexplained 45/82/92/100/108% grade multipliers. The threshold and 50 km/h default ceiling are user-changeable modeling assumptions, not recommended descending speeds.
- Crr presets .004/.005/.008/.012 and CdA .30/.35/.45 are illustrative effective coefficients. Tire pressure, vibration, roughness, posture, clothing and rider size are not estimated separately. Very rough gravel is especially uncertain. Default drivetrain efficiency is 97%, constant under all loads.
- Constant signed along-route wind cannot represent a real loop under compass-direction wind. No crosswind, yaw, shelter, drafting or live weather. Temperature changes density only, not heat/fatigue effects.
- Nearest virtual gear to preferred cadence ignores shift behavior, cross-chaining, drivetrain compatibility and cadence-dependent power limitations. `cadence = v × 60 / (wheel circumference × front/rear)`. A below-60-rpm flag is an illustrative preparation prompt, not a clinical or physiological threshold. Gearing does not change ride time.
- The four comparisons alter **one input field** each. Weight lowers kit by 2 kg when possible, otherwise bike by 2 kg, while watts remain fixed. Scenarios that exceed allowed parameter limits are omitted rather than silently clamped. A scenario that cannot complete the route is marked unavailable with an explanation, preserving the valid baseline and other comparisons. Comparisons can yield negative savings: lower mass may slow a coasting descent; lower CdA may reduce strong-tailwind assistance enough to stop a coasting rider. No improvement is highlighted when all changes save at most half a second. Rankings are sensitivity examples, not expected upgrade benefits.
- No uncertainty band is invented. Rounded minutes, one decimal km/h and whole-meter climbing reflect approximate inputs. Small differences displayed as <1 minute should not drive equipment decisions.

## GPX processing

Use track points in separate `trkseg` sections; support `rtept` if no track sections exist. Waypoints alone are insufficient. Namespace prefixes are supported. XML with DTD/entities is refused; file size ≤10 MB, ≤100,000 input points, ≤100 sections and ≤1,500 km connected horizontal length. Processing occurs in a cancellable browser worker; no GPX data leaves the browser.

Coordinates must be finite and within geographic bounds; elevations within −500 to 9,000 m. Spherical haversine (Earth radius 6,371,000 m) determines horizontal intervals. Duplicate/near-duplicate locations below .05 m are removed (including any conflicting elevation at that duplicate). Jumps >2 km split tracks, and connecting distance is omitted with a warning. Intervals >250 m get a sparse-data warning. These cutoffs are practical heuristics, not automatic proof of bad data. Valid legitimate long intervals may be excluded; check the quality panel.

Partial missing elevations are interpolated by distance **inside the same section**, with nearest-known leading/trailing elevations held constant and a warning. A usable section with no elevations fails: we cannot assume it is flat. Single-point and sub-1 m sections cannot define terrain and are omitted. Route totals include only modeled sections.

Interpolate elevation on a 25 m horizontal grid, including the exact final point of every section. A centered median filter spans roughly the selected smoothing width (0/100/200 m); section endpoints are preserved. The odd-sized window shrinks symmetrically near each endpoint, avoiding one-sided median bias and artificial ramps at a short final interval. Segment differences preserve **horizontal distance and net endpoint elevation**. Accumulate ascent/descent from processed segment differences. Slope distance is slightly longer than GPS horizontal distance. Both are exposed; smoothing can change slope distance through elevation changes but does not change horizontal distance.

Profile inspection selects the segment containing the requested distance and interpolates elevation within that same segment. At a track break, the following section supplies both elevation and grade; no interpolation spans the missing connection. Separate sections follow the connected-span semantics in the [GPX 1.1 schema](https://www.topografix.com/GPX/1/1/#type_trksegType).

Recorded ascent is computed before resampling/smoothing, after duplicate/gap handling and missing-value interpolation. Raw recorded ascent and modeled ascent are reported separately. Resampling/smoothing can remove noise **and real short hills**; when reduction exceeds 30 m or 15% (whichever is larger), show a warning. “No detected issues” is a heuristic status, not a data accuracy certificate. No elevation lookup, GPS jitter correction, route snapping, timestamp processing or map matching is included.

## Intentional differences from the Python prototype

| Prototype behavior                                          | Beta behavior                                                            |
| ----------------------------------------------------------- | ------------------------------------------------------------------------ |
| Squared relative wind always resists travel                 | Signed drag allows wind assistance                                       |
| Force clamp and 0.1 m/s lower bound                         | Correct force equilibrium for coasting; stationary reported explicitly   |
| Approximate mg × grade and constant rolling load            | Exact sin/cos slope geometry                                             |
| No drivetrain losses                                        | Explicit crank-to-wheel efficiency                                       |
| Mass × W/kg and hidden grade pacing                         | Absolute sustainable crank power, optional descent coasting              |
| Track breaks connected; sparse chunks/last boundary dropped | Sections kept separate; every interval and remainder preserved           |
| Point-count moving mean                                     | Uniform distance grid and median smoothing, disclosed effect             |
| Ascent/distance interpreted as one uphill route             | Manual aggregate routes deferred; terrain distribution unknown           |
| Some cassette lists assembled from endpoints                | Actual manufacturer cog lists; custom counts validated                   |
| Weight scenarios also changed watts at fixed W/kg           | One variable changes; watts fixed for mass                               |
| Inverse silently converged to a power bound                 | Bounded target reachability checked; no public inverse UI                |
| Heat-derived sweat, fixed sodium/carbs/recovery goals       | Unsupported prescriptions excluded; only illustrative energy expenditure |

Reproduced by executing the legacy pure solver directly: 0 W/−5%/90 kg returned **0.36 km/h**. The new analytical equilibrium at density 1.225 kg/m³, CdA .35 m² and Crr .005 is approximately **49 km/h**, before a route speed ceiling. Agreement with legacy outputs is not a verification criterion. The old Python modules remain historical and retain their original limitations.
