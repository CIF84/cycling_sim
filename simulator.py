import math
import pandas as pd

from biology import estimate_segment_biology

G = 9.81
AIR_DENSITY = 1.225

DEFAULT_CDA = 0.35
DEFAULT_CRR = 0.005

WHEEL_CIRCUMFERENCE = 2.11
MIN_CADENCE_THRESHOLD = 70
TARGET_CADENCE_RPM = 85


def solve_speed_from_power(
    power_w,
    total_mass_kg,
    grade_pct,
    wind_kmh=0.0,
    cda=DEFAULT_CDA,
    crr=DEFAULT_CRR,
    max_iter=80,
):
    grade = grade_pct / 100
    wind_ms = wind_kmh / 3.6

    def required_power(v):
        v_air = v + wind_ms

        f_gravity = total_mass_kg * G * grade
        f_rolling = total_mass_kg * G * crr
        f_aero = 0.5 * AIR_DENSITY * cda * (v_air ** 2)

        total_force = f_gravity + f_rolling + f_aero
        total_force = max(total_force, 0.1)

        return total_force * v

    low = 0.1
    high = 25.0

    for _ in range(max_iter):
        mid = (low + high) / 2
        p_mid = required_power(mid)

        if p_mid < power_w:
            low = mid
        else:
            high = mid

    return (low + high) / 2


def estimate_cadence_rpm(
    speed_kmh,
    chainring_teeth,
    cassette_teeth,
    wheel_circumference_m=WHEEL_CIRCUMFERENCE,
):
    development_m = wheel_circumference_m * (
        chainring_teeth / cassette_teeth
    )

    speed_m_per_min = speed_kmh * 1000 / 60

    return speed_m_per_min / development_m


def choose_virtual_gear(
    speed_kmh,
    chainring_teeth=40,
    cassette_teeth_options=None,
    target_cadence_rpm=TARGET_CADENCE_RPM,
):
    """
    Choose the cassette cog that gets cadence closest to target cadence.

    This is a simple virtual shifting model.
    It assumes one front chainring and a list of available rear cogs.
    """

    if cassette_teeth_options is None:
        cassette_teeth_options = [10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 42, 45]

    gear_options = []

    for cog in cassette_teeth_options:
        cadence = estimate_cadence_rpm(
            speed_kmh=speed_kmh,
            chainring_teeth=chainring_teeth,
            cassette_teeth=cog,
        )

        gear_options.append(
            {
                "selected_cog_teeth": cog,
                "cadence_rpm": cadence,
                "cadence_error": abs(cadence - target_cadence_rpm),
            }
        )

    best = min(
        gear_options,
        key=lambda x: x["cadence_error"],
    )

    return best


def assign_target_power(
    grade_pct,
    base_power_w,
):
    if grade_pct >= 8:
        return base_power_w * 1.08

    if grade_pct >= 4:
        return base_power_w * 1.00

    if grade_pct >= 1:
        return base_power_w * 0.92

    if grade_pct >= -2:
        return base_power_w * 0.82

    return base_power_w * 0.45


def simulate_segment(
    distance_m,
    grade_pct,
    rider_mass_kg,
    bike_mass_kg,
    base_power_w,
    temp_c=20,
    humidity_pct=50,
    wind_kmh=0.0,
    chainring_teeth=40,
    cassette_teeth_options=None,
    target_cadence_rpm=TARGET_CADENCE_RPM,
    cda=DEFAULT_CDA,
    crr=DEFAULT_CRR,
):
    total_mass_kg = rider_mass_kg + bike_mass_kg

    target_power_w = assign_target_power(
        grade_pct=grade_pct,
        base_power_w=base_power_w,
    )

    speed_ms = solve_speed_from_power(
        power_w=target_power_w,
        total_mass_kg=total_mass_kg,
        grade_pct=grade_pct,
        wind_kmh=wind_kmh,
        cda=cda,
        crr=crr,
    )

    speed_kmh = speed_ms * 3.6
    time_s = distance_m / speed_ms

    gear = choose_virtual_gear(
        speed_kmh=speed_kmh,
        chainring_teeth=chainring_teeth,
        cassette_teeth_options=cassette_teeth_options,
        target_cadence_rpm=target_cadence_rpm,
    )

    biology = estimate_segment_biology(
        power_w=target_power_w,
        time_s=time_s,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
    )

    return {
        "distance_m": distance_m,
        "grade_pct": grade_pct,
        "target_power_w": target_power_w,
        "speed_ms": speed_ms,
        "speed_kmh": speed_kmh,
        "time_s": time_s,
        "selected_cog_teeth": gear["selected_cog_teeth"],
        "cadence_rpm": gear["cadence_rpm"],
        **biology,
    }


