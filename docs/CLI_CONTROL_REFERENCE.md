# Level-4 Infrastructure CLI Control Reference

> **Complete CLI authority for GitHub + Railway + Vercel from local terminal**
> Generated: 2026-02-22
> Status: ✅ Fully Authenticated and Operational

---

## 🔐 Authentication Status

| CLI | Version | Account | Status |
|-----|---------|---------|--------|
| **GitHub CLI** | 2.87.2 | `adityat54544` | ✅ Authenticated |
| **Vercel CLI** | 50.22.1 | `adityat100810081008-6460` | ✅ Authenticated |
| **Railway CLI** | 4.30.3 | `pibifo1773@esyline.com` | ✅ Authenticated |

### Token Scopes
- **GitHub**: `gist`, `read:org`, `repo`, `workflow` (full repo + workflow control)

---

## 📁 Project Links

| Platform | Project | Environment | Service |
|----------|---------|-------------|---------|
| Railway | `nurturing-enjoyment` | `production` | `AI-SAAS-1` |
| GitHub | `adityat54544/AI-SAAS-1` | `main` branch | - |
| Vercel | `aditya-tiwaris-projects-f3858565` | - | Frontend |

---

## 🚀 GitHub CLI Commands

### Repository Management
```powershell
# View repository info
gh repo view adityat54544/AI-SAAS-1

# Create new repository
gh repo create <name> --public --clone

# Clone repository
gh repo clone adityat54544/AI-SAAS-1

# Fork repository
gh repo fork adityat54544/AI-SAAS-1 --clone

# Delete repository (DANGEROUS)
gh repo delete adityat54544/<repo> --yes

# List repositories
gh repo list adityat54544 --limit 50
```

### Workflow Control
```powershell
# List all workflows
gh workflow list

# View workflow runs
gh run list --workflow=CI --limit 10

# Trigger workflow manually
gh workflow run CI --ref main

# View workflow run details
gh run view <run-id>

# Cancel workflow run
gh run cancel <run-id>

# Re-run workflow
gh run rerun <run-id>

# Download workflow logs
gh run download <run-id>

# Watch workflow run in real-time
gh run watch <run-id>
```

### Pull Request Management
```powershell
# Create PR
gh pr create --title "feat: new feature" --body "Description"

# List PRs
gh pr list --state open

# View PR
gh pr view <pr-number>

# Merge PR
gh pr merge <pr-number> --squash --delete-branch

# Close PR
gh pr close <pr-number>

# Checkout PR locally
gh pr checkout <pr-number>
```

### Issue Management
```powershell
# Create issue
gh issue create --title "Bug: description" --body "Details"

# List issues
gh issue list --state open

# Close issue
gh issue close <issue-number>

# Add labels
gh issue edit <issue-number> --add-label "bug,high-priority"
```

### Secrets Management
```powershell
# List secrets
gh secret list

# Set secret
gh secret set <SECRET_NAME> --body "secret-value"

# Set secret from file
gh secret set <SECRET_NAME> < secret.txt

# Delete secret
gh secret delete <SECRET_NAME>
```

### Variables Management
```powershell
# List variables
gh variable list

# Set variable
gh variable set <VAR_NAME> --body "value"

# Delete variable
gh variable delete <VAR_NAME>
```

---

## 🛤️ Railway CLI Commands

### Project Management
```powershell
# View current status
railway status

# List projects
railway project

# Create new project
railway project create

# Link existing project
railway link

# Unlink project
railway unlink
```

### Service Management
```powershell
# List services
railway service list

# Select service
railway service

# View service logs
railway logs

# View logs with filter
railway logs --filter "error"

# Deploy service
railway up

# Deploy with CI mode
railway up --ci
```

### Environment Management
```powershell
# List environments
railway environment

# Create environment
railway environment create staging

# Switch environment
railway environment production
```

### Variables Management
```powershell
# List all variables
railway variables

# Set variable
railway variables set KEY=value

# Set multiple variables
railway variables set KEY1=value1 KEY2=value2

# Delete variable
railway variables unset KEY
```

### Domain Management
```powershell
# Generate domain
railway domain

# Add custom domain
railway domain add example.com
```

### Database Management
```powershell
# Connect to database
railway connect

# Run database migration
railway run python -m alembic upgrade head
```

---

## ▲ Vercel CLI Commands

