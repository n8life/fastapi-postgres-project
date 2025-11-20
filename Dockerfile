FROM python:3.11-slim

# Use the existing nobody user (UID 65534) for security
# Create a home directory for nobody user and set permissions
RUN mkdir -p /home/nobody && chown nobody:nogroup /home/nobody

# Set working directory and change ownership
WORKDIR /app
RUN chown nobody:nogroup /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv as root, then switch to non-root user
RUN pip install --no-cache-dir uv

# Copy project files with nobody user ownership
COPY --chown=nobody:nogroup pyproject.toml uv.lock ./

# Set home directory and switch to nobody user before installing dependencies
ENV HOME=/home/nobody
USER nobody

# Install dependencies
RUN uv sync --frozen

# Copy source code with nobody user ownership
COPY --chown=nobody:nogroup . .

# Add volumes for writable directories to support read-only filesystem
VOLUME ["/tmp", "/var/tmp"]

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uv", "run", "python", "-c", "import uvicorn; import os; uvicorn.run('app.main:app', host=os.getenv('UVICORN_HOST', '0.0.0.0'), port=8000)"]
