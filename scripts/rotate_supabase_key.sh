#!/bin/bash
# ==============================================================================
# Supabase Key Rotation Script
# ==============================================================================
# This script provides instructions for rotating Supabase keys.
# It does NOT automatically rotate keys - manual intervention required.
# ==============================================================================

set -e

echo "================================================================================"
echo "SUPABASE KEY ROTATION GUIDE"
echo "================================================================================"
echo ""
echo "This script provides step-by-step instructions for rotating Supabase keys."
echo "DO NOT run any destructive commands automatically."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}STEP 1: Generate new keys in Supabase Dashboard${NC}"
echo "----------------------------------------"
echo "1. Navigate to: https://supabase.com/dashboard"
echo "2. Select your project"
echo "3. Go to Settings > API"
echo "4. For service_role key rotation:"
echo "   - Click 'Reset service_role key' (WARNING: This will invalidate current key)"
echo "   - Copy the new key immediately"
echo "5. For anon key rotation (if needed):"
echo "   - Click 'Reset anon key'"
echo "   - Copy the new key immediately"
echo ""

echo -e "${YELLOW}STEP 2: Update environment variables${NC}"
echo "----------------------------------------"
echo "Update the following environment variables in each service:"
echo ""
echo "Railway Services:"
echo "  1. Go to: https://railway.app/dashboard"
echo "  2. Select your project"
echo "  3. For each service (api, worker, cron):"
echo "     - Go to Variables tab"
echo "     - Update SUPABASE_SERVICE_ROLE_KEY with new value"
echo "     - Update SUPABASE_ANON_KEY if rotated"
echo ""
echo "GitHub Repository Secrets:"
echo "  1. Go to: https://github.com/<owner>/<repo>/settings/secrets/actions"
echo "  2. Update the following secrets:"
echo "     - SUPABASE_SERVICE_ROLE_KEY"
echo "     - SUPABASE_ANON_KEY"
echo ""

echo -e "${YELLOW}STEP 3: Redeploy services${NC}"
echo "----------------------------------------"
echo "After updating environment variables:"
echo "  1. Trigger a new deployment in Railway"
echo "  2. Verify services are healthy"
echo "  3. Monitor logs for any authentication errors"
echo ""

echo -e "${YELLOW}STEP 4: Verify rotation${NC}"
echo "----------------------------------------"
echo "Run the following checks:"
echo "  1. Health check: curl https://your-api-url/health"
echo "  2. Test authentication flow"
echo "  3. Check worker job processing"
echo ""

echo -e "${RED}IMPORTANT SECURITY NOTES:${NC}"
echo "----------------------------------------"
echo "1. Never commit keys to git repository"
echo "2. Rotate keys immediately if exposed"
echo "3. Use separate keys for different environments"
echo "4. Enable 2FA on all accounts with key access"
echo "5. Log key rotation events in your security audit trail"
echo ""

echo "================================================================================"
echo "Key rotation guide complete. Follow the steps above manually."
echo "================================================================================"