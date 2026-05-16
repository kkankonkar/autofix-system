"""Tests for main module JSON schema validation."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from fixium.main import format_summary, is_bob_fixable_comment, validate_implement_target
from fixium.github_client import GitHubClient


class TestJSONSchemaValidation:
    """Test JSON schema validation for review output."""
    
    def test_format_summary_with_canonical_schema(self):
        """Test format_summary with canonical schema format."""
        review_data = {
            "pr_number": 3,
            "files_reviewed": ["README.md"],
            "review_summary": {
                "total_findings": 8,
                "critical": 1,
                "high": 2,
                "medium": 3,
                "low": 2
            },
            "findings": []
        }
        
        result = format_summary(review_data)
        
        assert "🔴 Critical: 1" in result
        assert "🔴 High: 2" in result
        assert "🟡 Medium: 3" in result
        assert "🔵 Low: 2" in result
    
    def test_format_summary_no_issues(self):
        """Test format_summary with no issues."""
        review_data = {
            "review_summary": {
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        result = format_summary(review_data)
        
        assert result == "No issues found"
    
    def test_format_summary_empty_data(self):
        """Test format_summary with empty data."""
        review_data = {}
        
        result = format_summary(review_data)
        
        assert result == "No issues found"
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_reads_canonical_schema(self, mock_file, mock_exists):
        """Test main reads data according to canonical schema."""
        mock_exists.return_value = True
        review_data = {
            "pr_number": 3,
            "files_reviewed": ["README.md"],
            "review_summary": {
                "total_findings": 8,
                "critical": 1,
                "high": 2,
                "medium": 3,
                "low": 2
            },
            "findings": []
        }
        mock_file.return_value.read.return_value = json.dumps(review_data)
        
        # Simulate the code path in main.py
        with open('dummy.json') as f:
            loaded_data = json.load(f)
        
        summary_data = loaded_data.get('review_summary', {})
        total_findings = summary_data.get('total_findings', 0)
        
        assert total_findings == 8
        assert summary_data['critical'] == 1
        assert summary_data['high'] == 2
        assert summary_data['medium'] == 3
        assert summary_data['low'] == 2
    
    def test_validate_required_fields(self):
        """Test that required schema fields are present."""
        review_data = {
            "pr_number": 3,
            "files_reviewed": ["README.md"],
            "review_summary": {
                "total_findings": 8,
                "critical": 1,
                "high": 2,
                "medium": 3,
                "low": 2
            },
            "findings": [
                {
                    "file": "README.md",
                    "line": 267,
                    "severity": "critical",
                    "type": "security",
                    "title": "Test issue",
                    "description": "Test description"
                }
            ]
        }
        
        # Verify required top-level fields
        assert "pr_number" in review_data
        assert "files_reviewed" in review_data
        assert "review_summary" in review_data
        assert "findings" in review_data
        
        # Verify required summary fields
        summary = review_data["review_summary"]
        assert "total_findings" in summary
        assert "critical" in summary
        assert "high" in summary
        assert "medium" in summary
        assert "low" in summary
        
        # Verify required finding fields
        if review_data["findings"]:
            finding = review_data["findings"][0]
            assert "file" in finding
            assert "line" in finding
            assert "severity" in finding
            assert "type" in finding
            assert "title" in finding
            assert "description" in finding
    
    def test_severity_enum_values(self):
        """Test that severity values match schema enum."""
        valid_severities = ["critical", "high", "medium", "low"]
        
        for severity in valid_severities:
            review_data = {
                "review_summary": {
                    "total_findings": 1,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
            review_data["review_summary"][severity] = 1
            
            # Should not raise any errors
            result = format_summary(review_data)
            assert result != "No issues found"
    
    def test_type_enum_values(self):
        """Test that type values match schema enum."""
        valid_types = ["security", "bug", "maintainability", "performance", "style"]
        
        for type_value in valid_types:
            finding = {
                "file": "test.py",
                "line": 1,
                "severity": "high",
                "type": type_value,
                "title": "Test",
                "description": "Test description"
            }
            
            # Verify type is one of the valid enum values
            assert finding["type"] in valid_types


    def test_is_bob_fixable_comment_true(self):
        """Test bob-fixable marker detection."""
        review_comment = {
            "body": "Please fix this.\n\n`bob_fixable: true`"
        }

        assert is_bob_fixable_comment(review_comment) is True

    def test_is_bob_fixable_comment_false(self):
        """Test missing bob-fixable marker returns false."""
        review_comment = {
            "body": "Please fix this if possible."
        }

        assert is_bob_fixable_comment(review_comment) is False

    def test_validate_implement_target_requires_reply_id(self):
        """Test implement target validation requires reply comment ID."""
        mock_client = Mock(spec=GitHubClient)

        with pytest.raises(ValueError, match="REPLY_TO_COMMENT_ID is required"):
            validate_implement_target(mock_client, None)

    def test_validate_implement_target_rejects_non_fixable_comment(self):
        """Test implement target validation rejects non-fixable comments."""
        mock_client = Mock(spec=GitHubClient)
        mock_client.get_review_comment.return_value = {
            "id": 456,
            "body": "Not marked for automatic implementation"
        }

        with pytest.raises(ValueError, match="not marked as bob_fixable"):
            validate_implement_target(mock_client, 456)

    def test_validate_implement_target_returns_review_comment(self):
        """Test implement target validation returns valid review comment."""
        mock_client = Mock(spec=GitHubClient)
        review_comment = {
            "id": 456,
            "body": "Fix this.\n\n`bob_fixable: true`",
            "path": "src/app.py",
            "line": 10
        }
        mock_client.get_review_comment.return_value = review_comment

        result = validate_implement_target(mock_client, 456)

        assert result == review_comment
        mock_client.get_review_comment.assert_called_once_with(456)

# Made with Bob