"""Event Stream Viewer component for ETHAN UI."""

import streamlit as st
from datetime import datetime
import config
from api_client import EthanAPIClient

client = EthanAPIClient()


def render_events() -> None:
    st.title("📡 Event Stream")

    if "events" not in st.session_state:
        st.session_state.events = []

    events = client.get_events()
    if events:
        st.session_state.events = events[-config.MAX_EVENTS:]

    for evt in reversed(st.session_state.events):
        with st.expander(f"[{evt.get('type', '?')}] {evt.get('source', '?')} — {evt.get('timestamp', '')[:19]}"):
            st.json(evt.get("data", {}))
            if evt.get("metadata"):
                st.caption(f"metadata: {evt['metadata']}")