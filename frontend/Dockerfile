FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 streamlituser && chown -R streamlituser:streamlituser /app
USER streamlituser

# Install Python dependencies
COPY --chown=streamlituser:streamlituser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Add user's pip bin to PATH
ENV PATH="/home/streamlituser/.local/bin:${PATH}"

# Copy application code
COPY --chown=streamlituser:streamlituser . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Configure Streamlit
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run the application
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]