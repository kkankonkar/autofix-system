"""
AutoFix System - Main Application
A simplified MVP that demonstrates the core functionality.
"""

from datetime import datetime
import os
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.ai_agent import HybridAgent
from src.fix_generator import FixGenerator
from src.pr_creator import PRCreator
from src.repo_manager import RepoManager

# Import analytics routes
from src.analytics.routes import router as analytics_router
from src.database import engine, Base

# Initialize FastAPI app
app = FastAPI(
    title="AutoFix System MVP",
    description="Automated code fix system with AI integration",
    version="1.0.0-mvp"
)

# Include analytics routes
app.include_router(analytics_router)

# Simple in-memory storage for MVP
logs_db = {}
analyses_db = {}
fixes_db = {}
pull_requests_db = {}


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
            "get_fix": "POST /api/v1/fix/{log_id}",
            "create_pr": "POST /api/v1/pr/create/{log_id}",
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
        "analyses_completed": len(analyses_db),
        "fixes_generated": len(fixes_db),
        "pull_requests_created": len(pull_requests_db),
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
    """
    if log_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analyses_db[log_id]
    log = logs_db[log_id]

    if not analysis["fixable"]:
        raise HTTPException(status_code=400, detail="Error is not automatically fixable")

    code_context = build_code_context(log, analysis)
    generator = FixGenerator()

    try:
        fix = await generator.generate_fix(
            analysis_id=log_id,
            error_analysis=analysis,
            code_context=code_context,
        )
        fix_payload = fix.dict()
    except Exception:
        fix_payload = generate_template_fix(analysis["error_type"], log)

    fixes_db[log_id] = {
        "log_id": log_id,
        "timestamp": datetime.utcnow().isoformat(),
        "fix": fix_payload,
    }

    return {
        "log_id": log_id,
        "fix_generated": True,
        "fix": fix_payload,
        "detected_file_path": fix_payload.get("file_path", "Not detected"),
        "next_steps": [
            "Review the proposed fix",
            f"Target file: {fix_payload.get('file_path', 'Not detected')}",
            "Create pull request automatically using POST /api/v1/pr/create/{log_id}",
        ]
    }


@app.post("/api/v1/pr/create/{log_id}")
async def create_pull_request_for_fix(
    log_id: str,
    target_file_path: Optional[str] = Form(None),
    base_branch: str = Form("main"),
):
    """Generate a fix, apply it to a repository, and open a GitHub pull request.
    
    If target_file_path is not provided, it will be auto-detected from the error analysis.
    """
    if log_id not in logs_db:
        raise HTTPException(status_code=404, detail="Log not found")

    if log_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")

    log = logs_db[log_id]
    analysis = analyses_db[log_id]

    if not log.get("repository_url"):
        raise HTTPException(status_code=400, detail="repository_url is required to create a PR")

    if not analysis.get("fixable"):
        raise HTTPException(status_code=400, detail="Analysis is not marked as fixable")

    if log_id not in fixes_db:
        await generate_fix(log_id)

    fix_record = fixes_db[log_id]["fix"]
    branch_name = f"autofix/{log_id}"
    repo_manager = RepoManager()
    pr_creator = PRCreator()

    checkout_dir = None

    try:
        repo, checkout_dir = repo_manager.prepare_repository(
            repository_url=log["repository_url"],
            branch_name=branch_name,
            base_branch=base_branch,
        )

        # Check if fix has multiple file changes
        file_changes = fix_record.get("file_changes", [])
        
        if file_changes:
            # Handle multiple file changes
            files_modified = []
            for change in file_changes:
                change_file_path = change.get("file_path", "")
                
                # Normalize the file path
                normalized_path = repo_manager.find_file_in_repo(checkout_dir, change_file_path)
                if not normalized_path:
                    # Try as-is if normalization fails
                    normalized_path = change_file_path
                
                change_original = change.get("original_code", "")
                change_fixed = change.get("fixed_code", "")
                
                if not change_fixed.strip():
                    continue
                
                try:
                    if change_original.strip():
                        # Try to replace specific code snippet
                        repo_manager.replace_code_snippet(
                            checkout_dir=checkout_dir,
                            file_path=normalized_path,
                            original_code=change_original,
                            fixed_code=change_fixed,
                        )
                    else:
                        # Check if we have line number information
                        line_number = change.get("line_number") or analysis.get("line_number")
                        if line_number and (checkout_dir / normalized_path).exists():
                            # Use line-based replacement (safer - preserves rest of file)
                            # Estimate end line (assume fix is ~10 lines)
                            end_line = line_number + 10
                            repo_manager.replace_lines_in_file(
                                checkout_dir=checkout_dir,
                                file_path=normalized_path,
                                start_line=line_number,
                                end_line=end_line,
                                fixed_code=change_fixed,
                            )
                        else:
                            # New file - write entire content
                            repo_manager.write_file(checkout_dir, normalized_path, change_fixed)
                except ValueError as e:
                    # If snippet not found, try line-based replacement if we have line numbers
                    if "not found in target file" in str(e):
                        line_number = change.get("line_number") or analysis.get("line_number")
                        if line_number:
                            # Use line-based replacement as fallback
                            end_line = line_number + 10  # Estimate
                            try:
                                repo_manager.replace_lines_in_file(
                                    checkout_dir=checkout_dir,
                                    file_path=normalized_path,
                                    start_line=line_number,
                                    end_line=end_line,
                                    fixed_code=change_fixed,
                                )
                            except ValueError:
                                # Last resort: skip this change and log warning
                                print(f"Warning: Could not apply fix to {normalized_path}: {e}")
                                continue
                        else:
                            # No line number info - cannot safely apply fix
                            raise HTTPException(
                                status_code=400,
                                detail=f"Cannot apply fix to {normalized_path}: original code not found and no line number provided"
                            )
                    else:
                        raise
                
                files_modified.append(normalized_path)
            
            if not files_modified:
                raise HTTPException(status_code=400, detail="No valid file changes found in fix")
            
            target_file_path = ", ".join(files_modified)
        else:
            # Handle single file change (backward compatibility)
            # Auto-detect target file path if not provided
            if not target_file_path:
                detected_path = auto_detect_target_file_path(analysis, fix_record, checkout_dir)
                if not detected_path:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not auto-detect target file path. Please provide target_file_path explicitly."
                    )
                target_file_path = detected_path
            
            # Normalize the file path
            normalized_path = repo_manager.find_file_in_repo(checkout_dir, target_file_path)
            if normalized_path:
                target_file_path = normalized_path

            fixed_code = extract_fixed_code(fix_record)
            if not fixed_code.strip():
                raise HTTPException(status_code=400, detail="Generated fix does not contain fixed_code")

            original_code = extract_original_code(fix_record)
            try:
                if original_code.strip():
                    # Try to replace specific code snippet
                    repo_manager.replace_code_snippet(
                        checkout_dir=checkout_dir,
                        file_path=target_file_path,
                        original_code=original_code,
                        fixed_code=fixed_code,
                    )
                else:
                    # Check if we have line number information
                    line_number = analysis.get("line_number")
                    if line_number and (checkout_dir / target_file_path).exists():
                        # Use line-based replacement (safer - preserves rest of file)
                        end_line = line_number + 10  # Estimate
                        repo_manager.replace_lines_in_file(
                            checkout_dir=checkout_dir,
                            file_path=target_file_path,
                            start_line=line_number,
                            end_line=end_line,
                            fixed_code=fixed_code,
                        )
                    else:
                        # New file - write entire content
                        repo_manager.write_file(checkout_dir, target_file_path, fixed_code)
            except ValueError as e:
                # If snippet not found, try line-based replacement if we have line numbers
                if "not found in target file" in str(e):
                    line_number = analysis.get("line_number")
                    if line_number:
                        # Use line-based replacement as fallback
                        end_line = line_number + 10  # Estimate
                        try:
                            repo_manager.replace_lines_in_file(
                                checkout_dir=checkout_dir,
                                file_path=target_file_path,
                                start_line=line_number,
                                end_line=end_line,
                                fixed_code=fixed_code,
                            )
                        except ValueError:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Cannot apply fix: original code not found and line-based replacement failed"
                            )
                    else:
                        # No line number info - cannot safely apply fix
                        raise HTTPException(
                            status_code=400,
                            detail="Cannot apply fix: original code not found and no line number provided"
                        )
                else:
                    raise

        commit_message = extract_commit_message(fix_record, log_id)
        repo_manager.commit_and_push(repo, branch_name, commit_message)

        pr_title = commit_message
        pr_body = extract_pr_description(fix_record, analysis, log)
        created_pr = pr_creator.create_pull_request(
            repository_url=log["repository_url"],
            branch_name=branch_name,
            title=pr_title,
            body=pr_body,
            base_branch=base_branch,
            fix_proposal_id=log_id,
        )

        pr_payload = created_pr.dict()
        pull_requests_db[log_id] = pr_payload

        return {
            "status": "success",
            "log_id": log_id,
            "branch_name": branch_name,
            "target_file_path": target_file_path,
            "pull_request": pr_payload,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create pull request: {exc}") from exc
    finally:
        if checkout_dir is not None:
            repo_manager.cleanup(checkout_dir)


def build_code_context(log: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Build context for fix generation."""
    return (
        f"Repository: {log.get('repository_url', 'unknown')}\n"
        f"Application: {log.get('application', 'unknown')}\n"
        f"Filename: {log.get('filename', 'N/A')}\n"
        f"Detected file path: {analysis.get('file_path', 'unknown')}\n"
        f"Detected line number: {analysis.get('line_number', 0)}\n"
        f"Function name: {analysis.get('function_name', 'unknown')}\n"
        f"Root cause: {analysis.get('analysis', analysis.get('root_cause', 'unknown'))}\n"
        f"Stack trace:\n{log.get('stack_trace', 'N/A')}\n\n"
        f"Full log:\n{log.get('raw_log', log.get('message', ''))}"
    )


