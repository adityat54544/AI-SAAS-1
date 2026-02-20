#!/bin/bash
# ==============================================================================
# PostgreSQL Backup Script for Supabase/PostgreSQL
# ==============================================================================
# This script performs pg_dump backups and uploads to S3-compatible storage.
# Designed to run as a Railway cron job.
#
# Required environment variables:
# - DATABASE_URL or SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
# - S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION
# - BACKUP_RETENTION_DAYS (optional, default: 30)
# ==============================================================================

set -e

# Configuration
BACKUP_DIR="/tmp/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="autodevops_backup_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================================================"
echo "PostgreSQL Backup Script"
echo "================================================================================"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# ==============================================================================
# STEP 1: Create backup directory
# ==============================================================================
echo -e "${YELLOW}STEP 1: Preparing backup directory${NC}"
mkdir -p "${BACKUP_DIR}"
echo "Backup directory: ${BACKUP_DIR}"

# ==============================================================================
# STEP 2: Extract connection info from DATABASE_URL
# ==============================================================================
echo -e "${YELLOW}STEP 2: Extracting database connection info${NC}"

if [ -n "${DATABASE_URL}" ]; then
    echo "Using DATABASE_URL for connection"
    # Parse DATABASE_URL (format: postgresql://user:pass@host:port/dbname)
    DB_HOST=$(echo "${DATABASE_URL}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo "${DATABASE_URL}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo "${DATABASE_URL}" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    DB_USER=$(echo "${DATABASE_URL}" | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
elif [ -n "${SUPABASE_URL}" ]; then
    echo "Using SUPABASE_URL for connection"
    # For Supabase, we use the connection pooler or direct connection
    DB_HOST="db.${SUPABASE_URL#https://}"
    DB_PORT="5432"
    DB_NAME="postgres"
    DB_USER="postgres"
else
    echo -e "${RED}ERROR: No database connection configured${NC}"
    echo "Set DATABASE_URL or SUPABASE_URL environment variable"
    exit 1
fi

echo "Database host: ${DB_HOST}"
echo "Database name: ${DB_NAME}"
echo "Database user: ${DB_USER}"
echo "Database port: ${DB_PORT:-5432}"

# ==============================================================================
# STEP 3: Perform pg_dump
# ==============================================================================
echo -e "${YELLOW}STEP 3: Performing pg_dump backup${NC}"

BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Set PGPASSWORD from DATABASE_URL if available
if [ -n "${DATABASE_URL}" ]; then
    export PGPASSWORD=$(echo "${DATABASE_URL}" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
fi

# Run pg_dump with compression
echo "Running pg_dump..."
pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT:-5432}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    | gzip > "${BACKUP_PATH}"

# Check backup was created
if [ -f "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    echo -e "${GREEN}Backup created: ${BACKUP_PATH} (${BACKUP_SIZE})${NC}"
else
    echo -e "${RED}ERROR: Backup file not created${NC}"
    exit 1
fi

# ==============================================================================
# STEP 4: Upload to S3
# ==============================================================================
echo -e "${YELLOW}STEP 4: Uploading to S3${NC}"

if [ -n "${S3_BUCKET}" ]; then
    echo "S3 Bucket: ${S3_BUCKET}"
    echo "S3 Region: ${S3_REGION:-us-east-1}"
    
    # Configure AWS CLI
    aws configure set aws_access_key_id "${S3_ACCESS_KEY}"
    aws configure set aws_secret_access_key "${S3_SECRET_KEY}"
    aws configure set default.region "${S3_REGION:-us-east-1}"
    
    # Upload to S3
    S3_PATH="s3://${S3_BUCKET}/backups/postgresql/${BACKUP_FILE}"
    echo "Uploading to: ${S3_PATH}"
    
    aws s3 cp "${BACKUP_PATH}" "${S3_PATH}" \
        --storage-class STANDARD_IA \
        --metadata "timestamp=${TIMESTAMP},database=${DB_NAME}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Upload successful${NC}"
    else
        echo -e "${RED}ERROR: Upload failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}S3_BUCKET not configured, skipping upload${NC}"
fi

# ==============================================================================
# STEP 5: Cleanup old backups
# ==============================================================================
echo -e "${YELLOW}STEP 5: Cleaning up old backups${NC}"

# Local cleanup
echo "Cleaning local backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "autodevops_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

# S3 cleanup (if configured)
if [ -n "${S3_BUCKET}" ]; then
    echo "Cleaning S3 backups older than ${RETENTION_DAYS} days..."
    CUTOFF_DATE=$(date -d "-${RETENTION_DAYS} days" +%Y%m%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y%m%d 2>/dev/null)
    
    aws s3 ls "s3://${S3_BUCKET}/backups/postgresql/" | while read -r line; do
        FILE_DATE=$(echo "${line}" | awk '{print $4}' | grep -o '[0-9]\{8\}' | head -1)
        if [ -n "${FILE_DATE}" ] && [ "${FILE_DATE}" -lt "${CUTOFF_DATE}" ]; then
            FILE_NAME=$(echo "${line}" | awk '{print $4}')
            echo "Deleting old backup: ${FILE_NAME}"
            aws s3 rm "s3://${S3_BUCKET}/backups/postgresql/${FILE_NAME}" 2>/dev/null || true
        fi
    done
fi

# ==============================================================================
# STEP 6: Cleanup local temp file
# ==============================================================================
rm -f "${BACKUP_PATH}"

# ==============================================================================
# Summary
# ==============================================================================
echo ""
echo "================================================================================"
echo -e "${GREEN}Backup completed successfully${NC}"
echo "================================================================================"
echo "Backup file: ${BACKUP_FILE}"
echo "Retention: ${RETENTION_DAYS} days"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# Output metrics for monitoring
echo "backup_status=success"
echo "backup_timestamp=${TIMESTAMP}"
echo "backup_size_bytes=$(stat -f%z "${BACKUP_PATH}" 2>/dev/null || stat -c%s "${BACKUP_PATH}" 2>/dev/null || echo 0)"