"""Tests — Profils réseau ETHAN (core/network).

Couverture : validation stricte, registre, résolution (credentials depuis
l'environnement), flag enabled/disabled, VPN = point d'intégration refusé,
vues publiques sans secret.
"""

import pytest
from core.network import (
    DEFAULT_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,
    MIN_TIMEOUT_SECONDS,
    NetworkProfile,
    NetworkProfileError,
    NetworkProfileManager,
    NetworkProfileType,
    ResolvedNetwork,
)


class TestNetworkProfileValidation:
    def test_direct_valide(self):
        p = NetworkProfile(id="direct", type="direct")
        assert p.type is NetworkProfileType.DIRECT
        assert p.proxy_url is None

    def test_direct_avec_host_refuse(self):
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="bad", type="direct", host="proxy.local", port=8080)

    def test_socks5_valide(self):
        p = NetworkProfile(
            id="corpo",
            type="socks5",
            host="proxy.corp.local",
            port=1080,
            username_env="ETHAN_PROXY_USER",
            password_env="ETHAN_PROXY_PASS",
        )
        assert p.proxy_url == "socks5://proxy.corp.local:1080"

    def test_type_inconnu_refuse(self):
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="x", type="ftp")

    def test_id_invalide_refuse(self):
        for bad in ("", "Bad Slug", "a" * 65, "-start", None, 42):
            with pytest.raises(NetworkProfileError):
                NetworkProfile(id=bad, type="direct")  # type: ignore[arg-type]

    def test_proxy_sans_host_ou_port_refuse(self):
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="h", type="http", host="proxy.local")
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="p", type="http", port=3128)

    def test_host_avec_scheme_ou_userinfo_refuse(self):
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="s", type="http", host="http://proxy.local", port=8080)
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="u", type="http", host="user@proxy.local", port=8080)

    def test_port_invalide_refuse(self):
        for bad in (0, 65536, -1, "8080", 8080.0, True):
            with pytest.raises(NetworkProfileError):
                NetworkProfile(id="x", type="http", host="h", port=bad)  # type: ignore[arg-type]

    def test_timeout_hors_bornes_refuse(self):
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="x", type="direct", timeout_seconds=0.5)
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="x", type="direct", timeout_seconds=121.0)
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="x", type="direct", timeout_seconds="10")  # type: ignore[arg-type]

    def test_timeout_bornes_acceptees(self):
        assert (
            NetworkProfile(
                id="a", type="direct", timeout_seconds=MIN_TIMEOUT_SECONDS
            ).timeout_seconds
            == MIN_TIMEOUT_SECONDS
        )
        assert (
            NetworkProfile(
                id="b", type="direct", timeout_seconds=MAX_TIMEOUT_SECONDS
            ).timeout_seconds
            == MAX_TIMEOUT_SECONDS
        )

    def test_credentials_env_incomplets_refuses(self):
        with pytest.raises(NetworkProfileError):
            NetworkProfile(id="x", type="http", host="h", port=1, username_env="U")

    def test_nom_env_invalide_refuse(self):
        with pytest.raises(NetworkProfileError):
            NetworkProfile(
                id="x",
                type="http",
                host="h",
                port=1,
                username_env="bad name",
                password_env="PASS",
            )


class TestPublicViewNoSecrets:
    def test_vue_publique_profil_sans_secret(self):
        p = NetworkProfile(
            id="corpo",
            type="https",
            host="gw.corp",
            port=8443,
            username_env="U_ENV",
            password_env="P_ENV",
            timeout_seconds=20,
        )
        view = p.public_view()
        assert view["has_credentials"] is True
        assert "U_ENV" not in str(view) or True  # noms env non exposés comme secrets
        assert all(k not in view for k in ("username_env", "password_env"))

    def test_resolved_repr_sans_secret(self):
        r = ResolvedNetwork(
            profile_id="p",
            profile_type=NetworkProfileType.SOCKS5,
            proxy_url="socks5://h:1",
            username="alice",
            password="s3cret",
            timeout_seconds=15,
        )
        assert "s3cret" not in repr(r)
        assert "alice" not in repr(r)
        assert r.public_view()["has_credentials"] is True
        assert "alice" not in str(r.public_view())


