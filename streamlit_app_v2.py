import streamlit as st

from v2.app_styles import inject_global_styles
from v2.app_styles import render_html
from v2.comparison_panel import render_differences_panel
from v2.engine_adapter import run_ride_engine
from v2.onboarding import render_decision_launchpad
from v2.performance import configure_performance_engine
from v2.ride_panel import ride_panel
from v2.route_intelligence import render_route_intelligence
from v2.route_service import resolve_route_segments
from v2.workspace_guidance import render_workspace_guidance


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

# ==========================================================
# HELPERS
# ==========================================================


configure_performance_engine(render_html, run_ride_engine)

inject_global_styles()


# ==========================================================
# FIXED TOP — DECISION LAUNCHPAD
# ==========================================================

selected_intent = render_decision_launchpad(render_html)


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

render_workspace_guidance(selected_intent, render_html)

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
        render_html=render_html,
        resolve_route_segments=resolve_route_segments,
        render_route_intelligence=render_route_intelligence,
        run_ride_engine=run_ride_engine,
        selected_intent=selected_intent,
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
        render_html=render_html,
        resolve_route_segments=resolve_route_segments,
        render_route_intelligence=render_route_intelligence,
        run_ride_engine=run_ride_engine,
        selected_intent=selected_intent,
    )


render_differences_panel(summary_a, summary_b, inputs_a, inputs_b, selected_intent)
