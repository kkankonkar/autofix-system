# Fixium Python Implementation Guide

## Architecture: Hybrid Python + Shell

### Why Hybrid?
- **Python**: Better for API interactions, JSON processing, logic, and testing
- **Shell**: Keep for Bob Shell invocation (already works well) and git operations
- **Best of Both**: Leverage strengths of each language

### Language Breakdown

**Python Components** (70% of codebase):
- ✅ Comment parsing and validation
- ✅ GitHub API client (using PyGithub)
- ✅ Access control and authorization
- ✅ Progress tracking and updates
- ✅ Error handling and messaging
- ✅ JSON processing and filtering
- ✅ Unit testing with pytest
- ✅ Main orchestration logic

**Shell Components** (30% of codebase):
- ✅ Bob Shell invocation (`bob -p "..."`)
- ✅ Git operations (checkout, diff, etc.)
- ✅ File system operations
- ✅ Existing `review_workflow.sh` wrapper

---

## Project Structure

```
code-review-workflow/
├── fixium/                          # NEW: Python package
│   ├── __init__.py
│   ├── main.py                      # Main orchestrator
│   ├── comment_parser.py            # Parse PR comments
│   ├── github_client.py             # GitHub API wrapper
│   ├── access_control.py            # Authorization logic
│   ├── progress_tracker.py          # Progress comments
│   ├── error_handler.py             # Error handling
│   ├── config.py                    # Configuration
│   └── review_runner.py             # Bob Shell wrapper
├── lib/                             # Keep shell scripts
│   ├── review_wrapper.sh            # Wrapper for bob shell
│   └── git_operations.sh            # Git commands
├── tests/                           # NEW: Python tests
│   ├── __init__.py
│   ├── test_comment_parser.py
│   ├── test_github_client.py
│   ├── test_access_control.py
│   └── test_progress_tracker.py
├── review_workflow.sh               # Keep existing
├── submit_pr_comments.sh            # Keep existing
├── requirements.txt                 # NEW: Python dependencies
├── pytest.ini                       # NEW: Test configuration
└── Dockerfile                       # Updated for Python
```

---

## Python Modules

### 1. Comment Parser (`fixium/comment_parser.py`)

**Purpose**: Parse Fixium commands from PR comments

