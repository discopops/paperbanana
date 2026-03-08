"""Tests for text loader."""

import pytest
from pathlib import Path
from paperbanana.loaders.text import TextLoader
from paperbanana.core.types import LoaderConfig


@pytest.mark.asyncio
async def test_text_loader_basic(tmp_path):
    """Test basic text file loading."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_content = "This is a test methodology section.\nIt has multiple lines."
    test_file.write_text(test_content, encoding="utf-8")

    # Load the file
    loader = TextLoader()
    result = await loader.load(test_file)

    assert result.source_context == test_content
    assert result.metadata["format"] == "text"
    assert result.metadata["encoding"] == "utf-8"
    assert not result.metadata["truncated"]
    assert len(result.images) == 0


@pytest.mark.asyncio
async def test_text_loader_with_max_length(tmp_path):
    """Test text loader with max_length truncation."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_content = "A" * 1000
    test_file.write_text(test_content, encoding="utf-8")

    # Load with max length
    loader = TextLoader()
    config = LoaderConfig(max_length=100)
    result = await loader.load(test_file, config)

    assert len(result.source_context) == 100
    assert result.metadata["truncated"]


@pytest.mark.asyncio
async def test_text_loader_file_not_found():
    """Test text loader with non-existent file."""
    loader = TextLoader()
    with pytest.raises(FileNotFoundError):
        await loader.load(Path("nonexistent.txt"))


def test_text_loader_availability():
    """Test that text loader is always available."""
    loader = TextLoader()
    assert loader.is_available()


def test_text_loader_can_handle():
    """Test text loader file extension handling."""
    loader = TextLoader()
    assert loader.can_handle(Path("test.txt"))
    assert loader.can_handle(Path("test.text"))
    assert not loader.can_handle(Path("test.pdf"))
    assert not loader.can_handle(Path("test.md"))
