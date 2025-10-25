# Multi-stage Dockerfile for Next.js application
# Optimized for production deployment

# ==================== BUILD STAGE ====================
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN \
  rm -f package-lock.json && \
  if [ -f yarn.lock ]; then yarn install --frozen-lockfile --prefer-offline; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else npm install; \
  fi

# ==================== BUILD STAGE ====================
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variable to enable standalone output
ENV NEXT_TELEMETRY_DISABLED 1
ENV NEXT_OUTPUT standalone

# Build application
RUN npm run build

# ==================== PRODUCTION STAGE ====================
FROM nginx:alpine AS runner

# Install ca-certificates for HTTPS and security
RUN apk add --no-cache ca-certificates

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/out /app

# Copy nginx configuration for Next.js standalone
COPY nginx.conf /etc/nginx/nginx.conf

# Create necessary directories with correct permissions
RUN mkdir -p /app && \
    mkdir -p /var/cache/nginx && \
    mkdir -p /var/log/nginx && \
    mkdir -p /var/run && \
    chown -R nextjs:nodejs /app && \
    chown -R nextjs:nodejs /var/cache/nginx && \
    chown -R nextjs:nodejs /var/log/nginx && \
    chown -R nextjs:nodejs /var/run

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
