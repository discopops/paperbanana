"""TIFF high-resolution image exporter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from paperbanana.core.types import ExportConfig
from paperbanana.exporters.base import BaseExporter

if TYPE_CHECKING:
    from PIL import Image


class TIFFExporter(BaseExporter):
    """Exporter for TIFF format.

    High-resolution lossless format suitable for print publication.
    Uses LZW compression for smaller file sizes while maintaining quality.

    No additional dependencies required (Pillow built-in).
    """

    format_name: ClassVar[str] = "TIFF (High-Res)"
    file_extension: ClassVar[str] = ".tiff"

    async def export(
        self, image: Image.Image, output_path: Path, config: ExportConfig | None = None
    ) -> Path:
        """Export image as TIFF.

        Args:
            image: PIL Image object to export
            output_path: Path where the TIFF should be saved
            config: Optional configuration for export behavior

        Returns:
            Path to the exported TIFF file

        Raises:
            ValueError: If export fails
        """
        if config is None:
            config = ExportConfig()

        # Ensure output path has correct extension
        if output_path.suffix.lower() not in [".tiff", ".tif"]:
            output_path = output_path.with_suffix(".tiff")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Save as TIFF with LZW compression
            save_kwargs = {
                "format": "TIFF",
                "dpi": (config.dpi, config.dpi),
                "compression": config.compression or "tiff_lzw",
            }

            # Add metadata if requested
            if config.embed_metadata:
                save_kwargs["description"] = "PaperBanana Generated Diagram"

            image.save(output_path, **save_kwargs)

        except Exception as e:
            raise ValueError(f"Failed to export TIFF: {e}") from e

        return output_path

    def is_available(self) -> bool:
        """TIFF exporter is always available (Pillow built-in)."""
        return True

    def get_install_hint(self) -> str:
        """No installation needed for TIFF exporter."""
        return "No additional dependencies required (Pillow built-in)"
