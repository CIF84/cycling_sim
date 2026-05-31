import pandas as pd

from simulator import simulate_route
from reporting import summarize_ride


def evaluate_configuration(
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

    return summary


def build_roi_table(
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
):
    baseline = evaluate_configuration(
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
        bottle_sizes_ml=bottle_sizes_ml,
    )

    baseline_duration = baseline["duration_h"]

    current_power_w = rider_mass_kg * fitness_wkg

    tests = [
        {
            "name": "+10 W",
            "rider_mass_kg": rider_mass_kg,
            "bike_mass_kg": bike_mass_kg,
            "fitness_wkg": (current_power_w + 10) / rider_mass_kg,
            "cda": cda,
            "crr": crr,
        },
        {
            "name": "+20 W",
            "rider_mass_kg": rider_mass_kg,
            "bike_mass_kg": bike_mass_kg,
            "fitness_wkg": (current_power_w + 20) / rider_mass_kg,
            "cda": cda,
            "crr": crr,
        },
        {
            "name": "-1 kg rider",
            "rider_mass_kg": rider_mass_kg - 1,
            "bike_mass_kg": bike_mass_kg,
            "fitness_wkg": current_power_w / (rider_mass_kg - 1),
            "cda": cda,
            "crr": crr,
        },
        {
            "name": "-5 kg rider",
            "rider_mass_kg": rider_mass_kg - 5,
            "bike_mass_kg": bike_mass_kg,
            "fitness_wkg": current_power_w / (rider_mass_kg - 5),
            "cda": cda,
            "crr": crr,
        },
        {
            "name": "-1 kg bike",
            "rider_mass_kg": rider_mass_kg,
            "bike_mass_kg": bike_mass_kg - 1,
            "fitness_wkg": fitness_wkg,
            "cda": cda,
            "crr": crr,
        },
        {
            "name": "10% aero gain",
            "rider_mass_kg": rider_mass_kg,
            "bike_mass_kg": bike_mass_kg,
            "fitness_wkg": fitness_wkg,
            "cda": cda * 0.90,
            "crr": crr,
        },
        {
            "name": "Fast tires",
            "rider_mass_kg": rider_mass_kg,
            "bike_mass_kg": bike_mass_kg,
            "fitness_wkg": fitness_wkg,
            "cda": cda,
            "crr": crr * 0.85,
        },
    ]

    rows = []

    for test in tests:
        result = evaluate_configuration(
            segments_df=segments_df,
            rider_mass_kg=test["rider_mass_kg"],
            bike_mass_kg=test["bike_mass_kg"],
            fitness_wkg=test["fitness_wkg"],
            temp_c=temp_c,
            humidity_pct=humidity_pct,
            wind_kmh=wind_kmh,
            wind_mode=wind_mode,
            chainring_teeth=chainring_teeth,
            cassette_teeth=cassette_teeth,
            cda=test["cda"],
            crr=test["crr"],
            bottle_sizes_ml=bottle_sizes_ml,
        )

        saved_minutes = (
            baseline_duration - result["duration_h"]
        ) * 60

        rows.append(
            {
                "change": test["name"],
                "time_saved_min": round(saved_minutes, 2),
                "new_duration_h": round(
                    result["duration_h"],
                    2,
                ),
            }
        )

    df = pd.DataFrame(rows)

    df = df.sort_values(
        by="time_saved_min",
        ascending=False,
    )

    return df