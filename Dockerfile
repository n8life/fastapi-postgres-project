FROM python:3.11-slim

# Create a non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory and change ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv as root, then switch to non-root user
RUN pip install --no-cache-dir uv

# Copy project files and change ownership
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Switch to non-root user before installing dependencies
USER appuser

# Install dependencies
RUN uv sync --frozen

# Copy source code with proper ownership
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
