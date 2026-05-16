"""Configuration management for Fixium."""
import os
from typing import Optional


class Config:
    """Centralized configuration for Fixium."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # GitHub configuration
        self.github_token = os.getenv('GITHUB_TOKEN') or os.getenv('MY_GITHUB_TOKEN')
        self.github_repository = os.getenv('GITHUB_REPOSITORY')
        self.github_owner = os.getenv('GITHUB_OWNER')
        self.github_repo = os.getenv('GITHUB_REPO')
        
        # Fixium configuration
        self.bob_api_key = os.getenv('BOBSHELL_API_KEY')
        self.authorized_users = os.getenv('FIXIUM_AUTHORIZED_USERS', '')
        
        # PR context
        self.pr_number = self._get_int_env('PR_NUMBER')
        self.comment_body = os.getenv('COMMENT_BODY')
        self.comment_user = os.getenv('COMMENT_USER')
        
        # Operational settings
        self.max_comments_per_batch = self._get_int_env('MAX_COMMENTS_PER_BATCH', 30)
        self.rate_limit_buffer = self._get_int_env('RATE_LIMIT_BUFFER', 10)
        self.review_timeout = self._get_int_env('REVIEW_TIMEOUT', 1800)  # 30 minutes
        
        # Workspace
        self.workspace_dir = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    
    @staticmethod
    def _get_int_env(key: str, default: Optional[int] = None) -> Optional[int]:
        """Get integer environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def validate(self) -> list[str]:
        """
        Validate required configuration.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not self.github_token:
            errors.append("GITHUB_TOKEN or MY_GITHUB_TOKEN is required")
        
        if not self.github_repository:
            errors.append("GITHUB_REPOSITORY is required")
        
        if not self.pr_number:
            errors.append("PR_NUMBER is required")
        
        if not self.comment_body:
            errors.append("COMMENT_BODY is required")
        
        if not self.comment_user:
            errors.append("COMMENT_USER is required")
        
        return errors
    
    def __repr__(self) -> str:
        """String representation (safe - no secrets)."""
        return (
            f"Config(repository={self.github_repository}, "
            f"pr_number={self.pr_number}, "
            f"user={self.comment_user})"
        )

# Made with Bob
