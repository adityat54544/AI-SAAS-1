#!/bin/bash
# ==============================================================================
# Gemini API Key Rotation Script
# ==============================================================================
# This script provides instructions for rotating Gemini API keys.
# It does NOT automatically rotate keys - manual intervention required.
# ==============================================================================

set -e

echo "================================================================================"
echo "GEMINI API KEY ROTATION GUIDE"
echo "================================================================================"
echo ""
echo "This script provides step-by-step instructions for rotating Gemini API keys."
echo "DO NOT run any destructive commands automatically."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}STEP 1: Generate new API key in Google AI Studio${NC}"
echo "----------------------------------------"
echo "1. Navigate to: https://aistudio.google.com/app/apikey"
echo "2. Sign in with your Google account"
echo "3. Click 'Create API Key'"
echo "4. Select or create a Google Cloud project"
echo "5. Copy the new API key immediately"
echo "6. (Optional) Set up API key restrictions:"
echo "   - Application restrictions (HTTP referrers, IP addresses, etc.)"
echo "   - API restrictions (limit to Generative Language API only)"
echo ""

echo -e "${YELLOW}STEP 2: Update environment variables${NC}"
echo "----------------------------------------"
echo "Update the following environment variables in each service:"
echo ""
echo "Railway Services:"
echo "  1. Go to: https://railway.app/dashboard"
echo "  2. Select your project"
echo "  3. For each service (api, worker):"
echo "     - Go to Variables tab"
echo "     - Update GEMINI_API_KEY with new value"
echo ""
echo "GitHub Repository Secrets:"
echo "  1. Go to: https://github.com/<owner>/<repo>/settings/secrets/actions"
echo "  2. Update GEMINI_API_KEY secret"
echo ""

echo -e "${YELLOW}STEP 3: Delete old API key${NC}"
echo "----------------------------------------"
echo "After verifying new key works:"
echo "  1. Go to: https://aistudio.google.com/app/apikey"
echo "  2. Find the old API key"
echo "  3. Click the delete/trash icon"
echo "  4. Confirm deletion"
echo ""

echo -e "${YELLOW}STEP 4: Verify rotation${NC}"
echo "----------------------------------------"
echo "Run the following checks:"
echo "  1. Health check: curl https://your-api-url/health"
echo "  2. Trigger an analysis job"
echo "  3. Verify AI responses are working"
echo "  4. Monitor logs for any API errors"
echo ""

echo -e "${RED}IMPORTANT SECURITY NOTES:${NC}"
echo "----------------------------------------"
echo "1. Never commit API keys to git repository"
echo "2. Rotate keys immediately if exposed"
echo "3. Use separate keys for different environments (dev/staging/prod)"
echo "4. Enable 2FA on your Google account"
echo "5. Set up API key restrictions in Google Cloud Console"
echo "6. Monitor API usage in Google Cloud Console for anomalies"
echo ""

echo -e "${GREEN}COST CONTROL REMINDERS:${NC}"
echo "----------------------------------------"
echo "The following environment variables control Gemini usage:"
echo "  - AI_MAX_TOKENS_PER_TASK: Maximum tokens per task (default: 32000)"
echo "  - AI_DAILY_QUOTA_PER_USER: Daily token quota per user (default: 100000)"
echo "  - AI_MODEL_DEFAULT: Default model (gemini-1.5-flash)"
echo ""
echo "Monitor costs at: https://console.cloud.google.com/billing"
echo ""

echo "================================================================================"
echo "Key rotation guide complete. Follow the steps above manually."
echo "================================================================================"