def simulate_route(
    segments_df,
    rider_mass_kg,
    bike_mass_kg,
    fitness_wkg,
    temp_c=20,
    humidity_pct=50,
    wind_kmh=0.0,
    wind_mode="head",
    chainring_teeth=40,
    cassette_teeth=45,
    cassette_teeth_options=None,
    target_cadence_rpm=TARGET_CADENCE_RPM,
    cda=DEFAULT_CDA,
    crr=DEFAULT_CRR,
):
    if segments_df.empty:
        raise ValueError("segments_df is empty.")

    if cassette_teeth_options is None:
        cassette_teeth_options = [10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 42, cassette_teeth]

    cassette_teeth_options = sorted(set(cassette_teeth_options))

    base_power_w = rider_mass_kg * fitness_wkg

    signed_wind_kmh = wind_kmh
    if wind_mode == "tail":
        signed_wind_kmh = -wind_kmh

    rows = []

    cumulative_time_s = 0.0
    cumulative_distance_m = 0.0
    cumulative_kcal = 0.0
    cumulative_carbs_g = 0.0
    cumulative_sweat_l = 0.0
    cumulative_sodium_mg = 0.0

    for _, segment in segments_df.iterrows():
        segment_result = simulate_segment(
            distance_m=segment["dist_m"],
            grade_pct=segment["grade_pct"],
            rider_mass_kg=rider_mass_kg,
            bike_mass_kg=bike_mass_kg,
            base_power_w=base_power_w,
            temp_c=temp_c,
            humidity_pct=humidity_pct,
            wind_kmh=signed_wind_kmh,
            chainring_teeth=chainring_teeth,
            cassette_teeth_options=cassette_teeth_options,
            target_cadence_rpm=target_cadence_rpm,
            cda=cda,
            crr=crr,
        )

        cumulative_time_s += segment_result["time_s"]
        cumulative_distance_m += segment["dist_m"]
        cumulative_kcal += segment_result["kcal"]
        cumulative_carbs_g += segment_result["carbs_g"]
        cumulative_sweat_l += segment_result["sweat_l"]
        cumulative_sodium_mg += segment_result["sodium_mg"]

        rows.append(
            {
                **segment.to_dict(),
                **segment_result,
                "low_cadence_flag": segment_result["cadence_rpm"] < MIN_CADENCE_THRESHOLD,
                "cum_time_s": cumulative_time_s,
                "cum_time_h": cumulative_time_s / 3600,
                "cum_dist_m": cumulative_distance_m,
                "cum_dist_km": cumulative_distance_m / 1000,
                "cum_kcal": cumulative_kcal,
                "cum_carbs_g": cumulative_carbs_g,
                "cum_sweat_l": cumulative_sweat_l,
                "cum_sodium_mg": cumulative_sodium_mg,
            }
        )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    demo_segments = pd.DataFrame(
        [
            {
                "segment_id": 1,
                "start_km": 0,
                "end_km": 1,
                "dist_m": 1000,
                "grade_pct": 2,
                "elev_delta_m": 20,
                "elev_gain_m": 20,
                "elev_loss_m": 0,
            }
        ]
    )

    result = simulate_route(
        segments_df=demo_segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        fitness_wkg=3.0,
        temp_c=24,
        humidity_pct=50,
    )

    print(result)