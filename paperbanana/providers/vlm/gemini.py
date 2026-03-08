"""Google Gemini VLM provider (FREE tier)."""

from __future__ import annotations

from typing import Optional

import structlog
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

from paperbanana.core.utils import image_to_base64
from paperbanana.providers.base import VLMProvider

logger = structlog.get_logger()


class GeminiVLM(VLMProvider):
    """Google Gemini VLM using the google-genai SDK.

    Free tier: https://makersuite.google.com/app/apikey
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self._api_key = api_key
        self._model = model
        self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai

                self._client = genai.Client(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "google-genai is required for Gemini provider. "
                    "Install with: pip install 'paperbanana[google]'"
                )
        return self._client

    def is_available(self) -> bool:
        return self._api_key is not None

    @retry(stop=stop_after_attempt(8), wait=wait_exponential(min=2, max=120))
    async def generate(
        self,
        prompt: str,
        images: Optional[list[Image.Image]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        response_format: Optional[str] = None,
    ) -> str:
        from google.genai import types

        client = self._get_client()

        contents = []
        if images:
            for img in images:
                b64 = image_to_base64(img)
                contents.append(
                    types.Part.from_bytes(
                        data=__import__("base64").b64decode(b64),
                        mime_type="image/png",
                    )
                )
        contents.append(prompt)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_prompt:
            config.system_instruction = system_prompt
        if response_format == "json":
            config.response_mime_type = "application/json"

        response = client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )

        logger.debug(
            "Gemini response",
            model=self._model,
            usage=getattr(response, "usage_metadata", None),
        )
        return response.text

    def supports_code_execution(self) -> bool:
        """Check if current model supports code execution.

        Code execution is available in Gemini 3 Flash models
        for agentic vision capabilities.
        """
        return "gemini-3" in self._model.lower()

    @retry(stop=stop_after_attempt(8), wait=wait_exponential(min=2, max=120))
    async def generate_with_tools(
        self,
        prompt: str,
        images: Optional[list[Image.Image]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        response_format: Optional[str] = None,
        tools: Optional[list[str]] = None,
    ) -> str:
        """Generate with tool support (code execution) for agentic vision.

        This method enables Gemini 3 Flash's agentic vision capabilities,
        allowing the model to write and execute Python code for visual
        analysis tasks like OCR, layout measurements, and quantitative
        image analysis.

        Args:
            prompt: The user prompt text.
            images: Optional list of images for vision tasks.
            system_prompt: Optional system-level instructions.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in the response.
            response_format: Optional format hint ("json" for JSON mode).
            tools: Optional list of tools (e.g., ["code_execution"]).

        Returns:
            Generated text response with code execution results.

        Raises:
            ValueError: If code execution is requested but model doesn't support it.
        """
        from google.genai import types

        # If no tools requested, fall back to standard generate
        if not tools or "code_execution" not in tools:
            return await self.generate(
                prompt=prompt,
                images=images,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

        # Verify code execution support
        if not self.supports_code_execution():
            raise ValueError(
                f"Code execution requested but {self._model} does not support it. "
                f"Use a Gemini 3 Flash model for agentic vision capabilities."
            )

        client = self._get_client()

        # Build contents with images
        contents = []
        if images:
            for img in images:
                b64 = image_to_base64(img)
                contents.append(
                    types.Part.from_bytes(
                        data=__import__("base64").b64decode(b64),
                        mime_type="image/png",
                    )
                )
        contents.append(prompt)

        # Configure with code execution tool
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            tools=[types.Tool(code_execution=types.ToolCodeExecution())],
        )
        if system_prompt:
            config.system_instruction = system_prompt
        if response_format == "json":
            config.response_mime_type = "application/json"

        response = client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )

        logger.debug(
            "Gemini response (with code execution)",
            model=self._model,
            usage=getattr(response, "usage_metadata", None),
            has_code_execution=True,
        )
        return response.text
