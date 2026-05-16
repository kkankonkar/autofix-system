# Fixium Folder Structure Plan

## Recommendation: Use Existing Folder with Nested Python Package ✅

**DO NOT create a new folder.** Instead, add Python code as a nested package inside the existing `code-review-workflow` directory.

---

## Why Use Existing Folder?

### Advantages ✅
1. **Keep existing shell scripts** - They already work and are tested
2. **Gradual migration** - Add Python alongside shell, migrate incrementally
3. **Reuse existing work** - Don't duplicate review_workflow.sh, prompts, lib/, etc.
4. **Single repository** - Easier to maintain and version control
5. **Docker simplicity** - One Dockerfile, one image
6. **Backward compatible** - Can still use shell scripts directly if needed
7. **Preserve git history** - Keep all existing commits and history
8. **Easier deployment** - Single deployment pipeline

### Disadvantages of New Folder ❌
- ❌ Duplicate code and prompts
- ❌ Two repositories to maintain
- ❌ Harder to keep in sync
- ❌ More complex deployment
- ❌ Lose existing git history
- ❌ Need to copy/update files in two places

---

## Proposed Folder Structure

```
code-review-workflow/                    # EXISTING ROOT - Keep as-is
│
├── fixium/                              # NEW - Python package
│   ├── __init__.py                      # Package init
│   ├── main.py                          # Main orchestrator
│   ├── comment_parser.py                # Parse PR comments
│   ├── github_client.py                 # GitHub API wrapper
│   ├── access_control.py                # User authorization
│   ├── progress_tracker.py              # Progress comments
│   ├── review_runner.py                 # Bob Shell wrapper
│   ├── error_handler.py                 # Error handling
│   └── config.py                        # Configuration
│
├── tests/                               # NEW - Python tests
│   ├── __init__.py
│   ├── test_comment_parser.py
│   ├── test_github_client.py
│   ├── test_access_control.py
│   ├── test_progress_tracker.py
│   ├── test_review_runner.py
│   └── test_error_handler.py
│
├── lib/                                 # EXISTING - Keep shell libraries
│   ├── github_api.sh                    # UPDATE - Rebrand to Fixium
│   ├── comment_formatter.sh             # UPDATE - Rebrand to Fixium
│   └── [other shell scripts]
│
├── prompts/                             # EXISTING - Keep prompts
│   ├── review-workflow.md               # UPDATE - Rebrand to Fixium
│   ├── code-review.md                   # UPDATE - Rebrand to Fixium
│   ├── implement-review-findings.md     # UPDATE - Rebrand to Fixium
│   ├── verify-implementations.md        # UPDATE - Rebrand to Fixium
│   ├── code-review-post-fixes-check.md  # UPDATE - Rebrand to Fixium
│   └── README.md                        # UPDATE - Rebrand to Fixium
│
├── .github/                             # NEW - GitHub Actions
│   └── workflows/
│       └── fixium.yml                   # NEW - Workflow file
│
├── config/                              # EXISTING - Keep config
│   └── github.env                       # EXISTING - Keep as-is
│
├── review_workflow.sh                   # EXISTING - UPDATE rebrand
├── submit_pr_comments.sh                # EXISTING - UPDATE rebrand
├── requirements.txt                     # NEW - Python dependencies
├── pytest.ini                           # NEW - Test configuration
├── Dockerfile                           # EXISTING - UPDATE for Python
├── .dockerignore                        # NEW - Docker ignore file
├── .gitignore                           # EXISTING - UPDATE for Python
│
├── README.md                            # EXISTING - UPDATE rebrand
├── README-pr-comments.md                # EXISTING - UPDATE rebrand
├── QUICKSTART-pr-comments.md            # EXISTING - UPDATE rebrand
├── AGENTS.md                            # EXISTING - Already created
├── FIXIUM-GITHUB-ACTIONS-PLAN.md       # NEW - Planning doc
├── FIXIUM-PYTHON-IMPLEMENTATION.md     # NEW - Planning doc
└── FIXIUM-FOLDER-STRUCTURE.md          # NEW - This file
```

---

## File Status Legend

- **EXISTING** - File already exists, keep as-is or update
- **NEW** - File needs to be created
- **UPDATE** - File exists but needs modifications (rebranding, etc.)

---

## Implementation Steps

