from gpx_utils import build_manual_route
from presets import get_surface_crr, get_aero_cda
from inverse import estimate_power_for_target_time


def test_inverse_solver_returns_power():
    segments = build_manual_route(
        distance_km=20,
        elevation_gain_m=300,
        segment_length_m=1000,
    )

    result = estimate_power_for_target_time(
        segments_df=segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        target_time_h=1.0,
        temp_c=20,
        humidity_pct=50,
        wind_kmh=0,
        wind_mode="head",
        chainring_teeth=34,
        cassette_teeth=32,
        cda=get_aero_cda("endurance_road"),
        crr=get_surface_crr("normal_road"),
        bottle_sizes_ml=[750, 750],
    )

    assert result["required_power_w"] > 0
    assert result["required_wkg"] > 0
    assert result["estimated_time_h"] > 0