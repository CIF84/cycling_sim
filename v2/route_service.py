import math
import tempfile

import pandas as pd
import streamlit as st

from v2.engine_adapter import ENGINE_DIAGNOSTICS


try:
    from gpx_utils import load_gpx, build_segments
except Exception as exc:  # keep the UI alive if imports fail
    load_gpx = None
    build_segments = None
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
