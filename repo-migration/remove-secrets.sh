#!/bin/bash
# ==============================================================================
# Secret Removal Script for Git History
# ==============================================================================
# This script helps identify and safely remove secrets from git history.
# WARNING: This is a DESTRUCTIVE operation that rewrites git history.
# 
# IMPORTANT: 
# - Always run with --dry-run first
# - Requires --apply flag to actually make changes
# - All team members must re-clone after history rewrite
# - Rotate ALL exposed secrets immediately after history rewrite
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default flags
DRY_RUN=true
APPLY=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --apply)
            APPLY=true
            DRY_RUN=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--apply] [--help]"
            echo ""
            echo "Options:"
            echo "  --dry-run  Show what would be done without making changes (default)"
            echo "  --apply    Actually rewrite git history (DESTRUCTIVE)"
            echo "  --help     Show this help message"
            echo ""
            echo "WARNING: --apply will rewrite git history and require all team members to re-clone"
            exit 0
            ;;
    esac
done

echo "================================================================================"
echo "SECRET REMOVAL FROM GIT HISTORY"
echo "================================================================================"
echo ""

if [ "$APPLY" = true ]; then
    echo -e "${RED}!!! DESTRUCTIVE MODE ENABLED !!!${NC}"
    echo "This will rewrite git history and force push to remote."
    echo ""
    read -p "Are you absolutely sure? Type 'yes' to continue: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi
else
    echo -e "${YELLOW}Running in DRY-RUN mode${NC}"
    echo "No changes will be made. Use --apply to actually rewrite history."
    echo ""
fi

# ==============================================================================
# STEP 1: Check prerequisites
# ==============================================================================
echo -e "${BLUE}STEP 1: Checking prerequisites${NC}"
echo "----------------------------------------"

# Check for required tools
if ! command -v git &> /dev/null; then
    echo -e "${RED}ERROR: git is not installed${NC}"
    exit 1
fi

if ! command -v detect-secrets &> /dev/null; then
    echo -e "${YELLOW}WARNING: detect-secrets is not installed${NC}"
    echo "Install with: pip install detect-secrets"
fi

if ! command -v gitleaks &> /dev/null; then
    echo -e "${YELLOW}WARNING: gitleaks is not installed${NC}"
    echo "Install from: https://github.com/gitleaks/gitleaks"
fi

# Check for git-filter-repo (preferred tool for history rewriting)
if ! command -v git-filter-repo &> /dev/null; then
    echo -e "${YELLOW}WARNING: git-filter-repo is not installed${NC}"
    echo "Install with: pip install git-filter-repo"
    echo "git-filter-repo is the recommended tool for rewriting git history."
fi

echo -e "${GREEN}Prerequisites check complete${NC}"
echo ""

# ==============================================================================
# STEP 2: Scan for secrets
# ==============================================================================
echo -e "${BLUE}STEP 2: Scanning for secrets${NC}"
echo "----------------------------------------"

echo "Running detect-secrets scan..."
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --all-files > .detected-secrets.json 2>/dev/null || true
    echo "Results saved to .detected-secrets.json"
fi

echo ""
echo "Running gitleaks scan..."
if command -v gitleaks &> /dev/null; then
    if [ "$DRY_RUN" = true ]; then
        gitleaks detect --verbose --redact || true
    else
        gitleaks detect --verbose --redact --report-path .gitleaks-report.json || true
        echo "Results saved to .gitleaks-report.json"
    fi
fi

echo ""

# ==============================================================================
# STEP 3: Create secrets patterns file
# ==============================================================================
echo -e "${BLUE}STEP 3: Preparing secrets patterns${NC}"
echo "----------------------------------------"

# Create a file with patterns to replace
cat > .secrets-patterns.txt << 'EOF'
# Add your secret patterns here (one per line)
# Format: pattern_to_find==>REPLACEMENT_VALUE
# 
# Examples:
# AKIA[A-Z0-9]{16}==>REMOVED_AWS_KEY
# sk-[a-zA-Z0-9]{32,}==>REMOVED_API_KEY
# [a-zA-Z0-9]{32,}==>REMOVED_SECRET
EOF

echo "Created .secrets-patterns.txt template"
echo "Edit this file to add your specific secret patterns"
echo ""

# ==============================================================================
# STEP 4: Show instructions for history rewrite
# ==============================================================================
echo -e "${BLUE}STEP 4: History rewrite instructions${NC}"
echo "----------------------------------------"
echo ""
echo "To remove secrets from git history, follow these steps:"
echo ""

echo "1. Create a fresh clone of the repository:"
echo "   git clone https://github.com/owner/repo.git repo-clean"
echo "   cd repo-clean"
echo ""

echo "2. Create a backup:"
echo "   cd .. && cp -r repo-clean repo-backup && cd repo-clean"
echo ""

echo "3. Run git-filter-repo with your patterns:"
echo "   git filter-repo --replace-text .secrets-patterns.txt"
echo ""

echo "4. Verify the changes:"
echo "   git log --all --oneline"
echo "   gitleaks detect --verbose"
echo ""

echo "5. Force push to remote (DESTRUCTIVE):"
echo "   git remote add origin https://github.com/owner/repo.git"
echo "   git push --force --all origin"
echo "   git push --force --tags origin"
echo ""

echo "6. Rotate ALL exposed secrets immediately:"
echo "   - API keys (Gemini, GitHub, etc.)"
echo "   - Database credentials (Supabase)"
echo "   - Encryption keys"
echo "   - OAuth secrets"
echo ""

# ==============================================================================
# STEP 5: Apply if requested
# ==============================================================================
if [ "$APPLY" = true ]; then
    echo -e "${RED}STEP 5: Applying history rewrite${NC}"
    echo "----------------------------------------"
    echo ""
    echo "This script does NOT automatically rewrite history."
    echo "Follow the manual steps above to ensure safety."
    echo ""
    echo "After completing the history rewrite:"
    echo "1. Rotate ALL secrets that were exposed"
    echo "2. Notify all team members to re-clone"
    echo "3. Update all CI/CD secrets"
    echo "4. Document the incident in your security log"
fi

# ==============================================================================
# Cleanup
# ==============================================================================
echo ""
echo "================================================================================"
echo "Scan complete. Review results above."
echo "================================================================================"
echo ""
echo -e "${YELLOW}REMINDERS:${NC}"
echo "1. Never commit secrets to git"
echo "2. Use pre-commit hooks (detect-secrets, gitleaks)"
echo "3. Use environment variables or secret management"
echo "4. Rotate secrets immediately if exposed"
echo "5. Enable branch protection rules"
echo ""