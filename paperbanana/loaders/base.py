"""Base classes for document loaders."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from paperbanana.core.types import LoadResult, LoaderConfig


class BaseLoader(ABC):
    """Abstract base class for all document loaders.

    Each loader handles specific input formats (e.g., PDF, Markdown, DOCX)
    and extracts text content in a standardized way.

    Attributes:
        format_name: Human-readable format name (e.g., "PDF Document")
        supported_extensions: List of file extensions this loader handles (e.g., [".pdf"])
    """

    format_name: ClassVar[str] = "Unknown"
    supported_extensions: ClassVar[list[str]] = []

    def can_handle(self, path: Path) -> bool:
        """Check if this loader can handle the given file.

        Args:
            path: Path to the file to check

        Returns:
            True if this loader supports the file's extension
        """
        return path.suffix.lower() in self.supported_extensions

    @abstractmethod
    async def load(self, path: Path, config: LoaderConfig | None = None) -> LoadResult:
        """Load content from a document.

        Args:
            path: Path to the document to load
            config: Optional configuration for loading behavior

        Returns:
            LoadResult containing extracted text and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid or cannot be parsed
            ImportError: If required dependencies are not installed
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if this loader's dependencies are available.

        Returns:
            True if all required dependencies are installed
        """
        # Base implementation - subclasses override if they have dependencies
        return True

    def get_install_hint(self) -> str:
        """Get installation instructions for missing dependencies.

        Returns:
            pip install command for this loader's dependencies
        """
        return "No additional dependencies required"
