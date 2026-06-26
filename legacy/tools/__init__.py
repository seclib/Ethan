"""Tools primitive — tool system with ABC interface and built-in tools."""

from __future__ import annotations

from ethan.tools._stubs import BaseTool, ToolExecutor, ToolSpec

# Import built-in tools to trigger @ToolRegistry.register() decorators.
# Each is wrapped in try/except so the package loads even before the
# individual tool modules are created.
try:
    import ethan.tools.calculator  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.think  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.retrieval  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.llm_tool  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.file_read  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.web_search  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.code_interpreter  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.code_interpreter_docker  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.repl  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.storage_tools  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.mcp_adapter  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.channel_tools  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.http_request  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.docker_shell_exec  # noqa: F401
    import ethan.tools.shell_exec  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.memory_manage  # noqa: F401
except ImportError:
    pass
try:
    import ethan.tools.user_profile_manage  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.skill_manage  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.file_write  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.apply_patch  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.git_tool  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.db_query  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.pdf_tool  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.image_tool  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.audio_tool  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.knowledge_tools  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.text_to_speech  # noqa: F401
except ImportError:
    pass

try:
    import ethan.tools.digest_collect  # noqa: F401
except ImportError:
    pass

__all__ = ["BaseTool", "ToolExecutor", "ToolSpec"]
