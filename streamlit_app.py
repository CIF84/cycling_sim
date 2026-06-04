import tempfile

import streamlit as st

from gpx_utils import load_gpx, build_segments, build_manual_route
from simulator import simulate_route
from reporting import summarize_ride, build_fueling_plan
from presets import get_surface_crr, get_aero_cda, SURFACE_PRESETS, AERO_PRESETS
from compare import compare_surfaces, compare_aero_positions
from scenario import compare_scenarios
from inverse import estimate_power_for_target_time
from roi import build_roi_table
from cassette import compare_cassettes
from recommendations import build_recommendations

st.set_page_config(
    page_title="Bike Science Pro",
    layout="wide",
)

st.title("Bike Science Pro")
st.caption("Cycling physics, fueling, gearing, and performance ROI simulator")

# ==========================================================
# PRODUCT ORIENTATION
# ==========================================================

card1, card2, card3, card4 = st.columns(4)

with card1:
    st.info(
        """
**What is it?**

Physics-based cycling simulator.
"""
    )

with card2:
    st.info(
        """
**What does it consider?**

Weight, fitness, aero, weather, elevation, surface, gearing.
"""
    )

with card3:
    st.info(
        """
**What does it calculate?**

Ride time, calories, fueling, hydration.
"""
    )

with card4:
    st.info(
        """
**Can I trust it?**

Transparent assumptions, calculations and route-specific estimates.
"""
    )

with st.expander(
    "How does Bike Science Pro work?",
    expanded=False,
):
    st.markdown("""
Bike Science Pro simulates your ride segment-by-segment using:

- Rider and bike weight
- Rider fitness (W/kg)
- Aerodynamics (CdA)
- Surface rolling resistance
- Weather conditions
- Route elevation profile
- Gearing and cadence

The simulator estimates:

- Ride duration
- Calories burned
- Fueling requirements
- Hydration needs

Time Savings estimates how much faster this route could be completed 
if one aspect of rider fitness, body weight, aerodynamics, or equipment improved. 

To make comparisons consistent, the simulator uses several standardized 
benchmark scenarios:

- +10 W rider power
- +20 W rider power
- -5 kg rider weight
- Improved aerodynamics
- Faster rolling tires

These benchmarks are intended to illustrate the relative impact of common improvements on this specific route rather than serve as
personalized recommendations or performance targets.

All estimates are route-specific and should be treated as directional guidance rather than guaranteed outcomes.
""")

# ==========================================================
# SIDEBAR INPUTS
# ==========================================================

st.sidebar.header("Route")

route_mode = st.sidebar.radio(
    "Route mode",
    ["Upload GPX", "Manual route"],
)

uploaded_gpx = None

if route_mode == "Upload GPX":
    uploaded_gpx = st.sidebar.file_uploader(
        "Upload GPX file",
        type=["gpx"],
    )
else:
    distance_km = st.sidebar.number_input(
        "Distance (km)",
        min_value=1.0,
        value=80.0,
        step=1.0,
    )

    elevation_gain_m = st.sidebar.number_input(
        "Elevation gain (m)",
        min_value=0.0,
        value=1200.0,
        step=50.0,
    )


segment_length_m = st.sidebar.slider(
    "Segment length (m)",
    min_value=200,
    max_value=2000,
    value=1000,
    step=100,
)

elevation_smooth_window = st.sidebar.slider(
    "Elevation smoothing window",
    min_value=1,
    max_value=21,
    value=7,
    step=2,
)


st.sidebar.header("Rider & Bike")

rider_mass_kg = st.sidebar.number_input(
    "Rider mass (kg)",
    min_value=40.0,
    max_value=150.0,
    value=95.0,
    step=1.0,
)

bike_mass_kg = st.sidebar.number_input(
    "Bike + gear mass (kg)",
    min_value=5.0,
    max_value=30.0,
    value=9.0,
    step=0.5,
)

fitness_wkg = st.sidebar.number_input(
    "Fitness / sustained power (W/kg)",
    min_value=1.0,
    max_value=7.0,
    value=3.0,
    step=0.1,
)

chainring_teeth = st.sidebar.number_input(
    "Chainring teeth",
    min_value=28,
    max_value=54,
    value=34,
    step=1,
)

cassette_teeth = st.sidebar.number_input(
    "Largest cassette cog",
    min_value=25,
    max_value=52,
    value=32,
    step=1,
)


st.sidebar.header("Conditions")

temp_c = st.sidebar.number_input(
    "Temperature (°C)",
    min_value=-10.0,
    max_value=45.0,
    value=24.0,
    step=1.0,
)

humidity_pct = st.sidebar.number_input(
    "Humidity (%)",
    min_value=0.0,
    max_value=100.0,
    value=50.0,
    step=5.0,
)

