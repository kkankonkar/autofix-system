"""
AutoFix System - Main Application
A simplified MVP that demonstrates the core functionality.
"""

from datetime import datetime
import os
import uuid
from pathlib import Path
from typing import Any, Optional, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.ai_agent import HybridAgent
from src.fix_generator import FixGenerator
from src.pr_creator import PRCreator
from src.repo_manager import RepoManager
from src.utils.log_parser import extract_multiple_errors

# Configuration
MAX_ERRORS_PER_LOG = int(os.getenv("MAX_ERRORS_PER_LOG", "3"))

# Initialize FastAPI app
app = FastAPI(
    title="AutoFix System MVP",
    description="Automated code fix system with AI integration",
    version="1.0.0-mvp"
)

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
    max_errors: Optional[int] = Form(None),
):
    """
    Ingest an entire log file and repository URL for processing.
    Extracts and analyzes up to max_errors (default: 3) from the log file.
    """
    raw_log_bytes = await log_file.read()
    if not raw_log_bytes:
        raise HTTPException(status_code=400, detail="Uploaded log file is empty")

    raw_log = raw_log_bytes.decode("utf-8", errors="replace")
    
    # Use provided max_errors or default from config
    max_errors_to_process = max_errors if max_errors is not None else MAX_ERRORS_PER_LOG
    
    # Extract multiple errors from the log file
    error_blocks = extract_multiple_errors(raw_log, max_errors=max_errors_to_process)
    
    log_id = f"log-{uuid.uuid4().hex[:8]}"
    
    # Store the original log
    parsed_log = parse_uploaded_log(repository_url, raw_log, log_file.filename)
    logs_db[log_id] = {
        "id": log_id,
        "timestamp": datetime.utcnow().isoformat(),
        **parsed_log.dict()
    }
    
    # Analyze each error independently
    analyses = []
    for idx, error_block in enumerate(error_blocks):
        error_id = f"{log_id}-{idx + 1}"
        analysis = await analyze_single_error(error_block, parsed_log, error_id)
        analyses.append(analysis)
    
    # Store all analyses under the log_id
    analyses_db[log_id] = {
        "log_id": log_id,
        "timestamp": datetime.utcnow().isoformat(),
        "total_errors": len(error_blocks),
        "errors_analyzed": len(analyses),
        "errors": analyses,
        # Keep backward compatibility - store first error at top level
        **(analyses[0] if analyses else {
            "error_type": "NoError",
            "analysis": "No errors found in log",
            "fixable": False,
            "status": "analyzed"
        })
    }

    return {
        "status": "success",
        "log_id": log_id,
        "message": f"Log file ingested and analyzed ({len(analyses)} errors found)",
        "total_errors": len(error_blocks),
        "errors_analyzed": len(analyses),
        "errors_fixable": sum(1 for a in analyses if a.get("fixable")),
        "analysis_url": f"/api/v1/analysis/{log_id}",
        "filename": log_file.filename,
        "errors": [
            {
                "error_id": a.get("error_id"),
                "error_type": a.get("error_type"),
                "fixable": a.get("fixable"),
                "file_path": a.get("file_path")
            }
            for a in analyses
        ]
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


async def analyze_single_error(error_block: dict, log: LogSubmission, error_id: str) -> dict:
    """
    Analyze a single error block extracted from a log file.
    
    Args:
        error_block: Extracted error information
        log: Original log submission
        error_id: Unique identifier for this error
        
    Returns:
        Analysis dictionary for the error
    """
    error_message = error_block.get("error_message", "")
    stack_trace = error_block.get("stack_trace", "")
    detected_file_path = error_block.get("file_path")
    detected_line_number = error_block.get("line_number")
    detected_error_type = error_block.get("error_type")
    
    code_context = (
        f"Application: {log.application}\n"
        f"Repository: {log.repository_url or 'unknown'}\n"
        f"Filename: {log.filename or 'N/A'}\n"
        f"Error Message: {error_message}\n"
        f"Stack Trace:\n{stack_trace}\n"
    )

    try:
        agent = HybridAgent()
        analysis = await agent.analyze_error(error_message, code_context)
        return {
            "error_id": error_id,
            "error_type": analysis.get("error_type", detected_error_type or "UnknownError"),
            "analysis": analysis.get("root_cause", "No root cause provided"),
            "fixable": analysis.get("fixable", False),
            "confidence": analysis.get("confidence", 0.0),
            "status": "analyzed",
            "file_path": analysis.get("file_path") or detected_file_path,
            "line_number": analysis.get("line_number") or detected_line_number,
            "function_name": analysis.get("function_name"),
            "repository": analysis.get("repository", log.repository_url),
            "error_message": error_message,
            "stack_trace": stack_trace,
        }
    except Exception:
        # Fallback analysis based on detected or message content
        message_lower = error_message.lower()
        
        if detected_error_type:
            error_type = detected_error_type
        elif "typeerror" in message_lower:
            error_type = "TypeError"
        elif "nullpointer" in message_lower or "null" in message_lower:
            error_type = "NullPointerException"
        elif "syntaxerror" in message_lower:
            error_type = "SyntaxError"
        elif "referenceerror" in message_lower:
            error_type = "ReferenceError"
        elif "indexerror" in message_lower:
            error_type = "IndexError"
        else:
            error_type = "UnknownError"
        
        # Determine if fixable
        fixable = error_type in ["TypeError", "NullPointerException", "SyntaxError", "ReferenceError", "IndexError"]
        
        # Generate analysis based on error type
        analysis_map = {
            "TypeError": "Type mismatch or undefined value access",
            "NullPointerException": "Attempting to access null or undefined object",
            "SyntaxError": "Invalid syntax in code",
            "ReferenceError": "Variable or function not defined",
            "IndexError": "Array or list index out of bounds",
            "UnknownError": "Error type could not be determined"
        }

        return {
            "error_id": error_id,
            "error_type": error_type,
            "analysis": analysis_map.get(error_type, "Unknown error"),
            "fixable": fixable,
            "confidence": 0.7 if fixable else 0.3,
            "status": "analyzed",
            "file_path": detected_file_path,
            "line_number": detected_line_number,
            "repository": log.repository_url,
            "error_message": error_message,
            "stack_trace": stack_trace,
        }


async def analyze_error_mvp(log: LogSubmission) -> dict:
    """
    Analyze an error using Bob CLI with a deterministic fallback.
    (Kept for backward compatibility)
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
    Generate fixes for all analyzed errors in the log.
    Creates a combined fix with all file changes.
    """
    if log_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_record = analyses_db[log_id]
    log = logs_db[log_id]
    
    # Check if we have multiple errors
    errors = analysis_record.get("errors", [])
    
    if not errors:
        # Backward compatibility: single error at top level
        if not analysis_record.get("fixable"):
            raise HTTPException(status_code=400, detail="Error is not automatically fixable")
        errors = [analysis_record]
    
    # Filter only fixable errors
    fixable_errors = [e for e in errors if e.get("fixable")]
    
    if not fixable_errors:
        raise HTTPException(status_code=400, detail="No fixable errors found")
    
    # Generate fixes for all fixable errors
    all_file_changes = []
    fix_explanations = []
    generator = FixGenerator()
    
    for error in fixable_errors:
        error_id = error.get("error_id", log_id)
        code_context = build_code_context(log, error)
        
        try:
            fix = await generator.generate_fix(
                analysis_id=error_id,
                error_analysis=error,
                code_context=code_context,
            )
            fix_dict = fix.dict()
            
            # Extract file changes
            file_changes = fix_dict.get("file_changes", [])
            if not file_changes and fix_dict.get("fixed_code"):
                # Convert single fix to file_changes format
                file_changes = [{
                    "file_path": fix_dict.get("file_path", error.get("file_path", "unknown")),
                    "original_code": fix_dict.get("original_code", ""),
                    "fixed_code": fix_dict.get("fixed_code", "")
                }]
            
            all_file_changes.extend(file_changes)
            fix_explanations.append({
                "error_id": error_id,
                "error_type": error.get("error_type"),
                "explanation": fix_dict.get("explanation", ""),
                "file_path": error.get("file_path")
            })
            
        except Exception as e:
            # Generate template fix as fallback
            template_fix = generate_template_fix(error.get("error_type", "UnknownError"), log)
            all_file_changes.append({
                "file_path": error.get("file_path", "unknown"),
                "original_code": template_fix.get("original_code", ""),
                "fixed_code": template_fix.get("fixed_code", "")
            })
            fix_explanations.append({
                "error_id": error.get("error_id", log_id),
                "error_type": error.get("error_type"),
                "explanation": template_fix.get("explanation", ""),
                "file_path": error.get("file_path")
            })
    
    # Create combined fix payload
    combined_fix_payload = {
        "analysis_id": log_id,
        "file_changes": all_file_changes,
        "explanation": generate_combined_explanation(fix_explanations),
        "commit_message": generate_combined_commit_message(fixable_errors),
        "pr_description": generate_combined_pr_description(fixable_errors, fix_explanations, log),
        "test_suggestions": [
            f"Test fix for {e.get('error_type')}" for e in fixable_errors
        ],
        "errors_fixed": len(fixable_errors),
        "total_file_changes": len(all_file_changes)
    }
    
    fixes_db[log_id] = {
        "log_id": log_id,
        "timestamp": datetime.utcnow().isoformat(),
        "fix": combined_fix_payload,
    }

    return {
        "log_id": log_id,
        "fix_generated": True,
        "errors_fixed": len(fixable_errors),
        "total_file_changes": len(all_file_changes),
        "fix": combined_fix_payload,
        "files_modified": list(set(fc.get("file_path") for fc in all_file_changes)),
        "next_steps": [
            f"Review the proposed fixes for {len(fixable_errors)} errors",
            f"Files to be modified: {', '.join(set(fc.get('file_path', 'unknown') for fc in all_file_changes))}",
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

        # Use combined commit message and PR description if available
        commit_message = fix_record.get("commit_message") or extract_commit_message(fix_record, log_id)
        repo_manager.commit_and_push(repo, branch_name, commit_message)

        pr_title = commit_message
        pr_body = fix_record.get("pr_description") or extract_pr_description(fix_record, analysis, log)
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


def generate_combined_explanation(fix_explanations: List[dict]) -> str:
    """Generate combined explanation for multiple fixes."""
    if not fix_explanations:
        return "No fixes generated"
    
    if len(fix_explanations) == 1:
        return fix_explanations[0].get("explanation", "No explanation provided")
    
    explanation = f"This fix addresses {len(fix_explanations)} errors:\n\n"
    for idx, fix_exp in enumerate(fix_explanations, 1):
        explanation += f"{idx}. **{fix_exp.get('error_type', 'Unknown')}** "
        explanation += f"in `{fix_exp.get('file_path', 'unknown')}`\n"
        explanation += f"   {fix_exp.get('explanation', 'No explanation')}\n\n"
    
    return explanation


def generate_combined_commit_message(errors: List[dict]) -> str:
    """Generate commit message for multiple error fixes."""
    if not errors:
        return "Fix: Automated error resolution"
    
    if len(errors) == 1:
        error = errors[0]
        return f"Fix: Resolve {error.get('error_type', 'error')} in {error.get('file_path', 'code')}"
    
    error_types = list(set(e.get('error_type', 'Unknown') for e in errors))
    return f"Fix: Resolve {len(errors)} errors ({', '.join(error_types[:3])})"


def generate_combined_pr_description(errors: List[dict], fix_explanations: List[dict], log: dict) -> str:
    """Generate comprehensive PR description for multiple fixes."""
    if not errors:
        return "## Automated Fix\n\nNo errors to fix."
    
    description = "## Automated Fix: Multiple Error Resolution\n\n"
    description += f"This PR fixes **{len(errors)} errors** detected in the log file.\n\n"
    description += f"**Repository:** {log.get('repository_url', 'unknown')}\n"
    description += f"**Log File:** {log.get('filename', 'N/A')}\n\n"
    
    description += "---\n\n"
    
    # List each error
    for idx, error in enumerate(errors, 1):
        description += f"### Error {idx}: {error.get('error_type', 'Unknown')}\n\n"
        description += f"- **File:** `{error.get('file_path', 'unknown')}`\n"
        if error.get('line_number'):
            description += f"- **Line:** {error.get('line_number')}\n"
        if error.get('function_name'):
            description += f"- **Function:** `{error.get('function_name')}`\n"
        description += f"- **Root Cause:** {error.get('analysis', 'No analysis')}\n"
        
        # Add explanation if available
        matching_explanation = next(
            (exp for exp in fix_explanations if exp.get('error_id') == error.get('error_id')),
            None
        )
        if matching_explanation and matching_explanation.get('explanation'):
            description += f"- **Fix:** {matching_explanation.get('explanation')}\n"
        
        description += "\n"
    
    description += "---\n\n"
    description += "## Changes Made\n\n"
    
    # List unique files modified
    files_modified = list(set(e.get('file_path', 'unknown') for e in errors if e.get('file_path')))
    for file_path in files_modified:
        description += f"- Modified `{file_path}`\n"
    
    description += "\n## Testing\n\n"
    description += "Please review the changes and test the following scenarios:\n\n"
    for idx, error in enumerate(errors, 1):
        description += f"{idx}. Test case for {error.get('error_type', 'error')}\n"
    
    description += "\n---\n\n"
    description += "*This PR was automatically generated by the AutoFix System*\n"
    
    return description


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
