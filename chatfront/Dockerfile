# ===========================================================================
# Stage 1: Builder
# ---------------------------------------------------------------------------
FROM node:22-alpine AS builder

# Set working directory
WORKDIR /chatfront

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build application
RUN pnpm run build

# ===========================================================================
# Stage 2: Final image
# ---------------------------------------------------------------------------
FROM node:22-alpine AS runner

# Set working directory
WORKDIR /chatfront

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install production dependencies only
RUN pnpm install --prod --frozen-lockfile

# Copy built application from builder
COPY --from=builder /chatfront/build ./build
COPY --from=builder /chatfront/public ./public

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Expose port
EXPOSE 3000

# Start the application
CMD ["pnpm", "start"] 