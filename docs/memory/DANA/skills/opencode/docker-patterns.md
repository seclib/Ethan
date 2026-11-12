# Docker Patterns

**Source :** `/home/fatsio/.config/opencode/skills/docker-patterns/SKILL.md`  
**Domaine :** DevOps et infrastructure  
**Type :** Analyse stratégique  
**Niveau :** Éssentiel  

## Description

Docker and Docker Compose patterns for local development, hardened CLI installer harnesses, container security, networking, volumes, and multi-service orchestration.

## Main capabilities

- **Multi-stage Dockerfiles** : Build optimization, production image size reduction, dev/production separation
- **Docker Compose patterns** : Standard web app stacks, service health checks, volume strategies, network modes
- **Container security** : Non-root users, secret management, trusted base images, vulnerability scanning
- **Networking** : Custom networks, port mapping, service discovery, DNS configuration
- **Volume management** : Named volumes, anonymous volumes, bind mounts, propagation modes
- **Multi-service orchestration** : 13-service patterns, dependency ordering, health check coordination

## What it can do

- Generate multi-stage Dockerfile patterns
- Create docker-compose.yml configurations for standard web app stacks
- Configure service health checks (pg_isready, redis-cli ping, etc.)
- Set up volume strategies for data persistence
- Define custom networks for service isolation
- Provide hardening best practices for production containers

## Practical examples

### Multi-stage Dockerfile

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
RUN npm ci --production
EXPOSE 3000
CMD ["node", "index.js"]
```

### Docker Compose for Local Development

```yaml
services:
  app:
    build:
      context: .
      target: dev
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: npm run dev

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app_dev
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
```

## Original source path

`/home/fatsio/.config/opencode/skills/docker-patterns/SKILL.md`

## Classification

- **Domaines :** infrastructure, Docker, Compose, conteneurisation, déploiement
- **Statut :** Éssentiel (Niveau A)
- **Références :** `monitoring-expert`, `redis-patterns`, `change-impact`
- **Validé :** Oui (rapport d'analyse stratégique)
