"""Log entry data model."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LogSeverity(str, Enum):
    """Log severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogEntry(BaseModel):
    """Represents a log entry from an application."""
    
    id: str = Field(..., description="Unique identifier for the log entry")
    timestamp: datetime = Field(..., description="When the log was created")
    application: str = Field(..., description="Application name that generated the log")
    severity: LogSeverity = Field(..., description="Log severity level")
    message: str = Field(..., description="Log message")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    repository_url: Optional[str] = Field(None, description="Associated repository URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "log-123456",
                "timestamp": "2024-01-15T10:30:00Z",
                "application": "my-web-app",
                "severity": "ERROR",
                "message": "TypeError: Cannot read property 'name' of undefined",
                "stack_trace": "at getUserName (app.js:42:15)\nat processUser (app.js:30:10)",
                "metadata": {"environment": "production", "user_id": "user-789"},
                "repository_url": "https://github.com/org/my-web-app"
            }
        }

# Made with Bob
