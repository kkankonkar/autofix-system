# Code Review Workflow - Agent Documentation

## Overview
This directory contains an automated code review workflow system that integrates Fixium AI with GitHub Pull Requests. The system provides comprehensive code review, automated fix implementation, verification, and PR comment submission capabilities.

## Core Components

### Main Workflow Script

#### `review_workflow.sh`
- **Purpose**: Orchestrates the complete code review lifecycle
- **Key Features**:
  - Multi-phase workflow (Review → Implement → Verify)
  - PR integration with automatic file fetching
  - Automated iteration until code is clean
  - Colored terminal output for better UX
- **Commands**:
  - `review` - Conduct code review on files/directories
  - `review-pr` - Review a GitHub Pull Request
  - `implement` - Implement review findings
  - `verify` - Verify implementations and check for new issues
  - `auto` - Run complete workflow with iterations
  - `submit` - Submit review comments to PR
- **Dependencies**: Fixium CLI, jq, bash 4.0+

### PR Comment Submission

#### `submit_pr_comments.sh`
- **Purpose**: Submit code review findings as inline GitHub PR comments
- **API Integration**: GitHub REST API v3
- **Features**:
  - Line-specific inline comments
  - Markdown formatting with severity badges
  - Batch submission for efficiency
  - Dry-run mode for preview
  - Smart filtering by severity/type
  - Automatic retry with exponential backoff
  - Rate limit handling
- **Parameters**:
  - `review_file` - JSON file with findings
  - `pr_number` - GitHub PR number
  - `--dry-run` - Preview without submitting
  - `--severity` - Filter by severity (high, medium, low)
  - `--type` - Filter by type (bug, security, maintainability, performance)
  - `--exclude-severity` - Exclude specific severities
  - `--exclude-type` - Exclude specific types
  - `--batch-size` - Comments per batch (default: 30)

### Library Components

#### `lib/github_api.sh`
- **Purpose**: GitHub API client library
- **Functions**:
  - `validate_token()` - Verify GitHub token validity
  - `check_rate_limit()` - Monitor API rate limits
  - `get_pr_info()` - Fetch PR details
  - `get_pr_commit_sha()` - Get latest commit SHA
  - `get_pr_files()` - List changed files in PR
  - `create_review_comment()` - Submit single comment
  - `create_review_batch()` - Submit multiple comments efficiently
  - `retry_api_call()` - Retry with exponential backoff
- **API Endpoint**: `https://api.github.com`
- **Authentication**: GitHub Personal Access Token
- **Rate Limiting**: Monitors and respects GitHub API limits

#### `lib/comment_formatter.sh`
- **Purpose**: Format review findings as markdown comments
- **Functions**:
  - `format_finding()` - Format single finding as markdown
  - `format_finding_with_code()` - Format with syntax highlighting
  - `get_severity_badge()` - Get emoji for severity level
  - `get_type_icon()` - Get emoji for finding type
  - `group_findings_by_file()` - Group findings by file path
- **Output Format**: GitHub-flavored markdown with:
  - Severity badges (🔴 HIGH, 🟡 MEDIUM, 🔵 LOW)
  - Type icons (🐛 BUG, 🔒 SECURITY, 🔧 MAINTAINABILITY, ⚡ PERFORMANCE)
  - Code blocks with syntax highlighting
  - Line number references

### Prompt Templates

#### `prompts/review-workflow.md`
- **Purpose**: Comprehensive code review methodology
- **Defines**:
  - Review steps and process
  - Review aspects (functionality, security, maintainability, performance)
  - Findings format and severity levels
  - Tool usage guidelines

#### `prompts/code-review.md`
- **Purpose**: Initial code review prompt template
- **Output**: JSON file with findings by severity
- **Usage**: Phase 1 of workflow

#### `prompts/implement-review-findings.md`
- **Purpose**: Implementation tracking prompt
- **Output**: JSON file documenting implemented/blocked/skipped fixes
- **Priority**: Critical → High → Medium → Low
- **Usage**: Phase 2 of workflow

#### `prompts/verify-implementations.md`
- **Purpose**: Post-implementation verification prompt
- **Output**: JSON file with verification results and new findings
- **Usage**: Phase 3 of workflow

#### `prompts/code-review-post-fixes-check.md`
- **Purpose**: Detailed verification methodology
- **Referenced by**: verify-implementations.md

#### `prompts/analyze-documentation.md`
- **Purpose**: Documentation gap analysis methodology
- **Output**: JSON file with documentation update suggestions
- **Analyzes**: All .md files in repository (README, API docs, guides, etc.)
- **Usage**: Documentation analysis workflow

