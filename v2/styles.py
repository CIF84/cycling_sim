import streamlit as st


def render_html(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


def inject_styles() -> None:
    render_html(
        """
<style>
/* paste the whole CSS block from streamlit_app_v2.py here */
</style>
"""
    )