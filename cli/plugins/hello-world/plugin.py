"""ETHAN Plugin: hello-world — example minimal plugin."""
ETHAN_PLUGIN = {
    "name": "hello-world",
    "version": "1.0.0",
    "api_version": "2",
    "capabilities": [
        {
            "name": "hello.greet",
            "version": "1.0.0",
            "module": "hello-world",
            "inputs": ["hello.greet.request"],
            "outputs": ["hello.greet.complete"],
        }
    ],
    "commands": {
        "hello": {
            "help": "Say hello",
            "handler": "cmd_hello",
            "args": [{"name": "name", "type": "str", "help": "Who to greet"}],
        }
    },
    "subscriptions": {},
}

def cmd_hello(args):
    print(f"Hello, {args[0] if args else 'world'}!")