- **Includes**: Comprehensive assessment guidelines

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | - | Yes |
| `GITHUB_OWNER` | Repository owner/organization | - | Yes |
| `GITHUB_REPO` | Repository name | pay-go-metrics-monitor | Yes |
| `GITHUB_API_URL` | GitHub API endpoint | https://api.github.com | No |
| `MAX_COMMENTS_PER_BATCH` | Comments per batch request | 30 | No |
| `RATE_LIMIT_BUFFER` | Rate limit safety buffer | 10 | No |
| `MAX_RETRIES` | Maximum retry attempts | 3 | No |
| `RETRY_DELAY` | Initial retry delay (seconds) | 5 | No |

### Configuration File

**Location**: `config/github.env`

```bash
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
GITHUB_OWNER="your-organization"
GITHUB_REPO="pay-go-metrics-monitor"
MAX_COMMENTS_PER_BATCH=30
RATE_LIMIT_BUFFER=10
```

## Workflow Phases

### Phase 1: Code Review
```bash
./review_workflow.sh review <target> [output_file]
```
- **Input**: Source files, directory, or file list
- **Output**: `review1.json` with findings by severity
- **Process**: Fixium analyzes code following review-workflow.md
- **Target Options**:
  - Single file: `./path/to/file.go`
  - Directory: `./path/to/directory/`
  - File list: `@files.txt` (one path per line)
  - PR: Use `review-pr` command instead

### Phase 2: Implementation
```bash
./review_workflow.sh implement <review_file> [output_file]
```
- **Input**: `review1.json`
- **Output**: `implementation1.json`
- **Process**: Fixium implements fixes with priority ordering
- **Tracking**: Documents implemented/blocked/skipped status

### Phase 3: Verification
```bash
./review_workflow.sh verify <implementation_file> <original_review_file> [output_file]
```
- **Input**: `implementation1.json`, `review1.json`
- **Output**: `review2.json`
- **Process**: Verifies implementations and identifies new issues
- **Result Codes**:
  - 0: Success, no new issues
  - 1: Verification failed
  - 2: New issues found, iteration needed

### Phase 4: PR Comment Submission
```bash
./review_workflow.sh submit <review_file> <pr_number> [options]
```
- **Input**: `review1.json`, PR number
- **Output**: Inline comments on GitHub PR
- **Options**: Filtering, dry-run, batch size

### Automated Workflow
```bash
./review_workflow.sh auto <target> [max_iterations]
```
- **Process**: Runs all phases automatically with iterations
- **Default**: Maximum 3 iterations
- **Stops**: When no new issues found or max iterations reached

### PR Review Workflow
```bash
./review_workflow.sh review-pr <pr_number> [output_file] [--auto-submit]

### Documentation Analysis Workflow
```bash
./review_workflow.sh analyze-docs <pr_number> [options]
```
- **Process**:
  1. Classifies PR changes (major vs minor)
  2. Discovers all .md files in repository
  3. Analyzes documentation gaps for major features
  4. Generates actionable suggestions
- **Output**: `docs_analysis_pr{number}.json`
- **Options**:
  - `--force` - Analyze even if classified as minor
  - `--files file1.md,file2.md` - Analyze specific files only

```
- **Process**:
  1. Fetches changed files from PR
  2. Validates files exist locally
  3. Runs code review on PR files
  4. Optionally auto-submits comments
- **Output**: `review_pr{number}.json`
- **Auto-submit**: Use `--auto-submit` flag

## JSON Output Formats

### Review Output (Phase 1 & 3)
```json
{
  "findings": [
    {
      "severity": "high",
      "type": "bug",
      "count": 3,
      "comments": [
        {
          "file": "path/to/file.go",
          "lineNumber": 123,
          "issue": "Description of the issue",
          "details": "Detailed explanation",
          "suggestion": "Recommended fix"
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

### Implementation Output (Phase 2)
```json
{
  "implementations": [
    {
      "file": "path/to/file.go",
      "lineNumber": 123,
      "severity": "critical",
      "status": "implemented",
      "implementation": {
        "description": "What was changed",
        "filesModified": ["file1.go"],
        "approach": "How it was fixed"
      }
    }
  ],
  "summary": {
    "totalFindings": 14,
    "implemented": 9,
    "blocked": 1,
    "skipped": 4
  }
}
```

### Verification Output (Phase 3)
```json
{
  "implementationVerification": {
    "totalImplementations": 9,
    "verified": 8,

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

    "issuesFound": 1,
    "details": [...]
  },
  "findings": [...],
  "summary": {
    "totalNewFindings": 2
  }
}
```

## Common Usage Patterns

### 1. Review Local Files
```bash
# Single file
./review_workflow.sh review ./scheduler/scheduler.go