```python
"""Parse Fixium commands from PR comments."""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FilterOptions:
    """Filter options for code review."""
    severity: Optional[List[str]] = None
    type: Optional[List[str]] = None
    exclude_severity: Optional[List[str]] = None
    exclude_type: Optional[List[str]] = None
    
    def to_cli_args(self) -> List[str]:
        """Convert to CLI arguments for submit_pr_comments.sh."""
        args = []
        if self.severity:
            args.extend(['--severity', ','.join(self.severity)])
        if self.type:
            args.extend(['--type', ','.join(self.type)])
        if self.exclude_severity:
            args.extend(['--exclude-severity', ','.join(self.exclude_severity)])
        if self.exclude_type:
            args.extend(['--exclude-type', ','.join(self.exclude_type)])
        return args
    
    def __str__(self) -> str:
        """Human-readable filter description."""
        parts = []
        if self.severity:
            parts.append(f"Severity: {', '.join(self.severity)}")
        if self.type:
            parts.append(f"Type: {', '.join(self.type)}")
        if self.exclude_severity:
            parts.append(f"Excluding severity: {', '.join(self.exclude_severity)}")
        if self.exclude_type:
            parts.append(f"Excluding type: {', '.join(self.exclude_type)}")
        return ' | '.join(parts) if parts else "No filters"


@dataclass
class FixiumCommand:
    """Parsed Fixium command."""
    command: str
    filters: FilterOptions
    raw_comment: str
    
    def is_valid(self) -> bool:
        """Check if command is valid."""
        return self.command in ['review']  # Add more commands later


class CommentParser:
    """Parser for Fixium PR comments."""
    
    COMMAND_PATTERN = r'Fixium:(\w+)'
    SEVERITY_PATTERN = r'--severity\s+([^\s]+)'
    TYPE_PATTERN = r'--type\s+([^\s]+)'
    EXCLUDE_SEVERITY_PATTERN = r'--exclude-severity\s+([^\s]+)'
    EXCLUDE_TYPE_PATTERN = r'--exclude-type\s+([^\s]+)'
    
    VALID_SEVERITIES = {'critical', 'high', 'medium', 'low'}
    VALID_TYPES = {'bug', 'security', 'maintainability', 'performance'}
    
    @classmethod
    def parse(cls, comment_body: str) -> Optional[FixiumCommand]:
        """
        Parse Fixium command from comment body.
        
        Args:
            comment_body: The PR comment text
            
        Returns:
            FixiumCommand if valid command found, None otherwise
        """
        # Extract command
        command_match = re.search(cls.COMMAND_PATTERN, comment_body, re.IGNORECASE)
        if not command_match:
            return None
        
        command = command_match.group(1).lower()
        
        # Extract filter options
        filters = FilterOptions(
            severity=cls._parse_list_option(comment_body, cls.SEVERITY_PATTERN),
            type=cls._parse_list_option(comment_body, cls.TYPE_PATTERN),
            exclude_severity=cls._parse_list_option(comment_body, cls.EXCLUDE_SEVERITY_PATTERN),
            exclude_type=cls._parse_list_option(comment_body, cls.EXCLUDE_TYPE_PATTERN)
        )
        
        return FixiumCommand(
            command=command,
            filters=filters,
            raw_comment=comment_body
        )
    
    @classmethod
    def _parse_list_option(cls, text: str, pattern: str) -> Optional[List[str]]:
        """Parse comma-separated list option."""
        match = re.search(pattern, text)
        if not match:
            return None
        
        values = [v.strip().lower() for v in match.group(1).split(',')]
        return values if values else None
    
    @classmethod
    def validate_filters(cls, filters: FilterOptions) -> List[str]:
        """
        Validate filter options.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate severity values
        if filters.severity:
            invalid = set(filters.severity) - cls.VALID_SEVERITIES
            if invalid:
                errors.append(f"Invalid severity values: {', '.join(invalid)}")
        
        if filters.exclude_severity:
            invalid = set(filters.exclude_severity) - cls.VALID_SEVERITIES
            if invalid:
                errors.append(f"Invalid exclude-severity values: {', '.join(invalid)}")
        
        # Validate type values
        if filters.type:
            invalid = set(filters.type) - cls.VALID_TYPES
            if invalid:
                errors.append(f"Invalid type values: {', '.join(invalid)}")
        
        if filters.exclude_type:
            invalid = set(filters.exclude_type) - cls.VALID_TYPES
            if invalid:
                errors.append(f"Invalid exclude-type values: {', '.join(invalid)}")
        
        return errors
```

### 2. GitHub Client (`fixium/github_client.py`)

**Purpose**: Wrapper around PyGithub for GitHub API operations

