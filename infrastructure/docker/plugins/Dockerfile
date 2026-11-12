# ETHAN Plugins — Extension Runtime
FROM python:3.12-slim

WORKDIR /app

# Install plugins package
COPY plugins/pyproject.toml .
COPY plugins/sdk/ sdk/
COPY plugins/builtin/ builtin/

RUN pip install --no-cache-dir .

# Plugin configuration
COPY infrastructure/config/plugins.yaml /etc/ethan/plugins.yaml

EXPOSE 8003

HEALTHCHECK --interval=15s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

ENTRYPOINT ["python", "-m", "plugins.sandbox.runtime"]