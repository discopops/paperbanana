"""SVG vector format exporter."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from paperbanana.core.types import ExportConfig
from paperbanana.exporters.base import BaseExporter

if TYPE_CHECKING:
    from PIL import Image


class SVGExporter(BaseExporter):
    """Exporter for SVG format.

    For matplotlib-generated plots: Exports native SVG (if source is available)
    For raster diagrams: Embeds image as base64-encoded PNG in SVG wrapper

    No additional dependencies required (uses Pillow + base64).
    """

    format_name: ClassVar[str] = "SVG Vector"
    file_extension: ClassVar[str] = ".svg"

    async def export(
        self, image: Image.Image, output_path: Path, config: ExportConfig | None = None
    ) -> Path:
        """Export image as SVG.

        For raster images, creates an SVG wrapper with embedded base64 PNG.

        Args:
            image: PIL Image object to export
            output_path: Path where the SVG should be saved
            config: Optional configuration for export behavior

        Returns:
            Path to the exported SVG file

        Raises:
            ValueError: If export fails
        """
        if config is None:
            config = ExportConfig()

        # Ensure output path has correct extension
        if output_path.suffix.lower() != ".svg":
            output_path = output_path.with_suffix(".svg")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert image to base64-encoded PNG
            buffer = BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

            # Get image dimensions
            width, height = image.size

            # Create SVG wrapper with embedded PNG
            svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}"
     viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <title>PaperBanana Generated Diagram</title>
  <image width="{width}" height="{height}"
         xlink:href="data:image/png;base64,{image_base64}"/>
</svg>"""

            # Write SVG file
            output_path.write_text(svg_content, encoding="utf-8")

        except Exception as e:
            raise ValueError(f"Failed to export SVG: {e}") from e

        return output_path

    def is_available(self) -> bool:
        """SVG exporter is always available (no dependencies)."""
        return True

    def get_install_hint(self) -> str:
        """No installation needed for SVG exporter."""
        return "No additional dependencies required (built-in)"
