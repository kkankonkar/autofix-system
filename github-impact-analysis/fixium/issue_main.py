"""Main entry point for Fixium issue implementation."""
import os
import sys
import json
import time
from typing import Optional
from github import Github

from .issue_analyzer import IssueAnalyzer
from .code_generator import CodeGenerator
from .pr_creator import PRCreator
from .github_client import GitHubClient
from .access_control import AccessControl


def main():
    """Main entry point for issue implementation workflow."""
    # Track start time for analytics
    start_time = time.time()
    
    # Get environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPOSITORY')
    issue_number = int(os.getenv('ISSUE_NUMBER', '0'))
    comment_user = os.getenv('COMMENT_USER', '')
    workspace_dir = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    
    # Validate required environment variables
    if not github_token:
        print("❌ Error: GITHUB_TOKEN not set")
        sys.exit(1)
    
    if not repo_name:
        print("❌ Error: GITHUB_REPOSITORY not set")
        sys.exit(1)
    
    if not issue_number:
        print("❌ Error: ISSUE_NUMBER not set")
        sys.exit(1)
    
    print(f"🤖 Fixium Issue Implementation")
    print(f"📋 Repository: {repo_name}")
    print(f"🎫 Issue: #{issue_number}")
    print(f"👤 Triggered by: {comment_user}")
    print()
    
    try:
        # Initialize GitHub client
        print("🔌 Connecting to GitHub...")
        github_client = GitHubClient(token=github_token, repository=repo_name)
        github = Github(github_token)
        
        # Check authorization
        print(f"🔐 Checking authorization for {comment_user}...")
        access_control = AccessControl()
        if not access_control.is_authorized(comment_user):
            error_msg = f"❌ User {comment_user} is not authorized to use Fixium:implementfix"
            print(error_msg)
            
            # Comment on issue
            github_client.post_issue_comment(
                issue_number,
                f"⚠️ **Authorization Failed**\n\n{error_msg}\n\n"
                f"Please contact a repository administrator to be added to the authorized users list."
            )
            sys.exit(1)
        
        print(f"✅ User {comment_user} is authorized")
        print()
        
        # Post initial comment
        initial_comment = github_client.post_issue_comment(
            issue_number,
            "🤖 **Fixium Implementation Started**\n\n"
            "I'm analyzing this issue to generate a code implementation.\n\n"
            "**Status**: Analyzing issue requirements..."
        )
        comment_id = initial_comment.id
        
        # Phase 1: Analyze Issue
        print("📊 Phase 1: Analyzing Issue")
        print("-" * 50)
        
        analyzer = IssueAnalyzer(github, repo_name)
        analysis = analyzer.analyze_issue(issue_number)
        
        # Save analysis
        analysis_file = f"issue_analysis_{issue_number}.json"
        with open(os.path.join(workspace_dir, analysis_file), 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)
        
        print(f"   Issue Type: {analysis.issue_type.value}")
        print(f"   Has Sufficient Context: {analysis.has_sufficient_context}")
        print(f"   Requirements: {len(analysis.requirements)}")
        print(f"   Affected Files: {len(analysis.affected_files)}")
        print()
        
        # Check if context is sufficient
        if not analysis.has_sufficient_context:
            print("⚠️  Insufficient context for implementation")
            print("   Missing:")
            for item in analysis.missing_context:
                print(f"   - {item}")
            print()
            
            # Update comment with missing context
            missing_items = "\n".join(f"- {item}" for item in analysis.missing_context)
            github_client.update_comment(
                comment_id,
                f"⚠️ **Insufficient Context**\n\n"
                f"I need more information to implement this issue. Please update the issue description with:\n\n"
                f"{missing_items}\n\n"
                f"Once you've added this information, comment `Fixium:implementfix` again to retry."
            )
            
            sys.exit(0)  # Not an error, just needs more info
        
        # Update progress comment
        github_client.update_comment(
            comment_id,
            f"🤖 **Fixium Implementation In Progress**\n\n"
            f"✅ Issue analysis complete\n"
            f"⏳ Generating code changes...\n\n"
            f"**Issue Type**: {analysis.issue_type.value}\n"
            f"**Requirements**: {len(analysis.requirements)}\n"
            f"**Affected Components**: {len(analysis.affected_files)}"
        )
        
        # Phase 2: Generate Code Changes
        print("💻 Phase 2: Generating Code Changes")
        print("-" * 50)
        
        generator = CodeGenerator(workspace_dir)
        changes = generator.generate_changes(analysis.to_dict())
        
        print(f"   Files Changed: {len(changes.changes)}")
        print(f"   Tests Added: {len(changes.tests_added)}")
        print(f"   Validation: {changes.validation_status}")
        
        # Print cost information
        if changes.cost_info and (changes.cost_info.coins_used > 0 or changes.cost_info.dollars_used > 0):
            print(f"   💰 Cost: {changes.cost_info.coins_used:.2f} coins (${changes.cost_info.dollars_used:.4f})")
        
        print()
        
        if changes.validation_status == 'failed':
            print("⚠️  Code validation failed:")
            for error in changes.validation_errors:
                print(f"   - {error}")
            print()
        
        # Save changes
        changes_file = f"code_changes_issue{issue_number}.json"
        with open(os.path.join(workspace_dir, changes_file), 'w') as f:
            json.dump(changes.to_dict(), f, indent=2)
        
        # Update progress comment
        github_client.update_comment(
            comment_id,
            f"🤖 **Fixium Implementation In Progress**\n\n"
            f"✅ Issue analysis complete\n"
            f"✅ Code changes generated\n"
            f"⏳ Creating pull request...\n\n"
            f"**Files Changed**: {len(changes.changes)}\n"
            f"**Validation**: {changes.validation_status}"
        )
        
        # Phase 3: Create Pull Request
        print("🔀 Phase 3: Creating Pull Request")
        print("-" * 50)
        
        pr_creator = PRCreator(github, repo_name, workspace_dir)
        
        # Create branch
        print("   Creating branch...")
        branch_name = pr_creator.create_branch(issue_number)
        print(f"   ✅ Branch created: {branch_name}")
        
        # Apply changes
        print("   Applying code changes...")
        pr_creator.apply_changes(branch_name, changes.to_dict())
        print(f"   ✅ Changes committed and pushed")
        
        # Create PR
        print("   Creating pull request...")
        pr = pr_creator.create_pull_request(
            branch_name,
            issue_number,
            analysis.title,
            changes.to_dict()
        )
        print(f"   ✅ PR created: #{pr.number}")
        
        # Link to issue
        print("   Linking PR to issue...")
        pr_creator.link_to_issue(pr, issue_number)
        
        # Add labels
        if analysis.labels:
            print("   Adding labels...")
            pr_creator.add_labels(pr, analysis.labels)
        
        print()
        print("✅ Implementation Complete!")
        print(f"   PR: #{pr.number} - {pr.title}")
        print(f"   URL: {pr.html_url}")
        print()
        
        # Post analytics event (non-blocking)
        try:
            from .analytics_client import build_fix_event, post_analytics_event
            
            issue = github_client.get_issue(issue_number)
            event_data = build_fix_event(
                issue_info=issue,
                pr_info=pr,
                cost_info=changes.cost_info,
                fix_data=changes.to_dict(),
                metadata={
                    'triggeredBy': 'issue_comment',
                    'duration': int(time.time() - start_time),
                    'status': 'success',
                    'fixiumVersion': '1.0.0'
                }
            )
            post_analytics_event(event_data)
        except Exception as e:
            print(f"⚠️  Analytics posting failed (non-critical): {e}")
        
        # Update final comment
        validation_note = ""
        if changes.validation_status == 'failed':
            validation_note = (
                "\n\n⚠️ **Validation Issues Detected**\n\n"
                "The generated code has some validation issues. "
                "Please review and fix them before merging:\n\n"
                + "\n".join(f"- {error}" for error in changes.validation_errors)
            )
        
        # Format cost information for comment
        cost_section = ""
        if changes.cost_info and (changes.cost_info.coins_used > 0 or changes.cost_info.dollars_used > 0):
            cost_section = f"\n\n{changes.cost_info.format_for_comment()}"
        
        github_client.update_comment(
            comment_id,
            f"✅ **Implementation Complete**\n\n"
            f"I've created a pull request to implement this issue:\n\n"
            f"➡️ **PR #{pr.number}**: {pr.title}\n"
            f"🔗 {pr.html_url}\n\n"
            f"**Summary**:\n"
            f"- Files changed: {len(changes.changes)}\n"
            f"- Tests added: {len(changes.tests_added)}\n"
            f"- Branch: `{branch_name}`\n"
            f"- Validation: {changes.validation_status}"
            f"{validation_note}"
            f"{cost_section}\n\n"
            f"Please review the changes and provide feedback!"
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        
        # Try to update comment if we have comment_id
        try:
            if 'comment_id' in locals():
                github_client.update_comment(
                    comment_id,
                    f"❌ **Implementation Failed**\n\n"
                    f"An error occurred while generating the implementation:\n\n"
                    f"```\n{error_msg}\n```\n\n"
                    f"This could be due to:\n"
                    f"- Complex changes requiring human judgment\n"
                    f"- Insufficient codebase context\n"
                    f"- Ambiguous requirements\n\n"
                    f"Please consider implementing this manually or breaking it into smaller issues."
                )
        except:
            pass
        
        sys.exit(1)


if __name__ == '__main__':
    main()


# Made with Bob