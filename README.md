# AutoFix System - Automated Code Fix with Bob AI Agent

An intelligent system that automatically analyzes application logs, identifies code errors, generates fixes using Bob AI agent, and creates pull requests in GitHub repositories.

## 🎯 Features

- **Automated Log Monitoring** - Ingests logs from multiple applications
- **AI-Powered Analysis** - Uses Bob CLI as the primary execution path to analyze errors
- **Smart Fix Generation** - Generates context-aware code fixes through Bob CLI workflows
- **Automatic PR Creation** - Creates pull requests with detailed explanations
- **Generic Design** - Works with any application and GitHub repository
- **Scalable Architecture** - Queue-based processing for high throughput

## 🏗️ Architecture

```
Applications → Log Ingestion → Queue → Error Analyzer (Bob AI)
                                          ↓
GitHub ← PR Creator ← Fix Generator ← Repo Manager
```

### Components:

1. **Log Ingestion Service** - Collects logs via webhook/API
2. **Error Analyzer** - Analyzes logs using Bob AI
3. **Repository Manager** - Clones and manages source repositories
4. **Fix Generator** - Generates code fixes using Bob AI
5. **PR Creator** - Creates and manages pull requests

## 📦 Project Structure

```
autofix-system/
├── src/
│   ├── ai_agent/          # Bob + OpenAI integration
│   ├── ingestion/         # Log ingestion service
│   ├── analyzer/          # Error analysis
│   ├── repo_manager/      # Repository management
│   ├── fix_generator/     # Fix generation
│   ├── pr_creator/        # PR creation
│   ├── models/            # Data models
│   └── utils/             # Utilities
├── config/                # Configuration files
├── tests/                 # Test suite
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker setup
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Redis (for queue)
- PostgreSQL (for persistence)
- GitHub App credentials
- Bob CLI installed and available in PATH
- OpenAI API key (optional fallback)

### Installation

1. **Clone the repository:**
   ```bash
   cd /Users/kalpeshkankonkar/Downloads/autofix-system
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your credentials
   ```

5. **Start services:**
   ```bash
   # Start Redis
   redis-server

   # Start PostgreSQL
   # (or use Docker: docker-compose up -d postgres redis)

   # Run migrations
   alembic upgrade head

   # Start the application
   python -m src.main
   ```

## ⚙️ Configuration

### Environment Variables

Create `config/.env`:

```bash
# AI Configuration
AI_AGENT_PRIMARY=bob_cli
AI_AGENT_FALLBACK=openai
BOB_CLI_COMMAND=bob
BOB_MODE=ask
OPENAI_API_KEY=your_openai_api_key

# GitHub Configuration
GITHUB_APP_ID=your_github_app_id
GITHUB_PRIVATE_KEY_PATH=/path/to/private-key.pem
GITHUB_INSTALLATION_ID=your_installation_id

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/autofix

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=5
```

### Application Configuration

Create `config/applications.yaml`:

```yaml
applications:
  - name: "my-web-app"
    log_source:
      type: "webhook"
      endpoint: "/logs/my-web-app"
    repository:
      url: "https://github.com/org/my-web-app"
      branch: "main"
      auto_merge: false
    
  - name: "api-service"
    log_source:
      type: "file"
      path: "/var/log/api-service/*.log"
    repository:
      url: "https://github.com/org/api-service"
      branch: "develop"
      auto_merge: false
```

## 📡 API Endpoints

### Log Ingestion

**POST** `/api/v1/logs/ingest`

Submit a repository URL and an entire log file using multipart form-data:

```bash
curl -X POST http://localhost:8000/api/v1/logs/ingest \
  -F "repository_url=https://github.com/org/my-web-app" \
  -F "log_file=@/absolute/path/to/application.log"
