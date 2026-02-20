# Worker Auto-Scaling Guide

## Railway Horizontal Scaling

### Manual Scaling

```bash
# Scale API service
railway scale autodevops-api 3

# Scale worker service
railway scale autodevops-worker 5
```

### Auto-Scaling Configuration

Railway supports automatic scaling based on metrics. Configure in `infra/railway/railway.toml`:

```toml
[[scaling]]
service = "autodevops-api"
minReplicas = 1
maxReplicas = 3
targetCPU = 70

[[scaling]]
service = "autodevops-worker"
minReplicas = 1
maxReplicas = 5
targetCPU = 80
```

## Worker Concurrency Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKER_CONCURRENCY` | 5 | Total concurrent jobs |
| `ANALYSIS_CONCURRENCY` | 2 | Concurrent analysis jobs |
| `SYNC_CONCURRENCY` | 5 | Concurrent sync jobs |
| `CI_CONCURRENCY` | 2 | Concurrent CI generation jobs |

### Adjusting Concurrency

```bash
# Increase worker concurrency
railway variables set --service autodevops-worker WORKER_CONCURRENCY=10

# Adjust specific job type limits
railway variables set --service autodevops-worker ANALYSIS_CONCURRENCY=4
```

## Queue-Based Scaling

### Monitoring Queue Depth

```bash
# Check pending jobs in Redis
redis-cli LLEN bull:analysis:wait
redis-cli LLEN bull:sync:wait
redis-cli LLEN bull:ci_generation:wait
```

### Scaling Triggers

| Queue Depth | Action |
|-------------|--------|
| < 10 | Scale to min (1 replica) |
| 10-50 | Scale to 2-3 replicas |
| 50-100 | Scale to 3-5 replicas |
| > 100 | Alert + scale to max |

## Scaling Scripts

### Scale Based on Queue Depth

```bash
#!/bin/bash
# scripts/scale_workers.sh

QUEUE_DEPTH=$(redis-cli LLEN bull:analysis:wait)
MAX_REPLICAS=5

if [ "$QUEUE_DEPTH" -gt 100 ]; then
    REPLICAS=$MAX_REPLICAS
elif [ "$QUEUE_DEPTH" -gt 50 ]; then
    REPLICAS=3
elif [ "$QUEUE_DEPTH" -gt 10 ]; then
    REPLICAS=2
else
    REPLICAS=1
fi

railway scale autodevops-worker $REPLICAS
```

### Cron-Based Auto-Scaling

Add to Railway cron service for periodic scaling checks:

```yaml
# Scale check every 5 minutes
*/5 * * * * /app/scripts/scale_workers.sh
```

## Cost Considerations

### Scaling Cost Impact

| Replicas | Est. Memory | Est. CPU | Railway Cost |
|----------|-------------|----------|--------------|
| 1 | 512MB | 0.5 vCPU | $5/month |
| 3 | 1.5GB | 1.5 vCPU | $15/month |
| 5 | 2.5GB | 2.5 vCPU | $25/month |

### Optimization Tips

1. **Scale down during off-hours**:
   ```bash
   # Schedule via cron
   0 22 * * * railway scale autodevops-worker 1  # 10 PM
   0 8 * * * railway scale autodevops-worker 3   # 8 AM
   ```

2. **Use job priorities** to ensure important jobs processed first

3. **Monitor memory usage** to avoid over-provisioning

## Worker Isolation Best Practices

### Ephemeral Clones

Workers already use ephemeral shallow clones:

```typescript
// In workers/src/processors/analysis.processor.ts
const cloneOptions = {
    depth: 1,  // Shallow clone
    noTags: true,
    singleBranch: true,
};
```

### Cleanup After Jobs

```typescript
// Cleanup local caches after job completion
await fs.rm(tempDir, { recursive: true, force: true });
```

### Memory Management

```typescript
// Force garbage collection for large repos
if (global.gc) {
    global.gc();
}
```

## Monitoring

### Key Metrics

- `worker_jobs_processed_total`
- `worker_jobs_failed_total`
- `worker_queue_depth`
- `worker_processing_time_seconds`

### Alerts

Set up alerts for:
- Queue depth > 100 for 5 minutes
- No jobs processed in 10 minutes
- Worker memory > 80% of limit