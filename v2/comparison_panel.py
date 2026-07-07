import streamlit as st

from v2.decision_context import build_scenario_verdict
from v2.decision_context import calculate_ride_differences
from v2.decision_context import render_decision_context


def _render_html(html: str) -> None:
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

    _render_html(
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
