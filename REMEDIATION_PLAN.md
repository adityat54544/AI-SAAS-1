# Vercel to Coolify Migration - Remediation Plan

## Current Status: PARTIALLY COMPLETE

### Completed Tasks ✅
1. **Repository Analysis**
   - Created `repo_analysis.json` with complete file listing
   - Created `secrets_inventory.json` (key names only, no values)

2. **Vercel Artifacts Removed**
   - Deleted `frontend/.vercel/` directory
   - Deleted `frontend/vercel.json`
   - Deleted `vercel-patch.json`
   - Removed Railway configs (`railway.toml`, `frontend/railway.toml`)

3. **Dockerfiles Created**
   - `frontend/Dockerfile` - Next.js standalone production build
   - `frontend/.dockerignore` - Build exclusions
   - `Dockerfile.coolify` - FastAPI production build with dynamic PORT
   - `docker-compose.coolify.yml` - Local testing configuration

4. **Configuration Updated**
   - `frontend/next.config.js` - Enabled standalone output
   - `.gitignore` - Added Vercel/Coolify patterns
   - `.env.example` - Removed Vercel/Railway references

5. **Documentation Created**
   - `docs/coolify_deployment.md` - Complete deployment guide
   - `deployment_report.json` - Deployment configuration
   - `security_migration_report.json` - Security audit report

6. **Git Commits Made**
   - `8c485f3` - chore: migrate from Vercel/Railway to Coolify deployment
   - `38dcf5d` - docs: add migration reports for Vercel to Coolify transition

---

### Remaining Tasks (Require Credentials)

#### 1. SSH into Ubuntu VPS and Install Coolify
**Required:** `COOLIFY_SSH` or VPS IP/credentials

```bash
# SSH into VPS
ssh root@YOUR_VPS_IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Coolify (non-interactive)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# Verify installation
docker ps | grep coolify
```

#### 2. Migrate Secrets to Coolify
**Required:** `COOLIFY_ADMIN_TOKEN`, VPS URL

```bash
# Set Coolify API endpoint
COOLIFY_URL="https://your-vps-ip:3000"
COOLIFY_TOKEN="your-admin-token"

# Create backend service and set environment variables
curl -X POST "${COOLIFY_URL}/api/v1/services" \
  -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "autodevops-api",
    "dockerfile": "Dockerfile.coolify",
    "repository": "https://github.com/adityat54544/AI-SAAS-1"
  }'

# Set backend environment variables (read from stdin)
# Note: Pass actual secret values via stdin, never echo to logs
cat <<EOF | curl -X POST "${COOLIFY_URL}/api/v1/services/autodevops-api/env" \
  -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @-
{
  "SUPABASE_URL": "<actual-value>",
  "SUPABASE_SERVICE_ROLE_KEY": "<actual-value>",
  "SUPABASE_ANON_KEY": "<actual-value>",
  "GEMINI_API_KEY": "<actual-value>",
  "REDIS_URL": "redis://redis:6379/0",
  "ENCRYPTION_KEY": "<actual-value>",
  "CORS_ORIGINS": "https://your-domain.com",
  "FRONTEND_URL": "https://your-domain.com"
}
EOF
```

#### 3. Revoke Vercel GitHub Integration
**Required:** `GITHUB_TOKEN` with repo scope

```bash
# List GitHub App installations
curl -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/user/installations

# Revoke Vercel app (replace INSTALLATION_ID)
curl -X DELETE \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/user/installations/INSTALLATION_ID

# Delete Vercel webhooks
curl -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/repos/adityat54544/AI-SAAS-1/hooks

# Delete each Vercel webhook by ID
curl -X DELETE \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/repos/adityat54544/AI-SAAS-1/hooks/HOOK_ID
```

#### 4. Push Changes to GitHub

```bash
# Push all commits
git push origin main
```

#### 5. Deploy and Verify

```bash
# Trigger deployment (via git push or Coolify API)
git push origin main

# OR via Coolify API
curl -X POST "${COOLIFY_URL}/api/v1/services/autodevops-api/deploy" \
  -H "Authorization: Bearer ${COOLIFY_TOKEN}"

curl -X POST "${COOLIFY_URL}/api/v1/services/autodevops-frontend/deploy" \
  -H "Authorization: Bearer ${COOLIFY_TOKEN}"

# Verify health checks
curl -sS https://api.your-domain.com/health | jq
curl -I https://your-domain.com
```

---

### Git History Secret Scan

To scan git history for potentially leaked secrets:

```bash
# Install git-secrets or trufflehog
# Using trufflehog:
pip install trufflehog3
trufflehog3 --history https://github.com/adityat54544/AI-SAAS-1

# Using git-secrets:
git secrets --install
git secrets --scan-history

# If secrets found, clean history with BFG:
# 1. Create passwords.txt with secret patterns
# 2. Run:
bfg --replace-text passwords.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force origin main
```

---

### Automated Verification Checklist

After deployment, run these verification checks:

```bash
# 1. DNS Resolution
nslookup your-domain.com
nslookup api.your-domain.com

# 2. Backend Health
curl -sS https://api.your-domain.com/health | jq
# Expected: {"status": "healthy", "environment": "production"}

# 3. Frontend HTTP 200
curl -I https://your-domain.com
# Expected: HTTP/1.1 200 OK

# 4. FastAPI Docs Accessible
curl -sS https://api.your-domain.com/docs | head -20
# Expected: HTML content with FastAPI swagger

# 5. CORS Preflight Test
curl -X OPTIONS https://api.your-domain.com/health \
  -H "Origin: https://your-domain.com" \
  -H "Access-Control-Request-Method: GET"

# 6. Redis Connectivity (inside container)
docker exec autodevops-api python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
# Expected: True

# 7. Sample API Call
curl -X GET https://api.your-domain.com/health \
  -H "Authorization: Bearer <test-token>"
```

---

### Rollback Instructions

```bash
# Via Coolify Dashboard:
# 1. Navigate to Service > Deployments
# 2. Select previous successful deployment
# 3. Click "Rollback"

# Via CLI:
git revert HEAD
git push origin main

# Or checkout specific commit:
git checkout <previous-commit-hash>
git push origin main --force
```

---

### Redeploy Command

```bash
git checkout <tag-or-commit> && git push origin main
```

---

## Required Credentials Summary

| Credential | Purpose | Required For |
|------------|---------|--------------|
| `GITHUB_TOKEN` | GitHub API access | Revoke Vercel integration, push changes |
| `COOLIFY_SSH` or VPS IP | VPS access | Install Coolify on Ubuntu |
| `COOLIFY_ADMIN_TOKEN` | Coolify API | Configure services, set secrets |
| Secret values | Environment vars | Coolify service configuration |

---

## Files Ready for Deployment

- ✅ `frontend/Dockerfile` - Production Next.js
- ✅ `frontend/.dockerignore` - Build exclusions
- ✅ `Dockerfile.coolify` - Production FastAPI
- ✅ `docker-compose.coolify.yml` - Local testing
- ✅ `docs/coolify_deployment.md` - Deployment guide
- ✅ `deployment_report.json` - Configuration report
- ✅ `security_migration_report.json` - Security audit
- ✅ `.env.example` - Updated template

## Next Step

Provide the required credentials to complete the migration:
1. `GITHUB_TOKEN` - To push changes and revoke Vercel integration
2. VPS SSH credentials - To install Coolify
3. Secret values - To configure Coolify services