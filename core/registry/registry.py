"""ETHAN Capability Registry — Module capability management"""

from typing import Any, Dict, List, Optional


class Capability:
    """A capability declared by a module"""
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        module: str = "",
        description: str = "",
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        state_reads: Optional[List[str]] = None,
        state_writes: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        shared: bool = False,
    ):
        self.name = name
        self.version = version
        self.module = module
        self.description = description
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.state_reads = state_reads or []
        self.state_writes = state_writes or []
        self.dependencies = dependencies or []
        self.shared = shared
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "module": self.module,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "state_reads": self.state_reads,
            "state_writes": self.state_writes,
            "dependencies": self.dependencies,
            "shared": self.shared,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Capability":
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            module=data.get("module", ""),
            description=data.get("description", ""),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            state_reads=data.get("state_reads", []),
            state_writes=data.get("state_writes", []),
            dependencies=data.get("dependencies", []),
            shared=data.get("shared", False),
        )


class CapabilityRegistry:
    """Registry of all module capabilities"""
    
    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}
        self._modules: Dict[str, List[str]] = {}
        
    async def start(self) -> None:
        """Initialize the registry"""
        # Register built-in capabilities
        self._register_builtin()
        
    def _register_builtin(self) -> None:
        """Register built-in capabilities"""
        builtins = [
            Capability(
                name="system.status",
                version="1.0.0",
                module="kernel",
                description="Get system status",
                outputs=["status.result"],
            ),
            Capability(
                name="system.health",
                version="1.0.0",
                module="kernel",
                description="Health check",
                outputs=["health.result"],
            ),
            Capability(
                name="message.echo",
                version="1.0.0",
                module="kernel",
                description="Echo message back",
                inputs=["message.send"],
                outputs=["message.result"],
            ),
        ]
        for cap in builtins:
            self.register(cap)
    
    def register(self, capability: Capability) -> None:
        """Register a capability"""
        if capability.name in self._capabilities:
            existing = self._capabilities[capability.name]
            if existing.version >= capability.version:
                return  # Don't downgrade
        
        self._capabilities[capability.name] = capability
        
        if capability.module not in self._modules:
            self._modules[capability.module] = []
        if capability.name not in self._modules[capability.module]:
            self._modules[capability.module].append(capability.name)
    
    def unregister(self, name: str) -> None:
        """Unregister a capability"""
        if name in self._capabilities:
            cap = self._capabilities.pop(name)
            if cap.module in self._modules:
                self._modules[cap.module] = [
                    c for c in self._modules[cap.module] if c != name
                ]
    
    def get(self, name: str) -> Optional[Capability]:
        """Get a capability by name"""
        return self._capabilities.get(name)
    
    def find(self, query: str) -> List[Capability]:
        """Find capabilities matching a query"""
        results = []
        for cap in self._capabilities.values():
            if (query in cap.name or query in cap.description):
                results.append(cap)
        return results
    
    def list_by_module(self, module: str) -> List[Capability]:
        """List capabilities for a module"""
        caps = []
        for name in self._modules.get(module, []):
            if name in self._capabilities:
                caps.append(self._capabilities[name])
        return caps
    
    def list_all(self) -> List[Capability]:
        """List all registered capabilities"""
        return list(self._capabilities.values())
    
    def validate_dependencies(self, name: str) -> bool:
        """Validate that a capability's dependencies are met"""
        cap = self.get(name)
        if not cap:
            return False
        for dep in cap.dependencies:
            if dep not in self._capabilities:
                return False
        return True
    
    def get_conflicts(self, capability: Capability) -> List[str]:
        """Check for write conflicts with existing capabilities"""
        conflicts = []
        for existing in self._capabilities.values():
            if existing.module == capability.module:
                continue
            for key in capability.state_writes:
                if key in existing.state_writes and not existing.shared:
                    conflicts.append(f"{existing.name} writes to {key}")
        return conflicts
    
    @property
    def count(self) -> int:
        return len(self._capabilities)
    
    @property
    def modules(self) -> List[str]:
        return list(self._modules.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "capabilities": {
                name: cap.to_dict()
                for name, cap in self._capabilities.items()
            },
            "modules": self._modules,
        }