```

The server extracts:
- repository URL from the form field
- filename from the uploaded file
- first non-empty log line as the summary message
- full uploaded content for analysis context

### Status Check

**GET** `/api/v1/status`

Check system status:

```bash
curl http://localhost:8000/api/v1/status
```

### Job Status

**GET** `/api/v1/jobs/{job_id}`

Check processing status:

```bash
curl http://localhost:8000/api/v1/jobs/job-123456
```

## 🤖 Bob AI Integration

### Using Bob CLI (Primary)

The system integrates with Bob through the installed CLI, matching the non-interactive prompt execution pattern used by review automation workflows:

```python
from src.ai_agent import BobAgent

agent = BobAgent()
analysis = await agent.analyze_error(log_entry, code_context)
```

### Using OpenAI (Fallback)

If Bob is unavailable, the system automatically falls back to OpenAI:

```python
from src.ai_agent import OpenAIAgent

agent = OpenAIAgent(api_key="your-key")
analysis = await agent.analyze_error(log_entry, code_context)
```

### Hybrid Approach (Recommended)

```python
from src.ai_agent import HybridAgent

agent = HybridAgent()
# Tries Bob first, falls back to OpenAI
analysis = await agent.analyze_error(log_entry, code_context)
```

## 🔄 Workflow

### 1. Log Submission

Application sends error log to ingestion endpoint:

```
POST /api/v1/logs/ingest
```

### 2. Queue Processing

Log is added to Redis queue for async processing.

### 3. Error Analysis

Bob AI analyzes the error and extracts:
- Error type
- File location
- Root cause
- Fixability assessment

### 4. Repository Preparation

System clones the repository and locates the problematic code.

### 5. Fix Generation

Bob AI generates a fix based on:
- Error details
- Code context
- Repository structure

### 6. PR Creation

System creates a pull request with:
- Fixed code
- Detailed explanation
- Link to original error log
- Suggested reviewers

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/test_analyzer.py
```

### Integration Tests

```bash
# Requires test repository
pytest tests/integration/
```

## 📊 Monitoring

### Metrics

The system exposes Prometheus metrics at `/metrics`:

- `autofix_logs_ingested_total` - Total logs ingested
- `autofix_errors_analyzed_total` - Total errors analyzed
- `autofix_prs_created_total` - Total PRs created
- `autofix_processing_duration_seconds` - Processing time

### Logs

Structured JSON logs are written to stdout:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "PR created successfully",
  "pr_number": 123,
  "repository": "org/my-web-app"
}
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

See `docs/DEPLOYMENT.md` for Kubernetes deployment guide.

## 🔐 Security

### GitHub App Permissions

Required permissions:
- **Contents**: Read & Write (for creating branches and commits)
- **Pull Requests**: Read & Write (for creating PRs)
- **Issues**: Read & Write (for linking issues)

### API Authentication

Use API keys for log ingestion:

```bash
curl -X POST http://localhost:8000/api/v1/logs/ingest \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '...'
```

## 📈 Scalability

### Horizontal Scaling

Run multiple worker instances:

```bash
# Worker 1
python -m src.worker --id worker-1

# Worker 2
python -m src.worker --id worker-2
```

### Load Balancing

Use nginx or cloud load balancer for API endpoints.

## 🛠️ Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linters
black src/
flake8 src/
mypy src/
```

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit PR

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - Detailed system architecture
- [API Reference](docs/API.md) - Complete API documentation
- [Deployment](docs/DEPLOYMENT.md) - Deployment guide
- [Contributing](docs/CONTRIBUTING.md) - Contribution guidelines

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md).

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@autofix-system.com

## 🎯 Roadmap

- [x] Core log ingestion
- [x] Bob AI integration
- [x] GitHub PR creation
- [ ] Dashboard UI
- [ ] GitLab support
- [ ] Bitbucket support
- [ ] Slack notifications
- [ ] Auto-merge for low-risk fixes
- [ ] ML-based fix validation

## 📊 Status

**Current Version**: 1.0.0-beta  
**Status**: Production Ready  
**Last Updated**: 2024-01-15

---

Built with ❤️ using Bob AI Agent