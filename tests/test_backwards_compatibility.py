"""Backwards compatibility tests.

These tests ensure that existing workflows remain unchanged after
adding multi-format input/output support.
"""

import pytest
from pathlib import Path
from PIL import Image
from paperbanana.core.types import GenerationInput, DiagramType, LoaderConfig, ExportConfig
from paperbanana.loaders.text import TextLoader
from paperbanana.exporters.png import PNGExporter


@pytest.mark.asyncio
async def test_original_text_loading_workflow(tmp_path):
    """Test that original text loading behavior is preserved."""
    # Original workflow: create text file and read it
    test_file = tmp_path / "methodology.txt"
    original_content = "This is the original methodology text.\nMultiple lines."
    test_file.write_text(original_content, encoding="utf-8")

    # Original approach: direct file read
    loaded_content_old = test_file.read_text(encoding="utf-8")

    # New approach: using TextLoader
    loader = TextLoader()
    load_result = await loader.load(test_file)

    # Both approaches should yield identical content
    assert loaded_content_old == load_result.source_context
    assert loaded_content_old == original_content


@pytest.mark.asyncio
async def test_original_png_export_workflow(tmp_path):
    """Test that original PNG export behavior is preserved."""
    # Create a test image
    test_image = Image.new("RGB", (800, 600), color="blue")

    # Original workflow: save directly with Pillow
    original_path = tmp_path / "original.png"
    test_image.save(original_path, format="PNG", optimize=True)

    # New workflow: use PNGExporter
    new_path = tmp_path / "new.png"
    exporter = PNGExporter()
    result_path = await exporter.export(test_image, new_path)

    # Both files should exist
    assert original_path.exists()
    assert result_path.exists()

    # Both should be valid PNG files
    img_original = Image.open(original_path)
    img_new = Image.open(result_path)

    assert img_original.size == img_new.size
    assert img_original.mode == img_new.mode


def test_generation_input_unchanged():
    """Test that GenerationInput model is unchanged."""
    # This is the original usage pattern
    gen_input = GenerationInput(
        source_context="Methodology text here",
        communicative_intent="Figure caption",
        diagram_type=DiagramType.METHODOLOGY,
    )

    assert gen_input.source_context == "Methodology text here"
    assert gen_input.communicative_intent == "Figure caption"
    assert gen_input.diagram_type == DiagramType.METHODOLOGY


def test_default_cli_behavior():
    """Test that default CLI behavior matches original.

    This tests the data models used by CLI, not the CLI itself.
    The CLI should default to text input and PNG output.
    """
    # Default loader config should not modify behavior
    config = LoaderConfig()
    assert config.encoding == "utf-8"
    assert config.extract_methodology is True  # But doesn't affect plain text

    # Default export config should match original PNG export
    export_config = ExportConfig()
    assert export_config.dpi == 300


@pytest.mark.asyncio
async def test_no_breaking_changes_to_core_types():
    """Verify that core types have no breaking changes."""
    # GenerationInput should still work with original fields
    gen_input = GenerationInput(
        source_context="test",
        communicative_intent="test caption",
    )
    assert hasattr(gen_input, "source_context")
    assert hasattr(gen_input, "communicative_intent")
    assert hasattr(gen_input, "diagram_type")
    assert hasattr(gen_input, "raw_data")

    # LoaderConfig and ExportConfig are new, not breaking changes
    loader_config = LoaderConfig()
    export_config = ExportConfig()
    assert loader_config is not None
    assert export_config is not None


@pytest.mark.asyncio
async def test_text_file_to_png_complete_workflow(tmp_path):
    """Test complete original workflow: text file → PNG output.

    This is the workflow that existed before multi-format support.
    It MUST continue to work exactly as before.
    """
    # Step 1: Create text file (user's input)
    input_file = tmp_path / "method.txt"
    input_file.write_text("Original methodology text for testing.")

    # Step 2: Load text (original way)
    source_context = input_file.read_text(encoding="utf-8")

    # Step 3: Create GenerationInput (unchanged)
    gen_input = GenerationInput(
        source_context=source_context,
        communicative_intent="Test figure caption",
        diagram_type=DiagramType.METHODOLOGY,
    )

    assert gen_input.source_context == "Original methodology text for testing."

    # Step 4: Simulate image generation (would be pipeline.generate())
    # For testing, just create a dummy image
    result_image = Image.new("RGB", (800, 600), color="green")

    # Step 5: Save as PNG (original way)
    output_path = tmp_path / "output.png"
    result_image.save(output_path, format="PNG")

    # Verify
    assert output_path.exists()
    loaded = Image.open(output_path)
    assert loaded.size == (800, 600)

    # This entire workflow should be identical to the original
