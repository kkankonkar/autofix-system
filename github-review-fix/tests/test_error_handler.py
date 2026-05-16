"""Tests for error handler module."""
import pytest
from unittest.mock import Mock
from fixium.error_handler import ErrorHandler


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_init(self):
        """Test initialization."""
        mock_client = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        assert handler.client == mock_client
        assert handler.pr_number == 123
    
    def test_handle_invalid_command(self):
        """Test handling invalid command."""
        mock_client = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        handler.handle_invalid_command("Some random comment")
        
        mock_client.post_comment.assert_called_once()
        call_args = mock_client.post_comment.call_args
        
        assert call_args[0][0] == 123
        assert 'Invalid Fixium Command' in call_args[0][1]
        assert 'Fixium:review' in call_args[0][1]
    
    def test_handle_invalid_filters(self):
        """Test handling invalid filters."""
        mock_client = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        errors = ['Invalid severity: invalid1', 'Invalid type: invalid2']
        handler.handle_invalid_filters(errors)
        
        mock_client.post_comment.assert_called_once()
        call_args = mock_client.post_comment.call_args
        
        assert call_args[0][0] == 123
        assert 'Invalid Filter Options' in call_args[0][1]
        assert 'invalid1' in call_args[0][1]
        assert 'invalid2' in call_args[0][1]
    
    def test_handle_timeout(self):
        """Test handling timeout error."""
        mock_client = Mock()
        mock_progress = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        handler.handle_timeout(mock_progress)
        
        mock_progress.error.assert_called_once()
        call_args = mock_progress.error.call_args
        
        assert call_args[0][0] == 'Review Timeout'
        assert 'taking too long' in call_args[0][1]
    
    def test_handle_review_error(self):
        """Test handling review execution error."""
        mock_client = Mock()
        mock_progress = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        handler.handle_review_error(mock_progress, "Analysis failed: syntax error")
        
        mock_progress.error.assert_called_once()
        call_args = mock_progress.error.call_args
        
        assert call_args[0][0] == 'Analysis Error'
        assert 'syntax error' in call_args[0][1]
    
    def test_handle_submission_error(self):
        """Test handling comment submission error."""
        mock_client = Mock()
        mock_progress = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        handler.handle_submission_error(mock_progress, "Rate limit exceeded")
        
        mock_progress.error.assert_called_once()
        call_args = mock_progress.error.call_args
        
        assert call_args[0][0] == 'Submission Error'
        assert 'Rate limit' in call_args[0][1]
    
    def test_handle_unexpected_error_with_progress(self):
        """Test handling unexpected error with progress tracker."""
        mock_client = Mock()
        mock_progress = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        handler.handle_unexpected_error("Something went wrong", mock_progress)
        
        mock_progress.error.assert_called_once()
        call_args = mock_progress.error.call_args
        
        assert call_args[0][0] == 'Unexpected Error'
        assert 'Something went wrong' in call_args[0][1]
    
    def test_handle_unexpected_error_without_progress(self):
        """Test handling unexpected error without progress tracker."""
        mock_client = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        handler.handle_unexpected_error("Something went wrong")
        
        mock_client.post_comment.assert_called_once()
        call_args = mock_client.post_comment.call_args
        
        assert call_args[0][0] == 123
        assert 'Unexpected Error' in call_args[0][1]
        assert 'Something went wrong' in call_args[0][1]
    
    def test_handle_configuration_error(self):
        """Test handling configuration errors."""
        mock_client = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        errors = ['GITHUB_TOKEN is required', 'PR_NUMBER is required']
        handler.handle_configuration_error(errors)
        
        mock_client.post_comment.assert_called_once()
        call_args = mock_client.post_comment.call_args
        
        assert call_args[0][0] == 123
        assert 'Configuration Error' in call_args[0][1]
        assert 'GITHUB_TOKEN' in call_args[0][1]
        assert 'PR_NUMBER' in call_args[0][1]
    
    def test_error_message_truncation(self):
        """Test that long error messages are truncated."""
        mock_client = Mock()
        mock_progress = Mock()
        handler = ErrorHandler(mock_client, 123)
        
        # Create a very long error message
        long_error = "Error: " + "x" * 1000
        handler.handle_review_error(mock_progress, long_error)
        
        call_args = mock_progress.error.call_args
        error_message = call_args[0][1]
        
        # Dynamic formatting adds wrapper text around the truncated details block
        assert len(error_message) < 800
        assert 'Error: ' in error_message
        assert 'x' * 100 in error_message

# Made with Bob