wind_kmh = st.sidebar.number_input(
    "Wind speed (km/h)",
    min_value=0.0,
    max_value=80.0,
    value=5.0,
    step=1.0,
)

wind_mode = st.sidebar.selectbox(
    "Wind mode",
    ["head", "tail"],
)


st.sidebar.header("Surface & Aero")

surface_key = st.sidebar.selectbox(
    "Surface",
    list(SURFACE_PRESETS.keys()),
    index=list(SURFACE_PRESETS.keys()).index("mixed_gravel"),
)

aero_key = st.sidebar.selectbox(
    "Aero position",
    list(AERO_PRESETS.keys()),
    index=list(AERO_PRESETS.keys()).index("endurance_road"),
)


st.sidebar.header("Targets")

target_time_h = st.sidebar.number_input(
    "Target time (hours)",
    min_value=0.5,
    max_value=20.0,
    value=3.0,
    step=0.1,
)

bottle_capacity_ml = st.sidebar.number_input(
    "Bottle capacity total (ml)",
    min_value=0,
    max_value=5000,
    value=1500,
    step=250,
)

bottle_sizes_ml = [bottle_capacity_ml]


run_button = st.sidebar.button("Run simulation", type="primary")


# ==========================================================
# ROUTE BUILDER
# ==========================================================

def build_route_from_inputs():
    if route_mode == "Upload GPX":
        if uploaded_gpx is None:
            return None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".gpx") as tmp:
            tmp.write(uploaded_gpx.getvalue())
            tmp_path = tmp.name

        gpx_df = load_gpx(tmp_path)

        return build_segments(
            gpx_df,
            segment_length_m=segment_length_m,
            elevation_smooth_window=elevation_smooth_window,
        )

    return build_manual_route(
        distance_km=distance_km,
        elevation_gain_m=elevation_gain_m,
        segment_length_m=segment_length_m,
    )


# ==========================================================
# MAIN APP
# ==========================================================

if not run_button:
    st.info("Set parameters in the sidebar, then click **Run simulation**.")
    st.stop()


segments = build_route_from_inputs()

if segments is None:
    st.warning("Upload a GPX file first.")
    st.stop()


crr = get_surface_crr(surface_key)
cda = get_aero_cda(aero_key)

sim = simulate_route(
    segments_df=segments,
    rider_mass_kg=rider_mass_kg,
    bike_mass_kg=bike_mass_kg,
    fitness_wkg=fitness_wkg,
    temp_c=temp_c,
    humidity_pct=humidity_pct,
    wind_kmh=wind_kmh,
    wind_mode=wind_mode,
    chainring_teeth=chainring_teeth,
    cassette_teeth=cassette_teeth,
    cda=cda,
    crr=crr,
)

summary = summarize_ride(
    sim_df=sim,
    rider_mass_kg=rider_mass_kg,
    bottle_sizes_ml=bottle_sizes_ml,
)

gear_usage = (
    sim.groupby("selected_cog_teeth")
    .size()
    .reset_index(name="segments")
    .sort_values("selected_cog_teeth")
)

gear_usage["pct_of_route"] = (
    gear_usage["segments"]
    / gear_usage["segments"].sum()
    * 100
)

roi = build_roi_table(
    segments_df=segments,
    rider_mass_kg=rider_mass_kg,
    bike_mass_kg=bike_mass_kg,
    fitness_wkg=fitness_wkg,
    temp_c=temp_c,
    humidity_pct=humidity_pct,
    wind_kmh=wind_kmh,
    wind_mode=wind_mode,
    chainring_teeth=chainring_teeth,
    cassette_teeth=cassette_teeth,
    cda=cda,
    crr=crr,
    bottle_sizes_ml=bottle_sizes_ml,

)

recommendations = build_recommendations(
    ride_summary=summary,
    roi_table=roi,
    gear_usage=gear_usage,
    current_power_w=rider_mass_kg * fitness_wkg,
    current_cda=cda,
    current_crr=crr,
)

# ==========================================================
# RIDE BRIEFING
# ==========================================================

st.divider()
st.header("Ride Briefing")
st.caption(
    "Everything you need to prepare for this specific ride."
)

# ==========================================================
# SUMMARY CARDS
# ==========================================================

st.subheader("How hard is this ride?")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "🚴 Distance",
    f"{summary['distance_km']} km",
    help="Total route distance",
)

col2.metric(
    "⏱ Duration",
    f"{summary['duration_h']} h",
    help="Estimated ride time",
)

col3.metric(
    "⚡ Avg Speed",
    f"{summary['avg_speed_kmh']} km/h",
    help="Estimated average speed",
)

col4.metric(
    "🔥 Calories",
    f"{summary['energy_kcal']} kcal",
    help="Estimated calories burned",
)

