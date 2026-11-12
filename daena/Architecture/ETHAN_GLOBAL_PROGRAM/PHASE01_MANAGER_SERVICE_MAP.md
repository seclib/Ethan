# Phase 01 — Manager / Service Map

## Managers / services

| Manager/service | File | Responsibility |
|---|---|---|
| ProviderManager | `core/llm/provider_manager.py` | providers, models, secrets in memory, chat routing |
| PluginRegistry | `core/plugins` | catalog and plugin lifecycle |
| ApplicationRegistry | `core/applications/application_registry.py` | app registration/compliance/lifecycle persistence |
| ApplicationDiscoveryService | `core/applications/discovery.py` | manifest discovery, declared capabilities |
| OdinService | `core/plugins/odin.py` | docker controller, status, install, start, stop |
| FrameService | `core/plugins/frame.py` + ComposeService | compose-based Frame runtime |
| QuantarService | `core/applications/quantar_service.py`, `core/plugins/quantar.py` | Docker image/run + status |
| HROT gateway | `core/security/hrot_provider_gateway.py` | authorization + adapter execution in process |
| Rust contracts | `core/rust/...`, `core/rust/.../Cargo.toml` | typed contract binaries (health/capability) |

## Not integrated / non-executable link
- Quantar provider gateway transport from worker to ETHAN is not implemented; documented blocked.
