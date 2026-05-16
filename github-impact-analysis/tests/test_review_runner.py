"""Tests for review runner module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess
from fixium.review_runner import ReviewRunner


class TestReviewRunner:
    """Test ReviewRunner class."""
    
    def test_init_default(self):
        """Test initialization with default workspace."""
        runner = ReviewRunner()
        assert runner.workspace_dir is not None
    
    def test_init_custom_workspace(self):
        """Test initialization with custom workspace."""
        runner = ReviewRunner('/custom/path')
        assert runner.workspace_dir == '/custom/path'
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_run_review_success(self, mock_exists, mock_run):
        """Test successful review execution."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0)
        
        runner = ReviewRunner('/workspace')
        result = runner.run_review(123, 'output.json')
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check command arguments
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert 'review_workflow.sh' in str(cmd[0])
        assert 'review-pr' in cmd
        assert '123' in cmd
        assert 'output.json' in cmd
    
    @patch('pathlib.Path.exists')
    def test_run_review_script_not_found(self, mock_exists):
        """Test review with missing script."""
        mock_exists.return_value = False
        
        runner = ReviewRunner('/workspace')
        
        with pytest.raises(FileNotFoundError, match="Review script not found"):
            runner.run_review(123, 'output.json')
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_run_review_timeout(self, mock_exists, mock_run):
        """Test review timeout."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 1800)
        
        runner = ReviewRunner('/workspace')
        
        with pytest.raises(TimeoutError, match="timed out after 1800s"):
            runner.run_review(123, 'output.json', timeout=1800)
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_run_review_failure(self, mock_exists, mock_run):
        """Test review failure."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'cmd', stderr='Error message'
        )
        
        runner = ReviewRunner('/workspace')
        
        with pytest.raises(RuntimeError, match="Review failed"):
            runner.run_review(123, 'output.json')
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_submit_comments_success(self, mock_exists, mock_run):
        """Test successful comment submission."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0)
        
        runner = ReviewRunner('/workspace')
        filter_args = ['--severity', 'high']
        result = runner.submit_comments('review.json', 123, filter_args)
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check command arguments
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert 'submit_pr_comments.sh' in str(cmd[0])
        assert 'review.json' in cmd
        assert '123' in cmd
        assert '--severity' in cmd
        assert 'high' in cmd
    
    @patch('pathlib.Path.exists')
    def test_submit_comments_script_not_found(self, mock_exists):
        """Test comment submission with missing script."""
        mock_exists.return_value = False
        
        runner = ReviewRunner('/workspace')
        
        with pytest.raises(FileNotFoundError, match="Submit script not found"):
            runner.submit_comments('review.json', 123, [])
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_submit_comments_timeout(self, mock_exists, mock_run):
        """Test comment submission timeout."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 600)
        
        runner = ReviewRunner('/workspace')
        
        with pytest.raises(TimeoutError, match="timed out after 600s"):
            runner.submit_comments('review.json', 123, [], timeout=600)
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_submit_comments_failure(self, mock_exists, mock_run):
        """Test comment submission failure."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'cmd', stderr='Submission error'
        )
        
        runner = ReviewRunner('/workspace')
        
        with pytest.raises(RuntimeError, match="Comment submission failed"):
            runner.submit_comments('review.json', 123, [])
    
    @patch('pathlib.Path.exists')
    def test_check_scripts_exist(self, mock_exists):
        """Test checking script existence."""
        # Mock both scripts exist
        mock_exists.return_value = True
        
        runner = ReviewRunner('/workspace')
        status = runner.check_scripts_exist()
        
        assert status['review_workflow.sh'] is True
        assert status['submit_pr_comments.sh'] is True
    
    @patch('pathlib.Path.exists')
    def test_check_scripts_exist_missing(self, mock_exists):
        """Test checking with missing scripts."""
        # Mock scripts don't exist
        mock_exists.return_value = False
        
        runner = ReviewRunner('/workspace')
        status = runner.check_scripts_exist()
        
        assert status['review_workflow.sh'] is False
        assert status['submit_pr_comments.sh'] is False
    
    def test_get_workspace_dir(self):
        """Test getting workspace directory."""
        runner = ReviewRunner('/custom/workspace')
        assert runner.get_workspace_dir() == '/custom/workspace'

# Made with Bob
