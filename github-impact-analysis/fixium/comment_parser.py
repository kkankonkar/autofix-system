"""Parse Fixium commands from PR comments."""
import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class FilterOptions:
    """Filter options for code review."""
    severity: Optional[list[str]] = None
    type: Optional[list[str]] = None
    exclude_severity: Optional[list[str]] = None
    exclude_type: Optional[list[str]] = None
    
    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments for submit_pr_comments.sh."""
        args = []
        if self.severity:
            args.extend(['--severity', ','.join(self.severity)])
        if self.type:
            args.extend(['--type', ','.join(self.type)])
        if self.exclude_severity:
            args.extend(['--exclude-severity', ','.join(self.exclude_severity)])
        if self.exclude_type:
            args.extend(['--exclude-type', ','.join(self.exclude_type)])
        return args
    
    def __str__(self) -> str:
        """Human-readable filter description."""
        parts = []
        if self.severity:
            parts.append(f"Severity: {', '.join(self.severity)}")
        if self.type:
            parts.append(f"Type: {', '.join(self.type)}")
        if self.exclude_severity:
            parts.append(f"Excluding severity: {', '.join(self.exclude_severity)}")
        if self.exclude_type:
            parts.append(f"Excluding type: {', '.join(self.exclude_type)}")
        return ' | '.join(parts) if parts else "No filters"


@dataclass
class DocUpdateOptions:
    """Options for documentation update analysis."""
    skip_classification: bool = False  # Force analysis even for minor changes
    focus_files: Optional[list[str]] = None  # Specific doc files to check
    
    def __str__(self) -> str:
        """Human-readable options description."""
        parts = []
        if self.skip_classification:
            parts.append("Skip classification (force analysis)")
        if self.focus_files:
            parts.append(f"Focus files: {', '.join(self.focus_files)}")
        return ' | '.join(parts) if parts else "No special options"


@dataclass
class FixiumCommand:
    """Parsed Fixium command."""
    command: str
    filters: FilterOptions = field(default_factory=FilterOptions)
    doc_options: DocUpdateOptions = field(default_factory=DocUpdateOptions)
    raw_comment: str = ""
    
    def is_valid(self) -> bool:
        """Check if command is valid."""
        return self.command in ['review', 'updatedocs', 'implementfix', 'analyzeimpact']


class CommentParser:
    """Parser for Fixium PR comments."""
    
    COMMAND_PATTERN = r'Fixium:(\w+)'
    SEVERITY_PATTERN = r'--severity\s+([^\s]+)'
    TYPE_PATTERN = r'--type\s+([^\s]+)'
    EXCLUDE_SEVERITY_PATTERN = r'--exclude-severity\s+([^\s]+)'
    EXCLUDE_TYPE_PATTERN = r'--exclude-type\s+([^\s]+)'
    
    # Doc update options patterns
    FORCE_PATTERN = r'--force'
    FILES_PATTERN = r'--files\s+([^\s]+)'
    
    VALID_SEVERITIES = {'critical', 'high', 'medium', 'low'}
    VALID_TYPES = {'bug', 'security', 'maintainability', 'performance'}
    
    @classmethod
    def parse(cls, comment_body: str) -> Optional[FixiumCommand]:
        """
        Parse Fixium command from comment body.
        
        Args:
            comment_body: The PR comment text
            
        Returns:
            FixiumCommand if valid command found, None otherwise
        """
        # Extract command
        command_match = re.search(cls.COMMAND_PATTERN, comment_body, re.IGNORECASE)
        if not command_match:
            return None
        
        command = command_match.group(1).lower()
        
        # Extract filter options (for review command)
        filters = FilterOptions(
            severity=cls._parse_list_option(comment_body, cls.SEVERITY_PATTERN),
            type=cls._parse_list_option(comment_body, cls.TYPE_PATTERN),
            exclude_severity=cls._parse_list_option(comment_body, cls.EXCLUDE_SEVERITY_PATTERN),
            exclude_type=cls._parse_list_option(comment_body, cls.EXCLUDE_TYPE_PATTERN)
        )
        
        # Extract doc update options (for updatedocs command)
        doc_options = DocUpdateOptions(
            skip_classification=bool(re.search(cls.FORCE_PATTERN, comment_body)),
            focus_files=cls._parse_list_option(comment_body, cls.FILES_PATTERN)
        )
        
        return FixiumCommand(
            command=command,
            filters=filters,
            doc_options=doc_options,
            raw_comment=comment_body
        )
    
    @classmethod
    def _parse_list_option(cls, text: str, pattern: str) -> Optional[list[str]]:
        """Parse comma-separated list option."""
        match = re.search(pattern, text)
        if not match:
            return None
        
        values = [v.strip().lower() for v in match.group(1).split(',')]
        return values if values else None
    
    @classmethod
    def validate_filters(cls, filters: FilterOptions) -> list[str]:
        """
        Validate filter options.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate severity values
        if filters.severity:
            invalid = set(filters.severity) - cls.VALID_SEVERITIES
            if invalid:
                errors.append(f"Invalid severity values: {', '.join(invalid)}")
        
        if filters.exclude_severity:
            invalid = set(filters.exclude_severity) - cls.VALID_SEVERITIES
            if invalid:
                errors.append(f"Invalid exclude-severity values: {', '.join(invalid)}")
        
        # Validate type values
        if filters.type:
            invalid = set(filters.type) - cls.VALID_TYPES
            if invalid:
                errors.append(f"Invalid type values: {', '.join(invalid)}")
        
        if filters.exclude_type:
            invalid = set(filters.exclude_type) - cls.VALID_TYPES
            if invalid:
                errors.append(f"Invalid exclude-type values: {', '.join(invalid)}")
        
        return errors

# Made with Bob
