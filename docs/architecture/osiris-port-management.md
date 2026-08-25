# Osiris-Lab v2: Port Management & Allocation System

## 1. Objective and Context
Osiris-Lab v2 comprises multiple Docker microservices. A recurring problem was that services like Grafana and Open WebUI were conflicting on static ports (e.g., 3000), causing system instability. 

The **Port Management & Allocation System** provides a deterministic, safe, and reproducible port assignment solution. It scans the host for free ports within a designated range (3000–9000), avoids collisions, and maintains a registry file that holds all established port allocations. 

## 2. Core Architecture
The tool is implemented as a lightweight Python CLI (`osiris-ports.py`) designed with Google SRE principles in mind. It ensures quick allocations (<100ms) with no external cloud dependencies.

### Key Components:
- **PortRegistry (`port_registry.json`)**: Persistent JSON store representing the source of truth for all current port mappings.
- **PortScanner**: Probes the host system (both `127.0.0.1` and `0.0.0.0`) using Python socket binding tests to verify actual real-time availability of a port.
- **PortAllocator**: Reads the registry to avoid logical collisions, then uses the `PortScanner` to ensure no physical system collisions, selecting the first available port in the designated range.
- **Docker Compose Integrator**: Translates the active allocations into a `docker-compose.ports.yml` file, acting as an override file for Docker Compose deployments.

## 3. Tool Commands
The system interacts via the `osiris-ports.py` CLI:
- `allocate`: Assigns an available host port to a service.
- `list`: Displays all tracked allocations in the registry.
- `check`: Validates whether the allocated ports are actually in use on the host system.
- `generate`: Dumps a `docker-compose.ports.yml` based on the registry.
- `reset`: Purges the registry entirely.

## 4. Example Usage
```bash
# Allocate port for grafana (internal port 3000)
$ ./osiris-ports.py allocate grafana --container osiris-grafana --container-port 3000
Allocated port 3001 for service 'grafana'.

# Allocate port for prometheus (internal port 9090)
$ ./osiris-ports.py allocate prometheus --container osiris-prometheus --container-port 9090
Allocated port 3002 for service 'prometheus'.

# List all allocations
$ ./osiris-ports.py list
SERVICE              CONTAINER            HOST_PORT  CONTAINER_PORT 
----------------------------------------------------------------------
grafana              osiris-grafana       3001       3000           
prometheus           osiris-prometheus    3002       9090           

# Check status of ports on the host
$ ./osiris-ports.py check
SERVICE              HOST_PORT  STATUS         
--------------------------------------------------
grafana              3001       FREE           
prometheus           3002       FREE           

# Generate docker-compose overrides
$ ./osiris-ports.py generate
Generated docker-compose.ports.yml
```

## 5. Docker-Compose Integration Example

The recommended workflow is to omit the static `ports:` declarations from your main `docker-compose.yml`. Instead, run the generator:

```bash
$ ./osiris-ports.py generate
```

This will produce a `docker-compose.ports.yml` override file that looks like this:

```yaml
version: '3.8'
services:
  grafana:
    ports:
      - 3001:3000
  prometheus:
    ports:
      - 3002:9090
```

To run your stack with the dynamically allocated ports, pass both files to the `docker compose` command:

```bash
docker compose -f docker-compose.yml -f docker-compose.ports.yml up -d
```

This guarantees an idempotent and safe deployment, preventing any "address already in use" errors at runtime.
