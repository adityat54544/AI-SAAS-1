# AutoDevOps AI Platform - Frontend Dockerfile (Next.js)
# Optimized for Railway/Coolify deployment with standalone output

# ==============================================================================
# Stage 1: Dependencies
# ==============================================================================
FROM node:20-alpine AS deps
WORKDIR /app

# Install dependencies for native modules
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install --omit=dev

# ==============================================================================
# Stage 2: Builder
# ==============================================================================
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build arguments for environment variables (passed from Coolify)
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_API_URL

# Set environment variables for build time
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application - skip prebuild validation scripts
RUN npm run build --ignore-scripts

# ==============================================================================
# Stage 3: Runner (Production)
# ==============================================================================
FROM node:20-alpine AS runner
WORKDIR /app

# Set environment to production
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy the standalone output (public may not exist in standalone mode)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy public folder if it exists (otherwise create empty directory)
RUN if [ -d "/app/public" ]; then cp -r /app/public ./public; else mkdir -p ./public; fi

# Copy startup validation script
COPY --from=builder --chown=nextjs:nodejs /app/scripts/startup-validation.ts ./scripts/

# Install ts-node for running the validation script
RUN npm install -g ts-node

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check - use /healthz endpoint for more reliable checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/healthz || exit 1

# Startup validation timeout (in seconds)
ENV STARTUP_TIMEOUT=30

# Start the Next.js server directly (skip validation in production)
CMD ["node", "server.js"]
