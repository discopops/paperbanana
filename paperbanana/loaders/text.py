"""Plain text document loader."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from paperbanana.core.types import LoadResult, LoaderConfig
from paperbanana.loaders.base import BaseLoader


class TextLoader(BaseLoader):
    """Loader for plain text files (.txt, .md, etc.).

    This is the baseline loader that preserves existing PaperBanana behavior.
    Always available with no additional dependencies.
    """

    format_name: ClassVar[str] = "Plain Text"
    supported_extensions: ClassVar[list[str]] = [".txt", ".text"]

    async def load(self, path: Path, config: LoaderConfig | None = None) -> LoadResult:
        """Load content from a plain text file.

        Args:
            path: Path to the text file
            config: Optional configuration (encoding, max_length)

        Returns:
            LoadResult with file contents and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
            UnicodeDecodeError: If the file encoding is invalid
        """
        if config is None:
            config = LoaderConfig()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Read file with specified encoding
        try:
            source_context = path.read_text(encoding=config.encoding)
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode file with encoding '{config.encoding}': {e}"
            ) from e

        # Apply max length if specified
        if config.max_length and len(source_context) > config.max_length:
            source_context = source_context[: config.max_length]

        # Build metadata
        metadata = {
            "format": "text",
            "encoding": config.encoding,
            "file_size": path.stat().st_size,
            "truncated": config.max_length is not None
            and len(source_context) == config.max_length,
        }

        return LoadResult(
            source_context=source_context,
            metadata=metadata,
            images=[],
        )

    def is_available(self) -> bool:
        """Text loader is always available (no dependencies)."""
        return True

    def get_install_hint(self) -> str:
        """No installation needed for text loader."""
        return "No additional dependencies required (built-in)"
