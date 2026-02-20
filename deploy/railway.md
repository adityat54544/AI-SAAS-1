# Railway Deployment Guide

## Service Architecture

The AutoDevOps AI Platform is deployed on Railway as three separate services:

| Service | Description | Replicas | Port |
|---------|-------------|----------|------|
| `autodevops-api` | FastAPI backend | 1-3 | 8000 |
| `autodevops-worker` | BullMQ job workers | 1-5 | N/A |
| `autodevops-cron` | Scheduled jobs | 1 | N/A |

## Prerequisites

### Railway Plugins

1. **Redis** - Required for:
   - BullMQ job queues
   - Rate limiting storage
   - Session caching

### Required Environment Variables

#### All Services
```
ENVIRONMENT=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<from-supabase-dashboard>
SUPABASE_ANON_KEY=<from-supabase-dashboard>
REDIS_URL=${{Redis.REDIS_URL}}
```

#### API Service
```
GITHUB_CLIENT_ID=<oauth-app-id>
GITHUB_CLIENT_SECRET=<oauth-app-secret>
GITHUB_WEBHOOK_SECRET=<your-webhook-secret>
GEMINI_API_KEY=<from-google-ai-studio>
SENTRY_DSN=<from-sentry>
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
AI_MODEL_DEFAULT=gemini-1.5-flash
AI_MAX_TOKENS_PER_TASK=32000
AI_DAILY_QUOTA_PER_USER=100000
```

#### Worker Service
```
GEMINI_API_KEY=<from-google-ai-studio>
WORKER_CONCURRENCY=5
ANALYSIS_CONCURRENCY=2
SYNC_CONCURRENCY=5
CI_CONCURRENCY=2
```

#### Cron Service
```
S3_BUCKET=<backup-bucket>
S3_ACCESS_KEY=<aws-access-key>
S3_SECRET_KEY=<aws-secret-key>
S3_REGION=us-east-1
BACKUP_RETENTION_DAYS=30
```

## Deployment Steps

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway project create autodevops-ai-platform
```

### 2. Add Redis Plugin

```bash
# Add Redis plugin
railway add --plugin redis

# Verify Redis is running
railway status
```

### 3. Deploy Services

#### API Service
```bash
# Create API service
railway service create autodevops-api

# Set service variables
railway variables set --service autodevops-api ENVIRONMENT=production
railway variables set --service autodevops-api SUPABASE_URL=<your-url>
# ... set all required variables

# Deploy
railway up --service autodevops-api
```

#### Worker Service
```bash
# Create worker service
railway service create autodevops-worker

# Set service variables
railway variables set --service autodevops-worker ENVIRONMENT=production
# ... set all required variables

# Deploy
railway up --service autodevops-worker
```

#### Cron Service
```bash
# Create cron service
railway service create autodevops-cron

# Deploy
railway up --service autodevops-cron
```

### 4. Configure Domains

```bash
# Generate domain for API
railway domain generate autodevops-api

# Add custom domain (optional)
railway domain add autodevops-api api.autodevops.ai
```

## Scaling

### Horizontal Scaling

```bash
# Scale API to 3 replicas
railway scale autodevops-api 3

# Scale workers to 5 replicas
railway scale autodevops-worker 5
```

### Vertical Scaling

In Railway dashboard:
1. Go to Service → Settings
2. Adjust CPU and Memory limits
3. Service will restart automatically

## Monitoring

### Health Checks

```bash
# Check API health
curl https://your-api-domain.railway.app/health

# Check API readiness
curl https://your-api-domain.railway.app/ready
```

### Logs

```bash
# View API logs
railway logs --service autodevops-api

# View worker logs
railway logs --service autodevops-worker --follow
```

### Metrics

Prometheus metrics are exposed at `/metrics`:
```bash
curl https://your-api-domain.railway.app/metrics
```

## Troubleshooting

### Service Won't Start

1. Check logs: `railway logs --service <name>`
2. Verify environment variables are set
3. Check health check configuration

### High Memory Usage

1. Reduce worker concurrency: `WORKER_CONCURRENCY=2`
2. Scale horizontally instead of vertically
3. Check for memory leaks in logs

### Redis Connection Issues

1. Verify Redis plugin is added
2. Check `REDIS_URL` is using `${{Redis.REDIS_URL}}`
3. Restart affected services

## Cost Optimization

- Use Railway's free tier for development
- Scale to 0 replicas for non-critical services during off-hours
- Monitor usage in Railway dashboard
- Use `STANDARD_IA` storage class for S3 backups