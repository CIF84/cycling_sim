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

EQUIPMENT_OPPORTUNITY_LABELS = {"Aerodynamics", "Rolling Resistance", "Bike Weight"}


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


def _format_live_duration(hours: float) -> str:
    total_minutes = int(round(hours * 60))
    hours_part, minutes_part = divmod(total_minutes, 60)
    return f"{hours_part} h {minutes_part:02d} min"


def _live_outcome(differences: dict) -> str:
    duration_delta = differences["duration"]["delta"]
    if duration_delta < -0.05:
        return f"Ride B faster by {abs(duration_delta):.1f} min"
    if duration_delta > 0.05:
        return f"Ride A faster by {duration_delta:.1f} min"
    return "Ride A and Ride B effectively tied"


def _changed_input_signal(inputs_a: dict, inputs_b: dict, keys: tuple[str, ...]) -> str | None:
    labels = {
        "rider_mass": "Mass",
        "fitness": "Fitness",
        "riding_style": "Position",
        "bike_mass": "Bike mass",
        "tires": "Tires",
        "drivetrain": "Drivetrain",
    }
    units = {"rider_mass": " kg", "fitness": " W/kg", "bike_mass": " kg"}
    for key in keys:
        value_a = inputs_a.get(key)
        value_b = inputs_b.get(key)
        if value_a == value_b:
            continue
        if isinstance(value_a, float) or isinstance(value_b, float):
            change = f"{float(value_a):.1f} → {float(value_b):.1f}{units.get(key, '')}"
        else:
            change = f"{value_a} → {value_b}{units.get(key, '')}"
        return f"{labels[key]} {change}"
    return None


def _live_signal(label: str, value: str, modifier: str = "") -> str:
    modifier_class = f" {modifier}" if modifier else ""
    return f"""
<div class="live-decision-signal{modifier_class}">
<div class="live-decision-label">{escape(label)}</div>
<div class="live-decision-value">{escape(value)}</div>
</div>
"""


def _live_signals_by_intent(
    selected_intent: str,
    summary_b: dict,
    inputs_a: dict,
    inputs_b: dict,
    performance_b: list[dict],
) -> list[tuple[str, str]]:
    duration = _format_live_duration(summary_b["duration_h"])
    speed = f"{summary_b['speed_kmh']:.1f} km/h"
    carbs = f"{summary_b['carbs_g']:.0f} g"
    fluids = f"{summary_b['fluid_goal_l']:.1f} L"
    sodium = f"{summary_b['sodium_mg']:.0f} mg"

    ranked_performance = sorted(performance_b, key=lambda item: item["value"], reverse=True)
    top_performance = ranked_performance[0] if ranked_performance else None
    opportunities = build_opportunity_engine(performance_b)

    if selected_intent == "compare_riders":
        signals = [("Ride B duration", duration), ("Ride B speed", speed)]
        rider_change = _changed_input_signal(
            inputs_a, inputs_b, ("fitness", "rider_mass", "riding_style")
        )
        if rider_change:
            signals.append(("Main rider difference", rider_change))
        return signals

    if selected_intent == "compare_setups":
        signals = [("Ride B speed", speed)]
        equipment_performance = [
            item for item in ranked_performance if item["label"] in EQUIPMENT_OPPORTUNITY_LABELS
        ]
        if equipment_performance:
            top = equipment_performance[0]
            signals.append(("Strongest contributor", f"{top['label']} · {top['value']:.1f} min"))
        equipment_opportunities = [
            item for item in opportunities if item["label"] in EQUIPMENT_OPPORTUNITY_LABELS
        ]
        if equipment_opportunities:
            top = equipment_opportunities[0]
            signals.append(("Best opportunity", f"{top['label']} · {top['roi_label']} ROI"))
        return signals

    if selected_intent == "compare_routes":
        return [
            ("Ride B duration", duration),
            ("Ride B distance", f"{summary_b['distance_km']:.1f} km"),
            ("Fueling demand", f"{carbs} carbs · {fluids} fluids"),
        ]

    if selected_intent == "plan_fueling":
        return [
            ("Carbs", carbs),
            ("Fluids", fluids),
            ("Sodium", sodium),
            ("Duration", duration),
            ("Refills", str(summary_b["refills"])),
        ]

    if selected_intent == "hack_ride":
        signals = []
        if top_performance:
            signals.append(
                ("Biggest modeled gain", f"{top_performance['label']} · {top_performance['value']:.1f} min")
            )
        if opportunities:
            top = opportunities[0]
            signals.extend(
                [
                    ("Strongest opportunity", top["label"]),
                    ("Payoff", top["payoff"]),
                    ("Effort", top["effort"]),
                    ("ROI", top["roi_label"]),
                ]
            )
        return signals

    return [
        ("Ride B duration", duration),
        ("Ride B speed", speed),
        ("Carbs", carbs),
        ("Fluids", fluids),
        ("Sodium", sodium),
    ]


def render_live_decision_bar(
    summary_a: dict,
    summary_b: dict,
    inputs_a: dict,
    inputs_b: dict,
    selected_intent: str,
    performance_b: list[dict] | None = None,
) -> None:
    """Render persistent, mode-aware feedback from existing comparison outputs."""
    if not summary_a.get("ready", True) or not summary_b.get("ready", True):
        _render_html(
            """
<aside class="live-decision-bar is-inactive" aria-label="Live Decision Bar" aria-live="polite">
<div class="live-decision-identity"><span>Live</span><strong>Decision Bar</strong></div>
<div class="live-decision-empty">Select valid routes to activate live comparison.</div>
<a class="live-decision-link" href="#decision-workspace" aria-label="View full decision">View full decision</a>
</aside>
"""
        )
        return

    differences = calculate_ride_differences(summary_a, summary_b)
    if performance_b is None:
        performance_b = build_performance_analysis(inputs_b, summary_b)
    signals = _live_signals_by_intent(
        selected_intent, summary_b, inputs_a, inputs_b, performance_b
    )[:6]
    signal_html = "".join(_live_signal(label, value) for label, value in signals)

    _render_html(
        f"""
<aside class="live-decision-bar" aria-label="Live Decision Bar" aria-live="polite">
<div class="live-decision-identity"><span>Live</span><strong>Decision Bar</strong></div>
{_live_signal('Outcome', _live_outcome(differences), 'live-decision-outcome')}
<div class="live-decision-signals">{signal_html}</div>
<a class="live-decision-link" href="#decision-workspace" aria-label="View full decision">Full decision ↑</a>
</aside>
"""
    )


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


def render_decision_workspace(
    summary_a: dict,
    summary_b: dict,
    inputs_a: dict,
    inputs_b: dict,
    selected_intent: str = "general",
    performance_b: list[dict] | None = None,
) -> None:
    """Render the Question → Evidence → Conclusion → Next Experiment workspace."""
    differences = calculate_ride_differences(summary_a, summary_b)
    verdict = build_scenario_verdict(summary_a, summary_b, inputs_a, inputs_b)
    guidance = get_workspace_guidance(selected_intent)
    if performance_b is None:
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
<section id="decision-workspace" class="decision-workspace" aria-label="Decision workspace">
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


def render_differences_panel(
    summary_a: dict,
    summary_b: dict,
    inputs_a: dict,
    inputs_b: dict,
    selected_intent: str = "general",
) -> None:
    """Backward-compatible name for the Phase 12.4 Decision Workspace."""
    render_decision_workspace(summary_a, summary_b, inputs_a, inputs_b, selected_intent)
