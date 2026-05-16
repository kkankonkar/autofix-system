"""Tests for progress tracker module."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from fixium.progress_tracker import ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker class."""
    
    def test_init(self):
        """Test initialization."""
        mock_client = Mock()
        tracker = ProgressTracker(mock_client, 123)
        
        assert tracker.client == mock_client
        assert tracker.pr_number == 123
        assert tracker.comment_id is None
        assert isinstance(tracker.start_time, datetime)
    
    def test_start(self):
        """Test starting progress tracking."""
        mock_client = Mock()
        mock_comment = Mock(id=456)
        mock_client.post_comment.return_value = mock_comment
        
        tracker = ProgressTracker(mock_client, 123)
        comment_id = tracker.start("No filters")
        
        assert comment_id == 456
        assert tracker.comment_id == 456
        mock_client.post_comment.assert_called_once()
        
        # Check comment content
        call_args = mock_client.post_comment.call_args
        assert call_args[0][0] == 123  # PR number
        assert 'Fixium Code Review Started' in call_args[0][1]
        assert 'No filters' in call_args[0][1]
    
    def test_update(self):
        """Test updating progress."""
        mock_client = Mock()
        mock_comment = Mock(id=456)
        mock_client.post_comment.return_value = mock_comment
        
        tracker = ProgressTracker(mock_client, 123)
        tracker.start("No filters")
        tracker.update("Running review", "Analyzing files")
        
        mock_client.update_comment.assert_called_once()
        
        # Check update content
        call_args = mock_client.update_comment.call_args
        assert call_args[0][0] == 456  # Comment ID
        assert 'Running review' in call_args[0][1]
        assert 'Analyzing files' in call_args[0][1]
    
    def test_update_without_start(self):
        """Test update without starting raises error."""
        mock_client = Mock()
        tracker = ProgressTracker(mock_client, 123)
        
        with pytest.raises(ValueError, match="Progress not started"):
            tracker.update("Status")
    
    def test_complete_no_findings(self):
        """Test completion with no findings."""
        mock_client = Mock()
        mock_comment = Mock(id=456)
        mock_client.post_comment.return_value = mock_comment
        
        tracker = ProgressTracker(mock_client, 123)
        tracker.start("No filters")
        tracker.complete(0, "")
        
        mock_client.update_comment.assert_called_once()
        
        # Check completion content
        call_args = mock_client.update_comment.call_args
        assert 'No issues found' in call_args[0][1]
        assert 'code looks good' in call_args[0][1]
    
    def test_complete_with_findings(self):
        """Test completion with findings."""
        mock_client = Mock()
        mock_comment = Mock(id=456)
        mock_client.post_comment.return_value = mock_comment
        
        tracker = ProgressTracker(mock_client, 123)
        tracker.start("No filters")
        tracker.complete(5, "🔴 High: 2 | 🟡 Medium: 3")
        
        mock_client.update_comment.assert_called_once()
        
        # Check completion content
        call_args = mock_client.update_comment.call_args
        assert '5 issue(s) found' in call_args[0][1]
        assert '🔴 High: 2' in call_args[0][1]
    
    def test_complete_without_start(self):
        """Test complete without starting raises error."""
        mock_client = Mock()
        tracker = ProgressTracker(mock_client, 123)
        
        with pytest.raises(ValueError, match="Progress not started"):
            tracker.complete(0, "")
    
    def test_error_with_progress(self):
        """Test error handling with progress started."""
        mock_client = Mock()
        mock_comment = Mock(id=456)
        mock_client.post_comment.return_value = mock_comment
        
        tracker = ProgressTracker(mock_client, 123)
        tracker.start("No filters")
        tracker.error("Timeout", "Review took too long")
        
        mock_client.update_comment.assert_called_once()
        
        # Check error content
        call_args = mock_client.update_comment.call_args
        assert 'Failed' in call_args[0][1]
        assert 'Timeout' in call_args[0][1]
        assert 'Review took too long' in call_args[0][1]
    
    def test_error_without_progress(self):
        """Test error handling without progress started."""
        mock_client = Mock()
        tracker = ProgressTracker(mock_client, 123)
        tracker.error("Configuration Error", "Missing token")
        
        # Should post new comment instead of updating
        mock_client.post_comment.assert_called_once()
        
        # Check error content
        call_args = mock_client.post_comment.call_args
        assert call_args[0][0] == 123  # PR number
        assert 'Failed' in call_args[0][1]
        assert 'Configuration Error' in call_args[0][1]
    
    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        mock_client = Mock()
        tracker = ProgressTracker(mock_client, 123)
        
        # Should return 0 or small number immediately
        elapsed = tracker.get_elapsed_time()
        assert isinstance(elapsed, int)
        assert elapsed >= 0
        assert elapsed < 2  # Should be less than 2 seconds

# Made with Bob
