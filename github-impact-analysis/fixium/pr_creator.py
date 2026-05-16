"""Create pull requests from code changes."""
from typing import Dict, Optional
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.GithubException import GithubException
import subprocess
import os


class PRCreator:
    """Create and manage pull requests."""
    
    def __init__(
        self, 
        github_client: Github, 
        repo_name: str,
        workspace_dir: str
    ):
        """
        Initialize PR creator.
        
        Args:
            github_client: PyGithub client instance
            repo_name: Repository name (owner/repo)
            workspace_dir: Local repository workspace directory
        """
        self.client = github_client
        self.repo: Repository = github_client.get_repo(repo_name)
        self.workspace_dir = workspace_dir
        self.repo_name = repo_name
    
    def create_branch(self, issue_number: int, base_branch: str = 'main') -> str:
        """
        Create a new branch for the issue.
        
        Args:
            issue_number: Issue number
            base_branch: Base branch to branch from (default: main)
            
        Returns:
            Branch name
            
        Raises:
            RuntimeError: If branch creation fails
        """
        branch_name = f"fixium/issue-{issue_number}"
        
        try:
            # Get base branch reference
            try:
                base_ref = self.repo.get_git_ref(f"heads/{base_branch}")
            except GithubException:
                # Try 'master' if 'main' doesn't exist
                base_branch = 'master'
                base_ref = self.repo.get_git_ref(f"heads/{base_branch}")
            
            base_sha = base_ref.object.sha
            
            # Create new branch
            try:
                self.repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=base_sha
                )
            except GithubException as e:
                if 'already exists' in str(e):
                    # Branch exists, delete and recreate
                    ref = self.repo.get_git_ref(f"heads/{branch_name}")
                    ref.delete()
                    self.repo.create_git_ref(
                        ref=f"refs/heads/{branch_name}",
                        sha=base_sha
                    )
                else:
                    raise
            
            # Checkout branch locally
            self._git_command(['checkout', '-B', branch_name, f'origin/{base_branch}'])
            
            return branch_name
            
        except Exception as e:
            raise RuntimeError(f"Failed to create branch: {e}")
    
    def apply_changes(
        self, 
        branch_name: str, 
        changes: Dict,
        commit_message: Optional[str] = None
    ) -> bool:
        """
        Apply code changes and commit to branch.
        
        Args:
            branch_name: Branch name
            changes: CodeChanges dictionary
            commit_message: Custom commit message (optional)
            
        Returns:
            True if successful
            
        Raises:
            RuntimeError: If applying changes fails
        """
        try:
            # Ensure we're on the correct branch
            self._git_command(['checkout', branch_name])
            
            # Apply each file change
            for change in changes['changes']:
                file_path = os.path.join(self.workspace_dir, change['file'])
                
                if change['action'] == 'create':
                    # Create parent directories
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Write new file
                    with open(file_path, 'w') as f:
                        f.write(change.get('content', ''))
                    
                    # Git add
                    self._git_command(['add', change['file']])
                
                elif change['action'] == 'modify':
                    # Overwrite file
                    with open(file_path, 'w') as f:
                        f.write(change.get('content', ''))
                    
                    # Git add
                    self._git_command(['add', change['file']])
                
                elif change['action'] == 'delete':
                    # Git rm
                    self._git_command(['rm', change['file']])
            
            # Commit changes
            if not commit_message:
                issue_number = changes['issueNumber']
                commit_message = f"Fix: Implement solution for issue #{issue_number}\n\n"
                commit_message += "Changes:\n"
                for change in changes['changes']:
                    commit_message += f"- {change['action']} {change['file']}: {change.get('description', 'Updated')}\n"
                
                if changes.get('implementationNotes'):
                    commit_message += f"\n{changes['implementationNotes']}"
            
            self._git_command(['commit', '-m', commit_message])
            
            # Push to remote
            self._git_command(['push', '-u', 'origin', branch_name])
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Failed to apply changes: {e}")
    
    def create_pull_request(
        self,
        branch_name: str,
        issue_number: int,
        issue_title: str,
        changes: Dict,
        base_branch: str = 'main'
    ) -> PullRequest:
        """
        Create a pull request.
        
        Args:
            branch_name: Source branch name
            issue_number: Issue number
            issue_title: Issue title
            changes: CodeChanges dictionary
            base_branch: Target branch (default: main)
            
        Returns:
            Created PullRequest object
            
        Raises:
            RuntimeError: If PR creation fails
        """
        try:
            # Check if base branch exists
            try:
                self.repo.get_branch(base_branch)
            except GithubException:
                base_branch = 'master'
            
            # Build PR title
            pr_title = f"Fix #{issue_number}: {issue_title}"
            
            # Build PR body
            pr_body = self._build_pr_description(issue_number, issue_title, changes)
            
            # Create PR
            pr = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=base_branch
            )
            
            return pr
            
        except Exception as e:
            raise RuntimeError(f"Failed to create pull request: {e}")
    
    def _build_pr_description(
        self,
        issue_number: int,
        issue_title: str,
        changes: Dict
    ) -> str:
        """
        Build PR description from changes.
        
        Args:
            issue_number: Issue number
            issue_title: Issue title
            changes: CodeChanges dictionary
            
        Returns:
            PR description markdown
        """
        description = f"## Fixes #{issue_number}\n\n"
        description += f"**Issue**: {issue_title}\n\n"
        
        # Changes summary
        description += "### Changes Made\n\n"
        for change in changes['changes']:
            action_emoji = {
                'create': '✨',
                'modify': '🔧',
                'delete': '🗑️'
            }.get(change['action'], '📝')
            
            description += f"{action_emoji} **{change['action'].title()}** `{change['file']}`"
            if change.get('description'):
                description += f": {change['description']}"
            description += "\n"
        
        description += "\n"
        
        # Implementation details
        if changes.get('implementationNotes'):
            description += "### Implementation Details\n\n"
            description += f"{changes['implementationNotes']}\n\n"
        
        # File statistics
        total_added = sum(c.get('linesAdded', 0) for c in changes['changes'])
        total_removed = sum(c.get('linesRemoved', 0) for c in changes['changes'])
        
        description += "### Statistics\n\n"
        description += f"- Files changed: {len(changes['changes'])}\n"
        description += f"- Lines added: +{total_added}\n"
        description += f"- Lines removed: -{total_removed}\n"
        
        # Tests
        if changes.get('testsAdded'):
            description += "\n### Tests Added\n\n"
            for test in changes['testsAdded']:
                description += f"- ✅ `{test}`\n"
        
        # Validation status
        description += "\n### Validation\n\n"
        status = changes.get('validationStatus', 'unknown')
        if status == 'passed':
            description += "✅ All validation checks passed\n"
        elif status == 'failed':
            description += "⚠️ Validation issues detected:\n"
            for error in changes.get('validationErrors', []):
                description += f"- {error}\n"
            description += "\n**Note**: Please review and fix validation issues before merging.\n"
        
        # Footer
        description += "\n---\n"
        description += "*🤖 Automatically generated by Fixium*\n"
        description += f"*Triggered by: `Fixium:implementfix` on issue #{issue_number}*"
        
        return description
    
    def link_to_issue(self, pr: PullRequest, issue_number: int) -> None:
        """
        Link PR to issue by adding a comment.
        
        Args:
            pr: PullRequest object
            issue_number: Issue number
        """
        try:
            issue = self.repo.get_issue(issue_number)
            
            comment = f"🤖 **Fixium Implementation**\n\n"
            comment += f"I've created a pull request to implement this issue:\n"
            comment += f"➡️ #{pr.number}: {pr.title}\n\n"
            comment += f"**Branch**: `{pr.head.ref}`\n"
            comment += f"**Status**: {pr.state}\n\n"
            comment += "Please review the changes and provide feedback!"
            
            issue.create_comment(comment)
            
        except Exception as e:
            # Don't fail if comment creation fails
            print(f"Warning: Failed to comment on issue: {e}")
    
    def add_labels(self, pr: PullRequest, labels: list[str]) -> None:
        """
        Add labels to PR.
        
        Args:
            pr: PullRequest object
            labels: List of label names
        """
        try:
            # Filter to only existing labels
            repo_labels = {label.name for label in self.repo.get_labels()}
            valid_labels = [l for l in labels if l in repo_labels]
            
            if valid_labels:
                pr.add_to_labels(*valid_labels)
        except Exception as e:
            print(f"Warning: Failed to add labels: {e}")
    
    def _git_command(self, args: list[str]) -> str:
        """
        Execute git command.
        
        Args:
            args: Git command arguments
            
        Returns:
            Command output
            
        Raises:
            RuntimeError: If command fails
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr}")


# Made with Bob