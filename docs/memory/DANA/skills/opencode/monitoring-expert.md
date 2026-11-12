# Monitoring Expert (monitoring-expert)

**Source :** `/home/fatsio/.config/opencode/skills/monitoring-expert/SKILL.md`  \n**Domaine :** DevOps — Observability  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

Configures monitoring systems, implements structured logging pipelines, creates Prometheus/Grafana dashboards, defines alerting rules (RED method: Rate, Errors, Duration; USE method: Utilization, Saturation, Errors). Implements structured logging, Metrics (Counters, Histograms), Tracing (OpenTelemetry).

## Main capabilities

- **RED method monitoring**: Rate, Errors, Duration — key metrics for service health
- **USE method monitoring**: Utilization, Saturation, Errors — resource metrics
- **Structured logging**: Implements structured log pipelines with correlation IDs
- **Prometheus metrics**: Creates counters, histograms, gauges for time-series data
- **Grafana dashboards**: Builds visualization dashboards for monitoring data
- **Alerting rules**: Defines PagerDuty/Alertmanager rules based on RED/USE methods

## What it can do

- Configure RED metrics (Rate, Errors, Duration) for service health monitoring
- Configure USE metrics (Utilization, Saturation, Errors) for resource monitoring
- Set up structured logging with correlation IDs and log severity levels
- Create Prometheus metrics endpoints with proper exposition format
- Build Grafana dashboards for service observability
- Define alerting rules for threshold-based and anomaly-based notifications

## When it is useful

- Setting up observability for new microservice architectures
- Adding monitoring to existing services without built-in observability
- Creating on-call dashboards for incident response
- Defining alerting policies for SRE teams
- Implementing OpenTelemetry tracing across service boundaries

## Practical examples

### RED method metrics

```python
# Rate: requests per second
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
REQUEST_COUNT.labels(method="GET", endpoint="/api/users").inc()

# Errors: request errors
REQUEST_ERRORS = Counter("http_requests_error_total", "Total HTTP request errors", ["method", "endpoint"])
REQUEST_ERRORS.labels(method="GET", endpoint="/api/users").inc()

# Duration: request latency
REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request latency")
with REQUEST_DURATION.time():
    handle_request()
```

### USE method monitoring

```python
# Utilization: CPU usage
CPU_USAGE = Gauge("system_cpu_usage_percent", "CPU usage percentage")

# Saturation: queue depth
QUEUE_DEPTH = Gauge("job_queue_length", "Number of jobs in queue")

# Errors: error rate
ERROR_RATE = Counter("job_errors_total", "Total job errors")
```

### Grafana dashboard JSON

```json
{
  "title": "Service Observability",
  "panels": [
    {
      "type": "stat",
      "datasource": "Prometheus",
 "targets": [{"expr": "http_requests_total", "legendFormat": "GET /api/users"}]
    }
  ]
}
```

## Original source path

`/home/fatsio/.config/opencode/skills/monitoring-expert/SKILL.md`

## Classification

- **Domaines :** DevOps, observability, monitoring, Prometheus, Grafana
- **Statut :** Spécialisé (Niveau B)
- **Références :** `redis-patterns`, `change-impact`, `error-handling`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis
