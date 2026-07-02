_render_html = None
_run_ride_engine = None


def configure_performance_engine(render_html_func, run_ride_engine_func) -> None:
    global _render_html, _run_ride_engine
    _render_html = render_html_func
    _run_ride_engine = run_ride_engine_func


def build_performance_analysis(inputs: dict, summary: dict) -> list[dict]:
    """Phase 3.3 Scale of Influence model.

    Instead of hard-coding performance bars directly, this function now
    re-runs the same engine adapter with standardized improvement scenarios.

    Once the real v1 simulator is connected inside run_ride_engine(...),
    these bars will automatically become route-specific simulation outputs.
    """
    if not summary.get("ready", True):
        return [
            {"label": "Route required", "detail": "select GPX or demo route", "value": 0.0}
        ]

    baseline_duration_h = summary["duration_h"]

    scenarios = [
        {
            "label": "Rider Power",
            "detail": "+10 W benchmark",
            "updates": {"fitness": inputs["fitness"] + 10 / inputs["rider_mass"]},
        },
        {
            "label": "Aerodynamics",
            "detail": "5% improvement",
            "updates": {"aero_gain_pct": 5},
        },
        {
            "label": "Body Weight",
            "detail": "−3 kg benchmark",
            "updates": {"rider_mass": max(40, inputs["rider_mass"] - 3)},
        },
        {
            "label": "Rolling Resistance",
            "detail": "10% tire improvement",
            "updates": {"rolling_resistance_gain_pct": 10},
        },
        {
            "label": "Bike Weight",
            "detail": "−0.5 kg benchmark",
            "updates": {"bike_mass": max(5.0, inputs["bike_mass"] - 0.5)},
        },
    ]

    performance = []

    for scenario in scenarios:
        scenario_inputs = inputs.copy()
        scenario_inputs.update(scenario["updates"])
        scenario_summary = _run_ride_engine(scenario_inputs)
        minutes_saved = max(0, (baseline_duration_h - scenario_summary["duration_h"]) * 60)

        performance.append(
            {
                "label": scenario["label"],
                "detail": scenario["detail"],
                "value": minutes_saved,
            }
        )

    return performance



def build_opportunity_engine(performance: list[dict]) -> list[dict]:
    """Phase 9.1 Opportunity Engine.

    Converts raw Scale of Influence bars into action-oriented improvement
    opportunities. Impact comes from real engine re-runs; effort, cost and
    payoff labels are transparent heuristics for decision support.
    """
    effort_map = {
        "Rider Power": {
            "effort": "high",
            "effort_score": 4,
            "cost": "training time",
            "action": "Structured training block, better pacing discipline, or more consistent training.",
            "package": "Fitness package",
        },
        "Aerodynamics": {
            "effort": "low/medium",
            "effort_score": 2,
            "cost": "position work",
            "action": "Improve riding position, clothing, cockpit setup, or bike fit.",
            "package": "Aero package",
        },
        "Rolling Resistance": {
            "effort": "low",
            "effort_score": 1,
            "cost": "tires / pressure",
            "action": "Review tires, pressure, casing, and tubeless setup.",
            "package": "Tire package",
        },
        "Body Weight": {
            "effort": "high",
            "effort_score": 4,
            "cost": "months",
            "action": "Long-term body composition change, not a quick ride-day lever.",
            "package": "Body composition package",
        },
        "Bike Weight": {
            "effort": "medium/high",
            "effort_score": 3,
            "cost": "equipment spend",
            "action": "Lower priority unless the route is climbing-heavy or the upgrade is cheap.",
            "package": "Equipment package",
        },
        "Route required": {
            "effort": "n/a",
            "effort_score": 99,
            "cost": "n/a",
            "action": "Select a route first.",
            "package": "Route setup",
        },
    }

    def payoff_label(value: float) -> str:
        if value >= 3.0:
            return "High"
        if value >= 1.0:
            return "Medium"
        if value > 0:
            return "Low"
        return "None"

    def roi_label(score: float) -> str:
        if score >= 1.5:
            return "Strong"
        if score >= 0.6:
            return "Good"
        if score > 0:
            return "Low"
        return "None"

    opportunities = []
    for item in performance:
        value = float(item.get("value", 0.0))
        info = effort_map.get(
            item["label"],
            {
                "effort": "unknown",
                "effort_score": 3,
                "cost": "unknown",
                "action": "Review this lever.",
                "package": item["label"],
            },
        )

        effort_score = info["effort_score"]
        roi_score = value / effort_score if effort_score else value
        opportunities.append(
            {
                "label": item["label"],
                "package": info["package"],
                "impact_min": value,
                "payoff": payoff_label(value),
                "effort": info["effort"],
                "cost": info["cost"],
                "action": info["action"],
                "roi_score": roi_score,
                "roi_label": roi_label(roi_score),
            }
        )

    return sorted(opportunities, key=lambda x: (x["roi_score"], x["impact_min"]), reverse=True)


