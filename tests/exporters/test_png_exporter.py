"""Tests for PNG exporter."""

import pytest
from pathlib import Path
from PIL import Image
from paperbanana.exporters.png import PNGExporter
from paperbanana.core.types import ExportConfig


@pytest.mark.asyncio
async def test_png_exporter_basic(tmp_path):
    """Test basic PNG export."""
    # Create a test image
    test_image = Image.new("RGB", (100, 100), color="red")

    # Export
    exporter = PNGExporter()
    output_path = tmp_path / "output.png"
    result_path = await exporter.export(test_image, output_path)

    assert result_path.exists()
    assert result_path.suffix == ".png"

    # Verify image can be loaded
    loaded_image = Image.open(result_path)
    assert loaded_image.size == (100, 100)


@pytest.mark.asyncio
async def test_png_exporter_auto_extension(tmp_path):
    """Test that PNG exporter adds .png extension if missing."""
    test_image = Image.new("RGB", (100, 100), color="blue")

    exporter = PNGExporter()
    output_path = tmp_path / "output"  # No extension
    result_path = await exporter.export(test_image, output_path)

    assert result_path.suffix == ".png"
    assert result_path.exists()


@pytest.mark.asyncio
async def test_png_exporter_with_config(tmp_path):
    """Test PNG export with custom DPI."""
    test_image = Image.new("RGB", (100, 100), color="green")

    exporter = PNGExporter()
    output_path = tmp_path / "output.png"
    config = ExportConfig(dpi=600)
    result_path = await exporter.export(test_image, output_path, config)

    assert result_path.exists()


def test_png_exporter_availability():
    """Test that PNG exporter is always available."""
    exporter = PNGExporter()
    assert exporter.is_available()
