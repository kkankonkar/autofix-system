# AutoFix System - Automated Code Fix with AI

An intelligent system that automatically analyzes application logs, identifies code errors, generates fixes using AI (Bob CLI or OpenAI), and creates pull requests in GitHub repositories.

## 🎯 Features

- **Automated Log Analysis** - Upload log files and get instant error analysis
- **Multi-Error Processing** - Extracts and fixes 2-3 errors from a single log file ⭐ NEW
- **AI-Powered Fix Generation** - Uses Bob CLI (primary) or OpenAI (fallback) to generate fixes
- **Path Normalization** - Handles absolute paths from containers (e.g., `/app/file.py` → `src/file.py`)
- **Multi-File Fixes** - Supports fixing multiple files in a single PR
- **Combined PR Creation** - All fixes merged into one comprehensive pull request
- **Safe Code Replacement** - Line-based replacement preserves unrelated code
- **Automatic PR Creation** - Creates pull requests with detailed explanations
- **Generic Design** - Works with any application and GitHub repository

## 🏗️ Architecture

```
Log Upload → Error Analysis (AI) → Fix Generation (AI) → PR Creation
                                          ↓
                              Path Normalization + Multi-File Support
```

## 📦 Project Structure

```
autofix-system/
├── src/
│   ├── ai_agent/          # Bob CLI + OpenAI integration
│   ├── repo_manager/      # Repository management & path normalization
│   ├── fix_generator/     # Fix generation with multi-file support
│   ├── pr_creator/        # PR creation
│   ├── models/            # Data models (FixProposal, FileChange, etc.)
│   └── main.py            # FastAPI application
├── docs/                  # Documentation
│   ├── MULTI_ERROR_PROCESSING.md  # NEW: Multi-error processing guide
│   ├── MULTI_FILE_FIXES_AND_PATH_NORMALIZATION.md
│   ├── FILE_PATH_AUTO_DETECTION_FLOW.md
│   └── AUTO_DETECT_FILE_PATH.md
├── requirements.txt       # Python dependencies
├── start.sh              # Quick start script
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **GitHub Personal Access Token** (with repo permissions)
- **Bob CLI** (optional, for primary AI agent)
  - Install from: https://github.com/RooVetGit/Roo-Code
  - Or use OpenAI as fallback
- **OpenAI API Key** (optional, for fallback)

### Setup

1. **Set Environment Variables:**

```bash
# Required: GitHub Token
export GITHUB_TOKEN="your_github_personal_access_token"

# Optional: Bob CLI (if using Bob as primary agent)
export BOB_CLI_COMMAND="bob"  # or path to bob executable

# Optional: OpenAI (if using as fallback or primary)
export OPENAI_API_KEY="your_openai_api_key"
```

2. **Run the System:**

```bash
./start.sh
```

That's it! The system will:
- Create a virtual environment
- Install dependencies
- Start the FastAPI server at http://localhost:8000

### API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📡 API Usage

### 1. Upload Log File

```bash
curl -X POST "http://localhost:8000/api/v1/logs/ingest" \
  -F "repository_url=https://github.com/your-org/your-repo" \
  -F "log_file=@/path/to/error.log"
```

**Response:**
```json
{
  "status": "success",
  "log_id": "log-abc123",
  "message": "Log file ingested and analyzed",
  "analysis_url": "/api/v1/analysis/log-abc123"
}
```

### 2. View Analysis

```bash
curl "http://localhost:8000/api/v1/analysis/log-abc123"
```

**Response:**
```json
{
  "log_id": "log-abc123",
  "error_type": "TypeError",
  "file_path": "consumer/billing_consumer.py",
  "line_number": 45,
  "analysis": "Attempting to access property on None object",
  "fixable": true
}
```

### 3. Generate Fix

```bash
curl -X POST "http://localhost:8000/api/v1/fix/log-abc123"
```

**Response:**
```json
{
  "log_id": "log-abc123",
  "fix_generated": true,
  "detected_file_path": "consumer/billing_consumer.py",
  "fix": {
    "file_path": "consumer/billing_consumer.py",
    "file_changes": [
      {
        "file_path": "consumer/billing_consumer.py",
        "original_code": "result = data.user",
        "fixed_code": "result = data.get('user')"
      }
    ],
    "explanation": "Added null check to prevent TypeError"
  }
}
```

### 4. Create Pull Request (Automatic!)

```bash
curl -X POST "http://localhost:8000/api/v1/pr/create/log-abc123" \
  -F "base_branch=main"
