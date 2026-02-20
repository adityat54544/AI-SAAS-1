# AutoDevOps AI Platform - Operations Runbook

This runbook provides procedures for common operational tasks and incident response.

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Service Architecture](#service-architecture)
3. [Common Operations](#common-operations)
4. [Incident Response](#incident-response)
5. [Troubleshooting](#troubleshooting)

---

## Quick Reference

### Service Endpoints

| Service | URL | Health Check |
|---------|-----|--------------|
| API | `https://api.autodevops.ai` | `/health` |
| Frontend | `https://autodevops.ai` | `/api/health` |
| Metrics | `https://api.autodevops.ai/metrics` | N/A |

### Key Contacts

- **On-call Engineer**: [Configure in PagerDuty]
- **Security Team**: security@example.com
- **Platform Lead**: [Configure]

### Critical Environment Variables

| Variable | Description | Rotation Frequency |
|----------|-------------|-------------------|
| `SUPABASE_SERVICE_ROLE_KEY` | Database admin key | Quarterly |
| `GEMINI_API_KEY` | AI API key | Monthly |
| `GITHUB_CLIENT_SECRET` | OAuth secret | Quarterly |
| `ENCRYPTION_KEY` | Data encryption key | Annually |

---

## Service Architecture

### Railway Services

```
┌─────────────────────────────────────────────────────────────┐
│                     Railway Project                         │
├─────────────────────────────────────────────────────────────┤
│  autodevops-api (FastAPI)                                   │
│  ├── Replicas: 1-3                                          │
│  ├── Health: /health                                        │
│  └── Metrics: /metrics                                      │
├─────────────────────────────────────────────────────────────┤
│  autodevops-worker (BullMQ)                                 │
│  ├── Replicas: 1-5                                          │
│  ├── Queues: analysis, sync, ci_generation                  │
│  └── Concurrency: Configurable                              │
├─────────────────────────────────────────────────────────────┤
│  autodevops-cron (Scheduler)                                │
│  ├── Replicas: 1                                            │
│  ├── Jobs: backup, cleanup                                  │
│  └── Schedule: Daily at 2 AM UTC                            │
├─────────────────────────────────────────────────────────────┤
│  Redis (Plugin)                                             │
│  └── Used for: Queue management, Rate limiting, Caching     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Request → API → Supabase (Database)
                  ↘ BullMQ Queue → Worker → Gemini API
                                        ↘ Results → Supabase
                                                  ↘ SSE → Frontend
```

---

## Common Operations

### 1. Deploy a New Version

```bash
# 1. Verify tests pass
pytest tests/ -v

# 2. Merge PR to main
git checkout main
git pull origin main

# 3. Railway auto-deploys from main
# Monitor deployment at: https://railway.app/dashboard

# 4. Verify deployment
curl https://api.autodevops.ai/health
```

### 2. Scale Workers

```bash
# Via Railway CLI
railway scale autodevops-worker 3

# Or via dashboard
# Go to service → Settings → Replicas
```

### 3. View Logs

```bash
# Railway CLI
railway logs --service autodevops-api

# Follow live logs
railway logs --service autodevops-worker --follow
```

### 4. Run Database Backup

```bash
# Manual backup
./scripts/backup_pg.sh

# Backups run automatically daily at 2 AM UTC via cron service
```

### 5. Rotate Secrets

```bash
# See detailed instructions
./scripts/rotate_supabase_key.sh
./scripts/rotate_gemini_key.sh
```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P1 - Critical | Service down, data loss risk | 15 minutes |
| P2 - High | Major feature broken | 1 hour |
| P3 - Medium | Minor feature issues | 4 hours |
| P4 - Low | Cosmetic issues | Next business day |

### Incident: API Service Down

**Symptoms**: Health check failing, 5xx errors

**Investigation**:
1. Check Railway dashboard for service status
2. Check recent deployments
3. Review error logs in Sentry

**Resolution**:
```bash
# 1. Check service status
railway status

# 2. View recent logs
railway logs --service autodevops-api --tail 100

# 3. Rollback if needed
railway rollback --service autodevops-api

# 4. Force redeploy
railway up --service autodevops-api
```

### Incident: Worker Backlog Growing

**Symptoms**: Jobs stuck in pending, queue length increasing

**Investigation**:
1. Check Redis connection
2. Check worker health
3. Check Gemini API status

**Resolution**:
```bash
# 1. Check queue status
redis-cli LLEN bull:analysis:wait

# 2. Scale workers up
railway scale autodevops-worker 5

# 3. Check worker logs
railway logs --service autodevops-worker

# 4. Clear stuck jobs if needed (caution!)
redis-cli DEL bull:analysis:wait
```

### Incident: Billing Spike (AI Costs)

**Symptoms**: Unexpected increase in Gemini API costs

**Investigation**:
1. Check AI usage logs
2. Review quota settings
3. Identify heavy users

**Resolution**:
1. Check current usage:
```sql
SELECT user_id, SUM(tokens_used) as total_tokens
FROM ai_usage
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY user_id
ORDER BY total_tokens DESC
LIMIT 10;
```

2. Adjust quotas:
```bash
# Lower per-user quota
railway variables set AI_DAILY_QUOTA_PER_USER 50000
```

3. Enable stricter rate limiting if needed

### Incident: Leaked Secret

**Symptoms**: API key found in logs, git history, or public

**Immediate Actions**:
1. Rotate the exposed secret immediately (see rotation scripts)
2. Check for unauthorized access
3. Audit recent activity

**Resolution**:
```bash
# 1. Rotate the key
./scripts/rotate_gemini_key.sh  # Follow instructions

# 2. Remove from git history (if committed)
./repo-migration/remove-secrets.sh --dry-run
# Then with --apply after verification

# 3. Update all services
railway variables set GEMINI_API_KEY <new_key>

# 4. Redeploy services
railway up --service autodevops-api
railway up --service autodevops-worker
```

---

## Troubleshooting

### Common Issues

#### API Returns 503 Service Unavailable

**Cause**: Database connection pool exhausted

**Solution**:
1. Check Supabase status
2. Increase connection pool size
3. Check for long-running queries

#### Workers Not Processing Jobs

**Cause**: Redis connection issue or worker crash

**Solution**:
```bash
# Check Redis
redis-cli ping

# Restart workers
railway restart --service autodevops-worker
```

#### Webhook Verification Failing

**Cause**: Incorrect webhook secret

**Solution**:
1. Verify `GITHUB_WEBHOOK_SECRET` is set correctly
2. Regenerate in GitHub settings if needed
3. Update in Railway variables

#### Rate Limiting Too Aggressive

**Cause**: Rate limit configuration too strict

**Solution**:
```bash
# Adjust rate limits
railway variables set RATE_LIMIT_REQUESTS 200
railway variables set RATE_LIMIT_WINDOW_SECONDS 60
```

### Health Check Commands

```bash
# API health
curl https://api.autodevops.ai/health

# API readiness
curl https://api.autodevops.ai/ready

# Prometheus metrics
curl https://api.autodevops.ai/metrics
```

---

## Post-Incident Checklist

After resolving any incident:

- [ ] Document the incident in your incident tracker
- [ ] Update this runbook if new procedures were discovered
- [ ] Review monitoring/alerting to catch this earlier next time
- [ ] Schedule post-mortem if P1 or P2
- [ ] Update status page if user-facing

---

## Related Documentation

- [Verification Procedures](./verification.md)
- [Branch Protection Rules](./branch_protection.md)
- [Alert Configuration](./alerts.md)
- [Railway Deployment Guide](../deploy/railway.md)