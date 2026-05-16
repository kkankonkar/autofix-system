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
class FixiumCommand:
    """Parsed Fixium command."""
    command: str
    filters: FilterOptions = field(default_factory=FilterOptions)
    raw_comment: str = ""
    instruction: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if command is valid."""
        return self.command in ['review', 'implement']


class CommentParser:
    """Parser for Fixium PR comments."""
    
    COMMAND_PATTERN = r'Fixium:(\w+)'
    SEVERITY_PATTERN = r'--severity\s+([^\s]+)'
    TYPE_PATTERN = r'--type\s+([^\s]+)'
    EXCLUDE_SEVERITY_PATTERN = r'--exclude-severity\s+([^\s]+)'
    EXCLUDE_TYPE_PATTERN = r'--exclude-type\s+([^\s]+)'
    
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
        
        # Extract filter options
        filters = FilterOptions(
            severity=cls._parse_list_option(comment_body, cls.SEVERITY_PATTERN),
            type=cls._parse_list_option(comment_body, cls.TYPE_PATTERN),
            exclude_severity=cls._parse_list_option(comment_body, cls.EXCLUDE_SEVERITY_PATTERN),
            exclude_type=cls._parse_list_option(comment_body, cls.EXCLUDE_TYPE_PATTERN)
        )
        instruction = cls._parse_instruction(comment_body, command_match.end(), command)
        
        return FixiumCommand(
            command=command,
            filters=filters,
            raw_comment=comment_body,
            instruction=instruction
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
    def _parse_instruction(cls, text: str, command_end: int, command: str) -> Optional[str]:
        """Parse optional freeform instruction text after the command."""
        if command != 'implement':
            return None

        remainder = text[command_end:].strip()
        if not remainder:
            return None

        # Strip known filter flags if they are present accidentally.
        remainder = re.sub(r'--severity\s+[^\s]+', '', remainder, flags=re.IGNORECASE)
        remainder = re.sub(r'--type\s+[^\s]+', '', remainder, flags=re.IGNORECASE)
        remainder = re.sub(r'--exclude-severity\s+[^\s]+', '', remainder, flags=re.IGNORECASE)
        remainder = re.sub(r'--exclude-type\s+[^\s]+', '', remainder, flags=re.IGNORECASE)

        normalized = ' '.join(remainder.split()).strip(' -:')
        return normalized or None

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
    
    @classmethod
    def parse_review_comment_body(cls, comment_body: str) -> dict[str, str]:
        """
        Parse a Fixium review comment to extract structured data.
        
        Args:
            comment_body: Full review comment markdown
            
        Returns:
            Dict with: severity, type, issue, suggestion, details, bob_fixable
        """
        result = {
            'severity': 'unknown',
            'type': 'unknown',
            'issue': '',
            'suggestion': '',
            'details': '',
            'bob_fixable': False
        }
        
        # Extract severity and type from header
        # Format: 🟡 MEDIUM SEVERITY | 🔧 MAINTAINABILITY
        header_match = re.search(
            r'(🔴|🟡|🔵|⚪)\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*SEVERITY\s*\|\s*[🔧🐛🔒⚡🎨]\s*(\w+)',
            comment_body,
            re.IGNORECASE
        )
        if header_match:
            result['severity'] = header_match.group(2).lower()
            result['type'] = header_match.group(3).lower()
        
        # Extract issue (between "Issue:" and next section)
        issue_match = re.search(
            r'Issue:\s*(.+?)(?=\n\n|Details:|Suggestion:|bob_fixable:|$)',
            comment_body,
            re.DOTALL
        )
        if issue_match:
            result['issue'] = issue_match.group(1).strip()
        
        # Extract suggestion
        suggestion_match = re.search(
            r'Suggestion:\s*(.+?)(?=\n\n|Details:|bob_fixable:|$)',
            comment_body,
            re.DOTALL
        )
        if suggestion_match:
            result['suggestion'] = suggestion_match.group(1).strip()
        
        # Extract details
        details_match = re.search(
            r'Details:\s*(.+?)(?=\n\n|Suggestion:|bob_fixable:|$)',
            comment_body,
            re.DOTALL
        )
        if details_match:
            result['details'] = details_match.group(1).strip()
        
        # Check bob_fixable flag
        result['bob_fixable'] = 'bob_fixable: true' in comment_body.lower()
        
        return result

# Made with Bob
