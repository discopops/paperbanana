"""HTML document loader with content extraction."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from paperbanana.core.types import LoadResult, LoaderConfig
from paperbanana.loaders.base import BaseLoader


class HTMLLoader(BaseLoader):
    """Loader for HTML documents with intelligent content extraction.

    Removes script/style tags, navigation, and boilerplate.
    Prefers main content areas (main, article tags).

    Requires: beautifulsoup4>=4.12, lxml>=5.0 (optional dependencies)
    """

    format_name: ClassVar[str] = "HTML"
    supported_extensions: ClassVar[list[str]] = [".html", ".htm"]

    async def load(self, path: Path, config: LoaderConfig | None = None) -> LoadResult:
        """Load content from an HTML file.

        Args:
            path: Path to the HTML file
            config: Optional configuration for extraction behavior

        Returns:
            LoadResult with extracted text and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
            ImportError: If beautifulsoup4 or lxml is not installed
        """
        if config is None:
            config = LoaderConfig()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Import dependencies
        try:
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise ImportError(
                "HTML loading requires beautifulsoup4 and lxml. "
                "Install with: pip install paperbanana[html]"
            ) from e

        # Read file
        try:
            html_content = path.read_text(encoding=config.encoding)
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode file with encoding '{config.encoding}': {e}"
            ) from e

        # Parse HTML
        soup = BeautifulSoup(html_content, "lxml")

        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # Try to find main content area
        main_content = None

        # Priority 1: <main> tag
        main_tag = soup.find("main")
        if main_tag:
            main_content = main_tag.get_text(separator="\n", strip=True)

        # Priority 2: <article> tag
        if not main_content:
            article_tag = soup.find("article")
            if article_tag:
                main_content = article_tag.get_text(separator="\n", strip=True)

        # Priority 3: Full body
        if not main_content:
            body_tag = soup.find("body")
            if body_tag:
                main_content = body_tag.get_text(separator="\n", strip=True)

        # Fallback: All text
        if not main_content:
            main_content = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in main_content.split("\n") if line.strip()]
        source_context = "\n".join(lines)

        # Apply max length if specified
        if config.max_length and len(source_context) > config.max_length:
            source_context = source_context[: config.max_length]

        # Build metadata
        metadata = {
            "format": "html",
            "file_size": path.stat().st_size,
            "title": soup.title.string if soup.title else None,
            "truncated": config.max_length is not None
            and len(source_context) == config.max_length,
        }

        return LoadResult(
            source_context=source_context,
            metadata=metadata,
            images=[],
        )

    def is_available(self) -> bool:
        """Check if beautifulsoup4 and lxml are installed."""
        try:
            import bs4  # noqa: F401
            import lxml  # noqa: F401

            return True
        except ImportError:
            return False

    def get_install_hint(self) -> str:
        """Get installation instructions for HTML dependencies."""
        return "Install with: pip install paperbanana[html]"
