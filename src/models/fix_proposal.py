"""Fix proposal data model."""

from pydantic import BaseModel, Field
from typing import List


class FixProposal(BaseModel):
    """Represents a proposed fix for an error."""
    
    analysis_id: str = Field(..., description="ID of the error analysis")
    original_code: str = Field(..., description="Original code with the error")
    fixed_code: str = Field(..., description="Fixed code")
    explanation: str = Field(..., description="Explanation of the fix")
    commit_message: str = Field(..., description="Commit message for the fix")
    pr_description: str = Field(..., description="Pull request description")
    test_suggestions: List[str] = Field(default_factory=list, description="Suggested tests")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "log-123456",
                "original_code": "const user = data.user;\nconsole.log(user.name);",
                "fixed_code": "const user = data?.user;\nif (user) {\n  console.log(user.name);\n}",
                "explanation": "Added null check to prevent accessing property on undefined",
                "commit_message": "Fix: Add null check for user object access",
                "pr_description": "## Problem\nTypeError when accessing user.name on undefined object\n\n## Solution\nAdded optional chaining and null check",
                "test_suggestions": ["Test with undefined data.user", "Test with valid user object"]
            }
        }

# Made with Bob
