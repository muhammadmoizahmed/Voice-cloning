# VoiceForge AI - Optimized Dockerfile for Render

FROM python:3.9-slim

# Install system dependencies first (as root)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements from build context to /app
COPY requirements-demo.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code to /app
COPY backend/ /app/

# Copy environment file
COPY .env.demo /app/.env

# Create necessary directories
RUN mkdir -p /app/uploads /app/outputs /app/static && \
    chmod 755 /app/uploads /app/outputs /app/static

# Create database file with proper permissions
RUN touch /app/voiceforge.db && chmod 666 /app/voiceforge.db

# Create non-root user
RUN useradd -m -u 1000 voiceforge

# Change ownership of app directory
RUN chown -R voiceforge:voiceforge /app

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
