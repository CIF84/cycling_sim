from html import escape

import streamlit as st

from v2.decision_context import build_scenario_verdict
from v2.decision_context import calculate_ride_differences
from v2.decision_context import render_decision_context
from v2.performance import build_opportunity_engine
from v2.performance import build_performance_analysis
from v2.performance import ride_performance_analysis
from v2.recommendations_panel import build_recommendations
from v2.recommendations_panel import ride_recommendations
from v2.ride_briefing import ride_briefing
from v2.workspace_guidance import get_workspace_guidance


EVIDENCE_ORDER_BY_INTENT = {
    "general": ("duration", "speed", "distance", "carbs", "fluids", "sodium"),
    "compare_riders": ("duration", "speed", "carbs", "fluids", "sodium", "distance"),
    "compare_setups": ("duration", "speed", "distance", "carbs", "fluids", "sodium"),
    "compare_routes": ("distance", "duration", "speed", "carbs", "fluids", "sodium"),
    "plan_fueling": ("carbs", "fluids", "sodium", "duration", "speed", "distance"),
    "hack_ride": ("duration", "speed", "carbs", "fluids", "sodium", "distance"),
}

PRIMARY_EVIDENCE_BY_INTENT = {
    "general": set(),
    "compare_riders": {"duration", "speed"},
    "compare_setups": {"duration", "speed"},
    "compare_routes": {"distance", "duration", "speed"},
    "plan_fueling": {"carbs", "fluids", "sodium"},
    "hack_ride": {"modeled_gain", "duration", "speed"},
}

NEXT_ACTION_CATEGORY_BY_INTENT = {
    "general": "Pacing",
    "compare_riders": "Pacing",
    "compare_setups": "Equipment",
    "compare_routes": "Pacing",
    "plan_fueling": "Nutrition",
}

EVIDENCE_FOCUS_BY_INTENT = {
    "general": "Balanced outcome evidence",
    "compare_riders": "Rider-related outcome evidence",
    "compare_setups": "Equipment-related outcome evidence",
    "compare_routes": "Route-character outcome evidence",
    "plan_fueling": "Nutrition and hydration evidence",
    "hack_ride": "Largest realistic improvement evidence",
}


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


def render_difference_card(label: str, item: dict, emphasis: str = "secondary") -> str:
    """Render one normalized difference card with presentation-only emphasis."""
    delta = "select route" if not item.get("unit") else signed_delta(
        item["delta"], item["unit"], item["decimals"], lower_is_better=item["lower_is_better"]
    )
    return f"""
<div class="diff-card evidence-{emphasis}">
<div class="evidence-rank">{'Core evidence' if emphasis == 'balanced' else emphasis}</div>
<div class="diff-label">{label}</div>
<div class="diff-value">{item['value']}</div>
<div class="{delta_class(item['delta'], lower_is_better=item['lower_is_better'])}">{delta}</div>
</div>
"""


def _render_modeled_gain_card(performance: list[dict]) -> str:
    ranked = sorted(performance, key=lambda item: item["value"], reverse=True)
    top = ranked[0] if ranked else {"label": "Route required", "value": 0.0}
    return f"""
<div class="diff-card evidence-primary modeled-gain-card">
<div class="evidence-rank">Primary</div>
<div class="diff-label">Biggest modeled gain</div>
<div class="diff-value">{escape(top['label'])}</div>
<div class="diff-positive">{top['value']:.1f} min saved</div>
</div>
"""


def _next_action(selected_intent: str, inputs_b: dict, summary_b: dict, performance_b: list[dict]) -> tuple[str, str]:
    """Select an already-generated recommendation for the prominent next-action slot."""
    if selected_intent == "hack_ride":
        opportunities = build_opportunity_engine(performance_b)
        if opportunities:
            return opportunities[0]["action"], "Ride B Opportunity Engine"

    recommendations = build_recommendations(inputs_b, summary_b)
    category = NEXT_ACTION_CATEGORY_BY_INTENT.get(selected_intent)
    if category not in recommendations:
        category = next(iter(recommendations))
    return recommendations[category][0], f"Ride B {category} recommendation"


def _render_deep_analysis(
    inputs_a: dict,
    summary_a: dict,
    inputs_b: dict,
    summary_b: dict,
    performance_b: list[dict],
) -> None:
    st.markdown("## Deep Analysis")
    st.caption("Detailed outputs remain available when you want to inspect the evidence more closely.")

    with st.expander("Comparison Context"):
        _render_html(render_decision_context(inputs_a, inputs_b))

    ride_a_tab, ride_b_tab = st.tabs(["Ride A", "Ride B"])
    for tab, inputs, summary, performance in (
        (ride_a_tab, inputs_a, summary_a, None),
        (ride_b_tab, inputs_b, summary_b, performance_b),
    ):
        with tab:
            with st.expander("Ride Briefing"):
                ride_briefing(summary)
            with st.expander("Recommendations"):
                ride_recommendations(inputs, summary)
            with st.expander("Performance Analysis · Opportunity Engine · Upgrade Advisor"):
                ride_performance_analysis(inputs, summary, performance=performance)


def render_differences_panel(
    summary_a: dict,
    summary_b: dict,
    inputs_a: dict,
    inputs_b: dict,
    selected_intent: str = "general",
) -> None:
    """Render the Question → Evidence → Conclusion → Next Experiment workspace."""
    differences = calculate_ride_differences(summary_a, summary_b)
    verdict = build_scenario_verdict(summary_a, summary_b, inputs_a, inputs_b)
    guidance = get_workspace_guidance(selected_intent)
    performance_b = build_performance_analysis(inputs_b, summary_b)

    order = EVIDENCE_ORDER_BY_INTENT.get(selected_intent, EVIDENCE_ORDER_BY_INTENT["general"])
    primary_keys = PRIMARY_EVIDENCE_BY_INTENT.get(selected_intent, set())
    labels = {
        "distance": "Distance",
        "duration": "Duration",
        "speed": "Speed",
        "carbs": "Carbs",
        "fluids": "Fluids",
        "sodium": "Sodium",
    }
    cards = []
    if selected_intent == "hack_ride":
        cards.append(_render_modeled_gain_card(performance_b))
    cards.extend(
        render_difference_card(
            labels[key],
            differences[key],
            "balanced" if selected_intent == "general" else "primary" if key in primary_keys else "secondary",
        )
        for key in order
    )

    next_action, action_source = _next_action(selected_intent, inputs_b, summary_b, performance_b)

    _render_html(
        f"""
<section class="decision-workspace" aria-label="Decision workspace">
<div class="investigation-step">Question</div>
<div class="investigation-question">{escape(guidance['question'])}</div>

<div class="decision-summary-card">
<div class="workspace-layer-label">Decision Summary</div>
<div class="decision-summary-verdict">{verdict}</div>
</div>

<div class="evidence-section">
<div class="workspace-layer-label">Evidence</div>
<div class="evidence-focus">{escape(EVIDENCE_FOCUS_BY_INTENT.get(selected_intent, EVIDENCE_FOCUS_BY_INTENT['general']))}</div>
<div class="diff-grid">{''.join(cards)}</div>
</div>

<div class="next-action-card">
<div class="workspace-layer-label">Recommended Next Action</div>
<div class="next-action-question">What should I try next?</div>
<div class="next-action-copy">{escape(next_action)}</div>
<div class="next-action-source">Existing output: {escape(action_source)}</div>
</div>
</section>
"""
    )

    _render_deep_analysis(inputs_a, summary_a, inputs_b, summary_b, performance_b)
