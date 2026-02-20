# On-Call Playbook

**AutoDevOps AI Platform**  
**Last Updated:** 2026-02-20

---

## Purpose

This playbook provides incident response procedures for on-call engineers. It contains runbook templates for common incidents and escalation procedures.

---

## Table of Contents

1. [Incident Classification](#incident-classification)
2. [Escalation Procedures](#escalation-procedures)
3. [Runbook: API Outage](#runbook-api-outage)
4. [Runbook: Database Issues](#runbook-database-issues)
5. [Runbook: AI Service Degradation](#runbook-ai-service-degradation)
6. [Runbook: Queue Backlog](#runbook-queue-backlog)
7. [Runbook: Security Incident](#runbook-security-incident)
8. [Postmortem Process](#postmortem-process)

---

## Incident Classification

### Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **SEV1** | Critical - Complete outage | 15 minutes | API completely down |
| **SEV2** | High - Major feature broken | 30 minutes | AI analysis failing |
| **SEV3** | Medium - Degraded performance | 2 hours | Slow response times |
| **SEV4** | Low - Minor issue | 24 hours | UI bug, documentation |

### Impact Assessment

1. **User Impact:** How many users affected?
2. **Business Impact:** Revenue/reputation impact?
3. **Duration:** How long has the issue existed?
4. **Trend:** Is the situation improving or worsening?

---

## Escalation Procedures

### Escalation Path

```
SEV1/SEV2: On-Call Engineer → @adityat54544
SEV3/SEV4: On-Call Engineer → GitHub Issue
```

### Communication Channels

| Channel | Purpose |
|---------|---------|
| GitHub Issues | Incident tracking |
| Email | Official notifications |
| GitHub Security Advisory | Security incidents only |

### Notification Template

```markdown
## Incident Notification

**Severity:** SEV[1-4]
**Status:** Investigating/Identified/Monitoring/Resolved
**Impact:** [Brief description of user impact]

### Summary
[2-3 sentence description]

### Current Status
[What is happening now]

### Next Steps
[Planned actions]

### Timeline
- [Time] - Issue detected
- [Time] - Investigation started

### Contact
@adityat54544
```

---

## Runbook: API Outage

### Symptoms
- Health check endpoints failing
- 5xx error rates elevated
- Users unable to access application

### Diagnosis Steps

```bash
# 1. Check health endpoints
curl https://your-api.railway.app/health
curl https://your-api.railway.app/ready

# 2. Check Railway status
railway status

# 3. Check recent deployments
railway logs --service autodevops-api

# 4. Check database connectivity
# Via Supabase dashboard

# 5. Check Redis connectivity
# Via Railway Redis logs
```

### Resolution Steps

1. **If deployment issue:**
   ```bash
   # Rollback to previous deployment
   railway rollback --service autodevops-api
   
   # Verify health
   curl https://your-api.railway.app/health
   ```

2. **If database issue:**
   - Check Supabase status page
   - Verify connection strings
   - Check for connection pool exhaustion

3. **If resource issue:**
   ```bash
   # Scale up API replicas
   railway scale --service autodevops-api --replicas 3
   ```

### Prevention
- Monitor health check failures in alerts
- Set up Railway auto-scaling
- Implement circuit breakers for dependencies

---

## Runbook: Database Issues

### Symptoms
- Database connection errors
- Slow query performance
- Deadlocks or timeouts

### Diagnosis Steps

```bash
# 1. Check Supabase dashboard
# https://supabase.com/dashboard/project/YOUR_PROJECT

# 2. Check connection pool
# Look at "Database > Pool Statistics" in Supabase

# 3. Check slow queries
# Look at "Logs > Postgres Logs" in Supabase

# 4. Check replication lag
# Look at "Database > Replication" in Supabase
```

### Resolution Steps

1. **Connection pool exhaustion:**
   - Increase pool size in Supabase
   - Check for connection leaks in application
   - Restart API services to release connections

2. **Slow queries:**
   - Identify slow query from logs
   - Check missing indexes
   - Consider query optimization

3. **Storage exhaustion:**
   - Check disk usage in Supabase
   - Clean up old data or increase storage

### Prevention
- Monitor connection pool metrics
- Regular query performance analysis
- Set up storage alerts

---

## Runbook: AI Service Degradation

### Symptoms
- AI analysis timeouts
- High error rates for AI calls
- Circuit breaker open

### Diagnosis Steps

```bash
# 1. Check AI endpoint logs
railway logs --service autodevops-api | grep -i "gemini\|ai"

# 2. Check circuit breaker status
# Via application metrics

# 3. Check Gemini API status
# https://status.cloud.google.com/

# 4. Check quota usage
# Via Google AI Studio dashboard
```

### Resolution Steps

1. **Rate limiting:**
   - Wait for rate limit reset
   - Reduce concurrent requests
   - Consider caching responses

2. **API key issues:**
   ```bash
   # Rotate API key
   ./scripts/rotate_gemini_key.sh
   ```

3. **Circuit breaker open:**
   - Wait for circuit to close (configurable)
   - Check underlying issue
   - Consider fallback responses

### Prevention
- Implement request caching
- Use token estimation before calls
- Monitor quota usage proactively

---

## Runbook: Queue Backlog

### Symptoms
- Job queue length increasing
- Processing delays
- Users waiting for results

### Diagnosis Steps

```bash
# 1. Check queue depth
railway logs --service autodevops-worker | grep -i "queue"

# 2. Check worker status
railway status --service autodevops-worker

# 3. Check Redis memory
# Via Railway Redis metrics

# 4. Check for failed jobs
# Check dead letter queue
```

### Resolution Steps

1. **Scale workers:**
   ```bash
   # Increase worker replicas
   railway scale --service autodevops-worker --replicas 5
   ```

2. **Clear stuck jobs:**
   ```bash
   # Connect to Redis and clear stuck jobs
   # Requires careful execution
   ```

3. **Prioritize queues:**
   - Pause low-priority queues
   - Focus on critical job types

### Prevention
- Auto-scaling based on queue depth
- Dead letter queue monitoring
- Regular queue maintenance

---

## Runbook: Security Incident

### Symptoms
- Suspicious activity in logs
- Unauthorized access attempts
- Data breach suspected

### Immediate Actions

1. **DO NOT PANIC - Follow steps in order**

2. **Contain:**
   - Rotate exposed credentials
   - Revoke compromised tokens
   - Block suspicious IPs

3. **Assess:**
   - Determine scope of breach
   - Identify affected data
   - Document timeline

4. **Communicate:**
   - Notify security contact
   - Create private security advisory

### Credential Rotation

```bash
# Rotate Supabase key
./scripts/rotate_supabase_key.sh

# Rotate Gemini key
./scripts/rotate_gemini_key.sh

# Rotate encryption key (requires data re-encryption)
# See SECURITY.md for procedure
```

### Documentation

Create incident report following `docs/final-improvements.md` postmortem template.

---

## Postmortem Process

### After Every SEV1/SEV2 Incident

1. **Timeline Construction**
   - When was the issue first detected?
   - When was response initiated?
   - When was root cause identified?
   - When was the fix deployed?
   - When was the incident resolved?

2. **Root Cause Analysis**
   - What caused the incident?
   - Why wasn't it caught earlier?
   - What dependencies failed?

3. **Impact Assessment**
   - How many users affected?
   - How long was the outage?
   - What data was affected?

4. **Action Items**
   - What changes will prevent recurrence?
   - What monitoring needs to be added?
   - What documentation needs updating?

### Postmortem Template

```markdown
## Incident: [Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** SEV[1-4]

### Summary
Brief description of the incident

### Timeline
- HH:MM UTC - Issue detected via [monitoring/user report]
- HH:MM UTC - On-call notified
- HH:MM UTC - Investigation started
- HH:MM UTC - Root cause identified: [cause]
- HH:MM UTC - Fix deployed
- HH:MM UTC - Incident resolved

### Root Cause
Detailed explanation of what caused the incident

### Impact
- Users affected: X
- Duration: Y hours
- Features affected: [list]

### Action Items
- [ ] [Action 1] - Owner: @someone - Due: YYYY-MM-DD
- [ ] [Action 2] - Owner: @someone - Due: YYYY-MM-DD

### Lessons Learned
**What went well:**
- [Positive aspect 1]

**What could be improved:**
- [Area for improvement 1]

### Appendix
[Any additional logs, screenshots, or data]
```

---

## Quick Reference

### Health Endpoints

| Service | Endpoint | Expected |
|---------|----------|----------|
| API | `/health` | 200 OK |
| API | `/ready` | 200 OK |
| API | `/metrics` | Prometheus format |

### Key Commands

```bash
# Railway
railway status                    # Check service status
railway logs --service [name]     # View logs
railway rollback --service [name] # Rollback deployment
railway scale --service [name] --replicas N  # Scale service

# Local debugging
docker-compose up -d              # Start local services
pytest tests/ -v                  # Run tests
```

### Important Links

| Resource | Location |
|----------|----------|
| Railway Dashboard | https://railway.app/ |
| Supabase Dashboard | https://supabase.com/dashboard |
| Grafana Dashboards | `grafana/dashboard.json` |
| Security Policy | `SECURITY.md` |
| Architecture Docs | `docs/architecture.md` |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Aditya Tiwari | Initial on-call playbook |

---

*For questions about this playbook, contact @adityat54544*