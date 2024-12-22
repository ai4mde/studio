# ===========================================================================
# Stage 1: Builder
# ---------------------------------------------------------------------------
FROM node:22-alpine AS builder

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /chatfront

# Copy package files
COPY package.json ./

# Install dependencies
RUN pnpm update --latest && \
    pnpm install && \
    pnpm cache clean

# Copy the rest of the code
COPY . .

# Build the application
RUN pnpm build

# ===========================================================================
# Stage 2: Final image
# ---------------------------------------------------------------------------
FROM node:22-alpine AS runner

# Set user ID
ARG USER_ID=1101

# Add build-time args
ARG NODE_ENV=production
ARG PORT=3000


# Install packages
RUN apk add --no-cache doas bash && \
    corepack enable && \
    corepack prepare pnpm@latest --activate

# Create non-root user and required directories
RUN adduser -D -u ${USER_ID} -h /chatfront -s /bin/bash cfuser && \
    mkdir /chatfront/data && \
    # Change ownership of data directory
    echo "permit nopass cfuser as root cmd chown args -R cfuser:cfuser /chatfront/data" > /etc/doas.d/doas.conf

# Set work directory
WORKDIR /chatfront
# Switch to non-root user and copy application code
USER cfuser

# Copy necessary files from builder
COPY --from=builder --chown=cfuser:cfuser /chatfront/package.json /chatfront/pnpm-lock.yaml ./

# Install only production dependencies
RUN pnpm update --latest && \
    pnpm install --prod --frozen-lockfile && \
    pnpm cache clean

COPY --from=builder --chown=cfuser:cfuser /chatfront/.next ./.next
COPY --from=builder --chown=cfuser:cfuser /chatfront/public ./public
COPY --from=builder --chown=cfuser:cfuser /chatfront/scripts ./scripts

# Use build args to set env vars
ENV NODE_ENV=${NODE_ENV}
ENV PORT=${PORT}
# Expose the port
#EXPOSE 3000

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/ || exit 1

# Start the application
ENTRYPOINT ["/bin/bash"]
CMD ["/chatfront/scripts/start.sh"]