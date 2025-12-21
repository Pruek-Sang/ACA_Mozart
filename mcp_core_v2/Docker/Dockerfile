# ═══════════════════════════════════════════════════════════════════
# MCP Core v2 Dockerfile - Electrical Design Calculation Engine
# ═══════════════════════════════════════════════════════════════════
# Architecture: Multi-stage build (Optimized for production)
# Base: Python 3.12 Slim
# Standard: Thai EIT/TIS (230V single-phase, 400V three-phase)
# ═══════════════════════════════════════════════════════════════════

FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install FastAPI/uvicorn for API
RUN pip install --no-cache-dir fastapi uvicorn[standard]

# ═══════════════════════════════════════════════════════════════════
# Production Stage
# ═══════════════════════════════════════════════════════════════════
FROM python:3.12-slim

# Metadata
LABEL maintainer="Aura - The Goddess of Code"
LABEL description="MCP Core v2 - Electrical Design Calculation Engine (NEC/Thai EIT)"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY api.py .
COPY pipeline.py .
COPY config.py .
COPY exceptions.py .
COPY integration.py .

# Copy modules
COPY models/ ./models/
COPY core/ ./core/
COPY dal/ ./dal/
COPY db/ ./db/
COPY cad/ ./cad/
# 🆕 CRITICAL: Context Injectors (Derating, kA Rating, N-G Link)
# Without this, Site Context features won't work!
COPY context/ ./context/
# 🆕 Catalog data (prices.csv for BOQ pricing)
COPY catalog/ ./catalog/

# Create directories for logs and output
RUN mkdir -p logs output

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5001/health').getcode() == 200 else 1)" || exit 1

# Run the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5001"]
