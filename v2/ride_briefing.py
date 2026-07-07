import streamlit as st


def _render_html(html: str) -> None:
    """Render raw HTML without leading indentation so Streamlit does not treat it as code."""
    cleaned = "\n".join(line.strip() for line in html.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def format_duration(hours: float) -> str:
    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h} h {m:02d} min"


def ride_briefing(summary: dict) -> None:
    if not summary.get("ready", True):
        _render_html(
            f"""
<div class="route-intelligence-empty">
<b>Ride Briefing</b><br>
{summary.get('engine_mode', 'Upload GPX or choose demo route to calculate this ride.')}
</div>
"""
        )
        return

    _render_html(
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
