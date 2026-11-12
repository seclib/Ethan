"""ETHAN Memory Module — capability declarations."""
ETHAN_CAPABILITIES = [
    {
        "name": "memory.store",
        "version": "1.0.0",
        "module": "memory",
        "inputs": ["memory.store.request"],
        "outputs": ["memory.store.complete", "memory.store.error"],
        "state_reads": ["memory:config"],
        "state_writes": ["memory:entry:*"],
        "dependencies": [],
        "shared": False,
    },
    {
        "name": "memory.recall",
        "version": "1.0.0",
        "module": "memory",
        "inputs": ["memory.recall.request"],
        "outputs": ["memory.recall.complete"],
        "state_reads": ["memory:entry:*", "memory:config"],
        "state_writes": [],
        "dependencies": [],
        "shared": False,
    },
]