```python
"""GitHub API client for Fixium."""
from typing import Optional, List
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.IssueComment import IssueComment
import os


class GitHubClient:
    """GitHub API client wrapper."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token not provided")
        
        self.client = Github(self.token)
        self.repo_name = os.getenv('GITHUB_REPOSITORY')
        if not self.repo_name:
            raise ValueError("GITHUB_REPOSITORY not set")
        
        self.repo = self.client.get_repo(self.repo_name)
    
    def get_pull_request(self, pr_number: int) -> PullRequest:
        """Get pull request by number."""
        return self.repo.get_pull(pr_number)
    
    def post_comment(self, pr_number: int, body: str) -> IssueComment:
        """
        Post a comment on a pull request.
        
        Args:
            pr_number: PR number
            body: Comment body (markdown)
            
        Returns:
            Created comment object
        """
        pr = self.get_pull_request(pr_number)
        return pr.as_issue().create_comment(body)
    
    def update_comment(self, comment_id: int, body: str) -> None:
        """
        Update an existing comment.
        
        Args:
            comment_id: Comment ID
            body: New comment body (markdown)
        """
        comment = self.repo.get_issue_comment(comment_id)
        comment.edit(body)
    
    def get_pr_files(self, pr_number: int) -> List[str]:
        """
        Get list of files changed in PR.
        
        Args:
            pr_number: PR number
            
        Returns:
            List of file paths
        """
        pr = self.get_pull_request(pr_number)
        return [f.filename for f in pr.get_files()]
    
    def check_rate_limit(self) -> dict:
        """
        Check GitHub API rate limit.
        
        Returns:
            Dict with 'remaining' and 'limit' keys
        """
        rate_limit = self.client.get_rate_limit()
        return {
            'remaining': rate_limit.core.remaining,
            'limit': rate_limit.core.limit,
            'reset': rate_limit.core.reset
        }
    
    def is_user_authorized(self, username: str, authorized_users: List[str]) -> bool:
        """
        Check if user is authorized.
        
        Args:
            username: GitHub username
            authorized_users: List of authorized usernames
            
        Returns:
            True if authorized
        """
        return username.lower() in [u.lower() for u in authorized_users]
```

### 3. Progress Tracker (`fixium/progress_tracker.py`)

**Purpose**: Manage progress comments during review

```python
"""Progress tracking for Fixium reviews."""
from typing import Optional
from datetime import datetime
from .github_client import GitHubClient


class ProgressTracker:
    """Track and update review progress via PR comments."""
    
    def __init__(self, github_client: GitHubClient, pr_number: int):
        """
        Initialize progress tracker.
        
        Args:
            github_client: GitHub API client
            pr_number: Pull request number
        """
        self.client = github_client
        self.pr_number = pr_number
        self.comment_id: Optional[int] = None
        self.start_time = datetime.now()
    
    def start(self, filter_info: str) -> int:
        """
        Post initial progress comment.
        
        Args:
            filter_info: Human-readable filter description
            
        Returns:
            Comment ID
        """
        body = f"""🔍 **Fixium Code Review Started**

**Status:** Analyzing PR files...
**Filters:** {filter_info}
**Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}

⏳ This may take a few minutes depending on the size of the PR."""
        
        comment = self.client.post_comment(self.pr_number, body)
        self.comment_id = comment.id
        return self.comment_id
    
    def update(self, status: str, details: str = "") -> None:
        """
        Update progress comment.
        
        Args:
            status: Current status message
            details: Additional details (optional)
        """
        if not self.comment_id:
            raise ValueError("Progress not started - call start() first")
        
        elapsed = (datetime.now() - self.start_time).seconds
        
        body = f"""🔍 **Fixium Code Review In Progress**

**Status:** {status}
**Elapsed:** {elapsed}s

{details}"""
        
        self.client.update_comment(self.comment_id, body)
    
    def complete(self, total_findings: int, summary: str) -> None:
        """
        Finalize progress comment with results.
        
        Args:
            total_findings: Total number of findings
            summary: Summary statistics
        """
        if not self.comment_id:
            raise ValueError("Progress not started - call start() first")
        
        elapsed = (datetime.now() - self.start_time).seconds
        
        if total_findings == 0:
            body = f"""✅ **Fixium Code Review Complete**

**Result:** No issues found - code looks good! 🎉
**Duration:** {elapsed}s

Great job maintaining code quality!"""
        else:
            body = f"""✅ **Fixium Code Review Complete**

**Findings:** {total_findings} issue(s) found
**Duration:** {elapsed}s

{summary}

📝 Review the inline comments below for details and suggestions."""
        
        self.client.update_comment(self.comment_id, body)
    
    def error(self, error_type: str, error_details: str) -> None:
        """
        Post error message.
        
        Args:
            error_type: Type of error
            error_details: Detailed error message
        """
        if not self.comment_id:
            # If we haven't started, post new comment
            body = f"""❌ **Fixium Code Review Failed**

**Error:** {error_type}

{error_details}

Please try again or contact support if the issue persists."""
            self.client.post_comment(self.pr_number, body)
        else:
            # Update existing progress comment
            body = f"""❌ **Fixium Code Review Failed**

**Error:** {error_type}

{error_details}

Please try again or contact support if the issue persists."""
            self.client.update_comment(self.comment_id, body)
```

