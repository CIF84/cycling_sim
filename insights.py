import pandas as pd


def generate_insights(
    ride_summary,
    roi_table,
    gear_usage,
):
    insights = []

    best_roi = roi_table.sort_values(
        "time_saved_min",
        ascending=False,
    ).iloc[0]

    insights.append(
        f"✓ Biggest performance gain: "
        f"{best_roi['change']} "
        f"({best_roi['time_saved_min']:.1f} min saved)"
    )

    aero_row = roi_table[
        roi_table["change"] == "10% aero gain"
    ]

    weight_row = roi_table[
        roi_table["change"] == "-5 kg rider"
    ]

    if not aero_row.empty and not weight_row.empty:
        aero_gain = aero_row.iloc[0]["time_saved_min"]
        weight_gain = weight_row.iloc[0]["time_saved_min"]

        if aero_gain > weight_gain:
            insights.append(
                f"✓ Aero beats weight "
                f"({aero_gain:.1f} vs {weight_gain:.1f} min)"
            )

    biggest_cog = gear_usage["selected_cog_teeth"].max()

    biggest_cog_row = gear_usage[
        gear_usage["selected_cog_teeth"] == biggest_cog
    ].iloc[0]

    if biggest_cog_row["pct_of_route"] < 5:
        insights.append(
            f"✓ Largest cog ({biggest_cog}T) "
            f"used only "
            f"{biggest_cog_row['pct_of_route']:.1f}% "
            f"of route"
        )
    else:
        insights.append(
            f"⚠ Largest cog ({biggest_cog}T) used "
            f"{biggest_cog_row['pct_of_route']:.1f}% of route"
        )

    carbs = ride_summary["carbs_g"]

    if carbs > 300:
        insights.append(
            f"⚠ High fueling demand ({carbs:.0f} g carbs)"
        )
    else:
        insights.append(
            f"✓ Manageable fueling demand ({carbs:.0f} g carbs)"
        )

    sweat = ride_summary["sweat_l"]

    if sweat > 3:
        insights.append(
            f"⚠ High sweat loss ({sweat:.1f} L)"
        )
    else:
        insights.append(
            f"✓ Moderate sweat loss ({sweat:.1f} L)"
        )

    return pd.DataFrame(
        {"insight": insights}
    )