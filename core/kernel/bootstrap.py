#!/usr/bin/env python3
"""ETHAN Kernel — Core Orchestrator Bootstrap"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.bus import EventBus
from core.registry import CapabilityRegistry
from core.executor import Executor
from core.planner import Planner
from core.state import StateManager

class Kernel:
    """ETHAN Kernel — Central Orchestrator"""
    
    def __init__(self):
        self.bus = EventBus()
        self.registry = CapabilityRegistry()
        self.executor = Executor()
        self.planner = Planner()
        self.state = StateManager()
        self.running = False
        
    async def start(self):
        """Start the kernel"""
        print("◆ ETHAN Kernel")
        print("  Core Orchestrator")
        print()
        
        # Connect to NATS
        print("Connecting to NATS...")
        await self.bus.connect("nats://nats:4222")
        print("  ✓ Connected to NATS")
        
        # Initialize components
        print("Initializing components...")
        await self.registry.start()
        print("  ✓ Capability Registry ready")
        
        await self.executor.start()
        print("  ✓ Executor ready")
        
        await self.planner.start()
        print("  ✓ Planner ready")
        
        await self.state.start()
        print("  ✓ State Manager ready")
        
        # Subscribe to events
        await self.setup_subscriptions()
        print("  ✓ Subscriptions configured")
        
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✓ Kernel is ready")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        
        self.running = True
        
        # Keep running
        while self.running:
            await asyncio.sleep(1)
            
    async def setup_subscriptions(self):
        """Setup event subscriptions"""
        # Interface events
        await self.bus.subscribe("ethan.interface.*", self.handle_interface_event)
        
        # Registry events
        await self.bus.subscribe("ethan.registry.*", self.handle_registry_event)
        
        # Executor events
        await self.bus.subscribe("ethan.executor.*", self.handle_executor_event)
        
    async def handle_interface_event(self, event):
        """Handle interface events"""
        event_type = event.get("type")
        
        if event_type == "interface.command":
            await self.handle_command(event)
        elif event_type == "interface.message":
            await self.handle_message(event)
            
    async def handle_command(self, event):
        """Handle CLI command"""
        payload = event.get("payload", {})
        command = payload.get("cmd")
        
        print(f"[KERNEL] Command received: {command}")
        
        # Create request
        request = {
            "type": "kernel.request.created",
            "source": "kernel",
            "payload": {
                "intent": command,
                "request_id": event.get("id")
            }
        }
        
        # Publish request
        await self.bus.publish("ethan.kernel.request.created", json.dumps(request).encode())
        
    async def handle_message(self, event):
        """Handle chat message"""
        payload = event.get("payload", {})
        content = payload.get("content")
        session_id = payload.get("session_id")
        
        print(f"[KERNEL] Message from {session_id}: {content}")
        
        # TODO: Route to planner → executor → modules
        # For now, just echo
        response = {
            "type": "response.ok",
            "source": "kernel",
            "payload": {
                "content": f"Echo: {content}",
                "session_id": session_id
            }
        }
        
        await self.bus.publish(
            f"ethan.response.{event.get('id')}",
            json.dumps(response).encode()
        )
        
    async def handle_registry_event(self, event):
        """Handle registry events"""
        pass
        
    async def handle_executor_event(self, event):
        """Handle executor events"""
        pass
        
    async def stop(self):
        """Stop the kernel"""
        print()
        print("◆ Shutting down kernel...")
        self.running = False
        
        # Disconnect from NATS
        await self.bus.disconnect()
        
        print("✓ Kernel stopped")

async def main():
    """Main entry point"""
    kernel = Kernel()
    
    try:
        await kernel.start()
    except KeyboardInterrupt:
        await kernel.stop()
    except Exception as e:
        print(f"✗ Kernel error: {e}")
        await kernel.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())