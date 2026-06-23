"""System State Panel component for ETHAN UI."""

import streamlit as st
import config
from api_client import EthanAPIClient

client = EthanAPIClient()


def render_state() -> None:
    st.title("🖥️ System State")

    state = client.get_state()
    if not state:
        st.warning("Unable to fetch system state")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Mode", state.get("mode", "unknown"))
    with col2:
        st.metric("Active Goal", state.get("active_goal", "none"))
    with col3:
        st.metric("Running Tasks", state.get("running_tasks", 0))

    st.subheader("Last Event")
    last = state.get("last_event")
    if last:
        st.json(last)
    else:
        st.info("No events yet")