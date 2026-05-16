# Secure Secrets Handling Rule

## Rule: Use Secure Methods for Handling Secrets and Authentication

### Purpose
Prevent exposure of sensitive credentials (API keys, tokens, passwords) in code, documentation, or command-line history.

### When This Rule Applies

**Always use secure methods when handling:**
- 🔑 API keys and tokens
- 🔐 Passwords and credentials
- 🎫 Authentication tokens (OAuth, JWT, etc.)
- 🔒 Private keys and certificates
- 💳 Database connection strings
- 🌐 Webhook secrets
- 📧 SMTP credentials

### ❌ Insecure Practices to Avoid

#### 1. Command-Line Arguments
```bash
# ❌ BAD - Visible in process list and shell history
docker run -e API_KEY="secret123" myapp
curl -H "Authorization: Bearer secret123" api.example.com
```

#### 2. Hardcoded in Code
```python
# ❌ BAD - Committed to version control
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgresql://user:password@host/db"
```

#### 3. Plain Text Files in Repo
```bash
# ❌ BAD - Committed to git
config.json:
{
  "apiKey": "secret123",
  "password": "mypassword"
}
```

#### 4. Logging Secrets
```python
# ❌ BAD - Secrets in logs
logger.info(f"Connecting with API key: {api_key}")
print(f"Token: {token}")
```

### ✅ Secure Practices

#### 1. Environment Variables (from secure sources)

**Docker/Podman with Secrets:**
```bash
# ✅ GOOD - Use secrets file
podman run --secret source=secrets.env,type=env myapp

# ✅ GOOD - Use --env-file (not visible in process list)
docker run --env-file .env.local myapp

# ✅ GOOD - Podman secrets (encrypted at rest)
echo "secret" | podman secret create api_key -
podman run --secret api_key,type=env,target=API_KEY myapp
```

**Shell Scripts:**
```bash
# ✅ GOOD - Read from secure file
if [ -f ~/.secrets/api_key ]; then
  export API_KEY=$(cat ~/.secrets/api_key)
fi

# ✅ GOOD - Use environment variable (set outside script)
: ${API_KEY:?API_KEY environment variable is required}
```

#### 2. Configuration Files (Excluded from Git)

**Create secure config:**
```bash
# ✅ GOOD - Secure permissions
cat > .env.local << 'EOF'
API_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host/db
EOF
chmod 600 .env.local
```

**Add to .gitignore:**
```gitignore
# ✅ GOOD - Never commit secrets
.env.local
secrets.env
*.key
*.pem
config/credentials.json
```

#### 3. Secret Management Systems

**GitHub Actions:**
```yaml
# ✅ GOOD - Use GitHub Secrets
env:
  API_KEY: ${{ secrets.API_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

**Kubernetes:**
```yaml
# ✅ GOOD - Use Kubernetes Secrets
env:
  - name: API_KEY
    valueFrom:
      secretKeyRef:
        name: api-credentials
        key: api-key
```

**HashiCorp Vault:**
```bash
# ✅ GOOD - Fetch from Vault
export API_KEY=$(vault kv get -field=api_key secret/myapp)
```

**AWS Secrets Manager:**
```python
# ✅ GOOD - Fetch from AWS
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='myapp/api-key')
API_KEY = secret['SecretString']
```

#### 4. Code Best Practices

**Python:**
```python
# ✅ GOOD - Load from environment
import os
from dotenv import load_dotenv

load_dotenv('.env.local')  # Load from secure file
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")
```

**Shell:**
```bash
# ✅ GOOD - Check for required secrets
: ${API_KEY:?API_KEY must be set}
: ${DATABASE_URL:?DATABASE_URL must be set}

# ✅ GOOD - Use secrets without exposing
curl -H "Authorization: Bearer ${API_KEY}" api.example.com
```

#### 5. Logging Best Practices

**Mask Secrets in Logs:**
```python
# ✅ GOOD - Mask sensitive data
import logging

def mask_secret(secret: str) -> str:
    """Mask secret for logging"""
    if not secret or len(secret) < 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"

logger.info(f"Using API key: {mask_secret(api_key)}")
# Output: "Using API key: sk-1...def9"
```

**GitHub Actions - Automatic Masking:**
```yaml
# ✅ GOOD - GitHub automatically masks secrets in logs
- name: Use secret
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: |
    echo "API Key is set"  # Don't echo the actual value
    # GitHub will mask $API_KEY if accidentally printed
```

### Security Checklist

Before committing or deploying:

- [ ] No secrets in code files
- [ ] No secrets in commit history
- [ ] Secrets files in `.gitignore`
- [ ] Secure file permissions (600 or 400)
- [ ] Secrets loaded from environment or secret manager
- [ ] Secrets masked in logs
- [ ] No secrets in command-line arguments
- [ ] No secrets in error messages
- [ ] Secrets rotated regularly
- [ ] Access to secrets is audited

### File Permissions

**Secure secrets files:**
```bash
# ✅ GOOD - Owner read/write only
chmod 600 .env.local
chmod 600 ~/.secrets/api_key

# ✅ GOOD - Owner read only (even more secure)
chmod 400 production.key
```

### Documentation Best Practices

**In README or docs:**
```markdown
# ✅ GOOD - Show structure, not actual secrets
## Configuration

Create `.env.local` with:
```
API_KEY=your-api-key-here
DATABASE_URL=postgresql://user:pass@host/db
```

Get your API key from: https://example.com/api-keys
```

**Example files:**
```bash
# ✅ GOOD - Provide template
cp .env.example .env.local
# Edit .env.local with your actual secrets
```

### Integration Examples

#### GitHub API
```python
# ✅ GOOD
import os
from github import Github

token = os.getenv('GITHUB_TOKEN')
if not token:
    raise ValueError("GITHUB_TOKEN required")
g = Github(token)
```

#### AWS
```python
# ✅ GOOD - Use IAM roles or AWS credentials file
import boto3
# Credentials from ~/.aws/credentials or IAM role
s3 = boto3.client('s3')
```

#### Database
```python
# ✅ GOOD
import os
from sqlalchemy import create_engine

db_url = os.getenv('DATABASE_URL')
if not db_url:
    raise ValueError("DATABASE_URL required")
engine = create_engine(db_url)
```

### Emergency Response

**If secrets are exposed:**

1. **Immediately revoke** the exposed credentials
2. **Rotate** to new credentials
3. **Audit** where the secret was used
4. **Remove** from git history if committed:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret" \
     --prune-empty --tag-name-filter cat -- --all
   ```
5. **Force push** (if safe to do so)
6. **Notify** affected parties

### Related Rules

- See `verify-before-assuming.md` - For checking file locations
- See `todo-management.md` - For documenting missing secrets

---

**Rule Status**: Active  
**Last Updated**: 2026-05-07  
**Enforcement**: Automatic via Bob AI Assistant  
**Priority**: Critical (security)