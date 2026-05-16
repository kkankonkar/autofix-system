"""Main entry point for Fixium."""
import sys
import os
import json
import time
from pathlib import Path
from typing import NoReturn

from .config import Config
from .comment_parser import CommentParser
from .github_client import GitHubClient
from .access_control import AccessControl
from .progress_tracker import ProgressTracker
from .review_runner import ReviewRunner
from .error_handler import ErrorHandler


def format_summary(review_data: dict) -> str:
    """
    Format review summary with emoji indicators.
    
    Args:
        review_data: Review JSON data
        
    Returns:
        Formatted summary string
    """
    summary = review_data.get('summary', {})
    
    parts = []
    if summary.get('critical', 0) > 0:
        parts.append(f"🔴 Critical: {summary['critical']}")
    if summary.get('high', 0) > 0:
        parts.append(f"🔴 High: {summary['high']}")
    if summary.get('medium', 0) > 0:
        parts.append(f"🟡 Medium: {summary['medium']}")
    if summary.get('low', 0) > 0:
        parts.append(f"🔵 Low: {summary['low']}")
    
    return ' | '.join(parts) if parts else "No issues found"


def exit_with_error(message: str, code: int = 1) -> NoReturn:
    """
    Print error message and exit.
    
    Args:
        message: Error message
        code: Exit code
    """
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def main() -> None:
    """Main Fixium workflow orchestrator."""
    print("🔍 Fixium Code Review Bot - Starting...")
    
    # Track start time for analytics
    start_time = time.time()
    
    # Load configuration
    config = Config()
    
    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in config_errors)
        exit_with_error(error_msg)
    
    print(f"✓ Configuration loaded: {config}")
    
    # Initialize components
    try:
        github_client = GitHubClient(config.github_token, config.github_repository)
        print(f"✓ GitHub client initialized for {config.github_repository}")
    except Exception as e:
        exit_with_error(f"Failed to initialize GitHub client: {e}")
    
    access_control = AccessControl(config.authorized_users)
    error_handler = ErrorHandler(github_client, config.pr_number)
    
    try:
        # Parse command
        print(f"Parsing comment: {config.comment_body[:100]}...")
        command = CommentParser.parse(config.comment_body)
        
        if not command or not command.is_valid():
            print("✗ Invalid command detected")
            error_handler.handle_invalid_command(config.comment_body)
            sys.exit(1)
        
        print(f"✓ Command parsed: {command.command}")
        print(f"  Filters: {command.filters}")
        
        # Check authorization
        print(f"Checking authorization for user: {config.comment_user}")
        if not access_control.is_authorized(config.comment_user):
            print(f"✗ User {config.comment_user} is not authorized")
            message = access_control.get_unauthorized_message(config.comment_user)
            github_client.post_comment(config.pr_number, message)
            sys.exit(1)
        
        print(f"✓ User {config.comment_user} is authorized")
        
        # Validate filters
        errors = CommentParser.validate_filters(command.filters)
        if errors:
            print(f"✗ Invalid filters: {errors}")
            error_handler.handle_invalid_filters(errors)
            sys.exit(1)
        
        print("✓ Filters validated")
        
        # Start progress tracking
        progress = ProgressTracker(github_client, config.pr_number)
        filter_info = str(command.filters)
        comment_id = progress.start(filter_info)
        print(f"✓ Progress tracking started (comment ID: {comment_id})")
        
        # Run review
        print("Running code review...")
        progress.update("Running code review...", "Analyzing PR files with Bob Shell")
        
        # ReviewRunner needs to find scripts in /fixium (Docker) or current dir (local)
        # Scripts are in the same directory as this Python code
        import sys
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        review_runner = ReviewRunner(script_dir)
        
        # Output file should be in GITHUB_WORKSPACE for artifact upload
        output_filename = f"review_pr{config.pr_number}.json"
        if config.workspace_dir and config.workspace_dir != script_dir:
            # In GitHub Actions: write to workspace, not script dir
            output_file = os.path.join(config.workspace_dir, output_filename)
            print(f"  Output will be written to: {output_file}")
        else:
            output_file = output_filename
        
        # Check if scripts exist
        scripts_status = review_runner.check_scripts_exist()
        print(f"  Scripts status: {scripts_status}")
        
        if not all(scripts_status.values()):
            missing = [name for name, exists in scripts_status.items() if not exists]
            error_msg = f"Required scripts not found: {', '.join(missing)}"
            print(f"✗ {error_msg}")
            error_handler.handle_unexpected_error(error_msg, progress)
            sys.exit(1)
        
        # Initialize cost_info
        cost_info = None
        
        try:
            success, cost_info = review_runner.run_review(
                config.pr_number,
                output_file,
                timeout=config.review_timeout
            )
            print(f"✓ Review completed, output: {output_file}")
            if cost_info and (cost_info.coins_used > 0 or cost_info.dollars_used > 0):
                print(f"  💰 Cost: {cost_info.coins_used:.2f} coins (${cost_info.dollars_used:.4f})")
        except TimeoutError as e:
            print(f"✗ Review timeout: {e}")
            error_handler.handle_timeout(progress)
            sys.exit(1)
        except RuntimeError as e:
            print(f"✗ Review error: {e}")
            error_handler.handle_review_error(progress, str(e))
            sys.exit(1)
        
        # Submit comments
        print("Submitting review comments...")
        progress.update("Submitting review comments...", "Posting findings to PR")
        
        filter_args = command.filters.to_cli_args()
        print(f"  Filter args: {filter_args}")
        
        try:
            review_runner.submit_comments(output_file, config.pr_number, filter_args)
            print("✓ Comments submitted successfully")
        except RuntimeError as e:
            print(f"✗ Submission error: {e}")
            error_handler.handle_submission_error(progress, str(e))
            sys.exit(1)
        
        # Get summary
        print(f"Reading review results from {output_file}...")
        output_path = Path(config.workspace_dir) / output_file
        
        if not output_path.exists():
            error_msg = f"Review output file not found: {output_file}"
            print(f"✗ {error_msg}")
            error_handler.handle_unexpected_error(error_msg, progress)
            sys.exit(1)
        
        with open(output_path) as f:
            review_data = json.load(f)
        
        # Handle both dict and list formats
        if isinstance(review_data, list):
            # If it's a list, wrap it in expected format
            print("⚠️  Review data is a list, converting to expected format")
            review_data = {
                'findings': review_data,
                'summary': {
                    'totalFindings': len(review_data)
                }
            }
        
        total_findings = review_data.get('summary', {}).get('totalFindings', 0)
        summary = format_summary(review_data)
        
        print(f"✓ Review summary: {total_findings} findings")
        print(f"  {summary}")
        
        # Complete progress (without cost in main summary)
        progress.complete(total_findings, summary)
        
        # Post separate cost comment if available
        if cost_info and (cost_info.coins_used > 0 or cost_info.dollars_used > 0):
            cost_comment = f"""## 💰 Review Cost Summary

{cost_info.format_for_comment()}

---
*🤖 Fixium Code Review Bot*"""
            github_client.post_comment(config.pr_number, cost_comment)
            print("✓ Cost summary posted")
        
        print("✅ Fixium review completed successfully!")
        
        # Post analytics event (non-blocking)
        try:
            from .analytics_client import build_review_event, post_analytics_event
            
            pr_info = github_client.get_pull_request(config.pr_number)
            event_data = build_review_event(
                pr_info=pr_info,
                cost_info=cost_info,
                review_data=review_data,
                metadata={
                    'triggeredBy': 'pull_request',
                    'duration': int(time.time() - start_time),
                    'status': 'success',
                    'fixiumVersion': '1.0.0'
                }
            )
            post_analytics_event(event_data)
        except Exception as e:
            print(f"⚠️  Analytics posting failed (non-critical): {e}")
        
    except KeyboardInterrupt:
        print("\n✗ Review interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        error_handler.handle_unexpected_error(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob
