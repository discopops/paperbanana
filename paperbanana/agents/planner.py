"""Planner Agent: Generates detailed textual descriptions from source context."""

from __future__ import annotations

from pathlib import Path

import structlog

from paperbanana.agents.base import BaseAgent
from paperbanana.core.types import DiagramType, ReferenceExample, ReferencePatterns
from paperbanana.core.utils import load_image
from paperbanana.providers.base import VLMProvider

logger = structlog.get_logger()


class PlannerAgent(BaseAgent):
    """Generates a comprehensive textual description for diagram generation.

    Uses in-context learning from retrieved reference examples (including
    their images) to create a detailed description that the Visualizer
    can render. Matches paper equation 4: P = VLM_plan(S, C, {(S_i, C_i, I_i)}).
    """

    def __init__(
        self,
        vlm_provider: VLMProvider,
        prompt_dir: str = "prompts",
        enable_reference_analysis: bool = False,
    ):
        super().__init__(vlm_provider, prompt_dir)
        self._enable_reference_analysis = enable_reference_analysis

    @property
    def agent_name(self) -> str:
        return "planner"

    async def run(
        self,
        source_context: str,
        caption: str,
        examples: list[ReferenceExample],
        diagram_type: DiagramType = DiagramType.METHODOLOGY,
    ) -> str:
        """Generate a detailed textual description of the target diagram.

        Args:
            source_context: Methodology text from the paper.
            caption: Communicative intent / figure caption.
            examples: Retrieved reference examples for in-context learning.
            diagram_type: Type of diagram being generated.

        Returns:
            Detailed textual description for the Visualizer.
        """
        # PHASE 1: Reference Pattern Analysis (NEW - Optional)
        reference_patterns = None
        if self._enable_reference_analysis and self.vlm.supports_code_execution():
            logger.info("Analyzing reference patterns with agentic vision")
            reference_patterns = await self._analyze_reference_patterns(examples)
            logger.info(
                "Reference pattern analysis complete",
                has_layout=reference_patterns.layout_structure is not None,
                num_colors=len(reference_patterns.color_palette),
            )

        # PHASE 2: Description Generation (EXISTING - Enhanced with patterns)
        # Format examples for in-context learning
        examples_text = self._format_examples(examples)

        # Load reference images for visual in-context learning
        example_images = self._load_example_images(examples)

        # Include reference patterns in prompt if available
        pattern_context = ""
        if reference_patterns:
            pattern_context = self._format_pattern_context(reference_patterns)

        prompt_type = "diagram" if diagram_type == DiagramType.METHODOLOGY else "plot"
        template = self.load_prompt(prompt_type)
        prompt = self.format_prompt(
            template,
            source_context=source_context,
            caption=caption,
            examples=examples_text,
            reference_patterns=pattern_context,
        )

        logger.info(
            "Running planner agent",
            num_examples=len(examples),
            num_images=len(example_images),
            context_length=len(source_context),
        )

        description = await self.vlm.generate(
            prompt=prompt,
            images=example_images if example_images else None,
            temperature=0.7,
            max_tokens=4096,
        )

        logger.info("Planner generated description", length=len(description))
        return description

    def _format_examples(self, examples: list[ReferenceExample]) -> str:
        """Format reference examples for the planner prompt.

        Each example includes its text metadata and a reference to the
        corresponding image (passed separately as visual input).
        """
        if not examples:
            return "(No reference examples available. Generate based on source context alone.)"

        lines = []
        img_index = 0
        for i, ex in enumerate(examples, 1):
            has_image = self._has_valid_image(ex)
            image_ref = ""
            if has_image:
                img_index += 1
                image_ref = f"\n**Diagram**: [See reference image {img_index} above]"

            lines.append(
                f"### Example {i}\n"
                f"**Caption**: {ex.caption}\n"
                f"**Source Context**: {ex.source_context[:500]}"
                f"{image_ref}\n"
            )
        return "\n".join(lines)

    def _has_valid_image(self, example: ReferenceExample) -> bool:
        """Check if a reference example has a valid image file."""
        if not example.image_path:
            return False
        return Path(example.image_path).exists()

    def _load_example_images(self, examples: list[ReferenceExample]) -> list:
        """Load reference images from disk for in-context learning.

        Returns a list of PIL Image objects for examples that have valid images.
        """
        images = []
        for ex in examples:
            if not self._has_valid_image(ex):
                continue
            try:
                img = load_image(ex.image_path)
                images.append(img)
            except Exception as e:
                logger.warning(
                    "Failed to load reference image",
                    image_path=ex.image_path,
                    error=str(e),
                )
        return images

    async def _analyze_reference_patterns(
        self, examples: list[ReferenceExample]
    ) -> ReferencePatterns:
        """Analyze visual patterns from reference examples using code execution.

        Uses Gemini 3 Flash's agentic vision to extract quantitative design
        patterns from reference diagrams, informing better initial descriptions.

        Args:
            examples: Reference examples with images to analyze.

        Returns:
            ReferencePatterns with extracted visual patterns.
        """
        # Load reference images (analyze top 5)
        example_images = self._load_example_images(examples[:5])
        if not example_images:
            logger.warning("No reference images available for pattern analysis")
            return ReferencePatterns()

        analysis_prompt = f"""You are a visual design pattern expert with Python code execution.

Analyze these {len(example_images)} reference academic diagrams to extract successful design patterns.

Use Python + PIL/numpy/matplotlib to:

1. LAYOUT STRUCTURE
   - Identify dominant layout pattern (vertical/horizontal flow, grid, etc.)
   - Measure component distribution and hierarchy
   - Calculate spacing and margin ratios

2. COLOR ANALYSIS
   - Extract color palette (dominant colors as hex codes)
   - Identify color roles (background, text, accent, etc.)

3. TYPOGRAPHY PATTERNS
   - Estimate text sizes for different roles (title, labels, body)
   - Identify font hierarchy patterns

4. VISUAL FLOW
   - Determine reading order (top-to-bottom, left-to-right, etc.)
   - Identify connection patterns (arrows, lines, grouping boxes)

5. SUCCESSFUL PATTERNS
   - What makes these diagrams effective?
   - Common design elements that appear consistently

Output JSON:
{{
    "layout_structure": "vertical flow with horizontal sub-components",
    "component_hierarchy": {{"main_boxes": 3, "sub_components": 8}},
    "color_palette": ["#FFFFFF", "#E8F4F8", "#FFE4CC"],
    "spacing_ratios": {{"margin": 0.08, "padding": 0.05, "gap": 0.03}},
    "text_sizes": {{"title": 16, "labels": 12, "body": 10}},
    "visual_flow": "top-to-bottom with left-to-right reading",
    "successful_patterns": ["Consistent color coding", "Clear visual hierarchy", "Adequate whitespace"]
}}
"""

        try:
            response = await self.vlm.generate_with_tools(
                prompt=analysis_prompt,
                images=example_images,
                temperature=0.1,  # Low temp for deterministic analysis
                max_tokens=4096,
                response_format="json",
                tools=["code_execution"],
            )
            return self._parse_reference_patterns(response)
        except Exception as e:
            logger.error(
                "Reference pattern analysis failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return ReferencePatterns()

    def _parse_reference_patterns(self, response: str) -> ReferencePatterns:
        """Parse JSON response into ReferencePatterns model."""
        import json

        try:
            data = json.loads(response)
            return ReferencePatterns(**data, raw_output=response)
        except Exception as e:
            logger.warning("Failed to parse reference patterns", error=str(e))
            return ReferencePatterns(raw_output=response)

    def _format_pattern_context(self, patterns: ReferencePatterns) -> str:
        """Format reference patterns for inclusion in planner prompt."""
        parts = ["REFERENCE VISUAL PATTERNS (from successful diagrams):"]

        if patterns.layout_structure:
            parts.append(f"Layout: {patterns.layout_structure}")

        if patterns.color_palette:
            parts.append(f"Color Palette: {', '.join(patterns.color_palette)}")

        if patterns.spacing_ratios:
            ratios = ", ".join(f"{k}={v:.2f}" for k, v in patterns.spacing_ratios.items())
            parts.append(f"Spacing Ratios: {ratios}")

        if patterns.text_sizes:
            sizes = ", ".join(f"{k}={v}pt" for k, v in patterns.text_sizes.items())
            parts.append(f"Text Sizes: {sizes}")

        if patterns.visual_flow:
            parts.append(f"Visual Flow: {patterns.visual_flow}")

        if patterns.successful_patterns:
            parts.append("Successful Patterns:")
            parts.extend(f"  - {p}" for p in patterns.successful_patterns)

        return "\n".join(parts)
