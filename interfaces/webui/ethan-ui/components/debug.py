"""Debug Console component for ETHAN UI."""

import streamlit as st
import config
from api_client import EthanAPIClient

client = EthanAPIClient()


def render_debug() -> None:
    st.title("🛠️ Debug Console")

    if "logs" not in st.session_state:
        st.session_state.logs = []

    logs = client.get_logs()
    if logs:
        st.session_state.logs = logs[-config.MAX_EVENTS:]

    for log in reversed(st.session_state.logs):
        level = log.get("level", "info").lower()
        color = {
            "error": "🔴",
            "warning": "🟡",
            "info": "🔵",
            "debug": "⚪",
        }.get(level, "⚪")

        st.markdown(f"{color} **{log.get('source', '?')}** — {log.get('message', '')}")
        st.caption(log.get("timestamp", ""))