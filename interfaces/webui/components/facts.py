"""Facts Dashboard — visualisation des faits atomiques et relations."""

import streamlit as st
import httpx


def render_facts(api_url: str) -> None:
    st.header("🧠 Faits atomiques")
    st.caption("Mémoire structurée : sujets, prédicats, objets, relations")

    tab1, tab2, tab3 = st.tabs(["📖 Explorer", "🔍 Rechercher", "🔗 Relations"])

    with tab1:
        _render_explore(api_url)
    with tab2:
        _render_search(api_url)
    with tab3:
        _render_relations(api_url)


def _render_explore(api_url: str) -> None:
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Statut", ["active", "superseded", "needs_review", "archived", "tous"])
    with col2:
        category_filter = st.selectbox(
            "Catégorie",
            ["toutes", "preference", "project", "goal", "identity", "knowledge", "skill", "event", "observation", "rule", "system"],
        )
    limit = st.slider("Nombre de faits", 5, 100, 20)

    params = {"limit": limit}
    if status_filter != "tous":
        params["status"] = status_filter
    if category_filter != "toutes":
        params["category"] = category_filter

    try:
        resp = httpx.get(f"{api_url}/internal/facts", params=params, timeout=5)
        if resp.status_code == 200:
            facts = resp.json()
            if facts:
                for f in facts:
                    confidence_pct = f.get("confidence", 0.5) * 100
                    with st.container(border=True):
                        st.write(f"**{f.get('subject', '?')}** → *{f.get('predicate', '?')}* → **{f.get('object', '?')}**")
                        cols = st.columns(4)
                        cols[0].caption(f"📂 {f.get('category', '?')}")
                        cols[1].caption(f"🏷 {f.get('status', '?')}")
                        cols[2].caption(f"🎯 {confidence_pct:.0f}%")
                        cols[3].caption(f"🆔 {f.get('id', '?')[:12]}…")
            else:
                st.info("Aucun fait trouvé")
        else:
            st.info("API facts non disponible (module optionnel)")
    except Exception:
        st.info("API facts non disponible")


def _render_search(api_url: str) -> None:
    query = st.text_input("Recherche plein texte", placeholder="Ex: marathon, projet, préférence…")
    if query:
        try:
            resp = httpx.get(f"{api_url}/internal/facts/search", params={"q": query}, timeout=5)
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    for r in results:
                        f = r.get("fact", r)
                        score = r.get("score", 0)
                        with st.container(border=True):
                            st.write(f"**{f.get('subject', '?')}** → *{f.get('predicate', '?')}* → **{f.get('object', '?')}**")
                            st.caption(f"Score: {score:.2f} | {f.get('category', '?')} | {f.get('status', '?')}")
                else:
                    st.info("Aucun résultat")
            else:
                st.info("Recherche indisponible")
        except Exception:
            st.info("Recherche indisponible")


def _render_relations(api_url: str) -> None:
    fact_id = st.text_input("ID du fait", placeholder="fct_abc123…")
    if fact_id:
        try:
            resp = httpx.get(f"{api_url}/internal/facts/{fact_id}/relations", timeout=5)
            if resp.status_code == 200:
                relations = resp.json()
                if relations:
                    for r in relations:
                        with st.container(border=True):
                            st.write(f"{r.get('from_fact_id', '?')[:12]}… **{r.get('relation_type', '?')}** → {r.get('to_fact_id', '?')[:12]}…")
                            st.caption(f"Créé: {r.get('created_at', '?')[:19]}")
                else:
                    st.info("Aucune relation")
            else:
                st.info("Relations indisponibles")
        except Exception:
            st.info("Relations indisponibles")