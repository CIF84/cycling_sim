from gpx_utils import load_gpx, build_segments, build_manual_route
from simulator import simulate_route
from reporting import summarize_ride, print_ride_summary, build_fueling_plan
from charts import plot_route_profile, plot_fueling_curves
from presets import get_surface_crr, get_aero_cda
from compare import compare_surfaces, compare_aero_positions
from scenario import compare_scenarios
from inverse import estimate_power_for_target_time


USE_GPX = True
GPX_PATH = "sample_routes/my_ride.gpx"

RIDER_MASS_KG = 95
BIKE_MASS_KG = 9
FITNESS_WKG = 3.0

DISTANCE_KM = 80
ELEVATION_GAIN_M = 1200

TEMP_C = 24
HUMIDITY_PCT = 50
WIND_KMH = 5
WIND_MODE = "head"

CHAINRING_TEETH = 34
CASSETTE_TEETH = 32
BOTTLE_SIZES_ML = [750, 750]

SURFACE = "mixed_gravel"
AERO_POSITION = "endurance_road"

SEGMENT_LENGTH_M = 1000
ELEVATION_SMOOTH_WINDOW = 7

TARGET_TIME_H = 3.00


def build_route():
    if USE_GPX:
        print(f"\nLoading GPX file: {GPX_PATH}")
        gpx_df = load_gpx(GPX_PATH)
        return build_segments(
            gpx_df,
            segment_length_m=SEGMENT_LENGTH_M,
            elevation_smooth_window=ELEVATION_SMOOTH_WINDOW,
        )

    print("\nUsing manual route mode")
    return build_manual_route(
        distance_km=DISTANCE_KM,
        elevation_gain_m=ELEVATION_GAIN_M,
        segment_length_m=SEGMENT_LENGTH_M,
    )


def run_simulation(segments):
    crr = get_surface_crr(SURFACE)
    cda = get_aero_cda(AERO_POSITION)

    return simulate_route(
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
        cda=cda,
        crr=crr,
    )


def print_reports(sim):
    summary = summarize_ride(
        sim_df=sim,
        rider_mass_kg=RIDER_MASS_KG,
        bottle_sizes_ml=BOTTLE_SIZES_ML,
    )

    print_ride_summary(summary)

    fueling_plan = build_fueling_plan(sim_df=sim, block_minutes=20)

    print("\n" + "=" * 60)
    print("FUELING / HYDRATION PLAN")
    print("=" * 60)

    if fueling_plan.empty:
        print("Ride too short for fueling blocks.")
    else:
        print(fueling_plan.to_string(index=False))

    print("\n" + "=" * 60)
    print("TOP 10 HARDEST SEGMENTS")
    print("=" * 60)

    hardest = sim.sort_values(by="grade_pct", ascending=False).head(10)

    cols = [
        "segment_id",
        "start_km",
        "end_km",
        "grade_pct",
        "speed_kmh",
        "target_power_w",
        "cadence_rpm",
    ]

    print(hardest[cols].round(1).to_string(index=False))

    print("\n" + "=" * 60)
    print("LOW CADENCE SEGMENTS")
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


def print_comparisons(segments):
    surface_comparison = compare_surfaces(
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
        aero_key=AERO_POSITION,
        bottle_sizes_ml=BOTTLE_SIZES_ML,
    )

    print("\n" + "=" * 60)
    print("SURFACE COMPARISON")
    print("=" * 60)
    print(surface_comparison.round(2).to_string(index=False))

    aero_comparison = compare_aero_positions(
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
        surface_key=SURFACE,
        bottle_sizes_ml=BOTTLE_SIZES_ML,
    )

    print("\n" + "=" * 60)
    print("AERO COMPARISON")
    print("=" * 60)
    print(aero_comparison.round(2).to_string(index=False))


