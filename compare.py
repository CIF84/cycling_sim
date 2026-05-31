import pandas as pd

from presets import SURFACE_PRESETS, AERO_PRESETS
from simulator import simulate_route
from reporting import summarize_ride


def compare_surfaces(
    segments_df,
    rider_mass_kg,
    bike_mass_kg,
    fitness_wkg,
    temp_c=20,
    humidity_pct=50,
    wind_kmh=0,
    wind_mode="head",
    chainring_teeth=34,
    cassette_teeth=32,
    aero_key="endurance_road",
    bottle_sizes_ml=None,
):
    """
    Compare the same route across all surface presets.
    """

    rows = []

    cda = AERO_PRESETS[aero_key]["cda"]

    baseline_duration_h = None
    baseline_speed_kmh = None

    for surface_key, surface in SURFACE_PRESETS.items():
        sim = simulate_route(
            segments_df=segments_df,
            rider_mass_kg=rider_mass_kg,
            bike_mass_kg=bike_mass_kg,
            fitness_wkg=fitness_wkg,
            temp_c=temp_c,
            humidity_pct=humidity_pct,
            wind_kmh=wind_kmh,
            wind_mode=wind_mode,
            chainring_teeth=chainring_teeth,
            cassette_teeth=cassette_teeth,
            cda=cda,
            crr=surface["crr"],
        )

        summary = summarize_ride(
            sim_df=sim,
            rider_mass_kg=rider_mass_kg,
            bottle_sizes_ml=bottle_sizes_ml,
        )

        if surface_key == "smooth_road":
            baseline_duration_h = summary["duration_h"]
            baseline_speed_kmh = summary["avg_speed_kmh"]

        rows.append(
            {
                "surface": surface["label"],
                "crr": surface["crr"],
                "duration_h": summary["duration_h"],
                "avg_speed_kmh": summary["avg_speed_kmh"],
                "energy_kcal": summary["energy_kcal"],
                "carbs_g": summary["carbs_g"],
                "fluid_goal_l": summary["fluid_goal_l"],
            }
        )

    df = pd.DataFrame(rows)

    if baseline_duration_h is not None:
        df["time_delta_min_vs_smooth"] = (
            (df["duration_h"] - baseline_duration_h) * 60
        ).round(1)

    if baseline_speed_kmh is not None:
        df["speed_delta_kmh_vs_smooth"] = (
            df["avg_speed_kmh"] - baseline_speed_kmh
        ).round(1)

    return df


def compare_aero_positions(
    segments_df,
    rider_mass_kg,
    bike_mass_kg,
    fitness_wkg,
    temp_c=20,
    humidity_pct=50,
    wind_kmh=0,
    wind_mode="head",
    chainring_teeth=34,
    cassette_teeth=32,
    surface_key="normal_road",
    bottle_sizes_ml=None,
):
    """
    Compare the same route across all aero presets.
    """

    rows = []

    crr = SURFACE_PRESETS[surface_key]["crr"]

    baseline_duration_h = None
    baseline_speed_kmh = None

    for aero_key, aero in AERO_PRESETS.items():
        sim = simulate_route(
            segments_df=segments_df,
            rider_mass_kg=rider_mass_kg,
            bike_mass_kg=bike_mass_kg,
            fitness_wkg=fitness_wkg,
            temp_c=temp_c,
            humidity_pct=humidity_pct,
            wind_kmh=wind_kmh,
            wind_mode=wind_mode,
            chainring_teeth=chainring_teeth,
            cassette_teeth=cassette_teeth,
            cda=aero["cda"],
            crr=crr,
        )

        summary = summarize_ride(
            sim_df=sim,
            rider_mass_kg=rider_mass_kg,
            bottle_sizes_ml=bottle_sizes_ml,
        )

        if aero_key == "endurance_road":
            baseline_duration_h = summary["duration_h"]
            baseline_speed_kmh = summary["avg_speed_kmh"]

        rows.append(
            {
                "aero_position": aero["label"],
                "cda": aero["cda"],
                "duration_h": summary["duration_h"],
                "avg_speed_kmh": summary["avg_speed_kmh"],
                "energy_kcal": summary["energy_kcal"],
                "carbs_g": summary["carbs_g"],
                "fluid_goal_l": summary["fluid_goal_l"],
            }
        )

    df = pd.DataFrame(rows)

    if baseline_duration_h is not None:
        df["time_delta_min_vs_endurance"] = (
            (df["duration_h"] - baseline_duration_h) * 60
        ).round(1)

    if baseline_speed_kmh is not None:
        df["speed_delta_kmh_vs_endurance"] = (
            df["avg_speed_kmh"] - baseline_speed_kmh
        ).round(1)

    return df