def render_opportunity_engine(performance: list[dict]) -> None:
    opportunities = build_opportunity_engine(performance)
    opportunities = [item for item in opportunities if item["impact_min"] > 0][:4]

    if not opportunities:
        _render_html(
            """
<div class="opportunity-section-title">Opportunity Engine</div>
<div class="performance-insight"><b>Next best action:</b> Select a route and scenario inputs to calculate ranked opportunities.</div>
"""
        )
        return

    top = opportunities[0]

    cards_html = ""
    for idx, item in enumerate(opportunities, start=1):
        css_class = "priority-1" if idx == 1 else "priority-2" if idx == 2 else "priority-low"

        cards_html += f"""
<div class="opportunity-card {css_class}">
<div class="opportunity-rank">Opportunity #{idx}</div>
<div class="opportunity-title">{item['label']}</div>

<div class="opportunity-decision-grid">
    <div class="opportunity-pill">
        <div class="opportunity-pill-label">Payoff</div>
        <div class="opportunity-pill-value">{item['payoff']}</div>
    </div>
    <div class="opportunity-pill">
        <div class="opportunity-pill-label">Effort</div>
        <div class="opportunity-pill-value">{item['effort']}</div>
    </div>
    <div class="opportunity-pill">
        <div class="opportunity-pill-label">ROI</div>
        <div class="opportunity-pill-value">{item['roi_label']}</div>
    </div>
</div>

<div class="opportunity-meta">
    <b>Modeled gain:</b> {item['impact_min']:.1f} min<br>
    <b>Cost type:</b> {item['cost']}<br>
    <b>Package:</b> {item['package']}
</div>
<div class="opportunity-meta" style="margin-top:0.45rem;">{item['action']}</div>
</div>
"""

    _render_html(
        f"""
<div class="opportunity-section-title">Opportunity Engine</div>

<div class="opportunity-focus">
    <div class="opportunity-focus-title">Biggest opportunity</div>
    <div class="opportunity-focus-main">Improve {top['label'].lower()} first.</div>
    <div class="opportunity-meta">
        Expected gain: <b>≈{top['impact_min']:.1f} minutes</b>. 
        This has a <b>{top['payoff'].lower()}</b> modeled payoff with <b>{top['effort']}</b> effort.
        Typical path: {top['action']}
    </div>
</div>

<div class="opportunity-portfolio-grid">
{cards_html}
</div>

<div class="opportunity-note">Phase 9.1 Opportunity Portfolio ranks levers by payoff vs effort, not modeled time alone. Impact still comes from real v1 engine re-runs.</div>
"""
    )
    render_upgrade_advisor(opportunities)


def build_upgrade_advisor(opportunities: list[dict]) -> list[dict]:
    """Phase 9.1 Upgrade Advisor.

    Converts ranked opportunities into human action cards. The modeled gain
    still comes from the real engine; difficulty/cost/time are practical
    heuristics intended to make the decision easier to understand.
    """
    action_library = {
        "Aerodynamics": {
            "difficulty": "Easy",
            "cost": "Low",
            "time": "Immediate",
            "actions": [
                "Tighter clothing",
                "Improve riding position",
                "Cockpit or handlebar setup",
                "Bike fit check",
            ],
        },
        "Rolling Resistance": {
            "difficulty": "Easy",
            "cost": "Low",
            "time": "Immediate",
            "actions": [
                "Optimize tire pressure",
                "Consider faster tire casing",
                "Review tubeless or TPU setup",
                "Check tire choice for surface",
            ],
        },
        "Rider Power": {
            "difficulty": "Hard",
            "cost": "Low",
            "time": "Weeks/months",
            "actions": [
                "Structured threshold block",
                "VO₂ max intervals",
                "Improve training consistency",
                "Avoid repeated pacing spikes",
            ],
        },
        "Body Weight": {
            "difficulty": "Hard",
            "cost": "Low",
            "time": "Months",
            "actions": [
                "Long-term body composition work",
                "Protect fueling quality",
                "Avoid crash dieting",
                "Prioritize recovery and consistency",
            ],
        },
        "Bike Weight": {
            "difficulty": "Medium",
            "cost": "High",
            "time": "Immediate",
            "actions": [
                "Prioritize rotating weight only if upgrade is sensible",
                "Review bottle/load strategy",
                "Avoid expensive low-impact upgrades",
                "Consider only if climbing-heavy route",
            ],
        },
    }

    ranked = []
    medals = ["🥇 Best ROI", "🥈 Second best", "🥉 Third best"]
    css_classes = ["best", "second", "third"]

    for idx, item in enumerate(opportunities[:3]):
        label = item["label"]
        profile = action_library.get(
            label,
            {
                "difficulty": item.get("effort", "Medium"),
                "cost": item.get("cost", "Unknown"),
                "time": "Depends",
                "actions": [item.get("action", "Review this lever.")],
            },
        )

        ranked.append(
            {
                "rank": medals[idx],
                "css_class": css_classes[idx],
                "label": label,
                "gain": item.get("impact_min", 0.0),
                "difficulty": profile["difficulty"],
                "cost": profile["cost"],
                "time": profile["time"],
                "actions": profile["actions"],
            }
        )

    return ranked


