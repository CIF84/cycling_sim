import streamlit as st
from html import escape


INTENT_SESSION_KEY = "bike_science_pro_intent"

INTENT_LABELS = {
    "general": "General exploration",
    "compare_riders": "Compare riders",
    "compare_setups": "Compare bike setups",
    "compare_routes": "Compare routes",
    "plan_fueling": "Plan fueling",
    "hack_ride": "Hack my ride",
}

LAUNCHPAD_ENTRIES = (
    (
        "compare_riders",
        "Compare riders",
        "Who is faster on the same route—and why?",
    ),
    (
        "compare_setups",
        "Compare bike setups",
        "Which bike, tire, weight, or position works better for this ride?",
    ),
    (
        "compare_routes",
        "Compare routes",
        "Which route better fits this rider and setup?",
    ),
    (
        "plan_fueling",
        "Plan fueling",
        "What should I eat and drink for this ride?",
    ),
    (
        "hack_ride",
        "Hack my ride",
        "Where are the biggest realistic gains?",
    ),
)


def _current_intent() -> str:
    intent = st.session_state.get(INTENT_SESSION_KEY, "general")
    if intent not in INTENT_LABELS:
        return "general"
    return intent


def _select_intent(intent: str) -> None:
    st.session_state[INTENT_SESSION_KEY] = intent


def _intent_from_query_params() -> str | None:
    intent = st.query_params.get("intent")
    if isinstance(intent, list):
        intent = intent[0] if intent else None
    if intent in INTENT_LABELS and intent != "general":
        return intent
    return None


def render_decision_launchpad(render_html) -> str:
    if INTENT_SESSION_KEY not in st.session_state:
        st.session_state[INTENT_SESSION_KEY] = "general"

    query_intent = _intent_from_query_params()
    if query_intent:
        _select_intent(query_intent)

    selected_intent = _current_intent()

    entry_markup = []
    for intent, label, supporting_text in LAUNCHPAD_ENTRIES:
        active_class = " active" if selected_intent == intent else ""
        entry_markup.append(
            f"""
<a class="decision-entry{active_class}" href="?intent={escape(intent)}">
<span class="decision-entry-title">{escape(label)}</span>
<span class="decision-entry-support">{escape(supporting_text)}</span>
</a>
"""
        )

    mode_label = INTENT_LABELS.get(selected_intent, INTENT_LABELS["general"])

    render_html(
        f"""
<div class="fixed-top">
<h1>Bike Science Pro</h1>
<p>Software that helps cyclists ask better questions—and then gives them evidence-based answers.</p>
<div class="decision-prompt">Have some of these on your mind?</div>
<div class="decision-grid">
{''.join(entry_markup)}
</div>
<div class="decision-mode">Current mode: {escape(mode_label)}</div>
</div>
"""
    )

    return selected_intent
