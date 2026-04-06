# VoiceForge AI - Optimized Dockerfile

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements-demo.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .
COPY .env.demo .env

# Create necessary directories with proper permissions
RUN mkdir -p uploads outputs static && \
    chmod 755 uploads outputs static && \
    touch voiceforge.db && \
    chmod 666 voiceforge.db

# Create non-root user for security
RUN useradd -m -u 1000 voiceforge && \
    chown -R voiceforge:voiceforge /app && \
    chmod 755 /app

# Switch to non-root user
USER voiceforge

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEMO_MODE=true
ENV MOCK_API_CALLS=true
ENV SKIP_EXTERNAL_APIS=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
