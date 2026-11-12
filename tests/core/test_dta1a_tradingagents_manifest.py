from pathlib import Path

import yaml

from core.applications.models import ApplicationManifest
from core.applications.validator import ContractValidator

TRADINGAGENTS_MANIFEST = """identity:
  app_id: tradingagents
  instance_id: tradingagents-local-default
  name: TradingAgents
  version: 0.7.1
  contract_version: 1.0.0
  publisher: TauricResearch
  manifest_version: 1
capabilities:
  - name: research-analysis
    description: Multi-agent financial market research and trading support
  - name: research-report-generation
    description: Structured research and report output generation
dependencies:
  - name: python
    version: ">=3.11"
    required: true
compatibility:
  - ethan 2026.11
interfaces:
  cli:
    kind: cli
    entrypoint: "python main.py"
permissions:
  - research-analysis
provenance:
  source: /home/fatsio/AI/TradingAgents
  repository: TauricResearch/TradingAgents
  revision: c454491
metadata:
  application_category: backend-agent-tool-pilot
  execution_model: cli-langgraph
  dedicated_react_page: "false"
  runtime_interface: "not-demonstrated"
"""


def test_proposed_tradingagents_manifest_is_valid():
    data = yaml.safe_load(TRADINGAGENTS_MANIFEST)
    result = ContractValidator().validate_manifest_data(data)
    assert result.is_valid is True
    assert result.status == "valid"
    assert result.identity is not None
    assert result.identity.app_id == "tradingagents"


def test_proposed_tradingagents_manifest_builds_canonical_model():
    data = yaml.safe_load(TRADINGAGENTS_MANIFEST)
    manifest = ApplicationManifest.from_mapping(data)
    assert manifest.identity.version == "0.7.1"
    assert [cap.name for cap in manifest.capabilities] == [
        "research-analysis",
        "research-report-generation",
    ]
    assert manifest.interfaces["cli"].kind == "cli"


def test_expected_no_executable_adapter_without_runtime_proof():
    # The manifest is explicitly a proposal; execution remains unimplemented.
    assert "runtime_interface: \"not-demonstrated\"" in TRADINGAGENTS_MANIFEST
