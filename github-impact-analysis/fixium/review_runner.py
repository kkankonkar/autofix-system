"""Review runner - wrapper for Bob Shell execution."""
import subprocess
import os
from typing import Optional, Tuple
from pathlib import Path

from .cost_tracker import CostTracker, CostInfo


class ReviewRunner:
    """Execute Bob Shell reviews via shell scripts."""
    
    def __init__(self, workspace_dir: Optional[str] = None):
        """
        Initialize review runner.
        
        Args:
            workspace_dir: Working directory (defaults to current dir)
        """
        self.workspace_dir = workspace_dir or os.getcwd()
    
    def run_review(
        self,
        pr_number: int,
        output_file: str,
        timeout: int = 1800  # 30 minutes default
    ) -> Tuple[bool, CostInfo]:
        """
        Run code review using review_workflow.sh.
        
        Args:
            pr_number: Pull request number
            output_file: Output JSON file path
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, cost_info)
            
        Raises:
            TimeoutError: If review times out
            RuntimeError: If review fails
        """
        script_path = Path(self.workspace_dir) / 'review_workflow.sh'
        
        if not script_path.exists():
            raise FileNotFoundError(f"Review script not found: {script_path}")
        
        cmd = [
            str(script_path),
            'review-pr',
            str(pr_number),
            output_file
        ]
        
        # Determine working directory for Bob
        # In GitHub Actions, use GITHUB_WORKSPACE so Bob can access repo files
        # Otherwise use script directory
        work_dir = os.getenv('GITHUB_WORKSPACE') or self.workspace_dir
        
        try:
            # Capture output to extract cost information
            result = subprocess.run(
                cmd,
                cwd=work_dir,  # Run in repo directory, not script directory
                capture_output=True,  # Capture to extract costs
                text=True,
                timeout=timeout,
                check=True
            )
            
            # Extract cost information from output
            combined_output = result.stdout + result.stderr
            cost_info = CostTracker.extract_costs(combined_output, "code review")
            
            # Print output for visibility
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=__import__('sys').stderr)
            
            return True, cost_info
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Review timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Review failed: {error_msg}")
    
    def submit_comments(
        self,
        review_file: str,
        pr_number: int,
        filter_args: list[str],
        timeout: int = 600  # 10 minutes default
    ) -> bool:
        """
        Submit review comments to PR.
        
        Args:
            review_file: Review JSON file
            pr_number: Pull request number
            filter_args: Filter arguments (e.g., ['--severity', 'high'])
            timeout: Timeout in seconds
            
        Returns:
            True if successful
            
        Raises:
            RuntimeError: If submission fails
        """
        script_path = Path(self.workspace_dir) / 'submit_pr_comments.sh'
        
        if not script_path.exists():
            raise FileNotFoundError(f"Submit script not found: {script_path}")
        
        cmd = [
            str(script_path),
            review_file,
            str(pr_number)
        ] + filter_args
        
        # Use same working directory as review
        work_dir = os.getenv('GITHUB_WORKSPACE') or self.workspace_dir
        
        try:
            # Don't capture output so user can see submission progress
            result = subprocess.run(
                cmd,
                cwd=work_dir,  # Run in repo directory, not script directory
                capture_output=False,  # Show output in real-time
                timeout=timeout,
                check=True
            )
            return True
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Comment submission timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Comment submission failed: {error_msg}")
    
    def check_scripts_exist(self) -> dict[str, bool]:
        """
        Check if required scripts exist.
        
        Returns:
            Dict with script names and existence status
        """
        scripts = {
            'review_workflow.sh': Path(self.workspace_dir) / 'review_workflow.sh',
            'submit_pr_comments.sh': Path(self.workspace_dir) / 'submit_pr_comments.sh'
        }
        
        return {name: path.exists() for name, path in scripts.items()}
    
    def get_workspace_dir(self) -> str:
        """
        Get workspace directory.
        
        Returns:
            Workspace directory path
        """
        return self.workspace_dir

# Made with Bob
