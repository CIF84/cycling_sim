import pandas as pd
import streamlit as st


def _render_html(html: str) -> None:
    """Render raw HTML without leading indentation so Streamlit does not treat it as code."""
    cleaned = "\n".join(line.strip() for line in html.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


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
        _render_html(
            f"""
<div class="route-intelligence-empty">
<b>Route intelligence</b><br>
{route_description}. Upload a GPX or choose the demo route to calculate distance, elevation and ride outputs.
</div>
"""
        )
        return

    _render_html(
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

    _render_html(
        """
<div class="route-intelligence-note">Phase 7.2 route intelligence based on modeled segments from the selected route.</div>
"""
    )
