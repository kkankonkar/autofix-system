"""Tests for comment parser module."""
import pytest
from fixium.comment_parser import CommentParser, FixiumCommand, FilterOptions


class TestFilterOptions:
    """Test FilterOptions dataclass."""
    
    def test_to_cli_args_empty(self):
        """Test CLI args with no filters."""
        filters = FilterOptions()
        assert filters.to_cli_args() == []
    
    def test_to_cli_args_severity(self):
        """Test CLI args with severity filter."""
        filters = FilterOptions(severity=['high', 'medium'])
        assert filters.to_cli_args() == ['--severity', 'high,medium']
    
    def test_to_cli_args_type(self):
        """Test CLI args with type filter."""
        filters = FilterOptions(type=['bug', 'security'])
        assert filters.to_cli_args() == ['--type', 'bug,security']
    
    def test_to_cli_args_exclude(self):
        """Test CLI args with exclude filters."""
        filters = FilterOptions(
            exclude_severity=['low'],
            exclude_type=['maintainability']
        )
        expected = ['--exclude-severity', 'low', '--exclude-type', 'maintainability']
        assert filters.to_cli_args() == expected
    
    def test_to_cli_args_combined(self):
        """Test CLI args with multiple filters."""
        filters = FilterOptions(
            severity=['high'],
            type=['bug'],
            exclude_severity=['low']
        )
        expected = ['--severity', 'high', '--type', 'bug', '--exclude-severity', 'low']
        assert filters.to_cli_args() == expected
    
    def test_str_no_filters(self):
        """Test string representation with no filters."""
        filters = FilterOptions()
        assert str(filters) == "No filters"
    
    def test_str_with_filters(self):
        """Test string representation with filters."""
        filters = FilterOptions(severity=['high'], type=['bug'])
        result = str(filters)
        assert 'Severity: high' in result
        assert 'Type: bug' in result


class TestFixiumCommand:
    """Test FixiumCommand dataclass."""
    
    def test_is_valid_review(self):
        """Test valid review command."""
        cmd = FixiumCommand(command='review')
        assert cmd.is_valid()
    
    def test_is_valid_invalid(self):
        """Test invalid command."""
        cmd = FixiumCommand(command='invalid')
        assert not cmd.is_valid()


class TestCommentParser:
    """Test CommentParser class."""
    
    def test_parse_simple_command(self):
        """Test parsing simple Fixium:review command."""
        comment = "Fixium:review"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.command == 'review'
        assert cmd.filters.severity is None
        assert cmd.filters.type is None
    
    def test_parse_case_insensitive(self):
        """Test case insensitive parsing."""
        comment = "FIXIUM:REVIEW"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.command == 'review'
    
    def test_parse_with_severity(self):
        """Test parsing with severity filter."""
        comment = "Fixium:review --severity high,medium"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.filters.severity == ['high', 'medium']
    
    def test_parse_with_type(self):
        """Test parsing with type filter."""
        comment = "Fixium:review --type bug,security"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.filters.type == ['bug', 'security']
    
    def test_parse_with_exclude(self):
        """Test parsing with exclude filters."""
        comment = "Fixium:review --exclude-severity low --exclude-type maintainability"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.filters.exclude_severity == ['low']
        assert cmd.filters.exclude_type == ['maintainability']
    
    def test_parse_combined_filters(self):
        """Test parsing with multiple filters."""
        comment = "Fixium:review --severity high --type bug,security --exclude-severity low"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.filters.severity == ['high']
        assert cmd.filters.type == ['bug', 'security']
        assert cmd.filters.exclude_severity == ['low']
    
    def test_parse_no_command(self):
        """Test parsing comment without Fixium command."""
        comment = "This is just a regular comment"
        cmd = CommentParser.parse(comment)
        
        assert cmd is None
    
    def test_parse_with_extra_text(self):
        """Test parsing with extra text around command."""
        comment = "Hey team, can you Fixium:review --severity high please?"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.command == 'review'
        assert cmd.filters.severity == ['high']
    
    def test_validate_filters_valid(self):
        """Test validation with valid filters."""
        filters = FilterOptions(
            severity=['high', 'medium'],
            type=['bug', 'security']
        )
        errors = CommentParser.validate_filters(filters)
        
        assert errors == []
    
    def test_validate_filters_invalid_severity(self):
        """Test validation with invalid severity."""
        filters = FilterOptions(severity=['high', 'invalid'])
        errors = CommentParser.validate_filters(filters)
        
        assert len(errors) == 1
        assert 'invalid' in errors[0].lower()
    
    def test_validate_filters_invalid_type(self):
        """Test validation with invalid type."""
        filters = FilterOptions(type=['bug', 'invalid'])
        errors = CommentParser.validate_filters(filters)
        
        assert len(errors) == 1
        assert 'invalid' in errors[0].lower()
    
    def test_validate_filters_multiple_errors(self):
        """Test validation with multiple errors."""
        filters = FilterOptions(
            severity=['invalid1'],
            type=['invalid2']
        )
        errors = CommentParser.validate_filters(filters)
        
        assert len(errors) == 2
    
    def test_validate_filters_exclude_invalid(self):
        """Test validation with invalid exclude filters."""
        filters = FilterOptions(
            exclude_severity=['invalid'],
            exclude_type=['invalid']
        )
        errors = CommentParser.validate_filters(filters)
        
        assert len(errors) == 2

# Made with Bob
