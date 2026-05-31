import pandas as pd


def build_recommendations(
    ride_summary,
    roi_table,
    gear_usage,
    current_power_w,
    current_cda,
    current_crr,
):
    recommendations = []

    best_roi = roi_table.sort_values(
        "time_saved_min",
        ascending=False,
    ).iloc[0]

    recommendations.append(
        {
            "type": "success",
            "title": "🚀 Biggest time saver",
            "summary": (
                f"{best_roi['change']} is the strongest modeled improvement, "
                f"saving approximately {best_roi['time_saved_min']:.1f} minutes."
            ),
            "details": (
                f"Current sustained power estimate: {current_power_w:.0f} W\n\n"
                f"Modeled improvement: {best_roi['change']}\n\n"
                f"New estimated duration: {best_roi['new_duration_h']:.2f} h"
            ),
        }
    )

    aero_row = roi_table[roi_table["change"] == "10% aero gain"]
    weight_row = roi_table[roi_table["change"] == "-5 kg rider"]

    if not aero_row.empty and not weight_row.empty:
        aero_gain = aero_row.iloc[0]["time_saved_min"]
        weight_gain = weight_row.iloc[0]["time_saved_min"]

        if aero_gain > weight_gain:
            title = "💨 Aerodynamics matter more than weight loss"
            summary = (
                f"A 10% aero improvement saves about {aero_gain:.1f} minutes, "
                f"while losing 5 kg saves about {weight_gain:.1f} minutes."
            )
        else:
            title = "⚖️ Weight loss matters more than aero on this route"
            summary = (
                f"Losing 5 kg saves about {weight_gain:.1f} minutes, "
                f"while a 10% aero improvement saves about {aero_gain:.1f} minutes."
            )

        recommendations.append(
            {
                "type": "info",
                "title": title,
                "summary": summary,
                "details": (
                    f"Aero scenario: CdA {current_cda:.3f} → {current_cda * 0.90:.3f}\n\n"
                    f"Weight scenario: rider mass reduced by 5 kg\n\n"
                    f"This comparison is route-specific. Aero usually matters more on faster/flatter routes; "
                    f"weight usually matters more on steep climbing routes."
                ),
            }
        )

    biggest_cog = gear_usage["selected_cog_teeth"].max()
    biggest_cog_row = gear_usage[
        gear_usage["selected_cog_teeth"] == biggest_cog
    ].iloc[0]

    if biggest_cog_row["pct_of_route"] < 5:
        recommendations.append(
            {
                "type": "success",
                "title": "⚙️ Current gearing looks sufficient",
                "summary": (
                    f"Your largest modeled cog ({biggest_cog}T) was used only "
                    f"{biggest_cog_row['pct_of_route']:.1f}% of the route."
                ),
                "details": (
                    "This suggests the current cassette range is not a major limiter on this route.\n\n"
                    "A larger cassette may still help comfort or cadence on steeper routes, "
                    "but this GPX does not appear to require it."
                ),
            }
        )
    else:
        recommendations.append(
            {
                "type": "warning",
                "title": "⚙️ Gearing may be close to the limit",
                "summary": (
                    f"Your largest modeled cog ({biggest_cog}T) was used "
                    f"{biggest_cog_row['pct_of_route']:.1f}% of the route."
                ),
                "details": (
                    "Frequent use of the largest cog can indicate limited climbing range.\n\n"
                    "A wider cassette or smaller chainring could improve comfort and cadence."
                ),
            }
        )

    carbs = ride_summary["carbs_g"]

    if carbs > 300:
        recommendations.append(
            {
                "type": "warning",
                "title": "🍌 Fueling is important",
                "summary": (
                    f"This ride requires approximately {carbs:.0f} g of carbohydrates."
                ),
                "details": (
                    "For longer endurance rides, under-fueling can significantly reduce performance.\n\n"
                    "A practical target is often around 60–90 g/hour for many riders, "
                    "and up to 90–120 g/hour for well-trained riders using mixed carb sources."
                ),
            }
        )

    sweat = ride_summary["sweat_l"]
    fluid_goal = ride_summary["fluid_goal_l"]

    if sweat > 3:
        recommendations.append(
            {
                "type": "warning",
                "title": "💧 Hydration needs planning",
                "summary": (
                    f"Estimated sweat loss is {sweat:.1f} L. "
                    f"Recommended fluid goal is about {fluid_goal:.1f} L."
                ),
                "details": (
                    "The fluid goal allows some safe body-water loss rather than replacing all sweat.\n\n"
                    "Hotter weather, higher humidity, and lower airflow can increase hydration needs."
                ),
            }
        )

    return pd.DataFrame(recommendations)