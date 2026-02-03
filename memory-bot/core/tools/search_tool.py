"""
Web search tool using OpenSERP API.

Provides web search, image search, and multi-engine support through the OpenSERP service.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from .base import Tool, ToolError, ToolResult


class SearchTool(Tool):
    """
    Web search tool using OpenSERP API.

    Supports multiple search engines including Google, Baidu, Bing, and mega (aggregate).
    """

    SUPPORTED_ENGINES = ["mega", "google", "baidu", "bing", "yandex", "duckduckgo"]
    DEFAULT_ENGINE = "mega"
    DEFAULT_LIMIT = 10

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:7000",
        timeout: int = 30
    ):
        """
        Initialize the search tool.

        Args:
            base_url: Base URL for the OpenSERP service.
            timeout: Request timeout in seconds.
        """
        super().__init__(
            name="search",
            description="Web search using multiple search engines (Google, Baidu, Bing, etc.)"
        )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def supported_engines(self) -> List[str]:
        """Get list of supported search engines."""
        return self.SUPPORTED_ENGINES.copy()

    @property
    def default_engine(self) -> str:
        """Get the default search engine."""
        return self.DEFAULT_ENGINE

    def _validate_search_params(
        self,
        query: str,
        engine: str = DEFAULT_ENGINE,
        limit: int = DEFAULT_LIMIT
    ) -> None:
        """
        Validate search parameters.

        Args:
            query: Search query string.
            engine: Search engine to use.
            limit: Maximum number of results.

        Raises:
            ValueError: If parameters are invalid.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if engine not in self.SUPPORTED_ENGINES:
            raise ValueError(
                f"Unsupported engine: {engine}. "
                f"Supported engines: {', '.join(self.SUPPORTED_ENGINES)}"
            )

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

    def _build_url(self, endpoint: str, engine: str) -> str:
        """
        Build the full URL for a search request.

        Args:
            endpoint: API endpoint (search or image).
            engine: Search engine to use.

        Returns:
            str: The complete URL.
        """
        return f"{self.base_url}/{engine}/{endpoint}"

    def _make_request(self, url: str) -> List[Dict[str, Any]]:
        """
        Make an HTTP request to the search API.

        Args:
            url: The URL to request.

        Returns:
            List[Dict]: The JSON response.

        Raises:
            ToolError: If the request fails.
        """
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "MemoryBot-SearchTool/1.0"
                }
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data if isinstance(data, list) else []

        except urllib.error.HTTPError as e:
            raise ToolError(
                f"HTTP error {e.code}: {e.reason}",
                code="HTTP_ERROR"
            )
        except urllib.error.URLError as e:
            raise ToolError(
                f"Failed to connect to search service: {e.reason}",
                code="CONNECTION_ERROR"
            )
        except json.JSONDecodeError as e:
            raise ToolError(
                f"Invalid JSON response: {e}",
                code="PARSE_ERROR"
            )
        except Exception as e:
            raise ToolError(
                f"Unexpected error: {e}",
                code="UNKNOWN_ERROR"
            )

    def _parse_response(self, response: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse and format the search response.

        Args:
            response: Raw API response.

        Returns:
            Dict: Formatted search results.

        Raises:
            ValueError: If response format is invalid.
        """
        if not isinstance(response, list):
            raise ValueError("Invalid response format: expected list")

        results = []
        for item in response:
            if not isinstance(item, dict):
                continue

            result = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", item.get("desc", "")),
            }

            # Include additional fields if present
            if "source" in item:
                result["source"] = item["source"]
            if "image" in item:
                result["image"] = item["image"]

            results.append(result)

        return {
            "results": results,
            "count": len(results),
            "query": "",  # Will be filled by execute
            "engine": ""  # Will be filled by execute
        }

    def search(
        self,
        query: str,
        engine: str = DEFAULT_ENGINE,
        limit: int = DEFAULT_LIMIT
    ) -> ToolResult:
        """
        Perform a web search.

        Args:
            query: Search query string.
            engine: Search engine to use.
            limit: Maximum number of results.

        Returns:
            ToolResult: Search results or error.
        """
        try:
            self._validate_search_params(query, engine, limit)

            encoded_query = urllib.parse.quote(query)
            url = self._build_url("search", engine)
            url = f"{url}?text={encoded_query}&limit={limit}"

            response = self._make_request(url)
            results = self._parse_response(response)
            results["query"] = query
            results["engine"] = engine

            return ToolResult.success_result(
                data=results,
                message=f"Found {results['count']} results for '{query}'"
            )

        except ValueError as e:
            return ToolResult.failure_result(f"Validation error: {e}")
        except ToolError as e:
            return ToolResult.failure_result(f"Search failed: {e.message}", code=e.code)
        except Exception as e:
            return ToolResult.failure_result(f"Unexpected error: {e}")

    def image_search(
        self,
        query: str,
        engine: str = DEFAULT_ENGINE,
        limit: int = DEFAULT_LIMIT
    ) -> ToolResult:
        """
        Perform an image search.

        Args:
            query: Search query string.
            engine: Search engine to use.
            limit: Maximum number of results.

        Returns:
            ToolResult: Image search results or error.
        """
        try:
            self._validate_search_params(query, engine, limit)

            encoded_query = urllib.parse.quote(query)
            url = self._build_url("image", engine)
            url = f"{url}?text={encoded_query}&limit={limit}"

            response = self._make_request(url)
            results = self._parse_response(response)
            results["query"] = query
            results["engine"] = engine
            results["type"] = "images"

            return ToolResult.success_result(
                data=results,
                message=f"Found {results['count']} images for '{query}'"
            )

        except ValueError as e:
            return ToolResult.failure_result(f"Validation error: {e}")
        except ToolError as e:
            return ToolResult.failure_result(f"Image search failed: {e.message}", code=e.code)
        except Exception as e:
            return ToolResult.failure_result(f"Unexpected error: {e}")

    def execute(self, **kwargs) -> ToolResult:
        """
        Execute a search operation.

        Args:
            action: Type of search - "search" or "image" (default: "search").
            query: Search query string.
            engine: Search engine to use.
            limit: Maximum number of results.

        Returns:
            ToolResult: Search results or error.
        """
        action = kwargs.get("action", "search")
        query = kwargs.get("query", "")
        engine = kwargs.get("engine", self.DEFAULT_ENGINE)
        limit = kwargs.get("limit", self.DEFAULT_LIMIT)

        if action == "search":
            return self.search(query, engine, limit)
        elif action == "image":
            return self.image_search(query, engine, limit)
        else:
            return ToolResult.failure_result(f"Unknown search action: {action}")
