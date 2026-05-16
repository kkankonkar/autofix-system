# Container Deployment Guide

## Overview

Fixium is designed to run in containers with all configuration provided via environment variables. This allows for flexible deployment across different environments without modifying code.

## Configuration Strategy

### Environment Variables (Required)

All sensitive and environment-specific configuration must be provided via environment variables:

```bash
# Required
GITHUB_TOKEN          # GitHub personal access token
GITHUB_OWNER          # Repository owner/organization
GITHUB_REPO           # Repository name
GITHUB_REPOSITORY     # Full repo path (owner/repo)
BOBSHELL_API_KEY      # Bob Shell API key
FIXIUM_AUTHORIZED_USERS  # Comma-separated list of authorized users

# For PR review workflow
PR_NUMBER             # Pull request number
COMMENT_BODY          # Comment text that triggered the review
COMMENT_USER          # GitHub username who posted the comment
```

### Config File (Optional Defaults)

The `config/github.env` file contains only **optional default values** for non-sensitive settings:

```bash
COMMENT_PREFIX        # Comment prefix for bot messages
MAX_COMMENTS_PER_BATCH  # Batch size for API calls
RATE_LIMIT_BUFFER     # Safety buffer for rate limits
MAX_RETRIES           # Maximum retry attempts
RETRY_DELAY           # Delay between retries
```

**Important:** Never commit sensitive data (tokens, keys) to `config/github.env`!

## Docker Deployment

### Building the Image

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Bob CLI (if needed)
# RUN curl -L https://github.com/IBM/bob/releases/download/vX.X.X/bob-linux-amd64 -o /usr/local/bin/bob && \
#     chmod +x /usr/local/bin/bob

# Copy application code
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 fixium && \
    chown -R fixium:fixium /app
USER fixium

# Entry point
CMD ["python3", "-m", "fixium.main"]
```

### Running the Container

#### Basic Run

```bash
docker run \
  -e GITHUB_TOKEN="ghp_xxxxxxxxxxxx" \
  -e GITHUB_OWNER="your-org" \
  -e GITHUB_REPO="your-repo" \
  -e GITHUB_REPOSITORY="your-org/your-repo" \
  -e BOBSHELL_API_KEY="sk-xxxxxxxxxxxx" \
  -e FIXIUM_AUTHORIZED_USERS="user1,user2" \
  -e PR_NUMBER="123" \
  -e COMMENT_BODY="Fixium:review --severity high" \
  -e COMMENT_USER="user1" \
  fixium:latest
```

#### Using Environment File

```bash
# Create env file (DO NOT COMMIT!)
cat > container.env << 'EOF'
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo
GITHUB_REPOSITORY=your-org/your-repo
BOBSHELL_API_KEY=sk-xxxxxxxxxxxx
FIXIUM_AUTHORIZED_USERS=user1,user2
PR_NUMBER=123
COMMENT_BODY=Fixium:review
COMMENT_USER=user1
EOF

# Run with env file
docker run --env-file container.env fixium:latest
```

#### With Secrets Management

```bash
# Using Docker secrets
echo "ghp_xxxxxxxxxxxx" | docker secret create github_token -
echo "sk-xxxxxxxxxxxx" | docker secret create bobshell_key -

docker service create \
  --name fixium \
  --secret github_token \
  --secret bobshell_key \
  -e GITHUB_TOKEN_FILE=/run/secrets/github_token \
  -e BOBSHELL_API_KEY_FILE=/run/secrets/bobshell_key \
  -e GITHUB_OWNER="your-org" \
  -e GITHUB_REPO="your-repo" \
  fixium:latest
```

## Kubernetes Deployment

### Using ConfigMap and Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fixium-secrets
type: Opaque
stringData:
  github-token: ghp_xxxxxxxxxxxx
  bobshell-api-key: sk-xxxxxxxxxxxx
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fixium-config
data:
  GITHUB_OWNER: "your-org"
  GITHUB_REPO: "your-repo"
  GITHUB_REPOSITORY: "your-org/your-repo"
  FIXIUM_AUTHORIZED_USERS: "user1,user2,user3"
---
apiVersion: batch/v1
kind: Job
metadata:
  name: fixium-review
spec:
  template:
    spec:
      containers:
      - name: fixium
        image: fixium:latest
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: fixium-secrets
              key: github-token
        - name: BOBSHELL_API_KEY
          valueFrom:
            secretKeyRef:
              name: fixium-secrets
              key: bobshell-api-key
        envFrom:
        - configMapRef:
            name: fixium-config
        - name: PR_NUMBER
          value: "123"
        - name: COMMENT_BODY
          value: "Fixium:review"
        - name: COMMENT_USER
          value: "user1"
      restartPolicy: Never
```

### Using External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: fixium-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: fixium-secrets
  data:
  - secretKey: github-token
    remoteRef:
      key: fixium/github-token
  - secretKey: bobshell-api-key
    remoteRef:
      key: fixium/bobshell-api-key
