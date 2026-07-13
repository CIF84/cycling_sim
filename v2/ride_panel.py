from collections.abc import Callable

import pandas as pd
import streamlit as st

from v2.scenario_model import build_scenario_inputs


SECTION_DEFAULTS_BY_INTENT = {
    "general": {
        "route": True,
        "rider": True,
        "bike": True,
        "weather": True,
        "surface": True,
    },
    "compare_riders": {
        "route": True,
        "rider": True,
        "bike": False,
        "weather": False,
        "surface": False,
    },
    "compare_setups": {
        "route": True,
        "rider": False,
        "bike": True,
        "weather": False,
        "surface": False,
    },
    "compare_routes": {
        "route": True,
        "rider": False,
        "bike": False,
        "weather": False,
        "surface": False,
    },
    "plan_fueling": {
        "route": True,
        "rider": True,
        "bike": False,
        "weather": True,
        "surface": False,
    },
    "hack_ride": {
        "route": True,
        "rider": True,
        "bike": True,
        "weather": False,
        "surface": False,
    },
}


def get_section_defaults(intent: str) -> dict[str, bool]:
    return SECTION_DEFAULTS_BY_INTENT.get(intent, SECTION_DEFAULTS_BY_INTENT["general"]).copy()


def _gpx_state_keys(label: str) -> tuple[str, str]:
    ride_key = label.lower()
    return f"ride_{ride_key}_gpx_bytes", f"ride_{ride_key}_gpx_filename"


def _persist_uploaded_gpx(label: str, uploaded_gpx) -> tuple[bytes | None, str | None]:
    bytes_key, filename_key = _gpx_state_keys(label)

    if uploaded_gpx is not None:
        st.session_state[bytes_key] = uploaded_gpx.getvalue()
        st.session_state[filename_key] = uploaded_gpx.name

    return st.session_state.get(bytes_key), st.session_state.get(filename_key)


def ride_panel(
    label: str,
    subtitle: str,
    defaults: dict,
    ride_a_segments: pd.DataFrame | None = None,
    *,
    render_html: Callable[[str], None],
    resolve_route_segments: Callable,
    render_route_intelligence: Callable[[pd.DataFrame | None, str], None],
    run_ride_engine: Callable[[dict], dict],
    selected_intent: str = "general",
) -> tuple[dict, dict, pd.DataFrame]:
    section_defaults = get_section_defaults(selected_intent)

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

        with st.expander("Route", expanded=section_defaults["route"]):

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

            uploaded_gpx_bytes, uploaded_gpx_filename = _persist_uploaded_gpx(label, uploaded_gpx)

            segments_df, route_description = resolve_route_segments(
                route_mode=route_mode,
                fallback_segments=ride_a_segments,
                uploaded_bytes=uploaded_gpx_bytes,
                uploaded_filename=uploaded_gpx_filename,
            )

            st.caption(f"Route used: {route_description}")
            render_route_intelligence(segments_df, route_description)

        with st.expander("Rider", expanded=section_defaults["rider"]):

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

        with st.expander("Bike", expanded=section_defaults["bike"]):

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

        with st.expander("Weather", expanded=section_defaults["weather"]):

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

        with st.expander("Surface", expanded=section_defaults["surface"]):

            surface = st.selectbox(
                f"Surface {label}",
                ["Smooth", "Normal", "Mixed gravel", "Rough"],
                key=f"{label}_surface",
            )

    inputs = build_scenario_inputs(
        rider_mass=rider_mass,
        fitness=fitness,
        riding_style=riding_style,
        bike_mass=bike_mass,
        tires=tires,
        drivetrain=drivetrain,
        temperature=temperature,
        humidity=humidity,
        wind=wind,
        surface=surface,
        segments_df=segments_df,
        route_description=route_description,
    )

    summary = run_ride_engine(inputs)

    return inputs, summary, segments_df
