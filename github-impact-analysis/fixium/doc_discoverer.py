"""Discover and categorize all documentation files in repository."""
from pathlib import Path
from typing import Dict, List
from enum import Enum
import re


class DocType(Enum):
    """Types of documentation files."""
    README = "readme"
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    CONTRIBUTING = "contributing"
    CHANGELOG = "changelog"
    ARCHITECTURE = "architecture"
    CONFIGURATION = "configuration"
    TUTORIAL = "tutorial"
    FAQ = "faq"
    OTHER = "other"


class DocumentationDiscoverer:
    """Discover and categorize documentation files."""
    
    # Common documentation directories
    DOC_DIRECTORIES = [
        'docs/', 'doc/', 'documentation/',
        'wiki/', '.github/', 'guides/',
        'tutorials/', 'examples/'
    ]
    
    # File patterns for categorization
    DOC_PATTERNS = {
        DocType.README: [
            r'^README\.md$',
            r'^readme\.md$',
            r'README\..*\.md$'
        ],
        DocType.API_REFERENCE: [
            r'api[-_]?(reference|docs?|guide)?\.md$',
            r'reference\.md$',
            r'endpoints?\.md$',
            r'routes\.md$'
        ],
        DocType.USER_GUIDE: [
            r'user[-_]?guide\.md$',
            r'usage\.md$',
            r'getting[-_]?started\.md$',
            r'quickstart\.md$',
            r'guide\.md$'
        ],
        DocType.DEVELOPER_GUIDE: [
            r'dev(eloper)?[-_]?guide\.md$',
            r'development\.md$',
            r'hacking\.md$',
            r'setup\.md$'
        ],
        DocType.CONTRIBUTING: [
            r'CONTRIBUTING\.md$',
            r'contribute\.md$',
            r'contribution\.md$'
        ],
        DocType.CHANGELOG: [
            r'CHANGELOG\.md$',
            r'HISTORY\.md$',
            r'RELEASES\.md$',
            r'NEWS\.md$'
        ],
        DocType.ARCHITECTURE: [
            r'architecture\.md$',
            r'design\.md$',
            r'technical[-_]?design\.md$',
            r'system[-_]?design\.md$'
        ],
        DocType.CONFIGURATION: [
            r'config(uration)?\.md$',
            r'settings\.md$',
            r'environment\.md$',
            r'env\.md$'
        ],
        DocType.TUTORIAL: [
            r'tutorial\.md$',
            r'walkthrough\.md$',
            r'examples?\.md$',
            r'how[-_]?to\.md$'
        ],
        DocType.FAQ: [
            r'faq\.md$',
            r'questions\.md$',
            r'troubleshooting\.md$'
        ]
    }
    
    # Directories to exclude from search
    EXCLUDED_DIRS = [
        'node_modules', 'vendor', '.git', 'build', 
        'dist', '__pycache__', '.venv', 'venv',
        '.pytest_cache', 'coverage', '.tox'
    ]
    
    def discover_all_docs(self, repo_path: str) -> Dict[DocType, List[str]]:
        """
        Discover all markdown documentation files in repository.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            Dictionary mapping doc types to file paths
            {
                DocType.README: ['README.md'],
                DocType.API_REFERENCE: ['docs/api.md', 'docs/endpoints.md'],
                DocType.USER_GUIDE: ['docs/user-guide.md'],
                ...
            }
        """
        repo = Path(repo_path)
        all_md_files = []
        
        # Find all .md files at root level
        all_md_files.extend(repo.glob('*.md'))
        
        # Search in common doc directories
        for doc_dir in self.DOC_DIRECTORIES:
            dir_path = repo / doc_dir
            if dir_path.exists() and dir_path.is_dir():
                all_md_files.extend(dir_path.rglob('*.md'))
        
        # Filter out excluded directories
        filtered_files = []
        for file_path in all_md_files:
            relative_path = str(file_path.relative_to(repo))
            if not any(excluded in relative_path for excluded in self.EXCLUDED_DIRS):
                filtered_files.append(file_path)
        
        # Categorize files
        categorized = {doc_type: [] for doc_type in DocType}
        
        for file_path in filtered_files:
            relative_path = str(file_path.relative_to(repo))
            doc_type = self._categorize_file(relative_path)
            categorized[doc_type].append(relative_path)
        
        # Remove empty categories
        return {k: sorted(v) for k, v in categorized.items() if v}
    
    def _categorize_file(self, file_path: str) -> DocType:
        """
        Categorize a documentation file by its path/name.
        
        Args:
            file_path: Relative file path
            
        Returns:
            DocType enum value
        """
        filename = Path(file_path).name
        
        for doc_type, patterns in self.DOC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return doc_type
        
        return DocType.OTHER
    
    def get_doc_summary(self, categorized_docs: Dict[DocType, List[str]]) -> str:
        """
        Generate human-readable summary of discovered docs.
        
        Args:
            categorized_docs: Dictionary from discover_all_docs()
            
        Returns:
            Formatted string with doc file listing
        """
        lines = ["📚 Discovered Documentation Files:"]
        
        for doc_type, files in sorted(categorized_docs.items(), key=lambda x: x[0].value):
            if files:
                type_name = doc_type.value.replace('_', ' ').title()
                lines.append(f"\n**{type_name}** ({len(files)} file(s)):")
                for file in files:
                    lines.append(f"  - {file}")
        
        total_files = sum(len(files) for files in categorized_docs.values())
        lines.insert(1, f"\n**Total**: {total_files} documentation file(s)\n")
        
        return "\n".join(lines)
    
    def should_check_file(self, file_path: str, doc_type: DocType) -> bool:
        """
        Determine if a doc file should be checked for updates.
        
        Some files like CHANGELOG.md are auto-generated and shouldn't
        be flagged for manual updates.
        
        Args:
            file_path: Relative file path
            doc_type: Type of documentation file
            
        Returns:
            True if file should be checked for updates
        """
        # Skip auto-generated files
        if doc_type == DocType.CHANGELOG:
            return False
        
        # Skip files in excluded directories
        if any(excluded in file_path for excluded in self.EXCLUDED_DIRS):
            return False
        
        return True
    
    def get_files_by_type(
        self, 
        categorized_docs: Dict[DocType, List[str]], 
        doc_types: List[DocType]
    ) -> List[str]:
        """
        Get all files of specific types.
        
        Args:
            categorized_docs: Dictionary from discover_all_docs()
            doc_types: List of DocType enums to filter
            
        Returns:
            List of file paths matching the types
        """
        files = []
        for doc_type in doc_types:
            if doc_type in categorized_docs:
                files.extend(categorized_docs[doc_type])
        return sorted(files)


# Made with Bob