### Deployment Management
```powershell
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Deploy with specific env
vercel --prod --env NEXT_PUBLIC_API_URL=https://api.example.com

# List deployments
vercel list

# View deployment details
vercel inspect <deployment-url>

# Delete deployment
vercel remove <deployment-url>

# Rollback to previous deployment
vercel rollback
```

### Project Management
```powershell
# Link project
vercel link

# View project info
vercel project ls

# View project domains
vercel domains ls

# Add domain
vercel domains add example.com

# Remove domain
vercel domains rm example.com
```

### Environment Variables
```powershell
# List environment variables
vercel env ls

# Add environment variable
vercel env add NEXT_PUBLIC_API_URL

# Pull env vars to local
vercel env pull .env.local

# Remove env var
vercel env rm NEXT_PUBLIC_API_URL
```

### Logs & Debugging
```powershell
# View logs
vercel logs <deployment-url>

# Real-time logs
vercel logs <deployment-url> --follow

# View build logs
vercel logs <deployment-url> --output
```

---

## 🔄 Complete Workflow Automation

### Full Stack Deployment
```powershell
# 1. Push changes to GitHub
git add . && git commit -m "feat: update feature"
git push origin main

# 2. Trigger CI workflow
gh workflow run CI --ref main

# 3. Deploy backend to Railway
railway up --service AI-SAAS-1

# 4. Deploy frontend to Vercel
cd frontend && vercel --prod

# 5. Watch CI status
gh run watch
```

### Emergency Rollback
```powershell
# Railway rollback (redeploy previous commit)
railway up --service AI-SAAS-1

# Vercel rollback
vercel rollback

# GitHub revert commit
gh api repos/adityat54544/AI-SAAS-1/commits/<sha>/comments -f body="Rollback reason"
```

### Database Migration Pipeline
```powershell
# 1. Run migration locally
supabase migration new <migration_name>

# 2. Apply to production (via Supabase CLI)
supabase db push --linked

# 3. Update Railway variables if needed
railway variables set DB_SCHEMA_VERSION=2

# 4. Redeploy backend
railway up --service AI-SAAS-1
```

### Environment Sync
```powershell
# Pull Railway variables to local
railway variables --json > railway-env.json

# Pull Vercel env to local
vercel env pull .env.local

# Push local env to Railway
railway variables set $(cat .env | grep -v '^#' | xargs)
```

---

## 📊 Monitoring & Observability

### Health Checks
```powershell
# Check Railway service health
curl https://ai-saas-1-production.up.railway.app/health

# Check Railway logs
railway logs --filter "error" --lines 100

# Check Vercel deployment status
vercel list

# Check GitHub Actions status
gh run list --workflow=CI --limit 5
```

### Log Streaming
```powershell
# Railway logs (real-time)
railway logs

# GitHub workflow logs
gh run watch

# Vercel build logs
vercel logs <url> --follow
```

---

## 🔧 Troubleshooting

### Re-authentication
```powershell
# GitHub CLI
gh auth login --web

# Vercel CLI
vercel login

# Railway CLI
railway login
```

### Reset Links
```powershell
# Reset Railway project link
railway unlink && railway link

# Reset Vercel project link
vercel link
```

### Clear Caches
```powershell
# Clear Vercel cache
vercel --force

# Clear Railway build cache (redeploy)
railway up --force
```

---

## 📋 Quick Reference Card

| Action | Command |
|--------|---------|
| **Deploy Backend** | `railway up` |
| **Deploy Frontend** | `vercel --prod` |
| **View Logs** | `railway logs` or `vercel logs <url>` |
| **Set Variable** | `railway variables set KEY=value` |
| **Trigger CI** | `gh workflow run CI` |
| **Create PR** | `gh pr create` |
| **View Status** | `railway status` / `gh auth status` |
| **Rollback** | `vercel rollback` / redeploy Railway |

---

## ✅ Verification Commands

Run these to verify CLI control:

```powershell
# Verify GitHub
gh auth status
gh repo view adityat54544/AI-SAAS-1

# Verify Railway
railway whoami
railway status
railway variables

# Verify Vercel
vercel whoami
vercel list
```

---

**System Status: Level-4 Infrastructure Authority Achieved** ✅

Your local terminal now has complete control over:
- ✅ GitHub: Repositories, Workflows, Secrets, PRs, Issues
- ✅ Railway: Services, Variables, Deployments, Logs, Environments
- ✅ Vercel: Deployments, Domains, Environment Variables, Rollbacks