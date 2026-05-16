# Local Testing Guide for Fixium

This guide explains how to test the Fixium code review workflow locally before deploying to GitHub Actions.

## Quick Start

```bash
# Run all local tests
./test_local.sh
```

## Prerequisites

### Required Tools
- **Python 3.9+** - For running Fixium
- **Bob CLI** - For code review functionality
- **Git** - For repository operations

### Required Files
Create a `secrets.env` file in the project root:

```bash
# secrets.env
GITHUB_TOKEN=ghp_your_github_token_here
BOBSHELL_API_KEY=your_bobshell_api_key
FIXIUM_AUTHORIZED_USERS=username1,username2
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo
```

**Important:** Add `secrets.env` to `.gitignore` to prevent committing secrets!

## Testing Levels

### Level 1: Unit Tests (Fastest)

Test individual Python modules without external dependencies:

```bash
# Run all unit tests
python3 -m pytest tests/ -v --no-cov

# Run specific test file
python3 -m pytest tests/test_github_client.py -v --no-cov

# Run specific test
python3 -m pytest tests/test_github_client.py::TestGitHubClient::test_update_comment -v --no-cov
```

### Level 2: Module Import Tests

Verify all Python modules can be imported correctly:

```bash
python3 -c "
from fixium.main import main
from fixium.config import Config
from fixium.github_client import GitHubClient
from fixium.comment_parser import CommentParser
from fixium.access_control import AccessControl
from fixium.progress_tracker import ProgressTracker
from fixium.review_runner import ReviewRunner
from fixium.error_handler import ErrorHandler
print('✓ All modules imported successfully')
"
```

### Level 3: Configuration Tests

Test configuration loading with your actual secrets:

```bash
# Source your secrets
source secrets.env

# Set mock environment
export GITHUB_REPOSITORY="${GITHUB_OWNER}/${GITHUB_REPO}"
export PR_NUMBER="123"
export COMMENT_BODY="Fixium:review --severity high"
export COMMENT_USER="${FIXIUM_AUTHORIZED_USERS%%,*}"
export GITHUB_WORKSPACE="$(pwd)"

# Test configuration
python3 -c "
from fixium.config import Config
config = Config()
errors = config.validate()
if errors:
    print(f'Errors: {errors}')
    exit(1)
print(f'✓ Configuration valid')
print(f'  Repository: {config.github_repository}')
print(f'  PR Number: {config.pr_number}')
"
```

### Level 4: Comment Parser Tests

Test command parsing logic:

```bash
python3 << 'EOF'
from fixium.comment_parser import CommentParser

test_cases = [
    "Fixium:review",
    "Fixium:review --severity high",
    "Fixium:review --severity high,medium --type bug,security",
    "Fixium:review --exclude-severity low",
]

for test in test_cases:
    command = CommentParser.parse(test)
    if command and command.is_valid():
        print(f"✓ Parsed: {test}")
        print(f"  Filters: {command.filters}")
    else:
        print(f"✗ Failed: {test}")
EOF
```

### Level 5: GitHub Client Tests (Mocked)

Test GitHub API client without making real API calls:

```bash
python3 << 'EOF'
import os
from unittest.mock import patch, Mock
from fixium.github_client import GitHubClient

# Load secrets
import dotenv
dotenv.load_dotenv('secrets.env')

with patch('fixium.github_client.Github') as mock_github:
    mock_repo = Mock()
    mock_github.return_value.get_repo.return_value = mock_repo
    
    client = GitHubClient(
        token=os.getenv('GITHUB_TOKEN'),
        repository=f"{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}"
    )
    print(f"✓ GitHub client initialized")
    print(f"  Repository: {client.repo_name}")
EOF
```

### Level 6: Full Workflow Test (Dry Run)

Test the complete workflow with a real PR (requires Bob CLI):

```bash
# Source secrets
source secrets.env

# Set environment for a real PR
export GITHUB_REPOSITORY="${GITHUB_OWNER}/${GITHUB_REPO}"
export PR_NUMBER="123"  # Use a real PR number
export COMMENT_BODY="Fixium:review --severity high"
export COMMENT_USER="${FIXIUM_AUTHORIZED_USERS%%,*}"
export GITHUB_WORKSPACE="$(pwd)"

# Run the main workflow (will make real API calls!)
python3 -m fixium.main
```

### Level 7: Shell Script Tests

Test the bash review workflow scripts:

```bash
# Test PR review (requires Bob CLI)
./review_workflow.sh review-pr 123

# Test with file list
echo "file1.py" > test_files.txt
echo "file2.py" >> test_files.txt
./review_workflow.sh review @test_files.txt
```

## Automated Testing Script

