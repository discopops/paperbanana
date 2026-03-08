"""Critic Agent: Evaluates generated images and provides revision feedback."""

from __future__ import annotations

import json

import structlog

from paperbanana.agents.base import BaseAgent
from paperbanana.core.types import CritiqueResult, DiagramType, VisualAnalysis
from paperbanana.core.utils import load_image
from paperbanana.providers.base import VLMProvider

logger = structlog.get_logger()


class CriticAgent(BaseAgent):
    """Evaluates generated diagrams and provides specific revision feedback.

    Compares the generated image against the source context to identify
    faithfulness, conciseness, readability, and aesthetic issues.
    """

    def __init__(
        self,
        vlm_provider: VLMProvider,
        prompt_dir: str = "prompts",
        enable_visual_analysis: bool = False,
    ):
        super().__init__(vlm_provider, prompt_dir)
        self._enable_visual_analysis = enable_visual_analysis

    @property
    def agent_name(self) -> str:
        return "critic"

    async def run(
        self,
        image_path: str,
        description: str,
        source_context: str,
        caption: str,
        diagram_type: DiagramType = DiagramType.METHODOLOGY,
    ) -> CritiqueResult:
        """Evaluate a generated image and provide revision feedback.

        Args:
            image_path: Path to the generated image.
            description: The description used to generate the image.
            source_context: Original methodology text.
            caption: Figure caption / communicative intent.
            diagram_type: Type of diagram.

        Returns:
            CritiqueResult with evaluation and optional revised description.
        """
        # Load the image
        image = load_image(image_path)

        # PHASE 1: Visual Analysis (NEW - Optional)
        visual_analysis = None
        if self._enable_visual_analysis and self.vlm.supports_code_execution():
            logger.info("Analyzing visual properties with agentic vision")
            visual_analysis = await self._analyze_visual_properties(
                image, description, source_context
            )
            logger.info(
                "Visual analysis complete",
                num_text_errors=len(visual_analysis.text_errors),
                has_layout_score=visual_analysis.layout_balance_score is not None,
            )

        # PHASE 2: Critique (EXISTING - Enhanced with analysis)
        extra_context = ""
        if visual_analysis:
            extra_context = self._format_analysis_context(visual_analysis)

        prompt_type = "diagram" if diagram_type == DiagramType.METHODOLOGY else "plot"
        template = self.load_prompt(prompt_type)
        prompt = self.format_prompt(
            template,
            source_context=source_context,
            caption=caption,
            description=description,
            visual_analysis=extra_context,
        )

        logger.info("Running critic agent", image_path=image_path)

        response = await self.vlm.generate(
            prompt=prompt,
            images=[image],
            temperature=0.3,
            max_tokens=4096,
            response_format="json",
        )

        critique = self._parse_response(response)
        critique.visual_analysis = visual_analysis
        logger.info(
            "Critic evaluation complete",
            needs_revision=critique.needs_revision,
            summary=critique.summary,
        )
        return critique

    def _parse_response(self, response: str) -> CritiqueResult:
        """Parse the VLM response into a CritiqueResult."""
        try:
            data = json.loads(response)
            return CritiqueResult(
                critic_suggestions=data.get("critic_suggestions", []),
                revised_description=data.get("revised_description"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse critic response", error=str(e))
            # Conservative fallback: empty suggestions means no revision needed
            return CritiqueResult(
                critic_suggestions=[],
                revised_description=None,
            )

    async def _analyze_visual_properties(
        self, image, description: str, source_context: str
    ) -> VisualAnalysis:
        """Run agentic vision analysis with code execution.

        Uses Gemini 3 Flash's code execution to perform quantitative analysis
        of the generated diagram, extracting measurements that inform critique.

        Args:
            image: PIL Image object to analyze.
            description: Description used to generate the image.
            source_context: Original methodology text.

        Returns:
            VisualAnalysis with quantitative measurements.
        """
        analysis_prompt = self._build_analysis_prompt(description, source_context)

        try:
            response = await self.vlm.generate_with_tools(
                prompt=analysis_prompt,
                images=[image],
                temperature=0.1,  # Low temp for deterministic analysis
                max_tokens=4096,
                response_format="json",
                tools=["code_execution"],
            )
            return self._parse_visual_analysis(response)
        except Exception as e:
            logger.error(
                "Visual analysis failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return VisualAnalysis()

    def _build_analysis_prompt(self, description: str, source_context: str) -> str:
        """Build prompt for visual analysis with code execution."""
        return f"""You are a visual analysis expert with Python code execution.

Analyze this academic diagram and provide quantitative measurements:

1. TEXT DETECTION & CLARITY
   - Extract all visible text using OCR or visual inspection
   - Identify text errors: typos, garbled text, nonsensical labels
   - Calculate text clarity score (font size, contrast, readability)

2. LAYOUT METRICS
   - Identify major diagram components and bounding boxes
   - Calculate layout balance (distribution across canvas)
   - Measure whitespace utilization

3. VISUAL PROPERTIES
   - Analyze color distribution and palette
   - Calculate contrast ratios for text/background
   - Check for accessibility issues

4. COMPARISON TO DESCRIPTION
   - Verify described elements are present and correctly positioned
   - Check for missing or hallucinated components

Use Python + PIL/matplotlib/numpy for analysis. Output JSON:
{{
    "detected_text": ["text1", "text2"],
    "text_clarity_score": 0.85,
    "text_errors": ["Found 'x-axiss' (typo)"],
    "bounding_boxes": {{"component1": [x, y, w, h]}},
    "layout_balance_score": 0.75,
    "color_distribution": {{"background": 0.6, "foreground": 0.4}},
    "contrast_ratios": {{"text_bg": 4.5}},
    "quantitative_metrics": {{"total_components": 5}}
}}

Description: {description}

Source Context: {source_context}
"""

    def _parse_visual_analysis(self, response: str) -> VisualAnalysis:
        """Parse JSON response into VisualAnalysis model."""
        try:
            data = json.loads(response)
            return VisualAnalysis(**data, raw_output=response)
        except Exception as e:
            logger.warning("Failed to parse visual analysis", error=str(e))
            return VisualAnalysis(raw_output=response)

    def _format_analysis_context(self, analysis: VisualAnalysis) -> str:
        """Format visual analysis for inclusion in critique prompt."""
        parts = ["VISUAL ANALYSIS (quantitative measurements):"]

        if analysis.detected_text:
            parts.append(f"Detected Text: {', '.join(analysis.detected_text[:10])}")
            if len(analysis.detected_text) > 10:
                parts.append(f"  ... and {len(analysis.detected_text) - 10} more")

        if analysis.text_errors:
            parts.append("Text Errors:")
            parts.extend(f"  - {err}" for err in analysis.text_errors)

        if analysis.text_clarity_score is not None:
            parts.append(f"Text Clarity Score: {analysis.text_clarity_score:.2f}")

        if analysis.layout_balance_score is not None:
            parts.append(f"Layout Balance Score: {analysis.layout_balance_score:.2f}")

        if analysis.bounding_boxes:
            parts.append(f"Detected Components: {len(analysis.bounding_boxes)}")

        if analysis.contrast_ratios:
            ratios = ", ".join(f"{k}={v:.1f}" for k, v in analysis.contrast_ratios.items())
            parts.append(f"Contrast Ratios: {ratios}")

        return "\n".join(parts)
