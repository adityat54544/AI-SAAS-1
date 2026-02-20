# Observability & SLO/SLI Guidance

**Document Purpose:** Define required metrics, monitoring infrastructure, and service level objectives for the AutoDevOps AI Platform.  
**Last Updated:** 2026-02-20  
**Status:** Baseline Collection Phase

---

## Overview

This document establishes the observability requirements for the platform, including:
- Required application metrics
- Prometheus scrape endpoints
- Grafana dashboard configuration
- Initial SLO targets (to be tuned after baseline collection)

---

## Required Metrics

The following metrics **MUST** be exported by the application for proper observability and operational awareness.

### Core Metrics Table

| Metric Name | Type | Description | Labels | Purpose |
|-------------|------|-------------|--------|---------|
| `requests_total` | Counter | Total HTTP requests | `method`, `endpoint`, `status` | Traffic monitoring, error rate calculation |
| `job_queue_length` | Gauge | Current jobs in queue | `queue` (analysis, sync, ci_gen) | Backlog monitoring, scaling trigger |
| `ai_calls_total` | Counter | Total AI API calls | `provider`, `model` | Usage tracking, cost analysis |
| `ai_errors_total` | Counter | AI API errors | `provider`, `error_type` | Error rate monitoring, reliability |
| `db_connection_errors` | Counter | DB connection failures | `database` | Infrastructure health |

### Prometheus Format Example

```prometheus
# TYPE requests_total counter
requests_total{method="GET",endpoint="/api/health",status="200"} 12345
requests_total{method="POST",endpoint="/api/analyze",status="202"} 567

# TYPE job_queue_length gauge
job_queue_length{queue="analysis"} 15
job_queue_length{queue="sync"} 3
job_queue_length{queue="ci_gen"} 0

# TYPE ai_calls_total counter
ai_calls_total{provider="gemini",model="flash"} 890

# TYPE ai_errors_total counter
ai_errors_total{provider="gemini",error_type="rate_limit"} 5
ai_errors_total{provider="gemini",error_type="timeout"} 2

# TYPE db_connection_errors counter
db_connection_errors{database="supabase"} 0
```

---

## Prometheus Scrape Endpoints

### Primary Metrics Endpoint

| Endpoint | Purpose | Format |
|----------|---------|--------|
| `/metrics` | Prometheus metrics | Prometheus text exposition format |
| `/health` | Liveness probe | JSON |
| `/ready` | Readiness probe (checks DB, Redis) | JSON |

### Prometheus Scrape Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'autodevops-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    
  - job_name: 'autodevops-workers'
    scrape_interval: 30s
    static_configs:
      - targets: ['worker:8001']
    metrics_path: /metrics
