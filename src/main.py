"""
AutoFix System - Main Application
A simplified MVP that demonstrates the core functionality.
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import os

from src.ai_agent import HybridAgent

# Initialize FastAPI app
app = FastAPI(
    title="AutoFix System MVP",
    description="Automated code fix system with AI integration",
    version="1.0.0-mvp"
)

# Simple in-memory storage for MVP
logs_db = {}
analyses_db = {}


class LogSubmission(BaseModel):
    """Normalized internal log submission model."""
    application: str
    severity: str
    message: str
    stack_trace: Optional[str] = None
    repository_url: Optional[str] = None
    raw_log: Optional[str] = None
    filename: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Analysis response model."""
    log_id: str
    error_type: str
    analysis: str
    fixable: bool
    status: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AutoFix System MVP",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "submit_log": "POST /api/v1/logs/ingest",
            "get_analysis": "GET /api/v1/analysis/{log_id}",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "logs_processed": len(logs_db),
        "analyses_completed": len(analyses_db)
    }


@app.post("/api/v1/logs/ingest")
async def ingest_log(
    repository_url: str = Form(...),
    log_file: UploadFile = File(...),
):
    """
    Ingest an entire log file and repository URL for processing.
    """
    raw_log_bytes = await log_file.read()
    if not raw_log_bytes:
        raise HTTPException(status_code=400, detail="Uploaded log file is empty")

    raw_log = raw_log_bytes.decode("utf-8", errors="replace")
    parsed_log = parse_uploaded_log(repository_url, raw_log, log_file.filename)

    log_id = f"log-{uuid.uuid4().hex[:8]}"

    logs_db[log_id] = {
        "id": log_id,
        "timestamp": datetime.utcnow().isoformat(),
        **parsed_log.dict()
    }

    analysis = await analyze_error_mvp(parsed_log)

    analyses_db[log_id] = {
        "log_id": log_id,
        "timestamp": datetime.utcnow().isoformat(),
        **analysis
    }

    return {
        "status": "success",
        "log_id": log_id,
        "message": "Log file ingested and analyzed",
        "analysis_url": f"/api/v1/analysis/{log_id}",
        "filename": log_file.filename,
    }


@app.get("/api/v1/analysis/{log_id}")
async def get_analysis(log_id: str):
    """Get analysis for a log entry."""
    
    if log_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analyses_db[log_id]


@app.get("/api/v1/logs")
async def list_logs():
    """List all ingested logs."""
    return {
        "total": len(logs_db),
        "logs": list(logs_db.values())
    }


def parse_uploaded_log(repository_url: str, raw_log: str, filename: Optional[str]) -> LogSubmission:
    """Convert uploaded log content into the internal log model."""
    first_non_empty_line = next((line.strip() for line in raw_log.splitlines() if line.strip()), "Log content uploaded")
    lowered_log = raw_log.lower()

    if "error" in lowered_log:
        severity = "ERROR"
    elif "warning" in lowered_log or "warn" in lowered_log:
        severity = "WARNING"
    else:
        severity = "INFO"

    return LogSubmission(
        application=filename or "uploaded-log",
        severity=severity,
        message=first_non_empty_line[:1000],
        stack_trace=raw_log[:4000],
        repository_url=repository_url,
        raw_log=raw_log,
        filename=filename,
    )


async def analyze_error_mvp(log: LogSubmission) -> dict:
    """
    Analyze an error using Bob CLI with a deterministic fallback.
    """
    code_context = (
        f"Application: {log.application}\n"
        f"Repository: {log.repository_url or 'unknown'}\n"
        f"Filename: {log.filename or 'N/A'}\n"
        f"Stack Trace:\n{log.stack_trace or 'N/A'}\n\n"
        f"Full Log:\n{log.raw_log or log.message}"
    )

    try:
        agent = HybridAgent()
        analysis = await agent.analyze_error(log.message, code_context)
        return {
            "error_type": analysis.get("error_type", "UnknownError"),
            "analysis": analysis.get("root_cause", "No root cause provided"),
            "fixable": analysis.get("fixable", False),
            "confidence": analysis.get("confidence", 0.0),
            "status": "analyzed",
            "file_path": analysis.get("file_path"),
            "line_number": analysis.get("line_number"),
            "function_name": analysis.get("function_name"),
            "repository": analysis.get("repository", log.repository_url),
        }
    except Exception:
        message = log.message.lower()

        if "typeerror" in message:
            error_type = "TypeError"
            analysis = "Type mismatch or undefined value access"
            fixable = True
        elif "nullpointer" in message or "null" in message:
            error_type = "NullPointerException"
            analysis = "Attempting to access null or undefined object"
            fixable = True
        elif "syntaxerror" in message:
            error_type = "SyntaxError"
            analysis = "Invalid syntax in code"
            fixable = True
        elif "referenceerror" in message:
            error_type = "ReferenceError"
            analysis = "Variable or function not defined"
            fixable = True
        else:
            error_type = "UnknownError"
            analysis = "Error type could not be determined"
            fixable = False

        return {
            "error_type": error_type,
            "analysis": analysis,
            "fixable": fixable,
            "confidence": 0.7 if fixable else 0.3,
            "status": "analyzed"
        }


@app.post("/api/v1/fix/{log_id}")
async def generate_fix(log_id: str):
    """
    Generate a fix for an analyzed error.
    
    MVP version returns a template fix.
    Production version would use AI to generate actual fixes.
    """
    if log_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_db[log_id]
    log = logs_db[log_id]
    
    if not analysis["fixable"]:
        raise HTTPException(status_code=400, detail="Error is not automatically fixable")
    
    # Generate template fix based on error type
    fix = generate_template_fix(analysis["error_type"], log)
    
    return {
        "log_id": log_id,
        "fix_generated": True,
        "fix": fix,
        "next_steps": [
            "Review the proposed fix",
            "Test in development environment",
            "Create pull request manually or use /api/v1/pr/create endpoint"
        ]
    }


def generate_template_fix(error_type: str, log: dict) -> dict:
    """Generate a template fix based on error type."""
    
    fixes = {
        "TypeError": {
            "description": "Add type checking and null safety",
            "code_template": "if (variable && typeof variable === 'expected_type') {\n  // safe to use variable\n}",
            "explanation": "Add defensive checks before accessing properties or methods"
        },
        "NullPointerException": {
            "description": "Add null/undefined checks",
            "code_template": "if (object != null) {\n  // safe to access object\n}",
            "explanation": "Check for null/undefined before accessing object properties"
        },
        "SyntaxError": {
            "description": "Fix syntax issues",
            "code_template": "// Review and fix syntax according to language rules",
            "explanation": "Syntax errors require manual review of the code"
        },
        "ReferenceError": {
            "description": "Define missing variables/functions",
            "code_template": "// Ensure variable is declared before use\nconst variable = defaultValue;",
            "explanation": "Declare variables before using them"
        }
    }
    
    return fixes.get(error_type, {
        "description": "Manual review required",
        "code_template": "// Error type not recognized",
        "explanation": "This error requires manual investigation"
    })


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    print("🚀 AutoFix System MVP starting...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print("✅ System ready!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("👋 AutoFix System shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

# Made with Bob
