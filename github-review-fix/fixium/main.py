"""Main entry point for Fixium."""
import sys
import json
from pathlib import Path
from typing import Any, NoReturn, Optional

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
        review_data: Review JSON data conforming to schema/review_output.schema.json
        
    Returns:
        Formatted summary string
    """
    summary = review_data.get('review_summary', {})
    
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


def is_bob_fixable_comment(review_comment: dict[str, Any]) -> bool:
    """Check whether a review comment is explicitly marked bob-fixable."""
    return '`bob_fixable: true`' in review_comment.get('body', '').lower()


def validate_implement_target(
    github_client: GitHubClient,
    reply_to_comment_id: Optional[int],
) -> dict[str, Any]:
    """
    Validate that the implement command is replying to a bob-fixable review comment.

    Args:
        github_client: GitHub client instance
        reply_to_comment_id: Review comment ID being replied to

    Returns:
        Review comment payload

    Raises:
        ValueError: If the target is missing, not found, or not bob-fixable
    """
    if reply_to_comment_id is None:
        raise ValueError("REPLY_TO_COMMENT_ID is required for Fixium:implement")

    review_comment = github_client.get_review_comment(reply_to_comment_id)

    if not is_bob_fixable_comment(review_comment):
        raise ValueError(
            f"Review comment {reply_to_comment_id} is not marked as bob_fixable"
        )

    return review_comment


def main() -> None:
    """Main Fixium workflow orchestrator."""
    print("🔍 Fixium Code Review Bot - Starting...")
    
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
    pr_number = config.pr_number
    comment_body = config.comment_body
    comment_user = config.comment_user
    review_timeout = config.review_timeout or 1800

    if pr_number is None or comment_body is None or comment_user is None:
        exit_with_error("Configuration validation failed after initialization")

    error_handler = ErrorHandler(github_client, pr_number)
    
    try:
        # Parse command
        print(f"Parsing comment: {comment_body[:100]}...")
        command = CommentParser.parse(comment_body)
        
        if not command or not command.is_valid():
            print("✗ Invalid command detected")
            error_handler.handle_invalid_command(comment_body)
            sys.exit(1)
        
        print(f"✓ Command parsed: {command.command}")
        print(f"  Filters: {command.filters}")
        
        # Check authorization
        print(f"Checking authorization for user: {comment_user}")
        if not access_control.is_authorized(comment_user):
            print(f"✗ User {comment_user} is not authorized")
            message = access_control.get_unauthorized_message(comment_user)
            github_client.post_comment(pr_number, message)
            sys.exit(1)
        
        print(f"✓ User {comment_user} is authorized")
        
        # Validate filters
        errors = CommentParser.validate_filters(command.filters)
        if errors:
            print(f"✗ Invalid filters: {errors}")
            error_handler.handle_invalid_filters(errors)
            sys.exit(1)
        
        print("✓ Filters validated")
        
        # Start progress tracking
        progress = ProgressTracker(github_client, pr_number)
        review_runner = ReviewRunner(config.workspace_dir)

        if command.command == 'implement':
            print("Validating implement target...")
            try:
                target_comment = validate_implement_target(
                    github_client,
                    config.reply_to_comment_id,
                )
            except ValueError as e:
                print(f"✗ Implement target error: {e}")
                error_handler.handle_unexpected_error(str(e))
                sys.exit(1)

            instruction_text = command.instruction or "No additional guidance provided"
            target_path = target_comment.get('path', 'unknown file')
            target_line = target_comment.get('line', 'unknown line')
            target_comment_id = target_comment.get('id', config.reply_to_comment_id)
            target_summary = f"Review comment {target_comment_id} on {target_path}:{target_line}"
            comment_id = progress.start(f"Implement target: {target_summary}")
            print(f"✓ Progress tracking started (comment ID: {comment_id})")
            
            # Parse review comment body to extract structured data
            comment_body = target_comment.get('body', '')
            parsed_finding = CommentParser.parse_review_comment_body(comment_body)
            
            progress.update(
                "Preparing implementation...",
                f"Targeting {target_summary}\n\nGuidance: {instruction_text}"
            )
            
            # Execute implementation
            print(f"Executing implementation for {target_path}:{target_line}...")
            try:
                timeout = config.review_timeout if config.review_timeout else 600
                implementation_result = review_runner.implement_finding(
                    file_path=str(target_path),
                    line_number=int(target_line) if isinstance(target_line, int) else 0,
                    comment_body=comment_body,
                    instruction=instruction_text,
                    timeout=timeout
                )
                
                if implementation_result.get('success'):
                    bob_cost = str(implementation_result.get('bob_cost_used', 'unknown'))
                    
                    # Extract issue summary from parsed finding
                    issue_summary = parsed_finding.get('issue', 'Code review finding')
                    if len(issue_summary) > 100:
                        issue_summary = issue_summary[:97] + "..."
                    
                    # Create concise completion message
                    completion_msg = f"✅ **Fix Implemented**\n\n"
                    completion_msg += f"**File:** `{target_path}`\n"
                    completion_msg += f"**Line:** {target_line}\n"
                    completion_msg += f"**Issue:** {issue_summary}\n\n"
                    completion_msg += f"Changes have been committed and pushed to the PR branch."
                    
                    progress.complete(
                        1,  # One finding implemented
                        completion_msg,
                        bob_cost
                    )
                    print(f"✓ Implementation completed successfully")
                    print(f"  File: {target_path}:{target_line}")
                    print(f"  Bob cost: {bob_cost}")
                else:
                    error_msg = str(implementation_result.get('error', 'Unknown error'))
                    progress.update(
                        "Implementation failed",
                        f"❌ {error_msg}"
                    )
                    error_handler.handle_unexpected_error(error_msg, progress)
                    sys.exit(1)
                    
            except TimeoutError as e:
                error_msg = f"Implementation timed out: {e}"
                print(f"✗ {error_msg}")
                progress.update("Implementation timed out", f"❌ {error_msg}")
                error_handler.handle_unexpected_error(error_msg, progress)
                sys.exit(1)
            except Exception as e:
                error_msg = f"Implementation failed: {e}"
                print(f"✗ {error_msg}")
                progress.update("Implementation failed", f"❌ {error_msg}")
                error_handler.handle_unexpected_error(error_msg, progress)
                sys.exit(1)
            
            # Exit after implement command completes
            sys.exit(0)

        filter_info = str(command.filters)
        comment_id = progress.start(filter_info)
        print(f"✓ Progress tracking started (comment ID: {comment_id})")
        
        # Run review
        print("Running code review...")
        progress.update("Running code review...", "Analyzing PR files with Bob Shell")
        
        output_file = f"review_pr{pr_number}.json"
        
        # Check if scripts exist
        scripts_status = review_runner.check_scripts_exist()
        print(f"  Scripts status: {scripts_status}")
        
        if not all(scripts_status.values()):
            missing = [name for name, exists in scripts_status.items() if not exists]
            error_msg = f"Required scripts not found: {', '.join(missing)}"
            print(f"✗ {error_msg}")
            error_handler.handle_unexpected_error(error_msg, progress)
            sys.exit(1)
        
        bob_cost_used = 'unknown'

        try:
            review_result = review_runner.run_review(
                pr_number,
                output_file,
                timeout=review_timeout
            )
            bob_cost_used = str(review_result.get('bob_cost_used', 'unknown'))
            print(f"✓ Review completed, output: {output_file}")
            print(f"  Bob cost used: {bob_cost_used}")
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
        
        submission_failed = False
        try:
            review_runner.submit_comments(output_file, pr_number, filter_args)
            print("✓ Comments submitted successfully")
        except RuntimeError as e:
            print(f"⚠️  Submission error (non-fatal): {e}")
            # Don't post a comment about comment submission failure
            submission_failed = True
            # Continue execution instead of exiting
        
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
        
        # Extract data according to canonical schema (schema/review_output.schema.json)
        summary_data = review_data.get('review_summary', {})
        total_findings = summary_data.get('total_findings', 0)
        summary = format_summary(review_data)
        
        print(f"✓ Review summary: {total_findings} findings")
        print(f"  {summary}")
        
        # Complete
        if submission_failed:
            completion_note = f"{summary}\n\n⚠️ Note: Comment submission failed, but review completed successfully."
            progress.complete(total_findings, completion_note, bob_cost_used)
            print("✅ Fixium review completed (with submission warning)")
        else:
            progress.complete(total_findings, summary, bob_cost_used)
            print("✅ Fixium review completed successfully!")
        
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
