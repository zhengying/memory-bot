"""Unit tests for SearchTool."""

import json
from unittest.mock import MagicMock, patch

import pytest

from core.tools.search_tool import SearchTool


class TestSearchToolInit:
    """Test SearchTool initialization."""

    def test_init_with_default_base_url(self):
        """Test initialization with default base URL."""
        tool = SearchTool()
        assert tool.name == "search"
        assert "web search" in tool.description.lower()
        assert tool.base_url == "http://127.0.0.1:7000"
        assert tool.default_engine == "mega"
        assert tool.timeout == 30

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        tool = SearchTool(base_url="http://custom:8080")
        assert tool.base_url == "http://custom:8080"

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        tool = SearchTool(timeout=60)
        assert tool.timeout == 60

    def test_supported_engines(self):
        """Test list of supported engines."""
        tool = SearchTool()
        engines = tool.supported_engines
        assert "mega" in engines
        assert "google" in engines
        assert "baidu" in engines
        assert "bing" in engines


class TestSearchToolValidateParams:
    """Test parameter validation."""

    def test_valid_search_params(self):
        """Test valid search parameters."""
        tool = SearchTool()
        # Should not raise
        tool._validate_search_params("test query", engine="mega")
        tool._validate_search_params("test query", engine="google")
        tool._validate_search_params("test query", engine="baidu")

    def test_empty_query(self):
        """Test empty query validation."""
        tool = SearchTool()
        with pytest.raises(ValueError, match="Query cannot be empty"):
            tool._validate_search_params("")
        with pytest.raises(ValueError, match="Query cannot be empty"):
            tool._validate_search_params("   ")
        with pytest.raises(ValueError, match="Query cannot be empty"):
            tool._validate_search_params(None)

    def test_invalid_engine(self):
        """Test invalid engine validation."""
        tool = SearchTool()
        with pytest.raises(ValueError, match="Unsupported engine"):
            tool._validate_search_params("test", engine="invalid_engine")

    def test_invalid_limit(self):
        """Test invalid limit validation."""
        tool = SearchTool()
        with pytest.raises(ValueError, match="Limit must be between"):
            tool._validate_search_params("test", limit=0)
        with pytest.raises(ValueError, match="Limit must be between"):
            tool._validate_search_params("test", limit=101)


class TestSearchToolBuildUrl:
    """Test URL building."""

    def test_build_search_url(self):
        """Test building search URL."""
        tool = SearchTool()
        url = tool._build_url("search", "google")
        assert url == "http://127.0.0.1:7000/google/search"

    def test_build_image_url(self):
        """Test building image search URL."""
        tool = SearchTool()
        url = tool._build_url("image", "mega")
        assert url == "http://127.0.0.1:7000/mega/image"


class TestSearchToolParseResponse:
    """Test response parsing."""

    def test_parse_valid_response(self):
        """Test parsing valid JSON response."""
        tool = SearchTool()
        mock_response = [
            {"title": "Test", "url": "http://example.com", "description": "Test desc"}
        ]
        result = tool._parse_response(mock_response)
        assert result["results"] == mock_response
        assert result["count"] == 1

    def test_parse_empty_response(self):
        """Test parsing empty response."""
        tool = SearchTool()
        result = tool._parse_response([])
        assert result["results"] == []
        assert result["count"] == 0

    def test_parse_invalid_response(self):
        """Test parsing invalid response."""
        tool = SearchTool()
        with pytest.raises(ValueError, match="Invalid response format"):
            tool._parse_response("not a list")


class TestSearchToolExecute:
    """Test main execute method."""

    @patch("urllib.request.urlopen")
    def test_execute_successful_search(self, mock_urlopen, tmp_path):
        """Test successful search execution."""
        tool = SearchTool()
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"title": "Test", "url": "http://example.com"}
        ]).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = tool.execute(query="test query")
        assert result.success is True
        assert result.data is not None

    def test_execute_missing_query(self):
        """Test execution without query."""
        tool = SearchTool()
        result = tool.execute()
        assert result.success is False
        assert "query" in result.message.lower()

    @patch("urllib.request.urlopen")
    def test_execute_network_error(self, mock_urlopen):
        """Test handling of network errors."""
        tool = SearchTool()
        mock_urlopen.side_effect = Exception("Connection refused")

        result = tool.execute(query="test")
        assert result.success is False
        assert "error" in result.message.lower() or "failed" in result.message.lower()


class TestSearchToolImageSearch:
    """Test image search functionality."""

    @patch("urllib.request.urlopen")
    def test_image_search_success(self, mock_urlopen):
        """Test successful image search."""
        tool = SearchTool()
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"url": "http://example.com/image.jpg", "title": "Test Image"}
        ]).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = tool.image_search("cat")
        assert result.success is True
        assert result.data is not None

    def test_image_search_empty_query(self):
        """Test image search with empty query."""
        tool = SearchTool()
        result = tool.image_search("")
        assert result.success is False


class TestSearchToolEngines:
    """Test different search engines."""

    @pytest.mark.parametrize("engine", ["google", "baidu", "bing", "mega"])
    @patch("urllib.request.urlopen")
    def test_search_with_different_engines(self, mock_urlopen, engine):
        """Test search with different engines."""
        tool = SearchTool()
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([]).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = tool.execute(query="test", engine=engine)
        assert result.success is True


class TestSearchToolErrorHandling:
    """Test error handling and edge cases."""

    def test_timeout_configuration(self):
        """Test timeout configuration."""
        tool = SearchTool(timeout=5)
        assert tool.timeout == 5

    @patch("urllib.request.urlopen")
    def test_json_decode_error(self, mock_urlopen):
        """Test handling of invalid JSON response."""
        tool = SearchTool()
        mock_response = MagicMock()
        mock_response.read.return_value = b"invalid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = tool.execute(query="test")
        assert result.success is False
