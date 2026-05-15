# CodeMedic AutoFix System - Docker Image with Bob CLI Support
FROM python:3.11-slim

# Set metadata
LABEL maintainer="CodeMedic Team"
LABEL description="CodeMedic AutoFix System - AI-powered automated code fixes with Bob CLI"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    git \
    curl \
    ca-certificates \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22.x (required by Bob CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    node --version && \
    npm --version

# Install Bob CLI (IBM AI Assistant)
# Official installation script handles architecture detection automatically
RUN curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash && \
    bob --version

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
# Use production requirements (no testing/dev dependencies)
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY src/ ./src/
COPY docs/ ./docs/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY *.md ./
COPY *.sh ./

# Make shell scripts executable
RUN chmod +x *.sh 2>/dev/null || true

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create directory for temporary repositories
RUN mkdir -p /tmp/autofix-system-repos && \
    chmod 777 /tmp/autofix-system-repos

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Made with ❤️ by CodeMedic Team