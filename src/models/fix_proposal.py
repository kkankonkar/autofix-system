"""Fix proposal data model."""

from pydantic import BaseModel, Field
from typing import List, Optional


class FileChange(BaseModel):
    """Represents a change to a single file."""
    
    file_path: str = Field(..., description="Relative path from repo root")
    original_code: str = Field(default="", description="Original code with the error")
    fixed_code: str = Field(..., description="Fixed code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/services/user_service.py",
                "original_code": "user = data.user\nprint(user.name)",
                "fixed_code": "user = data.get('user')\nif user:\n    print(user.name)"
            }
        }


class FixProposal(BaseModel):
    """Represents a proposed fix for an error."""
    
    analysis_id: str = Field(..., description="ID of the error analysis")
    file_path: str = Field(default="", description="Primary target file path (for backward compatibility)")
    file_changes: List[FileChange] = Field(default_factory=list, description="List of file changes")
    original_code: str = Field(default="", description="Original code (deprecated, use file_changes)")
    fixed_code: str = Field(default="", description="Fixed code (deprecated, use file_changes)")
    explanation: str = Field(..., description="Explanation of the fix")
    commit_message: str = Field(..., description="Commit message for the fix")
    pr_description: str = Field(..., description="Pull request description")
    test_suggestions: List[str] = Field(default_factory=list, description="Suggested tests")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "log-123456",
                "file_path": "src/services/user_service.js",
                "file_changes": [
                    {
                        "file_path": "src/services/user_service.js",
                        "original_code": "const user = data.user;",
                        "fixed_code": "const user = data?.user;"
                    },
                    {
                        "file_path": "src/utils/validator.js",
                        "original_code": "",
                        "fixed_code": "export function validateUser(user) {\n  return user != null;\n}"
                    }
                ],
                "explanation": "Added null check to prevent accessing property on undefined",
                "commit_message": "Fix: Add null check for user object access",
                "pr_description": "## Problem\nTypeError when accessing user.name on undefined object\n\n## Solution\nAdded optional chaining and null check",
                "test_suggestions": ["Test with undefined data.user", "Test with valid user object"]
            }
        }

# Made with Bob
