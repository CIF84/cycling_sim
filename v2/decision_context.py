def _format_duration(hours: float) -> str:
    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h} h {m:02d} min"


def calculate_ride_differences(summary_a: dict, summary_b: dict) -> dict:
    """Normalize Ride B vs Ride A differences for the bottom decision dock."""
    if not summary_a.get("ready", True) or not summary_b.get("ready", True):
        return {
            key: {"value": "—", "delta": 0, "unit": "", "decimals": 0, "lower_is_better": False}
            for key in ["distance", "duration", "speed", "carbs", "fluids", "sodium"]
        }

    distance_delta = summary_b["distance_km"] - summary_a["distance_km"]
    duration_delta_min = (summary_b["duration_h"] - summary_a["duration_h"]) * 60
    speed_delta = summary_b["speed_kmh"] - summary_a["speed_kmh"]
    carbs_delta = summary_b["carbs_g"] - summary_a["carbs_g"]
    fluid_delta = summary_b["fluid_goal_l"] - summary_a["fluid_goal_l"]
    sodium_delta = summary_b["sodium_mg"] - summary_a["sodium_mg"]

    same_distance = abs(distance_delta) < 0.01

    return {
        "distance": {
            "value": "Same" if same_distance else f"{summary_b['distance_km']:.1f} km",
            "delta": distance_delta,
            "unit": "km",
            "decimals": 1,
            "lower_is_better": False,
        },
        "duration": {
            "value": _format_duration(summary_b["duration_h"]),
            "delta": duration_delta_min,
            "unit": "min",
            "decimals": 0,
            "lower_is_better": True,
        },
        "speed": {
            "value": f"{summary_b['speed_kmh']:.1f} km/h",
            "delta": speed_delta,
            "unit": "km/h",
            "decimals": 1,
            "lower_is_better": False,
        },
        "carbs": {
            "value": f"{summary_b['carbs_g']:.0f} g",
            "delta": carbs_delta,
            "unit": "g",
            "decimals": 0,
            "lower_is_better": True,
        },
        "fluids": {
            "value": f"{summary_b['fluid_goal_l']:.1f} L",
            "delta": fluid_delta,
            "unit": "L",
            "decimals": 1,
            "lower_is_better": True,
        },
        "sodium": {
            "value": f"{summary_b['sodium_mg']:.0f} mg",
            "delta": sodium_delta,
            "unit": "mg",
            "decimals": 0,
            "lower_is_better": True,
        },
    }


def input_changed(inputs_a: dict, inputs_b: dict, key: str, tolerance: float = 0.0) -> bool:
    """Compare two input values with optional numeric tolerance."""
    value_a = inputs_a.get(key)
    value_b = inputs_b.get(key)

    if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
        return abs(value_a - value_b) > tolerance

    return value_a != value_b


def detect_comparison_context(inputs_a: dict, inputs_b: dict) -> dict:
    """Phase 9: infer comparison intent from scenario differences."""
    route_a = inputs_a.get("route_description")
    route_b = inputs_b.get("route_description")
    same_route = route_a == route_b

    rider_changed = any(
        [
            input_changed(inputs_a, inputs_b, "rider_mass"),
            input_changed(inputs_a, inputs_b, "fitness", tolerance=0.01),
            input_changed(inputs_a, inputs_b, "riding_style"),
        ]
    )

    bike_changed = any(
        [
            input_changed(inputs_a, inputs_b, "bike_mass", tolerance=0.01),
            input_changed(inputs_a, inputs_b, "tires"),
            input_changed(inputs_a, inputs_b, "drivetrain"),
        ]
    )

    conditions_changed = any(
        [
            input_changed(inputs_a, inputs_b, "temperature"),
            input_changed(inputs_a, inputs_b, "humidity"),
            input_changed(inputs_a, inputs_b, "wind"),
            input_changed(inputs_a, inputs_b, "surface"),
        ]
    )

    changed_groups = [
        name
        for name, changed in [
            ("route", not same_route),
            ("rider", rider_changed),
            ("bike", bike_changed),
            ("weather/surface", conditions_changed),
        ]
        if changed
    ]

    if not changed_groups:
        mode = "Simulation baseline"
        question = "What does this ride look like?"
        focus = "Ride briefing, fueling, hydration and route character."
    elif same_route and rider_changed and not bike_changed and not conditions_changed:
        mode = "Rider comparison"
        question = "How do rider attributes affect the same route?"
        focus = "Performance gap, power-to-weight, fueling demand and rider suitability."
    elif same_route and bike_changed and not rider_changed and not conditions_changed:
        mode = "Setup comparison"
        question = "Which bike or equipment setup performs better?"
        focus = "Equipment impact, rolling resistance, bike mass and aerodynamic assumptions."
    elif same_route and (rider_changed or bike_changed or conditions_changed):
        mode = "What-if optimization"
        question = "What changes if this rider or setup improves?"
        focus = "Time saved, practical levers, and whether changes are worth pursuing."
    elif not same_route and not rider_changed and not bike_changed:
        mode = "Route suitability"
        question = "Which route better fits this rider and setup?"
        focus = "Route character, difficulty, fueling demand, and expected ride outcome."
    elif not same_route and (rider_changed or bike_changed):
        mode = "General scenario comparison"
        question = "Which scenario performs better, and why?"
        focus = "Outcome differences across route, rider and setup assumptions."
    else:
        mode = "Scenario comparison"
        question = "What changed between Ride A and Ride B?"
        focus = "Key deltas and the most likely drivers of the difference."

    reason_bits = ["same route" if same_route else "different routes"]

    if rider_changed:
        reason_bits.append("rider changed")
    if bike_changed:
        reason_bits.append("bike/setup changed")
    if conditions_changed:
        reason_bits.append("weather/surface changed")
    if len(reason_bits) == 1:
        reason_bits.append("no major setup changes")

    return {
        "mode": mode,
        "question": question,
        "focus": focus,
        "reason": " · ".join(reason_bits),
        "changed_groups": changed_groups,
    }


