"""Markdown document loader with section extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar, Optional

from paperbanana.core.types import LoadResult, LoaderConfig
from paperbanana.loaders.base import BaseLoader


class MarkdownLoader(BaseLoader):
    """Loader for Markdown documents with section extraction.

    Parses Markdown headers to identify and extract methodology sections.
    No additional dependencies required (uses regex-based parsing).
    """

    format_name: ClassVar[str] = "Markdown"
    supported_extensions: ClassVar[list[str]] = [".md", ".markdown"]

    # Markdown header patterns for methodology
    METHODOLOGY_HEADERS = [
        r"^#{1,6}\s+method(?:ology|s)?",
        r"^#{1,6}\s+approach(?:es)?",
        r"^#{1,6}\s+experimental\s+(?:setup|design|methodology)",
        r"^#{1,6}\s+materials?\s+and\s+methods?",
        r"^#{1,6}\s+proposed\s+(?:method|approach)",
        r"^#{1,6}\s+framework",
    ]

    async def load(self, path: Path, config: LoaderConfig | None = None) -> LoadResult:
        """Load content from a Markdown file.

        Args:
            path: Path to the Markdown file
            config: Optional configuration for extraction behavior

        Returns:
            LoadResult with extracted text and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if config is None:
            config = LoaderConfig()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Read file
        try:
            full_text = path.read_text(encoding=config.encoding)
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode file with encoding '{config.encoding}': {e}"
            ) from e

        # Extract methodology section if configured
        source_context = full_text
        extraction_method = "full_text"

        if config.extract_methodology:
            extracted = self._extract_methodology_section(full_text)
            if extracted:
                source_context = extracted
                extraction_method = "section_extraction"

        # Apply max length if specified
        if config.max_length and len(source_context) > config.max_length:
            source_context = source_context[: config.max_length]

        # Build metadata
        metadata = {
            "format": "markdown",
            "file_size": path.stat().st_size,
            "extraction_method": extraction_method,
            "truncated": config.max_length is not None
            and len(source_context) == config.max_length,
        }

        return LoadResult(
            source_context=source_context,
            metadata=metadata,
            images=[],
        )

    def _extract_methodology_section(self, text: str) -> Optional[str]:
        """Extract methodology section from Markdown.

        Args:
            text: Full Markdown content

        Returns:
            Extracted methodology section, or None if not found
        """
        lines = text.split("\n")

        # Find methodology header and its level
        start_idx = None
        header_level = None

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for pattern in self.METHODOLOGY_HEADERS:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    start_idx = i + 1
                    # Detect header level (number of # symbols)
                    header_match = re.match(r"^(#{1,6})", line)
                    if header_match:
                        header_level = len(header_match.group(1))
                    break
            if start_idx is not None:
                break

        if start_idx is None:
            return None

        # Find next header of same or higher level (end of section)
        end_idx = len(lines)
        if header_level is not None:
            for i in range(start_idx, len(lines)):
                line = lines[i].strip()
                # Check if this is a header
                header_match = re.match(r"^(#{1,6})\s+", line)
                if header_match:
                    current_level = len(header_match.group(1))
                    # Stop if same or higher level (lower number of #)
                    if current_level <= header_level:
                        end_idx = i
                        break

        # Extract and clean the section
        methodology_lines = lines[start_idx:end_idx]
        methodology_text = "\n".join(methodology_lines).strip()

        # Return None if extraction is too short
        if len(methodology_text) < 100:
            return None

        return methodology_text

    def is_available(self) -> bool:
        """Markdown loader is always available (no dependencies)."""
        return True

    def get_install_hint(self) -> str:
        """No installation needed for Markdown loader."""
        return "No additional dependencies required (built-in)"
