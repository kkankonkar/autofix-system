"""Generate code changes based on issue analysis."""
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json
import tempfile
import os


@dataclass
class FileChange:
    """Represents a change to a single file."""
    file_path: str
    action: str  # modify, create, delete
    content: Optional[str] = None
    diff: Optional[str] = None
    description: str = ""
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class CodeChanges:
    """Collection of code changes for an issue."""
    issue_number: int
    changes: List[FileChange]
    tests_added: List[str]
    validation_status: str  # passed, failed, skipped
    validation_errors: List[str]
    implementation_notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'issueNumber': self.issue_number,
            'changes': [
                {
                    'file': c.file_path,
                    'action': c.action,
                    'content': c.content,
                    'diff': c.diff,
                    'description': c.description,
                    'linesAdded': c.lines_added,
                    'linesRemoved': c.lines_removed
                }
                for c in self.changes
            ],
            'testsAdded': self.tests_added,
            'validationStatus': self.validation_status,
            'validationErrors': self.validation_errors,
            'implementationNotes': self.implementation_notes
        }


class CodeGenerator:
    """Generate code changes using Bob AI."""
    
    def __init__(self, workspace_dir: str, script_dir: Optional[str] = None):
        """
        Initialize code generator.
        
        Args:
            workspace_dir: Repository workspace directory
            script_dir: Directory containing scripts (defaults to parent of this file)
        """
        self.workspace_dir = workspace_dir
        if script_dir:
            self.script_dir = script_dir
        else:
            self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def generate_changes(
        self, 
        issue_analysis: Dict,
        prompt_template_path: Optional[str] = None
    ) -> CodeChanges:
        """
        Generate code changes for an issue.
        
        Args:
            issue_analysis: Issue analysis dictionary
            prompt_template_path: Path to prompt template (optional)
            
        Returns:
            CodeChanges object
            
        Raises:
            RuntimeError: If code generation fails
        """
        issue_number = issue_analysis['issueNumber']
        
        # Load prompt template
        if not prompt_template_path:
            prompt_template_path = os.path.join(
                self.script_dir, 
                'prompts', 
                'generate-fix.md'
            )
        
        if not os.path.exists(prompt_template_path):
            raise FileNotFoundError(f"Prompt template not found: {prompt_template_path}")
        
        with open(prompt_template_path) as f:
            prompt_template = f.read()
        
        # Create temporary file with issue analysis
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.json', 
            delete=False,
            dir=self.workspace_dir
        ) as f:
            json.dump(issue_analysis, f, indent=2)
            analysis_file = f.name
        
        try:
            # Build Bob command - Use Bob AI's native workflow
            command = f"""{prompt_template}

## Issue Analysis

@{analysis_file}

## Your Task

Implement the code changes described in the issue analysis above.

**Step 1: Understand Requirements**
- Read the issue analysis file to understand what needs to be implemented
- Identify which files need to be created or modified

**Step 2: Implement Changes**
For each file that needs changes:
1. If modifying existing file: Use read_file to read current content
2. Implement the complete solution with proper code
3. Use write_to_file (for new files) or apply_diff (for modifications)
4. Ensure code is complete, working, and follows project patterns

**Step 3: Document Changes**
After implementing all changes, create a summary file documenting what you did.

## Important Guidelines

- Write ACTUAL CODE, not descriptions
- Read existing files before modifying them
- Include all imports, functions, and classes
- Follow the project's coding style
- Add appropriate error handling
- Include tests if needed

## Example of What NOT to Do

❌ BAD - Writing descriptions instead of code:
```python
# booking_system_backend/services/email.py
Complete file content created with 367 lines including SMTP integration
```

✅ GOOD - Writing actual code:
```python
# booking_system_backend/services/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to: str, subject: str, body: str):
    # Actual implementation here
    pass
```

Now implement the changes using your tools (read_file, write_to_file, apply_diff).
"""
            
            # Execute Bob AI to implement changes
            result = subprocess.run(
                ['bob', '-p', command, '--yolo'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Bob AI failed: {result.stderr}")
            
            # Get list of changed files from git
            git_status = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            
            if git_status.returncode != 0:
                raise RuntimeError(f"Git status failed: {git_status.stderr}")
            
            # Parse git status to find changed files
            changes = []
            for line in git_status.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                status = line[:2].strip()
                file_path = line[3:].strip()
                
                # Skip temporary files and analysis files
                if file_path.startswith('tmp') or file_path.startswith('issue_analysis_') or file_path.startswith('issue_') and file_path.endswith('_summary.json'):
                    continue
                
                # Determine action based on git status
                if status == 'A' or status == '??':
                    action = 'create'
                elif status == 'M':
                    action = 'modify'
                elif status == 'D':
                    action = 'delete'
                else:
                    continue  # Skip other statuses
                
                # Verify file exists in workspace (skip if not)
                full_path = os.path.join(self.workspace_dir, file_path)
                if action != 'delete' and not os.path.exists(full_path):
                    # File doesn't exist - might be a git status artifact
                    continue
                
                # Read file content (if not deleted)
                content = None
                if action != 'delete':
                    try:
                        with open(full_path, 'r') as f:
                            content = f.read()
                    except (IOError, UnicodeDecodeError) as e:
                        # Skip files that can't be read (binary files, etc.)
                        continue
                
                # Get diff for modified files
                diff = None
                if action == 'modify':
                    diff_result = subprocess.run(
                        ['git', 'diff', 'HEAD', file_path],
                        cwd=self.workspace_dir,
                        capture_output=True,
                        text=True
                    )
                    if diff_result.returncode == 0:
                        diff = diff_result.stdout
                
                # Count lines
                lines_added = 0
                lines_removed = 0
                if diff:
                    for diff_line in diff.split('\n'):
                        if diff_line.startswith('+') and not diff_line.startswith('+++'):
                            lines_added += 1
                        elif diff_line.startswith('-') and not diff_line.startswith('---'):
                            lines_removed += 1
                elif action == 'create' and content:
                    lines_added = len(content.split('\n'))
                
                changes.append(FileChange(
                    file_path=file_path,
                    action=action,
                    content=content,
                    diff=diff,
                    description=f"{'Created' if action == 'create' else 'Modified' if action == 'modify' else 'Deleted'} by Bob AI",
                    lines_added=lines_added,
                    lines_removed=lines_removed
                ))
            
            if not changes:
                raise RuntimeError("Bob AI did not make any file changes")
            
            # Create CodeChanges object
            code_changes = CodeChanges(
                issue_number=issue_number,
                changes=changes,
                tests_added=[c.file_path for c in changes if 'test' in c.file_path.lower()],
                validation_status='pending',
                validation_errors=[],
                implementation_notes=f"Bob AI implemented {len(changes)} file changes"
            )
            
            # Validate changes
            validation_status, validation_errors = self._validate_changes(code_changes)
            code_changes.validation_status = validation_status
            code_changes.validation_errors = validation_errors
            
            return code_changes
            
        finally:
            # Cleanup temp file
            if os.path.exists(analysis_file):
                os.unlink(analysis_file)
    
    def _parse_changes(self, data: Dict, issue_number: int) -> CodeChanges:
        """
        Parse changes from Bob AI output.
        
        Args:
            data: JSON data from Bob AI
            issue_number: Issue number
            
        Returns:
            CodeChanges object
        """
        changes = []
        
        for change_data in data.get('changes', []):
            change = FileChange(
                file_path=change_data['file'],
                action=change_data.get('action', 'modify'),
                content=change_data.get('content'),
                diff=change_data.get('diff'),
                description=change_data.get('description', ''),
                lines_added=change_data.get('linesAdded', 0),
                lines_removed=change_data.get('linesRemoved', 0)
            )
            changes.append(change)
        
        return CodeChanges(
            issue_number=issue_number,
            changes=changes,
            tests_added=data.get('testsAdded', []),
            validation_status='pending',
            validation_errors=[],
            implementation_notes=data.get('implementationNotes', '')
        )
    
    def _validate_changes(self, changes: CodeChanges) -> tuple[str, List[str]]:
        """
        Validate generated code changes.
        
        Args:
            changes: CodeChanges object
            
        Returns:
            Tuple of (status, errors)
        """
        errors = []
        
        # Check if any changes were generated
        if not changes.changes:
            errors.append("No code changes generated")
            return ('failed', errors)
        
        # Validate each file change
        for change in changes.changes:
            # Check file path is valid
            if not change.file_path:
                errors.append("Empty file path in change")
                continue
            
            # For create/modify, content must be provided
            if change.action in ['create', 'modify']:
                if not change.content:
                    errors.append(f"No content provided for {change.action} action on {change.file_path}")
            
            # For modify, diff should be provided
            if change.action == 'modify':
                if not change.diff:
                    errors.append(f"No diff provided for modify action on {change.file_path}")
            
            # Validate file extension (basic check)
            if change.action == 'create':
                path = Path(change.file_path)
                if not path.suffix:
                    errors.append(f"File has no extension: {change.file_path}")
        
        # Check for syntax errors (basic validation)
        for change in changes.changes:
            if change.content and change.action in ['create', 'modify']:
                syntax_errors = self._check_syntax(change.file_path, change.content)
                errors.extend(syntax_errors)
        
        status = 'passed' if not errors else 'failed'
        return (status, errors)
    
    def _check_syntax(self, file_path: str, content: str) -> List[str]:
        """
        Check syntax of generated code.
        
        Args:
            file_path: File path
            content: File content
            
        Returns:
            List of syntax errors
        """
        errors = []
        ext = Path(file_path).suffix
        
        # Python syntax check
        if ext == '.py':
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                errors.append(f"Python syntax error in {file_path}: {e}")
        
        # JavaScript/TypeScript basic check
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            # Check for basic syntax issues
            if content.count('{') != content.count('}'):
                errors.append(f"Mismatched braces in {file_path}")
            if content.count('(') != content.count(')'):
                errors.append(f"Mismatched parentheses in {file_path}")
        
        # JSON syntax check
        elif ext == '.json':
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"JSON syntax error in {file_path}: {e}")
        
        return errors
    
    def apply_changes_to_workspace(self, changes: CodeChanges) -> bool:
        """
        Apply code changes to workspace files.
        
        Args:
            changes: CodeChanges object
            
        Returns:
            True if successful
            
        Raises:
            RuntimeError: If applying changes fails
        """
        for change in changes.changes:
            file_path = os.path.join(self.workspace_dir, change.file_path)
            
            if change.action == 'create':
                if not change.content:
                    raise ValueError(f"Content required for create action: {change.file_path}")
                
                # Create parent directories if needed
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write new file
                with open(file_path, 'w') as f:
                    f.write(change.content)
            
            elif change.action == 'modify':
                if not change.content:
                    raise ValueError(f"Content required for modify action: {change.file_path}")
                
                # Overwrite existing file
                with open(file_path, 'w') as f:
                    f.write(change.content)
            
            elif change.action == 'delete':
                # Delete file
                if os.path.exists(file_path):
                    os.unlink(file_path)
        
        return True


# Made with Bob