"""Tests for loader registry."""

import pytest
from pathlib import Path
from paperbanana.loaders.registry import LoaderRegistry
from paperbanana.loaders.text import TextLoader


def test_registry_create_text_loader():
    """Test creating text loader via registry."""
    loader = LoaderRegistry.create("text")
    assert isinstance(loader, TextLoader)
    assert loader.is_available()


def test_registry_create_invalid_format():
    """Test creating loader with invalid format."""
    with pytest.raises(ValueError, match="Unsupported format"):
        LoaderRegistry.create("invalid_format")


def test_registry_auto_detect_text(tmp_path):
    """Test auto-detection of text files."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    loader = LoaderRegistry.auto_detect(test_file)
    assert isinstance(loader, TextLoader)


def test_registry_auto_detect_with_string_path(tmp_path):
    """Test auto-detection with string path."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    loader = LoaderRegistry.auto_detect(str(test_file))
    assert isinstance(loader, TextLoader)


def test_registry_get_available_formats():
    """Test getting available formats."""
    formats = LoaderRegistry.get_available_formats()
    assert "text" in formats
    assert formats["text"] == "Plain Text"
