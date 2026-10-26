from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest
from core.plugins import odin_compose_config
from scripts import odin_compose_controller as controller
from scripts.odin_compose_controller import (
    PROBE_JS,
    ControllerHandler,
    command_for,
    project_available,
)


def test_controller_maps_fixed_project_operations(tmp_path, monkeypatch):
    compose = tmp_path / "examples" / "odin" / "compose.yaml"
    compose.parent.mkdir(parents=True)
    compose.write_text("services: {}\n")
    monkeypatch.setattr(odin_compose_config, "ODIN_REPO_DIR", compose.parent)
    monkeypatch.setattr(odin_compose_config, "ODIN_COMPOSE_FILE", compose)
    monkeypatch.setattr(controller, "ODIN_REPO_DIR", compose.parent)
    monkeypatch.setattr(controller, "ODIN_COMPOSE_FILE", compose)

    argv = command_for(["up", "-d"], compose.parent)
    assert argv == ["docker", "compose", "--project-name", "odin", "-f", str(compose), "up", "-d"]
    assert command_for(["down"], compose.parent) == [
        "docker",
        "compose",
        "--project-name",
        "odin",
        "-f",
        str(compose),
        "down",
    ]
    assert "-v" not in command_for(["down"], compose.parent)
    assert command_for(["config"], compose.parent)[-2:] == ["config", "--quiet"]
    assert command_for(["probe"], compose.parent)[-3:] == ["node", "-e", PROBE_JS]


@pytest.mark.parametrize(
    "args",
    [
        ["down", "-v"],
        ["exec", "odin", "sh", "-c", "id"],
        ["up", "-d", "--project-directory=/tmp"],
        ["logs", "--tail=501", "--no-color"],
        ["logs", "--tail=10;id", "--no-color"],
    ],
)
def test_controller_rejects_arbitrary_or_destructive_args(tmp_path, args):
    with pytest.raises(ValueError):
        command_for(args, tmp_path)


def test_project_available_requires_fixed_compose_file(tmp_path, monkeypatch):
    repo = tmp_path / "odin"
    repo.mkdir()
    monkeypatch.setattr(controller, "ODIN_REPO_DIR", repo)
    monkeypatch.setattr(controller, "ODIN_COMPOSE_FILE", repo / "compose.yaml")
    assert not project_available(repo)
    (repo / "compose.yaml").write_text("services: {}\n")
    assert project_available(repo)


def test_controller_rejects_a_foreign_compose_path(tmp_path):
    with pytest.raises(ValueError, match="outside the fixed project"):
        command_for(["up", "-d"], tmp_path)


def test_controller_requires_internal_token_and_rejects_unapproved_operation(tmp_path, monkeypatch):
    repo = tmp_path / "odin"
    repo.mkdir()
    (repo / "compose.yaml").write_text("services: {}\n")
    monkeypatch.setattr(controller, "ODIN_REPO_DIR", repo)
    monkeypatch.setattr(controller, "ODIN_COMPOSE_FILE", repo / "compose.yaml")
    handler = type(
        "TestControllerHandler",
        (ControllerHandler,),
        {"repo_dir": repo, "token": "test-token"},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/run"
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps({"args": ["ps", "--all", "--format", "json"]}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as unauthorized:
            urllib.request.urlopen(request)
        assert unauthorized.value.code == 401

        request.add_header("Authorization", "Bearer test-token")
        request.data = json.dumps({"args": ["exec", "odin", "sh"]}).encode()
        with pytest.raises(urllib.error.HTTPError) as rejected:
            urllib.request.urlopen(request)
        assert rejected.value.code == 422
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
