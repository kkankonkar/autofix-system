"""Tests for documentation discovery module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fixium.doc_discoverer import (
    DocDiscoverer,
    DocumentationType,
    DocumentationFile,
)


class TestDocDiscoverer:
    """Test suite for DocDiscoverer class."""

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        client = Mock()
        client.owner = "test-owner"
        client.repo = "test-repo"
        return client

    @pytest.fixture
    def discoverer(self, mock_github_client):
        """Create a DocDiscoverer instance."""
        return DocDiscoverer(mock_github_client)

    def test_categorize_readme(self, discoverer):
        """Test categorization of README files."""
        assert discoverer._categorize_doc("README.md") == DocumentationType.README
        assert discoverer._categorize_doc("readme.md") == DocumentationType.README
        assert discoverer._categorize_doc("docs/README.md") == DocumentationType.README

    def test_categorize_api_docs(self, discoverer):
        """Test categorization of API documentation."""
        assert discoverer._categorize_doc("API.md") == DocumentationType.API
        assert discoverer._categorize_doc("api-reference.md") == DocumentationType.API
        assert discoverer._categorize_doc("docs/api/endpoints.md") == DocumentationType.API

    def test_categorize_user_guide(self, discoverer):
        """Test categorization of user guides."""
        assert discoverer._categorize_doc("GUIDE.md") == DocumentationType.USER_GUIDE
        assert discoverer._categorize_doc("user-guide.md") == DocumentationType.USER_GUIDE
        assert discoverer._categorize_doc("docs/tutorial.md") == DocumentationType.USER_GUIDE

    def test_categorize_developer_docs(self, discoverer):
        """Test categorization of developer documentation."""
        assert discoverer._categorize_doc("CONTRIBUTING.md") == DocumentationType.DEVELOPER
        assert discoverer._categorize_doc("DEVELOPMENT.md") == DocumentationType.DEVELOPER
        assert discoverer._categorize_doc("docs/architecture.md") == DocumentationType.DEVELOPER

    def test_categorize_changelog(self, discoverer):
        """Test categorization of changelog files."""
        assert discoverer._categorize_doc("CHANGELOG.md") == DocumentationType.CHANGELOG
        assert discoverer._categorize_doc("changelog.md") == DocumentationType.CHANGELOG
        assert discoverer._categorize_doc("HISTORY.md") == DocumentationType.CHANGELOG

    def test_categorize_config_docs(self, discoverer):
        """Test categorization of configuration documentation."""
        assert discoverer._categorize_doc("CONFIG.md") == DocumentationType.CONFIG
        assert discoverer._categorize_doc("configuration.md") == DocumentationType.CONFIG
        assert discoverer._categorize_doc("docs/settings.md") == DocumentationType.CONFIG

    def test_categorize_other(self, discoverer):
        """Test categorization of other documentation."""
        assert discoverer._categorize_doc("NOTES.md") == DocumentationType.OTHER
        assert discoverer._categorize_doc("random-doc.md") == DocumentationType.OTHER

    @patch('pathlib.Path.rglob')
    def test_discover_local_docs(self, mock_rglob, discoverer):
        """Test discovering documentation files locally."""
        # Mock file paths
        mock_files = [
            Path("README.md"),
            Path("docs/API.md"),
            Path("CONTRIBUTING.md"),
            Path("docs/guide/tutorial.md"),
        ]
        mock_rglob.return_value = mock_files

        docs = discoverer.discover_local_docs()

        assert len(docs) == 4
        assert any(doc.type == DocumentationType.README for doc in docs)
        assert any(doc.type == DocumentationType.API for doc in docs)
        assert any(doc.type == DocumentationType.DEVELOPER for doc in docs)
        assert any(doc.type == DocumentationType.USER_GUIDE for doc in docs)

    @patch('pathlib.Path.rglob')
    def test_discover_local_docs_excludes_node_modules(self, mock_rglob, discoverer):
        """Test that node_modules is excluded from discovery."""
        mock_files = [
            Path("README.md"),
            Path("node_modules/package/README.md"),
            Path("docs/API.md"),
        ]
        mock_rglob.return_value = mock_files

        docs = discoverer.discover_local_docs()

        # Should only find 2 files (excluding node_modules)
        assert len(docs) == 2
        assert all("node_modules" not in str(doc.path) for doc in docs)

    @patch('pathlib.Path.rglob')
    def test_discover_local_docs_excludes_vendor(self, mock_rglob, discoverer):
        """Test that vendor directory is excluded from discovery."""
        mock_files = [
            Path("README.md"),
            Path("vendor/lib/README.md"),
            Path("docs/API.md"),
        ]
        mock_rglob.return_value = mock_files

        docs = discoverer.discover_local_docs()

        assert len(docs) == 2
        assert all("vendor" not in str(doc.path) for doc in docs)

    def test_get_docs_by_type(self, discoverer):
        """Test filtering documentation by type."""
        docs = [
            DocumentationFile("README.md", DocumentationType.README),
            DocumentationFile("API.md", DocumentationType.API),
            DocumentationFile("GUIDE.md", DocumentationType.USER_GUIDE),
            DocumentationFile("CONTRIBUTING.md", DocumentationType.DEVELOPER),
        ]

        readme_docs = discoverer.get_docs_by_type(docs, DocumentationType.README)
        assert len(readme_docs) == 1
        assert readme_docs[0].path == "README.md"

        api_docs = discoverer.get_docs_by_type(docs, DocumentationType.API)
        assert len(api_docs) == 1
        assert api_docs[0].path == "API.md"

    def test_get_docs_summary(self, discoverer):
        """Test generating documentation summary."""
        docs = [
            DocumentationFile("README.md", DocumentationType.README),
            DocumentationFile("API.md", DocumentationType.API),
            DocumentationFile("API-v2.md", DocumentationType.API),
            DocumentationFile("GUIDE.md", DocumentationType.USER_GUIDE),
        ]

        summary = discoverer.get_docs_summary(docs)

        assert summary["total"] == 4
        assert summary["by_type"][DocumentationType.README.value] == 1
        assert summary["by_type"][DocumentationType.API.value] == 2
        assert summary["by_type"][DocumentationType.USER_GUIDE.value] == 1

    def test_format_docs_list(self, discoverer):
        """Test formatting documentation list."""
        docs = [
            DocumentationFile("README.md", DocumentationType.README),
            DocumentationFile("docs/API.md", DocumentationType.API),
        ]

        formatted = discoverer.format_docs_list(docs)

        assert "README.md" in formatted
        assert "docs/API.md" in formatted
        assert "README" in formatted
        assert "API" in formatted

    def test_documentation_file_dataclass(self):
        """Test DocumentationFile dataclass."""
        doc = DocumentationFile("test.md", DocumentationType.README)
        
        assert doc.path == "test.md"
        assert doc.type == DocumentationType.README
        assert isinstance(doc.type, DocumentationType)

    def test_documentation_type_enum(self):
        """Test DocumentationType enum values."""
        assert DocumentationType.README.value == "readme"
        assert DocumentationType.API.value == "api"
        assert DocumentationType.USER_GUIDE.value == "user_guide"
        assert DocumentationType.DEVELOPER.value == "developer"
        assert DocumentationType.CHANGELOG.value == "changelog"
        assert DocumentationType.CONFIG.value == "config"
        assert DocumentationType.OTHER.value == "other"

    @patch('pathlib.Path.rglob')
    def test_discover_local_docs_empty_repo(self, mock_rglob, discoverer):
        """Test discovering docs in empty repository."""
        mock_rglob.return_value = []

        docs = discoverer.discover_local_docs()

        assert len(docs) == 0
        assert isinstance(docs, list)

    def test_categorize_case_insensitive(self, discoverer):
        """Test that categorization is case-insensitive."""
        assert discoverer._categorize_doc("readme.MD") == DocumentationType.README
        assert discoverer._categorize_doc("API.MD") == DocumentationType.API
        assert discoverer._categorize_doc("Contributing.MD") == DocumentationType.DEVELOPER

# Made with Bob
