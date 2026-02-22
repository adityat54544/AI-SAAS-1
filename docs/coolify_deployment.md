# Coolify Deployment Guide

## AutoDevOps AI Platform - Vercel to Coolify Migration

This document provides complete instructions for deploying the AutoDevOps AI Platform on Coolify.

## Prerequisites

- Ubuntu 22.04 VPS with root access
- Domain name (optional but recommended)
- GitHub repository access
- Environment credentials

## Phase 1: Coolify Installation

### 1. Install Coolify on Ubuntu 22.04 VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
curl -fsSL https://get.docker.com | sh

# Install Coolify (non-interactive)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

### 2. Verify Coolify Installation

```bash
# Check Coolify status
docker ps | grep coolify

# Access Coolify dashboard
# https://your-vps-ip:3000
```

## Phase 2: Service Configuration

### Backend Service (FastAPI)

1. **Create New Service in Coolify**
   - Service Type: Docker
   - Source: GitHub Repository
   - Repository: `https://github.com/adityat54544/AI-SAAS-1`
   - Branch: `main`
   - Dockerfile: `Dockerfile.coolify`
   - Build Context: `.`

2. **Environment Variables (set in Coolify dashboard)**
   ```
   PORT=8000
   ENVIRONMENT=production
   SUPABASE_URL=<your-supabase-url>
   SUPABASE_SERVICE_ROLE_KEY=<your-key>
   SUPABASE_ANON_KEY=<your-key>
   GEMINI_API_KEY=<your-key>
   REDIS_URL=redis://redis:6379/0
   ENCRYPTION_KEY=<your-key>
   GITHUB_WEBHOOK_SECRET=<your-secret>
   CORS_ORIGINS=https://your-domain.com
   FRONTEND_URL=https://your-domain.com
   ```

3. **Health Check**
   - Path: `/health`
   - Interval: 30s
   - Timeout: 10s

### Frontend Service (Next.js)

1. **Create New Service in Coolify**
   - Service Type: Docker
   - Source: GitHub Repository
   - Repository: `https://github.com/adityat54544/AI-SAAS-1`
   - Branch: `main`
   - Dockerfile: `frontend/Dockerfile`
   - Build Context: `frontend`

2. **Build Arguments (set in Coolify)**
   ```
   NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-key>
   NEXT_PUBLIC_API_URL=https://api.your-domain.com
   ```

3. **Environment Variables**
   ```
   NODE_ENV=production
   NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-key>
   NEXT_PUBLIC_API_URL=https://api.your-domain.com
   ```

### Redis Service

1. **Add Database Service**
   - Service Type: Redis
   - Version: 7-alpine
   - Persistence: Enable

## Phase 3: Domain & SSL Configuration

### Configure Domains in Coolify

1. **Frontend Domain**
   - Domain: `your-domain.com`
   - SSL: Enable Let's Encrypt

2. **Backend Domain**
   - Domain: `api.your-domain.com`
   - SSL: Enable Let's Encrypt

## Phase 4: Deploy

### Deploy via Git Push

```bash
# Push to main branch triggers automatic deployment
git push origin main
```

### Manual Deploy via Coolify Dashboard

1. Navigate to Services
2. Select service
3. Click "Deploy" button

## Phase 5: Verification

### Health Checks

```bash
# Backend health check
curl -sS https://api.your-domain.com/health | jq

# Expected response
{"status": "healthy", "environment": "production"}

# Frontend check
curl -I https://your-domain.com

# Expected: HTTP/1.1 200 OK
```

### API Documentation

```bash
# Access FastAPI docs
curl https://api.your-domain.com/docs
```

## Rollback Instructions

### Via Coolify Dashboard

1. Navigate to Service > Deployments
2. Select previous successful deployment
3. Click "Rollback"

### Via CLI

```bash
# List deployments
docker ps -a

# Restore previous image
docker tag <previous-image> <current-image>
docker-compose -f docker-compose.coolify.yml up -d
```

## Redeploy Command

```bash
# Quick redeploy
git checkout <tag-or-commit> && git push origin main
```

## Troubleshooting

### Build Failures

1. Check build logs in Coolify dashboard
2. Verify environment variables are set
3. Ensure Dockerfile syntax is correct

### Runtime Errors

1. Check container logs: `docker logs <container-name>`
2. Verify health check endpoint is accessible
3. Check resource limits

### Common Issues

- **CORS errors**: Update `CORS_ORIGINS` in backend env
- **API connection failed**: Verify `NEXT_PUBLIC_API_URL` in frontend
- **Redis connection refused**: Check Redis service is running

## Security Recommendations

1. Rotate all secrets after migration
2. Enable Coolify's built-in firewall
3. Configure rate limiting
4. Enable HTTPS only
5. Set up log aggregation