def print_rider_scenarios(segments):
    crr = get_surface_crr(SURFACE)
    cda = get_aero_cda(AERO_POSITION)

    current_power_w = RIDER_MASS_KG * FITNESS_WKG
    improved_power_w = current_power_w + 15

    scenarios = [
        {
            "name": "Current",
            "rider_mass_kg": RIDER_MASS_KG,
            "fitness_wkg": FITNESS_WKG,
        },
        {
            "name": "-5 kg",
            "rider_mass_kg": RIDER_MASS_KG - 5,
            "fitness_wkg": current_power_w / (RIDER_MASS_KG - 5),
        },
        {
            "name": "+15 W",
            "rider_mass_kg": RIDER_MASS_KG,
            "fitness_wkg": improved_power_w / RIDER_MASS_KG,
        },
        {
            "name": "-5 kg +15 W",
            "rider_mass_kg": RIDER_MASS_KG - 5,
            "fitness_wkg": improved_power_w / (RIDER_MASS_KG - 5),
        },
    ]

    results = compare_scenarios(
        segments_df=segments,
        scenarios=scenarios,
        bike_mass_kg=BIKE_MASS_KG,
        temp_c=TEMP_C,
        humidity_pct=HUMIDITY_PCT,
        wind_kmh=WIND_KMH,
        wind_mode=WIND_MODE,
        chainring_teeth=CHAINRING_TEETH,
        cassette_teeth=CASSETTE_TEETH,
        cda=cda,
        crr=crr,
        bottle_sizes_ml=BOTTLE_SIZES_ML,
    )

    print("\n" + "=" * 60)
    print("RIDER SCENARIOS")
    print("=" * 60)
    print(results.round(2).to_string(index=False))


def print_target_time_analysis(segments):
    crr = get_surface_crr(SURFACE)
    cda = get_aero_cda(AERO_POSITION)

    result = estimate_power_for_target_time(
        segments_df=segments,
        rider_mass_kg=RIDER_MASS_KG,
        bike_mass_kg=BIKE_MASS_KG,
        target_time_h=TARGET_TIME_H,
        temp_c=TEMP_C,
        humidity_pct=HUMIDITY_PCT,
        wind_kmh=WIND_KMH,
        wind_mode=WIND_MODE,
        chainring_teeth=CHAINRING_TEETH,
        cassette_teeth=CASSETTE_TEETH,
        cda=cda,
        crr=crr,
        bottle_sizes_ml=BOTTLE_SIZES_ML,
    )

    current_power_w = RIDER_MASS_KG * FITNESS_WKG

    print("\n" + "=" * 60)
    print("TARGET TIME ANALYSIS")
    print("=" * 60)
    print(f"Current power:       {current_power_w:.0f} W")
    print(f"Current W/kg:        {FITNESS_WKG:.2f}")
    print(f"Target time:         {TARGET_TIME_H:.2f} h")
    print(f"Required power:      {result['required_power_w']:.0f} W")
    print(f"Required W/kg:       {result['required_wkg']:.2f}")
    print(f"Estimated time:      {result['estimated_time_h']:.2f} h")
    print(f"Extra power needed:  {result['required_power_w'] - current_power_w:.0f} W")


def export_charts(sim):
    route_chart = plot_route_profile(sim, output_path="route_profile.png")
    fueling_chart = plot_fueling_curves(sim, output_path="fueling_curves.png")

    print("\n" + "=" * 60)
    print("CHARTS SAVED")
    print("=" * 60)
    print(route_chart)
    print(fueling_chart)


def main():
    print("=" * 60)
    print("BIKE SCIENCE PRO")
    print("=" * 60)
    print(f"Surface:       {SURFACE}")
    print(f"Aero position: {AERO_POSITION}")

    segments = build_route()
    print(f"\nRoute contains {len(segments)} segments")

    sim = run_simulation(segments)

    print_reports(sim)
    export_charts(sim)
    print_comparisons(segments)
    print_rider_scenarios(segments)
    print_target_time_analysis(segments)

    return sim


if __name__ == "__main__":
    simulation = main()