# Redis Setup Guide

This guide explains how to configure Redis for the AutoDevOps AI Platform, including options for free managed Redis services.

## Table of Contents

- [Overview](#overview)
- [Configuration Priority](#configuration-priority)
- [Option 1: Supabase Redis (Recommended)](#option-1-supabase-redis-recommended)
- [Option 2: Upstash Redis (Free Tier)](#option-2-upstash-redis-free-tier)
- [Option 3: Self-Hosted Redis](#option-3-self-hosted-redis)
- [GitHub Actions Configuration](#github-actions-configuration)
- [Local Development](#local-development)
- [Troubleshooting](#troubleshooting)

## Overview

The AutoDevOps AI Platform uses Redis for:
- Job queue management (BullMQ)
- Rate limiting
- Distributed quota tracking
- Caching and session storage

For production deployments, you need a Redis instance. For CI testing, a Redis service container is automatically provided.

## Configuration Priority

The application determines the Redis connection using this priority:

1. **SUPABASE_REDIS_URL** + **SUPABASE_REDIS_PASSWORD** (if both set)
2. **REDIS_URL** (standalone Redis or Upstash)
3. Default: `redis://localhost:6379/0` (local development)

## Option 1: Supabase Redis (Recommended)

If your project uses Supabase, you can use Supabase's managed Redis service.

### Prerequisites
- A Supabase project (https://supabase.com)
- Access to project settings

### Steps

1. **Navigate to Supabase Dashboard**
   ```
   https://supabase.com/dashboard/project/YOUR_PROJECT_ID
   ```

2. **Find Redis Settings**
   - Go to **Project Settings** → **Database**
   - Look for **Redis** or **Connection Pooling** section
   - Note: Supabase Redis may require a Pro plan

3. **Copy Connection Details**
   - Copy the **Redis Connection URL**
   - Copy the **Redis Password**

4. **Configure Environment Variables**
   ```bash
   # In your .env file or GitHub Secrets
   SUPABASE_REDIS_URL=redis://aws-0-region.pooler.supabase.com:6379
   SUPABASE_REDIS_PASSWORD=your-redis-password
   ```

### GitHub Actions Setup

Add these secrets to your repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following repository secrets:
   - `SUPABASE_REDIS_URL`: Your Supabase Redis URL
   - `SUPABASE_REDIS_PASSWORD`: Your Supabase Redis password

## Option 2: Upstash Redis (Free Tier)

Upstash provides a generous free tier for Redis, perfect for development and small production workloads.

### Prerequisites
- An Upstash account (https://upstash.com)

### Steps

1. **Create Upstash Account**
   - Go to https://upstash.com
   - Sign up for a free account

2. **Create a Redis Database**
   - Click **Create Database**
   - Choose a name (e.g., "autodevops-redis")
   - Select a region close to your users
   - Click **Create**

3. **Get Connection Details**
   - Go to your database details page
   - Copy the **UPSTASH_REDIS_REST_URL** or use the Redis URL format:
     ```
     redis://default:PASSWORD@HOST.upstash.io:6379
     ```

4. **Configure Environment Variables**
   ```bash
   # In your .env file or GitHub Secrets
   REDIS_URL=redis://default:your-password@your-database.upstash.io:6379
   ```

### Upstash Free Tier Limits

| Metric | Limit |
|--------|-------|
| Databases | 1 |
| Storage | 256 MB |
| Bandwidth | 10 GB/month |
| Requests | 10,000/day |

### GitHub Actions Setup

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add repository secret:
   - `REDIS_URL`: Your Upstash Redis URL

## Option 3: Self-Hosted Redis

For full control, you can self-host Redis on your infrastructure.

### Docker Compose

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
```

### Configuration

```bash
REDIS_URL=redis://localhost:6379/0
# Optional: Add password
REDIS_PASSWORD=your-secure-password
```

## GitHub Actions Configuration

### Adding Secrets

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the required secrets:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `REDIS_URL` | Redis connection URL (Upstash or self-hosted) | No* |
| `REDIS_PASSWORD` | Redis password (optional) | No |
| `SUPABASE_REDIS_URL` | Supabase Redis URL | No* |
| `SUPABASE_REDIS_PASSWORD` | Supabase Redis password | No* |

*At least one Redis configuration must be set for production. CI tests use a fallback Redis service container.

### CI Behavior

The CI pipeline uses this logic:
1. If `REDIS_URL` secret is set → Use external Redis
2. If `SUPABASE_REDIS_URL` secret is set → Use Supabase Redis
3. Otherwise → Use CI-provided Redis service container

## Local Development

### Using Docker (Recommended)

```bash
# Start Redis container
docker run -d --name autodevops-redis -p 6379:6379 redis:7-alpine

# Or use docker-compose
docker-compose up -d redis
```

### Using Native Redis

```bash
# Install Redis on macOS
brew install redis
brew services start redis

# Install Redis on Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis
```

### Default Configuration

For local development, the default configuration works out of the box:

```bash
# No configuration needed - uses localhost Redis automatically
REDIS_URL=redis://localhost:6379/0
```

## Troubleshooting

### Connection Refused

**Symptoms:** `Connection refused` errors

**Solutions:**
1. Ensure Redis is running: `redis-cli ping`
2. Check the correct port: `netstat -an | grep 6379`
3. Verify no firewall blocking the connection

### Authentication Failed

**Symptoms:** `NOAUTH Authentication required`

**Solutions:**
1. Add the correct password to your configuration
2. For Upstash, include the password in the URL: `redis://default:PASSWORD@HOST:6379`

### Timeout Errors

**Symptoms:** Connection timeouts in CI

**Solutions:**
1. Check Redis health in CI logs
2. Verify the Redis service container started correctly
3. Check network connectivity between services

### SSL/TLS Issues

**Symptoms:** SSL certificate errors

**Solutions:**
1. Use `rediss://` URL scheme for TLS connections
2. For Upstash: `rediss://default:PASSWORD@HOST:6379`
3. Ensure your Redis provider supports TLS

### Redis Memory Issues

**Symptoms:** `OOM` errors, Redis crashes

**Solutions:**
1. Check memory usage: `redis-cli info memory`
2. Set maxmemory policy in redis.conf
3. Consider upgrading your Redis plan

## Environment Variables Summary

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Primary Redis connection URL |
| `REDIS_PASSWORD` | No | None | Password for Redis authentication |
| `SUPABASE_REDIS_URL` | No | None | Supabase Redis URL (takes priority) |
| `SUPABASE_REDIS_PASSWORD` | No | None | Password for Supabase Redis |

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for all credentials
3. **Enable TLS** for production Redis connections
4. **Set strong passwords** for Redis instances
5. **Use VPC/private networking** when possible
6. **Regularly rotate credentials**

## Additional Resources

- [Upstash Documentation](https://docs.upstash.com/redis)
- [Supabase Documentation](https://supabase.com/docs)
- [Redis Documentation](https://redis.io/docs/)
- [BullMQ Documentation](https://docs.bullmq.io/)