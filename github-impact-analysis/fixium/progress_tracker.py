"""Progress tracking for Fixium reviews."""
from typing import Optional
from datetime import datetime, timezone
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
        self.start_time = datetime.now(timezone.utc)
    
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

⏳ This may take a few minutes depending on the size of the PR.

---
*🤖 Fixium Code Review Bot*"""
        
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
        
        elapsed = int((datetime.now(timezone.utc) - self.start_time).total_seconds())
        
        body = f"""🔍 **Fixium Code Review In Progress**

**Status:** {status}
**Elapsed:** {elapsed}s

{details}

---
*🤖 Fixium Code Review Bot*"""
        
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
        
        elapsed = int((datetime.now(timezone.utc) - self.start_time).total_seconds())
        
        if total_findings == 0:
            body = f"""✅ **Fixium Code Review Complete**

**Result:** No issues found - code looks good! 🎉
**Duration:** {elapsed}s

Great job maintaining code quality!

---
*🤖 Fixium Code Review Bot*"""
        else:
            body = f"""✅ **Fixium Code Review Complete**

**Findings:** {total_findings} issue(s) found
**Duration:** {elapsed}s

{summary}

📝 Review the inline comments below for details and suggestions.

---
*🤖 Fixium Code Review Bot*"""
        
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

Please try again or contact support if the issue persists.

---
*🤖 Fixium Code Review Bot*"""
            self.client.post_comment(self.pr_number, body)
        else:
            # Update existing progress comment
            elapsed = int((datetime.now(timezone.utc) - self.start_time).total_seconds())
            
            body = f"""❌ **Fixium Code Review Failed**

**Error:** {error_type}
**Duration:** {elapsed}s

{error_details}

Please try again or contact support if the issue persists.

---
*🤖 Fixium Code Review Bot*"""
            self.client.update_comment(self.comment_id, body)
    
    def get_elapsed_time(self) -> int:
        """
        Get elapsed time in seconds.
        
        Returns:
            Elapsed seconds since start
        """
        return int((datetime.now(timezone.utc) - self.start_time).total_seconds())

# Made with Bob
