import math
import tempfile

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Bike Science Pro v2",
    layout="wide",
)

# ==========================================================
# PHASE 4.2 — REAL ENGINE BRIDGE
# ==========================================================
# This iteration keeps the v2 UI stable and upgrades the adapter layer.
#
# The app now tries to call a real v1 simulation entry point if one is
# available in the local project. If the exact v1 function signature does not
# match yet, it falls back safely to the temporary v2 model so the UI remains
# usable while we wire the engine.
#
# Next step after this file runs in your Codespace:
# - inspect ENGINE_DIAGNOSTICS in the app or terminal if fallback is used
# - adapt _run_real_v1_engine(...) to your exact simulator.py/scenario.py API

ENGINE_MODE = "Phase 4.2 bridge / waiting for real v1 engine"
ENGINE_DIAGNOSTICS: list[str] = []


# ==========================================================
# HELPERS
# ==========================================================


def render_html(html: str) -> None:
    """Render raw HTML without leading indentation so Streamlit does not treat it as code."""
    cleaned = "\n".join(line.strip() for line in html.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def format_duration(hours: float) -> str:
    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h} h {m:02d} min"


def signed_delta(value: float, unit: str, decimals: int = 1, lower_is_better: bool = False) -> str:
    sign = "+" if value >= 0 else "−"
    abs_value = abs(value)
    if decimals == 0:
        number = f"{abs_value:.0f}"
    else:
        number = f"{abs_value:.{decimals}f}"
    return f"{sign}{number} {unit}"


def delta_class(value: float, lower_is_better: bool = False) -> str:
    if value == 0:
        return "diff-neutral"
    positive_is_good = value > 0
    good = not positive_is_good if lower_is_better else positive_is_good
    return "diff-positive" if good else "diff-negative"



# ==========================================================
# PHASE 4.3 — REAL V1 ENGINE CONNECTION
# ==========================================================
# This iteration stops guessing function signatures and connects explicitly to
# the existing v1 engine primitives:
#
# simulate_route(...)  -> segment-level physics simulation
# summarize_ride(...)  -> ride briefing metrics
#
# Because v2 does not have GPX upload connected yet, this version uses a stable
# generated demo route. Phase 4.4 should replace _default_segments() with
# GPX upload + build_segments(...).

ENGINE_MODE = "Phase 6.1 expanded route intelligence"
ENGINE_DIAGNOSTICS: list[str] = []

try:
    from simulator import simulate_route
    from reporting import summarize_ride
    from gpx_utils import load_gpx, build_segments
except Exception as exc:  # keep the UI alive if imports fail
    simulate_route = None
    summarize_ride = None
    load_gpx = None
    build_segments = None
    ENGINE_MODE = "Phase 4.3 fallback — v1 engine imports failed"
    ENGINE_DIAGNOSTICS.append(f"Engine import failed: {exc}")


@st.cache_data
def _default_segments() -> pd.DataFrame:
    """Generated demo route until GPX upload is wired into v2.

    The goal is not to fake physics. The goal is to feed the real v1 simulator
    a consistent segment dataframe with the same structure produced by
    gpx_utils.build_segments(...).
    """
    total_distance_km = 80.78
    segment_count = 80
    segment_dist_m = total_distance_km * 1000 / segment_count

    rows = []
    for i in range(segment_count):
        start_km = i * segment_dist_m / 1000
        end_km = (i + 1) * segment_dist_m / 1000

        # Rolling route profile with one harder middle section.
        wave_grade = 2.4 * math.sin(i / 8.0) + 1.2 * math.sin(i / 3.3)
        hill_bump = 3.0 if 38 <= i <= 55 else 0.0
        descent = -2.2 if 58 <= i <= 70 else 0.0
        grade_pct = wave_grade + hill_bump + descent
        grade_pct = max(-7.0, min(8.5, grade_pct))

        elev_delta_m = segment_dist_m * grade_pct / 100

        rows.append(
            {
                "segment_id": i + 1,
                "start_km": round(start_km, 3),
                "end_km": round(end_km, 3),
                "dist_m": segment_dist_m,
                "grade_pct": grade_pct,
                "elev_delta_m": elev_delta_m,
                "elev_gain_m": max(elev_delta_m, 0),
                "elev_loss_m": abs(min(elev_delta_m, 0)),
            }
        )

    return pd.DataFrame(rows)



