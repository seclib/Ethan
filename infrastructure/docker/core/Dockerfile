# ETHAN Core — AI Brain
# Multi-stage build: compile Go binary, minimal runtime image
FROM golang:1.23-alpine AS builder

WORKDIR /app

# Cache go modules
COPY core/go.mod core/go.sum ./
RUN go mod download

# Build binary
COPY core/ .
RUN CGO_ENABLED=0 GOOS=linux go build -o /usr/local/bin/ethan-core ./cmd/ethan-core

# Minimal runtime
FROM alpine:latest

RUN apk --no-cache add ca-certificates curl

COPY --from=builder /usr/local/bin/ethan-core /usr/local/bin/ethan-core
COPY infrastructure/config/core.yaml /etc/ethan/core.yaml

EXPOSE 8000 50051

HEALTHCHECK --interval=15s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

USER nobody

ENTRYPOINT ["/usr/local/bin/ethan-core"]