### Phase 1: Create Python Package Structure
```bash
cd ~/code-review-workflow

# Create Python package
mkdir -p fixium
touch fixium/__init__.py
touch fixium/main.py
touch fixium/comment_parser.py
touch fixium/github_client.py
touch fixium/access_control.py
touch fixium/progress_tracker.py
touch fixium/review_runner.py
touch fixium/error_handler.py
touch fixium/config.py

# Create tests directory
mkdir -p tests
touch tests/__init__.py
touch tests/test_comment_parser.py
touch tests/test_github_client.py
touch tests/test_access_control.py
touch tests/test_progress_tracker.py
touch tests/test_review_runner.py
touch tests/test_error_handler.py

# Create Python config files
touch requirements.txt
touch pytest.ini
touch .dockerignore
```

### Phase 2: Create GitHub Actions
```bash
# Create GitHub Actions workflow
mkdir -p .github/workflows
touch .github/workflows/fixium.yml
```

### Phase 3: Update Existing Files
```bash
# Update for Python support
# - Dockerfile (add Python base image)
# - .gitignore (add Python patterns)
# - review_workflow.sh (rebrand to Fixium)
# - submit_pr_comments.sh (rebrand to Fixium)
# - lib/*.sh (rebrand to Fixium)
# - prompts/*.md (rebrand to Fixium)
# - README*.md (rebrand to Fixium)
```

---

## What Gets Created vs Updated

### New Files (Create from scratch)
```
fixium/                    # Entire Python package
tests/                     # Entire test suite
.github/workflows/         # GitHub Actions
requirements.txt           # Python dependencies
pytest.ini                 # Test config
.dockerignore             # Docker ignore
FIXIUM-*.md               # Planning docs (already created)
```

### Existing Files (Update/Rebrand)
```
review_workflow.sh         # Rebrand Bob Shell → Fixium
submit_pr_comments.sh      # Rebrand Bob Shell → Fixium
lib/github_api.sh         # Rebrand Bob Shell → Fixium
lib/comment_formatter.sh  # Rebrand Bob Shell → Fixium
prompts/*.md              # Rebrand Bob Shell → Fixium
README.md                 # Rebrand Bob Shell → Fixium
README-pr-comments.md     # Rebrand Bob Shell → Fixium
QUICKSTART-pr-comments.md # Rebrand Bob Shell → Fixium
Dockerfile                # Add Python support
.gitignore                # Add Python patterns
```

### Keep As-Is (No changes needed)
```
config/github.env         # Configuration file
review1.json              # Example review output
review2.json              # Example review output
review3.json              # Example review output
```

---

## Directory Tree After Implementation

```
code-review-workflow/
├── .github/
│   └── workflows/
│       └── fixium.yml                   ← NEW
├── config/
│   └── github.env                       ← KEEP
├── fixium/                              ← NEW PACKAGE
│   ├── __init__.py
│   ├── main.py
│   ├── comment_parser.py
│   ├── github_client.py
│   ├── access_control.py
│   ├── progress_tracker.py
│   ├── review_runner.py
│   ├── error_handler.py
│   └── config.py
├── lib/                                 ← UPDATE
│   ├── github_api.sh
│   └── comment_formatter.sh
├── prompts/                             ← UPDATE
│   ├── review-workflow.md
│   ├── code-review.md
│   ├── implement-review-findings.md
│   ├── verify-implementations.md
│   ├── code-review-post-fixes-check.md
│   └── README.md
├── tests/                               ← NEW
│   ├── __init__.py
│   ├── test_comment_parser.py
│   ├── test_github_client.py
│   ├── test_access_control.py
│   ├── test_progress_tracker.py
│   ├── test_review_runner.py
│   └── test_error_handler.py
├── .dockerignore                        ← NEW
├── .gitignore                           ← UPDATE
├── AGENTS.md                            ← KEEP
├── Dockerfile                           ← UPDATE
├── FIXIUM-FOLDER-STRUCTURE.md          ← NEW (this file)
├── FIXIUM-GITHUB-ACTIONS-PLAN.md       ← KEEP
├── FIXIUM-PYTHON-IMPLEMENTATION.md     ← KEEP
├── pytest.ini                           ← NEW
├── README.md                            ← UPDATE
├── README-pr-comments.md                ← UPDATE
├── QUICKSTART-pr-comments.md            ← UPDATE
├── requirements.txt                     ← NEW
├── review_workflow.sh                   ← UPDATE
├── review1.json                         ← KEEP
├── review2.json                         ← KEEP
├── review3.json                         ← KEEP
└── submit_pr_comments.sh                ← UPDATE
```

---

## Git Workflow

