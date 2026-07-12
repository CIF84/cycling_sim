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
        "users",
    ),
    (
        "compare_setups",
        "Compare bike setups",
        "Which bike, tire, weight, or position works better for this ride?",
        "bike",
    ),
    (
        "compare_routes",
        "Compare routes",
        "Which route better fits this rider and setup?",
        "route",
    ),
    (
        "plan_fueling",
        "Plan fueling",
        "What should I eat and drink for this ride?",
        "bottle",
    ),
    (
        "hack_ride",
        "Hack my ride",
        "Where are the biggest realistic gains?",
        "bolt",
    ),
)

ICON_SVGS = {
    "users": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"></path><circle cx="9.5" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
    "bike": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5.5" cy="17.5" r="3.5"></circle><circle cx="18.5" cy="17.5" r="3.5"></circle><path d="M15 6h2l1.5 4"></path><path d="M8 6h3l4 11"></path><path d="M5.5 17.5 10 11h4l-3 6.5"></path></svg>',
    "route": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="6" r="3"></circle><circle cx="18" cy="18" r="3"></circle><path d="M9 6h4a4 4 0 0 1 0 8h-2a4 4 0 0 0 0 8h4"></path></svg>',
    "bottle": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 2h4v4h-4z"></path><path d="M9 6h6l1 3v11a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V9z"></path><path d="M8 13h8"></path></svg>',
    "bolt": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2 4 14h7l-1 8 10-13h-7z"></path></svg>',
}


def _current_intent() -> str:
    intent = st.session_state.get(INTENT_SESSION_KEY, "general")
    if intent not in INTENT_LABELS:
        return "general"
    return intent


def set_intent(intent: str) -> None:
    if intent not in INTENT_LABELS:
        intent = "general"

    st.session_state[INTENT_SESSION_KEY] = intent
    st.query_params["intent"] = intent


def clear_intent() -> None:
    set_intent("general")


def _intent_from_query_params() -> str | None:
    intent = st.query_params.get("intent")
    if isinstance(intent, list):
        intent = intent[0] if intent else None
    if intent in INTENT_LABELS:
        return intent
    return None


def _raw_intent_query_param() -> str | None:
    intent = st.query_params.get("intent")
    if isinstance(intent, list):
        return intent[0] if intent else None
    return intent


def render_decision_launchpad(render_html) -> str:
    if INTENT_SESSION_KEY not in st.session_state:
        st.session_state[INTENT_SESSION_KEY] = _intent_from_query_params() or "general"
        st.query_params["intent"] = st.session_state[INTENT_SESSION_KEY]

    selected_intent = _current_intent()
    if _raw_intent_query_param() != selected_intent:
        st.query_params["intent"] = selected_intent

    mode_label = INTENT_LABELS.get(selected_intent, INTENT_LABELS["general"])

    with st.container(key="decision_launchpad_fixed"):
        render_html(
            """
<div class="decision-shell">
<h1>Bike Science Pro</h1>
<p>Software that helps cyclists ask better questions—and then gives them evidence-based answers.</p>
<div class="decision-prompt">Have some of these on your mind?</div>
</div>
"""
        )

        card_columns = st.columns(5, gap="small")
        for column, (intent, label, supporting_text, icon_name) in zip(card_columns, LAUNCHPAD_ENTRIES):
            with column:
                with st.container(key=f"decision_card_{intent}"):
                    active_class = " active" if selected_intent == intent else ""
                    selected_marker = (
                        '<span class="decision-entry-marker">Selected</span>' if selected_intent == intent else ""
                    )
                    render_html(
                        f"""
<div class="decision-card{active_class}">
<div class="decision-entry">
<span class="decision-icon">{ICON_SVGS[icon_name]}</span>
<span class="decision-entry-copy">{selected_marker}<span class="decision-entry-title">{escape(label)}</span><span class="decision-entry-support">{escape(supporting_text)}</span></span>
<span class="decision-arrow" aria-hidden="true">→</span>
</div>
</div>
"""
                    )
                    st.button(
                        label,
                        key=f"decision_intent_{intent}",
                        help=supporting_text,
                        on_click=set_intent,
                        args=(intent,),
                        use_container_width=True,
                    )

        mode_col, reset_col = st.columns([1, 4], gap="small", vertical_alignment="center")
        with mode_col:
            render_html(
                f"""
<div class="decision-mode"><span>Exploring:</span> {escape(mode_label)}</div>
"""
            )
        with reset_col:
            st.button(
                "General exploration",
                key="decision_intent_general",
                on_click=clear_intent,
                type="tertiary",
            )

    return selected_intent