def extract_fixed_code(fix_record: dict[str, Any]) -> str:
    """Normalize fixed code from either structured or template fix output."""
    return fix_record.get("fixed_code") or fix_record.get("code_template") or ""


def extract_original_code(fix_record: dict[str, Any]) -> str:
    """Extract original code for surgical snippet replacement."""
    return fix_record.get("original_code") or ""


def extract_commit_message(fix_record: dict[str, Any], log_id: str) -> str:
    """Normalize commit message from fix output."""
    return fix_record.get("commit_message") or f"Fix issue detected from {log_id}"


def extract_pr_description(fix_record: dict[str, Any], analysis: dict[str, Any], log: dict[str, Any]) -> str:
    """Normalize PR description from fix output."""
    return (
        fix_record.get("pr_description")
        or f"## Automated Fix\n\n"
        f"- Repository: {log.get('repository_url', 'unknown')}\n"
        f"- Error type: {analysis.get('error_type', 'UnknownError')}\n"
        f"- Analysis: {analysis.get('analysis', 'No analysis available')}\n"
        f"- Explanation: {fix_record.get('explanation', 'No explanation provided')}"
    )


def generate_template_fix(error_type: str, log: dict[str, Any]) -> dict[str, Any]:
    """Generate a template fix based on error type."""

    fixes = {
        "TypeError": {
            "description": "Add type checking and null safety",
            "original_code": log.get("raw_log", ""),
            "fixed_code": "if (variable && typeof variable === 'expected_type') {\n  // safe to use variable\n}",
            "explanation": "Add defensive checks before accessing properties or methods",
            "commit_message": "Fix: add type checking and null safety",
            "pr_description": "## Problem\nDetected a TypeError from uploaded logs.\n\n## Solution\nAdded defensive type checks and null safety.",
            "test_suggestions": ["Test with undefined values", "Test with expected input types"],
        },
        "NullPointerException": {
            "description": "Add null/undefined checks",
            "original_code": log.get("raw_log", ""),
            "fixed_code": "if (object != null) {\n  // safe to access object\n}",
            "explanation": "Check for null/undefined before accessing object properties",
            "commit_message": "Fix: guard against null object access",
            "pr_description": "## Problem\nDetected null object access.\n\n## Solution\nAdded null checks before property access.",
            "test_suggestions": ["Test with null object", "Test with initialized object"],
        },
        "SyntaxError": {
            "description": "Fix syntax issues",
            "original_code": log.get("raw_log", ""),
            "fixed_code": "// Review and fix syntax according to language rules",
            "explanation": "Syntax errors require manual review of the code",
            "commit_message": "Fix: adjust syntax based on log analysis",
            "pr_description": "## Problem\nDetected syntax-related issue.\n\n## Solution\nPrepared a manual syntax-fix placeholder for review.",
            "test_suggestions": ["Run linter", "Run unit tests"],
        },
        "ReferenceError": {
            "description": "Define missing variables/functions",
            "original_code": log.get("raw_log", ""),
            "fixed_code": "// Ensure variable is declared before use\nconst variable = defaultValue;",
            "explanation": "Declare variables before using them",
            "commit_message": "Fix: declare missing reference before use",
            "pr_description": "## Problem\nDetected missing variable or function reference.\n\n## Solution\nAdded declaration placeholder before usage.",
            "test_suggestions": ["Run affected code path", "Add regression test for missing reference"],
        }
    }

    return fixes.get(error_type, {
        "description": "Manual review required",
        "original_code": log.get("raw_log", ""),
        "fixed_code": "// Error type not recognized",
        "explanation": "This error requires manual investigation",
        "commit_message": "Fix: investigate unknown error from logs",
        "pr_description": "## Problem\nUnknown error detected from uploaded logs.\n\n## Solution\nManual investigation required.",
        "test_suggestions": ["Review logs manually"],
    })


