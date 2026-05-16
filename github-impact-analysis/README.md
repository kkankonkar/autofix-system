# Fixium - AI-Powered Code Review Workflow

Fixium is an automated code review system that integrates Bob AI (IBM's AI assistant) with GitHub Pull Requests to provide comprehensive code analysis, automated fix implementation, verification, and intelligent documentation suggestions.

## Features

### 🔍 Code Review (`Fixium:review`)
- **Comprehensive Analysis**: Multi-phase workflow covering functionality, security, maintainability, and performance
- **Automated Fixes**: Implements review findings with priority ordering (Critical → High → Medium → Low)
- **Verification**: Validates implementations and identifies new issues
- **Iterative Refinement**: Continues until code is clean (configurable max iterations)
- **PR Integration**: Submits inline comments directly to GitHub PRs

### 📚 Documentation Analysis (`Fixium:updatedocs`)
- **Smart Detection**: Automatically identifies major features vs minor changes
- **Comprehensive Discovery**: Analyzes ALL .md files in repository (README, API docs, guides, etc.)
- **Intelligent Suggestions**: Provides actionable documentation update recommendations
- **Selective Analysis**: Skip minor changes (bug fixes, dependency updates, security patches)
- **Force Mode**: Override automatic detection when needed

## Quick Start

### Prerequisites

- Python 3.11+
- Bob CLI (IBM AI Assistant)
- GitHub Personal Access Token with `repo` and `write:discussion` scopes
- Bob Shell API Key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/code-review-workflow.git
cd code-review-workflow
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
export GITHUB_TOKEN="your-github-token"
export BOBSHELL_API_KEY="your-bob-api-key"
export FIXIUM_AUTHORIZED_USERS="user1,user2,user3"
```

### Usage

#### Code Review

Comment on a PR with:
```
Fixium:review
```

**Options:**
- `Fixium:review --severity high,medium` - Filter by severity
- `Fixium:review --type bug,security` - Filter by type
- `Fixium:review --exclude-severity low` - Exclude severities
- `Fixium:review --files src/file1.py,src/file2.py` - Review specific files

#### Documentation Analysis

Comment on a PR with:
```
Fixium:updatedocs
```

**Behavior:**
- ✅ **Analyzes**: Major features, new functionality, significant refactors
- ❌ **Skips**: Bug fixes, dependency updates, security patches, minor changes

**Options:**
- `Fixium:updatedocs --force` - Analyze even if classified as minor change
- `Fixium:updatedocs --files README.md,docs/API.md` - Analyze specific files only

**Example Output:**
```json
{
  "pr_classification": {
    "type": "major",
    "confidence": "high",
    "reasoning": "New authentication system with multiple new files"
  },
  "documentation_files": [
    "README.md",
    "docs/API.md",
    "docs/authentication.md"
  ],
  "suggestions": [
    {
      "file": "README.md",
      "section": "Authentication",
      "priority": "high",
      "suggestion": "Add documentation for new OAuth2 authentication flow",
      "details": "The PR introduces OAuth2 support but README.md still only documents basic auth"
    }
  ]
}
```

## Architecture

### Components

```
fixium/
├── main.py                 # Code review entry point
├── doc_main.py            # Documentation analysis entry point
├── github_client.py       # GitHub API client
├── review_runner.py       # Code review orchestration
├── doc_runner.py          # Documentation analysis orchestration
├── doc_discoverer.py      # Documentation file discovery
├── change_classifier.py   # PR change classification
├── comment_parser.py      # Command parsing
├── access_control.py      # Authorization
├── error_handler.py       # Error handling
├── progress_tracker.py    # Progress tracking
└── config.py             # Configuration management

prompts/
├── review-workflow.md              # Review methodology
├── code-review.md                  # Initial review prompt
├── implement-review-findings.md    # Implementation prompt
├── verify-implementations.md       # Verification prompt
└── analyze-documentation.md        # Documentation analysis prompt

.github/workflows/
└── fixium.yml            # GitHub Actions workflow
```

### Workflow

#### Code Review Workflow

```
1. User comments "Fixium:review" on PR
2. GitHub Actions triggers fixium-review job
3. Access control validates user authorization
4. Review runner fetches PR files
5. Bob AI analyzes code (review-workflow.md)
6. Findings submitted as inline PR comments
7. (Optional) Automated fix implementation
8. (Optional) Verification of fixes
```

#### Documentation Analysis Workflow

```
1. User comments "Fixium:updatedocs" on PR
2. GitHub Actions triggers fixium-docs job
3. Access control validates user authorization
4. Change classifier analyzes PR commits and files
5. If major feature:
   a. Doc discoverer finds all .md files
   b. Bob AI analyzes documentation gaps
   c. Suggestions submitted as PR comment
6. If minor change:
   a. Skip analysis (unless --force used)
   b. Post skip reason as PR comment
```

## Change Classification

### Major Features (Analyzed)
- New features (`feat:` commits)
- Breaking changes (`BREAKING CHANGE:`)
- Major refactors (>500 lines changed)
- New API endpoints
- New modules/packages
- Architecture changes

### Minor Changes (Skipped)
- Bug fixes (`fix:` commits)
- Dependency updates (`chore(deps):`)
- Security patches (`security:`, CVE references)
- Documentation-only changes
- Test-only changes
- Configuration tweaks

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | Yes |
| `BOBSHELL_API_KEY` | Bob AI API key | Yes |
| `FIXIUM_AUTHORIZED_USERS` | Comma-separated list of authorized users | Yes |
| `GITHUB_REPOSITORY` | Repository (owner/repo) | Auto-set by Actions |
| `GITHUB_OWNER` | Repository owner | Auto-set by Actions |
| `GITHUB_REPO` | Repository name | Auto-set by Actions |
| `PR_NUMBER` | Pull request number | Auto-set by Actions |
| `COMMENT_BODY` | Comment text | Auto-set by Actions |
| `COMMENT_USER` | Comment author | Auto-set by Actions |

### GitHub Secrets

Set these in your repository settings:

1. `GITHUB_TOKEN` - Automatically provided by GitHub Actions
2. `BOBSHELL_API_KEY` - Your Bob AI API key
3. `FIXIUM_AUTHORIZED_USERS` - Comma-separated usernames (e.g., `user1,user2,user3`)

## Local Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_doc_discoverer.py

# Run with coverage
pytest --cov=fixium --cov-report=html
```

### Manual Code Review

```bash
# Review specific files
./review_workflow.sh review src/file.py

# Review directory
./review_workflow.sh review src/

# Review PR
./review_workflow.sh review-pr 123

# Auto-run complete workflow
./review_workflow.sh auto src/ 3
```

### Manual Documentation Analysis

```bash
# Analyze documentation for PR
./review_workflow.sh analyze-docs 123

# Force analysis (skip classification)
./review_workflow.sh analyze-docs 123 --force

# Analyze specific files
./review_workflow.sh analyze-docs 123 --files README.md,docs/API.md
```

## CI/CD Integration

### GitHub Actions

The workflow is automatically triggered by PR comments. See `.github/workflows/fixium.yml` for configuration.

**Jobs:**
- `fixium-review` - Triggered by `Fixium:review` comments
- `fixium-docs` - Triggered by `Fixium:updatedocs` comments

**Concurrency:**
- Each job has separate concurrency groups
- Only one review/analysis per PR at a time
- No cancellation of in-progress jobs

## Output Formats

### Code Review Output

```json
{
  "findings": [
    {
      "severity": "high",
      "type": "bug",
      "count": 3,
      "comments": [
        {
          "file": "src/handler.py",
          "lineNumber": 45,
          "issue": "Missing error handling",
          "details": "Function can raise exception without try-catch",
          "suggestion": "Add try-except block"
        }
      ]
    }
  ],
  "summary": {
    "totalFindings": 14,
    "critical": 2,
    "high": 4,
    "medium": 6,
    "low": 2
  }
}
```

### Documentation Analysis Output

```json
{
  "pr_classification": {
    "type": "major",
    "confidence": "high",
    "reasoning": "New feature with multiple new files",
    "commit_indicators": ["feat: Add payment system"],
    "file_indicators": ["src/payment/processor.py"]
  },
  "documentation_files": [
    {
      "path": "README.md",
      "type": "readme"
    },
    {
      "path": "docs/API.md",
      "type": "api"
    }
  ],
  "suggestions": [
    {
      "file": "README.md",
      "section": "Installation",
      "priority": "high",
      "suggestion": "Add payment system setup instructions",
      "details": "New payment module requires additional configuration"
    }
  ],
  "summary": {
    "total_suggestions": 5,
    "high_priority": 2,
    "medium_priority": 2,
    "low_priority": 1
  }
}
```

## Best Practices

### For Code Reviews

1. **Review incrementally** - Comment on PRs as they're developed
2. **Filter appropriately** - Focus on critical/high severity first
3. **Iterate until clean** - Use auto workflow for complete cycles
4. **Document decisions** - Use blocked/skipped reasons for tracking

### For Documentation Analysis

1. **Run on major features** - Let automatic classification work
2. **Use --force sparingly** - Only when classification is wrong
3. **Review all suggestions** - AI suggestions need human validation
4. **Update promptly** - Keep docs in sync with code changes

## Troubleshooting

### Common Issues

**"User not authorized"**
- Add user to `FIXIUM_AUTHORIZED_USERS` secret
- Format: `user1,user2,user3` (comma-separated, no spaces)

**"Bob CLI not found"**
- Ensure Bob CLI is installed in the environment
- Check PATH configuration

**"Rate limit exceeded"**
- GitHub API has rate limits
- Wait for rate limit reset
- Consider using GitHub App instead of PAT

**"Documentation analysis skipped"**
- PR classified as minor change
- Use `--force` flag to override
- Check commit messages and file changes

### Debug Mode

Enable debug logging:
```bash
export FIXIUM_DEBUG=1
python -m fixium.main
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

[Your License Here]

## Support

For issues or questions:
1. Check this documentation
2. Review error messages and logs
3. Check GitHub Actions logs
4. Open an issue on GitHub

---

**Made with Bob** 🤖
