"""ETHAN weather plugin — example."""
import json
from urllib.request import urlopen

ETHAN_PLUGIN = {
    "name": "weather",
    "version": "1.0.0",
    "api_version": "2",
    "description": "Weather forecasts for a city",
    "author": "ETHAN",
    "commands": {
        "weather": {
            "handler": lambda args: cmd_weather(args),
            "help": "weather <city>  Show weather for a city"
        }
    },
    "dependencies": [],
}


def cmd_weather(args):
    if not args:
        print("usage: weather <city>")
        return 1
    city = " ".join(args)
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%w"
        with urlopen(url, timeout=5) as r:
            data = r.read().decode().strip()
        print(f"{city}: {data}")
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return 1
    return 0