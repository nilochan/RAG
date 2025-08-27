FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 raguser && chown -R raguser:raguser /app
USER raguser

# Install Python dependencies
COPY --chown=raguser:raguser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Add user's pip bin to PATH
ENV PATH="/home/raguser/.local/bin:${PATH}"

# Copy application code
COPY --chown=raguser:raguser main.py .
COPY --chown=raguser:raguser src/ ./src/

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]