```

### Implementation Checklist

- [ ] Add `prometheus-client` to requirements.txt
- [ ] Implement `/metrics` endpoint in FastAPI
- [ ] Add instrumentation to all HTTP handlers
- [ ] Add queue metrics from Redis/BullMQ
- [ ] Add AI call tracking in router layer
- [ ] Add DB connection tracking

---

## Grafana Dashboard

### Dashboard Location

The Grafana dashboard configuration is located at:
```
grafana/dashboard.json
```

### Import Instructions

1. Open Grafana → Dashboards → Import
2. Upload `grafana/dashboard.json` or paste JSON
3. Configure Prometheus data source
4. Set appropriate time range (default: last 1 hour)

### Dashboard Panels

| Panel | Metric | Visualization |
|-------|--------|---------------|
| Request Rate | `rate(requests_total[5m])` | Graph |
| Error Rate | `rate(requests_total{status=~"5.."}[5m])` | Graph |
| Queue Depth | `job_queue_length` | Gauge |
| AI Calls/min | `rate(ai_calls_total[1m])` | Graph |
| AI Error Rate | `rate(ai_errors_total[5m])` | Graph |
| DB Errors | `db_connection_errors` | Stat |

### Dashboard Screenshot

> **Note:** Dashboard screenshot should be added after baseline data collection.

---

## Service Level Objectives (SLOs)

### Initial SLO Targets

> ⚠️ **IMPORTANT:** These are placeholder targets based on industry standards. They should be tuned after collecting 2-4 weeks of baseline data.

| SLO | Target | Measurement | Status |
|-----|--------|-------------|--------|
| **Availability** | 99.5% | Uptime over 30-day window | To be tuned |
| **Latency (p50)** | < 200ms | Request duration histogram | To be tuned |
| **Latency (p99)** | < 2s | Request duration histogram | To be tuned |
| **Error Rate** | < 1% | 5xx responses / total requests | To be tuned |
| **Queue Processing** | < 5min | Job age before processing | To be tuned |
| **AI Response Time** | < 30s | AI call duration | To be tuned |

### Service Level Indicators (SLIs)

| SLI | Metric | Calculation |
|-----|--------|-------------|
| Availability | `requests_total{status!~"5.."}` | Good requests / total requests |
| Latency | Histogram bucket | Percentile calculation |
| Throughput | `rate(requests_total[5m])` | Requests per second |
| Queue Health | `job_queue_length` | Current backlog vs threshold |
| AI Reliability | `ai_errors_total / ai_calls_total` | Error rate percentage |

### Error Budget

```
Error Budget = 1 - SLO Target
Monthly Error Budget (99.5% SLO) = 0.5% = 3.65 hours downtime allowed
```

---

## Alerting Strategy

### Alert Severity Levels

| Level | Response Time | Notification |
|-------|---------------|--------------|
| Critical | 5 minutes | PagerDuty + Slack |
| Warning | 1 hour | Slack |
| Info | 24 hours | Email |

### Recommended Alert Rules

> **Note:** Thresholds should be adjusted after baseline collection.

```yaml
# alerts.yml
groups:
  - name: autodevops-alerts
    rules:
      # Critical - Service Down
      - alert: ServiceDown
        expr: up{job="autodevops-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API service is down"
          
      # Critical - High Error Rate
      - alert: HighErrorRate
        expr: rate(requests_total{status=~"5.."}[5m]) / rate(requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate above 5%"
          
      # Warning - Queue Backlog
      - alert: QueueBacklog
        expr: job_queue_length > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Job queue backlog exceeds 100"
          
      # Warning - AI Errors
      - alert: AIErrorsIncreasing
        expr: rate(ai_errors_total[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AI errors detected"
```

---

## Implementation Roadmap

### Phase 1: Baseline Collection (Current)

- [x] Document required metrics
- [x] Create Grafana dashboard template
- [ ] Implement metrics endpoint
- [ ] Deploy Prometheus scraping
- [ ] Collect 2-4 weeks of baseline data

### Phase 2: Threshold Definition

- [ ] Analyze baseline metric distributions
- [ ] Define SLO targets based on data
- [ ] Configure alerting rules
- [ ] Document incident response procedures

### Phase 3: Continuous Improvement

- [ ] Monthly SLO review
- [ ] Alert tuning based on noise
- [ ] Dashboard refinements
- [ ] Error budget tracking

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │   API       │     │   Workers   │     │   Redis     │      │
│   │   :8000     │     │   :8001     │     │   :6379     │      │
│   │   /metrics  │     │   /metrics  │     │   (exporter)│      │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘      │
│          │                   │                   │              │
│          └───────────────────┴───────────────────┘              │
│                              │                                  │
│                              ▼                                  │
│                    ┌─────────────────┐                          │
│                    │   Prometheus    │                          │
│                    │   :9090         │                          │
│                    │   (scrape)      │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                          │
│                    │   Grafana       │                          │
│                    │   :3000         │                          │
│                    │   (dashboards)  │                          │
│                    └─────────────────┘                          │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   ALERTING                              │   │
│   │   Prometheus Alertmanager → PagerDuty / Slack          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `ops/alerts.md` | Alert configuration details |
| `ops/runbook.md` | Incident response procedures |
| `grafana/dashboard.json` | Dashboard configuration |
| `.github/workflows/monitoring_checks.yml` | CI metrics verification |

---

## Document Information

**Author:** DevOps Governance Agent  
**Created:** 2026-02-20  
**Version:** 1.0  
**Review Cycle:** Quarterly

---

*This document should be updated as SLO targets are refined based on production data.*