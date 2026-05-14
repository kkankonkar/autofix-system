# Bob CLI Docker Deployment Guide

Based on the code-review-workflow implementation, here's how to run Bob CLI in Docker containers for the AutoFix System.

## Key Discovery

The code-review-workflow successfully runs Bob CLI in Docker by:
1. Installing Node.js 22.x (Bob CLI requirement)
2. Installing Bob CLI using official installation script
3. Providing `BOBSHELL_API_KEY` environment variable

## Updated Dockerfile

```dockerfile
# AutoFix System - Docker Image with Bob CLI Support
FROM python:3.11-slim

# Set metadata
LABEL maintainer="AutoFix Team"
LABEL description="AutoFix System - AI-powered automated code fixes with Bob CLI"
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
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY docs/ ./docs/

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create directory for temporary repositories
RUN mkdir -p /tmp/autofix-system-repos

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environment Variables

```bash
# Required for Bob CLI
BOBSHELL_API_KEY=your_bob_api_key_here

# Required for GitHub
GITHUB_TOKEN=your_github_token_here

# Optional: AI Agent Selection
AI_AGENT_PRIMARY=bob_cli  # or openai
AI_AGENT_FALLBACK=openai

# Optional: OpenAI (if using as fallback)
OPENAI_API_KEY=your_openai_key_here
```

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  autofix-system:
    build: .
    ports:
      - "8000:8000"
    environment:
      # Bob CLI Configuration
      - BOBSHELL_API_KEY=${BOBSHELL_API_KEY}
      - AI_AGENT_PRIMARY=bob_cli
      - BOB_CLI_COMMAND=bob
      
      # GitHub Configuration
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      
      # Optional: OpenAI Fallback
      - AI_AGENT_FALLBACK=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/app/logs
      - /tmp/autofix-system-repos:/tmp/autofix-system-repos
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Building and Running

### Build the Image

```bash
docker build -t autofix-system:latest .
```

### Run with Environment Variables

```bash
docker run -d \
  --name autofix-system \
  -p 8000:8000 \
  -e BOBSHELL_API_KEY="your_bob_api_key" \
  -e GITHUB_TOKEN="your_github_token" \
  -e AI_AGENT_PRIMARY="bob_cli" \
  autofix-system:latest
```

### Run with Docker Compose

```bash
# Create .env file
cat > .env << 'EOF'
BOBSHELL_API_KEY=your_bob_api_key_here
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_key_here
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Cloud Deployment with Bob CLI

### AWS ECS with Bob CLI

**Task Definition:**
```json
{
  "family": "autofix-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "autofix-api",
      "image": "your-registry/autofix-system:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AI_AGENT_PRIMARY",
          "value": "bob_cli"
        },
        {
          "name": "BOB_CLI_COMMAND",
          "value": "bob"
        }
      ],
      "secrets": [
        {
          "name": "BOBSHELL_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:bobshell-api-key"
        },
        {
          "name": "GITHUB_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:github-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/autofix-system",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### GCP Cloud Run with Bob CLI

```bash
# Build and push
docker build -t gcr.io/PROJECT_ID/autofix-system .
docker push gcr.io/PROJECT_ID/autofix-system

# Deploy with Bob CLI support
gcloud run deploy autofix-system \
  --image gcr.io/PROJECT_ID/autofix-system \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AI_AGENT_PRIMARY=bob_cli,BOB_CLI_COMMAND=bob \
  --set-secrets BOBSHELL_API_KEY=bobshell-api-key:latest \
  --set-secrets GITHUB_TOKEN=github-token:latest \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

### Kubernetes with Bob CLI

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: autofix-secrets
type: Opaque
stringData:
  bobshell-api-key: "your_bob_api_key"
  github-token: "your_github_token"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autofix-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: autofix-system
  template:
    metadata:
      labels:
        app: autofix-system
    spec:
      containers:
      - name: autofix-api
        image: your-registry/autofix-system:latest
        ports:
        - containerPort: 8000
        env:
        - name: AI_AGENT_PRIMARY
          value: "bob_cli"
        - name: BOB_CLI_COMMAND
          value: "bob"
        - name: BOBSHELL_API_KEY
          valueFrom:
            secretKeyRef:
              name: autofix-secrets
              key: bobshell-api-key
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: autofix-secrets
              key: github-token
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: autofix-service
spec:
  selector:
    app: autofix-system
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Verifying Bob CLI Installation