def render_decision_context(inputs_a: dict, inputs_b: dict) -> str:
    context = detect_comparison_context(inputs_a, inputs_b)
    narratives={
"Simulation baseline":"You're exploring a single ride scenario. The analysis focuses on understanding the expected ride characteristics rather than comparing alternatives.",
"Rider comparison":"You're comparing how different rider attributes perform on the same route. Focus on performance gaps and the reasons behind them.",
"Setup comparison":"You're comparing equipment choices on the same route. The analysis emphasizes which setup changes are most influential.",
"What-if optimization":"You're exploring whether changing your rider or bike setup is worthwhile. The focus is on practical improvements and their expected payoff.",
"Route suitability":"You're comparing two routes for the same rider. The analysis focuses on which route better matches the rider and why.",
"General scenario comparison":"You're comparing multiple aspects at once. The analysis explains the overall outcome before drilling into individual contributors.",
"Scenario comparison":"You're comparing two ride scenarios and identifying the major drivers of the difference."
}
    qs={
"Simulation baseline":["What should I expect?","How demanding is this ride?","What should I fuel?"],
"Rider comparison":["Which rider is faster?","Why?","Which strengths matter most?"],
"Setup comparison":["Which setup is faster?","Which change matters most?","Is it worth it?"],
"What-if optimization":["What should I change first?","How much time can I save?","Where is the best ROI?"],
"Route suitability":["Which route suits me better?","Why?","What trade-offs exist?"],
"General scenario comparison":["Which scenario performs better?","What changed?","What should I look at first?"],
"Scenario comparison":["What changed?","Why?","What should I do next?"]
}
    q=''.join(f"✓ {x}<br>" for x in qs.get(context["mode"],[]))
    return f"""
<div class="decision-context">
<div class="decision-context-title">Current Analysis</div>
<div class="decision-context-main">{context['mode']}</div>
<div class="decision-context-meta">{narratives.get(context['mode'],'')}<br><br><b>Detected from inputs:</b> {context['reason']}<br><b>Analysis focus:</b> {context['focus']}</div>
</div>
<div class="questions-card">
<div class="questions-title">Questions answered</div>
<div class="questions-list">{q}</div>
</div>
"""

def build_scenario_verdict(summary_a: dict, summary_b: dict, inputs_a: dict, inputs_b: dict) -> str:
    """Create a compact human-readable comparison of Ride B vs Ride A."""
    if not summary_a.get("ready", True) or not summary_b.get("ready", True):
        return "<b>Scenario comparison:</b> Select a route for Ride A and Ride B to compare outcomes. Upload GPX or explicitly choose the generated demo route."

    context = detect_comparison_context(inputs_a, inputs_b)
    differences = calculate_ride_differences(summary_a, summary_b)

    duration_delta = differences["duration"]["delta"]
    speed_delta = differences["speed"]["delta"]
    carbs_delta = differences["carbs"]["delta"]
    fluid_delta = differences["fluids"]["delta"]

    if duration_delta < -0.5:
        time_phrase = f"Ride B is {abs(duration_delta):.0f} min faster"
    elif duration_delta > 0.5:
        time_phrase = f"Ride B is {duration_delta:.0f} min slower"
    else:
        time_phrase = "Ride B is effectively the same duration"

    if speed_delta > 0.1:
        speed_phrase = f"averaging {speed_delta:.1f} km/h more"
    elif speed_delta < -0.1:
        speed_phrase = f"averaging {abs(speed_delta):.1f} km/h less"
    else:
        speed_phrase = "with similar average speed"

    if carbs_delta < -1 or fluid_delta < -0.05:
        demand_phrase = "with lower fueling or hydration demand"
    elif carbs_delta > 1 or fluid_delta > 0.05:
        demand_phrase = "but with higher fueling or hydration demand"
    else:
        demand_phrase = "with similar fueling and hydration demand"

    setup_changes = []
    if inputs_a["rider_mass"] != inputs_b["rider_mass"]:
        setup_changes.append(f"rider mass {inputs_a['rider_mass']} → {inputs_b['rider_mass']} kg")
    if inputs_a["fitness"] != inputs_b["fitness"]:
        setup_changes.append(f"fitness {inputs_a['fitness']:.1f} → {inputs_b['fitness']:.1f} W/kg")
    if inputs_a["riding_style"] != inputs_b["riding_style"]:
        setup_changes.append(f"position {inputs_a['riding_style']} → {inputs_b['riding_style']}")
    if inputs_a["bike_mass"] != inputs_b["bike_mass"]:
        setup_changes.append(f"bike mass {inputs_a['bike_mass']:.1f} → {inputs_b['bike_mass']:.1f} kg")
    if inputs_a["tires"] != inputs_b["tires"]:
        setup_changes.append(f"tires {inputs_a['tires']} → {inputs_b['tires']}")
    if inputs_a["surface"] != inputs_b["surface"]:
        setup_changes.append(f"surface {inputs_a['surface']} → {inputs_b['surface']}")

    setup_phrase = "; ".join(setup_changes[:3]) if setup_changes else "same key setup assumptions"

    return (
        f"<b>{context['mode']}:</b> {time_phrase}, {speed_phrase}, {demand_phrase}. "
        f"Main change: {setup_phrase}."
    )
