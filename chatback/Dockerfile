# ===========================================================================
# Stage 1: Builder
# ---------------------------------------------------------------------------
FROM python:3.13-alpine3.21 AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.5 \
    PATH="/opt/poetry/bin:$PATH" \
    CUDA_VISIBLE_DEVICES="" \
    TORCH_CUDA_ARCH_LIST="None" \
    DISABLE_CUDA="1"

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    postgresql-dev \
    postgresql-client \
    bash \
    git \
    curl \
    make \
    libgcc \
    libstdc++ \
    argon2-libs \
    linux-headers

# Install poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - && \
    chmod a+x /opt/poetry/bin/poetry

# Set work directory
WORKDIR /chatback

# Copy only pyproject.toml first
COPY pyproject.toml ./

# Generate poetry.lock file and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry lock \
    && poetry update \
    && poetry install --only main

# Copy application code
#COPY . .

# Build any additional packages if needed
#RUN poetry build || true

# ===========================================================================
# Stage 2: Final image
# ---------------------------------------------------------------------------    
FROM python:3.13-alpine3.21

# Set user ID
ARG USER_ID=1101  # Default value if not provided

# Install runtime dependencies
RUN apk add --no-cache \
    libpq \
    libffi \
    openssl \
    postgresql-client \
    bash \
    argon2-libs \
    libgcc \
    libstdc++ \
    doas

# Change ownership of data directory
#RUN echo "permit nopass cbuser as root cmd chown args -R cbuser:cbuser /chatback/data" > /etc/doas.d/doas.conf

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /opt/poetry/bin/ /usr/local/bin/

# Create non-root user and required directories
RUN adduser -D -u ${USER_ID} -s /bin/bash cbuser && \
    #mkdir /chatback/data && \
    # Change ownership of data directory
    echo "permit nopass cbuser as root cmd chown args -R cbuser:cbuser /chatback/data" > /etc/doas.d/doas.conf

# Set work directory
WORKDIR /chatback

# Switch to non-root user and copy application code
USER cbuser
# During development, the chatback code is mounted from the host
#COPY --chown=cbuser:cbuser . .

# Expose port
EXPOSE 8000

# Start the application using the start script
ENTRYPOINT ["/bin/bash"]
CMD ["/chatback/scripts/start.sh"]