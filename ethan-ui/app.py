"""ETHAN Cognitive OS — Debug & Interaction UI."""

import streamlit as st
from components.chat import render_chat
from components.events import render_events
from components.state import render_state
from components.goals import render_goals
from components.debug import render_debug
import config

st.set_page_config(
    page_title="ETHAN Cognitive OS",
    page_icon="🧠",
    layout="wide",
)

st.sidebar.title("🧠 ETHAN OS")
page = st.sidebar.radio(
    "Navigation",
    ["Chat", "Events", "State", "Goals", "Debug"],
)

if page == "Chat":
    render_chat()
elif page == "Events":
    render_events()
elif page == "State":
    render_state()
elif page == "Goals":
    render_goals()
elif page == "Debug":
    render_debug()

st.sidebar.markdown("---")
st.sidebar.caption(f"API: {config.API_URL}")
st.sidebar.caption(f"Refresh: {config.EVENT_REFRESH_INTERVAL}s")