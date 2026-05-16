"""GitHub API client for Fixium."""
from typing import Optional, List
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.IssueComment import IssueComment
from github.Issue import Issue
from github.Repository import Repository
import os
import requests


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
        Update an existing comment.
        
        Args:
            comment_id: Comment ID
            body: New comment body (markdown)
        """
        # PyGithub doesn't have a direct method to get comment by ID
        # Use GitHub REST API directly
        url = f"https://api.github.com/repos/{self.repo_name}/issues/comments/{comment_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        response = requests.patch(url, json={"body": body}, headers=headers)
        response.raise_for_status()
    
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
    
    def get_issue(self, issue_number: int) -> Issue:
        """
        Get issue by number.
        
        Args:
            issue_number: Issue number
            
        Returns:
            Issue object
        """
        return self.repo.get_issue(issue_number)
    
    def post_issue_comment(self, issue_number: int, body: str) -> IssueComment:
        """
        Post a comment on an issue.
        
        Args:
            issue_number: Issue number
            body: Comment body (markdown)
            
        Returns:
            Created comment object
        """
        issue = self.get_issue(issue_number)
        return issue.create_comment(body)
    
    def get_commit_messages(self, pr_number: int) -> List[str]:
        """
        Get commit messages from a PR.
        
        Args:
            pr_number: PR number
            
        Returns:
            List of commit messages
        """
        pr = self.get_pull_request(pr_number)
        return [commit.commit.message for commit in pr.get_commits()]
        return self.client.get_user(username)
    
    def close(self):
        """Close the GitHub client connection."""
        # PyGithub doesn't require explicit closing, but good practice
        pass

# Made with Bob
