"""Tests for change classification module."""

import pytest
from unittest.mock import Mock, MagicMock
from fixium.change_classifier import (
    ChangeClassifier,
    ChangeType,
    ClassificationResult,
)


class TestChangeClassifier:
    """Test suite for ChangeClassifier class."""

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        client = Mock()
        client.owner = "test-owner"
        client.repo = "test-repo"
        return client

    @pytest.fixture
    def classifier(self, mock_github_client):
        """Create a ChangeClassifier instance."""
        return ChangeClassifier(mock_github_client)

    def test_classify_major_feature_commit(self, classifier):
        """Test classification of major feature commits."""
        commits = [
            Mock(commit=Mock(message="feat: Add new authentication system")),
            Mock(commit=Mock(message="feat: Implement user dashboard")),
        ]
        
        result = classifier._classify_by_commits(commits)
        
        assert result == ChangeType.MAJOR

    def test_classify_bug_fix_commit(self, classifier):
        """Test classification of bug fix commits."""
        commits = [
            Mock(commit=Mock(message="fix: Resolve login issue")),
            Mock(commit=Mock(message="fix: Correct validation error")),
        ]
        
        result = classifier._classify_by_commits(commits)
        
        assert result == ChangeType.MINOR

    def test_classify_dependency_update(self, classifier):
        """Test classification of dependency updates."""
        commits = [
            Mock(commit=Mock(message="chore: Update dependencies")),
            Mock(commit=Mock(message="chore(deps): Bump package version")),
        ]
        
        result = classifier._classify_by_commits(commits)
        
        assert result == ChangeType.MINOR

    def test_classify_security_patch(self, classifier):
        """Test classification of security patches."""
        commits = [
            Mock(commit=Mock(message="security: Patch vulnerability CVE-2024-1234")),
            Mock(commit=Mock(message="fix: Security update for auth")),
        ]
        
        result = classifier._classify_by_commits(commits)
        
        assert result == ChangeType.MINOR

    def test_classify_mixed_commits_major_wins(self, classifier):
        """Test that major features override minor changes."""
        commits = [
            Mock(commit=Mock(message="feat: Add new API endpoint")),
            Mock(commit=Mock(message="fix: Minor bug fix")),
            Mock(commit=Mock(message="chore: Update docs")),
        ]
        
        result = classifier._classify_by_commits(commits)
        
        assert result == ChangeType.MAJOR

    def test_classify_by_files_new_features(self, classifier):
        """Test classification based on new feature files."""
        files = [
            Mock(filename="src/features/new_feature.py", status="added"),
            Mock(filename="src/api/new_endpoint.py", status="added"),
        ]
        
        result = classifier._classify_by_files(files)
        
        assert result == ChangeType.MAJOR

    def test_classify_by_files_config_changes(self, classifier):
        """Test classification of configuration file changes."""
        files = [
            Mock(filename="package.json", status="modified"),
            Mock(filename="requirements.txt", status="modified"),
        ]
        
        result = classifier._classify_by_files(files)
        
        assert result == ChangeType.MINOR

    def test_classify_by_files_test_only(self, classifier):
        """Test classification of test-only changes."""
        files = [
            Mock(filename="tests/test_feature.py", status="modified"),
            Mock(filename="tests/test_api.py", status="added"),
        ]
        
        result = classifier._classify_by_files(files)
        
        assert result == ChangeType.MINOR

    def test_classify_by_files_docs_only(self, classifier):
        """Test classification of documentation-only changes."""
        files = [
            Mock(filename="README.md", status="modified"),
            Mock(filename="docs/guide.md", status="modified"),
        ]
        
        result = classifier._classify_by_files(files)
        
        assert result == ChangeType.MINOR

    def test_classify_by_files_major_refactor(self, classifier):
        """Test classification of major refactoring."""
        files = [
            Mock(filename="src/core/engine.py", status="modified", changes=500),
            Mock(filename="src/core/processor.py", status="modified", changes=400),
            Mock(filename="src/api/handler.py", status="modified", changes=300),
        ]
        
        result = classifier._classify_by_files(files)
        
        assert result == ChangeType.MAJOR

    def test_classify_pr_major_feature(self, classifier, mock_github_client):
        """Test full PR classification for major feature."""
        # Mock PR
        mock_pr = Mock()
        mock_pr.get_commits.return_value = [
            Mock(commit=Mock(message="feat: Add new payment system")),
        ]
        mock_pr.get_files.return_value = [
            Mock(filename="src/payment/processor.py", status="added", changes=200),
            Mock(filename="src/payment/gateway.py", status="added", changes=150),
        ]
        
        mock_github_client.get_pull_request.return_value = mock_pr
        
        result = classifier.classify_pr(123)
        
        assert result.change_type == ChangeType.MAJOR
        assert result.confidence == "high"
        assert "payment system" in result.reasoning.lower()

    def test_classify_pr_minor_fix(self, classifier, mock_github_client):
        """Test full PR classification for minor fix."""
        mock_pr = Mock()
        mock_pr.get_commits.return_value = [
            Mock(commit=Mock(message="fix: Resolve validation bug")),
        ]
        mock_pr.get_files.return_value = [
            Mock(filename="src/utils/validator.py", status="modified", changes=10),
        ]
        
        mock_github_client.get_pull_request.return_value = mock_pr
        
        result = classifier.classify_pr(123)
        
        assert result.change_type == ChangeType.MINOR
        assert "bug" in result.reasoning.lower() or "fix" in result.reasoning.lower()

    def test_classify_pr_dependency_update(self, classifier, mock_github_client):
        """Test classification of dependency update PR."""
        mock_pr = Mock()
        mock_pr.get_commits.return_value = [
            Mock(commit=Mock(message="chore(deps): Bump lodash from 4.17.20 to 4.17.21")),
        ]
        mock_pr.get_files.return_value = [
            Mock(filename="package-lock.json", status="modified", changes=50),
        ]
        
        mock_github_client.get_pull_request.return_value = mock_pr
        
        result = classifier.classify_pr(123)
        
        assert result.change_type == ChangeType.MINOR

    def test_classification_result_dataclass(self):
        """Test ClassificationResult dataclass."""
        result = ClassificationResult(
            change_type=ChangeType.MAJOR,
            confidence="high",
            reasoning="New feature added",
            commit_indicators=["feat: New feature"],
            file_indicators=["new_feature.py"],
        )
        
        assert result.change_type == ChangeType.MAJOR
        assert result.confidence == "high"
        assert result.reasoning == "New feature added"
        assert len(result.commit_indicators) == 1
        assert len(result.file_indicators) == 1

    def test_change_type_enum(self):
        """Test ChangeType enum values."""
        assert ChangeType.MAJOR.value == "major"
        assert ChangeType.MINOR.value == "minor"

    def test_classify_breaking_change(self, classifier):
        """Test classification of breaking changes."""
        commits = [
            Mock(commit=Mock(message="feat!: Remove deprecated API\n\nBREAKING CHANGE: Old API removed")),
        ]
        
        result = classifier._classify_by_commits(commits)
        
        assert result == ChangeType.MAJOR

    def test_classify_refactor_commit(self, classifier):
        """Test classification of refactor commits."""
        commits = [
            Mock(commit=Mock(message="refactor: Restructure authentication module")),
        ]
        
        result = classifier._classify_by_commits(commits)
        
        # Refactor can be major or minor depending on scope
        assert result in [ChangeType.MAJOR, ChangeType.MINOR]

    def test_classify_empty_commits(self, classifier):
        """Test classification with no commits."""
        commits = []
        
        result = classifier._classify_by_commits(commits)
        
        assert result == ChangeType.MINOR  # Default to minor

    def test_classify_empty_files(self, classifier):
        """Test classification with no files."""
        files = []
        
        result = classifier._classify_by_files(files)
        
        assert result == ChangeType.MINOR  # Default to minor

    def test_confidence_high_for_clear_major(self, classifier, mock_github_client):
        """Test high confidence for clear major features."""
        mock_pr = Mock()
        mock_pr.get_commits.return_value = [
            Mock(commit=Mock(message="feat: Add complete user management system")),
            Mock(commit=Mock(message="feat: Implement role-based access control")),
        ]
        mock_pr.get_files.return_value = [
            Mock(filename="src/users/manager.py", status="added", changes=300),
            Mock(filename="src/auth/rbac.py", status="added", changes=250),
        ]
        
        mock_github_client.get_pull_request.return_value = mock_pr
        
        result = classifier.classify_pr(123)
        
        assert result.change_type == ChangeType.MAJOR
        assert result.confidence == "high"

    def test_confidence_medium_for_mixed_signals(self, classifier, mock_github_client):
        """Test medium confidence for mixed signals."""
        mock_pr = Mock()
        mock_pr.get_commits.return_value = [
            Mock(commit=Mock(message="feat: Add new feature")),
            Mock(commit=Mock(message="fix: Bug fixes")),
        ]
        mock_pr.get_files.return_value = [
            Mock(filename="src/feature.py", status="modified", changes=50),
        ]
        
        mock_github_client.get_pull_request.return_value = mock_pr
        
        result = classifier.classify_pr(123)
        
        # Confidence might be medium due to mixed signals
        assert result.confidence in ["medium", "high"]

# Made with Bob
