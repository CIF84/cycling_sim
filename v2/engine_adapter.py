ENGINE_MODE = "Phase 6.1 expanded route intelligence"
ENGINE_DIAGNOSTICS: list[str] = []

try:
    from simulator import simulate_route
    from reporting import summarize_ride
except Exception as exc:  # keep the UI alive if imports fail
    simulate_route = None
    summarize_ride = None
    ENGINE_MODE = "Phase 4.3 fallback — v1 engine imports failed"
    ENGINE_DIAGNOSTICS.append(f"Engine import failed: {exc}")


def _no_route_summary(message: str = "Upload GPX or choose the demo route to calculate this ride.") -> dict:
    """Neutral summary used before a real route is selected."""
    return {
        "ready": False,
        "distance_km": 0.0,
        "duration_h": 0.0,
        "speed_kmh": 0.0,
        "calories": 0.0,
        "carbs_g": 0.0,
        "fluid_goal_l": 0.0,
        "sodium_mg": 0.0,
        "refills": "—",
        "engine_mode": message,
        "sim_df": None,
    }


def _temporary_estimate_ride_summary(inputs: dict) -> dict:
    """Safety fallback if the real v1 simulator errors."""
    distance_km = 80.78

    tire_adjustment = {
        "Fast gravel": 0.5,
        "Mixed gravel": 0.0,
        "Rough gravel": -0.8,
    }[inputs["tires"]]

    style_adjustment = {
        "Endurance": 0.0,
        "Upright": -0.7,
        "Aggressive": 0.8,
    }[inputs["riding_style"]]

    surface_adjustment = {
        "Smooth": 0.7,
        "Normal": 0.3,
        "Mixed gravel": 0.0,
        "Rough": -1.1,
    }[inputs["surface"]]

    aero_gain_pct = inputs.get("aero_gain_pct", 0)
    rolling_resistance_gain_pct = inputs.get("rolling_resistance_gain_pct", 0)

    speed_kmh = (
        25.4
        + (inputs["fitness"] - 3.0) * 3.2
        + (95 - inputs["rider_mass"]) * 0.06
        + (9.0 - inputs["bike_mass"]) * 0.16
        + tire_adjustment
        + style_adjustment
        + surface_adjustment
        + aero_gain_pct * 0.08
        + rolling_resistance_gain_pct * 0.035
        - inputs["wind"] * 0.035
    )
    speed_kmh = max(speed_kmh, 12.0)

    duration_h = distance_km / speed_kmh
    calories = duration_h * inputs["rider_mass"] * inputs["fitness"] * 3.35
    carbs_g = duration_h * 120
    heat_factor = 1 + max(inputs["temperature"] - 20, 0) * 0.015
    humidity_factor = 1 + max(inputs["humidity"] - 50, 0) * 0.006
    sweat_l = duration_h * 0.95 * heat_factor * humidity_factor
    fluid_goal_l = max(sweat_l - 1.9, 0.5)
    sodium_mg = fluid_goal_l * 1470
    refills = 0 if fluid_goal_l <= 1.5 else 1

    return {
        "ready": True,
        "distance_km": distance_km,
        "duration_h": duration_h,
        "speed_kmh": speed_kmh,
        "calories": calories,
        "carbs_g": carbs_g,
        "fluid_goal_l": fluid_goal_l,
        "sodium_mg": sodium_mg,
        "refills": refills,
        "engine_mode": "fallback temporary v2 model — v1 simulator errored",
    }


def _scenario_config_from_inputs(inputs: dict) -> dict:
    """Map v2 UI inputs into v1 simulator arguments."""
    cda_by_style = {
        "Upright": 0.42,
        "Endurance": 0.35,
        "Aggressive": 0.30,
    }

    crr_by_tire = {
        "Fast gravel": 0.0045,
        "Mixed gravel": 0.0060,
        "Rough gravel": 0.0080,
    }

    crr_by_surface = {
        "Smooth": 0.0040,
        "Normal": 0.0050,
        "Mixed gravel": 0.0070,
        "Rough": 0.0100,
    }

    cda = cda_by_style.get(inputs["riding_style"], 0.35)
    crr = max(
        crr_by_tire.get(inputs["tires"], 0.006),
        crr_by_surface.get(inputs["surface"], 0.006),
    )

    aero_gain_pct = float(inputs.get("aero_gain_pct", 0.0))
    rolling_resistance_gain_pct = float(inputs.get("rolling_resistance_gain_pct", 0.0))

    cda *= max(0.70, 1 - aero_gain_pct / 100)
    crr *= max(0.70, 1 - rolling_resistance_gain_pct / 100)

    drivetrain = inputs.get("drivetrain", "1x Gravel")
    if drivetrain == "2x Road":
        chainring_teeth = 46
        cassette_teeth = 34
    elif drivetrain == "MTB wide range":
        chainring_teeth = 34
        cassette_teeth = 51
    else:
        chainring_teeth = 40
        cassette_teeth = 45

    return {
        "segments_df": inputs.get("segments_df"),
        "rider_mass_kg": float(inputs["rider_mass"]),
        "bike_mass_kg": float(inputs["bike_mass"]),
        "fitness_wkg": float(inputs["fitness"]),
        "temp_c": float(inputs["temperature"]),
        "humidity_pct": float(inputs["humidity"]),
        "wind_kmh": float(inputs["wind"]),
        "wind_mode": "head",
        "chainring_teeth": chainring_teeth,
        "cassette_teeth": cassette_teeth,
        "cda": cda,
        "crr": crr,
        "bottle_sizes_ml": [750, 750],
    }


def run_ride_engine(inputs: dict) -> dict:
    """Single v2 integration point for Ride A / Ride B calculations."""
    if inputs.get("segments_df") is None:
        return _no_route_summary("No route selected — upload GPX or choose the demo route to calculate this ride")

    if simulate_route is None or summarize_ride is None:
        return _temporary_estimate_ride_summary(inputs)

    config = _scenario_config_from_inputs(inputs)

    try:
        sim_df = simulate_route(
            segments_df=config["segments_df"],
            rider_mass_kg=config["rider_mass_kg"],
            bike_mass_kg=config["bike_mass_kg"],
            fitness_wkg=config["fitness_wkg"],
            temp_c=config["temp_c"],
            humidity_pct=config["humidity_pct"],
            wind_kmh=config["wind_kmh"],
            wind_mode=config["wind_mode"],
            chainring_teeth=config["chainring_teeth"],
            cassette_teeth=config["cassette_teeth"],
            cda=config["cda"],
            crr=config["crr"],
        )

        summary = summarize_ride(
            sim_df=sim_df,
            rider_mass_kg=config["rider_mass_kg"],
            bottle_sizes_ml=config["bottle_sizes_ml"],
        )

        return {
            "ready": True,
            "distance_km": summary["distance_km"],
            "duration_h": summary["duration_h"],
            "speed_kmh": summary["avg_speed_kmh"],
            "calories": summary["energy_kcal"],
            "carbs_g": summary["carbs_g"],
            "fluid_goal_l": summary["fluid_goal_l"],
            "sodium_mg": summary["sodium_mg"],
            "refills": summary["refill_stops"],
            "engine_mode": "real v1 engine: simulate_route + summarize_ride using selected route",
            "sim_df": sim_df,
        }
    except Exception as exc:
        ENGINE_DIAGNOSTICS.append(f"Real v1 engine failed: {exc}")
        return _temporary_estimate_ride_summary(inputs)