### 4. Access Control (`fixium/access_control.py`)

**Purpose**: Handle user authorization

```python
"""Access control for Fixium."""
from typing import List
import os


class AccessControl:
    """Manage user authorization."""
    
    def __init__(self, authorized_users: str = None):
        """
        Initialize access control.
        
        Args:
            authorized_users: Comma-separated list of GitHub usernames
                            (defaults to FIXIUM_AUTHORIZED_USERS env var)
        """
        users_str = authorized_users or os.getenv('FIXIUM_AUTHORIZED_USERS', '')
        self.authorized_users = [
            u.strip().lower() 
            for u in users_str.split(',') 
            if u.strip()
        ]
    
    def is_authorized(self, username: str) -> bool:
        """
        Check if user is authorized.
        
        Args:
            username: GitHub username
            
        Returns:
            True if authorized
        """
        return username.lower() in self.authorized_users
    
    def get_unauthorized_message(self, username: str) -> str:
        """
        Get message for unauthorized user.
        
        Args:
            username: GitHub username
            
        Returns:
            Markdown formatted message
        """
        return f"""@{username} Sorry, you are not authorized to trigger Fixium reviews.

**To request access:**
Contact a repository administrator to add your username to the authorized users list.

**Current authorized users:** {len(self.authorized_users)} user(s)"""
```

### 5. Review Runner (`fixium/review_runner.py`)

**Purpose**: Wrapper for Bob Shell execution

```python
"""Review runner - wrapper for Bob Shell."""
import subprocess
import os
from typing import List, Optional
from pathlib import Path


class ReviewRunner:
    """Execute Bob Shell reviews."""
    
    def __init__(self, workspace_dir: str = None):
        """
        Initialize review runner.
        
        Args:
            workspace_dir: Working directory (defaults to current dir)
        """
        self.workspace_dir = workspace_dir or os.getcwd()
    
    def run_review(
        self, 
        pr_number: int, 
        output_file: str,
        timeout: int = 1800  # 30 minutes default
    ) -> bool:
        """
        Run code review using review_workflow.sh.
        
        Args:
            pr_number: Pull request number
            output_file: Output JSON file path
            timeout: Timeout in seconds
            
        Returns:
            True if successful
        """
        script_path = Path(self.workspace_dir) / 'review_workflow.sh'
        
        cmd = [
            str(script_path),
            'review-pr',
            str(pr_number),
            output_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return True
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Review timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Review failed: {e.stderr}")
    
    def submit_comments(
        self,
        review_file: str,
        pr_number: int,
        filter_args: List[str]
    ) -> bool:
        """
        Submit review comments to PR.
        
        Args:
            review_file: Review JSON file
            pr_number: Pull request number
            filter_args: Filter arguments (e.g., ['--severity', 'high'])
            
        Returns:
            True if successful
        """
        script_path = Path(self.workspace_dir) / 'submit_pr_comments.sh'
        
        cmd = [
            str(script_path),
            review_file,
            str(pr_number)
        ] + filter_args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Comment submission failed: {e.stderr}")
```

### 6. Main Orchestrator (`fixium/main.py`)

**Purpose**: Main entry point that orchestrates the workflow

