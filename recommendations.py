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