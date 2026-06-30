"""Budget Dashboard — visualisation des coûts et alertes budgétaires."""

from datetime import datetime, timedelta

import streamlit as st
import httpx


def render_budget(api_url: str) -> None:
    st.header("💰 Budget & Coûts")
    st.caption("Suivi des dépenses LLM et alertes budgétaires")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Statut global")
        _render_global_status(api_url)

    with col2:
        st.subheader("Projets")
        _render_projects(api_url)

    st.subheader("Alertes récentes")
    _render_alerts(api_url)

    with st.expander("📊 Coûts journaliers", expanded=False):
        _render_daily_costs(api_url)


def _render_global_status(api_url: str) -> None:
    try:
        resp = httpx.get(f"{api_url}/internal/budget/status", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            enabled = data.get("enabled", False)
            global_data = data.get("global", {})

            if not enabled:
                st.warning("Budget désactivé")
                return

            spent = global_data.get("spent_usd", 0)
            limit = global_data.get("limit_usd", 0)
            remaining = global_data.get("remaining_usd", 0)
            pct = global_data.get("utilization_pct", 0)
            status = global_data.get("status", "ok")

            status_icon = {"ok": "🟢", "warning": "🟡", "hard_stop": "🔴"}.get(status, "⚪")
            st.metric(f"{status_icon} Budget mensuel", f"${spent:.2f}", f"${remaining:.2f} restant")
            st.progress(min(pct / 100, 1.0), text=f"{pct:.1f}% utilisé / ${limit:.0f}")
        else:
            st.info("API budget non disponible (module optionnel)")
    except Exception:
        st.info("API budget non disponible")


def _render_projects(api_url: str) -> None:
    try:
        resp = httpx.get(f"{api_url}/internal/budget/status", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            projects = data.get("projects", {})
            if projects:
                proj_data = [
                    {
                        "Projet": pid,
                        "Dépensé": f"${p['spent_usd']:.4f}",
                        "Limite": f"${p['limit_usd']:.2f}",
                        "Restant": f"${p['remaining_usd']:.4f}",
                    }
                    for pid, p in projects.items()
                ]
                st.dataframe(proj_data, use_container_width=True)
            else:
                st.info("Aucun projet suivi")
    except Exception:
        st.info("Projets non disponibles")


def _render_alerts(api_url: str) -> None:
    try:
        resp = httpx.get(f"{api_url}/internal/budget/alerts", timeout=5)
        if resp.status_code == 200:
            alerts = resp.json()
            if alerts:
                for a in alerts:
                    icon = {"warning": "🟡", "hard_stop": "🔴", "ok": "🟢"}.get(a.get("status", ""), "⚪")
                    with st.container(border=True):
                        st.write(f"{icon} **{a.get('message', '?')}**")
                        st.caption(f"Scope: {a.get('scope', '?')} | {a.get('timestamp', '?')[:19]}")
            else:
                st.info("Aucune alerte")
    except Exception:
        st.info("Alertes non disponibles")


def _render_daily_costs(api_url: str) -> None:
    days = 30
    try:
        resp = httpx.get(
            f"{api_url}/internal/budget/daily",
            params={"days": days},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                st.line_chart(
                    {d["date"]: d["cost_usd"] for d in data},
                    use_container_width=True,
                )
            else:
                st.info("Aucune donnée quotidienne")
    except Exception:
        st.info("Données quotidiennes non disponibles")