```python
"""Main entry point for Fixium."""
import os
import sys
import json
from pathlib import Path

from .comment_parser import CommentParser
from .github_client import GitHubClient
from .access_control import AccessControl
from .progress_tracker import ProgressTracker
from .review_runner import ReviewRunner
from .error_handler import ErrorHandler


def main():
    """Main Fixium workflow."""
    # Get environment variables
    pr_number = int(os.getenv('PR_NUMBER'))
    comment_body = os.getenv('COMMENT_BODY')
    comment_user = os.getenv('COMMENT_USER')
    
    # Initialize components
    github_client = GitHubClient()
    access_control = AccessControl()
    error_handler = ErrorHandler(github_client, pr_number)
    
    try:
        # Parse command
        command = CommentParser.parse(comment_body)
        if not command or not command.is_valid():
            error_handler.handle_invalid_command(comment_body)
            sys.exit(1)
        
        # Check authorization
        if not access_control.is_authorized(comment_user):
            message = access_control.get_unauthorized_message(comment_user)
            github_client.post_comment(pr_number, message)
            sys.exit(1)
        
        # Validate filters
        errors = CommentParser.validate_filters(command.filters)
        if errors:
            error_handler.handle_invalid_filters(errors)
            sys.exit(1)
        
        # Start progress tracking
        progress = ProgressTracker(github_client, pr_number)
        filter_info = str(command.filters)
        progress.start(filter_info)
        
        # Run review
        progress.update("Running code review...", "Analyzing PR files")
        
        review_runner = ReviewRunner()
        output_file = f"review_pr{pr_number}.json"
        
        try:
            review_runner.run_review(pr_number, output_file)
        except TimeoutError as e:
            error_handler.handle_timeout(progress)
            sys.exit(1)
        except RuntimeError as e:
            error_handler.handle_review_error(progress, str(e))
            sys.exit(1)
        
        # Submit comments
        progress.update("Submitting review comments...", "Posting findings to PR")
        
        filter_args = command.filters.to_cli_args()
        try:
            review_runner.submit_comments(output_file, pr_number, filter_args)
        except RuntimeError as e:
            error_handler.handle_submission_error(progress, str(e))
            sys.exit(1)
        
        # Get summary
        with open(output_file) as f:
            review_data = json.load(f)
        
        total_findings = review_data.get('summary', {}).get('totalFindings', 0)
        summary = format_summary(review_data)
        
        # Complete
        progress.complete(total_findings, summary)
        
    except Exception as e:
        error_handler.handle_unexpected_error(str(e))
        sys.exit(1)


def format_summary(review_data: dict) -> str:
    """Format review summary."""
    summary = review_data.get('summary', {})
    
    parts = []
    if summary.get('critical', 0) > 0:
        parts.append(f"🔴 Critical: {summary['critical']}")
    if summary.get('high', 0) > 0:
        parts.append(f"🔴 High: {summary['high']}")
    if summary.get('medium', 0) > 0:
        parts.append(f"🟡 Medium: {summary['medium']}")
    if summary.get('low', 0) > 0:
        parts.append(f"🔵 Low: {summary['low']}")
    
    return ' | '.join(parts) if parts else "No issues found"


if __name__ == '__main__':
    main()
```

### 7. Error Handler (`fixium/error_handler.py`)

**Purpose**: Centralized error handling

