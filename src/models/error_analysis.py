"""Error analysis data model."""

from pydantic import BaseModel, Field
from typing import Optional


class ErrorAnalysis(BaseModel):
    """Represents an analysis of an error from a log entry."""
    
    log_entry_id: str = Field(..., description="ID of the log entry being analyzed")
    error_type: str = Field(..., description="Type of error (e.g., TypeError, NullPointerException)")
    file_path: str = Field(..., description="Path to the file containing the error")
    line_number: int = Field(..., description="Line number where the error occurred")
    function_name: Optional[str] = Field(None, description="Function/method name where error occurred")
    root_cause: str = Field(..., description="Root cause of the error")
    fixable: bool = Field(..., description="Whether the error is automatically fixable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    repository: str = Field(..., description="Repository URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "log_entry_id": "log-123456",
                "error_type": "TypeError",
                "file_path": "src/app.js",
                "line_number": 42,
                "function_name": "getUserName",
                "root_cause": "Attempting to access property 'name' on undefined object",
                "fixable": True,
                "confidence": 0.95,
                "repository": "https://github.com/org/my-web-app"
            }
        }

# Made with Bob
