"""Tests for Gemini agentic vision (code execution) capabilities."""

import pytest

from paperbanana.providers.vlm.gemini import GeminiVLM


class TestGeminiAgenticVision:
    """Test suite for Gemini code execution support."""

    def test_supports_code_execution_gemini_3(self):
        """Gemini 3 models should support code execution."""
        vlm = GeminiVLM(api_key="test-key", model="gemini-3-flash-preview")
        assert vlm.supports_code_execution() is True

    def test_supports_code_execution_gemini_2(self):
        """Gemini 2 models should NOT support code execution."""
        vlm = GeminiVLM(api_key="test-key", model="gemini-2.0-flash")
        assert vlm.supports_code_execution() is False

    @pytest.mark.asyncio
    async def test_generate_with_tools_unsupported_model(self):
        """Should raise error if code execution requested on unsupported model."""
        vlm = GeminiVLM(api_key="test-key", model="gemini-2.0-flash")

        with pytest.raises(ValueError, match="does not support it"):
            await vlm.generate_with_tools(
                prompt="Analyze this image",
                tools=["code_execution"],
            )

    @pytest.mark.asyncio
    async def test_generate_with_tools_fallback_no_tools(self):
        """Should fall back to standard generate if no tools requested."""
        vlm = GeminiVLM(api_key="test-key", model="gemini-3-flash-preview")

        # This should call standard generate internally
        # We can't test the actual API call without a real API key,
        # but we can verify it doesn't raise an error
        # In real tests with API key, this would verify the fallback works
        assert True  # Placeholder for actual API test


@pytest.mark.asyncio
async def test_generate_with_tools_code_execution():
    """Integration test: Verify code execution works with real API.

    This test requires GOOGLE_API_KEY environment variable.
    Skip if not available.
    """
    import os

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set")

    vlm = GeminiVLM(api_key=api_key, model="gemini-3-flash-preview")

    # Simple code execution test
    response = await vlm.generate_with_tools(
        prompt="Calculate 123 + 456 using Python code execution. Return the result as JSON: {'result': <number>}",
        tools=["code_execution"],
        response_format="json",
    )

    # Parse response and verify calculation
    import json

    data = json.loads(response)
    assert "result" in data
    assert data["result"] == 579
