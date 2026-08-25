#!/usr/bin/env python3
import argparse
import json
import socket
import os
import sys
from pathlib import Path

REGISTRY_FILE = Path(os.environ.get("OSIRIS_PORT_REGISTRY", "port_registry.json"))
START_PORT = 3000
END_PORT = 9000

def load_registry():
    if not REGISTRY_FILE.exists():
        return {}
    with open(REGISTRY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_registry(registry):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)

def is_port_in_use(port):
    """Check if a port is in use on the host (127.0.0.1 or 0.0.0.0)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)
        # Check both localhost and any IP
        for ip in ['127.0.0.1', '0.0.0.0']:
            try:
                result = s.connect_ex((ip, port))
                if result == 0:
                    return True
            except socket.error:
                pass
    return False

def allocate_port(service_name, container_name, container_port):
    registry = load_registry()
    
    # Check if already allocated
    if service_name in registry:
        allocated = registry[service_name]
        print(f"Service '{service_name}' already has port {allocated['host_port']} allocated.")
        return allocated['host_port']
    
    # Get used ports from registry to avoid conflict even if not currently bound
    used_ports = {entry['host_port'] for entry in registry.values()}
    
    # Find next free port
    assigned_port = None
    for port in range(START_PORT, END_PORT + 1):
        if port not in used_ports and not is_port_in_use(port):
            assigned_port = port
            break
            
    if not assigned_port:
        print("Error: No available ports found in the specified range.", file=sys.stderr)
        sys.exit(1)
        
    registry[service_name] = {
        "service_name": service_name,
        "container": container_name,
        "host_port": assigned_port,
        "container_port": container_port
    }
    
    save_registry(registry)
    print(f"Allocated port {assigned_port} for service '{service_name}'.")
    return assigned_port

def list_ports():
    registry = load_registry()
    if not registry:
        print("No ports allocated.")
        return
        
    print(f"{'SERVICE':<20} {'CONTAINER':<20} {'HOST_PORT':<10} {'CONTAINER_PORT':<15}")
    print("-" * 70)
    for srv, info in registry.items():
        print(f"{info['service_name']:<20} {info['container']:<20} {info['host_port']:<10} {info['container_port']:<15}")

def check_ports():
    registry = load_registry()
    if not registry:
        print("No ports to check.")
        return
        
    print(f"{'SERVICE':<20} {'HOST_PORT':<10} {'STATUS':<15}")
    print("-" * 50)
    for srv, info in registry.items():
        port = info['host_port']
        in_use = is_port_in_use(port)
        status = "IN_USE" if in_use else "FREE"
        print(f"{info['service_name']:<20} {port:<10} {status:<15}")

def reset_registry():
    if REGISTRY_FILE.exists():
        REGISTRY_FILE.unlink()
    print("Port registry has been reset.")

def generate_compose():
    registry = load_registry()
    if not registry:
        print("No ports allocated, nothing to generate.")
        return

    compose = {
        "version": "3.8",
        "services": {}
    }
    
    for srv, info in registry.items():
        compose["services"][srv] = {
            "ports": [
                f"{info['host_port']}:{info['container_port']}"
            ]
        }
        
    import yaml
    try:
        yaml_content = yaml.dump(compose, default_flow_style=False)
        with open("docker-compose.ports.yml", "w") as f:
            f.write(yaml_content)
        print("Generated docker-compose.ports.yml")
    except ImportError:
        print("PyYAML not installed. Outputting JSON instead:")
        print(json.dumps(compose, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Osiris-Lab Port Management & Allocation System")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # list
    subparsers.add_parser("list", help="List all allocated ports")
    
    # allocate
    alloc_parser = subparsers.add_parser("allocate", help="Allocate a port for a service")
    alloc_parser.add_argument("service", help="Service name (e.g., grafana)")
    alloc_parser.add_argument("--container", help="Container name", required=True)
    alloc_parser.add_argument("--container-port", type=int, help="Internal container port", required=True)
    
    # check
    subparsers.add_parser("check", help="Check status of allocated ports")
    
    # reset
    subparsers.add_parser("reset", help="Reset all allocations")
    
    # generate compose
    subparsers.add_parser("generate", help="Generate a docker-compose override file")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_ports()
    elif args.command == "allocate":
        allocate_port(args.service, args.container, args.container_port)
    elif args.command == "check":
        check_ports()
    elif args.command == "reset":
        reset_registry()
    elif args.command == "generate":
        generate_compose()

if __name__ == "__main__":
    main()
