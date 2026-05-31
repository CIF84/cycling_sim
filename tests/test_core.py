from simulator import solve_speed_from_power, estimate_cadence_rpm, assign_target_power
from biology import estimate_segment_biology, estimate_fluid_goal_l


def test_speed_is_positive():
    speed_ms = solve_speed_from_power(
        power_w=250,
        total_mass_kg=90,
        grade_pct=2,
        wind_kmh=0,
    )
    assert speed_ms > 0


def test_more_power_is_faster():
    slow = solve_speed_from_power(180, 90, 1)
    fast = solve_speed_from_power(280, 90, 1)
    assert fast > slow


def test_headwind_is_slower_than_no_wind():
    no_wind = solve_speed_from_power(250, 90, 0, wind_kmh=0)
    headwind = solve_speed_from_power(250, 90, 0, wind_kmh=20)
    assert headwind < no_wind


def test_cadence_positive():
    cadence = estimate_cadence_rpm(
        speed_kmh=20,
        chainring_teeth=34,
        cassette_teeth=32,
    )
    assert cadence > 0


def test_climb_power_higher_than_flat_power():
    base_power = 250
    climb_power = assign_target_power(8, base_power)
    flat_power = assign_target_power(0, base_power)
    assert climb_power > flat_power


def test_biology_outputs_positive_values():
    result = estimate_segment_biology(
        power_w=250,
        time_s=3600,
        temp_c=25,
        humidity_pct=50,
    )
    assert result["kcal"] > 0
    assert result["carbs_g"] > 0
    assert result["sweat_l"] > 0
    assert result["sodium_mg"] > 0


def test_fluid_goal_allows_safe_deficit():
    fluid_goal = estimate_fluid_goal_l(
        sweat_l=3.0,
        rider_mass_kg=90,
    )
    assert fluid_goal == 1.2