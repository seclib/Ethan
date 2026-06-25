"""Goal Tracker component for ETHAN UI."""

import streamlit as st
import config
from api_client import EthanAPIClient

client = EthanAPIClient()


def render_goals() -> None:
    st.title("🎯 Goal Tracker")

    goals = client.get_goals()
    if not goals:
        st.info("No goals found")
        return

    for goal in goals:
        status = goal.get("status", "unknown")
        priority = goal.get("priority", "medium")

        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{goal.get('id', '?')[:8]}** — {goal.get('description', 'No description')}")
            with col2:
                st.badge(status, color="blue" if status == "active" else "gray")
            with col3:
                st.caption(f"Priority: {priority}")