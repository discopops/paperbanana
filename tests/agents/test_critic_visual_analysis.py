"""Tests for Critic agent with visual analysis (agentic vision)."""

import pytest

from paperbanana.agents.critic import CriticAgent
from paperbanana.core.types import DiagramType, VisualAnalysis


class MockVLM:
    """Mock VLM provider for testing."""

    name = "mock"
    model_name = "mock-model"

    def __init__(self, response: str = "", supports_code: bool = False):
        self._response = response
        self._supports_code = supports_code

    async def generate(self, prompt, images=None, **kwargs):
        return self._response

    async def generate_with_tools(self, prompt, images=None, tools=None, **kwargs):
        if tools and "code_execution" in tools:
            # Return mock visual analysis JSON
            return """{
                "detected_text": ["Component A", "Component B"],
                "text_errors": ["Found typo: 'x-axiss'"],
                "text_clarity_score": 0.85,
                "layout_balance_score": 0.75,
                "bounding_boxes": {"box1": [10, 20, 100, 50]}
            }"""
        return self._response

    def supports_code_execution(self):
        return self._supports_code

    def is_available(self):
        return True


class TestCriticVisualAnalysis:
    """Test suite for Critic agent visual analysis."""

    @pytest.mark.asyncio
    async def test_critic_without_visual_analysis(self, tmp_path):
        """Critic should work normally when visual analysis is disabled."""
        # Create a dummy image
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="white")
        img_path = tmp_path / "test.png"
        img.save(img_path)

        vlm = MockVLM(
            response='{"critic_suggestions": [], "revised_description": null}'
        )
        critic = CriticAgent(vlm, enable_visual_analysis=False)

        result = await critic.run(
            image_path=str(img_path),
            description="Test description",
            source_context="Test context",
            caption="Test caption",
            diagram_type=DiagramType.METHODOLOGY,
        )

        assert result.needs_revision is False
        assert result.visual_analysis is None  # Should be None when disabled

    @pytest.mark.asyncio
    async def test_critic_with_visual_analysis_enabled(self, tmp_path):
        """Critic should perform visual analysis when enabled and supported."""
        # Create a dummy image
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="white")
        img_path = tmp_path / "test.png"
        img.save(img_path)

        vlm = MockVLM(
            response='{"critic_suggestions": ["Fix typo"], "revised_description": "Updated"}',
            supports_code=True,
        )
        critic = CriticAgent(vlm, enable_visual_analysis=True)

        result = await critic.run(
            image_path=str(img_path),
            description="Test description",
            source_context="Test context",
            caption="Test caption",
            diagram_type=DiagramType.METHODOLOGY,
        )

        assert result.needs_revision is True
        assert result.visual_analysis is not None
        assert isinstance(result.visual_analysis, VisualAnalysis)
        assert "Component A" in result.visual_analysis.detected_text
        assert len(result.visual_analysis.text_errors) > 0

    @pytest.mark.asyncio
    async def test_visual_analysis_graceful_fallback(self, tmp_path):
        """Critic should continue if visual analysis fails."""
        # Create a dummy image
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="white")
        img_path = tmp_path / "test.png"
        img.save(img_path)

        vlm = MockVLM(
            response='{"critic_suggestions": [], "revised_description": null}',
            supports_code=False,  # Doesn't support code execution
        )
        critic = CriticAgent(vlm, enable_visual_analysis=True)

        result = await critic.run(
            image_path=str(img_path),
            description="Test description",
            source_context="Test context",
            caption="Test caption",
            diagram_type=DiagramType.METHODOLOGY,
        )

        # Should still work, but visual_analysis will be None
        assert result.needs_revision is False
        assert result.visual_analysis is None


@pytest.mark.asyncio
async def test_visual_analysis_integration():
    """Integration test: Verify visual analysis works with real Gemini API.

    This test requires GOOGLE_API_KEY environment variable.
    Skip if not available.
    """
    import os

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set")

    from paperbanana.providers.vlm.gemini import GeminiVLM
    from paperbanana.core.config import Settings

    # Create a simple test image with text
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (400, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Test Component", fill="black")

    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f.name)
        img_path = f.name

    # Create VLM with code execution support
    vlm = GeminiVLM(api_key=api_key, model="gemini-3-flash-preview")
    critic = CriticAgent(vlm, enable_visual_analysis=True)

    result = await critic.run(
        image_path=img_path,
        description="A simple diagram with a test component",
        source_context="Testing visual analysis",
        caption="Figure 1: Test",
        diagram_type=DiagramType.METHODOLOGY,
    )

    # Verify visual analysis was performed
    assert result.visual_analysis is not None
    assert len(result.visual_analysis.detected_text) > 0

    # Clean up
    import os

    os.unlink(img_path)
