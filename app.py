from gpx_utils import load_gpx, build_segments, build_manual_route
from simulator import simulate_route
from reporting import summarize_ride, print_ride_summary, build_fueling_plan


# ==========================================================
# USER CONFIG
# ==========================================================

USE_GPX = False

GPX_PATH = "sample_routes/my_ride.gpx"

RIDER_MASS_KG = 90
BIKE_MASS_KG = 9
FITNESS_WKG = 3.0

DISTANCE_KM = 80
ELEVATION_GAIN_M = 1200

TEMP_C = 24
HUMIDITY_PCT = 50

WIND_KMH = 5
WIND_MODE = "head"  # "head" or "tail"

CHAINRING_TEETH = 34
CASSETTE_TEETH = 32

BOTTLE_SIZES_ML = [750, 750]

SEGMENT_LENGTH_M = 1000
ELEVATION_SMOOTH_WINDOW = 7


# ==========================================================
# APP RUNNER
# ==========================================================

def main():
    if USE_GPX:
        print(f"Loading GPX file: {GPX_PATH}")

        gpx_df = load_gpx(GPX_PATH)

        segments = build_segments(
            gpx_df,
            segment_length_m=SEGMENT_LENGTH_M,
            elevation_smooth_window=ELEVATION_SMOOTH_WINDOW,
        )

    else:
        print("Using manual route mode")

        segments = build_manual_route(
            distance_km=DISTANCE_KM,
            elevation_gain_m=ELEVATION_GAIN_M,
            segment_length_m=SEGMENT_LENGTH_M,
        )

    sim = simulate_route(
        segments_df=segments,
        rider_mass_kg=RIDER_MASS_KG,
        bike_mass_kg=BIKE_MASS_KG,
        fitness_wkg=FITNESS_WKG,
        temp_c=TEMP_C,
        humidity_pct=HUMIDITY_PCT,
        wind_kmh=WIND_KMH,
        wind_mode=WIND_MODE,
        chainring_teeth=CHAINRING_TEETH,
        cassette_teeth=CASSETTE_TEETH,
    )

    summary = summarize_ride(
        sim_df=sim,
        rider_mass_kg=RIDER_MASS_KG,
        bottle_sizes_ml=BOTTLE_SIZES_ML,
    )

    print_ride_summary(summary)

    fueling_plan = build_fueling_plan(
        sim_df=sim,
        block_minutes=20,
    )

    print("\nFUELING / HYDRATION PLAN")
    print("=" * 60)

    if fueling_plan.empty:
        print("Ride is too short for the selected fueling block length.")
    else:
        print(fueling_plan.to_string(index=False))

    print("\nTOP 10 HARDEST SEGMENTS BY GRADE")
    print("=" * 60)

    hardest = (
        sim.sort_values("grade_pct", ascending=False)
        .head(10)
        [
            [
                "segment_id",
                "start_km",
                "end_km",
                "grade_pct",
                "speed_kmh",
                "target_power_w",
                "cadence_rpm",
            ]
        ]
    )

    print(hardest.round(1).to_string(index=False))

    print("\nLOW CADENCE SEGMENTS")
    print("=" * 60)

    low_cadence = sim[sim["low_cadence_flag"]]

    if low_cadence.empty:
        print("No low cadence segments detected.")
    else:
        print(
            low_cadence[
                [
                    "segment_id",
                    "start_km",
                    "end_km",
                    "grade_pct",
                    "speed_kmh",
                    "cadence_rpm",
                ]
            ]
            .round(1)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()