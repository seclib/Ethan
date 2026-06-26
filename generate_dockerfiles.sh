#!/bin/bash
# Generate all Dockerfiles for ETHAN

set -e

echo "◆ Generating ETHAN Dockerfiles..."
echo ""

# Create deploy directory if needed
mkdir -p deploy/postgres

# Dockerfile.runtime
cat > deploy/Dockerfile.runtime << 'RUNTIME_EOF'
# ETHAN Runtime — Go-based Docker controller
# Multi-stage build for minimal image

# Build stage
FROM golang:1.23-alpine AS builder

WORKDIR /app

# Copy Go module files
COPY runtime/go.mod runtime/go.sum ./
RUN go mod download

# Copy source code
COPY runtime/ ./

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o ethan-runtime ./cmd/ethan-runtime/

# Final stage
FROM alpine:3.19

# Install curl for healthchecks
RUN apk --no-cache add curl

# Create non-root user
RUN addgroup -g 1000 ethan && \
    adduser -D -u 1000 -G ethan ethan

# Copy binary from builder
COPY --from=builder --chown=ethan:ethan /app/ethan-runtime /usr/local/bin/ethan-runtime

# Switch to non-root user
USER ethan

# Expose health check port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run
ENTRYPOINT ["ethan-runtime"]
CMD ["--config", "/etc/ethan/runtime.yaml"]
RUNTIME_EOF
echo "✓ deploy/Dockerfile.runtime"

# Dockerfile.api
cat > deploy/Dockerfile.api << 'API_EOF'
# ETHAN API Service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY core/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY core/ ./core/

# Create non-root user
RUN useradd -m -u 1000 ethan && \
    chown -R ethan:ethan /app

USER ethan

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
API_EOF
echo "✓ deploy/Dockerfile.api"

# Dockerfile.kernel
cat > deploy/Dockerfile.kernel << 'KERNEL_EOF'
# ETHAN Kernel Service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY core/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/

# Create non-root user
RUN useradd -m -u 1000 ethan && \
    chown -R ethan:ethan /app

USER ethan

# Expose health check port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run
CMD ["python", "kernel/bootstrap.py"]
KERNEL_EOF
echo "✓ deploy/Dockerfile.kernel"

# Dockerfile.module
cat > deploy/Dockerfile.module << 'MODULE_EOF'
# ETHAN Module Service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY core/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/

# Create non-root user
RUN useradd -m -u 1000 ethan && \
    chown -R ethan:ethan /app

USER ethan

# Health check (modules use NATS heartbeat)
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run (module ID passed via environment)
CMD ["python", "modules/${MODULE_ID:-executive}/main.py"]
MODULE_EOF
echo "✓ deploy/Dockerfile.module"

# Dockerfile.ui
cat > deploy/Dockerfile.ui << 'UI_EOF'
# ETHAN Web UI
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY ethan-ui/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ethan-ui/ ./

# Create non-root user
RUN useradd -m -u 1000 ethan && \
    chown -R ethan:ethan /app

USER ethan

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
UI_EOF
echo "✓ deploy/Dockerfile.ui"

# Postgres init script
cat > deploy/postgres/init.sql << 'SQL_EOF'
-- ETHAN Database Initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Create events table (event sourcing)
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    payload JSONB,
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);

-- Create goals table
CREATE TABLE IF NOT EXISTS goals (
    id VARCHAR(255) PRIMARY KEY,
    description TEXT NOT NULL,
    state VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_goals_state ON goals(state);

-- Create snapshots table
CREATE TABLE IF NOT EXISTS snapshots (
    id VARCHAR(255) PRIMARY KEY,
    module VARCHAR(255) NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_module ON snapshots(module);

-- Create outcomes table (learning)
CREATE TABLE IF NOT EXISTS outcomes (
    id VARCHAR(255) PRIMARY KEY,
    goal_id VARCHAR(255),
    success BOOLEAN NOT NULL,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outcomes_goal_id ON outcomes(goal_id);
SQL_EOF
echo "✓ deploy/postgres/init.sql"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ All Dockerfiles generated successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Files created:"
echo "  - deploy/Dockerfile.runtime"
echo "  - deploy/Dockerfile.api"
echo "  - deploy/Dockerfile.kernel"
echo "  - deploy/Dockerfile.module"
echo "  - deploy/Dockerfile.ui"
echo "  - deploy/postgres/init.sql"
echo ""