"""Execute documentation analysis workflow."""
from pathlib import Path
from typing import Optional, Dict
import subprocess
import json

from .change_classifier import ChangeClassifier
from .doc_discoverer import DocumentationDiscoverer


class DocRunner:
    """Run documentation gap analysis."""
    
    def __init__(self, workspace_dir: str, script_dir: Optional[str] = None):
        """
        Initialize documentation runner.
        
        Args:
            workspace_dir: Working directory (repository root)
            script_dir: Directory containing review_workflow.sh (defaults to parent of this file)
        """
        self.workspace_dir = workspace_dir
        if script_dir:
            self.script_dir = script_dir
        else:
            # Default: parent directory of this Python file (where scripts are)
            import os
            self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.classifier = ChangeClassifier()
        self.discoverer = DocumentationDiscoverer()
    
    def analyze_pr_docs(
        self, 
        pr_number: int,
        pr_files: list[str],
        commit_messages: list[str],
        pr_title: Optional[str],
        output_file: str,
        skip_classification: bool = False
    ) -> Dict:
        """
        Analyze PR for documentation gaps.
        
        Args:
            pr_number: Pull request number
            pr_files: List of files changed in PR
            commit_messages: List of commit messages
            pr_title: PR title
            output_file: Output JSON file path
            skip_classification: Force analysis even for minor changes
            
        Returns:
            Dictionary with analysis results
            
        Raises:
            RuntimeError: If analysis fails
        """
        # Discover all documentation files
        print("  Discovering documentation files...")
        docs = self.discoverer.discover_all_docs(self.workspace_dir)
        doc_count = sum(len(files) for files in docs.values())
        print(f"  Found {doc_count} documentation file(s)")
        
        # Classify changes (unless skipped)
        if not skip_classification:
            print("  Classifying PR changes...")
            classification = self.classifier.classify_pr(
                pr_files, 
                commit_messages,
                pr_title
            )
            
            print(f"  Classification: {classification['classification'].value}")
            print(f"  Should analyze docs: {classification['should_analyze_docs']}")
            
            if not classification['should_analyze_docs']:
                # Return early - no analysis needed
                return {
                    'prNumber': pr_number,
                    'changeClassification': {
                        'type': classification['classification'].value,
                        'confidence': classification['confidence'],
                        'reasons': classification['reasons']
                    },
                    'shouldUpdateDocs': False,
                    'discoveredDocs': {k.value: v for k, v in docs.items()},
                    'documentationGaps': [],
                    'summary': {
                        'totalDocsDiscovered': doc_count,
                        'totalGaps': 0
                    }
                }
        else:
            print("  Skipping classification (forced analysis)")
            classification = None
        
        # Run documentation analysis via Bob AI
        print("  Running documentation gap analysis...")
        success = self.run_doc_analysis(pr_number, output_file, docs, pr_files)
        
        if not success:
            raise RuntimeError("Documentation analysis failed")
        
        # Read and return results
        output_path = Path(self.workspace_dir) / output_file
        if not output_path.exists():
            raise RuntimeError(f"Analysis output file not found: {output_file}")
        
        with open(output_path) as f:
            results = json.load(f)
        
        return results
    
    def run_doc_analysis(
        self, 
        pr_number: int, 
        output_file: str,
        discovered_docs: Dict,
        pr_files: list[str]
    ) -> bool:
        """
        Execute Bob AI documentation analysis via shell script.
        
        Args:
            pr_number: Pull request number
            output_file: Output JSON file path
            discovered_docs: Dictionary of discovered documentation files
            pr_files: List of files changed in PR
            
        Returns:
            True if successful
            
        Raises:
            TimeoutError: If analysis times out
            RuntimeError: If analysis fails
        """
        script_path = Path(self.script_dir) / 'review_workflow.sh'
        
        if not script_path.exists():
            raise FileNotFoundError(f"Review script not found: {script_path}")
        
        cmd = [
            str(script_path),
            'analyze-docs',
            str(pr_number),
            output_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes
                check=True
            )
            return True
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Documentation analysis timed out after 1800s")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Documentation analysis failed: {error_msg}")
    
    def check_scripts_exist(self) -> Dict[str, bool]:
        """
        Check if required scripts exist.
        
        Returns:
            Dict with script names and existence status
        """
        scripts = {
            'review_workflow.sh': Path(self.script_dir) / 'review_workflow.sh'
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