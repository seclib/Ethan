from __future__ import annotations
import streamlit as st
from typing import Any

def render_sidebar_header(title="ETHAN", icon="🧠"):
    st.sidebar.title(f"{icon} {title}")

def render_metric_card(label, value, delta=None, help_text=""):
    st.metric(label=label, value=value, delta=delta, help=help_text)

def render_api_error(error):
    st.error(f"API Error: {error}")

def render_empty_state(message):
    st.info(message)
