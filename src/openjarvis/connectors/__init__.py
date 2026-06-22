"""Data source connectors for Deep Research."""

from ethan.connectors._stubs import (
    Attachment,
    BaseConnector,
    Document,
    SyncStatus,
)
from ethan.connectors.store import KnowledgeStore

__all__ = ["Attachment", "BaseConnector", "Document", "KnowledgeStore", "SyncStatus"]

# Auto-register built-in connectors
import ethan.connectors.obsidian  # noqa: F401

try:
    import ethan.connectors.gmail  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.gmail_imap  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.gdrive  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import ethan.connectors.notion  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.granola  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.gcontacts  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.imessage  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.apple_notes  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.apple_music  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.apple_contacts  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.slack_connector  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.outlook  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.gcalendar  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.dropbox  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import ethan.connectors.whatsapp  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.oura  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.apple_health  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.strava  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.spotify  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.google_tasks  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.weather  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.github_notifications  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.hackernews  # noqa: F401
except ImportError:
    pass

try:
    import ethan.connectors.news_rss  # noqa: F401
except ImportError:
    pass
