"""Integration tests for multi-format input/output workflow."""

import pytest
from pathlib import Path
from PIL import Image
from paperbanana.loaders.registry import LoaderRegistry
from paperbanana.exporters.registry import ExporterRegistry
from paperbanana.core.types import LoaderConfig, ExportConfig


@pytest.mark.asyncio
async def test_text_to_multiformat_export(tmp_path):
    """Test complete workflow: load text → export to multiple formats."""
    # Step 1: Create test input file
    input_file = tmp_path / "method.txt"
    input_file.write_text(
        "This is a methodology description for testing.\n"
        "It includes multiple lines of text explaining the approach."
    )

    # Step 2: Load document
    loader = LoaderRegistry.auto_detect(input_file)
    load_result = await loader.load(input_file)

    assert load_result.source_context is not None
    assert len(load_result.source_context) > 0

    # Step 3: Simulate image generation (create a simple test image)
    test_image = Image.new("RGB", (800, 600), color="white")

    # Step 4: Export to multiple formats
    export_config = ExportConfig(dpi=300)
    formats_to_test = ["png", "svg", "tiff"]

    for fmt in formats_to_test:
        exporter = ExporterRegistry.create(fmt)
        output_path = tmp_path / f"output{exporter.file_extension}"
        result_path = await exporter.export(test_image, output_path, export_config)

        assert result_path.exists()
        assert result_path.suffix == exporter.file_extension


@pytest.mark.asyncio
async def test_backwards_compatibility_text_to_png(tmp_path):
    """Test that existing text → PNG workflow remains unchanged."""
    # Create test file
    input_file = tmp_path / "method.txt"
    input_file.write_text("Test methodology text")

    # Load using text loader (original behavior)
    from paperbanana.loaders.text import TextLoader

    loader = TextLoader()
    load_result = await loader.load(input_file)

    # Create test image
    test_image = Image.new("RGB", (100, 100), color="red")

    # Export as PNG (original behavior)
    from paperbanana.exporters.png import PNGExporter

    exporter = PNGExporter()
    output_path = tmp_path / "output.png"
    result_path = await exporter.export(test_image, output_path)

    # Verify result
    assert result_path.exists()
    assert result_path.suffix == ".png"
    assert load_result.source_context == "Test methodology text"