The `test_local.sh` script runs Levels 1-5 automatically:

```bash
./test_local.sh
```

This script:
1. ✅ Checks prerequisites (Python, Bob CLI)
2. ✅ Verifies secrets.env exists
3. ✅ Installs Python dependencies
4. ✅ Runs all unit tests
5. ✅ Tests module imports
6. ✅ Tests configuration loading
7. ✅ Tests comment parsing
8. ✅ Tests GitHub client initialization

## Common Issues and Solutions

### Issue: `ModuleNotFoundError: No module named 'github'`

**Solution:** Install dependencies
```bash
pip3 install -r requirements.txt
```

### Issue: `ValueError: GitHub token not provided`

**Solution:** Create or update `secrets.env`
```bash
echo "GITHUB_TOKEN=your_token" >> secrets.env
echo "BOBSHELL_API_KEY=your_key" >> secrets.env
```

### Issue: `Bob CLI not found`

**Solution:** Install Bob CLI
```bash
# Download from GitHub releases
# https://github.com/IBM/bob/releases
```

### Issue: `AttributeError: 'Repository' object has no attribute...`

**Solution:** This indicates a PyGithub API mismatch. Check:
1. PyGithub version in `requirements.txt`
2. Method names in `fixium/github_client.py`
3. Run unit tests to catch these early

### Issue: Tests pass locally but fail in GitHub Actions

**Possible causes:**
1. **Environment differences** - Check Python version, dependencies
2. **Missing secrets** - Verify GitHub secrets are set
3. **File paths** - Use relative paths, not absolute
4. **Permissions** - Ensure scripts are executable

## Best Practices

### Before Every Commit

```bash
# Run quick tests
./test_local.sh

# Or manually:
python3 -m pytest tests/ -v --no-cov
```

### Before Creating PR

```bash
# Run full test suite with coverage
python3 -m pytest tests/ -v

# Test with a real PR (if safe)
export PR_NUMBER="your_test_pr"
python3 -m fixium.main
```

### After Changing GitHub Client

```bash
# Run GitHub client tests specifically
python3 -m pytest tests/test_github_client.py -v

# Test with mock environment
python3 << 'EOF'
from unittest.mock import patch, Mock
from fixium.github_client import GitHubClient

with patch('fixium.github_client.Github') as mock_github:
    mock_repo = Mock()
    mock_github.return_value.get_repo.return_value = mock_repo
    client = GitHubClient(token='test', repository='owner/repo')
    
    # Test the method you changed
    # Example: client.update_comment(123, "test")
    print("✓ Test passed")
EOF
```

## Continuous Integration

The GitHub Actions workflow (`.github/workflows/fixium.yml`) runs similar tests:

1. Checkout code
2. Setup Python 3.11
3. Install dependencies
4. Install Bob CLI
5. Set environment variables
6. Run Fixium

To simulate this locally:

```bash
# Use Python 3.11 (if available)
python3.11 -m pytest tests/ -v

# Or use Docker to match exact environment
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  python:3.11-slim \
  bash -c "pip install -r requirements.txt && pytest tests/ -v"
```

## Debugging Tips

### Enable Verbose Output

```bash
# Python verbose mode
python3 -v -m fixium.main

# Pytest verbose with traceback
python3 -m pytest tests/ -vv --tb=long

# Shell script debug mode
bash -x ./review_workflow.sh review-pr 123
```

### Check Environment Variables

```bash
# Print all Fixium-related env vars
env | grep -E '(GITHUB|FIXIUM|BOBSHELL|PR_NUMBER|COMMENT)'
```

### Test Individual Components

```bash
# Test just the config
python3 -c "from fixium.config import Config; print(Config())"

# Test just the parser
python3 -c "from fixium.comment_parser import CommentParser; print(CommentParser.parse('Fixium:review'))"

# Test just the GitHub client
python3 -c "from fixium.github_client import GitHubClient; print('Import OK')"
```

## Coverage Reports

Generate HTML coverage reports:

```bash
# Run tests with coverage
python3 -m pytest tests/ --cov=fixium --cov-report=html

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Related Documentation

- [README.md](README.md) - Main project documentation
- [AGENTS.md](AGENTS.md) - Agent rules and workflow
- [README-pr-comments.md](README-pr-comments.md) - PR comment submission
- [QUICKSTART-pr-comments.md](QUICKSTART-pr-comments.md) - Quick start guide

## Support

If tests fail and you can't resolve the issue:

1. Check error messages carefully
2. Review recent changes to the codebase
3. Compare with working version in git history
4. Check GitHub Actions logs for similar errors
5. Consult the documentation above

---

**Last Updated:** 2026-05-08  
**Maintainer:** Development Team