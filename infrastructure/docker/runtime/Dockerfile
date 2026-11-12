# ETHAN Runtime — Service Orchestrator
# Multi-stage build: compile Go binary, minimal runtime with Docker CLI
FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY runtime/go.mod runtime/go.sum ./
RUN go mod download

COPY runtime/ .
RUN CGO_ENABLED=0 GOOS=linux go build -o /usr/local/bin/ethan-runtime ./cmd/ethan-runtime

# Runtime needs Docker CLI (not Docker-in-Docker)
FROM alpine:latest

RUN apk --no-cache add ca-certificates docker-cli curl

COPY --from=builder /usr/local/bin/ethan-runtime /usr/local/bin/ethan-runtime
COPY runtime/compose/docker-compose.yml /usr/local/share/ethan/compose/docker-compose.yml
COPY infrastructure/config/runtime.yaml /etc/ethan/runtime.yaml

# Docker socket from host
VOLUME /var/run/docker.sock
VOLUME /var/run/ethan

EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

ENTRYPOINT ["/usr/local/bin/ethan-runtime"]