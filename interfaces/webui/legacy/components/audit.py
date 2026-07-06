"""Audit Dashboard — visualisation du journal d'audit immuable."""

import json
from datetime import datetime, timedelta
from typing import Any

import streamlit as st
import httpx


def render_audit(api_url: str) -> None:
    st.header("📋 Journal d'audit")
    st.caption("Traçabilité immuable de toutes les décisions système")

    col1, col2, col3 = st.columns(3)
    with col1:
        limit = st.number_input("Entrées à afficher", min_value=10, max_value=500, value=50)
    with col2:
        days = st.number_input("Jours en arrière", min_value=1, max_value=90, value=7)
    with col3:
        st.metric("Auto-refresh", f"{2}s")

    since = (datetime.utcnow() - timedelta(days=int(days))).isoformat()

    tab1, tab2, tab3 = st.tabs(["📄 Entrées", "📊 Résumé", "🔍 Recherche"])

    with tab1:
        _render_entries(api_url, limit, since)
    with tab2:
        _render_summary(api_url, since)
    with tab3:
        _render_search(api_url)


def _render_entries(api_url: str, limit: int, since: str) -> None:
    filters = {
        "category": st.selectbox(
            "Filtrer par catégorie",
            ["Toutes", "system", "command", "approval", "budget", "gate", "plugin", "skill", "memory", "security", "error", "mission", "proactive"],
        ),
        "decision": st.selectbox(
            "Filtrer par décision",
            ["Toutes", "allowed", "denied", "approved", "rejected", "auto", "timeout", "error"],
        ),
    }

    category_filter = filters["category"] if filters["category"] != "Toutes" else None
    decision_filter = filters["decision"] if filters["decision"] != "Toutes" else None

    try:
        resp = httpx.get(
            f"{api_url}/internal/audit",
            params={
                "limit": limit,
                "category": category_filter,
                "decision": decision_filter,
                "since": since,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            entries = data if isinstance(data, list) else data.get("entries", [])
            if entries:
                st.dataframe(
                    [
                        {
                            "Horodatage": e.get("timestamp", "")[11:19],
                            "Catégorie": e.get("category", ""),
                            "Décision": e.get("decision", ""),
                            "Action": e.get("action", ""),
                            "Acteur": e.get("actor", ""),
                        }
                        for e in entries
                    ],
                    use_container_width=True,
                )
            else:
                st.info("Aucune entrée d'audit trouvée")
        else:
            st.info("API audit non disponible (module optionnel)")
    except Exception:
        st.info("API audit non disponible (module optionnel)")


def _render_summary(api_url: str, since: str) -> None:
    try:
        resp = httpx.get(f"{api_url}/internal/audit/summary?since={since}", timeout=5)
        if resp.status_code == 200:
            summary = resp.json()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total entrées", summary.get("total", "N/A"))
            with col2:
                st.metric("Catégories", len(summary.get("categories", {})))
            with col3:
                st.metric("Acteurs uniques", summary.get("actors", "N/A"))

            st.subheader("Entrées par catégorie")
            cats = summary.get("categories", {})
            if cats:
                st.bar_chart(cats)
        else:
            st.info("Résumé indisponible")
    except Exception:
        st.info("Résumé indisponible")


def _render_search(api_url: str) -> None:
    query = st.text_input("Rechercher dans l'audit", placeholder="ID, action, acteur...")
    if query:
        try:
            resp = httpx.get(f"{api_url}/internal/audit/search", params={"q": query}, timeout=5)
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    for r in results:
                        with st.container(border=True):
                            st.write(f"**{r.get('action', '?')}** — {r.get('category', '?')}")
                            st.caption(f"{r.get('timestamp', '?')} | {r.get('actor', '?')} → {r.get('decision', '?')}")
                else:
                    st.info("Aucun résultat")
        except Exception:
            st.info("Recherche indisponible")