def render_upgrade_advisor(opportunities: list[dict]) -> None:
    upgrade_cards = build_upgrade_advisor(opportunities)

    if not upgrade_cards:
        return

    cards_html = ""
    for card in upgrade_cards:
        actions_html = "".join(f"<li>{action}</li>" for action in card["actions"])
        cards_html += f"""
<div class="upgrade-card {card['css_class']}">
    <div class="upgrade-rank">{card['rank']}</div>
    <div class="upgrade-title">{card['label']}</div>
    <div class="upgrade-gain">+{card['gain']:.1f} min</div>

    <div class="upgrade-meta-grid">
        <div class="upgrade-meta-pill">
            <div class="upgrade-meta-label">Difficulty</div>
            <div class="upgrade-meta-value">{card['difficulty']}</div>
        </div>
        <div class="upgrade-meta-pill">
            <div class="upgrade-meta-label">Cost</div>
            <div class="upgrade-meta-value">{card['cost']}</div>
        </div>
        <div class="upgrade-meta-pill">
            <div class="upgrade-meta-label">Time</div>
            <div class="upgrade-meta-value">{card['time']}</div>
        </div>
    </div>

    <div class="upgrade-actions-title">Typical actions</div>
    <ul class="upgrade-actions">{actions_html}</ul>
</div>
"""

    _render_html(
        f"""
<div class="upgrade-section-title">Upgrade Advisor</div>
<div class="upgrade-advisor-grid">
{cards_html}
</div>
<div class="upgrade-note">Phase 9.1 translates modeled opportunities into concrete actions, while keeping Scale of Influence as the calculation source.</div>
"""
    )

def ride_performance_analysis(inputs: dict, summary: dict) -> None:
    performance = build_performance_analysis(inputs, summary)
    performance = sorted(performance, key=lambda item: item["value"], reverse=True)
    max_value = max(item["value"] for item in performance) if performance else 1
    top = performance[0]
    second = performance[1] if len(performance) > 1 else None

    rows_html = ""
    for item in performance:
        width_pct = 0 if max_value == 0 else item["value"] / max_value * 100
        rows_html += f"""
<div class="performance-row">
<div class="performance-head">
<span>{item['label']} <span style="color:#a9a9a9;font-weight:600;">({item['detail']})</span></span>
<span class="performance-value">{item['value']:.1f} min</span>
</div>
<div class="performance-track"><div class="performance-fill" style="width:{width_pct:.0f}%;"></div></div>
</div>
"""

    if second:
        ratio_pct = (top["value"] / second["value"] - 1) * 100 if second["value"] else 0
        insight = (
            f"{top['label']} is the strongest modeled lever in this scenario, "
            f"about {ratio_pct:.0f}% stronger than {second['label']} "
            f"({top['value']:.1f} vs {second['value']:.1f} min)."
        )
    else:
        insight = "Performance analysis will compare modeled improvement levers for this ride."

    _render_html(
        f"""
<div class="performance-list">
{rows_html}
</div>
<div class="performance-insight"><b>Key insight:</b> {insight}</div>
<div class="performance-note">Phase 7.2 Scale of Influence generated by re-running standardized improvements through the real v1 engine and selected route.</div>
"""
    )
    render_opportunity_engine(performance)
