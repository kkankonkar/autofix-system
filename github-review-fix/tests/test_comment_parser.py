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
    
    def test_is_valid_implement(self):
        """Test valid implement command."""
        cmd = FixiumCommand(command='implement')
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
    
    def test_parse_implement_without_instruction(self):
        """Test parsing implement command without freeform instruction."""
        comment = "Fixium:implement"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.command == 'implement'
        assert cmd.instruction is None
    
    def test_parse_implement_with_instruction(self):
        """Test parsing implement command with freeform instruction."""
        comment = "Fixium:implement only apply the minimal safe fix"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.command == 'implement'
        assert cmd.instruction == 'only apply the minimal safe fix'
    
    def test_parse_implement_with_extra_text(self):
        """Test parsing implement command with extra surrounding text."""
        comment = "Please Fixium:implement prefer the existing helper function"
        cmd = CommentParser.parse(comment)
        
        assert cmd is not None
        assert cmd.command == 'implement'
        assert cmd.instruction == 'prefer the existing helper function'
    
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


class TestParseReviewCommentBody:
    """Test parse_review_comment_body method."""
    
    def test_parse_complete_comment(self):
        """Test parsing a complete review comment."""
        comment = """🟡 MEDIUM SEVERITY | 🔧 MAINTAINABILITY

Issue: Timeout values (45.0, 60.0, 90.0) are hardcoded throughout the proxy endpoints.

Details:

Suggestion: Define constants at module level: QUOTE_CREATE_TIMEOUT = 45.0

bob_fixable: true

🤖 Generated by Fixium Code Review | Line 308"""
        
        result = CommentParser.parse_review_comment_body(comment)
        
        assert result['severity'] == 'medium'
        assert result['type'] == 'maintainability'
        assert 'Timeout values' in result['issue']
        assert 'Define constants' in result['suggestion']
        assert result['bob_fixable'] is True
    
    def test_parse_critical_security(self):
        """Test parsing critical security issue."""
        comment = """🔴 CRITICAL SEVERITY | 🔒 SECURITY

Issue: API key is hardcoded in source code.

Suggestion: Move to environment variables.

bob_fixable: true"""
        
        result = CommentParser.parse_review_comment_body(comment)
        
        assert result['severity'] == 'critical'
        assert result['type'] == 'security'
        assert 'API key' in result['issue']
        assert 'environment variables' in result['suggestion']
        assert result['bob_fixable'] is True
    
    def test_parse_without_bob_fixable(self):
        """Test parsing comment without bob_fixable flag."""
        comment = """🟡 MEDIUM SEVERITY | 🐛 BUG

Issue: Function returns None instead of empty list.

Suggestion: Return [] instead of None."""
        
        result = CommentParser.parse_review_comment_body(comment)
        
        assert result['severity'] == 'medium'
        assert result['type'] == 'bug'
        assert result['bob_fixable'] is False
    
    def test_parse_with_details(self):
        """Test parsing comment with details section."""
        comment = """🔵 LOW SEVERITY | 🎨 STYLE

Issue: Inconsistent naming convention.

Details:
Some variables use camelCase while others use snake_case.
This makes the code harder to read.

Suggestion: Standardize on snake_case per PEP 8.

bob_fixable: true"""
        
        result = CommentParser.parse_review_comment_body(comment)
        
        assert result['severity'] == 'low'
        assert result['type'] == 'style'
        assert 'Inconsistent naming' in result['issue']
        assert 'camelCase' in result['details']
        assert 'snake_case' in result['suggestion']
        assert result['bob_fixable'] is True
    
    def test_parse_malformed_comment(self):
        """Test parsing malformed comment returns defaults."""
        comment = "This is not a properly formatted review comment"
        
        result = CommentParser.parse_review_comment_body(comment)
        
        assert result['severity'] == 'unknown'
        assert result['type'] == 'unknown'
        assert result['issue'] == ''
        assert result['suggestion'] == ''
        assert result['details'] == ''
        assert result['bob_fixable'] is False
    
    def test_parse_performance_issue(self):
        """Test parsing performance issue."""
        comment = """🟡 HIGH SEVERITY | ⚡ PERFORMANCE

Issue: Inefficient algorithm with O(n²) complexity.

Suggestion: Use hash map for O(n) lookup.

bob_fixable: true"""
        
        result = CommentParser.parse_review_comment_body(comment)
        
        assert result['severity'] == 'high'
        assert result['type'] == 'performance'
        assert 'Inefficient algorithm' in result['issue']
        assert 'hash map' in result['suggestion']
        assert result['bob_fixable'] is True
    
    def test_parse_case_insensitive_bob_fixable(self):
        """Test bob_fixable flag is case insensitive."""
        comment = """🟡 MEDIUM SEVERITY | 🔧 MAINTAINABILITY

Issue: Test issue

Suggestion: Test suggestion

BOB_FIXABLE: TRUE"""
        
        result = CommentParser.parse_review_comment_body(comment)
        
        assert result['bob_fixable'] is True

# Made with Bob
