import {
  formatElapsedTime,
  formatNumber,
  translate,
  type Locale,
} from "./format";
import type { FuelPlan } from "../model/fueling";
import type { Ride } from "../model/types";

export function fuelBrief(
  locale: Locale,
  ride: Ride,
  plan: FuelPlan | null,
  enabled: boolean,
) {
  if (!enabled) return [];
  const t = (
    key: Parameters<typeof translate>[1],
    values?: Parameters<typeof translate>[2],
  ) => translate(locale, key, values);
  const n = (value: number, digits = 0) => formatNumber(locale, value, digits);
  const time = (seconds: number) => formatElapsedTime(locale, seconds);
  if (!plan)
    return [
      t("Fuel & water plan"),
      t("Plan inputs are invalid; no intake or bottle coverage is exported."),
    ];
  return [
    t("Fuel & water plan"),
    `${t("Estimated expenditure")}: ${n(Math.round(ride.kcalLow / 50) * 50)}–${n(Math.round(ride.kcalHigh / 50) * 50)} kcal · ${t("During pedaling · 18–25% efficiency")}`,
    `${t("Planned carbohydrate intake")}: ${n(plan.carbsG)} g (≈ ${n(Math.round(plan.intakeKcal / 10) * 10)} kcal) · ${n(plan.carbGph)} g/h`,
    t(
      "Intake supports the ride; it does not replace every calorie spent. Carbohydrates include food and drinks. This is a plan, not a measurement of your needs or remaining body energy.",
    ),
    `${t("Planned fluid")}: ${n(plan.fluidMl / 1000, 1)} l · ${n(plan.drinkMlph)} ml/h`,
    t("Start with {litres} l in your bottles", {
      litres: n(plan.capacityMl / 1000, 1),
    }),
    `${t("Water reserve")}: ${n(plan.reserveMl)} ml`,
    t(
      "Starts full; each marked stop refills all bottles. Coverage follows your chosen rate, not predicted thirst. Carrying more does not mean drinking it all.",
    ),
    ...plan.legs
      .filter((l) => l.reserveAtM !== null)
      .map(
        (l) =>
          t("Reserve reached near {distance} km", {
            distance: n(l.reserveAtM! / 1000, 1),
          }) +
          " · " +
          (l.emptyAtM !== null
            ? t(
                "Bottles run out near {distance} km, before the next refill or finish.",
                { distance: n(l.emptyAtM / 1000, 1) },
              )
            : t(
                "This leg uses part of your reserve. Refill earlier or carry more.",
              )),
      ),
    ...(plan.stops.length
      ? plan.stops.map(
          (s, i) =>
            `${t("Refill {number}", { number: i + 1 })}: ${n(s.distanceM / 1000, 1)} km · ${time(s.timeS)} · ${t("Top up about {litres} l", { litres: n(plan.legs[i].refillMl / 1000, 1) })}`,
        )
      : [t("No refills planned. Bring enough for the whole modeled ride.")]),
    t(
      "Add a known water stop by distance or at the chart cursor. Check access yourself. These are water refills, not food resupply points.",
    ),
    ...(plan.windows.length
      ? [
          t("Fuel timing along the route"),
          t(
            "Spread intake through each 20-minute window, starting early. Markers sit at window midpoints, not exact eating deadlines. Include carbs in drinks; choose safe, comfortable moments.",
          ),
          ...plan.windows.map(
            (w) =>
              `${time(w.startS)}–${time(w.endS)}: ≈ ${n(w.carbsG)} g · ~${n(w.distanceM / 1000, 1)} km`,
          ),
        ]
      : [
          t(
            "No carbohydrate intake is planned. Short easy rides may not need an on-bike fuel schedule; longer or harder rides can. Zero modeled work does not mean zero body energy use.",
          ),
        ]),
    t(
      "AIS guidance for endurance exercise: 30–60 g/h over 1–2.5 h; up to 90 g/h for longer events with a practiced strategy. Shorter rides depend on intensity and prior eating. Our starting rates and 20-minute windows are planning choices.",
    ),
    t(
      "Fluid needs vary with the rider and conditions. This planner does not calculate sweat, sodium needs, absorption or glycogen. Expenditure omits coasting and resting metabolism. Plan extra for stops, delays and missing route sections.",
    ),
    t(
      "Plan quantities do not change bike mass automatically. Include carried water and food in Kit & water. Plans and stops stay in memory and clear on refresh; route changes clear stops.",
    ),
    "AIS: https://www.ausport.gov.au/ais/nutrition/supplements/group_a/sports-foods2/sports-drink/how-and-when-do-i-use-it",
    "NATA: https://pmc.ncbi.nlm.nih.gov/articles/PMC5634236/",
    "",
  ];
}
