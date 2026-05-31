from simulator import simulate_route
from reporting import summarize_ride


def estimate_time_for_power(
    segments_df,
    rider_mass_kg,
    bike_mass_kg,
    power_w,
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
    """
    Estimate route duration for a fixed rider power.

    We convert absolute power to W/kg because simulate_route currently
    receives fitness_wkg.
    """

    fitness_wkg = power_w / rider_mass_kg

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

    return summary["duration_h"]


def estimate_power_for_target_time(
    segments_df,
    rider_mass_kg,
    bike_mass_kg,
    target_time_h,
    temp_c,
    humidity_pct,
    wind_kmh,
    wind_mode,
    chainring_teeth,
    cassette_teeth,
    cda,
    crr,
    bottle_sizes_ml,
    min_power_w=100,
    max_power_w=500,
    max_iter=40,
):
    """
    Estimate required rider power to finish route in target_time_h.

    Uses binary search:
    - if estimated time is too slow, increase power
    - if estimated time is faster than target, decrease power

    Returns dictionary with required power and estimated duration.
    """

    if target_time_h <= 0:
        raise ValueError("target_time_h must be greater than 0.")

    low = min_power_w
    high = max_power_w

    for _ in range(max_iter):
        mid = (low + high) / 2

        estimated_time_h = estimate_time_for_power(
            segments_df=segments_df,
            rider_mass_kg=rider_mass_kg,
            bike_mass_kg=bike_mass_kg,
            power_w=mid,
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

        if estimated_time_h > target_time_h:
            low = mid
        else:
            high = mid

    required_power_w = (low + high) / 2

    final_time_h = estimate_time_for_power(
        segments_df=segments_df,
        rider_mass_kg=rider_mass_kg,
        bike_mass_kg=bike_mass_kg,
        power_w=required_power_w,
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

    return {
        "target_time_h": target_time_h,
        "estimated_time_h": final_time_h,
        "required_power_w": required_power_w,
        "required_wkg": required_power_w / rider_mass_kg,
    }