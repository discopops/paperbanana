"""Registry for discovering and instantiating document loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Type

from paperbanana.loaders.base import BaseLoader


class LoaderRegistry:
    """Central registry for all document loaders.

    Handles auto-detection of file formats and loader instantiation.
    Uses a plugin architecture where loaders self-register via class attributes.
    """

    _loaders: dict[str, Type[BaseLoader]] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Lazy initialization of loader registry.

        Imports all loader implementations to populate the registry.
        Only runs once on first access.
        """
        if cls._initialized:
            return

        # Import all loader implementations (triggers self-registration)
        try:
            from paperbanana.loaders.text import TextLoader

            cls._loaders["text"] = TextLoader
        except ImportError:
            pass

        try:
            from paperbanana.loaders.pdf import PDFLoader

            cls._loaders["pdf"] = PDFLoader
        except ImportError:
            pass

        try:
            from paperbanana.loaders.markdown import MarkdownLoader

            cls._loaders["markdown"] = MarkdownLoader
        except ImportError:
            pass

        try:
            from paperbanana.loaders.html import HTMLLoader

            cls._loaders["html"] = HTMLLoader
        except ImportError:
            pass

        try:
            from paperbanana.loaders.docx import DOCXLoader

            cls._loaders["docx"] = DOCXLoader
        except ImportError:
            pass

        cls._initialized = True

    @classmethod
    def create(cls, format_name: str) -> BaseLoader:
        """Create a loader instance for a specific format.

        Args:
            format_name: Format identifier (e.g., "pdf", "markdown", "text")

        Returns:
            Loader instance for the specified format

        Raises:
            ValueError: If the format is not supported or dependencies are missing
        """
        cls._initialize()

        format_name = format_name.lower()
        if format_name not in cls._loaders:
            available = ", ".join(cls._loaders.keys())
            raise ValueError(
                f"Unsupported format: {format_name}. Available formats: {available}"
            )

        loader_class = cls._loaders[format_name]
        loader = loader_class()

        if not loader.is_available():
            hint = loader.get_install_hint()
            raise ValueError(
                f"{loader.format_name} loader is not available.\n{hint}"
            )

        return loader

    @classmethod
    def auto_detect(cls, path: Path) -> BaseLoader:
        """Auto-detect the appropriate loader for a file.

        Detects format from file extension and returns the corresponding loader.
        Falls back to TextLoader if no specific loader is found.

        Args:
            path: Path to the file to load

        Returns:
            Loader instance that can handle the file

        Raises:
            ValueError: If no suitable loader is found or dependencies are missing
        """
        cls._initialize()

        # Convert to Path if string
        if isinstance(path, str):
            path = Path(path)

        # Try to find a loader that can handle this file
        for loader_class in cls._loaders.values():
            loader = loader_class()
            if loader.can_handle(path) and loader.is_available():
                return loader

        # Fallback to text loader (always available)
        if "text" in cls._loaders:
            return cls._loaders["text"]()

        raise ValueError(f"No loader available for file: {path}")

    @classmethod
    def get_available_formats(cls) -> dict[str, str]:
        """Get all available formats and their display names.

        Returns:
            Dict mapping format identifiers to human-readable names
        """
        cls._initialize()

        formats = {}
        for name, loader_class in cls._loaders.items():
            loader = loader_class()
            if loader.is_available():
                formats[name] = loader.format_name

        return formats

    @classmethod
    def get_unavailable_formats(cls) -> dict[str, str]:
        """Get formats with missing dependencies and installation hints.

        Returns:
            Dict mapping format names to installation instructions
        """
        cls._initialize()

        unavailable = {}
        for name, loader_class in cls._loaders.items():
            loader = loader_class()
            if not loader.is_available():
                unavailable[name] = loader.get_install_hint()

        return unavailable