# Directory
./review_workflow.sh review ./handlers/v2/

# File list
echo "./file1.go" > files.txt
echo "./file2.go" >> files.txt
./review_workflow.sh review @files.txt
```

### 2. Review Pull Request
```bash
# Review PR and generate JSON
./review_workflow.sh review-pr 123

# Review and auto-submit comments
./review_workflow.sh review-pr 123 review_pr123.json --auto-submit

# Review with custom output file
./review_workflow.sh review-pr 123 my_review.json
```

### 3. Submit Comments to PR
```bash
# Submit all findings
./review_workflow.sh submit review1.json 123

# Preview without submitting
./submit_pr_comments.sh review1.json 123 --dry-run

# Only high severity
./submit_pr_comments.sh review1.json 123 --severity high

# Bugs and security only
./submit_pr_comments.sh review1.json 123 --type bug,security

# Exclude low severity
./submit_pr_comments.sh review1.json 123 --exclude-severity low
```

### 4. Complete Manual Workflow
```bash
# Phase 1: Review
./review_workflow.sh review @files.txt review1.json

# Phase 2: Implement

### 6. Documentation Analysis
```bash
# Analyze documentation for PR
./review_workflow.sh analyze-docs 123

# Force analysis (skip classification)
./review_workflow.sh analyze-docs 123 --force

# Analyze specific files only
./review_workflow.sh analyze-docs 123 --files README.md,docs/API.md
```

./review_workflow.sh implement review1.json implementation1.json

# Phase 3: Verify
./review_workflow.sh verify implementation1.json review1.json review2.json

# Phase 4: Submit to PR
./review_workflow.sh submit review2.json 123 --severity high,medium
```

### 5. Automated Workflow
```bash
# Auto-run with default 3 iterations
./review_workflow.sh auto @files.txt

# Custom max iterations
./review_workflow.sh auto ./src/ 5
```

## Comment Format Examples

### High Severity Bug
```markdown
🔴 **HIGH SEVERITY** | 🐛 **BUG**

**Issue:** Missing parameter in WHERE clause causes compilation error

**Details:** The WHERE clause has 'CreatedAt <= ?' but jobStartTime is not 
passed as a parameter to the Where() method. This will cause a runtime error 
or incorrect query execution.

**Suggestion:**
```go
Where("SCSendStatus IN(?, ?) AND CreatedAt <= ?", 
      models.UsageSCSendStatus.NOTSENT, 
      models.UsageSCSendStatus.FILE_SEND_FAILED, 
      jobStartTime)
```

---
*🤖 Generated by Fixium Code Review | Line 47*
```

### Medium Severity Maintainability
```markdown
🟡 **MEDIUM SEVERITY** | 🔧 **MAINTAINABILITY**

**Issue:** Complex nested logic reduces readability

**Details:** Multiple nested if statements make the code flow difficult to follow.

**Suggestion:** Extract logic into separate functions with descriptive names.

---
*🤖 Generated by Fixium Code Review | Line 89*
```

## GitHub Token Setup

### Required Scopes
- ✅ `repo` (full control of private repositories)
- ✅ `write:discussion` (for PR comments)

### Create Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select required scopes
4. Generate and copy token
5. Set as environment variable or in config file

### Security Best Practices
- Never commit tokens to version control
- Use `.gitignore` for `config/github.env.local`
- Rotate tokens regularly
- Use tokens with minimal required scopes
- Consider GitHub Apps for production environments

## Error Handling

### Automatic Retries
Failed API calls retry with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: 5 seconds delay
- Attempt 3: 10 seconds delay
- Attempt 4: 20 seconds delay

### Rate Limiting
- Checks rate limit before submission
- Warns when remaining requests < buffer
- Adds delays between batch submissions
- Respects rate limit reset times

### File Validation
- Validates files exist in PR diff
- Skips files not in PR with warning
- Reports skipped comments in summary

## Troubleshooting

### Token Issues
```bash
# Check token is set
echo $GITHUB_TOKEN

# Validate token
./lib/github_api.sh --validate-token

# Check rate limit
./lib/github_api.sh --rate-limit
```

### PR Not Found
```bash
# Verify PR exists
./lib/github_api.sh --pr-info owner repo 123

