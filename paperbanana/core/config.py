"""Configuration management for PaperBanana."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class VLMConfig(BaseSettings):
    """VLM provider configuration."""

    provider: str = "gemini"
    model: str = "gemini-2.0-flash"


class ImageConfig(BaseSettings):
    """Image generation provider configuration."""

    provider: str = "google_imagen"
    model: str = "gemini-3-pro-image-preview"


class PipelineConfig(BaseSettings):
    """Pipeline execution configuration."""

    num_retrieval_examples: int = 10
    refinement_iterations: int = 3
    output_resolution: str = "2k"
    diagram_type: str = "methodology"


class ReferenceConfig(BaseSettings):
    """Reference set configuration."""

    path: str = "data/reference_sets"
    guidelines_path: str = "data/guidelines"


class OutputConfig(BaseSettings):
    """Output configuration."""

    dir: str = "outputs"
    save_iterations: bool = True
    save_prompts: bool = True
    save_metadata: bool = True


class Settings(BaseSettings):
    """Main PaperBanana settings, loaded from env vars and config files."""

    # Provider settings
    vlm_provider: str = "gemini"
    vlm_model: str = "gemini-2.0-flash"
    image_provider: str = "google_imagen"
    image_model: str = "gemini-3-pro-image-preview"

    # Pipeline settings
    num_retrieval_examples: int = 10
    refinement_iterations: int = 3
    output_resolution: str = "2k"

    # Reference settings
    reference_set_path: str = "data/reference_sets"
    guidelines_path: str = "data/guidelines"

    # Output settings
    output_dir: str = "outputs"
    save_iterations: bool = True

    # Agentic Vision settings (NEW - opt-in)
    planner_enable_reference_analysis: bool = False
    planner_reference_analysis_model: str = "gemini-3-flash-preview"
    critic_enable_visual_analysis: bool = False
    critic_visual_analysis_model: str = "gemini-3-flash-preview"

    # Input format settings
    default_input_format: str = "auto"  # Auto-detect by default
    pdf_extract_methodology: bool = True
    pdf_use_vlm_extraction: bool = False  # Opt-in for VLM-based extraction

    # Export format settings
    default_export_formats: str = "png"  # Comma-separated
    export_dpi: int = 300
    export_quality: int = 95

    # API Keys (loaded from environment)
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")

    # SSL
    skip_ssl_verification: bool = Field(default=False, alias="SKIP_SSL_VERIFICATION")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @classmethod
    def from_yaml(cls, config_path: str | Path, **overrides: Any) -> Settings:
        """Load settings from a YAML config file with optional overrides."""
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}
        else:
            yaml_config = {}

        flat = _flatten_yaml(yaml_config)
        flat.update(overrides)
        return cls(**flat)


def _flatten_yaml(config: dict, prefix: str = "") -> dict:
    """Flatten nested YAML config into flat settings keys."""
    flat = {}
    key_map = {
        "vlm.provider": "vlm_provider",
        "vlm.model": "vlm_model",
        "image.provider": "image_provider",
        "image.model": "image_model",
        "pipeline.num_retrieval_examples": "num_retrieval_examples",
        "pipeline.refinement_iterations": "refinement_iterations",
        "pipeline.output_resolution": "output_resolution",
        "reference.path": "reference_set_path",
        "reference.guidelines_path": "guidelines_path",
        "output.dir": "output_dir",
        "output.save_iterations": "save_iterations",
        "planner.enable_reference_analysis": "planner_enable_reference_analysis",
        "planner.reference_analysis_model": "planner_reference_analysis_model",
        "critic.enable_visual_analysis": "critic_enable_visual_analysis",
        "critic.visual_analysis_model": "critic_visual_analysis_model",
    }

    def _recurse(d: dict, prefix: str = "") -> None:
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                _recurse(v, full_key)
            else:
                if full_key in key_map:
                    flat[key_map[full_key]] = v

    _recurse(config)
    return flat
