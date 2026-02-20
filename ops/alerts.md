# Alert Configuration and Billing Thresholds

## Alert Types

### 1. Billing Alerts (AI Usage)

| Alert Name | Threshold | Action |
|------------|-----------|--------|
| `ai_daily_budget_80` | 80% of daily quota | Warning notification |
| `ai_daily_budget_100` | 100% of daily quota | Block new requests |
| `ai_monthly_budget_80` | 80% of monthly quota | Review usage |
| `ai_monthly_budget_100` | 100% of monthly quota | Escalate to finance |

### 2. Performance Alerts

| Alert Name | Condition | Severity |
|------------|-----------|----------|
| `high_latency` | P99 > 5s | Warning |
| `error_rate_high` | > 5% 5xx errors | Critical |
| `circuit_breaker_open` | Circuit breaker opens | Warning |
| `queue_backlog_high` | > 100 pending jobs | Warning |

### 3. Infrastructure Alerts

| Alert Name | Condition | Severity |
|------------|-----------|----------|
| `redis_connection_failed` | Cannot connect to Redis | Critical |
| `database_connection_failed` | Cannot connect to Supabase | Critical |
| `worker_not_processing` | No jobs processed in 5 min | Warning |
| `backup_failed` | Backup job failed | Critical |

## Railway Alert Configuration

### Email Alerts

1. Go to Railway Dashboard → Project Settings
2. Add email recipients for deployment and incident alerts
3. Enable "Deploy Notifications" and "Incident Alerts"

### Webhook Alerts

Configure webhook to send alerts to your monitoring system:

```bash
railway variables set ALERT_WEBHOOK_URL=https://your-webhook-url
```

## Billing Thresholds

### Gemini API Costs

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| gemini-1.5-flash | $0.075 | $0.30 |
| gemini-2.5-pro | $1.25 | $5.00 |

### Cost Estimation

```
Daily cost = (daily_tokens_input / 1M × input_rate) + (daily_tokens_output / 1M × output_rate)

Example with 1M tokens/day on Flash:
= (1 × $0.075) + (0.25 × $0.30) = $0.075 + $0.075 = $0.15/day
```

### Budget Limits (Default)

| Tier | Daily Quota | Monthly Estimate |
|------|-------------|------------------|
| Free | 100,000 tokens | ~$0.50/month |
| Pro | 1,000,000 tokens | ~$5/month |
| Enterprise | Custom | Negotiated |

## Monitoring Queries

### Check Current Day Usage

```sql
SELECT 
    SUM(tokens_used) as total_tokens,
    COUNT(*) as request_count,
    SUM(cost_estimate) as estimated_cost
FROM ai_usage
WHERE created_at > CURRENT_DATE;
```

### Top Users by Usage

```sql
SELECT 
    user_id,
    SUM(tokens_used) as total_tokens,
    COUNT(*) as request_count
FROM ai_usage
WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
GROUP BY user_id
ORDER BY total_tokens DESC
LIMIT 10;
```

### Cost by Model

```sql
SELECT 
    model,
    SUM(tokens_used) as total_tokens,
    SUM(cost_estimate) as total_cost
FROM ai_usage
WHERE created_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY model
ORDER BY total_cost DESC;
```

## Alert Response Procedures

### High AI Cost Alert

1. Check current usage with queries above
2. Identify heavy users
3. Verify no abuse/spam patterns
4. Adjust quotas if needed:
   ```bash
   railway variables set AI_DAILY_QUOTA_PER_USER 50000
   ```
5. Consider upgrading plan or negotiating volume pricing

### Queue Backlog Alert

1. Check worker health
2. Scale up workers: `railway scale autodevops-worker 5`
3. Check for stuck jobs in Redis
4. Clear stuck jobs if needed (caution)

### Circuit Breaker Open Alert

1. Check Gemini API status
2. Review error logs in Sentry
3. Check for rate limiting from Gemini
4. Wait for recovery or implement fallback

## Sentry Configuration

### Alert Rules

In Sentry, configure these alert rules:

1. **High Error Rate**: > 10 errors/min → Slack notification
2. **Circuit Breaker Events**: Any circuit breaker open → Email
3. **Database Errors**: Any connection error → PagerDuty
4. **AI API Errors**: > 5% failure rate → Slack

### Sentry Project Setup

```bash
# Set Sentry DSN
railway variables set SENTRY_DSN=https://xxx@sentry.io/xxx

# Optional: Set environment
railway variables set SENTRY_ENVIRONMENT=production