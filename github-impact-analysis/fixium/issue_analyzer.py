"""Analyze GitHub issues for code implementation."""
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from github import Github
from github.Issue import Issue
import re


class IssueType(Enum):
    """Type of issue."""
    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


@dataclass
class Requirement:
    """A single requirement extracted from issue."""
    description: str
    priority: str  # high, medium, low
    acceptance_criteria: List[str]


@dataclass
class IssueAnalysis:
    """Analysis result for a GitHub issue."""
    issue_number: int
    title: str
    body: str
    issue_type: IssueType
    has_sufficient_context: bool
    missing_context: List[str]
    requirements: List[Requirement]
    affected_files: List[str]
    related_issues: List[int]
    labels: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'issueNumber': self.issue_number,
            'title': self.title,
            'body': self.body,
            'type': self.issue_type.value,
            'hasSufficientContext': self.has_sufficient_context,
            'missingContext': self.missing_context,
            'requirements': [
                {
                    'description': r.description,
                    'priority': r.priority,
                    'acceptanceCriteria': r.acceptance_criteria
                }
                for r in self.requirements
            ],
            'affectedFiles': self.affected_files,
            'relatedIssues': self.related_issues,
            'labels': self.labels
        }


class IssueAnalyzer:
    """Analyze GitHub issues for implementation."""
    
    def __init__(self, github_client: Github, repo_name: str):
        """
        Initialize issue analyzer.
        
        Args:
            github_client: PyGithub client instance
            repo_name: Repository name (owner/repo)
        """
        self.client = github_client
        self.repo = github_client.get_repo(repo_name)
    
    def analyze_issue(self, issue_number: int) -> IssueAnalysis:
        """
        Analyze a GitHub issue.
        
        Args:
            issue_number: Issue number
            
        Returns:
            IssueAnalysis object
        """
        issue = self.repo.get_issue(issue_number)
        
        # Classify issue type
        issue_type = self._classify_issue(issue)
        
        # Check context sufficiency
        has_context, missing = self._check_context_sufficiency(issue, issue_type)
        
        # Extract requirements
        requirements = self._extract_requirements(issue)
        
        # Identify affected files
        affected_files = self._identify_affected_files(issue)
        
        # Find related issues
        related_issues = self._find_related_issues(issue)
        
        return IssueAnalysis(
            issue_number=issue_number,
            title=issue.title,
            body=issue.body or "",
            issue_type=issue_type,
            has_sufficient_context=has_context,
            missing_context=missing,
            requirements=requirements,
            affected_files=affected_files,
            related_issues=related_issues,
            labels=[label.name for label in issue.labels]
        )
    
    def _classify_issue(self, issue: Issue) -> IssueType:
        """
        Classify issue type based on labels and content.
        
        Args:
            issue: GitHub Issue object
            
        Returns:
            IssueType enum
        """
        labels = [label.name.lower() for label in issue.labels]
        
        # Check labels first
        if any(l in labels for l in ['bug', 'defect', 'error']):
            return IssueType.BUG
        if any(l in labels for l in ['feature', 'enhancement', 'improvement']):
            return IssueType.FEATURE if 'feature' in labels else IssueType.ENHANCEMENT
        if any(l in labels for l in ['documentation', 'docs']):
            return IssueType.DOCUMENTATION
        
        # Check title and body
        title_lower = issue.title.lower()
        body_lower = (issue.body or "").lower()
        
        if any(word in title_lower for word in ['bug', 'fix', 'error', 'broken']):
            return IssueType.BUG
        if any(word in title_lower for word in ['add', 'feature', 'implement']):
            return IssueType.FEATURE
        if any(word in title_lower for word in ['improve', 'enhance', 'update']):
            return IssueType.ENHANCEMENT
        
        return IssueType.UNKNOWN
    
    def _check_context_sufficiency(
        self, 
        issue: Issue, 
        issue_type: IssueType
    ) -> Tuple[bool, List[str]]:
        """
        Check if issue has sufficient context for implementation.
        
        Args:
            issue: GitHub Issue object
            issue_type: Classified issue type
            
        Returns:
            Tuple of (has_sufficient_context, missing_context_list)
        """
        missing = []
        body = issue.body or ""
        
        # Common requirements
        if len(body.strip()) < 50:
            missing.append("Detailed description (at least 50 characters)")
        
        # Type-specific requirements
        if issue_type == IssueType.BUG:
            if not self._has_reproduction_steps(body):
                missing.append("Steps to reproduce the bug")
            if not self._has_expected_behavior(body):
                missing.append("Expected behavior vs actual behavior")
        
        elif issue_type == IssueType.FEATURE:
            # For features, require either requirements OR acceptance criteria (not both)
            has_reqs = self._has_requirements(body)
            has_criteria = self._has_acceptance_criteria(body)
            if not has_reqs and not has_criteria:
                missing.append("Clear feature requirements or acceptance criteria")
        
        elif issue_type == IssueType.ENHANCEMENT:
            # For enhancements, be lenient - if it has requirements or criteria, that's enough
            has_reqs = self._has_requirements(body)
            has_criteria = self._has_acceptance_criteria(body)
            has_current = self._has_current_behavior(body)
            has_proposed = self._has_proposed_improvement(body)
            
            # Only require missing context if NONE of these are present
            if not any([has_reqs, has_criteria, has_current, has_proposed]):
                missing.append("Feature requirements, acceptance criteria, or description of proposed changes")
        
        return (len(missing) == 0, missing)
    
    def _has_reproduction_steps(self, text: str) -> bool:
        """Check if text contains reproduction steps."""
        patterns = [
            r'steps?\s+to\s+reproduce',
            r'how\s+to\s+reproduce',
            r'reproduction\s+steps',
            r'\d+\.\s+',  # Numbered list
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _has_expected_behavior(self, text: str) -> bool:
        """Check if text describes expected behavior."""
        patterns = [
            r'expected\s+(behavior|result|output)',
            r'should\s+(be|do|show|return)',
            r'actual\s+(behavior|result|output)',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _has_requirements(self, text: str) -> bool:
        """Check if text contains requirements."""
        patterns = [
            r'requirements?:',
            r'must\s+(have|support|include)',
            r'should\s+(have|support|include)',
            r'needs?\s+to',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _has_acceptance_criteria(self, text: str) -> bool:
        """Check if text contains acceptance criteria."""
        patterns = [
            r'acceptance\s+criteria',
            r'success\s+criteria',
            r'\[\s*[x\s]\s*\]',  # Checkbox list
            r'definition\s+of\s+done',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _has_current_behavior(self, text: str) -> bool:
        """Check if text describes current behavior."""
        patterns = [
            r'current(ly)?',
            r'right\s+now',
            r'at\s+the\s+moment',
            r'as\s+of\s+now',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _has_proposed_improvement(self, text: str) -> bool:
        """Check if text describes proposed improvement."""
        patterns = [
            r'proposed?',
            r'suggestion',
            r'improvement',
            r'better\s+if',
            r'would\s+be\s+nice',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _extract_requirements(self, issue: Issue) -> List[Requirement]:
        """
        Extract requirements from issue.
        
        Args:
            issue: GitHub Issue object
            
        Returns:
            List of Requirement objects
        """
        requirements = []
        body = issue.body or ""
        
        # Extract checkbox items as requirements
        checkbox_pattern = r'-\s*\[\s*[x\s]\s*\]\s*(.+)'
        checkboxes = re.findall(checkbox_pattern, body, re.MULTILINE)
        
        for checkbox in checkboxes:
            requirements.append(Requirement(
                description=checkbox.strip(),
                priority='medium',
                acceptance_criteria=[]
            ))
        
        # Extract numbered requirements
        numbered_pattern = r'^\d+\.\s+(.+)$'
        numbered = re.findall(numbered_pattern, body, re.MULTILINE)
        
        for item in numbered:
            if item.strip() and len(item.strip()) > 10:
                requirements.append(Requirement(
                    description=item.strip(),
                    priority='medium',
                    acceptance_criteria=[]
                ))
        
        # If no structured requirements found, create one from title
        if not requirements:
            requirements.append(Requirement(
                description=issue.title,
                priority='high',
                acceptance_criteria=[]
            ))
        
        return requirements
    
    def _identify_affected_files(self, issue: Issue) -> List[str]:
        """
        Identify files that might be affected by this issue.
        
        Args:
            issue: GitHub Issue object
            
        Returns:
            List of file paths
        """
        affected = []
        body = issue.body or ""
        
        # Look for file paths in backticks or code blocks
        file_patterns = [
            r'`([a-zA-Z0-9_/\-\.]+\.[a-zA-Z0-9]+)`',  # `path/to/file.ext`
            r'```[a-z]*\n([a-zA-Z0-9_/\-\.]+\.[a-zA-Z0-9]+)',  # In code blocks
            r'(?:file|path|in):\s*([a-zA-Z0-9_/\-\.]+\.[a-zA-Z0-9]+)',  # file: path
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, body, re.MULTILINE)
            affected.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        return [f for f in affected if not (f in seen or seen.add(f))]
    
    def _find_related_issues(self, issue: Issue) -> List[int]:
        """
        Find related issues mentioned in the issue.
        
        Args:
            issue: GitHub Issue object
            
        Returns:
            List of issue numbers
        """
        body = issue.body or ""
        
        # Look for #123 style references
        pattern = r'#(\d+)'
        matches = re.findall(pattern, body)
        
        # Convert to integers and remove duplicates
        return list(set(int(m) for m in matches if int(m) != issue.number))


# Made with Bob