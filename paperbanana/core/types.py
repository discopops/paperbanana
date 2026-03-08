"""Core data types for PaperBanana pipeline."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class DiagramType(str, Enum):
    """Type of academic illustration to generate."""

    METHODOLOGY = "methodology"
    STATISTICAL_PLOT = "statistical_plot"


class GenerationInput(BaseModel):
    """Input to the PaperBanana generation pipeline."""

    source_context: str = Field(description="Methodology section text or relevant paper excerpt")
    communicative_intent: str = Field(description="Figure caption describing what to communicate")
    diagram_type: DiagramType = Field(default=DiagramType.METHODOLOGY)
    raw_data: Optional[dict[str, Any]] = Field(
        default=None, description="Raw data for statistical plots (CSV path or dict)"
    )


class ReferenceExample(BaseModel):
    """A single reference example from the curated set."""

    id: str
    source_context: str
    caption: str
    image_path: str
    category: Optional[str] = None


class VisualAnalysis(BaseModel):
    """Output from visual analysis with code execution (agentic vision).

    This model captures quantitative measurements extracted from diagram
    analysis via code execution, enabling more precise critique feedback.
    """

    detected_text: list[str] = Field(
        default_factory=list, description="All text content detected in the image"
    )
    text_clarity_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Text readability score (0-1)"
    )
    text_errors: list[str] = Field(
        default_factory=list, description="Detected text errors (typos, garbled text)"
    )
    bounding_boxes: dict[str, list[float]] = Field(
        default_factory=dict, description="Component bounding boxes {name: [x, y, w, h]}"
    )
    layout_balance_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Layout balance score (0-1)"
    )
    color_distribution: Optional[dict[str, float]] = Field(
        default=None, description="Color distribution analysis"
    )
    contrast_ratios: Optional[dict[str, float]] = Field(
        default=None, description="Text/background contrast ratios"
    )
    quantitative_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Additional quantitative measurements"
    )
    raw_output: Optional[str] = Field(default=None, description="Raw output from code execution")


class ReferencePatterns(BaseModel):
    """Visual patterns extracted from reference diagrams (agentic vision).

    This model captures design patterns learned from analyzing reference
    examples with code execution, informing better initial descriptions.
    """

    layout_structure: Optional[str] = Field(
        default=None, description="Dominant layout pattern (e.g., vertical flow, grid)"
    )
    component_hierarchy: dict[str, int] = Field(
        default_factory=dict, description="Component type counts {type: count}"
    )
    color_palette: list[str] = Field(
        default_factory=list, description="Dominant colors as hex codes"
    )
    spacing_ratios: dict[str, float] = Field(
        default_factory=dict, description="Spacing measurements {margin/padding/gap: ratio}"
    )
    text_sizes: dict[str, int] = Field(
        default_factory=dict, description="Text sizes by role {title/label/body: pt}"
    )
    visual_flow: Optional[str] = Field(
        default=None, description="Reading order pattern (e.g., top-to-bottom)"
    )
    successful_patterns: list[str] = Field(
        default_factory=list, description="Qualitative successful design elements"
    )
    raw_output: Optional[str] = Field(default=None, description="Raw output from code execution")


class CritiqueResult(BaseModel):
    """Output from the Critic agent."""

    critic_suggestions: list[str] = Field(default_factory=list)
    revised_description: Optional[str] = Field(
        default=None, description="Revised description if revision needed"
    )
    visual_analysis: Optional[VisualAnalysis] = Field(
        default=None,
        description="Optional quantitative analysis from agentic vision (code execution)",
    )

    @property
    def needs_revision(self) -> bool:
        return len(self.critic_suggestions) > 0

    @property
    def summary(self) -> str:
        if not self.critic_suggestions:
            return "No issues found. Image is publication-ready."
        return "; ".join(self.critic_suggestions[:3])


class IterationRecord(BaseModel):
    """Record of a single refinement iteration."""

    iteration: int
    description: str
    image_path: str
    critique: Optional[CritiqueResult] = None


class GenerationOutput(BaseModel):
    """Output from the PaperBanana generation pipeline."""

    image_path: str = Field(description="Path to the final generated image")
    description: str = Field(description="Final optimized description")
    iterations: list[IterationRecord] = Field(
        default_factory=list, description="History of refinement iterations"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


VALID_WINNERS = {"Model", "Human", "Both are good", "Both are bad"}

WINNER_SCORE_MAP: dict[str, float] = {
    "Model": 100.0,
    "Human": 0.0,
    "Both are good": 50.0,
    "Both are bad": 50.0,
}


class DimensionResult(BaseModel):
    """Result for a single comparative evaluation dimension."""

    winner: str = Field(description="Model | Human | Both are good | Both are bad")
    score: float = Field(
        ge=0.0,
        le=100.0,
        description="100 (Model wins), 0 (Human wins), 50 (Tie)",
    )
    reasoning: str = Field(default="", description="Comparison reasoning")


class EvaluationScore(BaseModel):
    """Comparative evaluation scores for a generated illustration.

    Uses the paper's referenced comparison approach where a VLM judge
    compares model-generated vs human-drawn diagrams on four dimensions,
    with hierarchical aggregation (Primary: Faithfulness + Readability,
    Secondary: Conciseness + Aesthetics).
    """

    faithfulness: DimensionResult
    conciseness: DimensionResult
    readability: DimensionResult
    aesthetics: DimensionResult
    overall_winner: str = Field(description="Hierarchical aggregation result")
    overall_score: float = Field(
        ge=0.0,
        le=100.0,
        description="100 (Model wins), 0 (Human wins), 50 (Tie)",
    )


class RunMetadata(BaseModel):
    """Metadata for a single pipeline run, for reproducibility."""

    run_id: str
    timestamp: str
    vlm_provider: str
    vlm_model: str
    image_provider: str
    image_model: str
    refinement_iterations: int
    seed: Optional[int] = None
    config_snapshot: dict[str, Any] = Field(default_factory=dict)


# Document Loader Types


class LoadResult(BaseModel):
    """Standardized output from document loaders."""

    source_context: str = Field(description="Main text content extracted from document")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Format-specific metadata (sections, pages, extraction method, etc.)",
    )
    images: list[str] = Field(
        default_factory=list, description="Paths to extracted images (if any)"
    )


class LoaderConfig(BaseModel):
    """Configuration for document loaders."""

    extract_images: bool = Field(default=False, description="Extract embedded images")
    max_length: Optional[int] = Field(default=None, description="Max text length (chars)")
    encoding: str = Field(default="utf-8", description="Text encoding")
    extract_methodology: bool = Field(
        default=True, description="Auto-extract methodology section (structured docs)"
    )
    use_vlm_extraction: bool = Field(
        default=False, description="Use VLM for intelligent section extraction (slower, more accurate)"
    )


# Export System Types


class ExportConfig(BaseModel):
    """Configuration for image exporters."""

    dpi: int = Field(default=300, ge=72, le=1200, description="Resolution for raster formats")
    quality: int = Field(default=95, ge=1, le=100, description="Quality for lossy formats")
    compression: Optional[str] = Field(default=None, description="Compression method")
    transparent: bool = Field(default=False, description="Use transparent background (if supported)")
    embed_metadata: bool = Field(default=True, description="Embed generation metadata in output")
