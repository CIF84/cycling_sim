import pandas as pd

from simulator import simulate_route


CASSETTE_PRESETS = {
    "10-32 road": [10, 11, 12, 13, 14, 16, 18, 20, 22, 25, 28, 32],
    "10-36 all-road": [10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 36],
    "10-45 gravel": [10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 42, 45],
    "10-52 MTB/gravel": [10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 42, 52],
}


def summarize_cassette_usage(sim_df):
    """
    Summarize cadence and gear usage for one simulated cassette.
    """

    hardest_cog = sim_df["selected_cog_teeth"].max()
    hardest_cog_segments = int(
        (sim_df["selected_cog_teeth"] == hardest_cog).sum()
    )

    return {
        "avg_cadence_rpm": round(sim_df["cadence_rpm"].mean(), 1),
        "min_cadence_rpm": round(sim_df["cadence_rpm"].min(), 1),
        "low_cadence_segments": int(sim_df["low_cadence_flag"].sum()),
        "hardest_cog": hardest_cog,
        "hardest_cog_segments": hardest_cog_segments,
        "hardest_cog_pct": round(
            hardest_cog_segments / len(sim_df) * 100,
            1,
        ),
    }


def compare_cassettes(
    segments_df,
    rider_mass_kg,
    bike_mass_kg,
    fitness_wkg,
    temp_c,
    humidity_pct,
    wind_kmh,
    wind_mode,
    chainring_teeth,
    cda,
    crr,
):
    """
    Compare multiple cassette presets on the same route.

    This does not change speed/time because gearing does not yet constrain power.
    It evaluates cadence realism and gear sufficiency.
    """

    rows = []

    for cassette_name, cassette_options in CASSETTE_PRESETS.items():
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
            cassette_teeth=max(cassette_options),
            cassette_teeth_options=cassette_options,
            cda=cda,
            crr=crr,
        )

        summary = summarize_cassette_usage(sim)

        rows.append(
            {
                "cassette": cassette_name,
                "range": f"{min(cassette_options)}-{max(cassette_options)}",
                **summary,
            }
        )

    return pd.DataFrame(rows)