### Check Bob CLI in Container

```bash
# Enter running container
docker exec -it autofix-system bash

# Check Bob CLI version
bob --version

# Test Bob CLI
bob ask "What is Python?"

# Check environment variables
env | grep BOB
```

### Test Bob CLI Integration

```bash
# Test API endpoint
curl http://localhost:8000/health

# Upload a test log
curl -X POST "http://localhost:8000/api/v1/logs/ingest" \
  -F "repository_url=https://github.com/your-org/your-repo" \
  -F "log_file=@test_error.log"

# Check logs for Bob CLI usage
docker logs autofix-system | grep -i bob
```

## Troubleshooting

### Bob CLI Not Found

**Error:** `bob: command not found`

**Solution:**
```bash
# Rebuild image with Bob CLI installation
docker build --no-cache -t autofix-system:latest .

# Verify Bob CLI is installed
docker run --rm autofix-system:latest bob --version
```

### Bob CLI API Key Issues

**Error:** `BOBSHELL_API_KEY not set`

**Solution:**
```bash
# Check environment variable is set
docker exec autofix-system env | grep BOBSHELL

# Restart with correct key
docker run -e BOBSHELL_API_KEY="your_key" autofix-system:latest
```

### Node.js Version Issues

**Error:** `Node.js version incompatible`

**Solution:**
```dockerfile
# Ensure Node.js 22.x is installed
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs
```

## Performance Considerations

### Resource Requirements

**Minimum:**
- CPU: 1 vCPU
- Memory: 2 GB
- Disk: 10 GB

**Recommended:**
- CPU: 2 vCPU
- Memory: 4 GB
- Disk: 20 GB

### Scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: autofix-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: autofix-system
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Cost Optimization

### With Bob CLI

**AWS ECS Fargate:**
- 2 vCPU × 4GB RAM × 730 hours = ~$140/month
- Bob CLI API usage: Variable (pay per request)

**GCP Cloud Run:**
- 2 vCPU × 4GB RAM × variable usage = ~$80-120/month
- Bob CLI API usage: Variable

**Recommendation:** Use GCP Cloud Run for cost-effectiveness with Bob CLI

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use secrets management** (AWS Secrets Manager, GCP Secret Manager, etc.)
3. **Rotate keys regularly** (every 90 days)
4. **Use least privilege** IAM roles
5. **Enable audit logging** for API key usage
6. **Monitor Bob CLI usage** for anomalies

## Comparison: Bob CLI vs OpenAI

| Feature | Bob CLI | OpenAI |
|---------|---------|--------|
| **Installation** | Requires Node.js + Bob CLI | Python package only |
| **Container Size** | ~800 MB | ~400 MB |
| **Startup Time** | ~10 seconds | ~2 seconds |
| **API Cost** | Variable (IBM pricing) | Variable (OpenAI pricing) |
| **Reliability** | Depends on Bob service | Depends on OpenAI service |
| **Features** | IBM-specific features | General purpose |

## Recommended Architecture

### Production Setup

```
┌─────────────────────────────────────────────────────────┐
│                    Cloud Platform                        │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  AutoFix System Container                       │   │
│  │  - Python 3.11                                  │   │
│  │  - Node.js 22.x                                 │   │
│  │  - Bob CLI installed                            │   │
│  │  - FastAPI application                          │   │
│  │                                                  │   │
│  │  Environment:                                   │   │
│  │  - BOBSHELL_API_KEY (from secrets)             │   │
│  │  - GITHUB_TOKEN (from secrets)                  │   │
│  │  - AI_AGENT_PRIMARY=bob_cli                     │   │
│  │  - AI_AGENT_FALLBACK=openai                     │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Build Docker image** with Bob CLI support
2. **Test locally** with docker-compose
3. **Deploy to staging** environment
4. **Monitor Bob CLI usage** and costs
5. **Scale to production** based on load

## Related Documentation

- [Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)
- [Multi-File Fixes](MULTI_FILE_FIXES_AND_PATH_NORMALIZATION.md)
- [Main README](../README.md)

---

**Key Takeaway:** Bob CLI can run in Docker containers by installing Node.js 22.x and using the official Bob CLI installation script. Provide `BOBSHELL_API_KEY` as an environment variable for authentication.