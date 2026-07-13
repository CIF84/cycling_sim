from html import escape


WORKSPACE_GUIDANCE = {
    "general": {
        "label": "General exploration",
        "question": "Explore rider, bike, route, weather, and surface assumptions.",
        "keep_constant": "Nothing is prescribed; broader changes create broader analysis.",
        "experiment_with": "Change any inputs and watch how the modeled outcome responds.",
        "evidence": "The comparison panel explains what changed and which differences matter most.",
    },
    "compare_riders": {
        "label": "Compare riders",
        "question": "Which rider is faster on the same route, and why?",
        "keep_constant": "Route, bike, weather, and surface assumptions.",
        "experiment_with": "Rider weight, fitness, or riding style.",
        "evidence": "Time, speed, fueling demand, and the strongest modeled contributors.",
    },
    "compare_setups": {
        "label": "Compare bike setups",
        "question": "Which bike setup performs better for this ride?",
        "keep_constant": "Rider, route, weather, and surface assumptions.",
        "experiment_with": "Bike weight, tires, drivetrain, or riding position.",
        "evidence": "Time savings and the influence of aero, rolling resistance, and weight.",
    },
    "compare_routes": {
        "label": "Compare routes",
        "question": "Which route better fits this rider and setup?",
        "keep_constant": "Rider, bike, and comparable weather assumptions.",
        "experiment_with": "Routes, distance, climbing, terrain, duration, and fueling demand.",
        "evidence": "Route character, ride time, physiological demand, and practical trade-offs.",
    },
    "plan_fueling": {
        "label": "Plan fueling",
        "question": "What should the rider eat and drink for this ride?",
        "keep_constant": "The route, rider, and weather conditions you intend to ride.",
        "experiment_with": "Route, rider fitness, temperature, humidity, or wind.",
        "evidence": "Carbohydrate, fluid, sodium, refill, and pacing recommendations.",
    },
    "hack_ride": {
        "label": "Hack my ride",
        "question": "Where are the biggest realistic gains?",
        "keep_constant": "The route and current setup you actually use.",
        "experiment_with": "Fitness, weight, position, tires, bike weight, and plausible upgrades.",
        "evidence": "Scale of Influence, Opportunity Engine, and Upgrade Advisor payoff signals.",
    },
}


def get_workspace_guidance(intent: str) -> dict:
    return WORKSPACE_GUIDANCE.get(intent, WORKSPACE_GUIDANCE["general"]).copy()


def render_workspace_guidance(intent: str, render_html) -> None:
    guidance = get_workspace_guidance(intent)

    render_html(
        f"""
<section class="workspace-guidance" aria-label="Workspace guidance">
<div class="workspace-guidance-kicker">Mode: {escape(guidance["label"])}</div>
<div class="workspace-guidance-question">{escape(guidance["question"])}</div>
<div class="workspace-guidance-grid">
<div class="workspace-guidance-item"><span>Keep comparable</span>{escape(guidance["keep_constant"])}</div>
<div class="workspace-guidance-item"><span>Try changing</span>{escape(guidance["experiment_with"])}</div>
<div class="workspace-guidance-item workspace-guidance-evidence"><span>What you will learn</span>{escape(guidance["evidence"])}</div>
</div>
</section>
"""
    )
