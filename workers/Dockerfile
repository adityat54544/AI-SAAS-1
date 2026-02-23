# AutoDevOps AI Platform - Worker Service (BullMQ)

FROM node:20-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --omit=dev

# Copy source
COPY src/ ./src/
COPY tsconfig.json ./

# Set environment variables
ENV NODE_ENV=production \
    WORKER_CONCURRENCY=5 \
    ANALYSIS_CONCURRENCY=2 \
    SYNC_CONCURRENCY=5 \
    CI_CONCURRENCY=2

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD node -e "process.exit(0)" || exit 1

# Run the worker with ts-node (skip type validation)
CMD ["npx", "ts-node", "--transpile-only", "--project", "tsconfig.json", "src/index.ts"]
