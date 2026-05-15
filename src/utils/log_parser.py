"""
Log parsing utilities for extracting multiple errors from log files.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ErrorBlock:
    """Represents a single error extracted from a log file."""
    error_message: str
    stack_trace: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    error_type: Optional[str] = None
    context_lines: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.context_lines is None:
            self.context_lines = []


class MultiErrorExtractor:
    """Extract multiple distinct errors from a log file."""
    
    # Common error patterns across different languages
    ERROR_PATTERNS = [
        # Python
        r'(?:Traceback.*?(?=\n(?:Traceback|$)))',
        r'(?:.*?Error:.*)',
        r'(?:.*?Exception:.*)',
        
        # JavaScript/TypeScript
        r'(?:.*?Error:.*(?:\n\s+at\s+.*)*)',
        r'(?:Uncaught.*)',
        
        # Java
        r'(?:.*?Exception:.*(?:\n\s+at\s+.*)*)',
        
        # Go
        r'(?:panic:.*(?:\n.*goroutine.*)*)',
        
        # Generic
        r'(?:ERROR.*)',
        r'(?:FATAL.*)',
        r'(?:\[ERROR\].*)',
    ]
    
    # File path patterns in stack traces
    FILE_PATH_PATTERNS = [
        r'File ["\']([^"\']+)["\'],?\s+line\s+(\d+)',  # Python: File "path/file.py", line 42
        r'at\s+(?:[^\s]+\s+)?\(([^:)]+):(\d+):?\d*\)',  # JS: at func (file.js:42:10)
        r'at\s+([^\s:]+):(\d+)',  # Generic: at file.py:42
        r'in\s+([^\s:]+):(\d+)',  # Generic: in file.py:42
        r'([a-zA-Z0-9_/.\-]+\.(py|js|ts|java|go|rb|php|cpp|c|h|cs|swift|kt)):(\d+)',  # file.ext:line
    ]
    
    # Error type patterns
    ERROR_TYPE_PATTERNS = [
        r'(\w+Error):',  # Python/JS: TypeError:, ValueError:
        r'(\w+Exception):',  # Java/Python: NullPointerException:
        r'Uncaught\s+(\w+)',  # JS: Uncaught TypeError
        r'\[(\w+)\]',  # Generic: [ERROR]
    ]
    
    def __init__(self, max_errors: int = 3):
        """
        Initialize the extractor.
        
        Args:
            max_errors: Maximum number of errors to extract (default: 3)
        """
        self.max_errors = max_errors
    
    def extract_errors(self, raw_log: str) -> List[ErrorBlock]:
        """
        Extract up to max_errors distinct errors from log content.
        
        Args:
            raw_log: Raw log file content
            
        Returns:
            List of ErrorBlock objects, up to max_errors
        """
        errors = []
        lines = raw_log.split('\n')
        
        # Strategy 1: Find error blocks using patterns
        error_blocks = self._find_error_blocks(raw_log)
        
        # Strategy 2: If no structured errors found, look for ERROR/FATAL lines
        if not error_blocks:
            error_blocks = self._find_error_lines(lines)
        
        # Process each error block
        for block_text in error_blocks[:self.max_errors]:
            error = self._parse_error_block(block_text)
            if error and error.error_message.strip():
                errors.append(error)
        
        # Deduplicate errors (same error type and file)
        errors = self._deduplicate_errors(errors)
        
        return errors[:self.max_errors]
    
    def _find_error_blocks(self, raw_log: str) -> List[str]:
        """Find error blocks using regex patterns."""
        blocks = []
        
        for pattern in self.ERROR_PATTERNS:
            matches = re.finditer(pattern, raw_log, re.MULTILINE | re.DOTALL)
            for match in matches:
                block = match.group(0).strip()
                if len(block) > 10:  # Minimum length to be meaningful
                    blocks.append(block)
        
        return blocks
    
    def _find_error_lines(self, lines: List[str]) -> List[str]:
        """Find lines containing ERROR or FATAL keywords."""
        error_blocks = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            lower_line = line.lower()
            
            # Check if line contains error indicators
            if any(keyword in lower_line for keyword in ['error', 'fatal', 'exception', 'traceback']):
                # Collect this line and following context (up to 10 lines or until blank line)
                block_lines = [line]
                j = i + 1
                
                while j < len(lines) and j < i + 10:
                    next_line = lines[j]
                    if not next_line.strip():
                        break
                    # Include indented lines (likely stack trace)
                    if next_line.startswith((' ', '\t')) or ':' in next_line:
                        block_lines.append(next_line)
                    else:
                        break
                    j += 1
                
                error_blocks.append('\n'.join(block_lines))
                i = j
            else:
                i += 1
        
        return error_blocks
    
    def _parse_error_block(self, block_text: str) -> Optional[ErrorBlock]:
        """Parse an error block to extract structured information."""
        # Extract error message (first non-empty line)
        lines = [l for l in block_text.split('\n') if l.strip()]
        if not lines:
            return None
        
        error_message = lines[0].strip()
        
        # Extract error type
        error_type = self._extract_error_type(block_text)
        
        # Extract file path and line number
        file_path, line_number = self._extract_file_info(block_text)
        
        # Get context lines (up to 5 lines)
        context_lines = lines[:5]
        
        return ErrorBlock(
            error_message=error_message,
            stack_trace=block_text,
            file_path=file_path,
            line_number=line_number,
            error_type=error_type,
            context_lines=context_lines
        )
    
    def _extract_error_type(self, text: str) -> Optional[str]:
        """Extract error type from error text."""
        for pattern in self.ERROR_TYPE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Fallback: look for common error keywords
        text_lower = text.lower()
        if 'typeerror' in text_lower:
            return 'TypeError'
        elif 'nullpointer' in text_lower or 'null' in text_lower:
            return 'NullPointerException'
        elif 'syntax' in text_lower:
            return 'SyntaxError'
        elif 'reference' in text_lower:
            return 'ReferenceError'
        elif 'index' in text_lower:
            return 'IndexError'
        
        return 'UnknownError'
    
    def _extract_file_info(self, text: str) -> tuple[Optional[str], Optional[int]]:
        """Extract file path and line number from error text."""
        for pattern in self.FILE_PATH_PATTERNS:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    file_path = groups[0] if groups[0] else groups[-2]
                    line_number = int(groups[1] if len(groups) == 2 else groups[-1])
                    return file_path, line_number
        
        return None, None
    
    def _deduplicate_errors(self, errors: List[ErrorBlock]) -> List[ErrorBlock]:
        """Remove duplicate errors based on error type and file path."""
        seen = set()
        unique_errors = []
        
        for error in errors:
            # Create a key based on error type and file path
            key = (error.error_type, error.file_path)
            
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)
        
        return unique_errors


def extract_multiple_errors(raw_log: str, max_errors: int = 3) -> List[Dict]:
    """
    Convenience function to extract multiple errors from a log file.
    
    Args:
        raw_log: Raw log file content
        max_errors: Maximum number of errors to extract (default: 3)
        
    Returns:
        List of error dictionaries
    """
    extractor = MultiErrorExtractor(max_errors=max_errors)
    error_blocks = extractor.extract_errors(raw_log)
    
    return [
        {
            'error_message': block.error_message,
            'stack_trace': block.stack_trace,
            'file_path': block.file_path,
            'line_number': block.line_number,
            'error_type': block.error_type,
            'context_lines': block.context_lines,
        }
        for block in error_blocks
    ]


# Made with Bob