### Initial Setup
```bash
# Make sure you're in the right directory
cd ~/code-review-workflow

# Check current status
git status

# Create a feature branch for Fixium implementation
git checkout -b feature/fixium-implementation

# Create Python package structure
mkdir -p fixium tests .github/workflows
```

### Commit Strategy
```bash
# Commit 1: Add Python package structure
git add fixium/ tests/ requirements.txt pytest.ini
git commit -m "feat: Add Python package structure for Fixium"

# Commit 2: Add GitHub Actions workflow
git add .github/
git commit -m "feat: Add GitHub Actions workflow for Fixium"

# Commit 3: Update Dockerfile for Python
git add Dockerfile .dockerignore
git commit -m "feat: Update Dockerfile to support Python"

# Commit 4: Rebrand shell scripts
git add lib/ review_workflow.sh submit_pr_comments.sh
git commit -m "refactor: Rebrand Bob Shell to Fixium in shell scripts"

# Commit 5: Rebrand documentation
git add README*.md prompts/ AGENTS.md
git commit -m "docs: Rebrand Bob Shell to Fixium in documentation"

# Commit 6: Add planning documents
git add FIXIUM-*.md
git commit -m "docs: Add Fixium implementation planning documents"
```

---

## Docker Build Context

With this structure, the Docker build context includes everything:

```dockerfile
# Dockerfile can access:
COPY requirements.txt .          # Python deps
COPY fixium/ ./fixium/          # Python package
COPY lib/ ./lib/                # Shell scripts
COPY prompts/ ./prompts/        # Prompts
COPY review_workflow.sh .       # Main script
COPY submit_pr_comments.sh .    # Submit script
```

---

## Python Import Paths

With this structure, Python imports work cleanly:

```python
# From fixium/main.py
from fixium.comment_parser import CommentParser
from fixium.github_client import GitHubClient
from fixium.access_control import AccessControl
from fixium.progress_tracker import ProgressTracker
from fixium.review_runner import ReviewRunner
from fixium.error_handler import ErrorHandler

# From tests/test_comment_parser.py
from fixium.comment_parser import CommentParser
```

---

## Environment Variables

The Python code can access the same environment variables:

```python
import os

# GitHub configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')
GITHUB_OWNER = os.getenv('GITHUB_OWNER')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# Fixium configuration
BOBSHELL_API_KEY = os.getenv('BOBSHELL_API_KEY')
FIXIUM_AUTHORIZED_USERS = os.getenv('FIXIUM_AUTHORIZED_USERS')

# PR context
PR_NUMBER = os.getenv('PR_NUMBER')
COMMENT_BODY = os.getenv('COMMENT_BODY')
COMMENT_USER = os.getenv('COMMENT_USER')
```

---

## Testing Strategy

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=fixium --cov-report=html

# Run specific test
pytest tests/test_comment_parser.py -v
```

### Docker Testing
```bash
# Build image
docker build -t fixium:test .

# Run tests in container
docker run --rm fixium:test pytest

# Test with environment variables
docker run --rm \
  -e GITHUB_TOKEN="test_token" \
  -e PR_NUMBER="123" \
  -e COMMENT_BODY="Fixium:review --severity high" \
  -e COMMENT_USER="testuser" \
  fixium:test python -m fixium.main
```

---

## Migration Checklist

- [ ] Create `fixium/` Python package directory
- [ ] Create `tests/` directory
- [ ] Create `.github/workflows/` directory
- [ ] Add `requirements.txt`
- [ ] Add `pytest.ini`
- [ ] Add `.dockerignore`
- [ ] Implement Python modules (7 files)
- [ ] Write Python tests (6 files)
- [ ] Create GitHub Actions workflow
- [ ] Update Dockerfile for Python
- [ ] Update `.gitignore` for Python
- [ ] Rebrand shell scripts (Bob Shell → Fixium)
- [ ] Rebrand documentation (Bob Shell → Fixium)
- [ ] Test locally with pytest
- [ ] Test Docker build
- [ ] Test GitHub Actions workflow
- [ ] Deploy to production

---

## Summary

**✅ RECOMMENDED: Use existing `code-review-workflow` folder**

Add Python as a nested `fixium/` package inside the existing directory. This approach:
- Preserves existing work
- Enables gradual migration
- Maintains single source of truth
- Simplifies deployment
- Keeps git history

**❌ NOT RECOMMENDED: Create new folder**

Creating a separate folder would require duplicating code, maintaining two repositories, and losing the benefits of the existing infrastructure.

---

**Next Step**: Start implementation by creating the `fixium/` directory and Python files inside the existing `code-review-workflow` folder.