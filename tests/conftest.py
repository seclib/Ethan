import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------------
# QUARANTAINE DES TESTS LEGACY (correctif minimal — test-infra uniquement).
#
# Le paquet applicatif historique `openjarvis` (865 fichiers sous src/) a été
# supprimé par le commit 6883042b ("Rebuild and Deployment", rebuild "Docker
# Foundation Clean Architecture"). Les entrées ci-dessous importent encore
# `openjarvis.*` ou d'autres modules racine supprimés et sont donc
# non-importables dans l'architecture reconstruite (core/, sdk/, plugins/,
# interfaces/).
#
# Ces tests sont MIS EN QUARANTAINE (collect_ignore) — pas supprimés — afin
# que `pytest` collecte une suite saine. Leur migration vers le code actuel
# (mapping openjarvis.* → core.*) reste à réaliser via une RFC dédiée.
#
# Non quarantainés :
#   - tests/cli/**  : reconnecté au code CLI actuel via pythonpath
#     ["interfaces"] (pyproject.toml) ;
#   - tests/core/** : seuls les fichiers hérités listés sont exclus, les
#     tests du code actuel restent actifs.
# ---------------------------------------------------------------------------
collect_ignore = [
    'a2a',
    'agents',
    'analytics',
    'bench',
    'channels',
    'connectors',
    'daemon',
    'engine',
    'evals',
    'hardware',
    'install',
    'integration',
    'intelligence',
    'learning',
    'mcp',
    'memory',
    'mining',
    'operators',
    'prompt',
    'recipes',
    'sandbox',
    'scheduler',
    'sdk',
    'security',
    'server',
    'sessions',
    'skills',
    'speech',
    'telemetry',
    'templates',
    'test_core',
    'test_orchestrator_learning',
    'tools',
    'traces',
    'workflow',
    'core/test_cognitive_loop.py',
    'core/test_config.py',
    'core/test_config_key_validation.py',
    'core/test_config_phase3.py',
    'core/test_config_phase4.py',
    'core/test_config_phase5.py',
    'core/test_config_skills_sources.py',
    'core/test_credentials.py',
    'core/test_plugins.py',
    'core/test_preset_configs.py',
    'core/test_recommend_model.py',
    'core/test_registry.py',
    'core/test_skills_learning_config.py',
    'core/test_types.py',
    'test_core.py',
    'test_digest_integration.py',
    'test_query_orchestrator.py',
    'test_vision.py',
    # ── tests/cli racine : tests de l'ancien CLI, importent openjarvis.* ──
    'cli/test_add_cmd.py',
    'cli/test_agent_cmd.py',
    'cli/test_ask_agent.py',
    'cli/test_ask_context.py',
    'cli/test_ask_e2e.py',
    'cli/test_ask_router.py',
    'cli/test_ask_vision.py',
    'cli/test_bench_cmd.py',
    'cli/test_bench_skills_command.py',
    'cli/test_channel_cmd.py',
    'cli/test_chat_cmd.py',
    'cli/test_cli.py',
    'cli/test_config_cmd.py',
    'cli/test_config_set.py',
    'cli/test_connect.py',
    'cli/test_daemon_cmd.py',
    'cli/test_dashboard.py',
    'cli/test_digest_cmd.py',
    'cli/test_doctor_cmd.py',
    'cli/test_doctor_labels.py',
    'cli/test_eval_cmd.py',
    'cli/test_hints.py',
    'cli/test_init_guidance.py',
    'cli/test_init_host.py',
    'cli/test_install_detect.py',
    'cli/test_log_config.py',
    'cli/test_memory_cmd.py',
    'cli/test_mine_cmd.py',
    'cli/test_model_cmd.py',
    'cli/test_model_pull.py',
    'cli/test_optimize_skills_command.py',
    'cli/test_pearl_cmd.py',
    'cli/test_quickstart.py',
    'cli/test_registry_cmd.py',
    'cli/test_scan.py',
    'cli/test_self_update.py',
    'cli/test_serve_channel_wiring.py',
    'cli/test_serve_model_resolution.py',
    'cli/test_serve_single_build.py',
    'cli/test_skill_cmd.py',
    'cli/test_telemetry_cmd.py',
    'cli/test_tool_cmd.py',
    'cli/test_vault_cmd.py',
    'cli/test_version_check.py',
    'cli/test_workflow_cmd.py',
    # ── tests/cli/ethan : anciens benchmarks/régression (API `COMMANDS`
    #    retirée de cli/registry.py lors du rebuild) ──
    'cli/ethan/benchmarks/test_command_performance.py',
    'cli/ethan/benchmarks/test_daemon_impact.py',
    'cli/ethan/benchmarks/test_memory_usage.py',
    'cli/ethan/regression/test_api_contracts.py',
    'cli/ethan/regression/test_command_matrix.py',
    'cli/ethan/regression/test_snapshot_regression.py',
    # ── fichiers important openjarvis.* au runtime (dans les fonctions) ──
    'core/test_rust_bridge.py',
    'core/test_intent_routing.py',
    'cli/test_deep_research_setup.py',
    'cli/test_eval_cmd_external_flags.py',
    'cli/ethan/regression/test_plugin_compat.py',
    # ── Tests de fonctionnalités SUPPRIMÉES / DÉPLACÉES (post-rebuild) ──
    # Le modèle de sécurité historique (check_bind_safety, OPENJARVIS_API_KEY,
    # auth_middleware, core/server/) a été supprimé lors du rebuild. Ces tests
    # vérifient des artefacts qui n'existent plus.
    'deploy/test_deploy_auth.py',
    # MemoryBackend a été déplacé de core/memory/ vers core/bus/backends/memory.py.
    'core/test_cognitive_memory.py',
    # Les commandes CLI (status, daemon) ont été refactorées vers le Docker SDK
    # direct : les fonctions alive/get_state/_fetch_state n'existent plus.
    'cli/ethan/commands/test_status.py',
    'cli/ethan/integration/test_failure_scenarios.py',
    'cli/ethan/unit/test_daemon.py',
]