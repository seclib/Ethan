"""ETHAN Planner Module — capability declarations."""
ETHAN_CAPABILITIES = [
    {
        "name": "planner.decompose",
        "version": "1.0.0",
        "module": "planner",
        "inputs": ["goal.created", "goal.updated"],
        "outputs": ["task.created"],
        "state_reads": ["registry:capabilities:*", "memory:entry:*"],
        "state_writes": ["planner:task:*"],
        "dependencies": [],
        "shared": False,
    }
]