"""Base classes for image exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from paperbanana.core.types import ExportConfig

if TYPE_CHECKING:
    from PIL import Image


class BaseExporter(ABC):
    """Abstract base class for all image exporters.

    Each exporter handles specific output formats (e.g., PNG, SVG, PDF)
    and converts images to that format.

    Attributes:
        format_name: Human-readable format name (e.g., "PNG Image")
        file_extension: File extension including dot (e.g., ".png")
    """

    format_name: ClassVar[str] = "Unknown"
    file_extension: ClassVar[str] = ".bin"

    @abstractmethod
    async def export(
        self, image: Image.Image, output_path: Path, config: ExportConfig | None = None
    ) -> Path:
        """Export image to specified format.

        Args:
            image: PIL Image object to export
            output_path: Path where the exported file should be saved
            config: Optional configuration for export behavior

        Returns:
            Path to the exported file (same as output_path)

        Raises:
            ValueError: If export fails or format is not supported
            ImportError: If required dependencies are not installed
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if this exporter's dependencies are available.

        Returns:
            True if all required dependencies are installed
        """
        # Base implementation - subclasses override if they have dependencies
        return True

    def get_install_hint(self) -> str:
        """Get installation instructions for missing dependencies.

        Returns:
            pip install command for this exporter's dependencies
        """
        return "No additional dependencies required"