```

**Note:** `target_file_path` is **automatically detected** from the fix! No manual input needed.

**Response:**
```json
{
  "status": "success",
  "log_id": "log-abc123",
  "branch_name": "autofix/log-abc123",
  "target_file_path": "consumer/billing_consumer.py",
  "pull_request": {
    "pr_number": 42,
    "pr_url": "https://github.com/your-org/your-repo/pull/42",
    "status": "CREATED"
  }
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | **Yes** | - | GitHub Personal Access Token |
| `BOB_CLI_COMMAND` | No | `bob` | Path to Bob CLI executable |
| `OPENAI_API_KEY` | No | - | OpenAI API key (fallback) |
| `AI_AGENT_PRIMARY` | No | `bob_cli` | Primary AI agent (`bob_cli` or `openai`) |

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic) with these permissions:
   - `repo` (Full control of private repositories)
3. Copy the token and set it as `GITHUB_TOKEN` environment variable

### Bob CLI Setup

1. Install Bob CLI from: https://github.com/RooVetGit/Roo-Code
2. Ensure `bob` command is in your PATH
3. Or set `BOB_CLI_COMMAND` to the full path

## 🌟 Key Features Explained

### 1. Path Normalization

Handles absolute paths from Docker containers or runtime environments:

```
Input:  /app/consumer/billing_consumer.py
Output: consumer/billing_consumer.py (actual repo path)
```

**Strategies:**
- Direct path matching
- Filename search across repo
- Suffix matching
- Best match scoring

### 2. Multi-File Fixes

Supports fixing multiple files in a single PR:

```json
{
  "file_changes": [
    {"file_path": "services/user.py", "fixed_code": "..."},
    {"file_path": "utils/validator.py", "fixed_code": "..."},
    {"file_path": "tests/test_user.py", "fixed_code": "..."}
  ]
}
```

### 3. Safe Code Replacement

Uses line-based replacement to preserve unrelated code:

```python
# Only replaces lines 45-55, keeps everything else intact
replace_lines_in_file(
    file_path="billing.py",
    start_line=45,
    end_line=55,
    fixed_code="..."
)
```

### 4. Auto-Detection

File paths are automatically detected and passed through the workflow:

```
Log Analysis → Detects file_path
     ↓
Fix Generation → Stores file_path
     ↓
PR Creation → Uses file_path (no manual input!)
```

## 📚 Documentation

- **[Multi-File Fixes & Path Normalization](docs/MULTI_FILE_FIXES_AND_PATH_NORMALIZATION.md)** - Detailed guide
- **[File Path Auto-Detection Flow](docs/FILE_PATH_AUTO_DETECTION_FLOW.md)** - How auto-detection works
- **[System Design](AUTOMATED_FIX_SYSTEM_DESIGN.md)** - Architecture overview
- **[Implementation Guide](IMPLEMENTATION_GUIDE.md)** - Development guide

## 🧪 Testing

### Manual Testing

```bash
# 1. Create a test log file
cat > test_error.log << EOF
Traceback (most recent call last):
  File "/app/consumer/billing_consumer.py", line 45, in process
    result = data.user
TypeError: 'NoneType' object has no attribute 'user'
EOF

# 2. Upload to system
curl -X POST "http://localhost:8000/api/v1/logs/ingest" \
  -F "repository_url=https://github.com/your-org/your-repo" \
  -F "log_file=@test_error.log"

# 3. Follow the workflow (analysis → fix → PR)
```

## 🔐 Security

- **GitHub Token**: Keep your token secure, never commit it
- **API Keys**: Store in environment variables, not in code
- **PR Review**: Always review auto-generated PRs before merging

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn src.main:app --reload --port 8000
```

### Adding Features

1. Create feature branch
2. Implement changes in `src/`
3. Update documentation in `docs/`
4. Test thoroughly
5. Submit PR

## 🆘 Troubleshooting

### "original_code snippet was not found"

**Solution:** The system now automatically falls back to line-based replacement. Ensure your error analysis includes `line_number`.

### "Could not auto-detect target file path"

**Solution:** Provide explicit `target_file_path` parameter:
```bash
curl -X POST ".../pr/create/log-abc123" \
  -F "target_file_path=src/services/user.py"
```

### "Bob CLI not found"

**Solution:** Either:
1. Install Bob CLI and add to PATH
2. Set `BOB_CLI_COMMAND` to full path
3. Use OpenAI: `export AI_AGENT_PRIMARY=openai`

## 📊 Status

**Current Version**: 1.0.0-MVP  
**Status**: Production Ready  
**Last Updated**: 2024-01-15

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ using Bob AI Agent and OpenAI**