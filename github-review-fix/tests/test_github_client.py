"""Tests for GitHub client module."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from github import GithubException
from fixium.github_client import GitHubClient


class TestGitHubClient:
    """Test GitHubClient class."""
    
    @patch('fixium.github_client.Github')
    def test_init_with_token(self, mock_github):
        """Test initialization with token."""
        mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        
        assert client.token == 'test_token'
        assert client.repo_name == 'owner/repo'
        mock_github.assert_called_once_with('test_token')
    
    @patch('fixium.github_client.Github')
    def test_init_from_env(self, mock_github, monkeypatch):
        """Test initialization from environment variables."""
        monkeypatch.setenv('GITHUB_TOKEN', 'env_token')
        monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/repo')
        
        mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient()
        
        assert client.token == 'env_token'
        assert client.repo_name == 'owner/repo'
    
    def test_init_no_token(self):
        """Test initialization without token raises error."""
        with pytest.raises(ValueError, match="token not provided"):
            GitHubClient(repository='owner/repo')
    
    @patch('fixium.github_client.Github')
    def test_init_no_repository(self, mock_github):
        """Test initialization without repository raises error."""
        with pytest.raises(ValueError, match="GITHUB_REPOSITORY not set"):
            GitHubClient(token='test_token')
    
    @patch('fixium.github_client.Github')
    def test_get_pull_request(self, mock_github):
        """Test getting pull request."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        pr = client.get_pull_request(123)
        
        assert pr == mock_pr
        mock_repo.get_pull.assert_called_once_with(123)
    
    @patch('fixium.github_client.Github')
    def test_post_comment(self, mock_github):
        """Test posting comment."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_issue = Mock()
        mock_comment = Mock()
        
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.as_issue.return_value = mock_issue
        mock_issue.create_comment.return_value = mock_comment
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        comment = client.post_comment(123, "Test comment")
        
        assert comment == mock_comment
        mock_issue.create_comment.assert_called_once_with("Test comment")
    
    @patch('fixium.github_client.Github')
    def test_update_comment(self, mock_github):
        """Test updating issue comment via issue enumeration."""
        mock_repo = Mock()
        mock_comment = Mock(id=456)
        mock_issue = Mock()
        mock_issue.get_comments.return_value = [mock_comment]
        mock_repo.get_issues.return_value = [mock_issue]
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        client.update_comment(456, "Updated comment")
        
        mock_repo.get_issues.assert_called_once_with(state='all')
        mock_issue.get_comments.assert_called_once_with()
        mock_comment.edit.assert_called_once_with("Updated comment")

    @patch('fixium.github_client.Github')
    def test_post_then_update_comment_uses_issue_comment_flow(self, mock_github):
        """Test PR comment creation and update remain compatible."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_issue_resource = Mock()
        mock_comment = Mock(id=456)

        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_issues.return_value = [mock_issue_resource]
        mock_issue_resource.get_comments.return_value = [mock_comment]
        mock_pr.as_issue.return_value = mock_issue_resource
        mock_issue_resource.create_comment.return_value = mock_comment
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient(token='test_token', repository='owner/repo')
        created_comment = client.post_comment(123, "Initial comment")
        client.update_comment(created_comment.id, "Updated comment")

        assert created_comment == mock_comment
        mock_issue_resource.create_comment.assert_called_once_with("Initial comment")
        mock_repo.get_issues.assert_called_once_with(state='all')
        mock_issue_resource.get_comments.assert_called_once_with()
        mock_comment.edit.assert_called_once_with("Updated comment")
    
    @patch('fixium.github_client.Github')
    def test_get_pr_files(self, mock_github):
        """Test getting PR files."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_file1 = Mock(filename='file1.py')
        mock_file2 = Mock(filename='file2.py')
        
        mock_pr.get_files.return_value = [mock_file1, mock_file2]
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        files = client.get_pr_files(123)
        
        assert files == ['file1.py', 'file2.py']
    
    @patch('fixium.github_client.Github')
    def test_check_rate_limit(self, mock_github):
        """Test checking rate limit."""
        mock_rate_limit = Mock()
        mock_rate_limit.core.remaining = 4500
        mock_rate_limit.core.limit = 5000
        mock_rate_limit.core.reset = Mock()
        
        mock_github.return_value.get_rate_limit.return_value = mock_rate_limit
        mock_github.return_value.get_repo.return_value = Mock()
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        rate_info = client.check_rate_limit()
        
        assert rate_info['remaining'] == 4500
        assert rate_info['limit'] == 5000
        assert 'reset' in rate_info
    
    @patch('fixium.github_client.Github')
    def test_is_user_authorized(self, mock_github):
        """Test user authorization check."""
        mock_github.return_value.get_repo.return_value = Mock()
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        
        assert client.is_user_authorized('user1', ['user1', 'user2'])
        assert client.is_user_authorized('USER1', ['user1', 'user2'])  # Case insensitive
        assert not client.is_user_authorized('user3', ['user1', 'user2'])
    
    @patch('fixium.github_client.Github')
    def test_get_user(self, mock_github):
        """Test getting user information."""
        mock_user = Mock()
        mock_github.return_value.get_user.return_value = mock_user
        mock_github.return_value.get_repo.return_value = Mock()
        
        client = GitHubClient(token='test_token', repository='owner/repo')
        user = client.get_user('testuser')
        
        assert user == mock_user
        mock_github.return_value.get_user.assert_called_once_with('testuser')

    @patch('fixium.github_client.Github')
    def test_get_review_comment(self, mock_github):
        """Test getting a review comment by ID."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_review_comment = Mock()
        mock_review_comment.id = 456
        mock_review_comment.raw_data = {
            'id': 456,
            'body': 'Example body',
            'path': 'src/app.py',
            'line': 12
        }
        mock_pr.get_review_comments.return_value = [mock_review_comment]
        mock_repo.get_pulls.return_value = [mock_pr]
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient(token='test_token', repository='owner/repo')
        result = client.get_review_comment(456)

        assert result['id'] == 456
        assert result['path'] == 'src/app.py'
        mock_repo.get_pulls.assert_called_once_with(state='all')

    @patch('fixium.github_client.Github')
    def test_get_review_comment_not_found(self, mock_github):
        """Test missing review comment raises ValueError."""
        mock_repo = Mock()
        mock_pr = Mock()
        mock_review_comment = Mock()
        mock_review_comment.id = 123  # Different ID
        mock_review_comment.raw_data = {'id': 123}
        mock_pr.get_review_comments.return_value = [mock_review_comment]
        mock_repo.get_pulls.return_value = [mock_pr]
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient(token='test_token', repository='owner/repo')

        with pytest.raises(ValueError, match='Review comment not found: 999'):
            client.get_review_comment(999)

# Made with Bob
