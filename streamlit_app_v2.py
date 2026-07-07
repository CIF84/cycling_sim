import streamlit as st

from v2.decision_context import build_scenario_verdict
from v2.decision_context import calculate_ride_differences
from v2.decision_context import render_decision_context
from v2.engine_adapter import run_ride_engine
from v2.onboarding import render_onboarding_cards
from v2.performance import configure_performance_engine
from v2.recommendations_panel import ride_recommendations
from v2.ride_briefing import ride_briefing
from v2.ride_panel import ride_panel
from v2.route_intelligence import render_route_intelligence
from v2.route_service import resolve_route_segments


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


def render_html(html: str) -> None:
    """Render raw HTML without leading indentation so Streamlit does not treat it as code."""
    cleaned = "\n".join(line.strip() for line in html.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


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

configure_performance_engine(render_html, run_ride_engine)

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

.questions-card{
border:1px solid rgba(255,255,255,.12);
border-radius:10px;
padding:10px 12px;
background:rgba(255,255,255,.025);
margin:.65rem 0;
}
.questions-title{font-size:.72rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:.3rem;}
.questions-list{color:#d6d6d6;font-size:.82rem;line-height:1.6;}

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
    f"""
<div class="fixed-top">
<h1>Bike Science Pro</h1>
<p>Model scenarios. Compare outcomes. Make better decisions.</p>
{render_onboarding_cards()}
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
        ride_briefing=ride_briefing,
        ride_recommendations=ride_recommendations,
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
        ride_briefing=ride_briefing,
        ride_recommendations=ride_recommendations,
    )


# ==========================================================
# PHASE 4.1 — DIFFERENCES ADAPTER
# Keep comparison logic isolated so Phase 4.2 can swap in real v1 outputs.
# ==========================================================


def render_difference_card(label: str, item: dict) -> str:
    """Render one normalized difference card."""
    return f"""
<div class="diff-card">
<div class="diff-label">{label}</div>
<div class="diff-value">{item['value']}</div>
<div class="{delta_class(item['delta'], lower_is_better=item['lower_is_better'])}">{'select route' if not item.get('unit') else signed_delta(item['delta'], item['unit'], item['decimals'], lower_is_better=item['lower_is_better'])}</div>
</div>
"""



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