def auto_detect_target_file_path(analysis: dict, fix_record: dict, checkout_dir: Path) -> Optional[str]:
    """Auto-detect the target file path from analysis or fix record.
    
    Priority:
    1. file_path from fix_record (stored during fix generation)
    2. file_path from analysis (detected by AI during analysis)
    3. Search for file in repository based on error context
    """
    # Try to get from fix record first (most reliable as it was validated during fix generation)
    file_path = fix_record.get("file_path")
    if file_path and _validate_file_exists(checkout_dir, file_path):
        return file_path
    
    # Try to get from analysis
    file_path = analysis.get("file_path")
    if file_path and _validate_file_exists(checkout_dir, file_path):
        return file_path
    
    # Try to extract from stack trace or error message
    stack_trace = analysis.get("stack_trace", "")
    if stack_trace:
        # Look for common file path patterns in stack traces
        import re
        # Pattern for file paths like "at /path/to/file.py:123" or "File 'path/to/file.js', line 45"
        patterns = [
            r'File ["\']([^"\']+)["\']',  # Python style
            r'at ([^\s:]+):\d+',  # JavaScript/TypeScript style
            r'in ([^\s]+):\d+',  # Generic style
            r'([a-zA-Z0-9_/.-]+\.(py|js|ts|java|go|rb|php|cpp|c|h)):\d+',  # Generic file.ext:line
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, stack_trace)
            for match in matches:
                # Extract just the file path (match might be a tuple)
                potential_path = match[0] if isinstance(match, tuple) else match
                
                # Clean up the path (remove leading slashes, make relative)
                potential_path = potential_path.lstrip('/')
                
                if _validate_file_exists(checkout_dir, potential_path):
                    return potential_path
    
    return None


def _validate_file_exists(checkout_dir: Path, file_path: str) -> bool:
    """Check if a file exists in the repository checkout."""
    try:
        target_path = checkout_dir / file_path
        return target_path.exists() and target_path.is_file()
    except Exception:
        return False


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    print("🚀 AutoFix System MVP starting...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
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
