from gpx_utils import build_manual_route
from simulator import simulate_route
from reporting import summarize_ride, build_fueling_plan


def test_summarize_ride_returns_metrics():
    segments = build_manual_route(
        distance_km=20,
        elevation_gain_m=300,
        segment_length_m=1000,
    )

    sim = simulate_route(
        segments_df=segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        fitness_wkg=3.0,
        temp_c=25,
        humidity_pct=50,
    )

    summary = summarize_ride(
        sim_df=sim,
        rider_mass_kg=90,
        bottle_sizes_ml=[750, 750],
    )

    assert summary["distance_km"] > 0
    assert summary["duration_h"] > 0
    assert summary["energy_kcal"] > 0
    assert summary["carbs_g"] > 0
    assert summary["sweat_l"] > 0


def test_build_fueling_plan_returns_rows():
    segments = build_manual_route(
        distance_km=20,
        elevation_gain_m=300,
        segment_length_m=1000,
    )

    sim = simulate_route(
        segments_df=segments,
        rider_mass_kg=90,
        bike_mass_kg=9,
        fitness_wkg=3.0,
        temp_c=25,
        humidity_pct=50,
    )

    plan = build_fueling_plan(
        sim_df=sim,
        block_minutes=20,
    )

    assert len(plan) > 0
    assert "suggested_carbs_g" in plan.columns
    assert "suggested_fluid_ml" in plan.columns
    assert "suggested_sodium_mg" in plan.columns