# LightStock - Inventory Management System
# Multi-stage Docker build for production

FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 ims && \
    mkdir -p /app/instance /app/logs && \
    chown -R ims:ims /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=ims:ims /root/.local /home/ims/.local

# Copy application code
COPY --chown=ims:ims . .

# Set environment variables
ENV PATH=/home/ims/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production

# Expose port
EXPOSE 8000

# Switch to non-root user
USER ims

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/').raise_for_status()" || exit 1

# Run the application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
