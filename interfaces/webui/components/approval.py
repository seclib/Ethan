"""Approval Dashboard — Interface de gestion des approbations en attente."""

import streamlit as st
import httpx


def render_approval(api_url: str) -> None:
    st.header("✅ Approbations")
    st.caption("Gestion des demandes d'approbation en attente")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Demandes en attente")
        _render_pending(api_url)

    with col2:
        st.subheader("Actions rapides")
        _render_quick_actions(api_url)


def _render_pending(api_url: str) -> None:
    try:
        resp = httpx.get(f"{api_url}/internal/approval/pending", timeout=5)
        if resp.status_code == 200:
            pending = resp.json()
            if not pending:
                st.info("Aucune approbation en attente")
                return

            for req in pending:
                with st.container(border=True):
                    cols = st.columns([3, 1, 1])
                    cols[0].write(f"**{req.get('title', '?')}**")
                    cols[0].caption(f"{req.get('category', '?')} | {req.get('source', '?')}")
                    cols[1].metric("Timeout", f"{req.get('timeout_seconds', 300)}s")
                    if cols[2].button("Approuver", key=f"approve_{req['request_id']}"):
                        _resolve(api_url, req["request_id"], True)
                        st.rerun()
                    if cols[2].button("Rejeter", key=f"reject_{req['request_id']}"):
                        _resolve(api_url, req["request_id"], False)
                        st.rerun()
        else:
            st.info("API approbation non disponible")
    except Exception:
        st.info("API approbation non disponible")


def _render_quick_actions(api_url: str) -> None:
    st.write("**Créer une demande d'approbation test**")
    with st.form("test_approval"):
        category = st.selectbox(
            "Catégorie",
            ["file_write", "command_exec", "network_access", "plugin_install", "skill_install"],
        )
        title = st.text_input("Titre", value="Test approbation")
        description = st.text_area("Description", value="Ceci est un test")
        submitted = st.form_submit_button("Créer")
        if submitted:
            st.info("Utilisez l'API POST /internal/approval/resolve pour tester")


def _resolve(api_url: str, request_id: str, approved: bool) -> None:
    try:
        httpx.post(
            f"{api_url}/internal/approval/resolve",
            json={
                "request_id": request_id,
                "approved": approved,
                "reason": "Résolu depuis le dashboard",
                "responder": "human",
            },
            timeout=5,
        )
    except Exception as e:
        st.error(f"Erreur: {e}")