```

## GitHub Actions Integration

The workflow automatically provides environment variables:

```yaml
# .github/workflows/fixium.yml
- name: Run Fixium Code Review
  run: python -m fixium.main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    BOBSHELL_API_KEY: ${{ secrets.BOBSHELL_API_KEY }}
    FIXIUM_AUTHORIZED_USERS: ${{ secrets.FIXIUM_AUTHORIZED_USERS }}
    GITHUB_REPOSITORY: ${{ github.repository }}
    GITHUB_OWNER: ${{ github.repository_owner }}
    GITHUB_REPO: ${{ github.event.repository.name }}
    PR_NUMBER: ${{ github.event.issue.number }}
    COMMENT_BODY: ${{ github.event.comment.body }}
    COMMENT_USER: ${{ github.event.comment.user.login }}
```

## Cloud Platform Examples

### AWS ECS

```json
{
  "family": "fixium",
  "containerDefinitions": [
    {
      "name": "fixium",
      "image": "your-registry/fixium:latest",
      "secrets": [
        {
          "name": "GITHUB_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:fixium/github-token"
        },
        {
          "name": "BOBSHELL_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:fixium/bobshell-key"
        }
      ],
      "environment": [
        {"name": "GITHUB_OWNER", "value": "your-org"},
        {"name": "GITHUB_REPO", "value": "your-repo"},
        {"name": "GITHUB_REPOSITORY", "value": "your-org/your-repo"}
      ]
    }
  ]
}
```

### Google Cloud Run

```bash
gcloud run deploy fixium \
  --image gcr.io/your-project/fixium:latest \
  --set-secrets GITHUB_TOKEN=github-token:latest,BOBSHELL_API_KEY=bobshell-key:latest \
  --set-env-vars GITHUB_OWNER=your-org,GITHUB_REPO=your-repo,GITHUB_REPOSITORY=your-org/your-repo
```

### Azure Container Instances

```bash
az container create \
  --resource-group fixium-rg \
  --name fixium \
  --image your-registry.azurecr.io/fixium:latest \
  --secure-environment-variables \
    GITHUB_TOKEN="ghp_xxxxxxxxxxxx" \
    BOBSHELL_API_KEY="sk-xxxxxxxxxxxx" \
  --environment-variables \
    GITHUB_OWNER="your-org" \
    GITHUB_REPO="your-repo" \
    GITHUB_REPOSITORY="your-org/your-repo"
```

## Security Best Practices

### 1. Never Hardcode Secrets

❌ **Bad:**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"  # In config file
```

✅ **Good:**
```bash
docker run -e GITHUB_TOKEN="$GITHUB_TOKEN" ...  # From environment
```

### 2. Use Secrets Management

- **Docker:** Docker secrets
- **Kubernetes:** Kubernetes secrets or External Secrets Operator
- **AWS:** AWS Secrets Manager or Parameter Store
- **GCP:** Google Secret Manager
- **Azure:** Azure Key Vault

### 3. Rotate Credentials Regularly

```bash
# Rotate GitHub token
# 1. Create new token
# 2. Update secret in secrets manager
# 3. Restart containers
# 4. Revoke old token
```

### 4. Principle of Least Privilege

- Use tokens with minimal required scopes
- Limit authorized users list
- Use read-only tokens where possible

### 5. Audit and Monitor

```bash
# Log environment variable names (not values!)
echo "Configuration loaded:"
echo "  GITHUB_OWNER: ${GITHUB_OWNER}"
echo "  GITHUB_REPO: ${GITHUB_REPO}"
echo "  GITHUB_TOKEN: [REDACTED]"
```

## Local Development

For local testing, use `secrets.env` (gitignored):

```bash
# Copy template
cp secrets.env.example secrets.env

# Edit with your values
vim secrets.env

# Source and run
source secrets.env
python3 -m fixium.main
```

**Never commit `secrets.env` to version control!**

## Troubleshooting

### Environment Variables Not Set

```bash
# Check if variables are set
docker run fixium:latest env | grep GITHUB

# Debug container
docker run -it --entrypoint /bin/bash fixium:latest
env | grep GITHUB
```

### Config File Override

If `config/github.env` has values, they will override environment variables. Ensure it only contains optional defaults.

### Secrets Not Loading

```bash
# Kubernetes: Check secret exists
kubectl get secret fixium-secrets -o yaml

# Docker: Check secret is mounted
docker exec container-id ls -la /run/secrets/
```

## Migration Guide

### From Hardcoded Config to Environment Variables

1. **Identify hardcoded values** in `config/github.env`
2. **Move to environment variables** in your deployment
3. **Remove from config file**
4. **Test in staging** environment
5. **Deploy to production**

### Example Migration

**Before:**
```bash
# config/github.env
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_OWNER="my-org"
```

**After:**
```bash
# config/github.env (only defaults)
export COMMENT_PREFIX="🤖 Bob Shell Review"

# Deployment (environment variables)
docker run -e GITHUB_TOKEN="$GITHUB_TOKEN" -e GITHUB_OWNER="my-org" ...
```

## Related Documentation

- [README.md](README.md) - Main documentation
- [TESTING.md](TESTING.md) - Local testing guide
- [COMMENT-TRIGGER-EXPLAINED.md](COMMENT-TRIGGER-EXPLAINED.md) - Comment system

---

**Last Updated:** 2026-05-08  
**Maintainer:** Development Team