```python
"""Error handling for Fixium."""
from .github_client import GitHubClient
from .progress_tracker import ProgressTracker


class ErrorHandler:
    """Handle errors with user-friendly messages."""
    
    def __init__(self, github_client: GitHubClient, pr_number: int):
        """
        Initialize error handler.
        
        Args:
            github_client: GitHub API client
            pr_number: Pull request number
        """
        self.client = github_client
        self.pr_number = pr_number
    
    def handle_invalid_command(self, comment_body: str) -> None:
        """Handle invalid command."""
        message = f"""❌ **Invalid Fixium Command**

The comment does not contain a valid Fixium command.

**Valid commands:**
- `Fixium:review` - Run code review
- `Fixium:review --severity high` - Review with filters

**Your comment:**
```
{comment_body[:200]}
```

**Examples:**
```
Fixium:review
Fixium:review --severity high,medium
Fixium:review --type bug,security
```"""
        self.client.post_comment(self.pr_number, message)
    
    def handle_invalid_filters(self, errors: list) -> None:
        """Handle invalid filter options."""
        error_list = '\n'.join(f"- {e}" for e in errors)
        
        message = f"""❌ **Invalid Filter Options**

The filter options provided are not valid:

{error_list}

**Valid options:**
- `--severity critical,high,medium,low`
- `--type bug,security,maintainability,performance`
- `--exclude-severity low`
- `--exclude-type maintainability`

**Example:**
```
Fixium:review --severity high --type bug,security
```"""
        self.client.post_comment(self.pr_number, message)
    
    def handle_timeout(self, progress: ProgressTracker) -> None:
        """Handle review timeout."""
        message = """Review taking too long, please try with smaller scope

**Suggestions:**
- Try reviewing specific files instead of the entire PR
- Break the PR into smaller chunks
- Use severity filters to focus on critical issues first

**Example:**
```
Fixium:review --severity high
```"""
        progress.error("Review Timeout", message)
    
    def handle_review_error(self, progress: ProgressTracker, error_details: str) -> None:
        """Handle review execution error."""
        message = f"""The code analysis engine encountered an error.

**Details:**
```
{error_details[:500]}
```

**Suggestions:**
- Check if the code compiles successfully
- Verify all dependencies are available
- Try again in a few minutes"""
        progress.error("Analysis Error", message)
    
    def handle_submission_error(self, progress: ProgressTracker, error_details: str) -> None:
        """Handle comment submission error."""
        message = f"""Failed to submit review comments.

**Details:**
```
{error_details[:500]}
```

**Possible causes:**
- GitHub API rate limit reached
- Network connectivity issues
- Permission issues

**Suggestions:**
- Wait a few minutes and try again
- Check GitHub API status
- Contact administrator if issue persists"""
        progress.error("Submission Error", message)
    
    def handle_unexpected_error(self, error_details: str) -> None:
        """Handle unexpected error."""
        message = f"""❌ **Unexpected Error**

An unexpected error occurred during the review.

**Details:**
```
{error_details[:500]}
```

Please try again or contact support if the issue persists."""
        self.client.post_comment(self.pr_number, message)
```

---

## Dependencies (`requirements.txt`)

```txt
PyGithub==2.1.1
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
```

---

## Updated Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install bob CLI
# TODO: Add actual bob installation method

# Set working directory
WORKDIR /fixium

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Fixium code
COPY . .

# Make shell scripts executable
RUN chmod +x /fixium/*.sh /fixium/lib/*.sh

# Set Python path
ENV PYTHONPATH=/fixium

# Set entrypoint to Python main
ENTRYPOINT ["python", "-m", "fixium.main"]
```

---

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fixium --cov-report=html

# Run specific test file
pytest tests/test_comment_parser.py

# Run with verbose output
pytest -v
```

### Test Structure
```
tests/
├── __init__.py
├── test_comment_parser.py      # Comment parsing tests
├── test_github_client.py       # GitHub API tests (mocked)
├── test_access_control.py      # Authorization tests
├── test_progress_tracker.py    # Progress tracking tests
└── test_review_runner.py       # Review execution tests
```

---

## Benefits of Python Implementation

1. **Better Testing**: pytest provides excellent testing framework
2. **Cleaner Code**: Python's syntax is more readable than bash
3. **Better Error Handling**: Python exceptions vs bash exit codes
4. **JSON Processing**: Native JSON support, no jq needed
5. **API Clients**: PyGithub provides clean GitHub API interface
6. **Type Hints**: Better code documentation and IDE support
7. **Easier Maintenance**: More developers familiar with Python
8. **Better Debugging**: Python debuggers are more powerful

---

## Migration Strategy

1. **Phase 1**: Implement Python modules alongside existing shell scripts
2. **Phase 2**: Test Python implementation thoroughly
3. **Phase 3**: Switch Docker entrypoint to Python main
4. **Phase 4**: Keep shell scripts for Bob Shell invocation
5. **Phase 5**: Gradually migrate remaining shell logic to Python

---

## Next Steps

1. Create Python package structure
2. Implement core modules (parser, client, etc.)
3. Write comprehensive tests
4. Update Dockerfile
5. Test locally with Docker
6. Deploy to GitHub Actions
7. Monitor and iterate
