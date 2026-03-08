"""Registry for discovering and instantiating image exporters."""

from __future__ import annotations

from typing import Type

from paperbanana.exporters.base import BaseExporter


class ExporterRegistry:
    """Central registry for all image exporters.

    Handles format discovery and exporter instantiation.
    Uses a plugin architecture where exporters self-register via imports.
    """

    _exporters: dict[str, Type[BaseExporter]] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Lazy initialization of exporter registry.

        Imports all exporter implementations to populate the registry.
        Only runs once on first access.
        """
        if cls._initialized:
            return

        # Import all exporter implementations
        try:
            from paperbanana.exporters.png import PNGExporter

            cls._exporters["png"] = PNGExporter
        except ImportError:
            pass

        try:
            from paperbanana.exporters.svg import SVGExporter

            cls._exporters["svg"] = SVGExporter
        except ImportError:
            pass

        try:
            from paperbanana.exporters.pdf import PDFExporter

            cls._exporters["pdf"] = PDFExporter
        except ImportError:
            pass

        try:
            from paperbanana.exporters.tiff import TIFFExporter

            cls._exporters["tiff"] = TIFFExporter
        except ImportError:
            pass

        try:
            from paperbanana.exporters.tikz import TikZExporter

            cls._exporters["tikz"] = TikZExporter
        except ImportError:
            pass

        cls._initialized = True

    @classmethod
    def create(cls, format_name: str) -> BaseExporter:
        """Create an exporter instance for a specific format.

        Args:
            format_name: Format identifier (e.g., "png", "svg", "pdf")

        Returns:
            Exporter instance for the specified format

        Raises:
            ValueError: If the format is not supported or dependencies are missing
        """
        cls._initialize()

        format_name = format_name.lower()
        if format_name not in cls._exporters:
            available = ", ".join(cls._exporters.keys())
            raise ValueError(
                f"Unsupported format: {format_name}. Available formats: {available}"
            )

        exporter_class = cls._exporters[format_name]
        exporter = exporter_class()

        if not exporter.is_available():
            hint = exporter.get_install_hint()
            raise ValueError(
                f"{exporter.format_name} exporter is not available.\n{hint}"
            )

        return exporter

    @classmethod
    def create_multi(cls, formats: list[str]) -> list[BaseExporter]:
        """Create multiple exporter instances.

        Args:
            formats: List of format identifiers

        Returns:
            List of exporter instances

        Raises:
            ValueError: If any format is not supported
        """
        return [cls.create(fmt) for fmt in formats]

    @classmethod
    def get_available_formats(cls) -> dict[str, str]:
        """Get all available formats and their display names.

        Returns:
            Dict mapping format identifiers to human-readable names
        """
        cls._initialize()

        formats = {}
        for name, exporter_class in cls._exporters.items():
            exporter = exporter_class()
            if exporter.is_available():
                formats[name] = exporter.format_name

        return formats

    @classmethod
    def get_unavailable_formats(cls) -> dict[str, str]:
        """Get formats with missing dependencies and installation hints.

        Returns:
            Dict mapping format names to installation instructions
        """
        cls._initialize()

        unavailable = {}
        for name, exporter_class in cls._exporters.items():
            exporter = exporter_class()
            if not exporter.is_available():
                unavailable[name] = exporter.get_install_hint()

        return unavailable
