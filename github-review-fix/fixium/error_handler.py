"""Error handling for Fixium."""
from .github_client import GitHubClient
from .progress_tracker import ProgressTracker
from typing import Optional


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
Fixium:review --severity high --exclude-type maintainability
```

**Available filter options:**
- `--severity critical,high,medium,low` - Filter by severity
- `--type bug,security,maintainability,performance` - Filter by type
- `--exclude-severity low` - Exclude specific severities
- `--exclude-type maintainability` - Exclude specific types

---
*🤖 Fixium Code Review Bot*"""
        self.client.post_comment(self.pr_number, message)
    
    def handle_invalid_filters(self, errors: list[str]) -> None:
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
```

---
*🤖 Fixium Code Review Bot*"""
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
```

---
*🤖 Fixium Code Review Bot*"""
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
- Try again in a few minutes

---
*🤖 Fixium Code Review Bot*"""
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
- Check GitHub API status at https://www.githubstatus.com
- Contact administrator if issue persists

---
*🤖 Fixium Code Review Bot*"""
        progress.error("Submission Error", message)
    
    def handle_unexpected_error(self, error_details: str, progress: Optional[ProgressTracker] = None) -> None:
        """Handle unexpected error."""
        message = f"""❌ **Unexpected Error**

An unexpected error occurred during the review.

**Details:**
```
{error_details[:500]}
```

Please try again or contact support if the issue persists.

---
*🤖 Fixium Code Review Bot*"""
        
        if progress:
            progress.error("Unexpected Error", error_details[:500])
        else:
            self.client.post_comment(self.pr_number, message)
    
    def handle_configuration_error(self, errors: list[str]) -> None:
        """Handle configuration validation errors."""
        error_list = '\n'.join(f"- {e}" for e in errors)
        
        message = f"""❌ **Configuration Error**

Required configuration is missing or invalid:

{error_list}

**Required environment variables:**
- `GITHUB_TOKEN` or `MY_GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_REPOSITORY` - Repository in format 'owner/repo'
- `PR_NUMBER` - Pull request number
- `COMMENT_BODY` - Comment text
- `COMMENT_USER` - Comment author username

Please check the GitHub Actions workflow configuration.

---
*🤖 Fixium Code Review Bot*"""
        self.client.post_comment(self.pr_number, message)

# Made with Bob
