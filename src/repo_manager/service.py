"""Repository management utilities for cloning, editing, and pushing fixes."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from git import Repo


class RepoManager:
    """Manage temporary working copies of GitHub repositories."""

    def __init__(self, github_token: Optional[str] = None, workspace_root: Optional[str] = None) -> None:
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.workspace_root = Path(workspace_root or tempfile.gettempdir()) / "autofix-system-repos"
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def find_file_in_repo(self, checkout_dir: Path, partial_path: str) -> Optional[str]:
        """
        Find a file in the repository by searching for partial path matches.
        Handles cases where stack traces contain absolute paths like /app/consumer/file.py
        but the actual repo path is consumer/file.py or src/consumer/file.py.
        
        Args:
            checkout_dir: Repository checkout directory
            partial_path: Partial or absolute path from error log
            
        Returns:
            Relative path from repo root if found, None otherwise
        """
        # Clean the path - remove leading slashes and common prefixes
        clean_path = partial_path.lstrip('/')
        
        # Extract just the filename
        filename = Path(partial_path).name
        
        # Strategy 1: Try the path as-is (relative)
        if (checkout_dir / clean_path).exists():
            return clean_path
        
        # Strategy 2: Search for the filename in the repository
        matching_files = []
        for file_path in checkout_dir.rglob(filename):
            if file_path.is_file():
                rel_path = file_path.relative_to(checkout_dir)
                matching_files.append(str(rel_path))
        
        # If we found exactly one match, use it
        if len(matching_files) == 1:
            return matching_files[0]
        
        # Strategy 3: Try to match the path suffix
        # e.g., /app/consumer/billing.py -> consumer/billing.py or src/consumer/billing.py
        path_parts = Path(clean_path).parts
        for i in range(len(path_parts)):
            suffix_path = Path(*path_parts[i:])
            if (checkout_dir / suffix_path).exists():
                return str(suffix_path)
        
        # Strategy 4: If multiple matches, try to find best match by path similarity
        if len(matching_files) > 1:
            # Prefer matches that contain more of the original path components
            best_match = None
            best_score = 0
            
            for match in matching_files:
                score = sum(1 for part in path_parts if part in Path(match).parts)
                if score > best_score:
                    best_score = score
                    best_match = match
            
            if best_match:
                return best_match
        
        return None

    def _build_authenticated_url(self, repository_url: str) -> str:
        """Embed token in GitHub HTTPS URL for clone/push operations."""
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN is required for repository operations")

        parsed = urlparse(repository_url)
        if parsed.scheme != "https" or parsed.netloc != "github.com":
            raise ValueError("Only https://github.com repository URLs are supported")

        return f"https://x-access-token:{self.github_token}@github.com{parsed.path}"

    def repo_name_from_url(self, repository_url: str) -> str:
        """Extract owner/repo from a GitHub URL."""
        parsed = urlparse(repository_url)
        repo_path = parsed.path.strip("/")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]
        if "/" not in repo_path:
            raise ValueError("Repository URL must include owner/repo")
        return repo_path

    def prepare_repository(self, repository_url: str, branch_name: str, base_branch: str = "main") -> tuple[Repo, Path]:
        """Clone a repository into a temporary directory and create a fix branch."""
        repo_slug = self.repo_name_from_url(repository_url).replace("/", "-")
        checkout_dir = self.workspace_root / f"{repo_slug}-{branch_name}"

        if checkout_dir.exists():
            shutil.rmtree(checkout_dir)

        authenticated_url = self._build_authenticated_url(repository_url)
        repo = Repo.clone_from(authenticated_url, checkout_dir)

        origin = repo.remote("origin")
        origin.fetch()

        repo.git.checkout(base_branch)
        repo.git.checkout("-b", branch_name)
        return repo, checkout_dir

    def write_file(self, checkout_dir: Path, file_path: str, content: str) -> Path:
        """Write updated file content into the working tree."""
        target_path = checkout_dir / file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return target_path

    def replace_code_snippet(
        self,
        checkout_dir: Path,
        file_path: str,
        original_code: str,
        fixed_code: str,
    ) -> Path:
        """Replace an exact code snippet inside a target file with fuzzy matching fallback."""
        if not original_code.strip():
            raise ValueError("original_code is required for surgical replacement")

        target_path = checkout_dir / file_path
        if not target_path.exists():
            raise ValueError(f"Target file not found: {file_path}")

        existing_content = target_path.read_text(encoding="utf-8")
        
        # Try exact match first
        if original_code in existing_content:
            updated_content = existing_content.replace(original_code, fixed_code, 1)
            target_path.write_text(updated_content, encoding="utf-8")
            return target_path
        
        # Fallback: Try fuzzy matching with normalized whitespace
        normalized_original = self._normalize_code(original_code)
        lines = existing_content.split('\n')
        
        for i in range(len(lines)):
            # Try to match starting from each line
            for length in range(1, min(50, len(lines) - i + 1)):
                snippet = '\n'.join(lines[i:i+length])
                if self._normalize_code(snippet) == normalized_original:
                    # Found a match! Replace it
                    before = '\n'.join(lines[:i])
                    after = '\n'.join(lines[i+length:])
                    updated_content = before + ('\n' if before else '') + fixed_code + ('\n' if after else '') + after
                    target_path.write_text(updated_content, encoding="utf-8")
                    return target_path
        
        # If still not found, provide helpful error message
        raise ValueError(
            f"original_code snippet was not found in target file.\n"
            f"This usually means the AI generated a fix without seeing the actual file content.\n"
            f"Consider using write_file instead of replace_code_snippet, or ensure the AI has access to the actual file."
        )
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for fuzzy matching by removing extra whitespace."""
        lines = [line.strip() for line in code.strip().split('\n')]
        return '\n'.join(line for line in lines if line)

    def replace_lines_in_file(
        self,
        checkout_dir: Path,
        file_path: str,
        start_line: int,
        end_line: int,
        fixed_code: str,
    ) -> Path:
        """Replace specific lines in a file (line numbers are 1-based)."""
        target_path = checkout_dir / file_path
        if not target_path.exists():
            raise ValueError(f"Target file not found: {file_path}")
        
        lines = target_path.read_text(encoding="utf-8").split('\n')
        
        # Convert to 0-based indexing
        start_idx = start_line - 1
        end_idx = end_line
        
        # Validate line numbers
        if start_idx < 0 or end_idx > len(lines):
            raise ValueError(f"Invalid line range: {start_line}-{end_line} (file has {len(lines)} lines)")
        
        # Replace the lines
        fixed_lines = fixed_code.split('\n')
        new_lines = lines[:start_idx] + fixed_lines + lines[end_idx:]
        
        target_path.write_text('\n'.join(new_lines), encoding="utf-8")
        return target_path

    def commit_and_push(self, repo: Repo, branch_name: str, commit_message: str) -> None:
        """Commit local changes and push the fix branch."""
        repo.git.add(A=True)

        if not repo.is_dirty(untracked_files=True):
            raise ValueError("No repository changes found to commit")

        repo.index.commit(commit_message)
        repo.remote("origin").push(refspec=f"{branch_name}:{branch_name}")

    def cleanup(self, checkout_dir: Path) -> None:
        """Remove temporary checkout directory."""
        if checkout_dir.exists():
            shutil.rmtree(checkout_dir)


# Made with Bob