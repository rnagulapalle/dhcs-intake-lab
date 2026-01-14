# BHT Multi-Agent API Dockerfile
# Deterministic build with security best practices

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY agents/requirements.txt /build/agents-requirements.txt

# Install Python dependencies to a prefix
RUN pip install --no-cache-dir --prefix=/install -r agents-requirements.txt

# -------------------------------------------------------------------
# Production image
# -------------------------------------------------------------------
FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd --gid 1000 bht && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home bht

WORKDIR /app

# Install runtime dependencies only (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=bht:bht agents/ /app/agents/
COPY --chown=bht:bht api/ /app/api/
COPY --chown=bht:bht platform/ /app/platform/
COPY --chown=bht:bht scripts/ /app/scripts/

# Create data directories with correct permissions
# Note: /app/logs must be writable for file-based audit logging
RUN mkdir -p /app/data /app/chroma_data /app/logs && \
    chown -R bht:bht /app && \
    chmod 777 /app/logs

# Copy data if exists (optional)
COPY --chown=bht:bht data/ /app/data/

# Switch to non-root user
USER bht

# Environment defaults (secrets via runtime env, not build args)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BHT_PLATFORM_ENABLED=true \
    BHT_AUDIT_SINK=stdout \
    BHT_JSON_LOGS_ENABLED=true \
    BHT_AUDIT_LOG_PROMPTS=false \
    BHT_AUDIT_LOG_RESPONSES=false

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the API with production settings
CMD ["python", "-m", "uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--timeout-keep-alive", "75", \
     "--limit-concurrency", "100"]
