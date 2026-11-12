# ETHAN CLI Container (optional, for isolated environments)
# CLI normally runs on host, but container available for CI/testing
FROM python:3.12-slim

WORKDIR /app

COPY interfaces/cli/pyproject.toml interfaces/cli/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY interfaces/cli/ethan/ ethan/
RUN pip install -e .

ENTRYPOINT ["ethan"]