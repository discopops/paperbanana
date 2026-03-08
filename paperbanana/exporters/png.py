"""PNG image exporter (baseline format)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from paperbanana.core.types import ExportConfig
from paperbanana.exporters.base import BaseExporter

if TYPE_CHECKING:
    from PIL import Image


class PNGExporter(BaseExporter):
    """Exporter for PNG format.

    This is the baseline format that PaperBanana originally supported.
    Uses Pillow's PNG export with optimization.

    No additional dependencies required (Pillow is a core dependency).
    """

    format_name: ClassVar[str] = "PNG Image"
    file_extension: ClassVar[str] = ".png"

    async def export(
        self, image: Image.Image, output_path: Path, config: ExportConfig | None = None
    ) -> Path:
        """Export image as PNG.

        Args:
            image: PIL Image object to export
            output_path: Path where the PNG should be saved
            config: Optional configuration for export behavior

        Returns:
            Path to the exported PNG file

        Raises:
            ValueError: If export fails
        """
        if config is None:
            config = ExportConfig()

        # Ensure output path has correct extension
        if output_path.suffix.lower() != ".png":
            output_path = output_path.with_suffix(".png")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Save as PNG with optimization
            image.save(
                output_path,
                format="PNG",
                optimize=True,
                dpi=(config.dpi, config.dpi),
            )
        except Exception as e:
            raise ValueError(f"Failed to export PNG: {e}") from e

        return output_path

    def is_available(self) -> bool:
        """PNG exporter is always available (Pillow is core dependency)."""
        return True

    def get_install_hint(self) -> str:
        """No installation needed for PNG exporter."""
        return "No additional dependencies required (Pillow is a core dependency)"
