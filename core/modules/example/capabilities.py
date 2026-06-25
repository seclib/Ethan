"""Example module — capability declarations."""
ETHAN_CAPABILITIES = [
    {
        "name": "example.echo",
        "version": "1.0.0",
        "module": "example",
        "inputs": ["example.echo.request"],
        "outputs": ["example.echo.response"],
        "state_reads": [],
        "state_writes": ["example:last_echo"],
        "dependencies": [],
        "shared": False,
    }
]