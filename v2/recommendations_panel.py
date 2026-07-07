import streamlit as st


def _render_html(html: str) -> None:
    """Render raw HTML without leading indentation so Streamlit does not treat it as code."""
    cleaned = "\n".join(line.strip() for line in html.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


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

    _render_html(
        f"""
<div class="recommendation-grid">
{cards_html}
</div>
<div class="recommendation-note">Phase 7.2 recommendations generated from the real v1 engine summary and selected route.</div>
"""
    )
