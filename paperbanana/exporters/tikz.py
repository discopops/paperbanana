"""LaTeX/TikZ code exporter using VLM."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional

from paperbanana.core.types import ExportConfig
from paperbanana.exporters.base import BaseExporter

if TYPE_CHECKING:
    from PIL import Image

    from paperbanana.providers.base import BaseVLM


TIKZ_GENERATION_PROMPT = """Analyze this academic diagram and generate equivalent LaTeX/TikZ code.

Your task is to recreate this diagram as precise, compilable TikZ code that can be embedded in an academic paper.

Requirements:
1. Use standard TikZ packages (tikz, positioning, shapes, arrows.meta)
2. Maintain the exact visual structure, layout, and relationships shown
3. Preserve all text labels exactly as shown
4. Use appropriate node shapes (rectangle, circle, ellipse, etc.)
5. Match arrow styles and connections
6. Maintain relative positioning and spacing
7. Include color definitions if colors are used
8. Add comments explaining major components

Output format:
- Start with required package imports
- Define any custom styles or colors
- Provide complete, compilable tikzpicture environment
- Include standalone document wrapper for testing

The code should be publication-ready and require minimal manual editing."""


class TikZExporter(BaseExporter):
    """Exporter for LaTeX/TikZ code format.

    Uses a VLM to analyze the diagram and generate equivalent TikZ code.
    This is a best-effort approach - users may need to refine the generated code.

    Requires: VLM provider with vision capabilities
    """

    format_name: ClassVar[str] = "LaTeX/TikZ"
    file_extension: ClassVar[str] = ".tex"

    def __init__(self, vlm: Optional[BaseVLM] = None):
        """Initialize TikZ exporter.

        Args:
            vlm: Optional VLM provider for code generation
        """
        self.vlm = vlm

    async def export(
        self, image: Image.Image, output_path: Path, config: ExportConfig | None = None
    ) -> Path:
        """Export diagram as LaTeX/TikZ code.

        Args:
            image: PIL Image object to analyze
            output_path: Path where the .tex file should be saved
            config: Optional configuration for export behavior

        Returns:
            Path to the exported .tex file

        Raises:
            ValueError: If VLM is not configured or export fails
        """
        if config is None:
            config = ExportConfig()

        if self.vlm is None:
            raise ValueError(
                "TikZ export requires a VLM provider. "
                "Configure via: exporter.vlm = ProviderRegistry.create_vlm(settings)"
            )

        # Ensure output path has correct extension
        if output_path.suffix.lower() != ".tex":
            output_path = output_path.with_suffix(".tex")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Save image temporarily for VLM analysis
            temp_image_path = output_path.parent / f"{output_path.stem}_temp.png"
            image.save(temp_image_path, format="PNG")

            # Generate TikZ code using VLM
            tikz_code = await self._generate_tikz_code(temp_image_path)

            # Clean up temporary image
            temp_image_path.unlink(missing_ok=True)

            # Write TikZ code to file
            output_path.write_text(tikz_code, encoding="utf-8")

        except Exception as e:
            raise ValueError(f"Failed to export TikZ: {e}") from e

        return output_path

    async def _generate_tikz_code(self, image_path: Path) -> str:
        """Generate TikZ code from diagram image using VLM.

        Args:
            image_path: Path to the diagram image

        Returns:
            Generated LaTeX/TikZ code
        """
        # Read image for VLM analysis
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Generate TikZ code using VLM
        response = await self.vlm.generate(
            prompt=TIKZ_GENERATION_PROMPT, images=[image_data]
        )

        # Extract TikZ code from response
        # The VLM should return code, but we'll clean it up
        tikz_code = self._extract_code_from_response(response)

        return tikz_code

    def _extract_code_from_response(self, response: str) -> str:
        """Extract clean TikZ code from VLM response.

        Args:
            response: Raw VLM response

        Returns:
            Cleaned TikZ code
        """
        # Try to extract code blocks
        if "```" in response:
            # Find LaTeX code block
            code_blocks = []
            in_code = False
            current_block = []

            for line in response.split("\n"):
                if line.strip().startswith("```"):
                    if in_code:
                        code_blocks.append("\n".join(current_block))
                        current_block = []
                        in_code = False
                    else:
                        in_code = True
                elif in_code:
                    current_block.append(line)

            # Return the first substantial code block
            for block in code_blocks:
                if "\\begin{tikzpicture}" in block or "\\documentclass" in block:
                    return block

        # If no code blocks found, return the whole response
        # (assume VLM returned clean code)
        return response

    def is_available(self) -> bool:
        """TikZ exporter is available if VLM is configured."""
        return self.vlm is not None and self.vlm.is_available()

    def get_install_hint(self) -> str:
        """Get instructions for configuring TikZ exporter."""
        return (
            "TikZ export requires a VLM provider. "
            "Configure via: exporter.vlm = ProviderRegistry.create_vlm(settings)"
        )