st.subheader("What should I bring?")

col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "🍌 Carbs",
    f"{summary['carbs_g']} g",
    help="Estimated carbohydrate requirement",
)

col6.metric(
    "🥤 Fluids",
    f"{summary['fluid_goal_l']} L",
    help="Recommended fluid intake",
)

col7.metric(
    "🧂 Sodium",
    f"{summary['sodium_mg']} mg",
    help="Estimated sodium replacement",
)

col8.metric(
    "🚰 Refills",
    summary["refill_stops"],
    help="Estimated bottle refill stops",
)

# ==========================================================
# TABS
# ==========================================================

st.subheader("Ride Recommendations")

for _, rec in recommendations.iterrows():

    if rec["type"] == "success":
        st.success(
            f"**{rec['title']}**\n\n{rec['summary']}"
        )

    elif rec["type"] == "warning":
        st.warning(
            f"**{rec['title']}**\n\n{rec['summary']}"
        )

    else:
        st.info(
            f"**{rec['title']}**\n\n{rec['summary']}"
        )

    with st.expander("Show analysis"):
        st.write(rec["details"])

# ==========================================================
# PERFORMANCE ANALYSIS
# ==========================================================

st.divider()
st.header("Performance Analysis")
st.caption(
    "Route-specific insights showing which factors have the largest modeled influence on ride time."
)

# ==========================================================
# SCALE OF INFLUENCE
# ==========================================================

st.subheader("Scale of Influence")
st.caption(
    "For this route, rider power and aerodynamics have the largest modeled influence on ride time."
)

st.caption(
    "Results are based on standardized benchmark scenarios and should be treated as directional guidance."
)

roi_categories = {
    "+10 W": "Rider Power",
    "+20 W": "Rider Power",
    "10% aero gain": "Aerodynamics",
    "Fast tires": "Rolling Resistance",
    "-5 kg rider": "Body Weight",
    "-1 kg rider": "Body Weight",
    "-1 kg bike": "Bike Weight",
}

roi_grouped = roi.copy()

roi_grouped["category"] = roi_grouped["change"].map(roi_categories)

roi_grouped = (
    roi_grouped
    .dropna(subset=["category"])
    .groupby("category", as_index=False)["time_saved_min"]
    .max()
    .sort_values("time_saved_min", ascending=False)
)

top = roi_grouped.iloc[0]
second = roi_grouped.iloc[1]
body_weight = roi_grouped[roi_grouped["category"] == "Body Weight"].iloc[0]
bike_weight = roi_grouped[roi_grouped["category"] == "Bike Weight"].iloc[0]

top_vs_second_pct = (
    (top["time_saved_min"] / second["time_saved_min"] - 1) * 100
)

aero = roi_grouped[roi_grouped["category"] == "Aerodynamics"].iloc[0]

aero_vs_body_pct = (
    (aero["time_saved_min"] / body_weight["time_saved_min"] - 1) * 100
)

fitness_vs_bike_ratio = (
    top["time_saved_min"] / bike_weight["time_saved_min"]
)

st.info(
    f"""
**Key Insights**

On this route, **{top['category']}** and **{second['category']}** are the dominant performance factors.  
Weight reduction helps, but bike weight has comparatively little influence on finishing time.

- {top['category']} produces approximately **{top_vs_second_pct:.0f}% greater modeled impact** than {second['category']} ({top['time_saved_min']:.1f} vs {second['time_saved_min']:.1f} min saved).

- Aerodynamics produces approximately **{aero_vs_body_pct:.0f}% greater modeled impact** than reducing 5 kg of body weight ({aero['time_saved_min']:.1f} vs {body_weight['time_saved_min']:.1f} min saved).

- Improving rider fitness produces approximately **{fitness_vs_bike_ratio:.0f}× greater modeled gains** than reducing bike weight ({top['time_saved_min']:.1f} vs {bike_weight['time_saved_min']:.1f} min saved).
"""
)

max_gain = roi_grouped["time_saved_min"].max()

rank_icons = ["①", "②", "③", "④", "⑤"]

for rank, (_, row) in enumerate(roi_grouped.iterrows()):

    progress_value = row["time_saved_min"] / max_gain
    rank_icon = rank_icons[rank]

    st.markdown(
        f"""
### {rank_icon} {row['category']}

**Estimated impact:** {row['time_saved_min']:.1f} min saved
"""
    )

    st.progress(progress_value)

# ==========================================================
# DETAILED ANALYSIS
# ==========================================================

st.divider()
st.header("Detailed Analysis")
st.caption(
    "Simulation data, route profile, fueling plan and advanced comparisons."
)

# ==========================================================
# TABS
# ==========================================================

