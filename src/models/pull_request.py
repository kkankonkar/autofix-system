"""Pull request data model."""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PRStatus(str, Enum):
    """Pull request status."""
    CREATED = "CREATED"
    MERGED = "MERGED"
    CLOSED = "CLOSED"


class PullRequest(BaseModel):
    """Represents a pull request."""
    
    fix_proposal_id: str = Field(..., description="ID of the fix proposal")
    repository: str = Field(..., description="Repository name (org/repo)")
    branch_name: str = Field(..., description="Branch name for the fix")
    pr_number: int = Field(..., description="Pull request number")
    pr_url: str = Field(..., description="Pull request URL")
    status: PRStatus = Field(..., description="PR status")
    created_at: datetime = Field(..., description="When the PR was created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fix_proposal_id": "log-123456",
                "repository": "org/my-web-app",
                "branch_name": "autofix/log-123456",
                "pr_number": 42,
                "pr_url": "https://github.com/org/my-web-app/pull/42",
                "status": "CREATED",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

# Made with Bob
