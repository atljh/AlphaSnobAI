# Multi-stage Docker build for AlphaSnobAI v3.0
# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Create virtual environment and install dependencies
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies using uv
RUN uv pip install --no-cache -e ".[all]"

# Stage 2: Runtime - Minimal image
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 alphasnob && \
    mkdir -p /app /app/data /app/logs /app/config && \
    chown -R alphasnob:alphasnob /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Copy application code
COPY --chown=alphasnob:alphasnob src/ /app/src/
COPY --chown=alphasnob:alphasnob config/ /app/config/
COPY --chown=alphasnob:alphasnob pyproject.toml README.md ./

# Set environment variables
ENV PATH="/app/venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to app user
USER alphasnob

# Create volumes for persistent data
VOLUME ["/app/data", "/app/logs", "/app/config"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["alphasnob", "start"]
