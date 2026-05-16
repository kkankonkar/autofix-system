"""Tests for documentation runner module."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from fixium.doc_runner import DocRunner
from fixium.doc_discoverer import DocumentationFile, DocumentationType
from fixium.change_classifier import ChangeType, ClassificationResult


class TestDocRunner:
    """Test suite for DocRunner class."""

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        client = Mock()
        client.owner = "test-owner"
        client.repo = "test-repo"
        return client

    @pytest.fixture
    def runner(self, mock_github_client):
        """Create a DocRunner instance."""
        return DocRunner(mock_github_client, pr_number=123)

    @pytest.fixture
    def mock_classification(self):
        """Create a mock classification result."""
        return ClassificationResult(
            change_type=ChangeType.MAJOR,
            confidence="high",
            reasoning="New feature added",
            commit_indicators=["feat: New feature"],
            file_indicators=["new_feature.py"],
        )

    @pytest.fixture
    def mock_docs(self):
        """Create mock documentation files."""
        return [
            DocumentationFile("README.md", DocumentationType.README),
            DocumentationFile("docs/API.md", DocumentationType.API),
            DocumentationFile("CONTRIBUTING.md", DocumentationType.DEVELOPER),
        ]

    def test_init(self, mock_github_client):
        """Test DocRunner initialization."""
        runner = DocRunner(mock_github_client, pr_number=123)
        
        assert runner.github_client == mock_github_client
        assert runner.pr_number == 123
        assert runner.discoverer is not None
        assert runner.classifier is not None

    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_should_analyze_major_feature(
        self, mock_classifier_class, mock_discoverer_class, mock_github_client
    ):
        """Test that major features should be analyzed."""
        mock_classifier = Mock()
        mock_classifier.classify_pr.return_value = ClassificationResult(
            change_type=ChangeType.MAJOR,
            confidence="high",
            reasoning="New feature",
            commit_indicators=[],
            file_indicators=[],
        )
        mock_classifier_class.return_value = mock_classifier
        
        runner = DocRunner(mock_github_client, pr_number=123)
        should_analyze, reason = runner.should_analyze()
        
        assert should_analyze is True
        assert "major" in reason.lower()

    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_should_not_analyze_minor_change(
        self, mock_classifier_class, mock_discoverer_class, mock_github_client
    ):
        """Test that minor changes should not be analyzed."""
        mock_classifier = Mock()
        mock_classifier.classify_pr.return_value = ClassificationResult(
            change_type=ChangeType.MINOR,
            confidence="high",
            reasoning="Bug fix",
            commit_indicators=[],
            file_indicators=[],
        )
        mock_classifier_class.return_value = mock_classifier
        
        runner = DocRunner(mock_github_client, pr_number=123)
        should_analyze, reason = runner.should_analyze()
        
        assert should_analyze is False
        assert "minor" in reason.lower() or "skip" in reason.lower()

    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_force_analyze_overrides_classification(
        self, mock_classifier_class, mock_discoverer_class, mock_github_client
    ):
        """Test that force flag overrides classification."""
        mock_classifier = Mock()
        mock_classifier.classify_pr.return_value = ClassificationResult(
            change_type=ChangeType.MINOR,
            confidence="high",
            reasoning="Bug fix",
            commit_indicators=[],
            file_indicators=[],
        )
        mock_classifier_class.return_value = mock_classifier
        
        runner = DocRunner(mock_github_client, pr_number=123)
        should_analyze, reason = runner.should_analyze(force=True)
        
        assert should_analyze is True
        assert "forced" in reason.lower()

    @patch('subprocess.run')
    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_run_analysis_success(
        self, mock_classifier_class, mock_discoverer_class, mock_run, 
        mock_github_client, mock_classification, mock_docs
    ):
        """Test successful documentation analysis."""
        # Setup mocks
        mock_discoverer = Mock()
        mock_discoverer.discover_local_docs.return_value = mock_docs
        mock_discoverer_class.return_value = mock_discoverer
        
        mock_classifier = Mock()
        mock_classifier.classify_pr.return_value = mock_classification
        mock_classifier_class.return_value = mock_classifier
        
        # Mock subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "suggestions": [
                {
                    "file": "README.md",
                    "section": "Installation",
                    "suggestion": "Add installation steps",
                    "priority": "high"
                }
            ]
        })
        mock_run.return_value = mock_result
        
        runner = DocRunner(mock_github_client, pr_number=123)
        result = runner.run_analysis()
        
        assert result is not None
        assert "suggestions" in result
        assert len(result["suggestions"]) == 1

    @patch('subprocess.run')
    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_run_analysis_with_specific_files(
        self, mock_classifier_class, mock_discoverer_class, mock_run,
        mock_github_client, mock_classification
    ):
        """Test analysis with specific files."""
        mock_discoverer = Mock()
        mock_discoverer_class.return_value = mock_discoverer
        
        mock_classifier = Mock()
        mock_classifier.classify_pr.return_value = mock_classification
        mock_classifier_class.return_value = mock_classifier
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"suggestions": []})
        mock_run.return_value = mock_result
        
        runner = DocRunner(mock_github_client, pr_number=123)
        result = runner.run_analysis(files=["README.md", "API.md"])
        
        # Verify subprocess was called with correct files
        assert mock_run.called
        call_args = mock_run.call_args
        assert "README.md" in str(call_args)
        assert "API.md" in str(call_args)

    @patch('subprocess.run')
    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_run_analysis_failure(
        self, mock_classifier_class, mock_discoverer_class, mock_run,
        mock_github_client, mock_classification, mock_docs
    ):
        """Test handling of analysis failure."""
        mock_discoverer = Mock()
        mock_discoverer.discover_local_docs.return_value = mock_docs
        mock_discoverer_class.return_value = mock_discoverer
        
        mock_classifier = Mock()
        mock_classifier.classify_pr.return_value = mock_classification
        mock_classifier_class.return_value = mock_classifier
        
        # Mock subprocess failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Analysis failed"
        mock_run.return_value = mock_result
        
        runner = DocRunner(mock_github_client, pr_number=123)
        
        with pytest.raises(Exception):
            runner.run_analysis()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_save_results(
        self, mock_classifier_class, mock_discoverer_class, mock_json_dump,
        mock_file, mock_github_client
    ):
        """Test saving analysis results."""
        runner = DocRunner(mock_github_client, pr_number=123)
        
        results = {
            "suggestions": [
                {"file": "README.md", "suggestion": "Update docs"}
            ]
        }
        
        runner.save_results(results, "output.json")
        
        mock_file.assert_called_once_with("output.json", "w")
        mock_json_dump.assert_called_once()

    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_get_pr_info(
        self, mock_classifier_class, mock_discoverer_class, mock_github_client
    ):
        """Test getting PR information."""
        mock_pr = Mock()
        mock_pr.title = "Add new feature"
        mock_pr.body = "This PR adds a new feature"
        mock_pr.get_commits.return_value = [
            Mock(commit=Mock(message="feat: Add feature"))
        ]
        mock_pr.get_files.return_value = [
            Mock(filename="src/feature.py", status="added")
        ]
        
        mock_github_client.get_pull_request.return_value = mock_pr
        
        runner = DocRunner(mock_github_client, pr_number=123)
        pr_info = runner.get_pr_info()
        
        assert pr_info["title"] == "Add new feature"
        assert pr_info["body"] == "This PR adds a new feature"
        assert len(pr_info["commits"]) == 1
        assert len(pr_info["files"]) == 1

    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_format_analysis_context(
        self, mock_classifier_class, mock_discoverer_class, mock_github_client,
        mock_classification, mock_docs
    ):
        """Test formatting analysis context."""
        mock_discoverer = Mock()
        mock_discoverer.discover_local_docs.return_value = mock_docs
        mock_discoverer.format_docs_list.return_value = "README.md\ndocs/API.md"
        mock_discoverer_class.return_value = mock_discoverer
        
        mock_classifier = Mock()
        mock_classifier.classify_pr.return_value = mock_classification
        mock_classifier_class.return_value = mock_classifier
        
        runner = DocRunner(mock_github_client, pr_number=123)
        context = runner._format_analysis_context(
            mock_classification,
            mock_docs,
            {"title": "Test PR", "body": "Test body"}
        )
        
        assert "Test PR" in context
        assert "README.md" in context
        assert "New feature" in context

    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_filter_docs_by_files(
        self, mock_classifier_class, mock_discoverer_class, mock_github_client,
        mock_docs
    ):
        """Test filtering documentation by specific files."""
        runner = DocRunner(mock_github_client, pr_number=123)
        
        filtered = runner._filter_docs_by_files(
            mock_docs,
            ["README.md", "docs/API.md"]
        )
        
        assert len(filtered) == 2
        assert all(doc.path in ["README.md", "docs/API.md"] for doc in filtered)

    @patch('fixium.doc_runner.DocDiscoverer')
    @patch('fixium.doc_runner.ChangeClassifier')
    def test_filter_docs_nonexistent_files(
        self, mock_classifier_class, mock_discoverer_class, mock_github_client,
        mock_docs
    ):
        """Test filtering with nonexistent files."""
        runner = DocRunner(mock_github_client, pr_number=123)
        
        filtered = runner._filter_docs_by_files(
            mock_docs,
            ["NONEXISTENT.md"]
        )
        
        assert len(filtered) == 0

# Made with Bob
