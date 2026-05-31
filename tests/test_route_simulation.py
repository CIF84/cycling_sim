from gpx_utils import build_manual_route
from simulator import simulate_route


def test_simulate_route_returns_rows():
    segments = build_manual_route(
        distance_km=10,
        elevation_gain_m=100,
        segment_length_m=1000,
    )

    result = simulate_route(
        segments_df=segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        fitness_wkg=3.0,
    )

    assert len(result) == len(segments)
    assert result["time_s"].sum() > 0
    assert result["speed_kmh"].mean() > 0


def test_tailwind_is_faster_than_headwind():
    segments = build_manual_route(
        distance_km=10,
        elevation_gain_m=0,
        segment_length_m=1000,
    )

    headwind = simulate_route(
        segments_df=segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        fitness_wkg=3.0,
        wind_kmh=20,
        wind_mode="head",
    )

    tailwind = simulate_route(
        segments_df=segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        fitness_wkg=3.0,
        wind_kmh=20,
        wind_mode="tail",
    )

    assert tailwind["speed_kmh"].mean() > headwind["speed_kmh"].mean()


def test_route_has_biology_columns():
    segments = build_manual_route(
        distance_km=10,
        elevation_gain_m=100,
        segment_length_m=1000,
    )

    result = simulate_route(
        segments_df=segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        fitness_wkg=3.0,
        temp_c=25,
        humidity_pct=50,
    )

    assert result["kcal"].sum() > 0
    assert result["carbs_g"].sum() > 0
    assert result["sweat_l"].sum() > 0
    assert result["sodium_mg"].sum() > 0
    assert result["cum_kcal"].iloc[-1] > 0
    assert result["cum_carbs_g"].iloc[-1] > 0
    assert result["cum_sweat_l"].iloc[-1] > 0