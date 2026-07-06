"""SkillLab Dashboard — Interface de test et validation de skills."""

import json
import streamlit as st
import httpx


def render_skill_lab(api_url: str) -> None:
    st.header("🧪 Skill Lab")
    st.caption("Sandbox de test et validation des plugins/skills")

    tab1, tab2, tab3 = st.tabs(["▶️ Tester", "✅ Valider", "📊 Résultats"])

    with tab1:
        _render_test(api_url)
    with tab2:
        _render_validate(api_url)
    with tab3:
        _render_results(api_url)


def _render_test(api_url: str) -> None:
    st.subheader("Tester un skill")
    with st.form("test_skill"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nom du skill", value="mon_skill")
            code = st.text_area(
                "Code Python",
                value="print('Hello from skill')\nresult = {'status': 'ok'}",
                height=200,
            )
        with col2:
            test_input = st.text_input("Entrée de test", value="")
            requirements = st.text_input("Dépendances pip (séparées par virgule)", value="")
        submitted = st.form_submit_button("▶️ Lancer le test")
        if submitted:
            reqs = [r.strip() for r in requirements.split(",") if r.strip()]
            with st.spinner("Test en cours..."):
                try:
                    resp = httpx.post(
                        f"{api_url}/internal/skilllab/test",
                        json={
                            "code": code,
                            "name": name,
                            "input": test_input,
                            "requirements": reqs,
                        },
                        timeout=120,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        _show_result(result)
                    else:
                        st.error(f"Erreur API: {resp.status_code}")
                except Exception as e:
                    st.error(f"Erreur: {e}")


def _render_validate(api_url: str) -> None:
    st.subheader("Valider un plugin")
    with st.form("validate_plugin"):
        plugin_path = st.text_input("Chemin du dossier plugin", value="./mon-plugin")
        submitted = st.form_submit_button("✅ Valider")
        if submitted:
            with st.spinner("Validation en cours..."):
                try:
                    resp = httpx.post(
                        f"{api_url}/internal/skilllab/validate",
                        json={"path": plugin_path},
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        st.json(result.get("details", {}))
                        if result.get("passed"):
                            st.success("✅ Plugin valide")
                        else:
                            st.error("❌ Plugin invalide")
                    else:
                        st.error(f"Erreur API: {resp.status_code}")
                except Exception as e:
                    st.error(f"Erreur: {e}")


def _render_results(api_url: str) -> None:
    st.subheader("Historique des tests")
    try:
        resp = httpx.get(f"{api_url}/internal/skilllab/results", timeout=5)
        if resp.status_code == 200:
            results = resp.json()
            if not results:
                st.info("Aucun test enregistré")
                return
            for r in results:
                with st.container(border=True):
                    cols = st.columns([2, 1, 1])
                    cols[0].write(f"**{r.get('skill_name', '?')}**")
                    cols[0].caption(f"ID: {r.get('id', '?')[:12]}…")
                    status = r.get("status", "?")
                    icon = {"passed": "✅", "failed": "❌", "error": "⚠️"}.get(status, "❓")
                    cols[1].write(f"{icon} {status}")
                    cols[2].caption(f"{r.get('duration_ms', 0):.0f}ms")
                    if r.get("output"):
                        with st.expander("Sortie"):
                            st.code(r["output"])
                    if r.get("error"):
                        with st.expander("Erreur"):
                            st.code(r["error"])
        else:
            st.info("API SkillLab non disponible")
    except Exception:
        st.info("API SkillLab non disponible")


def _show_result(result: dict) -> None:
    status = result.get("status", "?")
    passed = result.get("passed", False)
    if passed:
        st.success(f"✅ Test réussi ({result.get('duration_ms', 0):.0f}ms)")
    else:
        st.error(f"❌ Test échoué ({result.get('duration_ms', 0):.0f}ms)")
    if result.get("output"):
        st.code(result["output"], language="python")
    if result.get("error"):
        st.error(result["error"])