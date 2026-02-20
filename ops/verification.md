# Verification Procedures

Pre-merge and post-deployment verification procedures for the AutoDevOps AI Platform.

## Pre-Merge Checklist

Before merging any PR to main:

### 1. Code Quality

- [ ] All linters pass (`ruff check app/`)
- [ ] Type checking passes (`mypy app/`)
- [ ] No new security vulnerabilities (`bandit -r app/`)
- [ ] No secrets in code (`detect-secrets scan`)

### 2. Tests

- [ ] All unit tests pass (`pytest tests/`)
- [ ] New code has adequate test coverage (>80%)
- [ ] Integration tests pass (if applicable)

### 3. Documentation

- [ ] API changes documented in docstrings
- [ ] README updated if needed
- [ ] Runbook updated if operational changes

### 4. Performance

- [ ] No significant performance regression
- [ ] Large payload handling tested
- [ ] Memory usage acceptable

---

## Post-Deployment Verification

After each deployment:

### 1. Health Checks

```bash
# API health
curl -f https://api.autodevops.ai/health || echo "FAILED"

# API readiness
curl -f https://api.autodevops.ai/ready || echo "FAILED"

# Expected response: {"status": "healthy", ...}
```

### 2. Database Connectivity

```bash
# Check database health
curl https://api.autodevops.ai/ready | jq '.checks.database'
# Expected: "connected"
```

### 3. Redis Connectivity

```bash
# Check Redis health
curl https://api.autodevops.ai/ready | jq '.checks.redis'
# Expected: "connected" or "not_configured"
```

### 4. Worker Status

```bash
# Check worker logs for startup
railway logs --service autodevops-worker --tail 20

# Look for: "All workers started"
```

### 5. Authentication Flow

```bash
# Test OAuth endpoint
curl -I https://api.autodevops.ai/auth/github
# Expected: 302 redirect to GitHub
```

### 6. Rate Limiting

```bash
# Verify rate limiting is active
for i in {1..110}; do
  curl -s -o /dev/null -w "%{http_code}\n" https://api.autodevops.ai/health
done
# Should see 429 after limit reached
```

---

## Feature-Specific Verification

### AI Analysis Feature

1. **Create a test repository analysis**

```bash
# Requires authentication token
curl -X POST https://api.autodevops.ai/api/repositories/{id}/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

2. **Verify job created**

```bash
# Check jobs endpoint
curl https://api.autodevops.ai/api/jobs \
  -H "Authorization: Bearer $TOKEN"
```

3. **Monitor job progress**

```bash
# Watch job status
railway logs --service autodevops-worker --follow
```

### Webhook Integration

1. **Verify webhook endpoint**

```bash
# Test with a valid signature
PAYLOAD='{"action":"push"}'
SECRET="your_webhook_secret"
SIGNATURE="sha256=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')"

curl -X POST https://api.autodevops.ai/webhooks/github \
  -H "X-Hub-Signature-256: $SIGNATURE" \
  -H "X-GitHub-Event: push" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
# Expected: 200 OK
```

2. **Test invalid signature**

```bash
curl -X POST https://api.autodevops.ai/webhooks/github \
  -H "X-Hub-Signature-256: sha256=invalid" \
  -H "X-GitHub-Event: push" \
  -H "Content-Type: application/json" \
  -d '{"action":"push"}'
# Expected: 401 Unauthorized
```

---

## Performance Verification

### Load Testing

```bash
# Install hey (load testing tool)
go install github.com/rakyll/hey@latest

# Test health endpoint
hey -n 1000 -c 50 https://api.autodevops.ai/health

# Verify:
# - No 5xx errors
# - Average latency < 100ms
# - P99 latency < 500ms
```

### AI Rate Limiting

```bash
# Verify quota enforcement
# Run multiple analysis requests and check quota exhaustion
```

---

## Security Verification

### 1. No Secrets Exposed

```bash
# Run secret detection
detect-secrets scan --all-files

# Check logs for sensitive data
railway logs --service autodevops-api | grep -i "password\|secret\|key\|token"
# Should show [REDACTED]
```

### 2. CORS Configuration

```bash
# Test CORS from unauthorized origin
curl -I -X OPTIONS https://api.autodevops.ai/health \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: GET"
# Should not include Access-Control-Allow-Origin
```

### 3. Authentication Required

```bash
# Test protected endpoint without auth
curl https://api.autodevops.ai/api/repositories
# Expected: 401 Unauthorized
```

---

## Rollback Procedures

### Quick Rollback

```bash
# List recent deployments
railway status

# Rollback to previous version
railway rollback --service autodevops-api

# Verify rollback
curl https://api.autodevops.ai/health
```

### Database Migration Rollback

```bash
# If a migration caused issues, rollback manually
# Requires database access
psql $DATABASE_URL -c "ROLLBACK;"
```

---

## Monitoring Verification

### Check Sentry

1. Navigate to Sentry dashboard
2. Verify no new error spikes
3. Check for unhandled exceptions

### Check Metrics

```bash
# Prometheus metrics
curl https://api.autodevops.ai/metrics

# Look for:
# - app_info
# - http_requests_total
# - circuit_breaker_state
```

### Circuit Breaker Status

```bash
# Check circuit breaker state via metrics
curl -s https://api.autodevops.ai/metrics | grep circuit_breaker
# Should show state="closed" (healthy)
```

---

## Scheduled Verification

### Daily Checks

- [ ] Backup completed successfully
- [ ] No security alerts
- [ ] Error rate within threshold

### Weekly Checks

- [ ] Review Sentry errors
- [ ] Check AI usage costs
- [ ] Review rate limit patterns

### Monthly Checks

- [ ] Rotate non-critical secrets
- [ ] Review access logs
- [ ] Update dependencies with security patches

---

## Sign-off

After completing verification:

| Check | Status | Verified By | Date |
|-------|--------|-------------|------|
| Health Checks | ✅/❌ | | |
| Database | ✅/❌ | | |
| Workers | ✅/❌ | | |
| Security | ✅/❌ | | |
| Performance | ✅/❌ | | |

**Deployment Approved**: _________________ Date: _________