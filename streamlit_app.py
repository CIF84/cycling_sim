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
# TIME SAVINGS
# ==========================================================

st.subheader("Time Savings")

roi_display = (
    roi.sort_values(
        "time_saved_min",
        ascending=False,
    )
    .head(4)
)

max_gain = roi_display["time_saved_min"].max()

for _, row in roi_display.iterrows():

    progress_value = row["time_saved_min"] / max_gain

    st.markdown(
        f"""
### {row['change']}

**{row['time_saved_min']:.1f} min saved**
"""
    )

    st.progress(progress_value)



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