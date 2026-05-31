import pandas as pd

from simulator import simulate_route
from reporting import summarize_ride


def run_scenario(
    segments_df,
    rider_mass_kg,
    bike_mass_kg,
    fitness_wkg,
    temp_c,
    humidity_pct,
    wind_kmh,
    wind_mode,
    chainring_teeth,
    cassette_teeth,
    cda,
    crr,
    bottle_sizes_ml,
    scenario_name,
):
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
        crr=crr,
    )

    summary = summarize_ride(
        sim_df=sim,
        rider_mass_kg=rider_mass_kg,
        bottle_sizes_ml=bottle_sizes_ml,
    )

    return {
        "scenario": scenario_name,
        "rider_mass_kg": rider_mass_kg,
        "fitness_wkg": fitness_wkg,
        "avg_speed_kmh": summary["avg_speed_kmh"],
        "duration_h": summary["duration_h"],
        "energy_kcal": summary["energy_kcal"],
    }


def compare_scenarios(
    segments_df,
    scenarios,
    bike_mass_kg,
    temp_c,
    humidity_pct,
    wind_kmh,
    wind_mode,
    chainring_teeth,
    cassette_teeth,
    cda,
    crr,
    bottle_sizes_ml,
):
    rows = []

    for s in scenarios:
        rows.append(
            run_scenario(
                segments_df=segments_df,
                rider_mass_kg=s["rider_mass_kg"],
                fitness_wkg=s["fitness_wkg"],
                bike_mass_kg=bike_mass_kg,
                temp_c=temp_c,
                humidity_pct=humidity_pct,
                wind_kmh=wind_kmh,
                wind_mode=wind_mode,
                chainring_teeth=chainring_teeth,
                cassette_teeth=cassette_teeth,
                cda=cda,
                crr=crr,
                bottle_sizes_ml=bottle_sizes_ml,
                scenario_name=s["name"],
            )
        )

    df = pd.DataFrame(rows)

    baseline = df.iloc[0]["duration_h"]

    df["time_delta_min"] = (
        (df["duration_h"] - baseline) * 60
    ).round(1)

    return df