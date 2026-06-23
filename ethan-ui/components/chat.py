"""Chat component for ETHAN UI."""

import streamlit as st
from datetime import datetime
from api_client import EthanAPIClient

client = EthanAPIClient()


def render_chat() -> None:
    st.title("💬 ETHAN Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            st.caption(msg.get("time", ""))

    if prompt := st.chat_input("Message ETHAN"):
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(datetime.now().strftime("%H:%M:%S"))

        response = client.send_message(prompt)
        answer = response.get("response", response.get("error", "No response"))

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        with st.chat_message("assistant"):
            st.markdown(answer)
            st.caption(datetime.now().strftime("%H:%M:%S"))