@st.cache_data(show_spinner=False)
def _segments_from_gpx_bytes(file_bytes: bytes) -> pd.DataFrame:
    """Convert uploaded GPX bytes into the v1 segment dataframe.

    Streamlit upload objects live in memory, while the existing v1 loader expects
    a file path. This small adapter writes a temporary file, then reuses the
    proven v1 GPX pipeline: load_gpx(...) -> build_segments(...).
    """
    if load_gpx is None or build_segments is None:
        raise RuntimeError("GPX utilities are not available.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".gpx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    points_df = load_gpx(tmp_path)
    return build_segments(points_df)


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


def _longest_climb_km(segments_df: pd.DataFrame, climb_threshold_pct: float = 2.0) -> float:
    """Estimate the longest continuous climb from modeled route segments."""
    longest_m = 0.0
    current_m = 0.0

    for _, row in segments_df.iterrows():
        if row["grade_pct"] >= climb_threshold_pct:
            current_m += row["dist_m"]
            longest_m = max(longest_m, current_m)
        else:
            current_m = 0.0

    return longest_m / 1000


def _difficulty_stars(distance_km: float, elevation_gain_m: float, hard_segments: int) -> str:
    """Simple route difficulty proxy for Phase 6.1."""
    climbing_density = elevation_gain_m / max(distance_km, 0.1)
    score = 1

    if distance_km >= 50:
        score += 1
    if distance_km >= 90:
        score += 1
    if climbing_density >= 10:
        score += 1
    if climbing_density >= 20:
        score += 1
    if hard_segments >= 20:
        score += 1

    score = max(1, min(score, 5))
    return "★" * score + "☆" * (5 - score)


def _route_character(route_type: str, distance_km: float, elevation_gain_m: float, hard_segments: int) -> str:
    """Human-readable route character label for Phase 6.2."""
    if distance_km >= 100 and elevation_gain_m >= 1500:
        return "big endurance day"
    if route_type == "climbing-heavy":
        return "climbing-focused route"
    if hard_segments >= 35:
        return "punchy rolling route"
    if route_type == "rolling":
        return "rolling endurance route"
    return "steady fast route"


def _climbing_profile(longest_climb_km: float, avg_climb_grade: float, hard_segments: int) -> str:
    """Short climbing profile label."""
    if longest_climb_km >= 6:
        return "long sustained climbs"
    if avg_climb_grade >= 6:
        return "steep climbs"
    if hard_segments >= 30:
        return "many short ramps"
    if longest_climb_km >= 2:
        return "rolling climbs"
    return "minor climbs"


def _route_profile_df(segments_df: pd.DataFrame | None) -> pd.DataFrame:
    """Build a compact elevation profile from modeled route segments."""
    if segments_df is None or segments_df.empty:
        return pd.DataFrame(columns=["distance_km", "relative_elevation_m"])

    profile = segments_df.copy()
    profile["distance_km"] = profile["end_km"]
    profile["relative_elevation_m"] = profile["elev_delta_m"].cumsum()

    start = pd.DataFrame({"distance_km": [0.0], "relative_elevation_m": [0.0]})
    return pd.concat(
        [start, profile[["distance_km", "relative_elevation_m"]]],
        ignore_index=True,
    )


def route_intelligence(segments_df: pd.DataFrame | None) -> dict:
    """Summarize route structure before running the ride simulation."""
    if segments_df is None or segments_df.empty:
        return {"ready": False}

    distance_km = segments_df["dist_m"].sum() / 1000
    elevation_gain_m = segments_df.get("elev_gain_m", pd.Series(dtype=float)).sum()
    elevation_loss_m = segments_df.get("elev_loss_m", pd.Series(dtype=float)).sum()
    max_grade = segments_df["grade_pct"].max()
    min_grade = segments_df["grade_pct"].min()
    avg_abs_grade = segments_df["grade_pct"].abs().mean()
    hard_segments = int((segments_df["grade_pct"].abs() >= 6).sum())

    climbing_density = elevation_gain_m / max(distance_km, 0.1)
    if climbing_density >= 20:
        route_type = "climbing-heavy"
    elif climbing_density >= 10:
        route_type = "rolling"
    else:
        route_type = "mostly flat"

    climbing_segments = segments_df[segments_df["grade_pct"] > 1.0]
    descending_segments = segments_df[segments_df["grade_pct"] < -1.0]
    flat_segments = segments_df[segments_df["grade_pct"].abs() <= 1.0]
    rolling_segments = segments_df[(segments_df["grade_pct"].abs() > 1.0) & (segments_df["grade_pct"].abs() < 4.0)]

    climbing_distance_km = climbing_segments["dist_m"].sum() / 1000
    descending_distance_km = descending_segments["dist_m"].sum() / 1000
    flat_distance_km = flat_segments["dist_m"].sum() / 1000
    rolling_distance_km = rolling_segments["dist_m"].sum() / 1000

    avg_climb_grade = (
        climbing_segments["elev_gain_m"].sum() / max(climbing_segments["dist_m"].sum(), 1) * 100
        if not climbing_segments.empty
        else 0.0
    )

    longest_climb_km = _longest_climb_km(segments_df)
    difficulty = _difficulty_stars(distance_km, elevation_gain_m, hard_segments)

    easy_segments = int((segments_df["grade_pct"].abs() < 3).sum())
    moderate_segments = int(((segments_df["grade_pct"].abs() >= 3) & (segments_df["grade_pct"].abs() < 6)).sum())
    very_hard_segments = int((segments_df["grade_pct"].abs() >= 10).sum())

    route_character = _route_character(route_type, distance_km, elevation_gain_m, hard_segments)
    climbing_profile = _climbing_profile(longest_climb_km, avg_climb_grade, hard_segments)

    return {
        "ready": True,
        "distance_km": distance_km,
        "elevation_gain_m": elevation_gain_m,
        "elevation_loss_m": elevation_loss_m,
        "max_grade": max_grade,
        "min_grade": min_grade,
        "avg_abs_grade": avg_abs_grade,
        "hard_segments": hard_segments,
        "very_hard_segments": very_hard_segments,
        "moderate_segments": moderate_segments,
        "easy_segments": easy_segments,
        "segments": len(segments_df),
        "difficulty": difficulty,
        "route_type": route_type,
        "route_character": route_character,
        "climbing_profile": climbing_profile,
        "climbing_density": climbing_density,
        "climbing_distance_km": climbing_distance_km,
        "descending_distance_km": descending_distance_km,
        "flat_distance_km": flat_distance_km,
        "rolling_distance_km": rolling_distance_km,
        "avg_climb_grade": avg_climb_grade,
        "longest_climb_km": longest_climb_km,
        "climbing_pct": climbing_distance_km / max(distance_km, 0.1) * 100,
        "descending_pct": descending_distance_km / max(distance_km, 0.1) * 100,
        "flat_pct": flat_distance_km / max(distance_km, 0.1) * 100,
        "rolling_pct": rolling_distance_km / max(distance_km, 0.1) * 100,
    }


def render_route_intelligence(segments_df: pd.DataFrame | None, route_description: str) -> None:
    """Render route-level facts inside the Input Zone."""
    info = route_intelligence(segments_df)

    if not info["ready"]:
        render_html(
            f"""
<div class="route-intelligence-empty">
<b>Route intelligence</b><br>
{route_description}. Upload a GPX or choose the demo route to calculate distance, elevation and ride outputs.
</div>
"""
        )
        return

    render_html(
        f"""
<div class="route-intelligence-section-title">Route Overview</div>
<div class="route-intelligence-grid">
<div class="route-intelligence-card"><div class="briefing-label">Route distance</div><div class="briefing-value">{info['distance_km']:.1f} km</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Elevation gain</div><div class="briefing-value">{info['elevation_gain_m']:.0f} m</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Max grade</div><div class="briefing-value">{info['max_grade']:.1f}%</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Route type</div><div class="briefing-value">{info['route_type']}</div></div>
</div>

<div class="route-intelligence-section-title">Ride Character</div>
<div class="route-intelligence-wide-card">
<div class="briefing-label">What kind of ride is this?</div>
<div class="briefing-value">{info['route_character']}</div>
<div class="route-intelligence-subtle">{info['distance_km']:.1f} km with {info['elevation_gain_m']:.0f} m gain, {info['hard_segments']} hard segments and a {info['climbing_profile']} climbing profile.</div>
</div>

<div class="route-intelligence-section-title">Difficulty</div>
<div class="route-intelligence-grid">
<div class="route-intelligence-card"><div class="briefing-label">Difficulty</div><div class="briefing-value">{info['difficulty']}</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Hard segments</div><div class="briefing-value">{info['hard_segments']}</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Longest climb</div><div class="briefing-value">{info['longest_climb_km']:.1f} km</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Steepest descent</div><div class="briefing-value">{info['min_grade']:.1f}%</div></div>
</div>

<div class="route-intelligence-section-title">Terrain Mix</div>
<div class="route-intelligence-grid">
<div class="route-intelligence-card"><div class="briefing-label">Climbing</div><div class="briefing-value">{info['climbing_pct']:.0f}%</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Descending</div><div class="briefing-value">{info['descending_pct']:.0f}%</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Flat</div><div class="briefing-value">{info['flat_pct']:.0f}%</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Rolling</div><div class="briefing-value">{info['rolling_pct']:.0f}%</div></div>
</div>

<div class="route-intelligence-section-title">Segment Severity</div>
<div class="route-intelligence-grid">
<div class="route-intelligence-card"><div class="briefing-label">Easy</div><div class="briefing-value">{info['easy_segments']}</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Moderate</div><div class="briefing-value">{info['moderate_segments']}</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Hard</div><div class="briefing-value">{info['hard_segments']}</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Very hard</div><div class="briefing-value">{info['very_hard_segments']}</div></div>
</div>

<div class="route-intelligence-section-title">Climbing</div>
<div class="route-intelligence-grid">
<div class="route-intelligence-card"><div class="briefing-label">Climbing distance</div><div class="briefing-value">{info['climbing_distance_km']:.1f} km</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Avg climb grade</div><div class="briefing-value">{info['avg_climb_grade']:.1f}%</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Elevation per km</div><div class="briefing-value">{info['climbing_density']:.1f} m/km</div></div>
<div class="route-intelligence-card"><div class="briefing-label">Modeled segments</div><div class="briefing-value">{info['segments']}</div></div>
</div>

<div class="route-intelligence-section-title">Route Profile</div>
"""
    )

    profile_df = _route_profile_df(segments_df)
    st.line_chart(
        profile_df,
        x="distance_km",
        y="relative_elevation_m",
        height=130,
    )

    render_html(
        """
<div class="route-intelligence-note">Phase 7.2 route intelligence based on modeled segments from the selected route.</div>
"""
    )


def resolve_route_segments(
    route_mode: str,
    uploaded_file,
    fallback_segments: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame | None, str]:
    """Resolve selected route without silently falling back to demo data."""
    if route_mode == "Same as Ride A":
        if fallback_segments is not None:
            return fallback_segments, "same route as Ride A"
        return None, "waiting for Ride A route"

    if route_mode == "Upload GPX":
        if uploaded_file is None:
            return None, "no GPX uploaded"
        try:
            return _segments_from_gpx_bytes(uploaded_file.getvalue()), f"uploaded GPX: {uploaded_file.name}"
        except Exception as exc:
            ENGINE_DIAGNOSTICS.append(f"GPX upload failed for {getattr(uploaded_file, 'name', 'unknown file')}: {exc}")
            return None, f"GPX upload failed: {exc}"

    if route_mode == "Generated demo route":
        return _default_segments(), "generated demo route"

    return None, "no route selected"


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

# ==========================================================
# CSS
# ==========================================================

render_html(
    """
<style>
:root {
--bg: #0e1117;
--panel: #111827;
--panel-soft: rgba(17, 24, 39, 0.94);
--scenario-panel: rgba(255,255,255,0.018);
--border: rgba(255,255,255,0.16);
--border-soft: rgba(255,255,255,0.10);
--text-muted: #a9a9a9;
--accent: #35aef5;
--danger: #f87171;
--success: #4ade80;
--warning: #facc15;
}

.block-container {
max-width: 100%;
padding-top: 282px;
padding-left: 255px;
padding-right: 48px;
padding-bottom: 235px;
}

header[data-testid="stHeader"] {
background: transparent;
}

.fixed-top {
position: fixed;
top: 0;
left: 0;
right: 0;
z-index: 1000;
background: var(--panel);
padding: 38px 48px 18px 48px;
border-bottom: 1px solid var(--border);
box-shadow: 0 10px 28px rgba(0,0,0,0.38);
}
.fixed-top h1 {
margin: 0;
padding: 0;
font-size: 2.25rem;
line-height: 1.1;
color: #ffffff;
letter-spacing: -0.025em;
}
.fixed-top p {
margin-top: 0.45rem;
margin-bottom: 0.9rem;
color: var(--text-muted);
font-size: 0.95rem;
}
.top-cards {
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 14px;
}
.info-card {
background: #17324a;
border: 1px solid rgba(53,174,245,0.22);
border-radius: 10px;
padding: 14px;
color: var(--accent);
min-height: 68px;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}
.info-card b {
color: var(--accent);
}

.fixed-left {
position: fixed;
top: 238px;
left: 0;
bottom: 190px;
width: 210px;
z-index: 999;
background: var(--panel-soft);
border-right: 1px solid var(--border);
box-shadow: 10px 0 24px rgba(0,0,0,0.22);
padding: 24px 18px 24px 48px;
white-space: nowrap;
overflow: hidden;
}
.fixed-left h3 {
margin-top: 0;
margin-bottom: 0.45rem;
font-size: 1.15rem;
}
.nav-note {
color: var(--text-muted);
font-size: 0.78rem;
margin-bottom: 1.15rem;
}
.nav-item {
margin: 0.85rem 0;
color: #d6d6d6;
font-size: 0.95rem;
}

.fixed-bottom {
position: fixed;
left: 210px;
right: 0;
bottom: 0;
z-index: 1000;
background: var(--panel);
padding: 14px 48px 16px 45px;
border-top: 1px solid var(--border);
box-shadow: 0 -10px 28px rgba(0,0,0,0.44);
}
.fixed-bottom h2 {
margin: 0 0 0.15rem 0;
padding: 0;
font-size: 1.35rem;
}
.bottom-caption {
color: var(--text-muted);
margin-bottom: 0.65rem;
font-size: 0.86rem;
}

.scenario-verdict {
background: rgba(53,174,245,0.08);
border: 1px solid rgba(53,174,245,0.18);
border-radius: 9px;
padding: 8px 11px;
margin: 0.55rem 0 0.75rem 0;
font-size: 0.86rem;
color: #dcefff;
}
.scenario-verdict b {
color: #ffffff;
}
.decision-context {
border: 1px solid rgba(53,174,245,0.28);
border-radius: 10px;
background: rgba(53,174,245,0.055);
padding: 10px 12px;
margin: 0.65rem 0 0.65rem 0;
}
.decision-context-title {
font-size: 0.72rem;
font-weight: 900;
letter-spacing: 0.1em;
text-transform: uppercase;
color: var(--accent);
margin-bottom: 0.25rem;
}
.decision-context-main {
font-size: 0.98rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.25rem;
}
.decision-context-meta {
font-size: 0.82rem;
color: #d6d6d6;
line-height: 1.4;
}

.diff-grid {
display: grid;
grid-template-columns: repeat(6, 1fr);
gap: 12px;
margin-bottom: 0.7rem;
}
.diff-card {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 9px;
padding: 9px 11px;
min-height: 68px;
}
.diff-label {
font-size: 0.76rem;
color: #cfcfcf;
margin-bottom: 0.15rem;
}
.diff-value {
font-size: 1.16rem;
font-weight: 700;
color: #ffffff;
line-height: 1.25;
}
.diff-positive {
color: var(--success);
font-size: 0.78rem;
margin-top: 0.15rem;
}
.diff-negative {
color: var(--danger);
font-size: 0.78rem;
margin-top: 0.15rem;
}
.diff-neutral {
color: var(--text-muted);
font-size: 0.78rem;
margin-top: 0.15rem;
}
.bottom-tabs {
display: flex;
gap: 10px;
margin-top: 0.45rem;
}
.bottom-tab {
padding: 6px 12px;
border-radius: 999px;
border: 1px solid rgba(255,255,255,0.18);
color: #d6d6d6;
font-size: 0.82rem;
}
.bottom-tab.active {
background: #ff4b4b;
color: white;
border-color: #ff4b4b;
}

.ride-title-card {
border-bottom: 1px solid var(--border);
margin-bottom: 1.25rem;
padding: 0 0 0.85rem 0;
}
.ride-title-card h2 {
margin: 0;
font-size: 2rem;
line-height: 1.05;
letter-spacing: -0.025em;
}
.ride-title-card p {
margin: 0.35rem 0 0 0;
color: var(--text-muted);
font-size: 0.95rem;
}
.section-divider {
margin: 2rem 0 1rem 0;
border-top: 1px solid var(--border);
}
.zone-label {
font-size: 0.82rem;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--accent);
font-weight: 700;
margin-bottom: 0.45rem;
}

.input-note {
margin-bottom: 1rem;
color: var(--text-muted);
font-size: 0.82rem;
}

.comparison-label {
font-size: 0.82rem;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--accent);
font-weight: 700;
margin-bottom: 0.45rem;
}

.zone-title-row {
display: flex;
align-items: baseline;
justify-content: space-between;
gap: 12px;
margin-bottom: 0.65rem;
}
.zone-subtitle {
color: var(--text-muted);
font-size: 0.82rem;
line-height: 1.45;
margin-bottom: 1rem;
}
.input-zone-marker,
.outcome-zone-marker {
font-size: 0.78rem;
letter-spacing: 0.12em;
text-transform: uppercase;
font-weight: 800;
color: var(--accent);
}
.input-zone-marker::before,
.outcome-zone-marker::before {
content: "";
display: inline-block;
width: 7px;
height: 7px;
border-radius: 999px;
background: var(--accent);
margin-right: 8px;
box-shadow: 0 0 12px rgba(53,174,245,0.55);
}

/* Visually separate assumptions from consequences. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.input-zone-marker) {
background: linear-gradient(180deg, rgba(17,24,39,0.74), rgba(17,24,39,0.42));
border-color: rgba(255,255,255,0.16) !important;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 24px rgba(0,0,0,0.14);
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.outcome-zone-marker) {
background: linear-gradient(180deg, rgba(21,33,48,0.78), rgba(21,33,48,0.48));
border-color: rgba(53,174,245,0.24) !important;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 26px rgba(0,0,0,0.18);
}

/* Give major sections stronger rhythm inside each ride. */
div[data-testid="stVerticalBlockBorderWrapper"] h3 {
margin-top: 0.95rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] h4 {
margin-top: 1.1rem;
margin-bottom: 0.55rem;
}

.briefing-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.75rem;
}
.briefing-card {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 10px 12px;
}
.briefing-label {
font-size: 0.76rem;
color: #cfcfcf;
margin-bottom: 0.15rem;
}
.briefing-value {
font-size: 1.2rem;
font-weight: 700;
color: white;
}
.briefing-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}

.recommendation-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.75rem;
}
.recommendation-card {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 10px 12px;
}
.recommendation-title {
font-weight: 800;
color: #ffffff;
margin-bottom: 0.45rem;
}
.recommendation-card ul {
margin: 0;
padding-left: 1.1rem;
color: #d6d6d6;
font-size: 0.84rem;
line-height: 1.45;
}
.recommendation-card li {
margin-bottom: 0.25rem;
}
.recommendation-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}


.performance-list {
margin-top: 0.75rem;
display: grid;
gap: 9px;
}
.performance-row {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 9px 11px;
}
.performance-head {
display: flex;
justify-content: space-between;
gap: 12px;
font-size: 0.84rem;
font-weight: 700;
color: #ffffff;
margin-bottom: 0.45rem;
}
.performance-value {
color: var(--accent);
white-space: nowrap;
}
.performance-track {
height: 7px;
border-radius: 999px;
background: rgba(255,255,255,0.10);
overflow: hidden;
}
.performance-fill {
height: 100%;
border-radius: 999px;
background: var(--accent);
}
.performance-insight {
margin-top: 0.85rem;
background: rgba(53, 174, 245, 0.10);
border: 1px solid rgba(53, 174, 245, 0.22);
border-radius: 8px;
padding: 10px 12px;
color: #dcefff;
font-size: 0.86rem;
line-height: 1.45;
}
.performance-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}


.opportunity-section-title {
margin-top: 1.2rem;
margin-bottom: 0.4rem;
font-weight: 800;
color: #ffffff;
}
.opportunity-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.7rem;
}
.opportunity-card {
background: rgba(53, 174, 245, 0.055);
border: 1px solid rgba(53, 174, 245, 0.18);
border-radius: 8px;
padding: 10px 12px;
position: relative;
overflow: hidden;
}
.opportunity-card.priority-1 {
border-color: rgba(74, 222, 128, 0.55);
background: linear-gradient(90deg, rgba(74, 222, 128, 0.12), rgba(53, 174, 245, 0.035));
}
.opportunity-card.priority-2 {
border-color: rgba(53, 174, 245, 0.42);
background: linear-gradient(90deg, rgba(53, 174, 245, 0.10), rgba(53, 174, 245, 0.035));
}
.opportunity-card.priority-low {
border-color: rgba(255,255,255,0.14);
background: rgba(255,255,255,0.025);
}
.opportunity-rank {
font-size: 0.72rem;
letter-spacing: 0.09em;
text-transform: uppercase;
color: var(--accent);
font-weight: 900;
margin-bottom: 0.35rem;
}
.opportunity-card.priority-1 .opportunity-rank {
color: #4ade80;
}
.opportunity-title {
font-size: 0.94rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.25rem;
}
.opportunity-meta {
font-size: 0.82rem;
color: #d6d6d6;
line-height: 1.45;
}
.opportunity-decision-grid {
display: grid;
grid-template-columns: repeat(3, minmax(0, 1fr));
gap: 6px;
margin: 0.55rem 0;
}
.opportunity-pill {
border: 1px solid rgba(255,255,255,0.12);
border-radius: 7px;
padding: 6px 8px;
background: rgba(255,255,255,0.025);
}
.opportunity-pill-label {
font-size: 0.68rem;
color: var(--text-muted);
margin-bottom: 0.1rem;
}
.opportunity-pill-value {
font-size: 0.82rem;
font-weight: 900;
color: #ffffff;
}
.opportunity-score {
margin-top: 0.55rem;
font-size: 0.82rem;
color: #9ee7ff;
font-weight: 800;
}
.opportunity-focus {
border: 1px solid rgba(74, 222, 128, 0.42);
border-radius: 8px;
background: rgba(74, 222, 128, 0.08);
padding: 10px 12px;
margin-top: 0.55rem;
margin-bottom: 0.75rem;
}
.opportunity-focus-title {
font-size: 0.85rem;
font-weight: 900;
color: #4ade80;
margin-bottom: 0.2rem;
}
.opportunity-focus-main {
font-size: 1rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.2rem;
}
.opportunity-portfolio-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.7rem;
}
.opportunity-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}


.upgrade-section-title {
margin-top: 1.25rem;
margin-bottom: 0.55rem;
font-weight: 900;
color: #ffffff;
}
.upgrade-advisor-grid {
display: grid;
grid-template-columns: repeat(3, minmax(0, 1fr));
gap: 10px;
margin-top: 0.65rem;
}
.upgrade-card {
border: 1px solid rgba(255,255,255,0.14);
border-radius: 10px;
padding: 12px;
background: rgba(255,255,255,0.025);
}
.upgrade-card.best {
border-color: rgba(74, 222, 128, 0.55);
background: linear-gradient(90deg, rgba(74, 222, 128, 0.12), rgba(53, 174, 245, 0.03));
}
.upgrade-card.second {
border-color: rgba(53, 174, 245, 0.45);
background: linear-gradient(90deg, rgba(53, 174, 245, 0.10), rgba(53, 174, 245, 0.025));
}
.upgrade-card.third {
border-color: rgba(255,255,255,0.18);
}
.upgrade-rank {
font-size: 0.78rem;
font-weight: 900;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--accent);
margin-bottom: 0.35rem;
}
.upgrade-card.best .upgrade-rank {
color: #4ade80;
}
.upgrade-title {
font-size: 1.05rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.25rem;
}
.upgrade-gain {
font-size: 1.25rem;
font-weight: 900;
color: #9ee7ff;
margin-bottom: 0.55rem;
}
.upgrade-meta-grid {
display: grid;
grid-template-columns: repeat(3, minmax(0, 1fr));
gap: 6px;
margin-bottom: 0.65rem;
}
.upgrade-meta-pill {
border: 1px solid rgba(255,255,255,0.12);
border-radius: 7px;
padding: 6px 7px;
background: rgba(0,0,0,0.12);
}
.upgrade-meta-label {
font-size: 0.66rem;
color: var(--text-muted);
margin-bottom: 0.1rem;
}
.upgrade-meta-value {
font-size: 0.78rem;
font-weight: 900;
color: #ffffff;
}
.upgrade-actions-title {
font-size: 0.78rem;
font-weight: 900;
color: #ffffff;
margin-top: 0.45rem;
margin-bottom: 0.25rem;
}
.upgrade-actions {
margin: 0.2rem 0 0 1rem;
padding: 0;
font-size: 0.8rem;
line-height: 1.45;
color: #d6d6d6;
}
.upgrade-actions li {
margin-bottom: 0.15rem;
}
.upgrade-note {
margin-top: 0.75rem;
font-size: 0.82rem;
color: var(--text-muted);
}


.placeholder-block {
margin-top: 1rem;
padding: 10px 12px;
border: 1px dashed rgba(255,255,255,0.16);
border-radius: 8px;
color: var(--text-muted);
font-size: 0.86rem;
}

/* Make scenario columns feel like two separate dashboards. */
div[data-testid="column"]:has(.ride-title-card) {
background: var(--scenario-panel);
border: 1px solid rgba(255,255,255,0.07);
border-radius: 12px;
padding: 18px 22px 28px 22px;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.025);
}

/* Subtle center divider between Ride A and Ride B. */
div[data-testid="column"]:has(.ride-title-card):first-of-type {
border-right: 1px solid rgba(255,255,255,0.18);
}

.stSlider, .stSelectbox {
margin-bottom: 0.55rem;
}

.route-intelligence-grid {
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 8px;
margin: 0.75rem 0 0.35rem 0;
}

.route-intelligence-card {
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 0.65rem;
background: rgba(53,174,245,0.035);
}

.route-intelligence-section-title {
color: var(--accent);
font-size: 0.78rem;
font-weight: 800;
letter-spacing: 0.11rem;
text-transform: uppercase;
margin-top: 0.95rem;
margin-bottom: 0.35rem;
}

.route-intelligence-wide-card {
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 0.75rem;
background: rgba(53,174,245,0.045);
margin: 0.75rem 0 0.35rem 0;
}

.route-intelligence-subtle {
color: var(--text-muted);
font-size: 0.82rem;
margin-top: 0.3rem;
}

.route-intelligence-empty {
border: 1px dashed var(--border);
border-radius: 8px;
padding: 0.75rem;
color: var(--text-muted);
background: rgba(255,255,255,0.025);
margin-top: 0.75rem;
}

.route-intelligence-note {
color: var(--text-muted);
font-size: 0.82rem;
margin-bottom: 1rem;
}

</style>
"""
)


# ==========================================================
# FIXED TOP — IDENTITY
# ==========================================================

render_html(
    """
<div class="fixed-top">
<h1>Bike Science Pro</h1>
<p>Model scenarios. Compare outcomes. Make better decisions.</p>
<div class="top-cards">
<div class="info-card"><b>What is it?</b><br><br>A physics-based decision cockpit for cyclists.</div>
<div class="info-card"><b>Compare riders</b><br><br>Who is faster on the same route, and why?</div>
<div class="info-card"><b>Compare setups</b><br><br>What changes if you alter weight, tires, position or fitness?</div>
<div class="info-card"><b>Compare routes</b><br><br>Which ride better fits this rider and setup?</div>
</div>
</div>
"""
)


# ==========================================================
# FIXED LEFT — NAVIGATION
# ==========================================================

render_html(
    """
<div class="fixed-left">
<h3>Navigation</h3>
<div class="nav-note">Architecture guide</div>
<div class="nav-item">Rider</div>
<div class="nav-item">Bike</div>
<div class="nav-item">Weather</div>
<div class="nav-item">Surface</div>
<div class="nav-item">Ride Comparison</div>
</div>
"""
)


# ==========================================================
# CENTER — RIDE A / RIDE B
# Navigation is intentionally static in this iteration. It serves as a layout placeholder.
# ==========================================================


def ride_briefing(summary: dict) -> None:
    if not summary.get("ready", True):
        render_html(
            f"""
<div class="route-intelligence-empty">
<b>Ride Briefing</b><br>
{summary.get('engine_mode', 'Upload GPX or choose demo route to calculate this ride.')}
</div>
"""
        )
        return

    render_html(
        f"""
<div class="briefing-grid">
<div class="briefing-card"><div class="briefing-label">Distance</div><div class="briefing-value">{summary['distance_km']:.1f} km</div></div>
<div class="briefing-card"><div class="briefing-label">Duration</div><div class="briefing-value">{format_duration(summary['duration_h'])}</div></div>
<div class="briefing-card"><div class="briefing-label">Avg speed</div><div class="briefing-value">{summary['speed_kmh']:.1f} km/h</div></div>
<div class="briefing-card"><div class="briefing-label">Calories</div><div class="briefing-value">{summary['calories']:.0f} kcal</div></div>
<div class="briefing-card"><div class="briefing-label">Carbs</div><div class="briefing-value">{summary['carbs_g']:.0f} g</div></div>
<div class="briefing-card"><div class="briefing-label">Fluids</div><div class="briefing-value">{summary['fluid_goal_l']:.1f} L</div></div>
<div class="briefing-card"><div class="briefing-label">Sodium</div><div class="briefing-value">{summary['sodium_mg']:.0f} mg</div></div>
<div class="briefing-card"><div class="briefing-label">Refills</div><div class="briefing-value">{summary['refills']}</div></div>
</div>
<div class="briefing-note">Phase 6.1 route engine: {summary.get("engine_mode", "engine mode unknown")}.</div>
"""
    )


def build_recommendations(inputs: dict, summary: dict) -> dict:
    """Temporary v2 recommendations model.

    This is intentionally simple. Later it should call the real recommendation
    logic from v1 once the v2 scenario engine is connected to the simulator.
    """
    if not summary.get("ready", True):
        return {
            "Route": [
                "Upload a GPX file or choose the generated demo route.",
                "Ride recommendations will appear once a route is selected.",
            ]
        }

    duration_h = summary["duration_h"]
    carbs_per_h = summary["carbs_g"] / duration_h
    bottles_needed = 2 if summary["fluid_goal_l"] <= 1.5 else 3

    if inputs["temperature"] >= 25:
        hydration_heat_note = "Increase fluid intake because this is a warm ride."
    else:
        hydration_heat_note = "Hydration demand looks manageable in these conditions."

    if inputs["wind"] >= 20:
        pacing_wind_note = "Avoid early surges; wind can make pacing errors expensive."
    else:
        pacing_wind_note = "Steady pacing should work well in these wind conditions."

    if inputs["surface"] in ["Mixed gravel", "Rough"]:
        tire_note = "Prioritize grip and comfort over pure rolling speed."
    else:
        tire_note = "Fast gravel tires are likely a sensible choice."

    if inputs["fitness"] >= 3.5:
        pacing_note = "Fitness supports a more assertive pacing strategy."
    else:
        pacing_note = "Keep effort controlled and avoid burning matches early."

    return {
        "Nutrition": [
            "Start fueling after the first 30 minutes.",
            f"Target roughly {carbs_per_h:.0f} g carbohydrates per hour.",
            "Eat consistently every 20 minutes rather than waiting until hungry.",
        ],
        "Hydration": [
            f"Plan around {summary['fluid_goal_l']:.1f} L total fluid.",
            f"Carry at least {bottles_needed} bottle{'s' if bottles_needed > 1 else ''} or plan a refill.",
            hydration_heat_note,
        ],
        "Pacing": [
            pacing_note,
            pacing_wind_note,
            "Keep power smooth on climbs and avoid repeated spikes.",
        ],
        "Equipment": [
            tire_note,
            "Current drivetrain setup is assumed sufficient for this placeholder model.",
            "Review gearing again once real segment-level simulation is connected.",
        ],
    }


def ride_recommendations(inputs: dict, summary: dict) -> None:
    recommendations = build_recommendations(inputs, summary)

    cards_html = ""
    for category, items in recommendations.items():
        items_html = "".join(f"<li>{item}</li>" for item in items)
        cards_html += f"""
<div class="recommendation-card">
<div class="recommendation-title">{category}</div>
<ul>{items_html}</ul>
</div>
"""

    render_html(
        f"""
<div class="recommendation-grid">
{cards_html}
</div>
<div class="recommendation-note">Phase 7.2 recommendations generated from the real v1 engine summary and selected route.</div>
"""
    )



def build_performance_analysis(inputs: dict, summary: dict) -> list[dict]:
    """Phase 3.3 Scale of Influence model.

    Instead of hard-coding performance bars directly, this function now
    re-runs the same engine adapter with standardized improvement scenarios.

    Once the real v1 simulator is connected inside run_ride_engine(...),
    these bars will automatically become route-specific simulation outputs.
    """
    if not summary.get("ready", True):
        return [
            {"label": "Route required", "detail": "select GPX or demo route", "value": 0.0}
        ]

    baseline_duration_h = summary["duration_h"]

    scenarios = [
        {
            "label": "Rider Power",
            "detail": "+10 W benchmark",
            "updates": {"fitness": inputs["fitness"] + 10 / inputs["rider_mass"]},
        },
        {
            "label": "Aerodynamics",
            "detail": "5% improvement",
            "updates": {"aero_gain_pct": 5},
        },
        {
            "label": "Body Weight",
            "detail": "−3 kg benchmark",
            "updates": {"rider_mass": max(40, inputs["rider_mass"] - 3)},
        },
        {
            "label": "Rolling Resistance",
            "detail": "10% tire improvement",
            "updates": {"rolling_resistance_gain_pct": 10},
        },
        {
            "label": "Bike Weight",
            "detail": "−0.5 kg benchmark",
            "updates": {"bike_mass": max(5.0, inputs["bike_mass"] - 0.5)},
        },
    ]

    performance = []

    for scenario in scenarios:
        scenario_inputs = inputs.copy()
        scenario_inputs.update(scenario["updates"])
        scenario_summary = run_ride_engine(scenario_inputs)
        minutes_saved = max(0, (baseline_duration_h - scenario_summary["duration_h"]) * 60)

        performance.append(
            {
                "label": scenario["label"],
                "detail": scenario["detail"],
                "value": minutes_saved,
            }
        )

    return performance



def build_opportunity_engine(performance: list[dict]) -> list[dict]:
    """Phase 9.1 Opportunity Engine.

    Converts raw Scale of Influence bars into action-oriented improvement
    opportunities. Impact comes from real engine re-runs; effort, cost and
    payoff labels are transparent heuristics for decision support.
    """
    effort_map = {
        "Rider Power": {
            "effort": "high",
            "effort_score": 4,
            "cost": "training time",
            "action": "Structured training block, better pacing discipline, or more consistent training.",
            "package": "Fitness package",
        },
        "Aerodynamics": {
            "effort": "low/medium",
            "effort_score": 2,
            "cost": "position work",
            "action": "Improve riding position, clothing, cockpit setup, or bike fit.",
            "package": "Aero package",
        },
        "Rolling Resistance": {
            "effort": "low",
            "effort_score": 1,
            "cost": "tires / pressure",
            "action": "Review tires, pressure, casing, and tubeless setup.",
            "package": "Tire package",
        },
        "Body Weight": {
            "effort": "high",
            "effort_score": 4,
            "cost": "months",
            "action": "Long-term body composition change, not a quick ride-day lever.",
            "package": "Body composition package",
        },
        "Bike Weight": {
            "effort": "medium/high",
            "effort_score": 3,
            "cost": "equipment spend",
            "action": "Lower priority unless the route is climbing-heavy or the upgrade is cheap.",
            "package": "Equipment package",
        },
        "Route required": {
            "effort": "n/a",
            "effort_score": 99,
            "cost": "n/a",
            "action": "Select a route first.",
            "package": "Route setup",
        },
    }

    def payoff_label(value: float) -> str:
        if value >= 3.0:
            return "High"
        if value >= 1.0:
            return "Medium"
        if value > 0:
            return "Low"
        return "None"

    def roi_label(score: float) -> str:
        if score >= 1.5:
            return "Strong"
        if score >= 0.6:
            return "Good"
        if score > 0:
            return "Low"
        return "None"

    opportunities = []
    for item in performance:
        value = float(item.get("value", 0.0))
        info = effort_map.get(
            item["label"],
            {
                "effort": "unknown",
                "effort_score": 3,
                "cost": "unknown",
                "action": "Review this lever.",
                "package": item["label"],
            },
        )

        effort_score = info["effort_score"]
        roi_score = value / effort_score if effort_score else value
        opportunities.append(
            {
                "label": item["label"],
                "package": info["package"],
                "impact_min": value,
                "payoff": payoff_label(value),
                "effort": info["effort"],
                "cost": info["cost"],
                "action": info["action"],
                "roi_score": roi_score,
                "roi_label": roi_label(roi_score),
            }
        )

    return sorted(opportunities, key=lambda x: (x["roi_score"], x["impact_min"]), reverse=True)


def render_opportunity_engine(performance: list[dict]) -> None:
    opportunities = build_opportunity_engine(performance)
    opportunities = [item for item in opportunities if item["impact_min"] > 0][:4]

    if not opportunities:
        render_html(
            """
<div class="opportunity-section-title">Opportunity Engine</div>
<div class="performance-insight"><b>Next best action:</b> Select a route and scenario inputs to calculate ranked opportunities.</div>
"""
        )
        return

    top = opportunities[0]

    cards_html = ""
    for idx, item in enumerate(opportunities, start=1):
        css_class = "priority-1" if idx == 1 else "priority-2" if idx == 2 else "priority-low"

        cards_html += f"""
<div class="opportunity-card {css_class}">
<div class="opportunity-rank">Opportunity #{idx}</div>
<div class="opportunity-title">{item['label']}</div>

<div class="opportunity-decision-grid">
    <div class="opportunity-pill">
        <div class="opportunity-pill-label">Payoff</div>
        <div class="opportunity-pill-value">{item['payoff']}</div>
    </div>
    <div class="opportunity-pill">
        <div class="opportunity-pill-label">Effort</div>
        <div class="opportunity-pill-value">{item['effort']}</div>
    </div>
    <div class="opportunity-pill">
        <div class="opportunity-pill-label">ROI</div>
        <div class="opportunity-pill-value">{item['roi_label']}</div>
    </div>
</div>

<div class="opportunity-meta">
    <b>Modeled gain:</b> {item['impact_min']:.1f} min<br>
    <b>Cost type:</b> {item['cost']}<br>
    <b>Package:</b> {item['package']}
</div>
<div class="opportunity-meta" style="margin-top:0.45rem;">{item['action']}</div>
</div>
"""

    render_html(
        f"""
<div class="opportunity-section-title">Opportunity Engine</div>

<div class="opportunity-focus">
    <div class="opportunity-focus-title">Biggest opportunity</div>
    <div class="opportunity-focus-main">Improve {top['label'].lower()} first.</div>
    <div class="opportunity-meta">
        Expected gain: <b>≈{top['impact_min']:.1f} minutes</b>. 
        This has a <b>{top['payoff'].lower()}</b> modeled payoff with <b>{top['effort']}</b> effort.
        Typical path: {top['action']}
    </div>
</div>

<div class="opportunity-portfolio-grid">
{cards_html}
</div>

<div class="opportunity-note">Phase 9.1 Opportunity Portfolio ranks levers by payoff vs effort, not modeled time alone. Impact still comes from real v1 engine re-runs.</div>
"""
    )
    render_upgrade_advisor(opportunities)


def build_upgrade_advisor(opportunities: list[dict]) -> list[dict]:
    """Phase 9.1 Upgrade Advisor.

    Converts ranked opportunities into human action cards. The modeled gain
    still comes from the real engine; difficulty/cost/time are practical
    heuristics intended to make the decision easier to understand.
    """
    action_library = {
        "Aerodynamics": {
            "difficulty": "Easy",
            "cost": "Low",
            "time": "Immediate",
            "actions": [
                "Tighter clothing",
                "Improve riding position",
                "Cockpit or handlebar setup",
                "Bike fit check",
            ],
        },
        "Rolling Resistance": {
            "difficulty": "Easy",
            "cost": "Low",
            "time": "Immediate",
            "actions": [
                "Optimize tire pressure",
                "Consider faster tire casing",
                "Review tubeless or TPU setup",
                "Check tire choice for surface",
            ],
        },
        "Rider Power": {
            "difficulty": "Hard",
            "cost": "Low",
            "time": "Weeks/months",
            "actions": [
                "Structured threshold block",
                "VO₂ max intervals",
                "Improve training consistency",
                "Avoid repeated pacing spikes",
            ],
        },
        "Body Weight": {
            "difficulty": "Hard",
            "cost": "Low",
            "time": "Months",
            "actions": [
                "Long-term body composition work",
                "Protect fueling quality",
                "Avoid crash dieting",
                "Prioritize recovery and consistency",
            ],
        },
        "Bike Weight": {
            "difficulty": "Medium",
            "cost": "High",
            "time": "Immediate",
            "actions": [
                "Prioritize rotating weight only if upgrade is sensible",
                "Review bottle/load strategy",
                "Avoid expensive low-impact upgrades",
                "Consider only if climbing-heavy route",
            ],
        },
    }

    ranked = []
    medals = ["🥇 Best ROI", "🥈 Second best", "🥉 Third best"]
    css_classes = ["best", "second", "third"]

    for idx, item in enumerate(opportunities[:3]):
        label = item["label"]
        profile = action_library.get(
            label,
            {
                "difficulty": item.get("effort", "Medium"),
                "cost": item.get("cost", "Unknown"),
                "time": "Depends",
                "actions": [item.get("action", "Review this lever.")],
            },
        )

        ranked.append(
            {
                "rank": medals[idx],
                "css_class": css_classes[idx],
                "label": label,
                "gain": item.get("impact_min", 0.0),
                "difficulty": profile["difficulty"],
                "cost": profile["cost"],
                "time": profile["time"],
                "actions": profile["actions"],
            }
        )

    return ranked


def render_upgrade_advisor(opportunities: list[dict]) -> None:
    upgrade_cards = build_upgrade_advisor(opportunities)

    if not upgrade_cards:
        return

    cards_html = ""
    for card in upgrade_cards:
        actions_html = "".join(f"<li>{action}</li>" for action in card["actions"])
        cards_html += f"""
<div class="upgrade-card {card['css_class']}">
    <div class="upgrade-rank">{card['rank']}</div>
    <div class="upgrade-title">{card['label']}</div>
    <div class="upgrade-gain">+{card['gain']:.1f} min</div>

    <div class="upgrade-meta-grid">
        <div class="upgrade-meta-pill">
            <div class="upgrade-meta-label">Difficulty</div>
            <div class="upgrade-meta-value">{card['difficulty']}</div>
        </div>
        <div class="upgrade-meta-pill">
            <div class="upgrade-meta-label">Cost</div>
            <div class="upgrade-meta-value">{card['cost']}</div>
        </div>
        <div class="upgrade-meta-pill">
            <div class="upgrade-meta-label">Time</div>
            <div class="upgrade-meta-value">{card['time']}</div>
        </div>
    </div>

    <div class="upgrade-actions-title">Typical actions</div>
    <ul class="upgrade-actions">{actions_html}</ul>
</div>
"""

    render_html(
        f"""
<div class="upgrade-section-title">Upgrade Advisor</div>
<div class="upgrade-advisor-grid">
{cards_html}
</div>
<div class="upgrade-note">Phase 9.1 translates modeled opportunities into concrete actions, while keeping Scale of Influence as the calculation source.</div>
"""
    )

def ride_performance_analysis(inputs: dict, summary: dict) -> None:
    performance = build_performance_analysis(inputs, summary)
    performance = sorted(performance, key=lambda item: item["value"], reverse=True)
    max_value = max(item["value"] for item in performance) if performance else 1
    top = performance[0]
    second = performance[1] if len(performance) > 1 else None

    rows_html = ""
    for item in performance:
        width_pct = 0 if max_value == 0 else item["value"] / max_value * 100
        rows_html += f"""
<div class="performance-row">
<div class="performance-head">
<span>{item['label']} <span style="color:#a9a9a9;font-weight:600;">({item['detail']})</span></span>
<span class="performance-value">{item['value']:.1f} min</span>
</div>
<div class="performance-track"><div class="performance-fill" style="width:{width_pct:.0f}%;"></div></div>
</div>
"""

    if second:
        ratio_pct = (top["value"] / second["value"] - 1) * 100 if second["value"] else 0
        insight = (
            f"{top['label']} is the strongest modeled lever in this scenario, "
            f"about {ratio_pct:.0f}% stronger than {second['label']} "
            f"({top['value']:.1f} vs {second['value']:.1f} min)."
        )
    else:
        insight = "Performance analysis will compare modeled improvement levers for this ride."

    render_html(
        f"""
<div class="performance-list">
{rows_html}
</div>
<div class="performance-insight"><b>Key insight:</b> {insight}</div>
<div class="performance-note">Phase 7.2 Scale of Influence generated by re-running standardized improvements through the real v1 engine and selected route.</div>
"""
    )
    render_opportunity_engine(performance)

def ride_panel(
    label: str,
    subtitle: str,
    defaults: dict,
    ride_a_segments: pd.DataFrame | None = None,
) -> tuple[dict, dict, pd.DataFrame]:
    render_html(
        f"""
<div class="ride-title-card">
<h2>Ride {label}</h2>
<p>{subtitle}</p>
</div>
"""
    )

    with st.container(border=True):
        render_html(
            '''
<div class="zone-title-row">
<div class="input-zone-marker">Input Zone</div>
</div>
<div class="zone-subtitle">Define route, rider, bike, weather and surface assumptions for this ride.</div>
'''
        )

        st.subheader("Route")

        if label == "A":
            route_options = ["Upload GPX", "Generated demo route"]
            route_default_index = 0
        else:
            route_options = ["Same as Ride A", "Upload GPX", "Generated demo route"]
            route_default_index = 0

        route_mode = st.selectbox(
            f"Route source {label}",
            route_options,
            index=route_default_index,
            key=f"{label}_route_mode",
        )

        uploaded_gpx = st.file_uploader(
            f"GPX file {label}",
            type=["gpx"],
            key=f"{label}_gpx_upload",
            help="Upload a GPX route. No demo data is used unless you explicitly choose the generated demo route.",
        )

        segments_df, route_description = resolve_route_segments(
            route_mode=route_mode,
            uploaded_file=uploaded_gpx,
            fallback_segments=ride_a_segments,
        )

        st.caption(f"Route used: {route_description}")
        render_route_intelligence(segments_df, route_description)

        st.subheader("Rider")

        rider_mass = st.slider(
            f"Rider mass {label} (kg)",
            min_value=40,
            max_value=150,
            value=defaults["rider_mass"],
            key=f"{label}_rider_mass",
        )

        fitness = st.slider(
            f"Fitness {label} (W/kg)",
            min_value=1.0,
            max_value=7.0,
            value=defaults["fitness"],
            step=0.1,
            key=f"{label}_fitness",
        )

        riding_style = st.selectbox(
            f"Riding style {label}",
            ["Endurance", "Upright", "Aggressive"],
            key=f"{label}_riding_style",
        )

        st.subheader("Bike")

        bike_mass = st.slider(
            f"Bike mass {label} (kg)",
            min_value=5.0,
            max_value=20.0,
            value=defaults["bike_mass"],
            step=0.5,
            key=f"{label}_bike_mass",
        )

        tires = st.selectbox(
            f"Tires {label}",
            ["Fast gravel", "Mixed gravel", "Rough gravel"],
            key=f"{label}_tires",
        )

        drivetrain = st.selectbox(
            f"Drivetrain {label}",
            ["1x Gravel", "2x Road", "MTB wide range"],
            key=f"{label}_drivetrain",
        )

        st.subheader("Weather")

        temperature = st.slider(
            f"Temperature {label} (°C)",
            min_value=-10,
            max_value=45,
            value=defaults["temperature"],
            key=f"{label}_temperature",
        )

        humidity = st.slider(
            f"Humidity {label} (%)",
            min_value=0,
            max_value=100,
            value=defaults["humidity"],
            key=f"{label}_humidity",
        )

        wind = st.slider(
            f"Wind {label} (km/h)",
            min_value=0,
            max_value=80,
            value=defaults["wind"],
            key=f"{label}_wind",
        )

        st.subheader("Surface")

        surface = st.selectbox(
            f"Surface {label}",
            ["Smooth", "Normal", "Mixed gravel", "Rough"],
            key=f"{label}_surface",
        )

    inputs = {
        "rider_mass": rider_mass,
        "fitness": fitness,
        "riding_style": riding_style,
        "bike_mass": bike_mass,
        "tires": tires,
        "drivetrain": drivetrain,
        "temperature": temperature,
        "humidity": humidity,
        "wind": wind,
        "surface": surface,
        "segments_df": segments_df,
        "route_description": route_description,
    }

    summary = run_ride_engine(inputs)

    render_html('<div class="section-divider"></div>')

    with st.container(border=True):
        render_html(
            '''
<div class="zone-title-row">
<div class="outcome-zone-marker">Outcome Zone</div>
</div>
<div class="zone-subtitle">Read the modeled consequences for this ride setup. <span style="color:#35aef5;">Engine adapter active</span></div>
'''
        )
        st.subheader("Ride Comparison")
        st.markdown("#### Ride Briefing")
        ride_briefing(summary)
        st.markdown("#### Recommendations")
        ride_recommendations(inputs, summary)
        st.markdown("#### Performance Analysis")
        ride_performance_analysis(inputs, summary)

    return inputs, summary, segments_df


ride_a, ride_b = st.columns(2, gap="large")

with ride_a:
    inputs_a, summary_a, segments_a = ride_panel(
        label="A",
        subtitle="Current ride setup",
        defaults={
            "rider_mass": 95,
            "fitness": 3.0,
            "bike_mass": 9.0,
            "temperature": 24,
            "humidity": 50,
            "wind": 5,
        },
    )

with ride_b:
    inputs_b, summary_b, segments_b = ride_panel(
        label="B",
        subtitle="Alternative ride setup",
        defaults={
            "rider_mass": 92,
            "fitness": 3.1,
            "bike_mass": 8.5,
            "temperature": 24,
            "humidity": 50,
            "wind": 5,
        },
        ride_a_segments=segments_a,
    )


# ==========================================================
# PHASE 4.1 — DIFFERENCES ADAPTER
# Keep comparison logic isolated so Phase 4.2 can swap in real v1 outputs.
# ==========================================================


def calculate_ride_differences(summary_a: dict, summary_b: dict) -> dict:
    """Normalize Ride B vs Ride A differences for the bottom decision dock."""
    if not summary_a.get("ready", True) or not summary_b.get("ready", True):
        return {
            key: {"value": "—", "delta": 0, "unit": "", "decimals": 0, "lower_is_better": False}
            for key in ["distance", "duration", "speed", "carbs", "fluids", "sodium"]
        }

    distance_delta = summary_b["distance_km"] - summary_a["distance_km"]
    duration_delta_min = (summary_b["duration_h"] - summary_a["duration_h"]) * 60
    speed_delta = summary_b["speed_kmh"] - summary_a["speed_kmh"]
    carbs_delta = summary_b["carbs_g"] - summary_a["carbs_g"]
    fluid_delta = summary_b["fluid_goal_l"] - summary_a["fluid_goal_l"]
    sodium_delta = summary_b["sodium_mg"] - summary_a["sodium_mg"]

    same_distance = abs(distance_delta) < 0.01

    return {
        "distance": {
            "value": "Same" if same_distance else f"{summary_b['distance_km']:.1f} km",
            "delta": distance_delta,
            "unit": "km",
            "decimals": 1,
            "lower_is_better": False,
        },
        "duration": {
            "value": format_duration(summary_b["duration_h"]),
            "delta": duration_delta_min,
            "unit": "min",
            "decimals": 0,
            "lower_is_better": True,
        },
        "speed": {
            "value": f"{summary_b['speed_kmh']:.1f} km/h",
            "delta": speed_delta,
            "unit": "km/h",
            "decimals": 1,
            "lower_is_better": False,
        },
        "carbs": {
            "value": f"{summary_b['carbs_g']:.0f} g",
            "delta": carbs_delta,
            "unit": "g",
            "decimals": 0,
            "lower_is_better": True,
        },
        "fluids": {
            "value": f"{summary_b['fluid_goal_l']:.1f} L",
            "delta": fluid_delta,
            "unit": "L",
            "decimals": 1,
            "lower_is_better": True,
        },
        "sodium": {
            "value": f"{summary_b['sodium_mg']:.0f} mg",
            "delta": sodium_delta,
            "unit": "mg",
            "decimals": 0,
            "lower_is_better": True,
        },
    }


def render_difference_card(label: str, item: dict) -> str:
    """Render one normalized difference card."""
    return f"""
<div class="diff-card">
<div class="diff-label">{label}</div>
<div class="diff-value">{item['value']}</div>
<div class="{delta_class(item['delta'], lower_is_better=item['lower_is_better'])}">{'select route' if not item.get('unit') else signed_delta(item['delta'], item['unit'], item['decimals'], lower_is_better=item['lower_is_better'])}</div>
</div>
"""




def input_changed(inputs_a: dict, inputs_b: dict, key: str, tolerance: float = 0.0) -> bool:
    """Compare two input values with optional numeric tolerance."""
    value_a = inputs_a.get(key)
    value_b = inputs_b.get(key)

    if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
        return abs(value_a - value_b) > tolerance

    return value_a != value_b


def detect_comparison_context(inputs_a: dict, inputs_b: dict) -> dict:
    """Phase 9: infer comparison intent from scenario differences."""
    route_a = inputs_a.get("route_description")
    route_b = inputs_b.get("route_description")
    same_route = route_a == route_b

    rider_changed = any(
        [
            input_changed(inputs_a, inputs_b, "rider_mass"),
            input_changed(inputs_a, inputs_b, "fitness", tolerance=0.01),
            input_changed(inputs_a, inputs_b, "riding_style"),
        ]
    )

    bike_changed = any(
        [
            input_changed(inputs_a, inputs_b, "bike_mass", tolerance=0.01),
            input_changed(inputs_a, inputs_b, "tires"),
            input_changed(inputs_a, inputs_b, "drivetrain"),
        ]
    )

    conditions_changed = any(
        [
            input_changed(inputs_a, inputs_b, "temperature"),
            input_changed(inputs_a, inputs_b, "humidity"),
            input_changed(inputs_a, inputs_b, "wind"),
            input_changed(inputs_a, inputs_b, "surface"),
        ]
    )

    changed_groups = [
        name
        for name, changed in [
            ("route", not same_route),
            ("rider", rider_changed),
            ("bike", bike_changed),
            ("weather/surface", conditions_changed),
        ]
        if changed
    ]

    if not changed_groups:
        mode = "Simulation baseline"
        question = "What does this ride look like?"
        focus = "Ride briefing, fueling, hydration and route character."
    elif same_route and rider_changed and not bike_changed and not conditions_changed:
        mode = "Rider comparison"
        question = "How do rider attributes affect the same route?"
        focus = "Performance gap, power-to-weight, fueling demand and rider suitability."
    elif same_route and bike_changed and not rider_changed and not conditions_changed:
        mode = "Setup comparison"
        question = "Which bike or equipment setup performs better?"
        focus = "Equipment impact, rolling resistance, bike mass and aerodynamic assumptions."
    elif same_route and (rider_changed or bike_changed or conditions_changed):
        mode = "What-if optimization"
        question = "What changes if this rider or setup improves?"
        focus = "Time saved, practical levers, and whether changes are worth pursuing."
    elif not same_route and not rider_changed and not bike_changed:
        mode = "Route suitability"
        question = "Which route better fits this rider and setup?"
        focus = "Route character, difficulty, fueling demand, and expected ride outcome."
    elif not same_route and (rider_changed or bike_changed):
        mode = "General scenario comparison"
        question = "Which scenario performs better, and why?"
        focus = "Outcome differences across route, rider and setup assumptions."
    else:
        mode = "Scenario comparison"
        question = "What changed between Ride A and Ride B?"
        focus = "Key deltas and the most likely drivers of the difference."

    reason_bits = ["same route" if same_route else "different routes"]

    if rider_changed:
        reason_bits.append("rider changed")
    if bike_changed:
        reason_bits.append("bike/setup changed")
    if conditions_changed:
        reason_bits.append("weather/surface changed")
    if len(reason_bits) == 1:
        reason_bits.append("no major setup changes")

    return {
        "mode": mode,
        "question": question,
        "focus": focus,
        "reason": " · ".join(reason_bits),
        "changed_groups": changed_groups,
    }


def render_decision_context(inputs_a: dict, inputs_b: dict) -> str:
    """Render compact context-aware explanation for the differences dock."""
    context = detect_comparison_context(inputs_a, inputs_b)

    return f"""
<div class="decision-context">
    <div class="decision-context-title">Decision Engine</div>
    <div class="decision-context-main">{context['mode']}: {context['question']}</div>
    <div class="decision-context-meta">
        Detected from inputs: {context['reason']}.<br>
        Analysis focus: {context['focus']}
    </div>
</div>
"""

def build_scenario_verdict(summary_a: dict, summary_b: dict, inputs_a: dict, inputs_b: dict) -> str:
    """Create a compact human-readable comparison of Ride B vs Ride A."""
    if not summary_a.get("ready", True) or not summary_b.get("ready", True):
        return "<b>Scenario comparison:</b> Select a route for Ride A and Ride B to compare outcomes. Upload GPX or explicitly choose the generated demo route."

    context = detect_comparison_context(inputs_a, inputs_b)
    differences = calculate_ride_differences(summary_a, summary_b)

    duration_delta = differences["duration"]["delta"]
    speed_delta = differences["speed"]["delta"]
    carbs_delta = differences["carbs"]["delta"]
    fluid_delta = differences["fluids"]["delta"]

    if duration_delta < -0.5:
        time_phrase = f"Ride B is {abs(duration_delta):.0f} min faster"
    elif duration_delta > 0.5:
        time_phrase = f"Ride B is {duration_delta:.0f} min slower"
    else:
        time_phrase = "Ride B is effectively the same duration"

    if speed_delta > 0.1:
        speed_phrase = f"averaging {speed_delta:.1f} km/h more"
    elif speed_delta < -0.1:
        speed_phrase = f"averaging {abs(speed_delta):.1f} km/h less"
    else:
        speed_phrase = "with similar average speed"

    if carbs_delta < -1 or fluid_delta < -0.05:
        demand_phrase = "with lower fueling or hydration demand"
    elif carbs_delta > 1 or fluid_delta > 0.05:
        demand_phrase = "but with higher fueling or hydration demand"
    else:
        demand_phrase = "with similar fueling and hydration demand"

    setup_changes = []
    if inputs_a["rider_mass"] != inputs_b["rider_mass"]:
        setup_changes.append(f"rider mass {inputs_a['rider_mass']} → {inputs_b['rider_mass']} kg")
    if inputs_a["fitness"] != inputs_b["fitness"]:
        setup_changes.append(f"fitness {inputs_a['fitness']:.1f} → {inputs_b['fitness']:.1f} W/kg")
    if inputs_a["riding_style"] != inputs_b["riding_style"]:
        setup_changes.append(f"position {inputs_a['riding_style']} → {inputs_b['riding_style']}")
    if inputs_a["bike_mass"] != inputs_b["bike_mass"]:
        setup_changes.append(f"bike mass {inputs_a['bike_mass']:.1f} → {inputs_b['bike_mass']:.1f} kg")
    if inputs_a["tires"] != inputs_b["tires"]:
        setup_changes.append(f"tires {inputs_a['tires']} → {inputs_b['tires']}")
    if inputs_a["surface"] != inputs_b["surface"]:
        setup_changes.append(f"surface {inputs_a['surface']} → {inputs_b['surface']}")

    setup_phrase = "; ".join(setup_changes[:3]) if setup_changes else "same key setup assumptions"

    return (
        f"<b>{context['mode']}:</b> {time_phrase}, {speed_phrase}, {demand_phrase}. "
        f"Main change: {setup_phrase}."
    )

def render_differences_panel(summary_a: dict, summary_b: dict, inputs_a: dict, inputs_b: dict) -> None:
    """Render the fixed bottom decision dock from normalized differences."""
    differences = calculate_ride_differences(summary_a, summary_b)
    verdict = build_scenario_verdict(summary_a, summary_b, inputs_a, inputs_b)

    cards_html = "".join(
        [
            render_difference_card("Distance", differences["distance"]),
            render_difference_card("Duration", differences["duration"]),
            render_difference_card("Speed", differences["speed"]),
            render_difference_card("Carbs", differences["carbs"]),
            render_difference_card("Fluids", differences["fluids"]),
            render_difference_card("Sodium", differences["sodium"]),
        ]
    )

    render_html(
        f"""
<div class="fixed-bottom">
<h2>Differences</h2>
<div class="bottom-caption">Compare Ride B against Ride A.</div>
{render_decision_context(inputs_a, inputs_b)}
<div class="scenario-verdict">{verdict}</div>
<div class="diff-grid">
{cards_html}
</div>
<div class="bottom-tabs">
<div class="bottom-tab active">Ride Briefing</div>
<div class="bottom-tab">Recommendations</div>
<div class="bottom-tab">Performance Analysis</div>
</div>
</div>
"""
    )


render_differences_panel(summary_a, summary_b, inputs_a, inputs_b)
