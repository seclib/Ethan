"""ETHAN Event Bus — NATS Implementation"""

import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

try:
    import nats
    from nats.aio.client import Client as NATSClient
    from nats.aio.msg import Msg
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False


class Event:
    """ETHAN Event — immutable event object"""
    
    def __init__(
        self,
        type: str,
        source: str,
        payload: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ):
        self.id = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.{uuid.uuid4().hex[:8]}"
        self.type = type
        self.source = source
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.payload = payload or {}
        self.context = context or {}
        self.session_id = session_id or ""
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "context": self.context,
            "session_id": self.session_id,
        }
    
    def to_json(self) -> bytes:
        return json.dumps(self.to_dict()).encode()
    
    @classmethod
    def from_json(cls, data: bytes) -> "Event":
        obj = json.loads(data)
        return cls(
            type=obj.get("type", "unknown"),
            source=obj.get("source", "unknown"),
            payload=obj.get("payload", {}),
            context=obj.get("context", {}),
            session_id=obj.get("session_id", ""),
        )


class EventBus:
    """Event Bus — NATS-based communication"""
    
    def __init__(self, servers: str = "nats://nats:4222"):
        self.servers = servers
        self._client: Optional[NATSClient] = None
        self._subscriptions: Dict[str, Any] = {}
        
    async def connect(self) -> None:
        """Connect to NATS server"""
        if not NATS_AVAILABLE:
            raise RuntimeError("NATS library not available. Install with: pip install nats-py")
        
        if self._client is not None:
            return
        
        self._client = await nats.connect(self.servers)
        
    async def disconnect(self) -> None:
        """Disconnect from NATS server"""
        if self._client:
            await self._client.close()
            self._client = None
            self._subscriptions = {}
    
    async def publish(self, subject: str, event: Event) -> None:
        """Publish an event to a subject"""
        if self._client is None:
            raise RuntimeError("Not connected to NATS")
        
        await self._client.publish(subject, event.to_json())
        
    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Event], Any],
        queue: Optional[str] = None,
    ) -> None:
        """Subscribe to a subject"""
        if self._client is None:
            raise RuntimeError("Not connected to NATS")
        
        async def handler(msg: Msg) -> None:
            event = Event.from_json(msg.data)
            await callback(event)
        
        sub = await self._client.subscribe(subject, cb=handler, queue=queue)
        self._subscriptions[subject] = sub
    
    async def request(self, subject: str, event: Event, timeout: float = 5.0) -> Optional[Event]:
        """Request-reply pattern"""
        if self._client is None:
            raise RuntimeError("Not connected to NATS")
        
        msg = await self._client.request(subject, event.to_json(), timeout=timeout)
        if msg:
            return Event.from_json(msg.data)
        return None
    
    async def unsubscribe(self, subject: str) -> None:
        """Unsubscribe from a subject"""
        if subject in self._subscriptions:
            await self._subscriptions[subject].unsubscribe()
            del self._subscriptions[subject]
    
    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.disconnect()