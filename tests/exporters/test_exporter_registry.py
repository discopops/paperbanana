"""Tests for exporter registry."""

import pytest
from paperbanana.exporters.registry import ExporterRegistry
from paperbanana.exporters.png import PNGExporter


def test_registry_create_png_exporter():
    """Test creating PNG exporter via registry."""
    exporter = ExporterRegistry.create("png")
    assert isinstance(exporter, PNGExporter)
    assert exporter.is_available()


def test_registry_create_invalid_format():
    """Test creating exporter with invalid format."""
    with pytest.raises(ValueError, match="Unsupported format"):
        ExporterRegistry.create("invalid_format")


def test_registry_create_multi():
    """Test creating multiple exporters."""
    exporters = ExporterRegistry.create_multi(["png", "svg"])
    assert len(exporters) == 2
    assert all(exp.is_available() for exp in exporters)


def test_registry_get_available_formats():
    """Test getting available formats."""
    formats = ExporterRegistry.get_available_formats()
    assert "png" in formats
    assert "svg" in formats
    assert formats["png"] == "PNG Image"
