from pathlib import Path
import yaml

def test_security_compose_has_hardening() -> None:
    config = yaml.safe_load(Path("examples/quantar/docker-compose.security.yml").read_text())
    service = config["services"]["quantar"]
    assert service["read_only"] is True
    assert service["user"] == "1000:1000"
    assert "no-new-privileges:true" in service["security_opt"]
    assert "ALL" in service["cap_drop"]
    assert "docker.sock" not in str(service.get("volumes", []))
    assert config["networks"]["ethan_quantar_isolated"]["internal"] is True
