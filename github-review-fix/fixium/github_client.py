"""GitHub API client for Fixium."""
from typing import Any, Optional
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.IssueComment import IssueComment
from github.Repository import Repository
import os


class GitHubClient:
    """GitHub API client wrapper using PyGithub."""
    
    def __init__(self, token: Optional[str] = None, repository: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (defaults to GITHUB_TOKEN or MY_GITHUB_TOKEN env var)
            repository: Repository in format 'owner/repo' (defaults to GITHUB_REPOSITORY env var)
        """
        self.token = token or os.getenv('GITHUB_TOKEN') or os.getenv('MY_GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token not provided (GITHUB_TOKEN or MY_GITHUB_TOKEN)")
        
        self.client = Github(self.token)
        self.repo_name = repository or os.getenv('GITHUB_REPOSITORY')
        if not self.repo_name:
            raise ValueError("GITHUB_REPOSITORY not set")
        
        self.repo: Repository = self.client.get_repo(self.repo_name)
    
    def get_pull_request(self, pr_number: int) -> PullRequest:
        """
        Get pull request by number.
        
        Args:
            pr_number: PR number
            
        Returns:
            PullRequest object
        """
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
        Update an existing PR issue comment.

        Uses a version-compatible lookup path by enumerating repository issues
        and matching the stored comment ID against each issue's comments.

        Args:
            comment_id: Comment ID
            body: New comment body (markdown)
        """
        for issue in self.repo.get_issues(state='all'):
            for comment in issue.get_comments():
                if comment.id == comment_id:
                    comment.edit(body)
                    return

        raise ValueError(f"Comment not found: {comment_id}")
    
    def get_pr_files(self, pr_number: int) -> list[str]:
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
            Dict with 'remaining', 'limit', and 'reset' keys
        """
        rate_limit = self.client.get_rate_limit()
        return {
            'remaining': rate_limit.core.remaining,
            'limit': rate_limit.core.limit,
            'reset': rate_limit.core.reset
        }
    
    def is_user_authorized(self, username: str, authorized_users: list[str]) -> bool:
        """
        Check if user is authorized.
        
        Args:
            username: GitHub username
            authorized_users: List of authorized usernames
            
        Returns:
            True if authorized
        """
        return username.lower() in [u.lower() for u in authorized_users]
    
    def get_user(self, username: str):
        """
        Get user information.
        
        Args:
            username: GitHub username
            
        Returns:
            User object
        """
        return self.client.get_user(username)
    
    def get_review_comment(self, comment_id: int) -> dict[str, Any]:
        """
        Get a pull request review comment by ID.

        Args:
            comment_id: Pull request review comment ID

        Returns:
            Review comment payload as a dictionary

        Raises:
            ValueError: If the review comment cannot be found
        """
        # Iterate through all pull requests to find the review comment
        for pr in self.repo.get_pulls(state='all'):
            try:
                for comment in pr.get_review_comments():
                    if comment.id == comment_id:
                        return comment.raw_data
            except GithubException:
                # Skip PRs that can't be accessed
                continue
        
        raise ValueError(f"Review comment not found: {comment_id}")

    def close(self):
        """Close the GitHub client connection."""
        # PyGithub doesn't require explicit closing, but good practice
        pass

# Made with Bob
