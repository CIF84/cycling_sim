import math
import pandas as pd

from biology import estimate_fluid_goal_l, estimate_recovery_meal


def summarize_ride(
    sim_df,
    rider_mass_kg,
    bottle_sizes_ml=None,
):
    """
    Summarize a simulated ride into practical headline metrics.
    """

    if sim_df.empty:
        raise ValueError("sim_df is empty.")

    bottle_sizes_ml = bottle_sizes_ml or []
    bottle_capacity_ml = sum(bottle_sizes_ml)

    total_distance_km = sim_df["cum_dist_km"].iloc[-1]
    total_time_h = sim_df["cum_time_h"].iloc[-1]

    total_kcal = sim_df["cum_kcal"].iloc[-1]
    total_carbs_g = sim_df["cum_carbs_g"].iloc[-1]
    total_sweat_l = sim_df["cum_sweat_l"].iloc[-1]
    total_sodium_mg = sim_df["cum_sodium_mg"].iloc[-1]

    fluid_goal_l = estimate_fluid_goal_l(
        sweat_l=total_sweat_l,
        rider_mass_kg=rider_mass_kg,
    )

    refill_stops = 0
    if bottle_capacity_ml > 0 and fluid_goal_l * 1000 > bottle_capacity_ml:
        refill_stops = math.ceil(
            (fluid_goal_l * 1000 - bottle_capacity_ml) / 750
        )

    recovery = estimate_recovery_meal(rider_mass_kg)

    return {
        "distance_km": round(total_distance_km, 2),
        "duration_h": round(total_time_h, 2),
        "avg_speed_kmh": round(total_distance_km / total_time_h, 1),
        "energy_kcal": round(total_kcal),
        "carbs_g": round(total_carbs_g),
        "sweat_l": round(total_sweat_l, 2),
        "fluid_goal_l": round(fluid_goal_l, 2),
        "sodium_mg": round(total_sodium_mg),
        "bottle_capacity_ml": bottle_capacity_ml,
        "refill_stops": refill_stops,
        "low_cadence_segments": int(sim_df["low_cadence_flag"].sum()),
        "recovery_carbs_g": round(recovery["carbs_g"]),
        "recovery_protein_g": round(recovery["protein_g"]),
    }


def print_ride_summary(summary):
    """
    Print a readable command-line ride summary.
    """

    print("=" * 60)
    print("BIKE SCIENCE PRO — RIDE SUMMARY")
    print("=" * 60)
    print(f"Distance:             {summary['distance_km']} km")
    print(f"Duration:             {summary['duration_h']} h")
    print(f"Average speed:        {summary['avg_speed_kmh']} km/h")
    print(f"Energy burned:        {summary['energy_kcal']} kcal")
    print(f"Carbohydrate need:    {summary['carbs_g']} g")
    print(f"Sweat loss:           {summary['sweat_l']} L")
    print(f"Fluid goal:           {summary['fluid_goal_l']} L")
    print(f"Sodium replacement:   {summary['sodium_mg']} mg")
    print(f"Bottle capacity:      {summary['bottle_capacity_ml']} ml")
    print(f"Refill stops:         {summary['refill_stops']}")
    print(f"Low cadence segments: {summary['low_cadence_segments']}")
    print(
        "Recovery meal:        "
        f"{summary['recovery_carbs_g']} g carbs | "
        f"{summary['recovery_protein_g']} g protein"
    )
    print("=" * 60)


def build_fueling_plan(
    sim_df,
    block_minutes=20,
):
    """
    Convert cumulative simulation needs into practical intake blocks.
    """

    if sim_df.empty:
        raise ValueError("sim_df is empty.")

    total_time_min = sim_df["cum_time_h"].iloc[-1] * 60

    checkpoints = range(
        block_minutes,
        int(total_time_min) + block_minutes,
        block_minutes,
    )

    rows = []

    prev_carbs = 0.0
    prev_sweat = 0.0
    prev_sodium = 0.0

    for checkpoint_min in checkpoints:
        subset = sim_df[
            sim_df["cum_time_h"] * 60 <= checkpoint_min
        ]

        if subset.empty:
            continue

        carbs = subset["cum_carbs_g"].iloc[-1]
        sweat = subset["cum_sweat_l"].iloc[-1]
        sodium = subset["cum_sodium_mg"].iloc[-1]

        block_carbs = carbs - prev_carbs
        block_fluid_ml = (sweat - prev_sweat) * 1000
        block_sodium = sodium - prev_sodium

        rows.append(
            {
                "time_min": checkpoint_min,
                "cum_carbs_g": round(carbs, 1),
                "cum_fluid_need_l": round(sweat, 2),
                "cum_sodium_mg": round(sodium),
                "suggested_carbs_g": round(block_carbs),
                "suggested_fluid_ml": round(block_fluid_ml, -1),
                "suggested_sodium_mg": round(block_sodium, -1),
            }
        )

        prev_carbs = carbs
        prev_sweat = sweat
        prev_sodium = sodium

    return pd.DataFrame(rows) 