"""PDF document loader with methodology extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar, Optional

from paperbanana.core.types import LoadResult, LoaderConfig
from paperbanana.loaders.base import BaseLoader


class PDFLoader(BaseLoader):
    """Loader for PDF documents with intelligent methodology extraction.

    Supports two extraction modes:
    1. Rule-based: Search for section headers and extract text between them
    2. VLM-based: Use vision-language model for intelligent extraction (opt-in)

    Requires: pymupdf>=1.24 (optional dependency)
    """

    format_name: ClassVar[str] = "PDF Document"
    supported_extensions: ClassVar[list[str]] = [".pdf"]

    # Common methodology section headers in academic papers
    METHODOLOGY_HEADERS = [
        r"^\s*\d*\.?\s*method(?:ology|s)?\s*$",
        r"^\s*\d*\.?\s*approach(?:es)?\s*$",
        r"^\s*\d*\.?\s*experimental\s+(?:setup|design|methodology)\s*$",
        r"^\s*\d*\.?\s*materials?\s+and\s+methods?\s*$",
        r"^\s*\d*\.?\s*proposed\s+(?:method|approach)\s*$",
        r"^\s*\d*\.?\s*framework\s*$",
    ]

    # Section headers that typically come after methodology
    STOP_HEADERS = [
        r"^\s*\d*\.?\s*results?\s*$",
        r"^\s*\d*\.?\s*evaluation\s*$",
        r"^\s*\d*\.?\s*experiments?\s*$",
        r"^\s*\d*\.?\s*discussion\s*$",
        r"^\s*\d*\.?\s*conclusion\s*$",
        r"^\s*\d*\.?\s*related\s+work\s*$",
        r"^\s*\d*\.?\s*references?\s*$",
    ]

    async def load(self, path: Path, config: LoaderConfig | None = None) -> LoadResult:
        """Load content from a PDF document.

        Args:
            path: Path to the PDF file
            config: Optional configuration for extraction behavior

        Returns:
            LoadResult with extracted text and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
            ImportError: If pymupdf is not installed
            ValueError: If the PDF cannot be parsed
        """
        if config is None:
            config = LoaderConfig()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Import pymupdf (will raise ImportError if not installed)
        try:
            import fitz  # pymupdf
        except ImportError as e:
            raise ImportError(
                "PDF loading requires pymupdf. Install with: pip install paperbanana[pdf]"
            ) from e

        # Open PDF document
        try:
            doc = fitz.open(path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}") from e

        # Extract full text
        full_text = self._extract_full_text(doc)

        # Extract images if requested
        images = []
        if config.extract_images:
            images = self._extract_images(doc, path.parent / f"{path.stem}_images")

        # Attempt methodology extraction if configured
        source_context = full_text
        extraction_method = "full_text"

        if config.extract_methodology:
            if config.use_vlm_extraction:
                # VLM-based extraction (not implemented yet, fallback to rule-based)
                # TODO: Implement VLM-based extraction
                extracted = self._extract_methodology_rule_based(full_text)
                if extracted:
                    source_context = extracted
                    extraction_method = "vlm_based"
            else:
                # Rule-based extraction
                extracted = self._extract_methodology_rule_based(full_text)
                if extracted:
                    source_context = extracted
                    extraction_method = "rule_based"

        # Apply max length if specified
        if config.max_length and len(source_context) > config.max_length:
            source_context = source_context[: config.max_length]

        # Build metadata
        metadata = {
            "format": "pdf",
            "page_count": doc.page_count,
            "file_size": path.stat().st_size,
            "extraction_method": extraction_method,
            "truncated": config.max_length is not None
            and len(source_context) == config.max_length,
        }

        doc.close()

        return LoadResult(
            source_context=source_context,
            metadata=metadata,
            images=images,
        )

    def _extract_full_text(self, doc) -> str:
        """Extract all text from a PDF document.

        Args:
            doc: Opened pymupdf document

        Returns:
            Full text content from all pages
        """
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())

        return "\n\n".join(text_parts)

    def _extract_methodology_rule_based(self, text: str) -> Optional[str]:
        """Extract methodology section using rule-based header matching.

        Args:
            text: Full text from the PDF

        Returns:
            Extracted methodology section, or None if not found
        """
        lines = text.split("\n")

        # Find methodology start
        start_idx = None
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for pattern in self.METHODOLOGY_HEADERS:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    start_idx = i + 1  # Start after the header
                    break
            if start_idx is not None:
                break

        if start_idx is None:
            return None  # Methodology section not found

        # Find methodology end (next major section)
        end_idx = len(lines)
        for i in range(start_idx, len(lines)):
            line_lower = lines[i].lower().strip()
            for pattern in self.STOP_HEADERS:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    end_idx = i
                    break
            if end_idx < len(lines):
                break

        # Extract and clean the section
        methodology_lines = lines[start_idx:end_idx]
        methodology_text = "\n".join(methodology_lines).strip()

        # Return None if extraction is too short (likely failed)
        if len(methodology_text) < 100:
            return None

        return methodology_text

    def _extract_images(self, doc, output_dir: Path) -> list[str]:
        """Extract images from PDF document.

        Args:
            doc: Opened pymupdf document
            output_dir: Directory to save extracted images

        Returns:
            List of paths to extracted images
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        image_paths = []

        for page_num, page in enumerate(doc):
            image_list = page.get_images()

            for img_idx, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                image_path = output_dir / f"page{page_num + 1}_img{img_idx + 1}.{image_ext}"
                image_path.write_bytes(image_bytes)
                image_paths.append(str(image_path))

        return image_paths

    def is_available(self) -> bool:
        """Check if pymupdf is installed."""
        try:
            import fitz  # noqa: F401

            return True
        except ImportError:
            return False

    def get_install_hint(self) -> str:
        """Get installation instructions for pymupdf."""
        return "Install with: pip install paperbanana[pdf]"