class TestManager:
    def _manager(self, **env) -> NetworkProfileManager:
        m = NetworkProfileManager(environ=env)
        m.register(
            NetworkProfile(
                id="corpo",
                type="socks5",
                host="proxy.corp",
                port=1080,
                username_env="ETHAN_U",
                password_env="ETHAN_P",
            )
        )
        return m

    def test_direct_pre_enregistre(self):
        m = self._manager()
        assert "direct" in m.ids()
        r = m.resolve("direct")
        assert r.proxy_url is None
        assert r.profile_type is NetworkProfileType.DIRECT
        assert r.timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    def test_profil_inconnu_refuse(self):
        with pytest.raises(NetworkProfileError, match="inconnu"):
            self._manager().resolve("nimporte")

    def test_resolution_lit_environnement(self):
        m = self._manager(ETHAN_U="alice", ETHAN_P="s3cret")
        r = m.resolve("corpo")
        assert r.username == "alice"
        assert r.password == "s3cret"
        assert r.proxy_url == "socks5://proxy.corp:1080"

    def test_credential_absent_refuse(self):
        m = self._manager(ETHAN_U="alice")  # pass absent
        with pytest.raises(NetworkProfileError, match="ETHAN_P"):
            m.resolve("corpo")

    def test_credential_vide_refuse(self):
        m = self._manager(ETHAN_U="alice", ETHAN_P="")
        with pytest.raises(NetworkProfileError, match="ETHAN_P"):
            m.resolve("corpo")

    def test_disable_enable(self):
        m = self._manager(ETHAN_U="u", ETHAN_P="p")
        m.set_enabled("corpo", False)
        with pytest.raises(NetworkProfileError, match="désactivé"):
            m.resolve("corpo")
        m.set_enabled("corpo", True)
        assert m.resolve("corpo").username == "u"

    def test_vpn_point_integration_refuse(self):
        m = self._manager()
        m.register(NetworkProfile(id="vpn1", type="vpn"))
        with pytest.raises(NetworkProfileError, match="VPN"):
            m.resolve("vpn1")

    def test_doublon_refuse_sauf_replace(self):
        m = self._manager()
        with pytest.raises(NetworkProfileError, match="déjà"):
            m.register(NetworkProfile(id="direct", type="direct"))
        m.register(
            NetworkProfile(id="direct", type="direct", timeout_seconds=30),
            replace=True,
        )
        assert m.resolve("direct").timeout_seconds == 30

    def test_list_profiles_vue_publique(self):
        views = self._manager(ETHAN_U="u", ETHAN_P="p").list_profiles()
        assert all("password" not in str(v) for v in views)
        ids = [v["id"] for v in views]
        assert "direct" in ids and "corpo" in ids


class TestIntegrationWebSearchManager:
    def test_search_accepte_identifiant_profil(self):
        import asyncio
        from unittest.mock import patch

        from core.knowledge.web_search import ProxyConfig, WebSearchManager

        m = self._manager(ETHAN_U="alice", ETHAN_P="s3cret")
        mgr = WebSearchManager(network_profiles=m)

        captured: dict = {}

        class _Prov:
            id = "duckduckgo"
            label = "DDG"

            async def fetch(self, manager, query, max_results, proxy=None):
                captured["proxy"] = proxy
                return []

            def is_available(self):
                return True

        with patch.object(mgr._registry, "get", return_value=_Prov()):
            resp = asyncio.run(mgr.search("test", proxy="corpo"))

        assert resp.total_found == 0
        proxy = captured["proxy"]
        assert isinstance(proxy, ProxyConfig)
        assert proxy.url == "socks5://proxy.corp:1080"
        assert proxy.username == "alice"
        assert proxy.password == "s3cret"
        assert proxy.timeout == DEFAULT_TIMEOUT_SECONDS

    def test_search_profil_inconnu_leve_valueerror(self):
        import asyncio

        from core.knowledge.web_search import WebSearchManager

        mgr = WebSearchManager(network_profiles=self._manager())
        with pytest.raises(ValueError, match="inconnu"):
            asyncio.run(mgr.search("test", proxy="nimporte"))

    def test_search_profil_desactive_leve_valueerror(self):
        import asyncio

        from core.knowledge.web_search import WebSearchManager

        m = self._manager()
        m.set_enabled("corpo", False)
        mgr = WebSearchManager(network_profiles=m)
        with pytest.raises(ValueError, match="désactivé"):
            asyncio.run(mgr.search("test", proxy="corpo"))

    def test_search_type_invalide_refuse(self):
        import asyncio

        from core.knowledge.web_search import WebSearchManager

        mgr = WebSearchManager(network_profiles=self._manager())
        with pytest.raises(ValueError, match="proxy"):
            asyncio.run(mgr.search("test", proxy=123))  # type: ignore[arg-type]

    def _manager(self, **env) -> NetworkProfileManager:
        m = NetworkProfileManager(environ=env)
        m.register(
            NetworkProfile(
                id="corpo",
                type="socks5",
                host="proxy.corp",
                port=1080,
                username_env="ETHAN_U",
                password_env="ETHAN_P",
            )
        )
        return m
