import json
import socket
import urllib.error

import pytest
from interfaces.bridge.rust.health_adapter import (
    RustHealthClient,
    RustHealthTimeout,
    RustHealthUnavailable,
)

TARGET = "interfaces.bridge.rust.health_adapter.urllib.request.urlopen"


def test_get_health_success(monkeypatch):
    class FakeResponse:
        headers = {"Content-Type": "application/json"}
        def get_content_charset(self):
            return "utf-8"
        def read(self):
            return json.dumps({"status": "ok", "ready": True}).encode()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None

    monkeypatch.setattr(TARGET, lambda request, timeout: FakeResponse())
    client = RustHealthClient("http://127.0.0.1:18081/", timeout=1.0)
    assert client.get_health() == {"status": "ok", "ready": True}


def test_timeout(monkeypatch):
    def raise_timeout(request, timeout):
        raise socket.timeout("timed out")

    monkeypatch.setattr(TARGET, raise_timeout)
    client = RustHealthClient("http://127.0.0.1:18081", timeout=0.1)
    with pytest.raises(RustHealthTimeout):
        client.get_health()


def test_unavailable(monkeypatch):
    def raise_urlerror(request, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(TARGET, raise_urlerror)
    client = RustHealthClient("http://127.0.0.1:18081", timeout=0.1)
    with pytest.raises(RustHealthUnavailable):
        client.get_diagnostics_version()


def test_invalid_json(monkeypatch):
    class FakeResponse:
        def get_content_charset(self):
            return "utf-8"
        def read(self):
            return b"{not-json"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None

    monkeypatch.setattr(TARGET, lambda request, timeout: FakeResponse())
    client = RustHealthClient("http://127.0.0.1:18081", timeout=0.1)
    with pytest.raises(RustHealthUnavailable):
        client.get_health()
