"""Abstract base classes for all providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from PIL import Image


class VLMProvider(ABC):
    """Abstract interface for Vision-Language Model providers.

    All VLM providers (used by Retriever, Planner, Stylist, Critic agents)
    must implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and config."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier being used."""
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        images: Optional[list[Image.Image]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        response_format: Optional[str] = None,
    ) -> str:
        """Generate text from a prompt, optionally with images.

        Args:
            prompt: The user prompt text.
            images: Optional list of images for vision tasks.
            system_prompt: Optional system-level instructions.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in the response.
            response_format: Optional format hint ("json" for JSON mode).

        Returns:
            Generated text response.
        """
        ...

    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        return True

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
        """Generate with tool support (code execution, etc).

        This method enables agentic vision capabilities like code execution
        for visual analysis. Providers that don't support tools will fall
        back to standard generate().

        Args:
            prompt: The user prompt text.
            images: Optional list of images for vision tasks.
            system_prompt: Optional system-level instructions.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in the response.
            response_format: Optional format hint ("json" for JSON mode).
            tools: Optional list of tools to enable (e.g., ["code_execution"]).

        Returns:
            Generated text response.

        Raises:
            NotImplementedError: If tools are requested but not supported.
        """
        if tools and "code_execution" in tools:
            raise NotImplementedError(
                f"{self.name} does not support code execution. "
                f"Use a provider that supports agentic vision (e.g., Gemini 3 Flash)."
            )
        return await self.generate(
            prompt=prompt,
            images=images,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    def supports_code_execution(self) -> bool:
        """Check if provider supports code execution for agentic vision.

        Returns:
            True if this provider can execute Python code during generation.
            False otherwise (will fall back to standard generation).
        """
        return False


class ImageGenProvider(ABC):
    """Abstract interface for image generation providers.

    Used by the Visualizer agent to generate methodology diagrams
    and other academic illustrations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and config."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier being used."""
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """Generate an image from a text prompt.

        Args:
            prompt: Text description of the desired image.
            negative_prompt: What to avoid in the image.
            width: Output image width in pixels.
            height: Output image height in pixels.
            seed: Random seed for reproducibility.

        Returns:
            Generated PIL Image.
        """
        ...

    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        return True
