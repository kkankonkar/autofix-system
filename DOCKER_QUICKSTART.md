# CodeMedic AutoFix System - Docker/Podman Quick Start

## 🚀 Quick Start (3 Steps)

### 1. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
GITHUB_TOKEN=ghp_your_token_here
BOBSHELL_API_KEY=your_bob_key_here
OPENAI_API_KEY=sk_your_key_here  # Optional
```

### 2. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

### 3. Access the API

- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **OpenAPI**: http://localhost:8000/openapi.json

## 📦 Deployment Options

### Option 1: Docker Compose (Easiest)

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Docker Script

```bash
# Run the automated script
./run-docker.sh
```

### Option 3: Podman Compose

```bash
# Start
podman-compose up -d

# View logs
podman-compose logs -f

# Stop
podman-compose down
```

### Option 4: Podman Script

```bash
# Run the automated script
./run-podman.sh
```

### Option 5: Manual Docker Run

```bash
# Build image
docker build -t codemedic/autofix-system:latest .

# Run container
docker run -d \
  --name autofix-system \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs" \
  codemedic/autofix-system:latest
```

### Option 6: Manual Podman Run

```bash
# Build image
podman build -t codemedic/autofix-system:latest .

# Run container
podman run -d \
  --name autofix-system \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs:Z" \
  codemedic/autofix-system:latest
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` |
| `BOBSHELL_API_KEY` | Bob CLI API Key | `your_bob_key` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (fallback) |
| `AI_AGENT_PRIMARY` | `bob_cli` | Primary AI agent |
| `AI_AGENT_FALLBACK` | `openai` | Fallback AI agent |
| `BOB_CLI_COMMAND` | `bob` | Bob CLI command |
| `LOG_LEVEL` | `INFO` | Logging level |

## 📊 Container Management

### View Logs

```bash
# Docker
docker logs -f autofix-system

# Podman
podman logs -f autofix-system

# Docker Compose
docker-compose logs -f
```

### Check Status

```bash
# Docker
docker ps --filter name=autofix-system

# Podman
podman ps --filter name=autofix-system

# Docker Compose
docker-compose ps
```

### Restart Container

```bash
# Docker
docker restart autofix-system

# Podman
podman restart autofix-system

# Docker Compose
docker-compose restart
```

### Stop Container

```bash
# Docker
docker stop autofix-system

# Podman
podman stop autofix-system

# Docker Compose
docker-compose stop
```

### Remove Container

```bash
# Docker
docker rm -f autofix-system

# Podman
podman rm -f autofix-system

# Docker Compose
docker-compose down
```

### Enter Container Shell

```bash
# Docker
docker exec -it autofix-system bash

# Podman
podman exec -it autofix-system bash
```

## 🧪 Testing the Deployment

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "logs_processed": 0,
  "analyses_completed": 0,
  "fixes_generated": 0,
  "pull_requests_created": 0
}
```

### 2. Upload Test Log

```bash
# Create test log
cat > test_error.log << 'EOF'
Traceback (most recent call last):
  File "/app/consumer/billing_consumer.py", line 45, in process
    result = data.user
TypeError: 'NoneType' object has no attribute 'user'
EOF

# Upload to API
curl -X POST "http://localhost:8000/api/v1/logs/ingest" \
  -F "repository_url=https://github.com/your-org/your-repo" \
  -F "log_file=@test_error.log"
```

### 3. Check Bob CLI

```bash
# Enter container
docker exec -it autofix-system bash

# Check Bob CLI version
bob --version

# Test Bob CLI
bob ask "What is Python?"
```

## 🐛 Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs autofix-system
```

**Common issues:**
- Missing environment variables
- Port 8000 already in use
- Invalid API keys

### Bob CLI Not Working

**Check Bob CLI installation:**
```bash
docker exec -it autofix-system bob --version
```

**Check API key:**
```bash
docker exec -it autofix-system env | grep BOBSHELL
```

**Solution:**
- Verify `BOBSHELL_API_KEY` in `.env`
- Rebuild image: `docker-compose build --no-cache`

### Port Already in Use

**Find process using port 8000:**
```bash
lsof -i :8000
```

**Kill process or use different port:**
```bash
# Edit docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Permission Denied (Podman)

**Add `:Z` to volume mounts:**
```bash
-v "$(pwd)/logs:/app/logs:Z"
```

### Image Build Fails

**Clear cache and rebuild:**
```bash
# Docker
docker build --no-cache -t codemedic/autofix-system:latest .

# Podman
podman build --no-cache -t codemedic/autofix-system:latest .
```

## 📈 Resource Requirements

### Minimum

- **CPU**: 1 vCPU
- **Memory**: 2 GB
- **Disk**: 10 GB

### Recommended

- **CPU**: 2 vCPU
- **Memory**: 4 GB
- **Disk**: 20 GB

### Adjust Resources

**Docker Compose:**
```yaml
services:
  autofix-system:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

**Docker Run:**
```bash
docker run -d \
  --cpus="2" \
  --memory="4g" \
  ...
```

## 🔐 Security Best Practices

1. **Never commit `.env` file**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use secrets management in production**
   - Docker Swarm secrets
   - Kubernetes secrets
   - Cloud provider secrets (AWS Secrets Manager, etc.)

3. **Run as non-root user** (already configured in Dockerfile)

4. **Keep images updated**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

5. **Use HTTPS in production**
   - Add reverse proxy (nginx, traefik)
   - Use Let's Encrypt for SSL

## 🌐 Production Deployment

### With Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name autofix.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### With SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d autofix.yourdomain.com
```

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml autofix
```

### Kubernetes

See [`docs/CLOUD_DEPLOYMENT_GUIDE.md`](docs/CLOUD_DEPLOYMENT_GUIDE.md) for Kubernetes deployment.

## 📚 Additional Resources

- [Main README](README.md)
- [Cloud Deployment Guide](docs/CLOUD_DEPLOYMENT_GUIDE.md)
- [Bob CLI Docker Deployment](docs/BOB_CLI_DOCKER_DEPLOYMENT.md)
- [Multi-File Fixes Guide](docs/MULTI_FILE_FIXES_AND_PATH_NORMALIZATION.md)

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker logs autofix-system`
2. Verify environment variables: `docker exec autofix-system env`
3. Test Bob CLI: `docker exec autofix-system bob --version`
4. Check health: `curl http://localhost:8000/health`

## 📝 Summary

**Quick Start:**
```bash
# 1. Setup
cp .env.example .env
# Edit .env with your keys

# 2. Run
docker-compose up -d

# 3. Test
curl http://localhost:8000/health
```

**That's it! 🎉**

---

**Made with ❤️ by CodeMedic Team**