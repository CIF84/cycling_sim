from collections.abc import Callable

import pandas as pd
import streamlit as st

from v2.performance import ride_performance_analysis
from v2.scenario_model import build_scenario_inputs


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
    ride_briefing: Callable[[dict], None],
    ride_recommendations: Callable[[dict, dict], None],
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
