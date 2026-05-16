"""Review runner - wrapper for Bob Shell execution."""
import json
import subprocess
import os
from typing import Optional
from pathlib import Path


class ReviewRunner:
    """Execute Bob Shell reviews via shell scripts."""
    
    def __init__(self, workspace_dir: Optional[str] = None):
        """
        Initialize review runner.
        
        Args:
            workspace_dir: Working directory (defaults to current dir)
        """
        self.workspace_dir = workspace_dir or os.getcwd()
        self._package_root = Path(__file__).resolve().parent.parent
    
    def run_review(
        self,
        pr_number: int,
        output_file: str,
        timeout: int = 1800  # 30 minutes default
    ) -> dict[str, object]:
        """
        Run code review using review_workflow.sh.
        
        Args:
            pr_number: Pull request number
            output_file: Output JSON file path
            timeout: Timeout in seconds
            
        Returns:
            Review execution metadata
            
        Raises:
            TimeoutError: If review times out
            RuntimeError: If review fails
        """
        try:
            script_path = self._resolve_script_path('review_workflow.sh')
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Review script not found: {e}")
        
        run_dir = self._resolve_script_run_dir(script_path)
        cmd = [
            str(script_path),
            'review-pr',
            str(pr_number),
            output_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=run_dir,
                capture_output=False,  # Allow output to be visible
                text=True,
                timeout=timeout,
                check=True
            )
            return self._load_review_usage(output_file)
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
        try:
            script_path = self._resolve_script_path('submit_pr_comments.sh')
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Submit script not found: {e}")
        
        run_dir = self._resolve_script_run_dir(script_path)
        cmd = [
            str(script_path),
            review_file,
            str(pr_number)
        ] + filter_args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=run_dir,
                capture_output=False,  # Allow output to be visible
                text=True,
                timeout=timeout,
                check=True
            )
            return True
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Comment submission timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Comment submission failed: {error_msg}")
    
    def implement_finding(
        self,
        file_path: str,
        line_number: int,
        comment_body: str,
        instruction: Optional[str] = None,
        timeout: int = 600
    ) -> dict[str, object]:
        """
        Implement a single review finding.
        
        Args:
            file_path: File containing the issue
            line_number: Line number of the issue
            comment_body: Full review comment body
            instruction: Optional user guidance
            timeout: Timeout in seconds
            
        Returns:
            Implementation result with success status and details
            
        Raises:
            TimeoutError: If implementation times out
            RuntimeError: If implementation fails
        """
        try:
            script_path = self._resolve_script_path('implement_finding.sh')
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Implement script not found: {e}")
        
        # implement_finding.sh must run from workspace to access repository files
        # Unlike review_workflow.sh which can run from package root
        run_dir = self.workspace_dir
        
        # Debug logging
        print(f"[DEBUG] implement_finding execution:")
        print(f"  workspace_dir: {self.workspace_dir}")
        print(f"  script_path: {script_path}")
        print(f"  run_dir: {run_dir}")
        print(f"  file_path: {file_path}")
        print(f"  line_number: {line_number}")
        
        cmd = [
            str(script_path),
            file_path,
            str(line_number),
            comment_body,
            instruction or ""
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=run_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            # Parse JSON result from stdout
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Fallback if output is not JSON
                return {
                    'success': True,
                    'output': result.stdout,
                    'bob_cost_used': self._extract_bob_cost(result.stdout)
                }
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Implementation timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            # Try to parse error output as JSON
            try:
                return json.loads(e.stdout)
            except (json.JSONDecodeError, AttributeError):
                return {
                    'success': False,
                    'error': e.stderr if e.stderr else str(e),
                    'output': e.stdout if e.stdout else ''
                }
    
    def _extract_bob_cost(self, output: str) -> str:
        """Extract Bob cost from output text."""
        import re
        
        # Look for cost patterns
        cost_match = re.search(r'\$([0-9]+\.[0-9]+)', output)
        if cost_match:
            return f"${cost_match.group(1)}"
        
        token_match = re.search(r'([0-9]+\.[0-9]+)\s*tokens', output)
        if token_match:
            return f"{token_match.group(1)} tokens"
        
        return "unknown"
    
    def _load_review_usage(self, output_file: str) -> dict[str, object]:
        """Load Bob usage metadata emitted by the shell workflow."""
        usage_path = Path(self.workspace_dir) / f"{output_file}.usage.json"
        usage_data: dict[str, object] = {
            'usage_file': str(usage_path),
            'bob_cost_used': 'unknown'
        }

        if not usage_path.exists():
            return usage_data

        try:
            with open(usage_path) as usage_file:
                parsed_usage = json.load(usage_file)
        except (OSError, json.JSONDecodeError):
            return usage_data

        bob_cost_used = parsed_usage.get('bob_cost_used', 'unknown')
        if not isinstance(bob_cost_used, str):
            bob_cost_used = str(bob_cost_used)

        usage_data.update(parsed_usage)
        usage_data['bob_cost_used'] = bob_cost_used
        return usage_data

    def _resolve_script_path(self, script_name: str) -> Path:
        """Resolve shell script path from workspace first, then package root."""
        workspace_path = Path(self.workspace_dir) / script_name
        if workspace_path.exists():
            return workspace_path

        package_root_path = self._package_root / script_name
        if package_root_path.exists():
            return package_root_path

        raise FileNotFoundError(f"Script not found: {workspace_path} or {package_root_path}")

    def _resolve_script_run_dir(self, script_path: Path) -> str:
        """Choose the correct working directory for executing shell scripts."""
        if script_path.parent == self._package_root:
            return str(self._package_root)
        return self.workspace_dir

    def check_scripts_exist(self) -> dict[str, bool]:
        """
        Check if required scripts exist.
        
        Returns:
            Dict with script names and existence status
        """
        scripts = {
            'review_workflow.sh': (
                (Path(self.workspace_dir) / 'review_workflow.sh').exists()
                or (self._package_root / 'review_workflow.sh').exists()
            ),
            'submit_pr_comments.sh': (
                (Path(self.workspace_dir) / 'submit_pr_comments.sh').exists()
                or (self._package_root / 'submit_pr_comments.sh').exists()
            ),
            'implement_finding.sh': (
                (Path(self.workspace_dir) / 'implement_finding.sh').exists()
                or (self._package_root / 'implement_finding.sh').exists()
            )
        }
        
        return scripts
    
    def get_workspace_dir(self) -> str:
        """
        Get workspace directory.
        
        Returns:
            Workspace directory path
        """
        return self.workspace_dir

# Made with Bob
