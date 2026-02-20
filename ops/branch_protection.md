# GitHub Branch Protection Configuration

## Recommended Settings for `main` Branch

### 1. Navigate to Branch Protection

1. Go to your repository on GitHub
2. Click **Settings** → **Branches**
3. Click **Add branch protection rule**
4. Enter `main` as the branch name pattern

### 2. Protection Rules to Enable

#### Branch Protection Settings

```
☑ Require a pull request before merging
  └─ ☑ Require approvals: 1
  └─ ☑ Dismiss stale pull request approvals when new commits are pushed
  └─ ☑ Require review from Code Owners (if CODEOWNERS file exists)

☑ Require status checks to pass before merging
  └─ ☑ Require branches to be up to date before merging
  └─ Required status checks:
      • security-scan
      • backend-test
      • frontend-test
      • workers-test
      • infra-lint

☑ Require conversation resolution before merging

☑ Require signed commits

☑ Require linear history

☐ Include administrators (optional - enable for production)
```

### 3. CODEOWNERS File

Create `.github/CODEOWNERS`:

```
# Default owners
* @your-org/platform-team

# Security-sensitive files
app/config.py @your-org/security-team
.github/workflows/ @your-org/platform-team
infra/ @your-org/platform-team

# Database migrations
supabase/migrations/ @your-org/platform-team

# Documentation
*.md @your-org/docs-team
```

### 4. GitHub CLI Configuration

```bash
# Set branch protection using GitHub CLI
gh api -X PUT repos/{owner}/{repo}/branches/main/protection \
  -F required_status_checks='{"strict":true,"contexts":["security-scan","backend-test","frontend-test","workers-test"]}' \
  -F enforce_admins=false \
  -F required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
  -F restrictions=null \
  -F required_linear_history=true \
  -F allow_force_pushes=false \
  -F allow_deletions=false
```

### 5. Required Secrets for CI

Configure these secrets in GitHub repository settings:

| Secret Name | Description | Required By |
|-------------|-------------|-------------|
| `SUPABASE_URL` | Supabase project URL | backend-test |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key | backend-test |
| `GITHUB_CLIENT_ID` | OAuth app ID | backend-test |
| `GITHUB_CLIENT_SECRET` | OAuth secret | backend-test |
| `GEMINI_API_KEY` | AI API key | backend-test |
| `RAILWAY_TOKEN` | Railway deployment | deploy |

### 6. Signed Commits Setup

All contributors must sign commits:

```bash
# Install GPG (macOS)
brew install gnupg

# Generate GPG key
gpg --full-generate-key

# List keys
gpg --list-secret-keys --keyid-format=long

# Configure git
git config --global user.signingkey <KEY_ID>
git config --global commit.gpgsign true

# Add GPG key to GitHub
# Copy output of:
gpg --armor --export <KEY_ID>
# Paste in GitHub Settings → SSH and GPG keys
```

### 7. Environment Protection

For production deployments:

1. Go to **Settings** → **Environments**
2. Create `production` environment
3. Add protection rules:
   - Required reviewers (1-2 approvers)
   - Wait timer (5 minutes for rollback window)
   - Deployment branches: `main` only

### 8. Webhook Configuration (Optional)

Configure repository webhooks for notifications:

```
Payload URL: https://api.autodevops.ai/webhooks/github
Content type: application/json
Secret: <generate-secure-secret>
Events:
  ☑ Push
  ☑ Pull request
  ☑ Pull request review
```

## Verification

After configuration, verify:

1. Create a test PR - verify status checks run
2. Attempt to push directly to main - should be blocked
3. Attempt to merge without approval - should be blocked
4. Verify signed commit requirement

## Related Documentation

- [Pre-commit Configuration](../.pre-commit-config.yaml)
- [CI Pipeline](../.github/workflows/ci.yml)
- [Verification Procedures](./verification.md)