# Check repository settings
echo $GITHUB_OWNER
echo $GITHUB_REPO
```

### Fixium Not Found
```bash
# Check Fixium installation
which bob

# Verify Fixium is in PATH
echo $PATH
```

### File Not in PR
Files not in PR diff are automatically skipped:
```
⚠️  File not in PR (skipping): some/file.go
```
This is expected if review includes files not changed in the PR.

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Code Review
on: pull_request

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Fixium Review
        run: |
          ./review_workflow.sh review-pr ${{ github.event.pull_request.number }}
      
      - name: Submit PR Comments
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_OWNER: ${{ github.repository_owner }}
├── fixium/
│   ├── __init__.py
│   ├── main.py                    # Code review entry point
│   ├── doc_main.py                # Documentation analysis entry point
│   ├── github_client.py           # GitHub API client
│   ├── review_runner.py           # Code review orchestration
│   ├── doc_runner.py              # Documentation analysis orchestration
│   ├── doc_discoverer.py          # Documentation file discovery
│   ├── change_classifier.py       # PR change classification
│   ├── comment_parser.py          # Command parsing
│   ├── access_control.py          # Authorization
│   ├── error_handler.py           # Error handling
│   ├── progress_tracker.py        # Progress tracking
│   └── config.py                  # Configuration management
├── tests/
│   ├── test_doc_discoverer.py     # Doc discovery tests
│   ├── test_change_classifier.py  # Change classification tests
│   ├── test_doc_runner.py         # Doc runner tests
│   └── ...                        # Other test files
├── .github/
│   └── workflows/
│       └── fixium.yml             # GitHub Actions workflow
          GITHUB_REPO: ${{ github.event.repository.name }}
        run: |
          ./submit_pr_comments.sh review_pr${{ github.event.pull_request.number }}.json \
            ${{ github.event.pull_request.number }} \
            --severity high,medium
```

## Dependencies

- **bash** 4.0+ - Shell interpreter
- **jq** - JSON processor for parsing responses
- **curl** - HTTP client for API calls
- **git** - Repository operations
- **Fixium** - AI code review agent
- **GitHub Personal Access Token** - API authentication

## File Structure

```
code-review-workflow/
├── review_workflow.sh          # Main workflow orchestrator
├── submit_pr_comments.sh       # PR comment submission
├── lib/
│   ├── github_api.sh          # GitHub API client
│   └── comment_formatter.sh   # Comment formatting
├── prompts/
│   ├── review-workflow.md     # Review methodology
│   ├── code-review.md         # Review prompt
│   ├── implement-review-findings.md
│   ├── verify-implementations.md
│   └── code-review-post-fixes-check.md
├── config/
│   └── github.env             # Configuration file
├── README.md                  # Main documentation
├── README-pr-comments.md      # PR comments documentation
├── QUICKSTART-pr-comments.md  # Quick start guide
└── agents.md                  # This file
```

## Best Practices

1. **Use dry-run first** - Preview comments before submitting
2. **Filter appropriately** - Focus on critical issues first
3. **Batch wisely** - Default batch size (30) is optimal
4. **Monitor rate limits** - Check limits before large submissions
5. **Review PR files** - Ensure review covers files in the PR
6. **Iterate until clean** - Use auto workflow for complete cycles
7. **Version control outputs** - Track review/implementation JSONs
8. **Document decisions** - Use blocked/skipped reasons

## Benefits

- ✅ **Automated Reviews** - Consistent code quality checks
- ✅ **PR Integration** - Seamless GitHub workflow
- ✅ **Accountability** - Complete audit trail
- ✅ **Quality Assurance** - Catches issues introduced by fixes
- ✅ **Iterative Refinement** - Continues until code is clean
- ✅ **Flexible Filtering** - Focus on what matters
- ✅ **Batch Efficiency** - Optimized API usage
- ✅ **Version Control** - All artifacts tracked in git

## Related Documentation

- Main README: `README.md`
- PR Comments Guide: `README-pr-comments.md`
- Quick Start: `QUICKSTART-pr-comments.md`
- Prompts Documentation: `prompts/README.md`

## Maintenance

- **Last Updated**: 2026-05-07
- **Maintainer**: Development Team
- **Review Frequency**: As needed for workflow improvements
- **Version**: 1.0.0

## Support

For issues or questions:
1. Check this documentation
2. Review error messages and logs
3. Validate configuration (token, owner, repo)
4. Check GitHub API status
5. Review Fixium documentation
6. Contact repository maintainers