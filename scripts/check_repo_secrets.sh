#!/bin/bash
# Repository Secret Scanner
# Runs detect-secrets and gitleaks in dry-run mode to check for secrets
# Output is written to ci/secret_audit.txt
# Does NOT auto-fix any issues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/ci/secret_audit.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Repository Secret Scanner"
echo "========================================"
echo ""
echo "Running secret detection tools in dry-run mode..."
echo "Output will be saved to: $OUTPUT_FILE"
echo ""

# Create ci directory if it doesn't exist
mkdir -p "$REPO_ROOT/ci"

# Initialize output file
{
    echo "========================================"
    echo "SECRET AUDIT REPORT"
    echo "========================================"
    echo ""
    echo "Repository: AutoDevOps AI Platform"
    echo "Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "Commit: $(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
    echo ""
} > "$OUTPUT_FILE"

# ============================================
# Gitleaks Scan
# ============================================
echo -e "${YELLOW}Running Gitleaks...${NC}"
{
    echo "----------------------------------------"
    echo "GITLEAKS SCAN RESULTS"
    echo "----------------------------------------"
    echo ""
} >> "$OUTPUT_FILE"

if command -v gitleaks &> /dev/null; then
    # Run gitleaks in no-git mode for current files
    if gitleaks detect --source="$REPO_ROOT" --no-git --redact --verbose >> "$OUTPUT_FILE" 2>&1; then
        echo -e "${GREEN}✅ Gitleaks: No secrets detected in current files${NC}"
        echo "Status: PASSED - No secrets detected" >> "$OUTPUT_FILE"
    else
        echo -e "${RED}⚠️ Gitleaks: Potential secrets detected - review output${NC}"
        echo "Status: WARNINGS FOUND - Review details above" >> "$OUTPUT_FILE"
    fi
    
    echo "" >> "$OUTPUT_FILE"
    
    # Also scan git history
    {
        echo ""
        echo "--- Git History Scan ---"
        echo ""
    } >> "$OUTPUT_FILE"
    
    if gitleaks detect --source="$REPO_ROOT" --redact --verbose >> "$OUTPUT_FILE" 2>&1; then
        echo -e "${GREEN}✅ Gitleaks History: No secrets in git history${NC}"
        echo "History Status: PASSED" >> "$OUTPUT_FILE"
    else
        echo -e "${RED}⚠️ Gitleaks History: Potential secrets in history${NC}"
        echo "History Status: WARNINGS FOUND" >> "$OUTPUT_FILE"
    fi
else
    echo -e "${YELLOW}⚠️ Gitleaks not installed - skipping${NC}"
    echo "Gitleaks: NOT INSTALLED" >> "$OUTPUT_FILE"
    echo "Install: brew install gitleaks or download from https://github.com/gitleaks/gitleaks" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"

# ============================================
# Detect-Secrets Scan
# ============================================
echo -e "${YELLOW}Running detect-secrets...${NC}"
{
    echo ""
    echo "----------------------------------------"
    echo "DETECT-SECRETS SCAN RESULTS"
    echo "----------------------------------------"
    echo ""
} >> "$OUTPUT_FILE"

if command -v detect-secrets &> /dev/null; then
    # Run detect-secrets scan
    if detect-secrets scan "$REPO_ROOT" --all-files 2>/dev/null >> "$OUTPUT_FILE"; then
        echo -e "${GREEN}✅ Detect-secrets: Scan completed${NC}"
    else
        echo -e "${RED}⚠️ Detect-secrets: Issues found or scan failed${NC}"
    fi
    
    # Check baseline if it exists
    if [ -f "$REPO_ROOT/.secrets.baseline" ]; then
        {
            echo ""
            echo "--- Baseline Comparison ---"
            echo ""
        } >> "$OUTPUT_FILE"
        
        # Compare with baseline
        detect-secrets audit "$REPO_ROOT/.secrets.baseline" 2>&1 | head -50 >> "$OUTPUT_FILE" || true
    else
        echo -e "${YELLOW}⚠️ No .secrets.baseline file found${NC}"
        echo "Baseline: NOT FOUND - Consider running 'detect-secrets scan > .secrets.baseline'" >> "$OUTPUT_FILE"
    fi
else
    echo -e "${YELLOW}⚠️ detect-secrets not installed - skipping${NC}"
    echo "Detect-secrets: NOT INSTALLED" >> "$OUTPUT_FILE"
    echo "Install: pip install detect-secrets" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"

# ============================================
# Additional Checks
# ============================================
{
    echo ""
    echo "----------------------------------------"
    echo "ADDITIONAL CHECKS"
    echo "----------------------------------------"
    echo ""
    
    # Check for .env files
    echo "Checking for .env files..."
    echo "Env files found:" >> "$OUTPUT_FILE"
    find "$REPO_ROOT" -name "*.env*" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null >> "$OUTPUT_FILE" || echo "None found" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Check for private key files
    echo "Checking for private key files..."
    echo "Private key files found:" >> "$OUTPUT_FILE"
    find "$REPO_ROOT" -name "*.pem" -o -name "*.key" -o -name "*_rsa" -o -name "id_rsa*" 2>/dev/null >> "$OUTPUT_FILE" || echo "None found" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Check .gitignore for secret patterns
    echo "Checking .gitignore coverage..."
    if [ -f "$REPO_ROOT/.gitignore" ]; then
        echo ".gitignore exists: YES" >> "$OUTPUT_FILE"
        if grep -q ".env" "$REPO_ROOT/.gitignore" 2>/dev/null; then
            echo ".env in .gitignore: YES" >> "$OUTPUT_FILE"
        else
            echo ".env in .gitignore: NO - RECOMMEND ADDING" >> "$OUTPUT_FILE"
        fi
        if grep -q "*.pem" "$REPO_ROOT/.gitignore" 2>/dev/null || grep -q "*.key" "$REPO_ROOT/.gitignore" 2>/dev/null; then
            echo "Key files in .gitignore: YES" >> "$OUTPUT_FILE"
        else
            echo "Key files in .gitignore: NO - RECOMMEND ADDING" >> "$OUTPUT_FILE"
        fi
    else
        echo ".gitignore: NOT FOUND" >> "$OUTPUT_FILE"
    fi
    
} >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"

# ============================================
# Summary
# ============================================
{
    echo ""
    echo "========================================"
    echo "SUMMARY"
    echo "========================================"
    echo ""
    echo "This audit was run in DRY-RUN mode."
    echo "No files were modified."
    echo ""
    echo "If secrets were detected:"
    echo "1. DO NOT commit the secret to git history"
    echo "2. Rotate the exposed credential immediately"
    echo "3. Use .env.example for documentation only"
    echo "4. Store secrets in environment variables"
    echo ""
    echo "For remediation, see:"
    echo "- repo-migration/remove-secrets.sh"
    echo "- SECURITY.md"
    echo ""
    echo "========================================"
    echo "End of Report"
    echo "========================================"
} >> "$OUTPUT_FILE"

# Display results
echo ""
echo "========================================"
echo "Audit Complete"
echo "========================================"
echo ""
cat "$OUTPUT_FILE"
echo ""
echo -e "${GREEN}Full report saved to: $OUTPUT_FILE${NC}"