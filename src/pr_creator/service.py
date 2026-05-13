"""GitHub pull request creation service."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from github import Github

from src.models.pull_request import PRStatus, PullRequest


class PRCreator:
    """Create pull requests using a GitHub Personal Access Token."""

    def __init__(self, github_token: Optional[str] = None) -> None:
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN is required for PR creation")
        self.client = Github(self.github_token)

    @staticmethod
    def repo_name_from_url(repository_url: str) -> str:
        """Extract owner/repo from GitHub URL."""
        parsed = urlparse(repository_url)
        repo_path = parsed.path.strip("/")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]
        if "/" not in repo_path:
            raise ValueError("Repository URL must include owner/repo")
        return repo_path

    def create_pull_request(
        self,
        repository_url: str,
        branch_name: str,
        title: str,
        body: str,
        base_branch: str = "main",
        fix_proposal_id: str = "",
    ) -> PullRequest:
        """Open a pull request for a previously pushed branch."""
        repo_name = self.repo_name_from_url(repository_url)
        repo = self.client.get_repo(repo_name)
        pull_request = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=base_branch,
        )

        return PullRequest(
            fix_proposal_id=fix_proposal_id,
            repository=repo_name,
            branch_name=branch_name,
            pr_number=pull_request.number,
            pr_url=pull_request.html_url,
            status=PRStatus.CREATED,
            created_at=datetime.utcnow(),
        )


# Made with Bob