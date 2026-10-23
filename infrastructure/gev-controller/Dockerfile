FROM python:3.11-slim

# Install Docker CLI only (not the full engine)
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY controller.py /opt/gev-controller/controller.py

EXPOSE 9400

CMD ["python", "/opt/gev-controller/controller.py"]