tabs = st.tabs(
    [
        "Route",
        "Fueling",
        "Hard Segments",
        "Gearing",
        "Comparisons",
        "Target Time",
        "ROI",
        "Raw Data",
    ]
)


with tabs[0]:
    st.subheader("Route Profile")

    profile_df = sim.copy()
    profile_df["relative_elevation_m"] = profile_df["elev_delta_m"].cumsum()
    profile_df["relative_elevation_m"] = (
        profile_df["relative_elevation_m"]
        - profile_df["relative_elevation_m"].min()
    )

    st.line_chart(
        profile_df,
        x="cum_dist_km",
        y=["relative_elevation_m", "speed_kmh", "target_power_w"],
    )


with tabs[1]:
    st.subheader("Fueling / Hydration Plan")

    fueling_plan = build_fueling_plan(
        sim_df=sim,
        block_minutes=20,
    )

    st.dataframe(
        fueling_plan,
        use_container_width=True,
    )


with tabs[2]:
    st.subheader("Top 10 Hardest Segments")

    hardest = (
        sim.sort_values("grade_pct", ascending=False)
        .head(10)
        [
            [
                "segment_id",
                "start_km",
                "end_km",
                "grade_pct",
                "speed_kmh",
                "target_power_w",
                "selected_cog_teeth",
                "cadence_rpm",
            ]
        ]
        .round(1)
    )

    st.dataframe(
        hardest,
        use_container_width=True,
    )


with tabs[3]:
    st.subheader("Gear Usage")

    gear_usage = (
        sim.groupby("selected_cog_teeth")
        .size()
        .reset_index(name="segments")
        .sort_values("selected_cog_teeth")
    )

    gear_usage["pct_of_route"] = (
        gear_usage["segments"]
        / gear_usage["segments"].sum()
        * 100
    ).round(1)

    st.dataframe(
        gear_usage,
        use_container_width=True,
    )

    st.subheader("Cassette Comparison")

    cassette_comparison = compare_cassettes(
        segments_df=segments,
        rider_mass_kg=rider_mass_kg,
        bike_mass_kg=bike_mass_kg,
        fitness_wkg=fitness_wkg,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=wind_kmh,
        wind_mode=wind_mode,
        chainring_teeth=chainring_teeth,
        cda=cda,
        crr=crr,
    )

    st.dataframe(
        cassette_comparison,
        use_container_width=True,
    )


with tabs[4]:
    st.subheader("Surface Comparison")

    surface_comparison = compare_surfaces(
        segments_df=segments,
        rider_mass_kg=rider_mass_kg,
        bike_mass_kg=bike_mass_kg,
        fitness_wkg=fitness_wkg,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=wind_kmh,
        wind_mode=wind_mode,
        chainring_teeth=chainring_teeth,
        cassette_teeth=cassette_teeth,
        aero_key=aero_key,
        bottle_sizes_ml=bottle_sizes_ml,
    )

    st.dataframe(
        surface_comparison,
        use_container_width=True,
    )

    st.subheader("Aero Comparison")

    aero_comparison = compare_aero_positions(
        segments_df=segments,
        rider_mass_kg=rider_mass_kg,
        bike_mass_kg=bike_mass_kg,
        fitness_wkg=fitness_wkg,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=wind_kmh,
        wind_mode=wind_mode,
        chainring_teeth=chainring_teeth,
        cassette_teeth=cassette_teeth,
        surface_key=surface_key,
        bottle_sizes_ml=bottle_sizes_ml,
    )

    st.dataframe(
        aero_comparison,
        use_container_width=True,
    )


with tabs[5]:
    st.subheader("Target Time Analysis")

    target_result = estimate_power_for_target_time(
        segments_df=segments,
        rider_mass_kg=rider_mass_kg,
        bike_mass_kg=bike_mass_kg,
        target_time_h=target_time_h,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=wind_kmh,
        wind_mode=wind_mode,
        chainring_teeth=chainring_teeth,
        cassette_teeth=cassette_teeth,
        cda=cda,
        crr=crr,
        bottle_sizes_ml=bottle_sizes_ml,
    )

    current_power_w = rider_mass_kg * fitness_wkg

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Current Power", f"{current_power_w:.0f} W")
    col2.metric("Required Power", f"{target_result['required_power_w']:.0f} W")
    col3.metric("Required W/kg", f"{target_result['required_wkg']:.2f}")
    col4.metric(
        "Extra Power",
        f"{target_result['required_power_w'] - current_power_w:.0f} W",
    )

with tabs[6]:
    st.subheader("Performance ROI — Detailed Table")

    st.dataframe(
        roi,
        use_container_width=True,
    )


with tabs[7]:
    st.subheader("Segment Simulation Data")

    st.dataframe(
        sim.round(2),
        use_container_width=True,
    )