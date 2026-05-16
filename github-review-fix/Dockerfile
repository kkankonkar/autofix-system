# Fixium Code Review Bot - Docker Image
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Fixium Team"
LABEL description="Fixium - AI-powered code review bot for GitHub Pull Requests"
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
WORKDIR /fixium

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY fixium/ ./fixium/
COPY tests/ ./tests/
COPY lib/ ./lib/
COPY prompts/ ./prompts/
COPY schema/ ./schema/
COPY config/ ./config/
COPY review_workflow.sh .
COPY submit_pr_comments.sh .
COPY implement_finding.sh .
COPY pytest.ini .

# Make shell scripts executable
RUN chmod +x /fixium/*.sh /fixium/lib/*.sh

# Set Python path
ENV PYTHONPATH=/fixium
ENV PYTHONUNBUFFERED=1

# Create directory for review outputs
RUN mkdir -p /fixium/outputs

# Set entrypoint to Python main module
ENTRYPOINT ["python", "-m", "fixium.main"]

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import fixium; print('Fixium is healthy')" || exit 1

# Made with Bob
